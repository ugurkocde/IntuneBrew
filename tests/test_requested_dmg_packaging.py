"""Requested DMGs without cask bundle IDs must reach actual app packaging."""
import json
from pathlib import Path
import tempfile
import unittest

from test_collect_app_info import (CountingSession, cask_response,
                                  collect_app_info as collector, run_collector)


CASES = {
    'github-copilot-app': ('GitHub Copilot', '1.3.0', '1.3.0'),
    'plezy': ('Plezy', '2.26.0', '2.26.0'),
}


class RequestedDmgPackagingTests(unittest.TestCase):
    def test_requested_sources_have_one_packaging_owner(self):
        for token in CASES:
            with self.subTest(cask=token):
                url = 'https://formulae.brew.sh/api/cask/' + token + '.json'
                self.assertEqual(collector.app_urls.count(url), 1)
                for sources in (collector.homebrew_cask_urls, collector.pkg_urls,
                                collector.pkg_in_pkg_urls, collector.pkg_in_dmg_urls):
                    self.assertNotIn(url, sources)

    def test_missing_cask_bundle_id_does_not_skip_app_packaging(self):
        for token, (name, cask_version, catalog_version) in CASES.items():
            with self.subTest(cask=token), tempfile.TemporaryDirectory() as directory:
                url = 'https://formulae.brew.sh/api/cask/' + token + '.json'
                filename = token + '.dmg'
                payload = {
                    'token': token, 'name': [name], 'desc': 'Fixture app',
                    'version': cask_version, 'homepage': 'https://example.test/',
                    'url': 'https://example.test/' + filename, 'sha256': 'a' * 64,
                    'artifacts': [{'app': [name + '.app']}],
                }
                session = CountingSession({url: cask_response(payload)})
                with run_collector(directory, [], session=session, app_urls=[url]):
                    collector.main()
                app_file = Path(directory) / 'Apps' / (collector.sanitize_filename(name) + '.json')
                result = json.loads(app_file.read_text())
                self.assertEqual(result['name'], name)
                self.assertEqual(result['homebrew_cask'], token)
                self.assertEqual(result['type'], 'app')
                self.assertEqual(result['version'], catalog_version)
                self.assertEqual(result['fileName'], filename)
                self.assertEqual(result['url'], payload['url'])
                self.assertEqual(result['vendor_url'], payload['url'])
                self.assertIsNone(result['bundleId'])
                self.assertNotIn('sha', result)
                self.assertEqual(session.requested, [url])
                self.assertEqual(collector.collection_failures, [])


if __name__ == '__main__':
    unittest.main()
