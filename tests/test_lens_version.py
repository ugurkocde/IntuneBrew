"""Match Lens's catalog version to its checksum-verified arm64 bundle."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
SPEC = importlib.util.spec_from_file_location('lens_collector', ROOT / '.github/scripts/collect_app_info.py')
COLLECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECTOR)
SOURCE = 'https://formulae.brew.sh/api/cask/lens.json'
VERSION = '2026.10.261408'
BUNDLE = 'com.electron.kontena-lens'
SHA = '784abc1d3ec6fe87aab5f8f6896f7b749edb641322ad8e173c34b17862c97418'


def cask(version=VERSION, url=None):
    return {'name': ['Lens'], 'desc': 'Kubernetes IDE',
            'homepage': 'https://k8slens.dev/', 'version': version,
            'url': url or f'https://api.k8slens.dev/binaries/Lens-{version}-latest-arm64.dmg',
            'sha256': SHA, 'artifacts': [{'app': ['Lens.app']}]}


class LensVersionTests(unittest.TestCase):
    def tearDown(self):
        COLLECTOR.cask_cache.clear()

    def collect(self, value, source=SOURCE):
        COLLECTOR.cask_cache[source] = value
        # The collection loop recovers Lens's known ID from its existing entry.
        # Keep that identity fixed while testing the version transformation.
        with patch.object(COLLECTOR, 'find_bundle_id', return_value=BUNDLE):
            return COLLECTOR.get_homebrew_app_info(source)

    def test_verified_release_retains_artifact_and_application_identity(self):
        value = cask()
        with patch.object(COLLECTOR.requests, 'get') as get:
            result = self.collect(value)
        self.assertEqual(result['version'], '2026.10.261408-latest')
        self.assertEqual(result['name'], 'Lens')
        self.assertEqual(result['bundleId'], BUNDLE)
        self.assertEqual(result['homebrew_cask'], 'lens')
        self.assertEqual(result['url'], value['url'])
        self.assertEqual(result['vendor_url'], value['url'])
        self.assertEqual(result['sha'], SHA)
        self.assertEqual(result['fileName'], 'Lens-2026.10.261408-latest-arm64.dmg')
        self.assertEqual(value['version'], VERSION)
        get.assert_not_called()

    def test_timestamp_changes_retain_release_identity(self):
        for version in ['2026.10.121159', '2026.11.050901', '2027.01.011030']:
            with self.subTest(version=version):
                self.assertEqual(self.collect(cask(version))['version'], version + '-latest')

    def test_unproven_versions_are_refused_before_download(self):
        for version in [VERSION+'-latest', VERSION+',1', VERSION+'_1',
                        VERSION+' ', VERSION+'\n', '2026.13.261408', '2026.00.261408',
                        '2026.10.26140', '2026.10.2614080', '２０２６.10.261408',
                        '2026.10.٢٦١٤٠٨', 'latest', '1.2.3']:
            with self.subTest(version=version), patch.object(COLLECTOR.requests, 'get') as get:
                with self.assertRaisesRegex(ValueError, 'Lens release version or URL'):
                    self.collect(cask(version))
                get.assert_not_called()

    def test_unproven_channel_architecture_or_url_is_refused(self):
        url = cask()['url']
        for changed in [url.replace('-latest-', '-beta-'), url.replace('arm64', 'x64'),
                        url.replace(VERSION, '2026.10.121159'), url+'?download=1',
                        url.replace('https:', 'http:'), url.replace('api.k8slens.dev', 'example.test'),
                        url+'\n']:
            with self.subTest(url=changed), patch.object(COLLECTOR.requests, 'get') as get:
                with self.assertRaisesRegex(ValueError, 'Lens release version or URL'):
                    self.collect(cask(url=changed))
                get.assert_not_called()

    def test_other_casks_keep_their_existing_version_rules(self):
        for token, original, expected in [('example-app', '1.2.3,4', '1.2.3'),
                                          ('example-app', '1.2.3_4', '1.2.3'),
                                          ('rstudio', '2026.10.0,123', '2026.10.0+123'),
                                          ('keeper-password-manager', '18.7.0', '18.7.0')]:
            with self.subTest(token=token, version=original):
                source = f'https://formulae.brew.sh/api/cask/{token}.json'
                self.assertEqual(self.collect(cask(original), source)['version'], expected)

    def test_dmg_guard_accepts_bundle_version_and_rejects_old_stripped_version(self):
        app = self.collect(cask())
        with patch.object(COLLECTOR.shutil, 'which', return_value='/usr/bin/hdiutil'), \
                patch.object(COLLECTOR, 'read_dmg_bundle_version', return_value=VERSION+'-latest'):
            COLLECTOR.verify_dmg_bundle_version(app, '2026.10.121159')
            app['version'] = VERSION
            with self.assertRaisesRegex(RuntimeError, 'Intune rejects that mismatch'):
                COLLECTOR.verify_dmg_bundle_version(app, '2026.10.121159')


if __name__ == '__main__':
    unittest.main()
