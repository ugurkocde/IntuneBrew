"""Run the real workflow scope step with a fake read-only GitHub diff."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def scope_script():
    lines = (ROOT / '.github/workflows/build-app-packages.yml').read_text().splitlines(True)
    start = next(i for i, line in enumerate(lines) if line.strip() == '- name: Determine build scope')
    run = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == 'run: |')
    body = []
    for line in lines[run + 1:]:
        if line.strip() and not line.startswith(' ' * 10):
            break
        body.append(line[10:] if line.strip() else '\n')
    return ''.join(body)


class BuildScopeTests(unittest.TestCase):
    def scope(self, diff, event='push', requested='', before='a' * 40, read_fails=False):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            patch = directory / 'diff'
            patch.write_text(diff)
            gh = directory / 'gh'
            gh.write_text(
                '#!' + sys.executable + '\n'
                'import pathlib, sys\n'
                'assert sys.argv[1] == "api"\n'
                + ('raise SystemExit(1)\n' if read_fails else
                   'sys.stdout.write(pathlib.Path(' + repr(str(patch)) + ').read_text())\n')
            )
            gh.chmod(0o700)
            output = directory / 'output'
            env = {
                'PATH': str(directory) + os.pathsep + str(Path(sys.executable).parent) + os.pathsep + os.defpath,
                'EVENT_NAME': event,
                'REQUESTED_TOKENS': requested,
                'BEFORE_SHA': before,
                'GITHUB_SHA': 'b' * 40,
                'GITHUB_REPOSITORY': 'fixture/catalog',
                'GITHUB_OUTPUT': str(output),
            }
            result = subprocess.run(['/bin/bash', '-e', '-c', scope_script()], env=env,
                                    capture_output=True, text=True, timeout=20)
            values = dict(line.split('=', 1) for line in output.read_text().splitlines()) if output.exists() else {}
            return result, values

    def assert_partial(self, diff, tokens):
        result, values = self.scope(diff)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(values.get('scope'), 'partial')
        self.assertEqual(values.get('tokens', '').split(), tokens)

    def test_cask_rename(self):
        self.assert_partial('@@\n-    "https://formulae.brew.sh/api/cask/mindjet-mindmanager.json",\n'
                            '+    "https://formulae.brew.sh/api/cask/mindmanager.json",\n', ['mindmanager'])

    def test_formula_addition(self):
        self.assert_partial('@@\n+    "https://formulae.brew.sh/api/formula/azure-cli.json",\n', ['azure-cli'])

    def test_mixed_tokens_are_sorted_and_unique(self):
        self.assert_partial('@@\n+    "https://formulae.brew.sh/api/cask/zeta.json",\n'
                            '+    "https://formulae.brew.sh/api/formula/alpha.json",\n'
                            '+    "https://formulae.brew.sh/api/cask/zeta.json",\n', ['alpha', 'zeta'])

    def test_removal_only_and_logic_changes_remain_full(self):
        for diff, reason in [('-    "https://formulae.brew.sh/api/cask/foo.json",\n', 'no casks were added'),
                             ('+def changed_logic():\n', 'changed beyond cask list entries')]:
            with self.subTest(diff=diff):
                result, values = self.scope(diff)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(values, {'scope': 'all'})
                self.assertIn(reason, result.stdout)

    def test_missing_collector_diff_or_failed_read_remains_full(self):
        for read_fails in [False, True]:
            with self.subTest(read_fails=read_fails):
                result, values = self.scope('', read_fails=read_fails)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(values, {'scope': 'all'})

    def test_manual_tokens_validation_is_preserved(self):
        result, values = self.scope('', event='workflow_dispatch', requested='mindmanager azure-cli')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(values, {'scope': 'partial', 'tokens': 'mindmanager azure-cli'})
        result, values = self.scope('', event='workflow_dispatch', requested='mindmanager;echo')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(values, {})

    def test_schedule_and_missing_base_remain_full(self):
        for options in [{'event': 'schedule'}, {'before': ''}, {'before': '0' * 40}]:
            with self.subTest(options=options):
                result, values = self.scope('+def anything():\n', **options)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(values, {'scope': 'all'})


if __name__ == '__main__':
    unittest.main()
