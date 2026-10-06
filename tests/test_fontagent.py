import json
import os
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))
import collect_fontagent as fontagent
import pending_requests


class FontAgentTests(unittest.TestCase):
    def test_reads_main_app_not_uninstaller_or_plugin(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'fontagentinstall.pkg/Payload/Applications/FontAgent 10'
            for name, bundle, version in [('FontAgent', fontagent.BUNDLE_ID, '10.2.9'),
                                           ('Uninstaller', 'com.insider.uninstaller', '1.0')]:
                plist = path / f'{name}.app/Contents/Info.plist'
                plist.parent.mkdir(parents=True)
                plist.write_bytes(plistlib.dumps({'CFBundleIdentifier': bundle, 'CFBundleShortVersionString': version}))
            self.assertEqual(fontagent.read_metadata(root), '10.2.9')
            plist = path / 'FontAgent.app/Contents/Info.plist'
            plist.write_bytes(plistlib.dumps({'CFBundleIdentifier': 'wrong', 'CFBundleShortVersionString': '10.2.9'}))
            with self.assertRaises(ValueError):
                fontagent.read_metadata(root)

    def test_missing_payload_fails(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                fontagent.read_metadata(root)

    def test_request_only_resolves_after_vendor_pkg_is_published(self):
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as root:
            try:
                os.chdir(root)
                Path('Apps').mkdir()
                Path('supported_apps.json').write_text(json.dumps({'fontagent': 'catalog-entry'}))
                path = Path('Apps/fontagent.json')
                data = {'name': 'FontAgent', 'custom_source': 'fontagent', 'version': '10.2.9',
                        'type': 'pkg_in_dmg', 'url': fontagent.SOURCE, 'fileName': 'FontAgent.dmg', 'sha': 'a' * 64}
                path.write_text(json.dumps(data))
                self.assertEqual(pending_requests.catalog_entries(), {})
                data.update(url='https://intunebrew.blob.core.windows.net/pkg/fontagent_10.2.9.pkg',
                            fileName='fontagent_10.2.9.pkg')
                path.write_text(json.dumps(data))
                self.assertIn('fontagent', pending_requests.catalog_entries())
            finally:
                os.chdir(previous)
