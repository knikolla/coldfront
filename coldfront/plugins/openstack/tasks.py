import os
import secrets

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from cinderclient import client as cinderclient
from neutronclient.v2_0 import client as neutronclient
from novaclient import client as novaclient

from coldfront.core.allocation.models import Allocation
from coldfront.plugins.openstack import utils

ALLOCATION_ATTR_PROJECT_ID = 'OpenStack Project ID'
ALLOCATION_ATTR_PROJECT_NAME = 'OpenStack Project Name'

RESOURCE_ATTR_AUTH_URL = 'OpenStack Auth URL'
RESOURCE_ATTR_FEDERATION_PROTOCOL = 'OpenStack Federation Protocol'
RESOURCE_ATTR_IDP = 'OpenStack Identity Provider'
RESOURCE_ATTR_PROJECT_DOMAIN = 'OpenStack Domain for Projects'
RESOURCE_ATTR_ROLE = 'OpenStack Role for User in Project'
RESOURCE_ATTR_USER_DOMAIN = 'OpenStack Domain for Users'

NOVA_VERSION = '2'
# Mapping of allocation attribute name for Quota, and what Nova expects
NOVA_KEY_MAPPING = {
    'OpenStack Compute Instance Quota': 'instances',
    'OpenStack Compute vCPU Quota': 'cores',
    'OpenStack Compute RAM Quota': 'ram',
}


def is_openstack_resource(resource):
    return resource.resource_type.name.lower() == 'openstack'


def get_unique_project_name(project_name):
    return f'{project_name}-f{secrets.token_hex(3)}'


def get_session_for_resource(resource):
    auth_url = resource.get_attribute(RESOURCE_ATTR_AUTH_URL)
    # Note: Authentication for a specific OpenStack cloud is stored in env
    # variables of the form OPENSTACK_{RESOURCE_NAME}_APPLICATION_CREDENTIAL_ID
    # and OPENSTACK_{RESOURCE_NAME}_APPLICATION_CREDENTIAL_SECRET
    # where resource name is has spaces replaced with underscored and is
    # uppercase.
    # This allows for the possibility of managing multiple OpenStack clouds
    # via multiple resources.
    var_name = resource.name.replace(' ', '_').replace('-', '_').upper()
    auth = v3.ApplicationCredential(
        auth_url=auth_url,
        application_credential_id=os.environ.get(
            f'OPENSTACK_{var_name}_APPLICATION_CREDENTIAL_ID'),
        application_credential_secret=os.environ.get(
            f'OPENSTACK_{var_name}_APPLICATION_CREDENTIAL_SECRET')
    )
    return session.Session(auth)


def activate_allocation(allocation_pk):
    def set_nova_quota():
        compute = novaclient.Client(NOVA_VERSION, session=ksa_session)
        # If the value is of a key is none, novaclient will just ignore it
        nova_payload = {nova_key: allocation.get_attribute(key)
                        for (key, nova_key) in NOVA_KEY_MAPPING.items()}
        compute.quotas.update(openstack_project.id, **nova_payload)

    allocation = Allocation.objects.get(pk=allocation_pk)

    # TODO(knikolla): It doesn't seem to be possible to select multiple resources
    # when requesting a new allocation, so why is this multivalued?
    # Does it have to do with linked resources?
    resource = allocation.resources.first()
    if is_openstack_resource(resource):
        ksa_session = get_session_for_resource(resource)
        identity = client.Client(session=ksa_session)

        # TODO: There is a possibility that this is a reactivation, rather than a new allocation
        openstack_project_name = get_unique_project_name(allocation.project.title)
        openstack_project = identity.projects.create(
            name=openstack_project_name,
            domain=resource.get_attribute(RESOURCE_ATTR_PROJECT_DOMAIN),
            enabled=True,
        )

        utils.add_attribute_to_allocation(allocation,
                                          ALLOCATION_ATTR_PROJECT_NAME,
                                          openstack_project_name)
        utils.add_attribute_to_allocation(allocation,
                                          ALLOCATION_ATTR_PROJECT_ID,
                                          openstack_project.id)

        set_nova_quota()
