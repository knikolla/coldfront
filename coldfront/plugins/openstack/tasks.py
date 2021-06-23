import secrets

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

from coldfront.core.allocation.models import (Allocation,
                                              AllocationAttribute,
                                              AllocationAttributeType)


def add_attribute_to_allocation(allocation, attribute_type, attribute_value):
    allocation_attribute_type_obj = AllocationAttributeType.objects.get(
        name=attribute_type)
    AllocationAttribute.objects.create(
        allocation_attribute_type=allocation_attribute_type_obj,
        allocation=allocation,
        value=attribute_value,
    )


def activate_allocation(allocation_pk):
    allocation = Allocation.objects.get(pk=allocation_pk)

    # TODO(knikolla): It doesn't seem to be possible to select multiple resources
    # when requesting a new allocation, so why is this multivalued?
    # Does it have to do with linked resources?
    resource = allocation.resources.first()

    if resource.resource_type.name.lower() == 'openstack':
        auth_url = resource.get_attribute('OpenStack Auth URL')

        auth = v3.Password(
            auth_url=auth_url,
            username='admin',
            user_domain_name='Default',
            password='nomoresecret',
            project_name='admin',
            project_domain_name='Default',
        )
        sess = session.Session(auth)
        identity = client.Client(session=sess)

        suffix = secrets.token_hex(3)
        openstack_project_name = f'{allocation.project.title}-f{suffix}'
        openstack_project = identity.projects.create(
            name=openstack_project_name,
            domain=resource.get_attribute('OpenStack Domain for Projects'),
            enabled=True,
        )

        add_attribute_to_allocation(allocation, 'OpenStack Project Name', openstack_project_name)
        add_attribute_to_allocation(allocation, 'OpenStack Project ID', openstack_project.id)
