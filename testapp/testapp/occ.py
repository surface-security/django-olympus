from olympus.base import OlympusCollector


class LifecycleCollector(OlympusCollector):
    """
    LifecycleCollector is a demo collector for the testapp, which serves to test the creation of indices in a live
    ElasticSearch database.
    **Beware the lifecycle policy name must exist in the ElasticSearch before creation.**
    To run this specific command (although not advised because this is simply a test command):
        - Setup ElasticSearch with the app, by using the variables `OLYMPUS_ELASTICSEARCH_URL`and
          `OLYMPUS_ELASTICSEARCH_VERIFY_CERTS`.
        - Check the apps with `occ.py` files are included in the main settings file, otherwise collectors are not
          loaded.
    """

    index_name = "lifecycle_collector"
    index_date_pattern = "%Y.%m.%d"
    index_lifecycle_name = "test"

    def collect(self):
        yield {
            "_id": "1",
            "key": "value",
        }

        self.logger.info(f"pushed {self.index_name} to ES successfully")
