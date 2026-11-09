import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.github/scripts'))
spec = importlib.util.spec_from_file_location('publish_catalog', Path(__file__).resolve().parents[1] / '.github/scripts/publish_catalog.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

class PublicationTests(unittest.TestCase):
    def test_formula_alias_uses_the_complete_published_app_package(self):
        data = dict(name='Azure CLI', version='2.90.0', bundleId='com.example.azurecli', homebrew_formula='azure-cli',
                    packaging_recipe='azure-cli-universal-v1', type='app',
                    fileName='azure_cli_2.90.0.pkg',
                    url='https://intunebrew.blob.core.windows.net/pkg/azure_cli_2.90.0.pkg', sha='a'*64)
        Path('Apps/azure_cli.json').write_text(json.dumps(data))
        publisher.publish()
        self.assertEqual(publisher.source_token(data), 'azure-cli')
        self.assertNotIn('homebrew_cask', data)
        self.assertEqual(json.loads(Path('Formulas/azure-cli.json').read_text()), json.loads(Path('Apps/azure_cli.json').read_text()))

    def test_formula_recipe_without_packaged_type_cannot_replace_legacy_alias(self):
        Path('Formulas').mkdir()
        Path('Formulas/azure-cli.json').write_text('{"previous":true}')
        Path('Apps/azure_cli.json').write_text(json.dumps(dict(name='Azure CLI', version='2.90.0', bundleId='com.example.azurecli', homebrew_formula='azure-cli', packaging_recipe='azure-cli-universal-v1')))
        publisher.publish()
        self.assertEqual(json.loads(Path('Formulas/azure-cli.json').read_text()), {'previous':True})

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = os.getcwd()
        os.chdir(self.temp.name)
        subprocess.run(['git', 'init', '-q'], check=True)
        Path('Apps').mkdir()
        for name in ['healthy', 'broken', 'other']:
            self.write(name, '1')
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-qm', 'baseline'], check=True)
    def tearDown(self):
        os.chdir(self.previous)
        self.temp.cleanup()
    def write(self, name, version, **extra):
        data = dict(name=name, version=version, homebrew_cask=name, bundleId='com.example.' + name)
        data.update(extra)
        Path(f'Apps/{name}.json').write_text(json.dumps(data))
    def test_invalid_bundle_id_update_retains_valid_previous_entry(self):
        for value in [None, '', '   ', 42, False]:
            with self.subTest(value=value):
                self.write('broken', '2', bundleId=value)
                state, _ = publisher.publish()
                self.assertEqual(json.loads(Path('Apps/broken.json').read_text())['version'], '1')
                self.assertEqual(state['failedApps'], [{'app':'broken', 'stage':'bundle ID validation'}])
                self.assertIn('broken', json.loads(Path('supported_apps.json').read_text()))
    def test_new_app_missing_bundle_id_is_omitted(self):
        Path('Apps/new.json').write_text(json.dumps(dict(name='New', version='1')))
        state, _ = publisher.publish()
        self.assertFalse(Path('Apps/new.json').exists())
        self.assertNotIn('new', json.loads(Path('supported_apps.json').read_text()))
        self.assertIn({'app':'new', 'stage':'bundle ID validation'}, state['failedApps'])
    def test_invalid_previous_bundle_id_is_not_published(self):
        self.write('broken', '1', bundleId=None)
        subprocess.run(['git', 'add', 'Apps/broken.json'], check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-qm', 'invalid old entry'], check=True)
        state, _ = publisher.publish()
        self.assertTrue(Path('Apps/broken.json').exists())
        self.assertNotIn('broken', json.loads(Path('supported_apps.json').read_text()))
        self.assertEqual(state['appCount'], 2)
    def test_deprecated_entry_without_bundle_id_stays_excluded(self):
        self.write('broken', '1', deprecated=True, bundleId=None)
        state, _ = publisher.publish()
        self.assertNotIn('broken', json.loads(Path('supported_apps.json').read_text()))
        self.assertEqual(state['status'], 'healthy')
    def test_failed_collection_retains_previous_version_and_healthy_update(self):
        self.write('healthy', '2')
        self.write('broken', '2')
        Path('collection-report.json').write_text(json.dumps({'failures':[{'cask':'broken','stage':'collection'}], 'collisions':[]}))
        state, feed = publisher.publish()
        self.assertEqual(json.loads(Path('Apps/broken.json').read_text())['version'], '1')
        self.assertEqual(state['status'], 'degraded')
        self.assertEqual([u['appName'] for u in feed['updates']], ['healthy'])
    def test_failed_packaging_restores_entry(self):
        self.write('broken', '2')
        Path('packaging-failed-apps.txt').write_text('broken\n')
        publisher.publish()
        self.assertEqual(json.loads(Path('Apps/broken.json').read_text())['version'], '1')
    def test_version_evidence_and_exact_text_refresh_do_not_offer_an_update(self):
        self.write('healthy', '1', sha='c' * 64, url='https://example.invalid/refreshed.dmg')
        Path('collection-report.json').write_text(json.dumps({
            'failures': [], 'collisions': [],
            'versionEvidence': [{'cask': 'healthy', 'action': 'REFRESH',
                                 'relation': 'EXACT', 'observedShort': '1',
                                 'artifactSha256': 'c' * 64, 'verified': True}]}))
        state, feed = publisher.publish()
        self.assertEqual(state['status'], 'healthy')
        self.assertEqual(feed['updates'], [])
        self.assertEqual(json.loads(Path('Apps/healthy.json').read_text())['sha'], 'c' * 64)
    def test_invalid_new_package_is_omitted(self):
        Path('README.md').write_text('Apps_Available-4-blue\n')
        self.write('new', '2', type='app', url='https://vendor.test/app.zip')
        state, _ = publisher.publish()
        self.assertFalse(Path('Apps/new.json').exists())
        self.assertEqual(state['appCount'], 3)
        self.assertIn('Apps_Available-3-blue', Path('README.md').read_text())
    def test_scoped_run_does_not_refresh_full_scan(self):
        Path('catalog-sync.json').write_text(json.dumps({'lastFullSyncAt':'2026-01-01T00:00:00Z','status':'degraded','failedApps':[]}))
        state, _ = publisher.publish('partial')
        self.assertEqual(state['lastFullSyncAt'], '2026-01-01T00:00:00Z')
        self.assertEqual(state['status'], 'degraded')
    def test_package_version_must_match(self):
        data = dict(type='app', version='1.2', fileName='test_1.20.pkg', url='https://intunebrew.blob.core.windows.net/pkg/test_1.20.pkg', sha='a'*64)
        self.assertFalse(publisher.valid_package(data))
