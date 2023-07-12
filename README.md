# django-olympus

[![build-status-image]][build-status]
[![coverage-status-image]][codecov]
[![pypi-version]][pypi]

Collect data from django models into ElasticSearch.

This Django application provides a `OlympusCollector` class that is a wrapper for the `ElasticSearch` API and database 
(using their official package).

To know more about how to use it, please check the [Setup](#setup) section.

## Setup

After adding `django-olympus` as part of your required packages, add `olympus` to `INSTALLED_APPS` in your `settings.py`.

The following settings are available for customization:

| Name | Default | Description |
| ---- | ------- | ----------- |
| OLYMPUS_ELASTICSEARCH_URL | None | This should point to the **ElasticSearch** server running. |
| OLYMPUS_ELASTICSEARCH_VERIFY_CERTS | None | This should tell whether certificates should be verified - only set this to false for local development |

Since this application provides a baseline Collector class, this will help you bootstrap data collectors to send 
information to `ElasticSearch`. The following section details how to write your own collectors.

### Collectors

To create your own collector, in any Django app of your project, extend the `OlympusCollector` class and implement the 
`collect` method to specify all the logic you need.

```python
#myapp/occ.py
from olympus.base import OlympusCollector


class SampleCollector(OlympusCollector):
    index_name = "sample_collector"  # can be anything you'd like.
    index_date_pattern = "%Y.%m.%d"  # can be anything you'd like.
    index_lifecycle_name = "something"  # if you use default lifecycle policies and would like to assign a different one.

    def collect(self):
        self.logger.info(f"started {self.index_name}")  # Base class provides built-in logging.

        data = some_func()  # Some logic to retrieve data, either from API, from Django's Database or whatever.

        yield = {
            "_id": "1",  # _id is mandatory and can be anything, really, as long as it is unique.
            "some": data.attribute,
            "more": data.attribute2,
        }
```

To keep collectors organized, you might want to create an `occ.py` file in each app, implementing the collectors. Each 
app can implement as many collectors as necessary, there is really no restrictions.

`olympus` API provides a `Django` command called `push_to_es` which allows you to run a collector. To run the sample 
above, `./manage.py push_to_es myapp.SampleCollector` would be required.

**Apps with collectors must be part of your `settings.py` file, otherwise collectors are not initialized and not added** 
**to the list - hence `push_to_es` will fail.**

