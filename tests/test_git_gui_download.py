"""Offline downloader contract: network retry never relaxes artifact validation."""
import hashlib
import http.client
import importlib.util
from pathlib import Path
import socket
import ssl
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch
from urllib.error import HTTPError, URLError

P = Path(__file__).resolve().parents[1] / '.github/scripts/package_git_gui.py'
spec = importlib.util.spec_from_file_location('git_gui_download_recipe', P)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)
URL = 'https://example.invalid/source.tar.xz'


class Response:
    def __init__(self, chunks, url=URL):
        self.chunks = list(chunks)
        self.url = url
        self.closed = False
    def __enter__(self): return self
    def __exit__(self, *args): self.closed = True
    def read(self, size):
        item = self.chunks.pop(0) if self.chunks else b''
        if isinstance(item, BaseException): raise item
        return item


class GitGuiDownloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'source'
        self.sleeper = patch.object(recipe.time, 'sleep')
        self.sleep = self.sleeper.start()
        self.addCleanup(self.sleeper.stop)

    def test_success_preserves_url_timeout_hash_and_closes_response(self):
        response = Response([b'complete', b' archive'])
        digest = hashlib.sha256(b'complete archive').hexdigest()
        with patch.object(recipe, 'urlopen', return_value=response) as request:
            recipe.download(URL, self.path, digest)
        self.assertEqual(self.path.read_bytes(), b'complete archive')
        self.assertTrue(response.closed)
        request.assert_called_once_with(URL, timeout=60)
        self.sleep.assert_not_called()

    def test_direct_and_wrapped_transient_connect_failure_retries_once(self):
        for make in [lambda: TimeoutError('fixture'), lambda: socket.timeout('fixture'),
                     lambda: ConnectionResetError('fixture'), lambda: http.client.RemoteDisconnected('fixture'),
                     lambda: URLError(TimeoutError('fixture')), lambda: URLError(ConnectionResetError('fixture'))]:
            with self.subTest(error=make):
                self.sleep.reset_mock(); response = Response([b'valid'])
                with patch.object(recipe, 'urlopen', side_effect=[make(), response]) as request:
                    recipe.download(URL, self.path, hashlib.sha256(b'valid').hexdigest())
                self.assertEqual(request.call_args_list, [call(URL, timeout=60)] * 2)
                self.assertEqual(self.path.read_bytes(), b'valid')
                self.assertTrue(response.closed)
                self.sleep.assert_called_once_with(1)

    def test_partial_read_failure_is_replaced_completely(self):
        for error in [TimeoutError('fixture'), ConnectionResetError('fixture'), URLError(socket.timeout('fixture'))]:
            with self.subTest(error=error):
                self.sleep.reset_mock()
                first = Response([b'old partial content much longer than replacement', error])
                second = Response([b'new'])
                with patch.object(recipe, 'urlopen', side_effect=[first, second]) as request:
                    recipe.download(URL, self.path, hashlib.sha256(b'new').hexdigest())
                self.assertEqual(self.path.read_bytes(), b'new')
                self.assertEqual(self.path.stat().st_size, 3)
                self.assertTrue(first.closed and second.closed)
                self.assertEqual(request.call_count, 2)
                self.sleep.assert_called_once_with(1)

    def test_exhaustion_raises_the_last_original_exception(self):
        last = URLError(TimeoutError('last fixture'))
        with patch.object(recipe, 'urlopen', side_effect=[TimeoutError('first fixture'), last]) as request:
            with self.assertRaises(URLError) as raised:
                recipe.download(URL, self.path)
        self.assertIs(raised.exception, last)
        self.assertEqual(request.call_count, 2)
        self.sleep.assert_called_once_with(1)
        self.assertFalse(self.path.exists())

    def test_http_tls_unclassified_and_nonmatching_errors_never_retry(self):
        errors = [HTTPError(URL, code, 'fixture', {}, None) for code in [401, 404, 429, 500, 503]]
        errors += [HTTPError(URL, 503, TimeoutError('not a network retry'), {}, None),
                   ssl.SSLCertVerificationError('fixture'), ssl.SSLError('fixture'),
                   URLError(ssl.SSLCertVerificationError('fixture')), URLError('timed out'),
                   URLError(ConnectionRefusedError('fixture')), URLError(URLError(TimeoutError('fixture'))),
                   ValueError('fixture')]
        for error in errors:
            with self.subTest(error=error), patch.object(recipe, 'urlopen', side_effect=error) as request:
                with self.assertRaises(type(error)): recipe.download(URL, self.path)
                self.assertEqual(request.call_count, 1)
        self.sleep.assert_not_called()

    def test_plaintext_and_redirect_downgrade_never_retry(self):
        with patch.object(recipe, 'urlopen') as request:
            with self.assertRaisesRegex(ValueError, 'HTTPS'): recipe.download('http://example.invalid/source', self.path)
            request.assert_not_called()
        response = Response([b'bad'], url='http://example.invalid/source')
        with patch.object(recipe, 'urlopen', return_value=response) as request:
            with self.assertRaisesRegex(ValueError, 'HTTPS'): recipe.download(URL, self.path)
            self.assertEqual(request.call_count, 1)
        self.assertTrue(response.closed)
        self.sleep.assert_not_called()

    def test_checksum_failure_never_retries(self):
        response = Response([b'wrong'])
        with patch.object(recipe, 'urlopen', return_value=response) as request:
            with self.assertRaisesRegex(ValueError, 'SHA-256'): recipe.download(URL, self.path, 'f' * 64)
            self.assertEqual(request.call_count, 1)
        self.assertTrue(response.closed)
        self.sleep.assert_not_called()

    def test_size_limit_is_preserved_without_network_retry(self):
        response = Response([b'x' * (1024 * 1024)] * 101)
        sink = MagicMock(); sink.__enter__.return_value = sink; sink.__exit__.return_value = False
        with patch.object(recipe, 'urlopen', return_value=response) as request, patch.object(Path, 'open', return_value=sink):
            with self.assertRaisesRegex(ValueError, 'download limit'): recipe.download(URL, self.path)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(sink.write.call_count, 100)
        self.assertTrue(response.closed)
        self.sleep.assert_not_called()

    def test_local_open_and_write_failures_never_retry_even_if_timeout_shaped(self):
        for error in [PermissionError('fixture'), OSError('disk fixture'), TimeoutError('local fixture'),
                      ConnectionResetError('local fixture'), URLError(TimeoutError('local fixture'))]:
            for phase in ['open', 'write']:
                with self.subTest(error=error, phase=phase):
                    response = Response([b'data'])
                    sink = MagicMock(); sink.__enter__.return_value = sink; sink.__exit__.return_value = False
                    if phase == 'write': sink.write.side_effect = error
                    with patch.object(recipe, 'urlopen', return_value=response) as request:
                        with patch.object(Path, 'open', **({'side_effect': error} if phase == 'open' else {'return_value': sink})):
                            with self.assertRaises(type(error)): recipe.download(URL, self.path)
                        self.assertEqual(request.call_count, 1)
                    self.assertTrue(response.closed)
        self.sleep.assert_not_called()

    def test_legacy_socket_timeout_type_is_also_supported(self):
        class LegacyTimeout(OSError): pass
        with patch.object(recipe.socket, 'timeout', LegacyTimeout):
            with patch.object(recipe, 'urlopen', side_effect=[URLError(LegacyTimeout('fixture')), Response([b'ok'])]) as request:
                recipe.download(URL, self.path)
                self.assertEqual(request.call_count, 2)
        self.assertEqual(self.path.read_bytes(), b'ok')
        self.sleep.assert_called_once_with(1)


if __name__ == '__main__': unittest.main()
