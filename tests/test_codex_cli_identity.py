"""The CLI request must not replace the desktop app's catalog identity."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
spec = importlib.util.spec_from_file_location('codex_identity_collector', ROOT / '.github/scripts/collect_app_info.py')
collector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = collector
spec.loader.exec_module(collector)


class CodexIdentityTests(unittest.TestCase):
    def test_cli_request_preserves_desktop_file(self):
        url = 'https://formulae.brew.sh/api/cask/codex.json'
        collector.cask_cache[url] = {
            'token': 'codex', 'name': ['Codex'], 'desc': 'Command line coding agent',
            'version': '0.167.2', 'homepage': 'https://example.test/codex',
            'url': 'https://example.test/codex-package-aarch64-apple-darwin.tar.gz',
            'sha256': 'a' * 64, 'artifacts': [{'binary': ['bin/codex']}],
        }
        try:
            info = collector.get_homebrew_app_info(url, needs_packaging=True)
            self.assertEqual(info['name'], 'Codex CLI')
            self.assertEqual(info['homebrew_cask'], 'codex')
            self.assertIsNone(info['bundleId'])
            with tempfile.TemporaryDirectory() as temporary:
                apps = Path(temporary)
                desktop = apps / 'codex.json'
                prior = json.dumps({'name': 'Codex', 'homebrew_cask': 'codex-app',
                                    'bundleId': 'com.openai.codex', 'deprecated': True}).encode()
                desktop.write_bytes(prior)
                target = apps / (collector.sanitize_filename(info['name']) + '.json')
                self.assertEqual(target.name, 'codex_cli.json')
                self.assertTrue(collector.claim_app_file(str(target), info['homebrew_cask']))
                target.write_text(json.dumps(info))
                self.assertEqual(desktop.read_bytes(), prior)
                self.assertEqual(json.loads(target.read_text())['homebrew_cask'], 'codex')
        finally:
            collector.cask_cache.pop(url, None)


if __name__ == '__main__':
    unittest.main()
