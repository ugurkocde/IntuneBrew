"""A forced Eclipse primary mirror must not publish a shutdown page."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
spec = importlib.util.spec_from_file_location('eclipse_collector', ROOT / '.github/scripts/collect_app_info.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
BODY = b'eclipse-dmg-fixture' * 9
SHA = hashlib.sha256(BODY).hexdigest()
FILE = '/technology/epp/downloads/release/2026-09/R/eclipse-jee-2026-09-R-macosx-cocoa-aarch64.dmg'
URL = 'https://www.eclipse.org/downloads/download.php?file=' + FILE + '&mirror_id=1'
FIXED = URL.replace('mirror_id=1', 'r=1')


def data():
    return {'version': '4.41,2026-09', 'url': URL, 'sha256': SHA, 'name': ['Eclipse JEE'],
            'desc': 'IDE', 'homepage': 'https://eclipse.org'}


def response(status=200, kind='application/octet-stream', body=BODY):
    result = Mock(status_code=status, headers={'content-type': kind}, url='https://official-mirror.invalid' + FILE)
    result.iter_content.return_value = [body]
    return result


class EclipseTests(unittest.TestCase):
    def tearDown(self):
        C.cask_cache.clear()
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0, 0))

    def test_exact_class_preserves_release_architecture_and_checksum(self):
        for package, arch in [('jee', 'aarch64'), ('modeling', 'x86_64')]:
            d = data();d['url'] = URL.replace('eclipse-jee-', 'eclipse-' + package + '-').replace('aarch64', arch)
            d['sha256'] = SHA.upper();source = 'https://formulae.brew.sh/api/cask/eclipse-' + package + '.json'
            C.cask_cache[source] = d;reply = response();reply.iter_content.return_value = [b'', BODY[:8], b'', BODY[8:]]
            with patch.object(C.requests, 'get', return_value=reply) as get:
                result = C.get_homebrew_app_info(source)
            self.assertEqual(result['url'], d['url'].replace('mirror_id=1', 'r=1'))
            self.assertEqual(result['vendor_url'], result['url']);self.assertEqual(result['sha'], SHA)
            self.assertEqual(result['version'], '4.41');self.assertTrue(result['fileName'].endswith('.dmg'))
            self.assertEqual(get.call_args.kwargs['stream'], True);reply.close.assert_called_once()

    def test_ambiguous_or_foreign_artifacts_never_reach_network(self):
        values = [URL.replace('www.eclipse.org', 'evil.invalid'), URL.replace('https:', 'http:'),
                  URL + '&extra=1', URL + '&file=' + FILE, URL + '&mirror_id=1', URL + '#fragment',
                  URL.replace('mirror_id=1', 'mirror_id='), URL.replace('mirror_id=1', 'mirror_id=2'),
                  URL.replace('/technology/epp/', '/elsewhere/'), URL.replace('/R/eclipse-', '/R/../eclipse-'),
                  URL.replace('.dmg', '.zip'), URL.replace('aarch64', 'armv7')]
        cases = [{'url': u} for u in values] + [{'version': None}, {'version': '4.41,2026-06'},
                  {'version': '4.41,2026-09,other'}, {'sha256': 'no_check'}, {'sha256': None}]
        for change in cases:
            d = data();d.update(change)
            with self.subTest(change=change), patch.object(C.requests, 'get') as get:
                with self.assertRaises(ValueError):C.get_eclipse_release_url(d)
                get.assert_not_called()

    def test_html_http_errors_and_partial_responses_do_not_publish(self):
        for status, kind in [(200, 'text/html'), (206, 'application/octet-stream'), (404, 'application/octet-stream'), (200, '')]:
            replies = [response(status, kind) for _ in C.DOWNLOAD_USER_AGENTS]
            with self.subTest(status=status, kind=kind), patch.object(C.requests, 'get', side_effect=replies):
                with self.assertRaisesRegex(ValueError, 'catalog update refused'):C.get_eclipse_release_url(data())
            for r in replies:r.close.assert_called_once()

    def test_binary_mime_cannot_hide_html_or_empty_truncated_wrong_body(self):
        for body in [b'<!DOCTYPE html>Temporary shutdown', b'', BODY[:-1], b'wrong']:
            r = response(body=body)
            with self.subTest(body=body), patch.object(C.requests, 'get', return_value=r) as get:
                with self.assertRaises(ValueError):C.get_eclipse_release_url(data())
                get.assert_called_once();r.close.assert_called_once()

    def test_oversized_header_and_stream_stop_without_retry(self):
        r = response();r.headers['content-length'] = str(C.WARP_MAX_DOWNLOAD_BYTES + 1)
        with patch.object(C.requests, 'get', return_value=r):
            with self.assertRaisesRegex(ValueError, 'size limit'):C.get_eclipse_release_url(data())
        r.iter_content.assert_not_called();r.close.assert_called_once()
        r = response()
        with patch.object(C, 'WARP_MAX_DOWNLOAD_BYTES', 10), patch.object(C.requests, 'get', return_value=r):
            with self.assertRaisesRegex(ValueError, 'size limit'):C.get_eclipse_release_url(data())
        r.close.assert_called_once()

    def test_https_required_after_redirect(self):
        r = response();r.url = 'http://mirror.invalid' + FILE
        with patch.object(C.requests, 'get', return_value=r):
            with self.assertRaisesRegex(ValueError, 'HTTPS'):C.get_eclipse_release_url(data())
        r.close.assert_called_once()

    def test_network_failure_can_fall_back_but_persistent_failure_refuses(self):
        r = response()
        with patch.object(C.requests, 'get', side_effect=[C.requests.Timeout(), r]):
            self.assertEqual(C.get_eclipse_release_url(data()), FIXED)
        with patch.object(C.requests, 'get', side_effect=C.requests.Timeout):
            with self.assertRaises(ValueError):C.get_eclipse_release_url(data())

    def test_one_deadline_restores_signal_and_closes_response(self):
        original = signal.getsignal(signal.SIGALRM);r = response();r.iter_content.side_effect = C._WarpDownloadDeadline()
        with patch.object(C.requests, 'get', return_value=r):
            with self.assertRaisesRegex(ValueError, 'Eclipse download exceeded deadline'):C.get_eclipse_release_url(data())
        self.assertEqual(signal.getsignal(signal.SIGALRM), original);r.close.assert_called_once()

    def test_siblings_and_other_casks_have_no_extra_network(self):
        for token, url in [('eclipse-java', FIXED), ('other', URL), ('visual-paradigm', 'https://vendor.invalid/file.dmg')]:
            d = data();d['url'] = url
            with patch.object(C.requests, 'get') as get:self.assertEqual(C.get_published_download_url(d, token), url)
            get.assert_not_called()

    def test_same_version_refresh_and_failure_preserve_existing_catalog(self):
        source = 'https://formulae.brew.sh/api/cask/eclipse-jee.json'
        for succeeds in [True, False]:
            with self.subTest(succeeds=succeeds), tempfile.TemporaryDirectory() as directory:
                before = os.getcwd()
                try:
                    os.chdir(directory);Path('Apps').mkdir()
                    old = {'name': 'Eclipse JEE', 'version': '4.41', 'url': URL, 'vendor_url': URL,
                           'sha': SHA, 'fileName': 'Eclipse-JEE-4.41.dmg', 'category': 'Developer Tools'}
                    path = Path('Apps/eclipse_jee.json');path.write_text(json.dumps(old))
                    original = path.read_bytes()
                    with contextlib.ExitStack() as stack:
                        for name in ['app_urls', 'pkg_in_pkg_urls', 'pkg_urls', 'pkg_in_dmg_urls', 'custom_scrapers']:
                            stack.enter_context(patch.object(C, name, []))
                        stack.enter_context(patch.object(C, 'homebrew_cask_urls', [source]))
                        stack.enter_context(patch.object(C, 'prefetch_cask_data', Mock()))
                        stack.enter_context(patch.dict(C.cask_cache, {source: data()}, clear=True))
                        stack.enter_context(patch.object(C, 'update_readme_apps', Mock()))
                        stack.enter_context(patch.object(C, 'update_readme_with_latest_changes', Mock()))
                        stack.enter_context(patch.object(C.requests, 'get', return_value=response(body=BODY if succeeds else b'bad')))
                        stack.enter_context(patch.dict(os.environ, {'CATALOG_ALLOW_PARTIAL': '1', 'CATALOG_COLLECTION_REPORT': 'collection-report.json'}))
                        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                        C.main()
                    result = json.loads(path.read_text())
                    if succeeds:
                        self.assertEqual(result['url'], FIXED);self.assertEqual(result['vendor_url'], FIXED)
                        self.assertEqual(result['version'], '4.41');self.assertEqual(result['sha'], SHA)
                        self.assertEqual(result['fileName'], old['fileName']);self.assertEqual(result['category'], old['category'])
                    else:
                        self.assertEqual(path.read_bytes(), original);self.assertNotIn('deprecated', result)
                        self.assertEqual(json.loads(Path('collection-report.json').read_text())['failures'], [{'cask': 'eclipse-jee', 'stage': 'collection'}])
                finally:os.chdir(before)


if __name__ == '__main__':unittest.main()
