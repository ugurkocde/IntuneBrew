import importlib.util
import json
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('uninstall_requested', ROOT / '.github/scripts/generate_uninstall_scripts.py')
uninstall = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uninstall)


class RequestedAppEnrichmentTests(unittest.TestCase):
    def test_specific_apps_entrypoint_generates_both_uninstall_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            azure = root / 'azure_cli.json'
            logi = root / 'logitech_options.json'
            azure.write_text(json.dumps(dict(name='Azure CLI', homebrew_formula='azure-cli', packaging_recipe='azure-cli-universal-v1')))
            logi.write_text(json.dumps(dict(name='Logitech Options+', homebrew_cask='logi-options+', packaging_recipe='logi-options-silent-v1')))
            with patch.object(sys, 'argv', ['uninstall', '--output', str(root/'scripts'), '--apps', str(azure), str(logi)]), patch.object(uninstall, 'get_brew_app_info', return_value={'artifacts':[]}), patch.object(uninstall, 'uninstall_dir', str(root/'scripts')):
                uninstall.main()
            self.assertIn('/usr/local/lib/intunebrew/azure_cli', (root/'scripts/uninstall_azure_cli.sh').read_text())
            self.assertIn('/Applications/logioptionsplus.app', (root/'scripts/uninstall_logitech_options.sh').read_text())

    def test_azure_uninstall_uses_its_installed_runtime_without_a_cask_lookup(self):
        data = dict(homebrew_formula='azure-cli', packaging_recipe='azure-cli-universal-v1')
        with patch.object(uninstall, 'get_brew_app_info') as lookup:
            paths = uninstall.get_local_uninstall_paths('Azure CLI', data)
        lookup.assert_not_called()
        self.assertIn('/usr/local/lib/intunebrew/azure_cli', paths)
        self.assertIn('/usr/local/bin/az', paths)
        self.assertIn('PKGUTIL:com.intunebrew.azure_cli', paths)

    def test_logi_cleanup_uses_the_plus_token_and_removes_installed_app_and_staged_installer(self):
        data = dict(homebrew_cask='logi-options+', packaging_recipe='logi-options-silent-v1')
        with patch.object(uninstall, 'get_brew_app_info', return_value={'artifacts':[{'uninstall':[{'launchctl':['com.logi.optionsplus']}]}]}) as lookup:
            paths = uninstall.get_local_uninstall_paths('Logitech Options+', data)
        lookup.assert_called_once_with('Logitech Options+', 'logi-options+')
        self.assertIn('LAUNCHCTL:com.logi.optionsplus', paths)
        self.assertIn('/Applications/logioptionsplus.app', paths)
        self.assertIn('/usr/local/lib/intunebrew/logitech_options', paths)

    def test_bundle_id_enrichment_preserves_runtime_detection_identifiers(self):
        overrides = json.loads((ROOT / '.github/data/bundle-id-overrides.json').read_text())['overrides']
        self.assertEqual(overrides['azure_cli'], 'com.intunebrew.azure_cli')
        self.assertEqual(overrides['logitech_options'], 'com.logi.optionsplus')
