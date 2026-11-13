"""Actual font publication function and workflow route; all external writes stubbed."""
import ast
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
code = (ROOT / '.github/scripts/package_cli.sh').read_text().split("<<'FONT_PUBLISH_PY'\n", 1)[1].split('\nFONT_PUBLISH_PY', 1)[0]
tree = ast.parse(code); namespace = {}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))],
                        type_ignores=[]), 'actual-font-publication', 'exec'), namespace)


class FontPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); (self.root / 'Apps').mkdir()
        (self.root / '.github/scripts').mkdir(parents=True)
        shutil.copytree(ROOT / 'lib', self.root / 'lib')
        self.script = self.root / '.github/scripts/package_cli.sh'; self.script.write_text('fixture')
        self.path = self.root / 'Apps/example_fonts.json'
        self.data = {'type': 'app', 'version': '1', 'bundleId': 'com.intunebrew.example_fonts',
                     'url': 'https://vendor.invalid/font.zip', 'fileName': 'old.pkg', 'sha': 'a' * 64,
                     'font_payload': {'source_url': 'https://vendor.invalid/font.zip',
                                      'archive_sha256': 'b' * 64, 'files': ['Font.ttf']}}
        self.path.write_text(json.dumps(self.data)); self.original = self.path.read_bytes()
        self.package = b'xar!' + b'fixture package bytes' * 4
        self.upload_code = 0; self.emit_package = True; self.calls = []

    def fake_run(self, command, **kwargs):
        self.calls.append(command)
        if command[0] == 'bash':
            self.assertEqual(command[1], str(self.script))
            if self.emit_package: (Path(command[3]) / 'example_fonts_1.pkg').write_bytes(self.package)
            return subprocess.CompletedProcess(command, 0)
        self.assertEqual(command[:4], ['az', 'storage', 'blob', 'upload'])
        self.assertEqual(command[command.index('--overwrite') + 1], 'false')
        return subprocess.CompletedProcess(command, self.upload_code)

    def publish(self, existing=None):
        response = io.BytesIO(self.package if existing is None else existing); response.status = 200
        with mock.patch.object(namespace['subprocess'], 'run', side_effect=self.fake_run), \
             mock.patch.object(namespace['urllib'].request, 'urlopen', return_value=response) as request:
            namespace['publish_font']('example_fonts', self.path, self.script)
            return request.call_count

    def test_content_addressed_nested_path_passes_catalog_without_deleting(self):
        self.assertEqual(self.publish(), 0)
        current = json.loads(self.path.read_text()); digest = hashlib.sha256(self.package).hexdigest()
        self.assertEqual(current['url'], 'https://intunebrew.blob.core.windows.net/pkg/fonts/example_fonts/' + digest + '/example_fonts_1.pkg')
        self.assertEqual(current['fileName'], 'example_fonts_1.pkg')
        self.assertEqual(current['sha'], digest)
        self.assertEqual(current['packaging_recipe'], 'font-pkg-v1')
        self.assertEqual(current['packageIdentifier'], current['bundleId'])
        self.assertFalse(any('delete' in call for call in self.calls))
        sys.path.insert(0, str(ROOT / '.github/scripts')); import publish_catalog
        self.assertTrue(publish_catalog.valid_package(current))

    def test_existing_content_is_accepted_only_after_complete_hash(self):
        self.upload_code = 1
        self.assertEqual(self.publish(), 1)
        self.assertNotEqual(self.path.read_bytes(), self.original)

    def test_upload_failure_or_existing_hash_mismatch_holds_original_metadata(self):
        self.upload_code = 1
        with self.assertRaises(ValueError): self.publish(b'xar!' + b'wrong' * 20)
        self.assertEqual(self.path.read_bytes(), self.original)
        with mock.patch.object(namespace['subprocess'], 'run', side_effect=self.fake_run), \
             mock.patch.object(namespace['urllib'].request, 'urlopen', side_effect=OSError('offline')):
            with self.assertRaises(OSError): namespace['publish_font']('example_fonts', self.path, self.script)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_missing_package_never_uploads_or_rewrites(self):
        self.emit_package = False
        with self.assertRaises(ValueError): self.publish()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.path.read_bytes(), self.original)


@unittest.skipUnless(shutil.which('jq'), 'Workflow jq dependency unavailable')
class FontWorkflowRouteTests(unittest.TestCase):
    def test_presence_routes_reuse_rebuild_hold_and_malformed_data_without_fallthrough(self):
        workflow = (ROOT / '.github/workflows/build-app-packages.yml').read_text()
        branch = textwrap.dedent(workflow.split('            # Font manifests never enter', 1)[1].split('            # List existing versions', 1)[0])
        # Restore the first comment fragment, then execute the exact branch.
        branch = '# Font manifests never enter' + branch
        for payload, cache_code, build_code, expected, counts in [('valid', 0, 0, 'font-cache', 'success 1 failed 0'),
                ('valid', 10, 0, 'font-cache\nfont-build', 'success 1 failed 0'), ('hostile', 10, 1, 'font-cache\nfont-build', 'success 0 failed 1'),
                (None, 1, 0, 'font-cache', 'success 0 failed 1'), ('absent', 0, 0, 'generic', 'success 0 failed 0')]:
            with self.subTest(payload=payload, cache=cache_code), tempfile.TemporaryDirectory() as folder:
                root = Path(folder); (root / 'Apps').mkdir(); (root / 'bin').mkdir(); (root / '.github/scripts').mkdir(parents=True)
                data = {} if payload == 'absent' else {'font_payload': payload}
                (root / 'Apps/example_fonts.json').write_text(json.dumps(data))
                trace = root / 'trace'
                (root / 'bin/python').write_text('#!/bin/bash\necho font-cache >> "$TRACE"\nexit ' + str(cache_code) + '\n')
                (root / 'bin/python').chmod(0o755)
                (root / '.github/scripts/package_cli.sh').write_text('#!/bin/bash\necho font-build >> "$TRACE"\nexit ' + str(build_code) + '\n')
                script = root / 'route.sh'
                script.write_text('set -euo pipefail\nSUCCESSFUL_APPS=()\nFAILED_APPS=()\nERROR_LOG=()\nfor app_name in example_fonts; do\n' + branch + '\necho generic >> "$TRACE"\ndone\n' + 'echo "success ${#SUCCESSFUL_APPS[@]} failed ${#FAILED_APPS[@]}" > "$TRACE.state"\n')
                import os
                result = subprocess.run(['bash', str(script)], env={**os.environ, 'WORKSPACE_DIR': str(root),
                    'TRACE': str(trace), 'PATH': str(root / 'bin') + ':' + os.environ['PATH']}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(trace.read_text().strip(), expected)
                self.assertEqual(Path(str(trace) + '.state').read_text().strip(), counts)


if __name__ == '__main__': unittest.main()
