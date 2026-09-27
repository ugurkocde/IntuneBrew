import importlib.util
import pathlib
import unittest

SPEC = importlib.util.spec_from_file_location('commit_catalog', pathlib.Path(__file__).parents[1] / '.github/scripts/commit_catalog.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PublicationMergeTests(unittest.TestCase):
    def test_independent_metadata_and_package_updates_survive(self):
        base = {'version': '1', 'url': 'old', 'category': 'Other', 'bundleId': 'old.id'}
        generated = {**base, 'version': '2', 'url': 'new'}
        current = {**base, 'category': 'Developer', 'bundleId': 'correct.id'}
        self.assertEqual(MODULE.merge_json(base, generated, current), {**current, 'version': '2', 'url': 'new'})

    def test_conflicting_versions_require_a_fresh_build(self):
        with self.assertRaisesRegex(ValueError, '/version'):
            MODULE.merge_json({'version': '1'}, {'version': '2'}, {'version': '3'})

    def test_deletions_and_identical_additions(self):
        self.assertEqual(MODULE.merge_json({'a': 1, 'b': 1}, {'b': 1}, {'a': 1, 'b': 2}), {'b': 2})
        self.assertEqual(MODULE.merge_content('app.json', None, b'{"a":1}', b'{"a":1}'), b'{"a":1}')

    def test_unrelated_documentation_edits_survive(self):
        result = MODULE.merge_content('README.md', b'header\n\n\n\nold table\n', b'header\n\n\n\nnew table\n', b'new header\n\n\n\nold table\n')
        self.assertEqual(result, b'new header\n\n\n\nnew table\n')

    def test_publish_against_a_concurrent_remote_commit(self):
        import json
        import os
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            def run(*args, cwd=root):
                return subprocess.check_output(['git', *args], cwd=cwd, stderr=subprocess.DEVNULL)
            run('init', '--bare', 'remote.git')
            run('clone', str(root / 'remote.git'), 'builder')
            builder = root / 'builder'
            run('checkout', '-b', 'main', cwd=builder)
            run('config', 'user.name', 'Test', cwd=builder)
            run('config', 'user.email', 'test@example.invalid', cwd=builder)
            (builder / 'Apps').mkdir()
            app = builder / 'Apps/app.json'
            app.write_text(json.dumps({'version': '1', 'category': 'Other'}))
            run('add', '.', cwd=builder)
            run('commit', '-m', 'base', cwd=builder)
            run('push', '-u', 'origin', 'main', cwd=builder)
            run('clone', '--branch', 'main', str(root / 'remote.git'), 'metadata')
            metadata = root / 'metadata'
            run('config', 'user.name', 'Test', cwd=metadata)
            run('config', 'user.email', 'test@example.invalid', cwd=metadata)
            (metadata / 'Apps/app.json').write_text(json.dumps({'version': '1', 'category': 'Developer'}))
            run('commit', '-am', 'category', cwd=metadata)
            run('push', cwd=metadata)
            app.write_text(json.dumps({'version': '2', 'category': 'Other'}))
            previous = pathlib.Path.cwd()
            try:
                os.chdir(builder)
                MODULE.main()
            finally:
                os.chdir(previous)
            published = json.loads(run('--git-dir', str(root / 'remote.git'), 'show', 'main:Apps/app.json'))
            self.assertEqual(published, {'version': '2', 'category': 'Developer'})
            self.assertEqual(json.loads(app.read_text()), {'version': '2', 'category': 'Other'})
