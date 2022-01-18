from typing import Generic, TypeVar
from unittest import mock

from django.utils import timezone

from olympus.base import OlympusCollector

C = TypeVar("C", bound=OlympusCollector)


class HelperTestCollectorMixin(Generic[C]):
    """Helper to test sub-classes of OlympusCollector (e.g occ.py)"""

    COLLECTOR_CLS: type[C]

    es_mock: mock.MagicMock
    collector: C
    test_now = timezone.datetime(year=2020, month=3, day=23, tzinfo=timezone.utc)
    test_now_patch: mock._patch
    test_now_mock: mock.MagicMock

    def setUp(self) -> None:
        self.test_now_patch = mock.patch("django.utils.timezone.now", return_value=self.test_now)
        self.test_now_mock = self.test_now_patch.start()
        self.es_mock = mock.MagicMock()
        self.collector = self.COLLECTOR_CLS(es=self.es_mock)

    def tearDown(self) -> None:
        self.test_now_patch.stop()
