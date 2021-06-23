from django.dispatch import receiver

from coldfront.plugins.openstack.tasks import activate_allocation
from coldfront.core.allocation.signals import allocation_activate


@receiver(allocation_activate)
def activate_allocation_receiver(sender, **kwargs):
    allocation_pk = kwargs.get('allocation_pk')
    # TODO: Async implementation
    activate_allocation(allocation_pk)
