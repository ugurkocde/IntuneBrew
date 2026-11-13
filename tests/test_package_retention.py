"""Exercise the real workflow cleanup function against a fake Azure store."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/build-app-packages.yml'


class PackageRetentionTests(unittest.TestCase):
    def run_cleanup(self, app, version, names, listing=None, fail_azure=False):
        source = WORKFLOW.read_text()
        match = re.search(r'(?ms)^          delete_superseded_blobs\(\) \{\n.*?^          \}\n', source)
        self.assertIsNotNone(match, 'The existing cleanup call contract must remain')
        function = textwrap.dedent(match.group(0))
        with tempfile.TemporaryDirectory(prefix='package-retention-') as folder:
            root = Path(folder)
            store = root / 'store'; store.mkdir()
            for index, name in enumerate(names):
                path = store / name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(('fixture-' + str(index)).encode())
            before = {str(p.relative_to(store)): p.read_bytes() for p in store.rglob('*') if p.is_file()}
            stub = root / 'az'
            stub.write_text('''#!/bin/bash
printf '%s\\n' "$*" >> "$CALLS"
[ "$FAIL_AZURE" != 1 ] || exit 7
if [ "$1 $2 $3" = 'storage blob delete' ]; then
  shift 3
  while [ "$#" -gt 0 ]; do
    if [ "$1" = --name ]; then shift; rm -f -- "$STORE/$1"; break; fi
    shift
  done
fi
''')
            stub.chmod(0o755)
            calls = root / 'calls'
            env = dict(os.environ, PATH=str(root) + ':' + os.environ['PATH'], CALLS=str(calls),
                       STORE=str(store), FAIL_AZURE='1' if fail_azure else '0')
            result = subprocess.run(['bash', '-eu', '-c', function + '\ndelete_superseded_blobs "$1" "$2" "$3"\n',
                                     'fixture', app, version, '\n'.join(names) if listing is None else listing],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(calls.exists(), 'Publication must not issue any Azure cleanup command')
            after = {str(p.relative_to(store)): p.read_bytes() for p in store.rglob('*') if p.is_file()}
            self.assertEqual(after, before, 'Every existing package must remain byte-identical')

    def test_shared_prefix_never_deletes_sibling_or_own_versions(self):
        self.run_cleanup('github_copilot', '1.3.1', ['github_copilot_1.3.0.pkg',
                         'github_copilot_cli_1.0.110.pkg', 'github_copilot_1.3.1.pkg'])

    def test_old_and_current_versions_remain_for_published_clients(self):
        self.run_cleanup('example', '2.0', ['example_1.0.pkg', 'example_2.0.pkg'])

    def test_numeric_suffix_sibling_and_font_paths_are_retained(self):
        self.run_cleanup('example', '2', ['example_2_1.0.pkg', 'example_2.pkg',
                         'fonts/example/' + 'a' * 64 + '/example_1.0.pkg'])

    def test_malformed_and_whitespace_names_do_not_authorize_deletion(self):
        self.run_cleanup('example', '2.0', ['unrelated.pkg', 'example_old beta.pkg',
                         'example_2x0.pkg', 'example_.pkg'])

    def test_partial_build_rollback_preserves_prior_catalog_target(self):
        self.run_cleanup('out_of_scope', '2.0', ['out_of_scope_1.0.pkg', 'out_of_scope_2.0.pkg'])

    def test_empty_listing_is_safe(self):
        self.run_cleanup('example', '2.0', ['example_1.0.pkg'], listing='')

    def test_failed_azure_operations_are_never_attempted(self):
        self.run_cleanup('example', '2.0', ['example_1.0.pkg', 'example_2.0.pkg'], fail_azure=True)

    def test_all_existing_publication_call_sites_remain(self):
        source = WORKFLOW.read_text()
        calls = re.findall(r'^ +delete_superseded_blobs "\$app_name" "\$version" "\$existing_versions"$', source, re.M)
        self.assertEqual(len(calls), 4)


if __name__ == '__main__':
    unittest.main()
