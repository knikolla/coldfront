from django.dispatch import receiver

from coldfront.plugins.openstack.tasks import (activate_allocation,
                                               add_user_to_allocation,
                                               disable_allocation)
from coldfront.core.allocation.signals import (allocation_activate,
                                               allocation_activate_user,
                                               allocation_disable)


@receiver(allocation_activate)
def activate_allocation_receiver(sender, **kwargs):
    allocation_pk = kwargs.get('allocation_pk')
    # TODO: Async implementation
    activate_allocation(allocation_pk)


@receiver(allocation_disable)
def allocation_disable_receiver(sender, **kwargs):
    allocation_pk = kwargs.get('allocation_pk')
    # TODO: Async implementation
    disable_allocation(allocation_pk)


@receiver(allocation_activate_user)
def activate_allocation_user_receiver(sender, **kwargs):
    allocation_user_pk = kwargs.get('allocation_user_pk')
    # TODO: Async implementation
    add_user_to_allocation(allocation_user_pk)
