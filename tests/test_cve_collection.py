"""Exercise the workflow's actual collector with fake providers and temporary files."""
import ast
import contextlib
import datetime
import io
import json
import os
import re
from pathlib import Path
import sys
import tempfile
import types
import typing
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from email.utils import parsedate_to_datetime
import unittest
from unittest import mock

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/check-app-cves.yml'


def collector_source():
    text = WORKFLOW.read_text()
    marker = "          cat > check_cves.py << 'PYTHON_SCRIPT'\n"
    source = text.split(marker, 1)[1].split('          PYTHON_SCRIPT', 1)[0]
    return '\n'.join(line[10:] if line.startswith('          ') else line for line in source.splitlines())


class NetworkError(Exception):
    pass


class RequestTimeout(NetworkError):
    pass


class Response:
    def __init__(self, status=200, data=None):
        self.status_code = status
        self.data = data

    def json(self):
        if isinstance(self.data, Exception):
            raise self.data
        return self.data


def page(total=0, ids=(), start=0):
    return Response(data={'totalResults': total, 'startIndex': start,
                          'vulnerabilities': [{'cve': {'id': name, 'published': '2099-01-01T00:00:00',
                                                       'descriptions': [{'lang': 'en', 'value': 'Fake fixture'}]}}
                                              for name in ids]})


class CollectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.previous = b'{"fixture": "previous data stays intact"}\n'
        self.file = self.directory / 'fixture_app.json'
        self.file.write_bytes(self.previous)
        self.kev = [Response(data={'vulnerabilities': [{'cveID': 'CVE-2099-0001'}]})]
        self.nvd = [page()]
        self.calls = []
        requests = types.SimpleNamespace(get=self.get, exceptions=types.SimpleNamespace(
            RequestException=NetworkError, Timeout=RequestTimeout))
        self.ns = {k: getattr(typing, k) for k in ['Dict', 'List', 'Optional', 'Any', 'Tuple']}
        self.ns.update({'os': os, 're': re, 'sys': sys, 'json': json, 'pathlib': __import__('pathlib'),
                        'tempfile': tempfile, 'datetime': datetime.datetime, 'timedelta': datetime.timedelta,
                        'time': time, 'requests': requests,
                        'NVD_API_KEY': 'FAKE_TEST_KEY', 'SPECIFIC_APP': '', 'FULL_SYNC': False,
                        'CVE_DIR': self.directory, 'CPE_MAPPINGS': {'fixture_app': ('fake_vendor', 'fake_product', [])},
                        'MAX_RETRIES': 3, 'REQUEST_DELAY': 0, 'RETRY_DELAY': 0,
                        'NVD_WORKERS': 1, 'SCAN_START_SECONDS': 2700, 'SCAN_HARD_SECONDS': 2880,
                        'threading': threading, 'ThreadPoolExecutor': ThreadPoolExecutor, 'wait': wait,
                        'parsedate_to_datetime': parsedate_to_datetime,
                        'LOG_LOCK': threading.Lock(), 'WORK_CONTEXT': threading.local(), 'CONTROL': None,
                        'KEV_CATALOG_URL': 'https://example.test/kev', 'kev_cache': {},
                        'kev_loaded': False, 'kev_failed': False, 'print': lambda *a, **k: None})
        nodes = [n for n in ast.parse(collector_source()).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual-workflow-collector>', 'exec'), self.ns)

    def get(self, url, **kwargs):
        name = 'kev' if url.endswith('/kev') else 'nvd'
        self.calls.append((name, (kwargs.get('params') or {}).get('startIndex')))
        sequence = self.kev if name == 'kev' else self.nvd
        if not sequence:
            raise AssertionError('Unexpected additional provider request')
        result = sequence.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def run_main(self):
        with contextlib.redirect_stderr(io.StringIO()):
            return self.ns['main']()

    def assert_failed_and_preserved(self):
        with self.assertRaises(SystemExit) as result:
            self.run_main()
        self.assertEqual(result.exception.code, 1)
        self.assertEqual(self.file.read_bytes(), self.previous)

    def test_complete_zero_is_published(self):
        self.run_main()
        self.assertEqual(json.loads(self.file.read_text())['total_cves'], 0)

    def test_null_severity_keeps_cve_and_kev_classification(self):
        self.nvd = [page(1, ['CVE-2099-0001'])]
        self.run_main()
        data = json.loads(self.file.read_text())
        self.assertEqual(data['total_cves'], 1)
        self.assertEqual(data['summary']['kev_count'], 1)
        self.assertEqual(data['summary']['critical'], 0)
        self.assertIsNone(data['vulnerabilities'][0]['severity'])

    def test_first_page_timeouts_preserve_previous_file(self):
        self.nvd = [RequestTimeout()] * 3
        self.assert_failed_and_preserved()
        self.assertEqual(sum(name == 'nvd' for name, _ in self.calls), 3)

    def test_later_page_failure_never_publishes_partial_data(self):
        self.nvd = [page(2, ['CVE-2099-0001'])] + [Response(503)] * 3
        self.assert_failed_and_preserved()

    def test_bad_response_shapes_preserve_previous_file(self):
        for data in [[], {}, {'totalResults': True, 'vulnerabilities': []},
                     {'totalResults': -1, 'vulnerabilities': []}, {'totalResults': 0},
                     {'totalResults': 0, 'vulnerabilities': {}, 'startIndex': 0},
                     {'totalResults': 0, 'vulnerabilities': [], 'startIndex': False}]:
            with self.subTest(data=data):
                self.nvd = [Response(data=data)]
                self.assert_failed_and_preserved()
                self.ns.update(kev_loaded=False, kev_failed=False, kev_cache={})
                self.kev = [Response(data={'vulnerabilities': [{'cveID': 'CVE-2099-0001'}]})]

    def test_invalid_json_preserves_previous_file(self):
        self.nvd = [Response(data=ValueError('Fake malformed JSON'))] * 3
        self.assert_failed_and_preserved()

    def test_empty_page_before_total_preserves_previous_file(self):
        self.nvd = [page(2, ['CVE-2099-0001']), page(2, [], 1)]
        self.assert_failed_and_preserved()

    def test_total_drift_preserves_previous_file(self):
        self.nvd = [page(2, ['CVE-2099-0001']), page(3, ['CVE-2099-0002'], 1)]
        self.assert_failed_and_preserved()

    def test_wrong_page_offset_preserves_previous_file(self):
        self.nvd = [page(2, ['CVE-2099-0001']), page(2, ['CVE-2099-0002'], 0)]
        self.assert_failed_and_preserved()

    def test_repeated_page_entries_are_rejected(self):
        self.nvd = [page(2, ['CVE-2099-0001']), page(2, ['CVE-2099-0001'], 1)]
        self.assert_failed_and_preserved()

    def test_malformed_vulnerability_is_rejected(self):
        self.nvd = [Response(data={'totalResults': 1, 'vulnerabilities': [{}]})]
        self.assert_failed_and_preserved()

    def test_page_over_total_is_rejected(self):
        self.nvd = [page(0, ['CVE-2099-0001'])]
        self.assert_failed_and_preserved()

    def test_complete_multiple_pages_are_published(self):
        self.nvd = [page(3, ['CVE-2099-0001', 'CVE-2099-0002']), page(3, ['CVE-2099-0003'], 2)]
        self.run_main()
        self.assertEqual(json.loads(self.file.read_text())['total_cves'], 3)
        self.assertEqual([start for name, start in self.calls if name == 'nvd'], [0, 2])
        self.assertEqual(sum(name == 'kev' for name, _ in self.calls), 1)

    def test_404_is_failure_not_zero(self):
        self.nvd = [Response(404)]
        self.assert_failed_and_preserved()

    def test_transient_403_and_429_then_success(self):
        self.nvd = [Response(403), Response(429), page()]
        self.run_main()
        self.assertEqual(json.loads(self.file.read_text())['total_cves'], 0)

    def test_alternate_product_failure_preserves_whole_app(self):
        self.ns['CPE_MAPPINGS']['fixture_app'] = ('fake_vendor', 'fake_product', ['fake_alternate'])
        self.nvd = [page(1, ['CVE-2099-0001'])] + [Response(503)] * 3
        self.assert_failed_and_preserved()

    def test_kev_outage_stops_before_writes_and_is_not_refetched(self):
        self.kev = [Response(503)] * 3
        with self.assertRaises(self.ns['KevUnavailable']):
            self.run_main()
        with self.assertRaises(self.ns['KevUnavailable']):
            self.ns['is_kev']('CVE-2099-0001')
        self.assertEqual(self.file.read_bytes(), self.previous)
        self.assertEqual(self.calls, [('kev', None)] * 3)

    def test_empty_kev_catalog_is_not_a_success(self):
        self.kev = [Response(data={'vulnerabilities': []})] * 3
        with self.assertRaises(self.ns['KevUnavailable']):
            self.run_main()
        self.assertEqual(self.file.read_bytes(), self.previous)
        self.assertEqual(self.calls, [('kev', None)] * 3)

    def test_interrupted_file_write_preserves_old_file(self):
        def broken_dump(data, file, **kwargs):
            file.write('{"partial":')
            raise OSError('Fake interrupted write')
        with mock.patch.object(json, 'dump', side_effect=broken_dump):
            with self.assertRaises(OSError):
                self.ns['save_cve_json']('fixture_app', 'Fixture App', [])
        self.assertEqual(self.file.read_bytes(), self.previous)
        self.assertEqual(list(self.directory.glob('*.tmp')), [])

    def test_invalid_cve_identifier_preserves_previous_file(self):
        self.nvd = [page(1, ['not-a-cve'])]
        self.assert_failed_and_preserved()

    def test_duplicate_entries_in_one_page_are_rejected(self):
        self.nvd = [page(2, ['CVE-2099-0001', 'CVE-2099-0001'])]
        self.assert_failed_and_preserved()

    def test_invalid_kev_identifier_stops_before_writes(self):
        self.kev = [Response(data={'vulnerabilities': [{'cveID': 'not-a-cve'}]})] * 3
        with self.assertRaises(self.ns['KevUnavailable']):
            self.run_main()
        self.assertEqual(self.file.read_bytes(), self.previous)
        self.assertEqual(self.calls, [('kev', None)] * 3)

    def test_workflow_retains_steps_and_success_only_sync(self):
        text = WORKFLOW.read_text()
        names = [line.split('- name: ', 1)[1] for line in text.splitlines() if line.startswith('      - name: ')]
        self.assertEqual(names, ['Checkout repository', 'Set up Python', 'Install dependencies',
                                 'Check CVEs for apps', 'Commit and push CVE files', 'Sync CVE data to Supabase'])
        sync = text.split('      - name: Sync CVE data to Supabase', 1)[1]
        self.assertIn('        if: ${{ success() }}', sync)
        self.assertNotIn('always()', sync)
        self.assertIn('          timeout --kill-after=30s 52m python -u check_cves.py', text)
        self.assertIn('  group: check-app-cves\n  cancel-in-progress: false', text)
        self.assertIn('    timeout-minutes: 60', text)


    def test_parallel_output_matches_serial_with_alternates_and_pages(self):
        mappings = {f'app_{i}': ('vendor', f'product_{i}', ['shared'] if i % 2 else []) for i in range(6)}
        self.ns['CPE_MAPPINGS'] = mappings
        lock = threading.Lock()
        def router(url, **kw):
            with lock:
                self.calls.append(('kev' if url.endswith('/kev') else 'nvd', None))
            if url.endswith('/kev'):
                return Response(data={'vulnerabilities':[{'cveID':'CVE-2099-0001'}]})
            params = kw['params']
            start = params['startIndex']
            return page(2, [f'CVE-2099-{start+1:04d}'], start)
        self.ns['requests'].get = router
        self.ns['NVD_WORKERS'] = 1
        self.run_main()
        serial = {key:(self.directory / f'{key}.json').read_bytes() for key in mappings}
        self.ns.update(NVD_WORKERS=4, kev_loaded=False, kev_failed=False, kev_cache={})
        self.run_main()
        self.assertEqual(serial, {key:(self.directory / f'{key}.json').read_bytes() for key in mappings})
        self.assertEqual(sum(kind == 'kev' for kind, _ in self.calls), 2)

    def test_failed_app_prevents_all_file_changes(self):
        self.ns['CPE_MAPPINGS']['other'] = ('vendor', 'other', [])
        other = self.directory / 'other.json'
        other.write_bytes(self.previous)
        self.nvd = [page(), Response(404)]
        self.assert_failed_and_preserved()
        self.assertEqual(other.read_bytes(), self.previous)

    def test_global_spacing_including_retry_and_rolling_window(self):
        now = [0.0]
        clock_lock = threading.Lock()
        def clock():
            with clock_lock: return now[0]
        def sleep(delay):
            with clock_lock: now[0] += delay
        control = self.ns['RuntimeControl'](6.1, 1000, 1100, clock, sleep)
        starts = []
        def acquire():
            control.acquire()
            with control.lock: starts.append(control.next_start - 6.1)
        with ThreadPoolExecutor(4) as pool:
            list(pool.map(lambda _: acquire(), range(12)))
        starts.sort()
        self.assertTrue(all(b-a >= 6.1-1e-8 for a,b in zip(starts, starts[1:])))
        self.assertTrue(all(sum(t <= x < t+30 for x in starts) <= 5 for t in starts))
        self.assertTrue(control.lock.acquire(blocking=False))
        control.lock.release()

    def test_waiter_rechecks_global_cooldown_outside_lock(self):
        now = [0.0]
        control = None
        sleeps = []
        def sleep(delay):
            self.assertTrue(control.lock.acquire(blocking=False))
            control.lock.release()
            sleeps.append(delay)
            if len(sleeps) == 1: control.cooldown(25)
            now[0] += delay
        control = self.ns['RuntimeControl'](6.1, 100, 110, lambda:now[0], sleep)
        control.acquire()
        control.acquire()
        self.assertGreaterEqual(now[0], 25)
        self.assertGreater(len(sleeps), 1)

    def test_start_deadline_prevents_provider_attempt(self):
        control = self.ns['RuntimeControl'](6.1, 0, 10)
        self.ns['CONTROL'] = control
        with self.assertRaises(self.ns['NvdUnavailable']):
            self.ns['nvd_request']('https://example.test/nvd')
        self.assertEqual(self.calls, [])
        self.assertEqual(self.file.read_bytes(), self.previous)

    def test_hard_deadline_reports_and_exits_without_join(self):
        entered, release = threading.Event(), threading.Event()
        def blocked(*args):
            entered.set()
            release.wait(2)
            return [], None
        self.ns['CONTROL'] = self.ns['RuntimeControl'](0, 10, .03)
        self.ns['process_app'] = blocked
        output = []
        self.ns['print'] = lambda *args, **kw: output.append(' '.join(map(str,args)))
        class DeadlineExit(BaseException): pass
        try:
            with mock.patch.object(os, '_exit', side_effect=DeadlineExit):
                with self.assertRaises(DeadlineExit):
                    self.ns['collect_apps'](self.ns['CPE_MAPPINGS'])
            self.assertTrue(entered.is_set())
            self.assertTrue(any('SCAN INCOMPLETE' in line for line in output))
            self.assertTrue(any('CVE_METRICS' in line for line in output))
            self.assertEqual(self.file.read_bytes(), self.previous)
        finally:
            release.set()

    def test_largest_previous_app_submitted_first_stable_ties(self):
        mappings = {key:('vendor', key, []) for key in ['small', 'big', 'equal']}
        for key, weight in [('small', 1), ('big', 50), ('equal', 50)]:
            (self.directory / f'{key}.json').write_text(json.dumps({'total_cves':weight}))
        observed = []
        def process(key, mapping):
            observed.append(key)
            return [], None
        self.ns['process_app'] = process
        self.ns['CONTROL'] = self.ns['RuntimeControl'](0, 10, 20)
        results = self.ns['collect_apps'](mappings)
        self.assertEqual(observed, ['big', 'equal', 'small'])
        self.assertEqual(list(results), list(mappings))

    def test_body_read_timeout_classified_without_exception_text_or_key(self):
        class ReadTimeoutError(Exception): pass
        self.nvd = [NetworkError(ReadTimeoutError('FAKE_TEST_KEY')) , page()]
        output = []
        self.ns['print'] = lambda *args, **kw:output.append(' '.join(map(str,args)))
        self.run_main()
        rows = self.ns['CONTROL'].attempts
        self.assertEqual([row['outcome'] for row in rows], ['body_read_timeout', '200'])
        self.assertNotIn('FAKE_TEST_KEY', '\n'.join(output))

    def test_retry_starts_use_shared_pacer_and_timeout_tuple(self):
        starts, moments = [], [0.0]
        def fake_get(url, **kw):
            starts.append(moments[0])
            self.assertEqual(kw['timeout'], (10, 60))
            return Response(429) if len(starts) == 1 else page()
        control = self.ns['RuntimeControl'](6.1, 100, 110, lambda:moments[0], lambda n:moments.__setitem__(0,moments[0]+n))
        self.ns.update(CONTROL=control)
        self.ns['requests'].get = fake_get
        self.ns['nvd_request']('https://example.test/nvd')
        self.assertEqual(len(starts), 2)
        self.assertGreaterEqual(starts[1]-starts[0], 6.1)

    def test_retry_after_numeric_date_and_invalid_values(self):
        response = Response(429)
        response.headers = {'Retry-After':'500'}
        self.assertEqual(self.ns['retry_after_seconds'](response, 5), 120)
        response.headers = {'Retry-After':'Wed, 21 Oct 2099 07:28:00 GMT'}
        self.assertEqual(self.ns['retry_after_seconds'](response, 5), 120)
        response.headers = {'Retry-After':'invalid'}
        self.assertEqual(self.ns['retry_after_seconds'](response, 5), 5)

    def test_production_constants_are_bounded(self):
        source = collector_source()
        constants = {node.targets[0].id:node.value for node in ast.parse(source).body
                     if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
        self.assertEqual(ast.literal_eval(constants['REQUEST_DELAY']), 6.1)
        self.assertEqual(ast.literal_eval(constants['NVD_WORKERS']), 4)
        self.assertIn('SCAN_START_SECONDS = 45 * 60', source)
        self.assertIn('SCAN_HARD_SECONDS = 48 * 60', source)


if __name__ == '__main__':
    unittest.main()
