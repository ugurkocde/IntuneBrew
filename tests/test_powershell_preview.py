"""Preview publication and cleanup must preserve stable PowerShell."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import add_new_app
import pending_requests
import publish_catalog
from test_collect_app_info import collect_app_info as collector, CountingSession, cask_response, run_collector

SPEC = importlib.util.spec_from_file_location('preview_uninstall', ROOT / '.github/scripts/generate_uninstall_scripts.py')
uninstall = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(uninstall)

TOKEN = 'powershell@preview'
URL = 'https://formulae.brew.sh/api/cask/powershell@preview.json'
PAYLOAD = dict(token=TOKEN, name=['PowerShell'], version='7.7.0-rc.1',
               url='https://example.invalid/powershell-preview.pkg', sha256='a'*64,
               desc='PowerShell Preview', homepage='https://example.invalid/',
               artifacts=[{'uninstall': [{'pkgutil': 'com.microsoft.powershell-preview'}]}])


class PreviewCatalogTests(unittest.TestCase):
    def test_collector_creates_preview_without_touching_stable(self):
        session = CountingSession({URL: cask_response(PAYLOAD)})
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'Apps'
            folder.mkdir()
            stable = folder / 'powershell.json'
            before = b'{"name":"PowerShell","version":"7.5.4","homebrew_cask":"powershell","deprecated":true}\n'
            stable.write_bytes(before)
            with run_collector(directory, [], session=session):
                with patch.object(collector, 'pkg_urls', [URL]):
                    collector.main()
            preview = json.loads((folder / 'powershell_preview.json').read_text())
            self.assertEqual(stable.read_bytes(), before)
            self.assertEqual(preview['name'], 'PowerShell Preview')
            self.assertEqual(preview['homebrew_cask'], TOKEN)
            self.assertEqual(preview['bundleId'], 'com.microsoft.powershell-preview')
            self.assertEqual(preview['version'], '7.7.0-rc.1')
            self.assertEqual(preview['type'], 'pkg')
            self.assertEqual(collector.filename_collisions, [])
            self.assertEqual(collector.collection_failures, [])

    def test_preview_deprecation_never_selects_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            stable = Path(directory) / 'powershell.json'
            preview = Path(directory) / 'powershell_preview.json'
            stable.write_text(json.dumps(dict(name='PowerShell', homebrew_cask='powershell')))
            before = stable.read_bytes()
            preview.write_text(json.dumps(dict(name='PowerShell Preview', homebrew_cask=TOKEN)))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(collector.mark_app_deprecated(directory, display_name='PowerShell', cask_token=TOKEN, reason='disabled'))
            self.assertEqual(stable.read_bytes(), before)
            self.assertTrue(json.loads(preview.read_text())['deprecated'])

    def test_deprecated_upstream_uses_preview_identity(self):
        with patch.dict(collector.cask_cache, {URL: dict(PAYLOAD, deprecated=True)}, clear=True):
            with self.assertRaises(collector.CaskUnavailableError) as result:
                collector.get_homebrew_app_info(URL)
        self.assertEqual(result.exception.display_name, 'PowerShell Preview')

    def test_intake_reports_distinct_preview_name(self):
        self.assertEqual(add_new_app.cask_display_name(PAYLOAD, TOKEN), 'PowerShell Preview')
        self.assertEqual(add_new_app.cask_display_name(dict(token='powershell', name=['PowerShell']), 'powershell'), 'PowerShell')
        with patch.object(add_new_app, 'get_homebrew_cask_list', return_value=[PAYLOAD]):
            results = add_new_app.search_homebrew_casks('PowerShell Preview')
        self.assertEqual(results[0][0], TOKEN)
        self.assertEqual(results[0][2], 0.95)
        self.assertEqual(add_new_app.cask_display_name(results[0][1], TOKEN), 'PowerShell Preview')

    def test_publisher_and_resolver_require_preview_source_and_index(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            folder = Path('Apps'); folder.mkdir()
            stable = dict(name='PowerShell', version='7.5.4', homebrew_cask='powershell', deprecated=True)
            preview = dict(name='PowerShell Preview', version='7.7.0-rc.1', homebrew_cask=TOKEN, type='pkg', url=PAYLOAD['url'], sha='a'*64)
            (folder/'powershell.json').write_text(json.dumps(stable))
            (folder/'powershell_preview.json').write_text(json.dumps(preview))
            Path('supported_apps.json').write_text(json.dumps({'powershell': 'stable'}))
            self.assertNotIn(TOKEN, pending_requests.catalog_entries())
            old = json.dumps(dict(preview, version='7.7.0-preview.1')).encode()
            with patch.object(publish_catalog, 'original', side_effect=lambda p: old if p.stem == 'powershell_preview' else json.dumps(stable).encode()), contextlib.redirect_stdout(io.StringIO()):
                publish_catalog.publish(scope=TOKEN)
            live = pending_requests.catalog_entries()
            self.assertEqual(live[TOKEN]['file'], 'Apps/powershell_preview.json')
            self.assertEqual(live[TOKEN]['name'], 'PowerShell Preview')
            self.assertNotIn('powershell', live)
            feed = json.loads(Path('latest-updates.json').read_text())
            self.assertTrue(feed['updates'][0]['logoUrl'].endswith('/powershell_preview.png'))
            self.assertTrue((ROOT/'Logos/powershell_preview.png').is_file())
            Path('.github').mkdir()
            Path('.github/pending-requests.json').write_text(json.dumps([dict(issue=373, casks=[TOKEN], recorded_at='2026-11-05T00:00:00Z')]))
            with contextlib.redirect_stdout(io.StringIO()): pending_requests.resolve()
            notice = json.loads(Path('pending-notifications.json').read_text())[0]
            self.assertEqual(notice['kind'], 'live')
            self.assertEqual(notice['apps'][0]['file'], 'Apps/powershell_preview.json')


class PreviewUninstallTests(unittest.TestCase):
    def generated(self):
        with patch.object(uninstall, 'get_brew_app_info', side_effect=AssertionError('Shared zap paths must not be fetched')):
            paths = uninstall.get_local_uninstall_paths('PowerShell Preview', dict(homebrew_cask=TOKEN))
        return uninstall.generate_uninstall_script('PowerShell Preview', paths)

    def run_sandbox(self, scenario='normal'):
        # Only execute a rebased copy. Every deletion target is inside this temp root.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            preview = root/'usr/local/microsoft/powershell/7-preview'
            stable = root/'usr/local/microsoft/powershell/7'
            app = root/'Applications/PowerShell-preview.app'
            alias = root/'usr/local/bin/pwsh-preview'
            for path in [preview, stable, app/'Contents', alias.parent, root/'home/.config/PowerShell']:
                path.mkdir(parents=True, exist_ok=True)
            (preview/'pwsh').write_text('preview')
            (stable/'pwsh').write_text('stable')
            (root/'home/.config/PowerShell/profile.ps1').write_text('shared profile')
            (app/'Contents/Info.plist').write_text('fixture')
            if scenario == 'replaced-payload':
                (preview/'pwsh').unlink(); preview.rmdir(); preview.symlink_to(stable, target_is_directory=True)
            alias.symlink_to('../microsoft/powershell/7-preview/pwsh' if scenario != 'foreign-link' else '../microsoft/powershell/7/pwsh')
            fake = root/'fakes'; fake.mkdir()
            scripts = {
                'pkgutil': '#!/bin/bash\nif [ "$1" = --pkg-info ]; then exit '+('1' if scenario == 'no-receipt' else '0')+'; fi\necho "$*" >> "'+str(root/'forgot')+'"\n',
                'PlistBuddy': '#!/bin/bash\necho '+('foreign.bundle' if scenario == 'foreign-bundle' else 'com.microsoft.powershell-preview')+'\n',
                'pkill': '#!/bin/bash\nexit 1\n',
            }
            for name, body in scripts.items():
                p=fake/name; p.write_text(body); p.chmod(0o700)
            text = self.generated().replace('"$EUID"', '0')
            for prefix in ['/usr/local/', '/Applications/']:
                text = text.replace(prefix, str(root)+prefix)
            for binary in ['/usr/sbin/pkgutil', '/usr/libexec/PlistBuddy', '/usr/bin/pkill']:
                text = text.replace(binary, str(fake/Path(binary).name))
            script=root/'uninstall.sh';script.write_text(text)
            result=subprocess.run(['/bin/bash', str(script)], capture_output=True, text=True)
            self.assertEqual((stable/'pwsh').read_text(), 'stable')
            self.assertEqual((root/'home/.config/PowerShell/profile.ps1').read_text(), 'shared profile')
            if scenario == 'normal':
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(preview.exists());self.assertFalse(app.exists());self.assertFalse(alias.is_symlink())
                self.assertEqual((root/'forgot').read_text().strip(), '--forget com.microsoft.powershell-preview')
            else:
                self.assertEqual(result.returncode, 0 if scenario == 'no-receipt' else 1, result.stderr)
                self.assertTrue(preview.exists());self.assertTrue(app.exists());self.assertTrue(alias.is_symlink())
                self.assertFalse((root/'forgot').exists())

    def test_cleanup_removes_only_preview(self): self.run_sandbox()
    def test_foreign_command_refuses_cleanup(self): self.run_sandbox('foreign-link')
    def test_foreign_app_refuses_cleanup(self): self.run_sandbox('foreign-bundle')
    def test_replaced_payload_refuses_cleanup(self): self.run_sandbox('replaced-payload')
    def test_missing_receipt_preserves_everything(self): self.run_sandbox('no-receipt')
