from datetime import datetime
from io import StringIO
from unittest import mock

from django.core.management import call_command, CommandError
from django.test import TestCase

from olympus.base import OlympusCollector


class ATestCollector(OlympusCollector):
    def collect(self):
        return [{'k': 1}, {'k': 2}]


class AnotherTestCollector(OlympusCollector):
    def collect(self):
        return [{'k': 2}]


class Test(TestCase):
    def test_push_to_es_list(self):
        out = StringIO()
        err = StringIO()
        call_command('push_to_es', no_progress=True, stdout=out, stderr=err)
        self.assertIn('tests.ATestCollector', out.getvalue())
        self.assertIn('tests.AnotherTestCollector', out.getvalue())
        self.assertEqual(err.getvalue(), '')

    def test_push_to_es_invalid(self):
        out = StringIO()
        err = StringIO()
        with self.assertRaises(CommandError) as cm:
            call_command('push_to_es', 'inexistent', no_progress=True, stdout=out, stderr=err)
        self.assertEqual(cm.exception.args, ('no valid collectors specified',))
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), '')
    
    def test_base_collector(self):
        timestamp = datetime(2019, 1, 15, 9, 0, 0)
        es = mock.MagicMock()
        with mock.patch('django.utils.timezone.now') as mp:
            x = ATestCollector()
            self.assertIsNotNone(x.timestamp)
            self.assertIsNotNone(x.es)
            # save for later
            es.transport.serializer = x.es.transport.serializer
            mp.assert_called_once_with()

            mp.reset_mock()
            x = ATestCollector(es=es, timestamp=timestamp)
            self.assertEqual(x.es, es)
            self.assertEqual(x.timestamp, timestamp)
            mp.assert_not_called()

        self.assertEqual(x.get_index_name(), 'tests.atestcollector')
        x.index_date_pattern = '%Y-%m'
        self.assertEqual(x.get_index_name(), 'tests.atestcollector-2019-01')

        x.create_index()
        es.indices.create.assert_called_once_with(ignore=400, index='tests.atestcollector-2019-01')

        es.reset_mock()
        self.assertEqual(x.push(), (0, []))
        es.bulk.assert_called_once_with(
            '''\
{"index":{"_index":"tests.atestcollector-2019-01","_type":"status"}}
{"k":1}
{"index":{"_index":"tests.atestcollector-2019-01","_type":"status"}}
{"k":2}
'''
        )


class TestMocked(TestCase):
    def setUp(self):
        p = mock.patch('olympus.base.OlympusCollector.create_index')
        self.ci_m = p.start()
        self.addCleanup(p.stop)

        p = mock.patch('elasticsearch.helpers.streaming_bulk')
        self.bulk_m = p.start()
        self.addCleanup(p.stop)
        def _f(*a, **b):
            for i in a[1]:
                yield (True, i)
        self.bulk_m.side_effect = _f

    def test_push_to_es_all_good(self):
        out = StringIO()
        err = StringIO()
        call_command('push_to_es', 'tests.ATestCollector', no_progress=True, stdout=out, stderr=err)
        self.ci_m.assert_called_once_with()
        self.bulk_m.assert_called_once()
        self.assertEqual(out.getvalue(), 'Matched 1 collectors\ntests.ATestCollector pushed 2 records\n')
        self.assertEqual(err.getvalue(), '')

    def test_push_to_es_so_so(self):
        out = StringIO()
        err = StringIO()
        def _f(*a, **b):
            # fail half
            for i, v in enumerate(a[1]):
                yield (i % 2, v)
        self.bulk_m.side_effect = _f

        with self.assertRaises(CommandError) as cm:
            call_command('push_to_es', 'tests.ATestCollector', no_progress=True, stdout=out)
        self.ci_m.assert_called_once_with()
        self.bulk_m.assert_called_once()
        self.assertEqual(out.getvalue(), 'Matched 1 collectors\ntests.ATestCollector pushed 1 records\n')
        self.assertEqual(err.getvalue(), '')
        self.assertEqual(cm.exception.args, ('These collectors failed', ['tests.ATestCollector']))

    def test_push_to_es_all_all_good(self):
        out = StringIO()
        err = StringIO()
        call_command('push_to_es', 'tests', no_progress=True, stdout=out, stderr=err)
        self.assertEqual(
            out.getvalue(),
            'Matched 2 collectors\n'
            'tests.ATestCollector pushed 2 records\n'
            'tests.AnotherTestCollector pushed 1 records\n',
        )
        self.assertEqual(err.getvalue(), '')

    def test_push_to_es_test_flag(self):
        out = StringIO()
        err = StringIO()
        call_command('push_to_es', 'tests', no_progress=True, test=True, stdout=out, stderr=err)
        self.assertEqual(
            out.getvalue(),
            'Matched 2 collectors\n'
            'tests.ATestCollector pushed 2 records\n'
            'tests.AnotherTestCollector pushed 1 records\n',
        )
        self.assertEqual(err.getvalue(), '')
        self.bulk_m.assert_not_called()
        self.ci_m.assert_not_called()
