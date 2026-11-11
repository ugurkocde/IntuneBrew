"""Offline artifact/collector regressions with fake app bundles and no real mounts."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import plistlib
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
spec = importlib.util.spec_from_file_location('artifact_fixture_collector', ROOT / '.github/scripts/collect_app_info.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
BUNDLE = 'org.example.fixture'
ARTIFACT = b'fixture artifact, never a real disk image'
SHA = hashlib.sha256(ARTIFACT).hexdigest()


def fake_app(root, name='Fixture', short='2.0', build=None, bundle=BUNDLE):
    contents = Path(root) / (name + '.app') / 'Contents'
    contents.mkdir(parents=True)
    data = {'CFBundleIdentifier': bundle, 'CFBundleShortVersionString': short}
    if build is not None:
        data['CFBundleVersion'] = build
    with (contents / 'Info.plist').open('wb') as f:
        plistlib.dump(data, f)
    return contents


class ReaderDiagnosticTests(unittest.TestCase):
    def setUp(self):
        fixture = tempfile.TemporaryDirectory()
        self.addCleanup(fixture.cleanup)
        self.root = Path(fixture.name).resolve()
        self.contents = fake_app(self.root)

    def read(self, bundle=BUNDLE):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = c._mounted_bundle_metadata(self.root, bundle)
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith('DMG_READER_DIAG v1 '))
        self.assertNotIn(str(self.root), lines[0])
        return result, json.loads(lines[0].removeprefix('DMG_READER_DIAG v1 ')), lines[0]

    def assert_unreadable(self, result):
        self.assertEqual(result, c.InspectionRefusal('CANDIDATE_UNREADABLE', True))

    def test_container_categories_and_exception_details_are_bounded(self):
        names = {'.fseventsd': 'fseventsd', '.background': 'background',
                 '.DocumentRevisions-V100': 'document_revisions',
                 '.Spotlight-V100': 'spotlight', '.TemporaryItems': 'temporary_items',
                 '.HFS+ Private Directory Data\r': 'hfs_private',
                 '.private-name-sentinel': 'other_hidden',
                 'private-name-sentinel': 'other_visible'}
        original = Path.iterdir
        for name, category in names.items():
            with self.subTest(name=name):
                directory = self.root / name
                directory.mkdir()

                def unreadable(path):
                    if path == directory:
                        raise PermissionError(13, 'private-error-sentinel', 'private-path-sentinel')
                    return original(path)

                with patch.object(Path, 'iterdir', unreadable):
                    result, diagnostic, line = self.read()
                self.assert_unreadable(result)
                self.assertEqual(diagnostic, {'stage': 'container_enumeration',
                    'component': None, 'container': category, 'bundleId': BUNDLE,
                    'exception': 'PermissionError', 'errno': 13,
                    'python': [sys.version_info.major, sys.version_info.minor]})
                self.assertNotIn('sentinel', line)
                directory.rmdir()

    def test_root_enumeration_and_is_dir_failures_have_distinct_stages(self):
        with patch.object(Path, 'iterdir', side_effect=PermissionError(13, 'private')):
            result, diagnostic, unused = self.read()
        self.assert_unreadable(result)
        self.assertEqual(diagnostic['stage'], 'root_enumeration')
        self.assertIsNone(diagnostic['container'])
        directory = self.root / '.fseventsd'
        directory.mkdir()
        original = Path.is_dir

        def unreadable(path):
            if path == directory:
                raise PermissionError(13, 'private')
            return original(path)

        with patch.object(Path, 'is_dir', unreadable):
            result, diagnostic, unused = self.read()
        self.assert_unreadable(result)
        self.assertEqual(diagnostic['stage'], 'entry_classification')
        self.assertEqual(diagnostic['container'], 'fseventsd')

    def test_containment_and_lstat_are_separate_for_each_component(self):
        original_resolve, original_lstat = Path.resolve, Path.lstat
        components = {'app': self.contents.parent, 'contents': self.contents,
                      'plist': self.contents / 'Info.plist'}
        for kind, target in components.items():
            with self.subTest(component=kind):
                def escape(path, *args, **kwargs):
                    return Path('/outside-sentinel') if path == target else original_resolve(path, *args, **kwargs)

                with patch.object(Path, 'resolve', escape):
                    result, diagnostic, line = self.read()
                self.assert_unreadable(result)
                self.assertEqual((diagnostic['stage'], diagnostic['component']),
                                 ('component_containment', kind))
                self.assertNotIn('outside-sentinel', line)

                def unreadable(path, *args, **kwargs):
                    if path == target:
                        raise PermissionError(13, 'private')
                    return original_lstat(path, *args, **kwargs)

                with patch.object(Path, 'is_symlink', return_value=False), \
                        patch.object(Path, 'resolve', lambda path, *args, **kwargs: path), \
                        patch.object(Path, 'lstat', unreadable):
                    result, diagnostic, unused = self.read()
                self.assert_unreadable(result)
                self.assertEqual((diagnostic['stage'], diagnostic['component']),
                                 ('component_lstat', kind))

    def test_plist_size_and_parse_failures_have_distinct_stages(self):
        target = self.contents / 'Info.plist'
        original = Path.stat

        def unreadable(path, *args, **kwargs):
            if path == target and kwargs.get('follow_symlinks', True):
                raise PermissionError(13, 'private')
            return original(path, *args, **kwargs)

        with patch.object(Path, 'is_symlink', return_value=False), \
                patch.object(Path, 'resolve', lambda path, *args, **kwargs: path), \
                patch.object(Path, 'stat', unreadable):
            result, diagnostic, unused = self.read()
        self.assert_unreadable(result)
        self.assertEqual(diagnostic['stage'], 'plist_size')
        target.write_bytes(b'not a plist')
        result, diagnostic, unused = self.read()
        self.assert_unreadable(result)
        self.assertEqual((diagnostic['stage'], diagnostic['component']),
                         ('plist_read_or_parse', 'plist'))
        self.assertEqual(diagnostic['exception'], 'InvalidFileException')

    def test_unsafe_bundle_unknown_exception_and_errno_are_sanitized(self):
        class PrivateErrorSentinel(Exception):
            pass

        for number in [True, -13, 0, 256, '13', None]:
            with self.subTest(errno=number):
                error = PrivateErrorSentinel('private-message-sentinel')
                error.errno = number
                with patch.object(Path, 'iterdir', side_effect=error):
                    result, diagnostic, line = self.read('https://secret.invalid/?token=private-sentinel')
                self.assert_unreadable(result)
                self.assertEqual(diagnostic['exception'], 'Exception')
                self.assertIsNone(diagnostic['bundleId'])
                self.assertIsNone(diagnostic['errno'])
                self.assertNotIn('sentinel', line)
                self.assertNotIn('secret', line)

    def test_logging_failure_does_not_replace_original_refusal(self):
        with patch.object(Path, 'iterdir', side_effect=PermissionError(13, 'private')), \
                patch('builtins.print', side_effect=BrokenPipeError('private')):
            self.assert_unreadable(c._mounted_bundle_metadata(self.root, BUNDLE))

    def test_public_bundle_filter_has_ascii_and_length_limits(self):
        for bundle, expected in [('a' * 200, 'a' * 200), ('a' * 201, None),
                                 ('org.example.\u0130', None), ('org.example\n', None), (42, None)]:
            with self.subTest(bundle=bundle), \
                    patch.object(Path, 'iterdir', side_effect=OSError(255, 'private')):
                result, diagnostic, unused = self.read(bundle)
            self.assert_unreadable(result)
            self.assertEqual(diagnostic['bundleId'], expected)
            self.assertEqual(diagnostic['errno'], 255)

    def test_success_and_other_refusals_are_silent_and_compatibility_is_unchanged(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(c._mounted_bundle_metadata(self.root, BUNDLE), ('2.0', None))
            self.assertEqual(c._bundle_version_in(self.root, BUNDLE), '2.0')
            self.assertEqual(c._mounted_bundle_metadata(self.root, 'org.example.other').code, 'NOT_FOUND')
            fake_app(self.root, 'Second')
            self.assertEqual(c._mounted_bundle_metadata(self.root, BUNDLE).code, 'AMBIGUOUS')
            shutil.rmtree(self.root / 'Second.app')
            target = self.contents / 'Info.plist'
            target.write_bytes(plistlib.dumps({'CFBundleIdentifier': BUNDLE,
                                               'CFBundleShortVersionString': 42}))
            self.assertEqual(c._mounted_bundle_metadata(self.root, BUNDLE).code, 'SHORT_MALFORMED')
            target.write_bytes(plistlib.dumps({'CFBundleIdentifier': BUNDLE,
                'CFBundleShortVersionString': '2.0', 'CFBundleVersion': 42}))
            self.assertEqual(c._mounted_bundle_metadata(self.root, BUNDLE).code, 'BUILD_MALFORMED')
            target.write_bytes(plistlib.dumps([]))
            self.assertEqual(c._mounted_bundle_metadata(self.root, BUNDLE).code, 'PLIST_INVALID')
            target.unlink()
            target.symlink_to(self.root / 'unopened-sentinel')
            self.assertEqual(c._mounted_bundle_metadata(self.root, BUNDLE).code, 'SYMLINK_COMPONENT')
        self.assertEqual(output.getvalue(), '')
        with patch.object(Path, 'iterdir', side_effect=PermissionError(13, 'private')), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertIsNone(c._bundle_version_in(self.root, BUNDLE))


class InspectorTests(unittest.TestCase):
    def setUp(self):
        self.mounted = False
        self.mount_root = None
        self.received = []
        self.prepare = lambda root: fake_app(root)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stream = self.stack.enter_context(patch.object(c, '_stream_to_temp_file', side_effect=self.download))
        self.process = self.stack.enter_context(patch.object(c.subprocess, 'run', side_effect=self.process_call))
        self.stack.enter_context(patch.object(c.os.path, 'ismount', side_effect=lambda _: self.mounted))
        self.stack.enter_context(patch.object(c.requests, 'get', side_effect=AssertionError('network forbidden')))

    def download(self, url, agent, target):
        target.seek(0)
        target.truncate()
        target.write(ARTIFACT)
        target.flush()
        return len(ARTIFACT)

    def process_call(self, args, **kwargs):
        if args[1] == 'attach':
            self.received.append(Path(args[2]).read_bytes())
            self.assertEqual(Path(args[2]).stat().st_mode & 0o777, 0o400)
            self.mount_root = Path(args[args.index('-mountpoint') + 1])
            self.mount_root.mkdir()
            self.mounted = True
            self.prepare(self.mount_root)
        else:
            self.mounted = False
        return SimpleNamespace(returncode=0)

    def inspect(self, declared=SHA):
        return c.inspect_dmg_artifact('https://example.invalid/app.dmg?private=value', BUNDLE, declared)

    def test_hash_and_mount_use_one_file_and_missing_build_is_allowed(self):
        obs = self.inspect()
        self.assertIsInstance(obs, c.BundleObservation)
        self.assertEqual((obs.artifact_sha256, obs.short_version, obs.bundle_version), (SHA, '2.0', None))
        self.assertEqual(self.received, [ARTIFACT])
        self.stream.assert_called_once()
        self.assertFalse(self.mount_root.parent.exists())

    def test_no_check_uses_fresh_download_each_time(self):
        self.assertEqual(self.inspect(None).artifact_sha256, SHA)
        self.assertEqual(self.inspect(None).artifact_sha256, SHA)
        self.assertEqual(self.stream.call_count, 2)

    def test_checksum_mismatch_never_mounts(self):
        refusal = self.inspect('a' * 64)
        self.assertEqual((refusal.code, refusal.integrity), ('CHECKSUM_MISMATCH', True))
        self.process.assert_not_called()

    def test_duplicate_matches_are_rejected_across_both_levels(self):
        def prepare(root):
            fake_app(root, 'A')
            fake_app(root / 'Nested', 'B', '9.0')
        self.prepare = prepare
        self.assertEqual(self.inspect().code, 'AMBIGUOUS')

    def test_unreadable_volume_trash_does_not_block_root_or_nested_app(self):
        original_iterdir = Path.iterdir
        for nested in [False, True]:
            with self.subTest(nested=nested):
                def prepare(root):
                    (root / '.Trashes').mkdir()
                    fake_app(root / 'Payload' if nested else root)

                def guarded_iterdir(path):
                    if path.name == '.Trashes':
                        raise PermissionError('fixture volume trash is unreadable')
                    return original_iterdir(path)

                self.prepare = prepare
                with patch.object(Path, 'iterdir', guarded_iterdir):
                    observation = self.inspect()
                self.assertIsInstance(observation, c.BundleObservation)
                self.assertEqual(observation.short_version, '2.0')
                self.assertFalse(self.mount_root.parent.exists())

    def test_other_unreadable_directories_still_refuse_inspection(self):
        original_iterdir = Path.iterdir
        for name in ['Trashes', '.trashes', '.Trashes2', '.fseventsd', 'Documents']:
            with self.subTest(name=name):
                def prepare(root):
                    (root / name).mkdir()
                    fake_app(root)

                def guarded_iterdir(path):
                    if path.name == name:
                        raise PermissionError('fixture sibling is unreadable')
                    return original_iterdir(path)

                self.prepare = prepare
                with patch.object(Path, 'iterdir', guarded_iterdir):
                    refusal = self.inspect()
                self.assertEqual((refusal.code, refusal.integrity),
                                 ('CANDIDATE_UNREADABLE', True))
                self.assertFalse(self.mount_root.parent.exists())

    def test_matching_app_in_volume_trash_is_not_an_install_source(self):
        def prepare(root):
            fake_app(root, 'Actual')
            fake_app(root / '.Trashes', 'Discarded', '9.0')
        self.prepare = prepare
        observation = self.inspect()
        self.assertIsInstance(observation, c.BundleObservation)
        self.assertEqual(observation.short_version, '2.0')

    def test_trash_named_app_is_still_checked_for_ambiguity(self):
        def prepare(root):
            fake_app(root, 'Actual')
            fake_app(root, '.Trashes', '9.0')
        self.prepare = prepare
        self.assertEqual(self.inspect().code, 'AMBIGUOUS')

    def test_wrong_id_and_symlinked_top_level_are_not_matches(self):
        self.prepare = lambda root: fake_app(root, bundle='org.example.other')
        self.assertEqual(self.inspect().code, 'NOT_FOUND')
        with tempfile.TemporaryDirectory() as outside:
            fake_app(outside)
            self.prepare = lambda root: (root / 'Linked.app').symlink_to(Path(outside) / 'Fixture.app')
            self.assertEqual(self.inspect().code, 'NOT_FOUND')

    def test_symlinked_contents_or_plist_cannot_escape_mount(self):
        for component in ['Contents', 'Info.plist']:
            with self.subTest(component=component), tempfile.TemporaryDirectory() as outside:
                external = fake_app(outside)
                def prepare(root):
                    inside = fake_app(root)
                    path = inside if component == 'Contents' else inside / 'Info.plist'
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    path.symlink_to(external if component == 'Contents' else external / 'Info.plist')
                self.prepare = prepare
                self.assertEqual(self.inspect().code, 'SYMLINK_COMPONENT')

    def test_unreadable_or_oversized_candidate_prevents_ambiguous_acceptance(self):
        for body in [b'not a plist', b'x' * (1024 * 1024 + 1)]:
            def prepare(root):
                fake_app(root, 'A')
                other = fake_app(root, 'B', bundle='org.example.other')
                (other / 'Info.plist').write_bytes(body)
            self.prepare = prepare
            self.assertTrue(self.inspect().integrity)

    def test_versions_are_strings_and_not_coerced_or_trimmed(self):
        for short in [42, b'2.0', '', '2.0\n', 'x' * 65]:
            with self.subTest(short=short):
                self.prepare = lambda root: fake_app(root, short=short)
                self.assertEqual(self.inspect().code, 'SHORT_MALFORMED')
        self.prepare = lambda root: fake_app(root, short=' 2.0 ')
        self.assertEqual(self.inspect().short_version, ' 2.0 ')
        for build in [42, '']:
            self.prepare = lambda root: fake_app(root, build=build)
            self.assertEqual(self.inspect().code, 'BUILD_MALFORMED')

    def test_missing_short_and_non_string_identity(self):
        def prepare(root):
            path = fake_app(root) / 'Info.plist'
            with path.open('wb') as f:
                plistlib.dump({'CFBundleIdentifier': BUNDLE}, f)
        self.prepare = prepare
        self.assertEqual(self.inspect().code, 'SHORT_MALFORMED')
        self.prepare = lambda root: fake_app(root, bundle=42)
        self.assertEqual(self.inspect().code, 'NOT_FOUND')

    def test_download_refusal_and_logs_do_not_expose_url(self):
        def refused(*_):
            print('https://example.invalid/app.dmg?private=value')
            return None
        self.stream.side_effect = refused
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(self.inspect().code, 'DOWNLOAD_FAILED')
        self.assertNotIn('example.invalid', output.getvalue())
        self.process.assert_not_called()
        self.stream.side_effect = c._OversizedDownload('sensitive details')
        self.assertEqual(self.inspect().code, 'DOWNLOAD_FAILED')

    def test_mount_failure_and_timeout_always_reconcile_cleanup(self):
        self.process.side_effect = lambda *_args, **_kwargs: SimpleNamespace(returncode=1)
        self.assertEqual(self.inspect().code, 'MOUNT_FAILED')
        def timed_out(args, **kwargs):
            if args[1] == 'attach':
                self.process_call(args, **kwargs)
                raise TimeoutError('fixture')
            return self.process_call(args, **kwargs)
        self.process.side_effect = timed_out
        self.assertEqual(self.inspect().code, 'INTERNAL_ERROR')
        self.assertFalse(self.mounted)
        self.assertEqual(self.process.call_args[0][0][1], 'detach')

    def test_cleanup_never_recursively_deletes_a_mounted_directory(self):
        def stuck(args, **kwargs):
            if args[1] == 'attach':
                return self.process_call(args, **kwargs)
            return SimpleNamespace(returncode=1)
        self.process.side_effect = stuck
        with patch.object(c.shutil, 'rmtree') as remove, contextlib.redirect_stdout(io.StringIO()):
            self.inspect()
            remove.assert_not_called()
        self.mounted = False
        shutil.rmtree(self.mount_root.parent)


class CollectorIntegrationTests(unittest.TestCase):
    def run_case(self, observation, raw='2.0.0', prior='1.0'):
        url = 'https://formulae.brew.sh/api/cask/fixture.json'
        app = {'name': 'Fixture', 'version': raw.split(',')[0], 'bundleId': BUNDLE,
               'fileName': 'fixture.dmg', 'url': 'https://example.invalid/fixture.dmg',
               'homebrew_cask': 'fixture', 'vendor_url': 'https://example.invalid/fixture.dmg'}
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            root = Path(directory)
            (root / 'Apps').mkdir()
            path = root / 'Apps/fixture.json'
            original = json.dumps(dict(app, version=prior, sha='b' * 64)).encode()
            path.write_bytes(original)
            stack.enter_context(contextlib.chdir(root))
            for name in ['app_urls', 'pkg_in_pkg_urls', 'pkg_urls', 'pkg_in_dmg_urls', 'custom_scrapers']:
                stack.enter_context(patch.object(c, name, []))
            stack.enter_context(patch.object(c, 'homebrew_cask_urls', [url]))
            stack.enter_context(patch.dict(c.cask_cache, {url: {'version': raw, 'sha256': 'no_check'}}, clear=True))
            stack.enter_context(patch.object(c, 'prefetch_cask_data'))
            stack.enter_context(patch.object(c, 'get_homebrew_app_info', return_value=dict(app)))
            stack.enter_context(patch.object(c.shutil, 'which', return_value='/fake/hdiutil'))
            inspect = stack.enter_context(patch.object(c, 'inspect_dmg_artifact', return_value=observation))
            hash_again = stack.enter_context(patch.object(c, 'calculate_file_hash', side_effect=AssertionError('second download')))
            stack.enter_context(patch.object(c, 'update_readme_apps'))
            stack.enter_context(patch.object(c, 'update_readme_with_latest_changes'))
            stack.enter_context(patch.dict(os.environ, {'CATALOG_COLLECTION_REPORT': str(root / 'report.json')}))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            c.main()
            result = path.read_bytes()
            report = json.loads((root / 'report.json').read_text())
            hash_again.assert_not_called()
            inspect.assert_called_once()
            return original, result, report

    def test_no_check_write_reuses_inspected_digest_and_keeps_schema(self):
        old, new, report = self.run_case(c.BundleObservation(SHA, BUNDLE, '2.0'))
        data = json.loads(new)
        self.assertEqual((data['version'], data['previous_version'], data['sha']), ('2.0', '1.0', SHA))
        self.assertEqual(data['fileName'], 'fixture.dmg')
        self.assertEqual(set(data), set(json.loads(old)) | {'previous_version'})
        self.assertEqual(report['versionEvidence'][0]['relation'], 'PAD')
        self.assertEqual(report['failures'], [])

    def test_integrity_or_unproven_release_holds_prior_file_byte_for_byte(self):
        for obs, reason in [(c.InspectionRefusal('AMBIGUOUS', True), 'AMBIGUOUS'),
                            (c.BundleObservation(SHA, BUNDLE, '2.0-demo'), 'RELATION_UNPROVEN')]:
            old, new, report = self.run_case(obs)
            self.assertEqual(old, new)
            self.assertEqual(report['failures'][0]['reason'], reason)

    def test_plus_build_stays_held_until_consumer_rollout(self):
        with patch.object(c, 'CATALOG_CONSUMER_CAPABILITIES', frozenset({'decorated_text'})):
            old, new, report = self.run_case(c.BundleObservation(SHA, BUNDLE, '2.0+2'), raw='2.0,2')
        self.assertEqual(old, new)
        self.assertEqual(report['failures'][0]['reason'], 'CONSUMER_CAPABILITY_PENDING')

    def test_plus_build_writes_exact_bundle_after_verified_consumer_rollout(self):
        _, new, report = self.run_case(c.BundleObservation(SHA, BUNDLE, '0.4.28+2'),
                                       raw='0.4.28,2', prior='0.4.26')
        self.assertEqual(json.loads(new)['version'], '0.4.28+2')
        self.assertEqual(report['versionEvidence'][0]['relation'], 'RENDER_PLUS')
        self.assertEqual(report['failures'], [])

    def test_decorated_release_is_shared_and_preserves_exact_observed_text(self):
        for raw, short in [('2.0,77', '2.0 (build 77)'), ('2.0,stable.3,123', '2.0-stable.3')]:
            with self.subTest(raw=raw):
                _, new, report = self.run_case(c.BundleObservation(SHA, BUNDLE, short), raw=raw)
                self.assertEqual(json.loads(new)['version'], short)
                self.assertEqual(json.loads(new)['fileName'], 'fixture.dmg')
                self.assertEqual(report['failures'], [])


if __name__ == '__main__':
    unittest.main()
