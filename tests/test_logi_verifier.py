"""Exercise the real verifier with fixture paths and fake installer commands only."""
import os
from pathlib import Path
import plistlib
import shlex
import subprocess
import sys
import tempfile
import unittest


class LogiVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tools = self.root / 'tools'
        self.tools.mkdir()
        self.app = self.root / 'Applications/logioptionsplus.app'
        self.trace = self.root / 'installer-called'
        self.package = self.root / 'logi.pkg'
        self.archive = self.root / 'vendor.zip'
        self.package.write_bytes(b'fake package')
        self.archive.write_bytes(b'fake vendor archive')
        self.command('python', '#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' "$@"\n')
        self.command('sudo', '#!/bin/sh\nexec "$@"\n')
        self.command('codesign', '#!/bin/sh\nexit "${TEST_SIGNATURE_STATUS:-0}"\n')
        self.command('curl', '''#!/usr/bin/env python3
import json, os, pathlib
counter = pathlib.Path(os.environ['TEST_FEED_COUNT'])
count = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(count))
mode = os.environ['TEST_MODE']
version = '2.8.981479' if mode == 'feed-before-mismatch' else '2.9.994631'
if mode == 'feed-drift' and count > 1: version = '2.10.1'
print(json.dumps({'version': version}))
''')
        installer = self.command('installer', '''#!/usr/bin/env python3
import os, pathlib, plistlib, sys
assert sys.argv[1:] == ['-pkg', os.environ['TEST_PACKAGE'], '-target', '/']
pathlib.Path(os.environ['TEST_TRACE']).touch()
print('RAW_VENDOR_LOG_MUST_NOT_LEAK')
if os.environ['TEST_MODE'] == 'installer-failed': raise SystemExit(7)
plist = pathlib.Path(os.environ['TEST_APP']) / 'Contents/Info.plist'
plist.parent.mkdir(parents=True)
app = {'CFBundleIdentifier': 'com.logi.optionsplus', 'CFBundleVersion': '2.9.994631',
       'CFBundleShortVersionString': '2.9.994631'}
if os.environ['TEST_MODE'] == 'wrong-build': app['CFBundleVersion'] = '2.8.981479'
if os.environ['TEST_MODE'] == 'wrong-short': app['CFBundleShortVersionString'] = '2.8.981479'
if os.environ['TEST_MODE'] == 'wrong-id': app['CFBundleIdentifier'] = 'com.example.other'
with plist.open('wb') as stream: plistlib.dump(app, stream)
''')
        source = Path(__file__).with_name('verify_logi_install.sh').read_text()
        # Only redirect the fixed install location and executable in a temporary copy.
        # All guards, feed checks, timeout and version/signature checks remain intact.
        self.assertEqual(source.count('/Applications/logioptionsplus.app'), 2)
        self.assertEqual(source.count('/usr/sbin/installer'), 1)
        source = source.replace('/Applications/logioptionsplus.app', shlex.quote(str(self.app)))
        source = source.replace('/usr/sbin/installer', str(installer))
        self.assertNotIn('/usr/sbin/installer', source)
        self.verifier = self.root / 'verify.sh'
        self.verifier.write_text(source)

    def command(self, name, source):
        path = self.tools / name
        path.write_text(source)
        path.chmod(0o755)
        return path

    def run_verifier(self, mode='match', **extra):
        env = dict(os.environ, PATH=str(self.tools) + os.pathsep + os.environ.get('PATH', ''),
                   CI='true', GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted', RUNNER_OS='macOS',
                   TEST_APP=str(self.app), TEST_TRACE=str(self.trace), TEST_PACKAGE=str(self.package),
                   TEST_FEED_COUNT=str(self.root / 'feed-count'), TEST_MODE=mode, **extra)
        result = subprocess.run(['bash', str(self.verifier), str(self.package), '2.9.994631', str(self.archive)],
                                env=env, text=True, capture_output=True, timeout=15)
        self.assertNotIn('RAW_VENDOR_LOG_MUST_NOT_LEAK', result.stdout + result.stderr)
        return result

    def test_exact_installed_app_and_stable_feed_pass(self):
        result = self.run_verifier()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.trace.exists())
        self.assertIn('logi-pkg-after', result.stdout)

    def test_rejects_wrong_installed_build(self):
        self.assertNotEqual(self.run_verifier('wrong-build').returncode, 0)

    def test_rejects_wrong_installed_short_version(self):
        self.assertNotEqual(self.run_verifier('wrong-short').returncode, 0)

    def test_rejects_wrong_installed_identity(self):
        self.assertNotEqual(self.run_verifier('wrong-id').returncode, 0)

    def test_rejects_installed_signature_failure(self):
        self.assertNotEqual(self.run_verifier(TEST_SIGNATURE_STATUS='1').returncode, 0)

    def test_rejects_feed_drift_after_install(self):
        self.assertNotEqual(self.run_verifier('feed-drift').returncode, 0)

    def test_rejects_feed_mismatch_before_install(self):
        self.assertNotEqual(self.run_verifier('feed-before-mismatch').returncode, 0)
        self.assertFalse(self.trace.exists())

    def test_propagates_installer_failure(self):
        self.assertNotEqual(self.run_verifier('installer-failed').returncode, 0)

    def test_refuses_existing_app(self):
        self.app.mkdir(parents=True)
        self.assertNotEqual(self.run_verifier().returncode, 0)
        self.assertFalse(self.trace.exists())

    def test_refuses_non_ci_execution(self):
        env = dict(os.environ, PATH=str(self.tools), CI='false')
        result = subprocess.run(['/bin/bash', str(self.verifier), str(self.package), '2.9.994631', str(self.archive)],
                                env=env, capture_output=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.trace.exists())


if __name__ == '__main__':
    unittest.main()
