__version__ = '0.0.4'

# set default_app_config when using django earlier than 3.2
try:
    import django

    if django.VERSION < (3, 2):
        default_app_config = 'olympus.apps.OlympusConfig'
except ImportError:
    pass


def autodiscover():
    from django.utils.module_loading import autodiscover_modules

    autodiscover_modules('occ')
