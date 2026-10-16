"""Keep Warp downloads usable by ordinary clients and pinned to the cask build."""
import hashlib
import importlib.util
import pathlib
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
    def tearDown(self):
        COLLECTOR.cask_cache.clear()

    def test_catalog_uses_full_artifact_version_and_upstream_checksum(self):
        COLLECTOR.cask_cache[SOURCE] = cask()
        reply = response()
        with patch.object(COLLECTOR.requests, 'get', return_value=reply) as get:
            result = COLLECTOR.get_homebrew_app_info(SOURCE)
        self.assertEqual(result['url'], URL)
        self.assertEqual(result['vendor_url'], URL)
        self.assertEqual(result['version'], VERSION.split('_')[0])
        self.assertEqual(result['sha'], SHA)
        self.assertTrue(result['fileName'].endswith('.dmg'))
        get.assert_called_once_with(URL, headers={'User-Agent': COLLECTOR.DOWNLOAD_USER_AGENTS[0]},
            timeout=COLLECTOR.DOWNLOAD_TIMEOUT, stream=True)
        reply.close.assert_called_once()

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


if __name__ == '__main__':
    unittest.main()
