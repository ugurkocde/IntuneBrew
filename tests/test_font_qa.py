"""Exercise the actual embedded receipt verifier without installing any file."""
import ast
import os
from pathlib import Path
import plistlib
import tempfile
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import font_payload
REAL_CHECK_OUTPUT = font_payload.subprocess.check_output
REAL_RUN = font_payload.subprocess.run
code = (ROOT / '.github/scripts/qa-app-test.sh').read_text().split("<<'FONT_QA_PY'\n", 1)[1].split('\nFONT_QA_PY', 1)[0]
tree = ast.parse(code)
namespace = {}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))],
                        type_ignores=[]), 'actual-font-qa-verifier', 'exec'), namespace)
verify = namespace['verify_fonts']


class FontQaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.fonts = self.root / 'Fonts'; self.fonts.mkdir()
        self.data = {'bundleId': 'com.intunebrew.example_fonts', 'version': '3.5.1',
                     'font_payload': {'files': ['nested/Regular Font.ttf', 'Bold.otf']}}
        self.contents = b'\x00\x01\x00\x00' + b'actual synthetic font bytes' * 3
        for name in ['Regular Font.ttf', 'Bold.otf']:
            (self.fonts / name).write_bytes(self.contents); (self.fonts / name).chmod(0o644)
        self.receipt = {'pkg-version': '3.5.1', 'volume': '/', 'install-location': 'Library/Fonts'}
        self.receipt_files = ['Regular Font.ttf', 'Bold.otf']
        self.extra_payload = False; self.scripts = False; self.attributes = []

    def check_output(self, command, **kwargs):
        if command[:2] == ['pkgutil', '--pkg-info-plist']:
            return plistlib.dumps(self.receipt)
        if command[0] == 'cksum': return REAL_CHECK_OUTPUT(command, **kwargs)
        if command[0] == 'xattr': return '\n'.join(self.attributes)
        self.assertEqual(command[:2], ['pkgutil', '--files'])
        return '\n'.join(self.receipt_files) + '\n'

    def expand(self, command, **kwargs):
        if command[0] == 'cksum': return REAL_RUN(command, **kwargs)
        self.assertIn(command[:2], [['pkgutil', '--expand-full'], ['pkgutil', '--expand']])
        if command[1] == '--expand': return
        root = Path(command[-1]); root.mkdir(); (root / 'Payload').mkdir()
        for name in ['Regular Font.ttf', 'Bold.otf']:
            (root / 'Payload' / name).write_bytes(self.contents)
        if self.extra_payload: (root / 'Payload/extra.ttf').write_bytes(self.contents)
        if self.scripts: (root / 'Scripts').mkdir()
        (root / 'PackageInfo').write_text('<pkg-info identifier="com.intunebrew.example_fonts" version="3.5.1" install-location="/Library/Fonts"/>')

    def run_verify(self):
        real_lstat = Path.lstat
        def runner_ownership(path):
            # Fixture bytes/modes are real, root ownership is only simulated.
            result = real_lstat(path)
            if path.parent == self.fonts:
                values = list(result); values[4] = values[5] = 0; return os.stat_result(values)
            return result
        with mock.patch.object(namespace['subprocess'], 'check_output', side_effect=self.check_output), \
             mock.patch.object(namespace['subprocess'], 'run', side_effect=self.expand), \
             mock.patch.object(Path, 'lstat', runner_ownership), \
             mock.patch.object(font_payload, 'inspect_component') as inspect:
            result = verify(self.data, self.root / 'fixture.pkg', self.fonts)
            inspect.assert_called_once()
            self.assertEqual(set(inspect.call_args.args[1]), {'Regular Font.ttf', 'Bold.otf'})
            return result

    def test_receipt_and_actual_file_bytes_succeed_with_honest_scope(self):
        result = self.run_verify()
        self.assertEqual(result['installed_version'], '3.5.1')
        self.assertEqual(result['verify_status'], 'fonts_verified')
        self.assertEqual(result['bundle_id_status'], 'receipt_verified')
        self.assertEqual(result['verification_scope'], 'runner_pkg_receipt_and_files')

    def test_resource_fork_or_finderinfo_hold(self):
        for name in ['com.apple.ResourceFork', 'com.apple.FinderInfo']:
            self.attributes = [name]
            with self.subTest(name=name), self.assertRaises(ValueError): self.run_verify()

    def test_receipt_mismatches_hold(self):
        for key, value in [('pkg-version', '3.5.0'), ('volume', '/Other'), ('install-location', '/usr/local')]:
            prior = self.receipt.copy(); self.receipt[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.run_verify()
            self.receipt = prior
        self.receipt_files.append('other.ttf')
        with self.assertRaises(ValueError): self.run_verify()

    def test_bytes_modes_symlinks_extra_payload_and_scripts_hold(self):
        font = self.fonts / 'Bold.otf'
        font.write_bytes(b'different')
        with self.assertRaises(ValueError): self.run_verify()
        font.write_bytes(self.contents); font.chmod(0o600)
        with self.assertRaises(ValueError): self.run_verify()
        font.chmod(0o644); font.unlink(); font.symlink_to('Regular Font.ttf')
        with self.assertRaises(ValueError): self.run_verify()
        font.unlink(); font.write_bytes(self.contents); font.chmod(0o644)
        self.extra_payload = True
        with self.assertRaises(ValueError): self.run_verify()
        self.extra_payload = False; self.scripts = True
        with self.assertRaises(ValueError): self.run_verify()


if __name__ == '__main__': unittest.main()
