"""Keep Warp downloads usable by ordinary clients and pinned to the cask build."""
import hashlib
import importlib.util
import pathlib
import signal
import socket
import threading
import time
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
SPEC = importlib.util.spec_from_file_location('warp_collector', ROOT / '.github/scripts/collect_app_info.py')
COLLECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECTOR)
SOURCE = 'https://formulae.brew.sh/api/cask/warp.json'
VERSION = '0.2026.09.30.08.29.stable_01'
PAYLOAD = b'warp-dmg-fixture' * 5
SHA = hashlib.sha256(PAYLOAD).hexdigest()
URL = f'https://releases.warp.dev/stable/v{VERSION}/Warp.dmg'


def cask():
    return {'version': VERSION, 'sha256': SHA, 'name': ['Warp'], 'desc': 'Terminal',
            'homepage': 'https://www.warp.dev',
            'url': f'https://app.warp.dev/download/brew?version=v{VERSION}&package=dmg'}


def response(status=200, content_type='application/octet-stream'):
    reply = Mock(status_code=status, headers={'content-type': content_type})
    reply.iter_content.return_value = [PAYLOAD]
    return reply


class WarpReleaseTests(unittest.TestCase):
    def setUp(self):
        self.previous_handler = signal.getsignal(signal.SIGALRM)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))

    def tearDown(self):
        COLLECTOR.cask_cache.clear()
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.assertEqual(signal.getsignal(signal.SIGALRM), self.previous_handler)

    def test_catalog_uses_full_artifact_version_and_upstream_checksum(self):
        COLLECTOR.cask_cache[SOURCE] = cask()
        reply = response()
        with patch.object(COLLECTOR.requests, 'get', return_value=reply) as get:
            result = COLLECTOR.get_homebrew_app_info(SOURCE)
        self.assertEqual(result['url'], URL)
        self.assertEqual(result['vendor_url'], URL)
        self.assertEqual(result['version'], '0.2026.09.30.08.29.01')
        self.assertEqual(result['sha'], SHA)
        self.assertTrue(result['fileName'].endswith('.dmg'))
        get.assert_called_once_with(URL, headers={'User-Agent': COLLECTOR.DOWNLOAD_USER_AGENTS[0]},
            timeout=COLLECTOR.DOWNLOAD_TIMEOUT, stream=True)
        reply.close.assert_called_once()

    def test_catalog_version_matches_warp_bundle_build_suffix(self):
        for release, expected in [
            ('0.2026.10.14.08.27.stable_03', '0.2026.10.14.08.27.03'),
            ('0.2026.10.21.08.25.stable_02', '0.2026.10.21.08.25.02'),
            ('0.2026.10.21.08.25.stable_10', '0.2026.10.21.08.25.10'),
        ]:
            with self.subTest(release=release):
                COLLECTOR.cask_cache[SOURCE] = dict(cask(), version=release)
                with patch.object(COLLECTOR.requests, 'get', return_value=response()):
                    result = COLLECTOR.get_homebrew_app_info(SOURCE)
                self.assertEqual(result['version'], expected)
                self.assertEqual(result['url'], f'https://releases.warp.dev/stable/v{release}/Warp.dmg')
                self.assertEqual(result['vendor_url'], result['url'])
                self.assertEqual(result['sha'], SHA)
                self.assertEqual(result['fileName'], 'Warp.dmg')

    def test_unproven_warp_versions_are_rejected_before_download(self):
        for release in [
            '0.2026.10.21.08.25.stable', '0.2026.10.21.08.25.stable_',
            '0.2026.10.21.08.25.stable_01_02', '0.2026.10.21.08.25.preview_01',
            '0.2026.10.21.08.25.stable_02 ', '0.2026.10.21.08.25.stable_02\n',
            '0.2026.10.21.08.25.stable_٠٢', '0.２０２６.10.21.08.25.stable_02',
        ]:
            with self.subTest(release=release):
                COLLECTOR.cask_cache[SOURCE] = dict(cask(), version=release)
                with patch.object(COLLECTOR.requests, 'get') as get:
                    with self.assertRaisesRegex(ValueError, 'Warp release version'):
                        COLLECTOR.get_homebrew_app_info(SOURCE)
                get.assert_not_called()

    def test_other_casks_keep_generic_underscore_normalization(self):
        source = 'https://formulae.brew.sh/api/cask/example-app.json'
        COLLECTOR.cask_cache[source] = dict(cask(), name=['Example App'], version='1.2.3_04')
        result = COLLECTOR.get_homebrew_app_info(source)
        self.assertEqual(result['version'], '1.2.3')

    def test_dmg_gate_accepts_bundle_version_and_rejects_stable_identifier(self):
        app = {'name': 'Warp', 'version': '0.2026.10.21.08.25.02',
               'bundleId': 'dev.warp.Warp-Stable', 'fileName': 'Warp.dmg', 'url': URL}
        with patch.object(COLLECTOR.shutil, 'which', return_value='/usr/bin/hdiutil'), \
                patch.object(COLLECTOR, 'read_dmg_bundle_version', return_value=app['version']):
            COLLECTOR.verify_dmg_bundle_version(app, '0.2026.10.14.08.27.stable')
            app['version'] = '0.2026.10.21.08.25.stable'
            with self.assertRaisesRegex(RuntimeError, 'Intune rejects that mismatch'):
                COLLECTOR.verify_dmg_bundle_version(app, '0.2026.10.14.08.27.stable')

    def test_html_errors_missing_types_and_http_errors_cannot_publish(self):
        for status, kind in [(200, 'text/html'), (200, ''), (404, 'application/octet-stream'),
                             (403, 'application/octet-stream'), (206, 'application/octet-stream'),
                             (200, 'application/json')]:
            with self.subTest(status=status, kind=kind):
                replies = [response(status, kind) for _ in COLLECTOR.DOWNLOAD_USER_AGENTS]
                with patch.object(COLLECTOR.requests, 'get', side_effect=replies):
                    with self.assertRaisesRegex(ValueError, 'catalog update refused'):
                        COLLECTOR.get_warp_release_url(cask())
                for reply in replies:
                    reply.close.assert_called_once()

    def test_network_failure_can_use_existing_client_fallback(self):
        reply = response(200, 'application/x-apple-diskimage; charset=binary')
        with patch.object(COLLECTOR.requests, 'get', side_effect=[
            COLLECTOR.requests.ConnectionError('temporary'), reply
        ]):
            self.assertEqual(COLLECTOR.get_warp_release_url(cask()), URL)
        reply.close.assert_called_once()

    def test_persistent_network_error_cannot_publish(self):
        with patch.object(COLLECTOR.requests, 'get', side_effect=COLLECTOR.requests.Timeout):
            with self.assertRaisesRegex(ValueError, 'catalog update refused'):
                COLLECTOR.get_warp_release_url(cask())

    def test_persistent_interrupted_body_cannot_publish(self):
        replies = [response() for _ in COLLECTOR.DOWNLOAD_USER_AGENTS]
        for reply in replies:
            reply.iter_content.side_effect = COLLECTOR.requests.exceptions.ChunkedEncodingError('interrupted')
        with patch.object(COLLECTOR.requests, 'get', side_effect=replies):
            with self.assertRaisesRegex(ValueError, 'catalog update refused'):
                COLLECTOR.get_warp_release_url(cask())
        for reply in replies:
            reply.close.assert_called_once()

    def test_complete_body_with_empty_chunks_and_uppercase_checksum(self):
        reply = response()
        reply.iter_content.return_value = [b'', PAYLOAD[:9], b'', PAYLOAD[9:]]
        data = cask()
        data['sha256'] = SHA.upper()
        COLLECTOR.cask_cache[SOURCE] = data
        with patch.object(COLLECTOR.requests, 'get', return_value=reply):
            result = COLLECTOR.get_homebrew_app_info(SOURCE)
        self.assertEqual(result['url'], URL)
        self.assertEqual(result['sha'], SHA)
        reply.iter_content.assert_called_once_with(chunk_size=1024 * 1024)
        reply.close.assert_called_once()

    def test_wrong_empty_or_truncated_body_fails_without_another_download(self):
        for body in [b'wrong artifact', b'', PAYLOAD[:-1]]:
            with self.subTest(body=body):
                reply = response()
                reply.iter_content.return_value = [body]
                with patch.object(COLLECTOR.requests, 'get', return_value=reply) as get:
                    with self.assertRaisesRegex(ValueError, 'checksum mismatch; catalog update refused'):
                        COLLECTOR.get_warp_release_url(cask())
                get.assert_called_once()
                reply.close.assert_called_once()

    def test_late_network_failure_can_fall_back_to_complete_body(self):
        interrupted, complete = response(), response()
        def chunks():
            yield PAYLOAD[:9]
            raise COLLECTOR.requests.exceptions.ChunkedEncodingError('interrupted')
        interrupted.iter_content.side_effect = lambda chunk_size: chunks()
        with patch.object(COLLECTOR.requests, 'get', side_effect=[interrupted, complete]) as get:
            self.assertEqual(COLLECTOR.get_warp_release_url(cask()), URL)
        self.assertEqual(get.call_count, 2)
        interrupted.close.assert_called_once()
        complete.close.assert_called_once()

    def test_size_header_rejected_before_body_without_retry(self):
        reply = response()
        reply.headers['content-length'] = str(COLLECTOR.WARP_MAX_DOWNLOAD_BYTES + 1)
        with patch.object(COLLECTOR.requests, 'get', return_value=reply) as get:
            with self.assertRaisesRegex(ValueError, 'size limit; catalog update refused'):
                COLLECTOR.get_warp_release_url(cask())
        get.assert_called_once()
        reply.iter_content.assert_not_called()
        reply.close.assert_called_once()

    def test_streamed_size_limit_without_length_header_fails_without_retry(self):
        reply = response()
        reply.iter_content.return_value = [PAYLOAD[:9], PAYLOAD[9:]]
        with patch.object(COLLECTOR, 'WARP_MAX_DOWNLOAD_BYTES', 10):
            with patch.object(COLLECTOR.requests, 'get', return_value=reply) as get:
                with self.assertRaisesRegex(ValueError, 'size limit; catalog update refused'):
                    COLLECTOR.get_warp_release_url(cask())
        get.assert_called_once()
        reply.close.assert_called_once()

    def test_unexpected_version_or_checksum_never_requests_an_artifact(self):
        for field, value in [('version', '../preview'), ('version', 'latest'),
                             ('version', '0.2026.09.30.08.29.preview_01'),
                             ('sha256', 'no_check'), ('sha256', ''), ('sha256', None)]:
            with self.subTest(field=field, value=value):
                data = cask()
                data[field] = value
                with patch.object(COLLECTOR.requests, 'get') as get:
                    with self.assertRaises(ValueError):
                        COLLECTOR.get_warp_release_url(data)
                get.assert_not_called()

    def test_other_casks_keep_their_original_url_without_release_probe(self):
        source = 'https://formulae.brew.sh/api/cask/other.json'
        data = cask()
        data['name'] = ['Other']
        data['url'] = 'https://example.invalid/Other.dmg'
        COLLECTOR.cask_cache[source] = data
        with patch.object(COLLECTOR.requests, 'get') as get:
            self.assertEqual(COLLECTOR.get_homebrew_app_info(source)['url'], data['url'])
        get.assert_not_called()


