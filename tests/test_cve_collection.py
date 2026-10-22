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


class ReadTimeout(RequestTimeout):
    pass


class ConnectTimeout(RequestTimeout):
    pass


class ChunkedEncodingError(NetworkError):
    pass


class ContentDecodingError(NetworkError):
    pass


class ReadTimeoutError(Exception):
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
        self.sizes = []
        requests = types.SimpleNamespace(get=self.get, exceptions=types.SimpleNamespace(
            RequestException=NetworkError, Timeout=RequestTimeout))
        self.ns = {k: getattr(typing, k) for k in ['Dict', 'List', 'Optional', 'Any', 'Tuple']}
        self.ns.update({'os': os, 're': re, 'sys': sys, 'json': json, 'pathlib': __import__('pathlib'),
                        'tempfile': tempfile, 'datetime': datetime.datetime, 'timedelta': datetime.timedelta,
                        'time': time, 'requests': requests,
                        'NVD_API_KEY': 'FAKE_TEST_KEY', 'SPECIFIC_APP': '', 'FULL_SYNC': False,
                        'CVE_DIR': self.directory, 'CPE_MAPPINGS': {'fixture_app': ('fake_vendor', 'fake_product', [])},
                        'MAX_RETRIES': 3, 'PAGE_SIZES': (500, 200, 100), 'REQUEST_DELAY': 0, 'RETRY_DELAY': 0,
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
        if name == 'nvd':
            self.sizes.append(kwargs['params']['resultsPerPage'])
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
        local = threading.local()
        barrier = threading.Barrier(4)
        starts_lock = threading.Lock()
        def clock():
            with clock_lock:
                local.last = now[0]
                return now[0]
        def sleep(delay):
            with clock_lock:
                now[0] += delay
        control = self.ns['RuntimeControl'](6.1, 1000, 1100, clock, sleep)
        starts = []
        def acquire():
            control.acquire()
            # Force other workers to advance the shared next_start before recording.
            barrier.wait(timeout=2)
            with starts_lock:
                starts.append(local.last)
        with ThreadPoolExecutor(4) as pool:
            list(pool.map(lambda _: acquire(), range(12)))
        starts.sort()
        self.assertEqual(len(starts), 12)
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

    def test_unknown_specific_app_reports_valid_keys_without_nvd_or_writes(self):
        self.ns['SPECIFIC_APP'] = 'missing_app'
        output = []
        self.ns['print'] = lambda *args, **kw: output.append(' '.join(map(str, args)))
        self.assert_failed_and_preserved()
        diagnostic = [line for line in output if 'ERROR: Unknown app' in line]
        self.assertEqual(len(diagnostic), 1)
        self.assertIn('missing_app', diagnostic[0])
        self.assertIn('fixture_app', diagnostic[0])
        self.assertEqual(self.calls, [('kev', None)])

    def test_first_failure_stops_queued_requests_and_keeps_original_cause(self):
        self.ns['CPE_MAPPINGS']['queued_app'] = ('vendor', 'queued', [])
        other = self.directory / 'queued_app.json'
        other.write_bytes(self.previous)
        self.nvd = [Response(404)]
        output = []
        self.ns['print'] = lambda *args, **kw: output.append(' '.join(map(str, args)))
        self.assert_failed_and_preserved()
        self.assertEqual(other.read_bytes(), self.previous)
        self.assertEqual(sum(name == 'nvd' for name, _ in self.calls), 1)
        control = self.ns['CONTROL']
        self.assertTrue(control.stopped)
        self.assertEqual(control.first_failure[0], 'fixture_app')
        self.assertIn('HTTP 404', control.first_failure[1])
        self.assertEqual(control.stopped_apps, {'queued_app'})
        self.assertEqual(sum('ERROR:' in line for line in output), 1)
        self.assertTrue(any('SCAN STOPPED after fixture_app' in line and 'queued_app' in line for line in output))

    def test_waiter_observes_stop_and_pause_does_not_sleep(self):
        now = [0.0]
        sleeps = []
        control = None
        def sleep(delay):
            sleeps.append(delay)
            with control.lock:
                control.stopped = True
            now[0] += delay
        control = self.ns['RuntimeControl'](6.1, 100, 110, lambda: now[0], sleep)
        control.acquire()
        with self.assertRaises(self.ns['ScanStopped']) as stopped:
            control.acquire()
        self.assertIn('stopped after earlier app failure', str(stopped.exception))
        before = list(sleeps)
        with self.assertRaises(self.ns['ScanStopped']):
            control.pause(5)
        self.assertEqual(sleeps, before)
        deadline = self.ns['RuntimeControl'](6.1, 0, 10)
        with self.assertRaises(self.ns['NvdUnavailable']) as expired:
            deadline.acquire()
        self.assertNotIsInstance(expired.exception, self.ns['ScanStopped'])
        self.assertIn('deadline exceeded', str(expired.exception))

    def test_inflight_requests_finish_but_no_followup_pages_start(self):
        self.ns.update(NVD_WORKERS=3, CPE_MAPPINGS={key: ('vendor', key, []) for key in ['first', 'second', 'third']})
        for key in self.ns['CPE_MAPPINGS']:
            (self.directory / f'{key}.json').write_bytes(self.previous)
        barrier = threading.Barrier(3)
        failed = threading.Event()
        calls = []
        calls_lock = threading.Lock()
        original = self.ns['process_app']
        def process(key, mapping):
            result = original(key, mapping)
            if key == 'first':
                failed.set()
            return result
        def transport(url, **kw):
            if url.endswith('/kev'):
                return Response(data={'vulnerabilities': [{'cveID': 'CVE-2099-0001'}]})
            params = kw['params']
            product = params['virtualMatchString'].split(':')[4]
            with calls_lock:
                calls.append((product, params['startIndex']))
            self.assertEqual(params['startIndex'], 0)
            barrier.wait(timeout=10)
            if product == 'first':
                return Response(404)
            self.assertTrue(failed.wait(10))
            return page(2, ['CVE-2099-0001'])
        self.ns['process_app'] = process
        self.ns['requests'].get = transport
        self.assert_failed_and_preserved()
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(self.ns['CONTROL'].attempts), 3)
        self.assertEqual(self.ns['CONTROL'].first_failure[0], 'first')
        self.assertEqual(self.ns['CONTROL'].stopped_apps, {'second', 'third'})
        for key in self.ns['CPE_MAPPINGS']:
            self.assertEqual((self.directory / f'{key}.json').read_bytes(), self.previous)

    def test_production_constants_are_bounded(self):
        source = collector_source()
        constants = {node.targets[0].id:node.value for node in ast.parse(source).body
                     if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
        self.assertEqual(ast.literal_eval(constants['REQUEST_DELAY']), 6.1)
        self.assertEqual(ast.literal_eval(constants['NVD_WORKERS']), 4)
        self.assertEqual(ast.literal_eval(constants['PAGE_SIZES']), (500, 200, 100))
        self.assertEqual(ast.literal_eval(constants['MAX_RETRIES']), 3)
        self.assertIn('timeout=(10, 60)', source)
        self.assertIn('SCAN_START_SECONDS = 45 * 60', source)
        self.assertIn('SCAN_HARD_SECONDS = 48 * 60', source)

    def sized_provider(self, total=650, on_call=None):
        """Serve complete, ordered fake pages while recording immutable request sizes."""
        observed = []
        def transport(url, **kwargs):
            if url.endswith('/kev'):
                return self.get(url, **kwargs)
            params = kwargs['params']
            product = params['virtualMatchString'].split(':')[4]
            start, size = params['startIndex'], params['resultsPerPage']
            observed.append((product, start, size))
            self.calls.append(('nvd', start))
            self.sizes.append(size)
            result = on_call(params, len(observed)) if on_call else None
            if isinstance(result, Exception):
                raise result
            return result or page(total, [f'CVE-2099-{i+1:04d}' for i in range(start, min(start+size, total))], start)
        self.ns['requests'].get = transport
        return observed

    def test_stalled_body_shrinks_same_offset_and_matches_complete_output(self):
        self.sized_provider()
        self.run_main()
        serial = self.file.read_bytes()
        self.ns.update(kev_loaded=False, kev_failed=False, kev_cache={})
        self.kev = [Response(data={'vulnerabilities': [{'cveID': 'CVE-2099-0001'}]})]
        observed = self.sized_provider(on_call=lambda params, count:
                                       NetworkError(ReadTimeoutError('FAKE_TEST_KEY')) if count == 1 else None)
        output = []
        self.ns['print'] = lambda *args, **kw: output.append(' '.join(map(str, args)))
        self.run_main()
        self.assertEqual(observed, [('fake_product', 0, 500), ('fake_product', 0, 200),
                                    ('fake_product', 200, 200), ('fake_product', 400, 200), ('fake_product', 600, 200)])
        self.assertEqual(self.file.read_bytes(), serial)
        self.assertEqual([r['requestedSize'] for r in self.ns['CONTROL'].attempts], [500, 200, 200, 200, 200])
        self.assertEqual(self.ns['CONTROL'].report()['requestedSizes'], {'500': 1, '200': 4})
        self.assertNotIn('FAKE_TEST_KEY', '\n'.join(output))

    def test_three_body_failures_are_bounded_and_stop_queued_apps(self):
        self.ns['CPE_MAPPINGS']['queued_app'] = ('vendor', 'queued', [])
        other = self.directory / 'queued_app.json'
        other.write_bytes(self.previous)
        self.nvd = [NetworkError(ReadTimeoutError()) for _ in range(3)]
        self.assert_failed_and_preserved()
        self.assertEqual(self.sizes, [500, 200, 100])
        self.assertEqual([start for name, start in self.calls if name == 'nvd'], [0, 0, 0])
        self.assertEqual(other.read_bytes(), self.previous)
        self.assertEqual(self.ns['CONTROL'].first_failure[0], 'fixture_app')
        self.assertIn('body_read_timeout', self.ns['CONTROL'].first_failure[1])

    def test_last_attempt_100_does_not_persist_and_alternate_resets_500(self):
        self.ns['CPE_MAPPINGS']['fixture_app'] = ('fake_vendor', 'fake_product', ['fake_alternate'])
        observed = self.sized_provider(total=451, on_call=lambda params, count: ReadTimeout() if count <= 2 else None)
        self.run_main()
        self.assertEqual(observed, [('fake_product', 0, 500), ('fake_product', 0, 200),
                                    ('fake_product', 0, 100), ('fake_product', 100, 200),
                                    ('fake_product', 300, 200), ('fake_alternate', 0, 500)])
        self.assertEqual(json.loads(self.file.read_text())['total_cves'], 451)

    def test_only_body_transport_failures_shrink_page_size(self):
        cases = [(ReadTimeout(), 200), (ChunkedEncodingError(), 200), (ContentDecodingError(), 200), (ConnectTimeout(), 500),
                 (NetworkError(), 500), (Response(429), 500), (Response(503), 500),
                 (Response(500), 500), (Response(data=ValueError('FAKE_TEST_KEY')), 500)]
        for first, expected in cases:
            with self.subTest(first=type(first).__name__, expected=expected):
                self.nvd = [first, page()]
                self.sizes.clear()
                self.run_main()
                self.assertEqual(self.sizes, [500, expected])

    def test_content_decoding_failures_shrink_and_recover_without_leaking_details(self):
        self.nvd = [ContentDecodingError('FAKE_TEST_KEY'), ContentDecodingError('FAKE_TEST_KEY'), page()]
        output = []
        self.ns['print'] = lambda *args, **kw: output.append(' '.join(map(str, args)))
        self.run_main()
        self.assertEqual(self.sizes, [500, 200, 100])
        self.assertEqual([start for name, start in self.calls if name == 'nvd'], [0, 0, 0])
        self.assertEqual([row['exceptionType'] for row in self.ns['CONTROL'].attempts],
                         ['ContentDecodingError', 'ContentDecodingError', None])
        self.assertNotIn('FAKE_TEST_KEY', '\n'.join(output))
        self.assertEqual(json.loads(self.file.read_text())['total_cves'], 0)

    def test_content_decoding_exhaustion_stops_queued_work_and_keeps_files(self):
        self.ns['CPE_MAPPINGS']['queued_app'] = ('vendor', 'queued', [])
        other = self.directory / 'queued_app.json'
        other.write_bytes(self.previous)
        self.nvd = [ContentDecodingError() for _ in range(3)]
        self.assert_failed_and_preserved()
        self.assertEqual(self.sizes, [500, 200, 100])
        self.assertEqual(other.read_bytes(), self.previous)
        self.assertEqual(self.ns['CONTROL'].first_failure[0], 'fixture_app')
        self.assertEqual(self.ns['CONTROL'].stopped_apps, {'queued_app'})

    def test_shrink_keeps_oversize_drift_offset_and_repeat_guards(self):
        for defect in ['oversized', 'total', 'offset', 'repeated']:
            with self.subTest(defect=defect):
                self.file.write_bytes(self.previous)
                def reply(params, count):
                    if count == 1:
                        return ReadTimeout()
                    start = params['startIndex']
                    if defect == 'oversized' and count == 2:
                        return page(650, [f'CVE-2099-{i+1:04d}' for i in range(201)])
                    if defect == 'offset' and count == 2:
                        return page(650, ['CVE-2099-0001'], 1)
                    if count == 3:
                        return page(651 if defect == 'total' else 650,
                                    ['CVE-2099-0001'] if defect == 'repeated' else ['CVE-2099-0201'], start)
                self.sized_provider(on_call=reply)
                self.assert_failed_and_preserved()
                expected = {'oversized': 'Oversized NVD page', 'total': 'NVD pagination changed during collection',
                            'offset': 'NVD pagination changed during collection', 'repeated': 'Repeated NVD page entries'}
                self.assertEqual(self.ns['CONTROL'].first_failure[1], expected[defect])

    def test_shrinking_retry_uses_global_pacer(self):
        now, starts = [0.0], []
        self.ns['CONTROL'] = self.ns['RuntimeControl'](6.1, 100, 110, lambda: now[0], lambda n: now.__setitem__(0, now[0]+n))
        def transport(url, **kwargs):
            starts.append((now[0], kwargs['params']['resultsPerPage']))
            if len(starts) == 1:
                raise ReadTimeout()
            return page()
        self.ns['requests'].get = transport
        self.ns['nvd_request']('https://example.test/nvd', {'resultsPerPage': 500, 'startIndex': 1000})
        self.assertEqual([size for _, size in starts], [500, 200])
        self.assertGreaterEqual(starts[1][0]-starts[0][0], 6.1)

    def test_shrink_retry_cannot_escape_stop_or_start_deadline(self):
        for stopped in [True, False]:
            with self.subTest(stopped=stopped):
                now, calls = [0.0], []
                control = self.ns['RuntimeControl'](6.1, 5, 15, lambda: now[0], lambda n: now.__setitem__(0, now[0]+n))
                self.ns['CONTROL'] = control
                def transport(url, **kwargs):
                    calls.append(kwargs['params']['resultsPerPage'])
                    if stopped:
                        with control.lock:
                            control.stopped = True
                    raise ReadTimeout()
                self.ns['requests'].get = transport
                expected = self.ns['ScanStopped'] if stopped else self.ns['NvdUnavailable']
                with self.assertRaises(expected):
                    self.ns['nvd_request']('https://example.test/nvd', {'resultsPerPage': 500, 'startIndex': 0})
                self.assertEqual(calls, [500])
                self.assertEqual(self.file.read_bytes(), self.previous)


if __name__ == '__main__':
    unittest.main()
