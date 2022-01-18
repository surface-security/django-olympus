from django.apps import AppConfig
from django.conf import settings

APP_SETTINGS = {
    'ELASTICSEARCH_URL': '127.0.0.1',
    'ELASTICSEARCH_VERIFY_CERTS': True,
}


class OlympusConfig(AppConfig):
    name = 'olympus'

    def ready(self):
        super().ready()
        for k, v in APP_SETTINGS.items():
            _k = f'{self.name.upper()}_{k}'
            if not hasattr(settings, _k):
                setattr(settings, _k, v)
        self.module.autodiscover()