@unittest.skipUnless(hasattr(signal, 'setitimer'), 'Unix interval timer required')
class WarpDeadlineTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.original = signal.getsignal(signal.SIGALRM)
        self.sentinel = lambda signum, frame: None
        signal.signal(signal.SIGALRM, self.sentinel)

    def tearDown(self):
        try:
            self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
            self.assertEqual(signal.getsignal(signal.SIGALRM), self.sentinel)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, self.original)

    def test_deadline_interrupts_real_trickling_read_and_closes_socket(self):
        stop, disconnected = threading.Event(), threading.Event()
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(3)
        address = listener.getsockname()
        connections, errors = [], []
        def serve():
            try:
                connection, _ = listener.accept()
                connections.append(1)
                with connection:
                    connection.settimeout(3)
                    connection.recv(65536)
                    connection.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: 100000000\r\n\r\n')
                    while not stop.wait(0.1):
                        try:
                            connection.sendall(b'x')
                        except (BrokenPipeError, ConnectionResetError):
                            disconnected.set()
                            break
            except Exception as error:
                errors.append(error)
        baseline = set(threading.enumerate())
        worker = threading.Thread(target=serve)
        worker.start()
        real_get = COLLECTOR.requests.get
        def local_get(url, **kwargs):
            return real_get('http://127.0.0.1:' + str(address[1]) + '/Warp.dmg', **kwargs)
        started = time.monotonic()
        try:
            with patch.object(COLLECTOR, 'WARP_DOWNLOAD_DEADLINE', 0.8):
                with patch.object(COLLECTOR.requests, 'get', side_effect=local_get) as get:
                    with self.assertRaisesRegex(ValueError, 'deadline; catalog update refused'):
                        COLLECTOR.get_warp_release_url(cask())
            self.assertLess(time.monotonic() - started, 4)
            get.assert_called_once()
            self.assertTrue(disconnected.wait(2), 'Timed-out response socket was not closed')
            self.assertEqual(connections, [1])
            self.assertEqual(errors, [])
        finally:
            stop.set()
            listener.close()
            worker.join(timeout=4)
        self.assertFalse(worker.is_alive())
        self.assertEqual(set(threading.enumerate()), baseline)

    def test_one_budget_covers_all_client_attempts(self):
        denied, blocked = response(403), response()
        def blocked_chunks(chunk_size):
            time.sleep(10)
            yield PAYLOAD
        blocked.iter_content.side_effect = blocked_chunks
        def get_reply(*args, **kwargs):
            if get.call_count == 1:
                time.sleep(0.4)
                return denied
            return blocked
        started = time.monotonic()
        with patch.object(COLLECTOR, 'WARP_DOWNLOAD_DEADLINE', 0.8):
            with patch.object(COLLECTOR.requests, 'get', side_effect=get_reply) as get:
                with self.assertRaisesRegex(ValueError, 'deadline; catalog update refused'):
                    COLLECTOR.get_warp_release_url(cask())
        self.assertEqual(get.call_count, 2)
        self.assertLess(time.monotonic() - started, 3)
        denied.close.assert_called_once()
        blocked.close.assert_called_once()

    def test_non_main_thread_refuses_without_network_or_signal_changes(self):
        errors = []
        def run():
            try:
                COLLECTOR.get_warp_release_url(cask())
            except Exception as error:
                errors.append(error)
        with patch.object(COLLECTOR.requests, 'get') as get:
            worker = threading.Thread(target=run)
            worker.start()
            worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ValueError)
        self.assertRegex(str(errors[0]), 'deadline is unavailable; catalog update refused')
        get.assert_not_called()

    def test_prearmed_timer_is_untouched(self):
        signal.setitimer(signal.ITIMER_REAL, 50)
        try:
            with patch.object(COLLECTOR.requests, 'get') as get:
                with self.assertRaisesRegex(ValueError, 'timer is occupied; catalog update refused'):
                    COLLECTOR.get_warp_release_url(cask())
            get.assert_not_called()
            self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0], 45)
            self.assertEqual(signal.getsignal(signal.SIGALRM), self.sentinel)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def test_unsupported_timer_refuses_before_network(self):
        with patch.object(COLLECTOR, 'signal', SimpleNamespace()):
            with patch.object(COLLECTOR.requests, 'get') as get:
                with self.assertRaisesRegex(ValueError, 'deadline is unavailable; catalog update refused'):
                    COLLECTOR.get_warp_release_url(cask())
        get.assert_not_called()


if __name__ == '__main__':
    unittest.main()
