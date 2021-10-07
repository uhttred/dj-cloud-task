from django.apps import AppConfig


class CloudTaskConfig(AppConfig):

    name = 'cloudtask'
    verbose_name = 'Django Cloud Task'

    def ready(self) -> None:
        from cloudtask.configs import conf
        conf.validate()