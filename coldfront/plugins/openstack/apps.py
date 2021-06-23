from django.apps import AppConfig


class OpenStackConfig(AppConfig):
    name = 'coldfront.plugins.openstack'

    def ready(self):
        import coldfront.plugins.openstack.signals
