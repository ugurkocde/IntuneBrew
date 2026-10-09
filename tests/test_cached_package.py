import hashlib
import functools
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest.mock import Mock, call, patch

from urllib3.exceptions import ProtocolError

SPEC = importlib.util.spec_from_file_location('reuse_cached_package', pathlib.Path(__file__).parents[1] / '.github/scripts/reuse_cached_package.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
URL = 'https://intunebrew.blob.core.windows.net/pkg/app_2.pkg'
PAYLOAD = b'xar!' + b'fixture package content' * 4


def session_for(payload=PAYLOAD, error=None):
    response = Mock()
    response.raise_for_status.side_effect = error
    response.iter_content.return_value = [payload]
    session = Mock()
    session.get.return_value.__enter__ = Mock(return_value=response)
    session.get.return_value.__exit__ = Mock(return_value=False)
    return session


def interrupted_payload():
    yield PAYLOAD[:32]
    raise MODULE.requests.exceptions.ChunkedEncodingError('stream interrupted')


class CachedPackageTests(unittest.TestCase):
    def test_vendor_archive_hash_is_never_reused(self):
        original = {'version': '2', 'url': 'https://vendor.invalid/app.zip', 'fileName': 'app.zip', 'sha': 'a' * 64}
        current = {**original, 'type': 'app'}
        session = session_for()
        result = MODULE.update_cached_package(current, original, URL, session)
        self.assertEqual(result['sha'], hashlib.sha256(PAYLOAD).hexdigest())
        self.assertEqual(result['url'], URL)
        self.assertEqual(current['url'], original['url'])
        session.get.assert_called_once()

    def test_known_package_hash_is_reused_instead_of_collector_hash(self):
        previous = {'version': '2', 'url': URL, 'fileName': 'app_2.pkg', 'sha': 'b' * 64}
        current = {**previous, 'url': 'https://vendor.invalid/app.zip', 'sha': 'a' * 64}
        session = session_for()
        result = MODULE.update_cached_package(current, previous, URL, session)
        self.assertEqual(result['sha'], 'b' * 64)
        session.get.assert_called_once_with(URL, headers={"Range": "bytes=0-27"}, stream=True, timeout=(20, 120))

    def test_known_checksum_cannot_hide_invalid_archive(self):
        previous = {"version": "2", "url": URL, "fileName": "app_2.pkg", "sha": "b" * 64}
        with self.assertRaises(ValueError):
            MODULE.update_cached_package(previous, previous, URL, session_for(b"AppleDouble metadata" * 4))

    def test_failed_prior_publication_or_changed_version_downloads_package(self):
        previous = {'version': '1', 'url': URL.replace('_2', '_1'), 'fileName': 'app_1.pkg', 'sha': 'b' * 64}
        result = MODULE.update_cached_package({'version': '2'}, previous, URL, session_for())
        self.assertEqual(result['sha'], hashlib.sha256(PAYLOAD).hexdigest())

    def test_invalid_or_failed_download_is_never_published(self):
        for session in [session_for(b'HTML error page'), session_for(b'xar!'), session_for(error=RuntimeError('download failed'))]:
            with self.assertRaises((ValueError, RuntimeError)):
                MODULE.update_cached_package({'version': '2'}, {}, URL, session)

    def test_trusted_range_retries_connection_failure(self):
        previous = {'version': '2', 'url': URL, 'fileName': 'app_2.pkg', 'sha': 'b' * 64}
        session = session_for()
        response = session.get.return_value
        reset = ProtocolError('Connection aborted.', ConnectionResetError(54, 'Connection reset by peer'))
        session.get.side_effect = [MODULE.requests.exceptions.ConnectionError(reset), response]
        sleep = Mock()
        result = MODULE.update_cached_package(previous, previous, URL, session, sleep)
        self.assertEqual(result['sha'], previous['sha'])
        self.assertEqual(session.get.call_args_list, [
            call(URL, headers={'Range': 'bytes=0-27'}, stream=True, timeout=(20, 120))
        ] * 2)
        sleep.assert_called_once_with(1)

    def test_interrupted_full_download_restarts_checksum(self):
        session = session_for()
        response = session.get.return_value.__enter__.return_value
        response.iter_content.side_effect = [interrupted_payload(), [PAYLOAD]]
        sleep = Mock()
        result = MODULE.update_cached_package({'version': '2'}, {}, URL, session, sleep)
        self.assertEqual(result['sha'], hashlib.sha256(PAYLOAD).hexdigest())
        self.assertEqual(session.get.call_count, 2)
        self.assertEqual(session.get.return_value.__exit__.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_transient_failures_are_bounded_and_do_not_mutate_manifests(self):
        current = {'version': '2', 'url': 'https://vendor.invalid/app.zip', 'sha': 'a' * 64}
        previous = {'version': '1', 'sha': 'b' * 64}
        for exception in (MODULE.requests.exceptions.ConnectionError,
                          MODULE.requests.exceptions.Timeout,
                          MODULE.requests.exceptions.ChunkedEncodingError):
            with self.subTest(exception=exception.__name__):
                error = exception('transient failure')
                session = session_for()
                session.get.side_effect = error
                sleep = Mock()
                with self.assertRaises(exception) as raised:
                    MODULE.update_cached_package(current, previous, URL, session, sleep)
                self.assertIs(raised.exception, error)
                self.assertEqual(session.get.call_count, 3)
                self.assertEqual(sleep.call_args_list, [call(1), call(2)])
                self.assertEqual(current, {'version': '2', 'url': 'https://vendor.invalid/app.zip', 'sha': 'a' * 64})
                self.assertEqual(previous, {'version': '1', 'sha': 'b' * 64})

    def test_certificate_http_and_integrity_failures_are_not_retried(self):
        sessions = [session_for(error=MODULE.requests.exceptions.SSLError('certificate failure')),
                    session_for(error=MODULE.requests.exceptions.HTTPError('403')),
                    session_for(error=MODULE.requests.exceptions.HTTPError('503')),
                    session_for(b'HTML error page'), session_for(b'xar!')]
        for session in sessions:
            with self.subTest(session=session):
                sleep = Mock()
                with self.assertRaises((MODULE.requests.exceptions.SSLError,
                                        MODULE.requests.exceptions.HTTPError, ValueError)):
                    MODULE.update_cached_package({'version': '2'}, {}, URL, session, sleep)
                session.get.assert_called_once()
                sleep.assert_not_called()

    def test_invalid_url_never_downloads_or_retries(self):
        session, sleep = Mock(), Mock()
        with self.assertRaises(ValueError):
            MODULE.update_cached_package({}, {}, 'https://vendor.invalid/app.pkg', session, sleep)
        session.get.assert_not_called()
        sleep.assert_not_called()

    def test_failed_cli_verification_preserves_file_and_leaves_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            apps = pathlib.Path(directory) / 'Apps'
            apps.mkdir()
            manifest = apps / 'app.json'
            contents = json.dumps({'version': '2', 'url': 'https://vendor.invalid/app.zip'}) + '\n'
            manifest.write_text(contents)
            error = MODULE.requests.exceptions.ConnectionError('connection reset')
            sleep = Mock()
            verifier = functools.partial(MODULE.update_cached_package, sleep=sleep)
            with patch('sys.argv', ['reuse_cached_package.py', str(manifest), URL]), \
                    patch.object(MODULE.subprocess, 'run', return_value=Mock(returncode=1)), \
                    patch.object(MODULE.requests, 'get', side_effect=error) as get, \
                    patch.object(MODULE, 'update_cached_package', verifier):
                with self.assertRaises(MODULE.requests.exceptions.ConnectionError):
                    MODULE.main()
            self.assertEqual(get.call_count, 3)
            self.assertEqual(sleep.call_args_list, [call(1), call(2)])
            self.assertEqual(manifest.read_text(), contents)
            self.assertFalse(manifest.with_suffix('.json.tmp').exists())
