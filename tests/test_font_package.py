"""Build and inspect synthetic font PKGs; never install on the test host."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FONT = b'\x00\x01\x00\x00' + b'synthetic font bytes' * 4


@unittest.skipUnless(sys.platform == 'darwin', 'macOS pkgbuild inspection only')
class FontPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='font-package-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scripts = self.root / '.github/scripts'; self.scripts.mkdir(parents=True)
        (self.root / 'Apps').mkdir(); self.extracted = self.root / 'extracted'; self.extracted.mkdir()
        shutil.copyfile(ROOT / '.github/scripts/package_cli.sh', self.scripts / 'package_cli.sh')
        shutil.copytree(ROOT / 'lib', self.root / 'lib')
        # Copy the fixture archive only. No production network/test override.
        (self.scripts / 'download_vendor.sh').write_text('#!/bin/bash\ncp "$(dirname "$0")/fixture" "$2"\n')
        self.names = ['ttf/Regular Font.ttf', 'Bold.otf']
        self.members = [(n, FONT, 'file') for n in self.names] + [('LICENSE', b'license', 'file')]

    def prepare(self, members=None, zip_archive=False):
        archive = self.scripts / 'fixture'
        if zip_archive:
            with zipfile.ZipFile(archive, 'w') as z:
                for name, data, kind in members or self.members:
                    info = zipfile.ZipInfo(name)
                    info.external_attr = (0o120777 if kind == 'symlink' else 0o100644) << 16
                    z.writestr(info, data)
        else:
            with tarfile.open(archive, 'w:xz') as tar:
                for name, data, kind in members or self.members:
                    info = tarfile.TarInfo(name)
                    if kind in ('symlink', 'hardlink'):
                        info.type = tarfile.SYMTYPE if kind == 'symlink' else tarfile.LNKTYPE; info.linkname = 'Bold.otf'
                    elif kind == 'directory': info.type = tarfile.DIRTYPE
                    else: info.size = len(data)
                    tar.addfile(info, io.BytesIO(data) if kind == 'file' else None)
        self.data = {'name': 'Example Fonts', 'type': 'app', 'version': '3.5.1',
                     'bundleId': 'com.intunebrew.example_fonts', 'font_payload': {
                         'source_url': 'https://example.invalid/fonts.' + ('zip' if zip_archive else 'tar.xz'),
                         'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'files': self.names}}
        self.save()

    def save(self): (self.root / 'Apps/example_fonts.json').write_text(json.dumps(self.data))

    def run_package(self, identifier='com.intunebrew.example_fonts'):
        return subprocess.run(['bash', str(self.scripts / 'package_cli.sh'), 'example_fonts', str(self.extracted),
                               '3.5.1', identifier], capture_output=True, text=True, timeout=30)

    def test_exact_flat_payload_receipt_bom_and_no_scripts_for_tar_and_zip(self):
        for is_zip in (False, True):
            self.prepare(zip_archive=is_zip)
            result = self.run_package(); self.assertEqual(result.returncode, 0, result.stderr)
            package = self.extracted / 'example_fonts_3.5.1.pkg'
            listed = subprocess.check_output(['pkgutil', '--payload-files', str(package)], text=True).splitlines()
            self.assertEqual(set(listed), {'.', './Regular Font.ttf', './Bold.otf'})
            expanded = self.root / ('expanded-' + str(is_zip))
            subprocess.run(['pkgutil', '--expand', str(package), str(expanded)], check=True)
            info = ET.parse(expanded / 'PackageInfo').getroot()
            self.assertEqual((info.get('identifier'), info.get('version'), info.get('install-location')),
                             ('com.intunebrew.example_fonts', '3.5.1', '/Library/Fonts'))
            self.assertFalse(list(expanded.rglob('Scripts')))
            rows = subprocess.check_output(['lsbom', '-p', 'fmug', str(expanded / 'Bom')], text=True).splitlines()
            self.assertIn('.\t40755\t0\t0', rows)
            for line in rows[1:]: self.assertTrue(line.endswith('\t100644\t0\t0'), line)
            package.unlink()

    def test_archive_counterexamples_fail_without_output(self):
        cases = [self.members[:-2] + self.members[-1:], self.members + [('Extra.ttf', FONT, 'file')],
                 [('ttf/Regular Font.ttf', FONT, 'symlink'), self.members[1]],
                 [('ttf/Regular Font.ttf', FONT, 'hardlink'), self.members[1]],
                 [('ttf/Regular Font.ttf', b'', 'directory'), self.members[1]],
                 [('ttf/Regular Font.ttf', b'not a font' * 8, 'file'), self.members[1]],
                 self.members + [('../escape', b'bad', 'file')],
                 self.members + [('Vendor.pkg', b'bad', 'file')],
                 self.members + [('ttf', b'Bold.otf', 'symlink')],
                 self.members + [self.members[0]], self.members + [('Other.ttc', FONT, 'file')]]
        for members in cases:
            with self.subTest(members=[(x[0], x[2]) for x in members]):
                self.prepare(members); result = self.run_package()
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertFalse(list(self.extracted.glob('*.pkg')))
        self.prepare([('ttf/Regular Font.ttf', FONT, 'symlink'), self.members[1]], zip_archive=True)
        self.assertNotEqual(self.run_package().returncode, 0)

    def test_binding_and_ambiguous_caller_tree_fail(self):
        self.prepare(); self.data['font_payload']['archive_sha256'] = '0' * 64; self.save()
        self.assertNotEqual(self.run_package().returncode, 0)

    def test_archive_header_resource_limits_hold_before_payload_copy(self):
        self.prepare(self.members + [(f'readme-{n}', b'', 'file') for n in range(10000)])
        result = self.run_package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('too many entries', result.stderr)
        # A header declaring an enormous file is enough; no enormous fixture.
        info = tarfile.TarInfo('oversized.bin'); info.size = 2 * 1024 ** 3 + 1
        archive = self.scripts / 'fixture'; archive.write_bytes(__import__('lzma').compress(info.tobuf() + b'\0' * 1024))
        self.data['font_payload']['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest(); self.save()
        result = self.run_package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('expanded size bound', result.stderr)
        self.prepare(); self.assertNotEqual(self.run_package('com.example.wrong').returncode, 0)
        (self.extracted / 'Vendor.app').mkdir()
        self.assertNotEqual(self.run_package().returncode, 0)

    def test_no_manifest_preserves_unsupported_cli_default(self):
        (self.root / 'Apps/example_fonts.json').write_text('{}')
        result = self.run_package(); self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.extracted.iterdir()), [])


if __name__ == '__main__': unittest.main()
