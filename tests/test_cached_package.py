import hashlib
import importlib.util
import pathlib
import unittest
from unittest.mock import Mock

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
