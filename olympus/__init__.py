__version__ = '0.0.1'
default_app_config = 'olympus.apps.OlympusConfig'


def autodiscover():
    from django.utils.module_loading import autodiscover_modules

    autodiscover_modules('occ')
