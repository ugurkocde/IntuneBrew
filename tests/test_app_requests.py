import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


approval = module('add_new_app')
pending = module('pending_requests')
scoped = module('revert_out_of_scope')


class AppRequestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.temp.name)
        Path('.github/scripts').mkdir(parents=True)
        Path('Apps').mkdir()
        Path('.github/scripts/collect_app_info.py').write_text('homebrew_cask_urls = [\n]\n')
        Path('supported_apps.json').write_text('{}')
        self.output = Path('outputs')
        self.env = patch.dict(os.environ, {'GITHUB_OUTPUT': str(self.output), 'ISSUE_NUMBER': '42', 'NEEDS_REVIEW': ''})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        os.chdir(self.cwd)
        self.temp.cleanup()

    def approve(self, casks, payloads):
        with patch.dict(os.environ, COMMENT_BODY='/approve ' + ' '.join(casks)), patch.object(
            approval, 'fetch_homebrew_info', side_effect=lambda token: payloads.get(token)
        ), contextlib.redirect_stdout(io.StringIO()):
            try:
                approval.main()
            except SystemExit as error:
                status = error.code
            else:
                status = 0
        return status, dict(line.split('=', 1) for line in self.output.read_text().splitlines())

    def payload(self, **extra):
        return {'token': 'requested', 'name': ['Requested'], 'url': 'https://vendor.test/requested.dmg', **extra}

    def record(self, casks, review=False):
        with patch.dict(os.environ, APPS_JSON=json.dumps([{'cask': cask} for cask in casks]), NEEDS_REVIEW=str(review).lower()):
            pending.record()

    def publish(self, cask, **extra):
        Path(f'Apps/{cask}.json').write_text(json.dumps({'homebrew_cask': cask, 'name': cask, 'version': '1', **extra}))
        index = json.loads(Path('supported_apps.json').read_text())
        index[cask] = f'https://example.test/Apps/{cask}.json'
        Path('supported_apps.json').write_text(json.dumps(index))

    def notifications(self):
        pending.resolve()
        return json.loads(Path(pending.NOTIFICATIONS_FILE).read_text())

    def ack(self, items):
        Path(pending.DELIVERIES_FILE).write_text(json.dumps(items))
        pending.acknowledge()

    def test_partial_approval_keeps_failed_casks_for_review(self):
        status, outputs = self.approve(['requested', 'missing'], {'requested': self.payload()})
        self.assertEqual(status, 0)
        self.assertEqual(outputs['app_added'], 'true')
        self.assertEqual(outputs['needs_review'], 'true')
        self.assertEqual(json.loads(outputs['review_json'])[0]['name'], 'missing')
        self.assertIn('requested.json', Path('.github/scripts/collect_app_info.py').read_text())
        self.assertNotIn('missing.json', Path('.github/scripts/collect_app_info.py').read_text())

    def test_disabled_and_deprecated_casks_never_enter_the_collector(self):
        original = Path('.github/scripts/collect_app_info.py').read_text()
        for flag in ['disabled', 'deprecated']:
            with self.subTest(flag=flag):
                self.output.unlink(missing_ok=True)
                status, outputs = self.approve(['requested'], {'requested': self.payload(**{flag: True})})
                self.assertEqual(status, 1)
                self.assertEqual(outputs['needs_review'], 'true')
                self.assertEqual(Path('.github/scripts/collect_app_info.py').read_text(), original)

    def test_versioned_tokens_survive_url_and_command_extraction(self):
        self.assertEqual(approval.extract_casks_from_urls('https://formulae.brew.sh/api/cask/dotnet-sdk@8.json\nhttps://formulae.brew.sh/cask/dotnet-sdk@8'), ['dotnet-sdk@8'])
        self.assertEqual(approval.extract_casks_from_urls('https://formulae.brew.sh/api/cask/example.app.json'), ['example.app'])
        self.assertEqual(approval.extract_casks_from_comment('/approve dotnet-sdk@8'), ['dotnet-sdk@8'])

    def test_supported_formula_is_added_to_the_app_packaging_list(self):
        Path('.github/scripts/collect_app_info.py').write_text('app_urls = [\n]\n')
        status, outputs = self.approve(['azure-cli'], {'azure-cli': {'name': 'azure-cli', 'versions': {'stable': '2.90.0'}}})
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(outputs['apps_json'])[0]['name'], 'Azure CLI')
        self.assertIn('/api/formula/azure-cli.json', Path('.github/scripts/collect_app_info.py').read_text())
        for url in ['https://formulae.brew.sh/formula/azure-cli', 'https://formulae.brew.sh/api/formula/azure-cli.json']:
            self.assertEqual(approval.extract_casks_from_urls(url), ['azure-cli'])
        self.assertEqual(approval.extract_casks_from_urls('https://formulae.brew.sh/formula/node'), [])

    def test_installer_only_logi_entry_is_rebuilt_and_not_reported_as_fulfilled(self):
        Path('.github/scripts/collect_app_info.py').write_text('app_urls = [\n "https://formulae.brew.sh/api/cask/logi-options+.json",\n]\n')
        self.publish('logi-options+')
        status, outputs = self.approve(['logi-options+'], {})
        self.assertEqual(status, 0)
        self.assertEqual(outputs['app_added'], 'true')
        self.assertEqual(outputs['rebuild_tokens'], 'logi-options+')
        self.assertNotIn('all_duplicates', outputs)
        self.record(['logi-options+'])
        self.assertEqual(self.notifications(), [])
        self.publish('logi-options+', packaging_recipe='logi-options-silent-v1')
        self.assertEqual(self.notifications()[0]['kind'], 'live')

    def test_formula_completion_requires_its_published_package_recipe(self):
        self.record(['azure-cli'])
        self.publish('azure-cli', homebrew_cask=None, homebrew_formula='azure-cli')
        self.assertEqual(self.notifications(), [])
        self.publish('azure-cli', homebrew_cask=None, homebrew_formula='azure-cli', packaging_recipe='azure-cli-universal-v1')
        self.assertEqual(self.notifications()[0]['apps'][0]['name'], 'azure-cli')

    def test_registered_but_unpublished_cask_is_not_closed_as_a_live_duplicate(self):
        Path('.github/scripts/collect_app_info.py').write_text(
            'homebrew_cask_urls = [\n    "https://formulae.brew.sh/api/cask/requested.json",\n]\n'
        )
        status, outputs = self.approve(['requested'], {})
        self.assertEqual(status, 1)
        self.assertEqual(outputs['needs_review'], 'true')
        self.assertNotIn('all_duplicates', outputs)
        self.output.unlink()
        self.publish('requested')
        status, outputs = self.approve(['requested'], {})
        self.assertEqual(status, 0)
        self.assertEqual(outputs['all_duplicates'], 'true')

    def test_live_duplicate_does_not_hide_an_unmatched_part_of_the_request(self):
        Path('.github/scripts/collect_app_info.py').write_text(
            'homebrew_cask_urls = [\n    "https://formulae.brew.sh/api/cask/requested.json",\n]\n'
        )
        self.publish('requested')
        with patch.dict(os.environ, COMMENT_BODY='', ISSUE_BODY='', ISSUE_TITLE='App Request: Requested and Unknown'), patch.object(
            approval, 'search_homebrew_casks', side_effect=[[('requested', self.payload(), 1.0)], []]
        ), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as exit:
            approval.main()
        self.assertEqual(exit.exception.code, 0)
        outputs = dict(line.split('=', 1) for line in self.output.read_text().splitlines())
        self.assertEqual(outputs['needs_review'], 'true')
        self.assertEqual(outputs['app_added'], 'false')
        self.assertNotIn('all_duplicates', outputs)

    def test_successful_delivery_is_the_only_way_to_remove_a_live_request(self):
        self.record(['requested'])
        self.publish('requested')
        first = self.notifications()
        self.assertEqual(len(first), 1)
        self.assertEqual(len(pending.load_state()), 1)
        self.ack([])
        self.assertEqual(self.notifications(), first)
        self.ack(first)
        self.assertEqual(pending.load_state(), [])
        self.assertEqual(self.notifications(), [])

    def test_placeholder_unpublished_and_invalid_packages_do_not_resolve(self):
        self.record(['requested'])
        for extra in [dict(version='0.0.0'), dict(type='app', url='https://vendor.test/app.zip')]:
            self.publish('requested', **extra)
            self.assertEqual(self.notifications(), [])
        self.publish('requested')
        Path('supported_apps.json').write_text('{}')
        self.assertEqual(self.notifications(), [])

    def test_stale_request_sends_one_review_notice_then_can_recover(self):
        self.record(['requested'])
        entries = pending.load_state()
        entries[0]['recorded_at'] = '2020-01-01T00:00:00Z'
        pending.save_state(entries)
        first = self.notifications()
        self.assertEqual(first[0]['kind'], 'needs-review')
        self.ack([])
        self.assertEqual(self.notifications(), first)
        self.ack(first)
        self.assertEqual(len(pending.load_state()), 1)
        self.assertEqual(self.notifications(), [])
        self.publish('requested')
        recovered = self.notifications()
        self.assertEqual(recovered[0]['kind'], 'live')
        self.ack(recovered)
        self.assertEqual(pending.load_state(), [])

    def test_repeat_approval_preserves_casks_and_stale_receipt_cannot_clear_it(self):
        self.record(['first'])
        self.publish('first')
        old_notification = self.notifications()
        self.record(['second'], review=True)
        self.assertEqual(pending.load_state()[0]['casks'], ['first', 'second'])
        self.ack(old_notification)
        self.assertEqual(len(pending.load_state()), 1)
        self.publish('second')
        self.assertTrue(self.notifications()[0]['needs_review'])

    def test_corrupt_state_fails_without_overwriting_requests(self):
        Path(pending.STATE_FILE).write_text('{broken')
        with self.assertRaises(json.JSONDecodeError):
            self.record(['requested'])
        self.assertEqual(Path(pending.STATE_FILE).read_text(), '{broken')

    def test_scoped_restore_preserves_new_app_and_restores_everything_else(self):
        subprocess.run(['git', 'init', '-q'], check=True)
        Path('README.md').write_text('original')
        self.publish('existing')
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.test', 'commit', '-qm', 'baseline'], check=True)
        self.publish('existing', version='2')
        self.publish('requested')
        self.publish('unexpected')
        Path('README.md').write_text('generated')
        scoped.revert({'requested'})
        self.assertEqual(json.loads(Path('Apps/existing.json').read_text())['version'], '1')
        self.assertTrue(Path('Apps/requested.json').exists())
        self.assertFalse(Path('Apps/unexpected.json').exists())
        self.assertEqual(Path('README.md').read_text(), 'original')

    def test_scoped_restore_finishes_git_enumeration_before_restoring(self):
        operations = []
        real_run = subprocess.run
        def run(args, **kwargs):
            operations.append(args)
            return real_run(args, **kwargs)
        subprocess.run(['git', 'init', '-q'], check=True)
        Path('README.md').write_text('baseline')
        self.publish('existing')
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.test', 'commit', '-qm', 'baseline'], check=True)
        self.publish('existing', version='2')
        with patch.object(scoped.subprocess, 'run', side_effect=run):
            scoped.revert(set())
        self.assertEqual(operations[0][1:3], ['--no-optional-locks', 'diff'])
        self.assertEqual(operations[1][1:3], ['--no-optional-locks', 'ls-files'])
        self.assertEqual(operations[2][1], 'restore')
