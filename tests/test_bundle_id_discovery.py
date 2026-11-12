"""Missing-ID casks retain vendor DMGs and all existing artifact/version gates."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from test_collect_app_info import (CountingSession, cask_response,
                                  collect_app_info as c, run_collector)

DIGEST = 'a' * 64


def fixture(token='future-one', name='Future One', checksum=DIGEST):
    return {'token': token, 'name': [name], 'version': '1.2.3', 'desc': 'Fixture',
            'homepage': 'https://example.test/', 'url': 'https://example.test/' + token + '.dmg',
            'sha256': checksum,
            'artifacts': [{'app': [name + '.app'], 'target': '/Applications/' + name + '.app'}]}


def app_bundle(root, name='Fixture.app', bundle='org.example.fixture', short='1.2.3'):
    contents = Path(root) / name / 'Contents'
    contents.mkdir(parents=True)
    (contents / 'Info.plist').write_bytes(plistlib.dumps(
        {'CFBundleIdentifier': bundle, 'CFBundleShortVersionString': short, 'CFBundleVersion': '7'}))
    return contents


class DiscoveryCollectorTests(unittest.TestCase):
    def collect(self, data, observation, previous=None):
        url = 'https://formulae.brew.sh/api/cask/' + data['token'] + '.json'
        session = CountingSession({url: cask_response(data)})
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'Apps'
            folder.mkdir()
            path = folder / (c.sanitize_filename(data['name'][0]) + '.json')
            before = json.dumps(previous).encode() if previous is not None else None
            if before is not None:
                path.write_bytes(before)
            with run_collector(directory, [url], session=session), \
                    patch.object(c.shutil, 'which', return_value='/usr/bin/hdiutil'), \
                    patch.object(c, '_stable_budget', side_effect=lambda seconds: contextlib.nullcontext()), \
                    patch.object(c, 'inspect_dmg_artifact', return_value=observation) as inspect, \
                    patch.object(c, 'read_vendor_sha256', return_value=None):
                c.main()
                hash_calls = c.calculate_file_hash.call_count
            result = path.read_bytes() if path.exists() else None
            return result, before, list(c.collection_failures), inspect.call_args_list, hash_calls

    def test_two_unregistered_casks_discover_once_and_keep_direct_vendor_metadata(self):
        for token, name, checksum in [('future-one', 'Future One', DIGEST),
                                      ('future-two', 'Future Two', 'no_check')]:
            with self.subTest(cask=token):
                data = fixture(token, name, checksum)
                obs = c.BundleObservation(DIGEST, 'org.example.' + token, '1.2.3', '7')
                raw, _, failures, calls, hashes = self.collect(data, obs)
                result = json.loads(raw)
                self.assertEqual((result['bundleId'], result['version'], result['sha']),
                                 (obs.bundle_id, obs.short_version, DIGEST))
                self.assertEqual(result['url'], data['url'])
                self.assertEqual(result['vendor_url'], data['url'])
                self.assertEqual(result['homebrew_cask'], token)
                self.assertNotIn('type', result)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0].args, (data['url'], None, DIGEST if checksum == DIGEST else None))
                self.assertEqual(calls[0].kwargs['app_name'], name + '.app')
                self.assertEqual((failures, hashes), ([], 0))
                self.assertTrue(c.version_evidence[-1]['bundleIdDiscovered'])

    def test_prior_or_cask_identity_keeps_normal_inspection_path(self):
        for prior_id in [True, False]:
            with self.subTest(prior=prior_id):
                data = fixture()
                prior = {'name': 'Future One', 'homebrew_cask': 'future-one',
                         'version': '1.2.2', 'url': 'https://example.test/old.dmg',
                         'bundleId': 'org.example.known', 'sha': 'b' * 64} if prior_id else None
                if not prior_id:
                    data['artifacts'].append({'uninstall': [{'quit': 'org.example.known'}]})
                obs = c.BundleObservation(DIGEST, 'org.example.known', '1.2.3', '7')
                raw, _, failures, calls, _ = self.collect(data, obs, prior)
                self.assertEqual(json.loads(raw)['bundleId'], 'org.example.known')
                self.assertEqual(failures, [])
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0].args[1], 'org.example.known')
                self.assertNotIn('app_name', calls[0].kwargs)
                self.assertNotIn('bundleIdDiscovered', c.version_evidence[-1])

    def test_ineligible_casks_do_not_inspect(self):
        original = fixture()
        cases = []
        for artifacts in [[{'app': ['A.app']}, {'app': ['B.app']}],
                          [{'app': ['Future One.app'], 'target': '/Applications/Renamed.app'}],
                          [{'app': ['Folder/Future One.app']}],
                          [{'app': ['Future One.app', {'target': 'Other.app'}]}],
                          [{'app': ['Future One.app']}, {'pkg': ['installer.pkg']}],
                          [{'app': ['Future One.app']}, {'postflight': []}]]:
            data = copy.deepcopy(original)
            data['artifacts'] = artifacts
            cases.append((data, {}))
        for source in ['http://example.test/app.dmg', 'https://example.test/app.zip']:
            data = copy.deepcopy(original)
            data['url'] = source
            cases.append((data, {}))
        cases.append((original, {'url': 'https://override.example.test/app.dmg'}))
        for data, overrides in cases:
            with self.subTest(data=data), patch.object(c.shutil, 'which', return_value='hdiutil'), \
                    patch.object(c, 'inspect_dmg_artifact') as inspect:
                info = {'url': data['url'], 'fileName': data['url'].rsplit('/', 1)[-1],
                        'version': '1.2.3', 'bundleId': None, **overrides}
                self.assertIsNone(c.discover_missing_bundle_id(info, None, data, data['token']))
                inspect.assert_not_called()

    def test_every_refusal_preserves_prior_file_and_never_legacy_passes(self):
        for code in ['CHECKSUM_MISMATCH', 'NOT_FOUND', 'SYMLINK_COMPONENT',
                     'BUNDLE_ID_INVALID', 'DOWNLOAD_FAILED', 'MOUNT_FAILED', 'CLEANUP_INCOMPLETE']:
            for exists in [False, True]:
                with self.subTest(code=code, prior=exists):
                    previous = {'name': 'Future One', 'homebrew_cask': 'future-one',
                                'version': '1.2.2', 'bundleId': None,
                                'url': 'https://example.test/old.dmg', 'sha': 'b' * 64} if exists else None
                    raw, before, failures, calls, hashes = self.collect(
                        fixture(), c.InspectionRefusal(code, False), previous)
                    self.assertEqual(raw, before)
                    self.assertEqual(failures[0]['reason'], 'BUNDLE_ID_' + code)
                    self.assertEqual((len(calls), hashes), (1, 0))

    def test_known_prior_formula_stable_source_or_missing_mount_tool_skips_discovery(self):
        data = fixture()
        original = {'url': data['url'], 'fileName': 'future-one.dmg', 'bundleId': None}
        cases = [(original, {'bundleId': 'org.example.known'}, 'future-one', 'hdiutil'),
                 ({**original, 'homebrew_formula': 'future-formula'}, None, 'future-one', 'hdiutil'),
                 (original, None, 'rotato', 'hdiutil'), (original, None, 'future-one', None)]
        for info, prior, token, tool in cases:
            with self.subTest(token=token, tool=tool), \
                    patch.object(c.shutil, 'which', return_value=tool), \
                    patch.object(c, 'inspect_dmg_artifact') as inspect:
                self.assertIsNone(c.discover_missing_bundle_id(info, prior, data, token))
                inspect.assert_not_called()

    def test_unraid_shaped_version_is_held_by_existing_reconcile(self):
        data = fixture('future-release', 'Future Release')
        data['version'] = '2.0.11.1,1'
        obs = c.BundleObservation(DIGEST, 'org.example.release', 'v2.0.11.1-unraid.1', 'v2.0.11.1-unraid.1')
        raw, _, failures, calls, hashes = self.collect(data, obs)
        self.assertIsNone(raw)
        self.assertEqual(failures[0]['reason'], 'RELATION_UNPROVEN')
        self.assertEqual((len(calls), hashes), (1, 0))

    def test_supplied_observation_does_not_take_plan_noop_or_legacy_shortcut(self):
        info = {'url': 'https://example.test/app.dmg', 'fileName': 'app.dmg',
                'version': '1.2.3', 'bundleId': 'org.example.fixture'}
        data = {'url': info['url'], 'version': '1.2.3', 'sha256': DIGEST}
        obs = c.BundleObservation(DIGEST, 'org.example.fixture', '8.0.0', '7')
        with patch.object(c.shutil, 'which', return_value='hdiutil'), \
                patch.object(c, 'plan', side_effect=AssertionError('discovery must reconcile')), \
                patch.object(c, '_recover_vendor_stable', side_effect=AssertionError('not recovery')):
            with self.assertRaises(c.CatalogVersionHold):
                c.reconcile_vendor_dmg(info, None, data, 'future-one', observation=obs)


class DiscoveryReaderTests(unittest.TestCase):
    def test_exact_app_ignores_uninstaller_and_supports_unicode_normalisation(self):
        with tempfile.TemporaryDirectory() as directory:
            app_bundle(directory, 'Uninstall Cafe\u0301.app', 'org.example.uninstaller')
            app_bundle(directory, 'Cafe\u0301.app', 'org.example.main')
            self.assertEqual(c._mounted_bundle_metadata(directory, None, app_name='Caf\u00e9.app'),
                             ('org.example.main', '1.2.3', '7'))

    def test_symlinked_root_is_not_found_and_other_components_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app_bundle(root, 'Real.app')
            (root / 'Fixture.app').symlink_to(root / 'Real.app', target_is_directory=True)
            self.assertEqual(c._mounted_bundle_metadata(root, None, app_name='Fixture.app').code, 'NOT_FOUND')
            (root / 'Fixture.app').unlink()
            contents = app_bundle(root)
            plist = contents / 'Info.plist'
            plist.unlink()
            plist.symlink_to(root / 'Real.app/Contents/Info.plist')
            self.assertEqual(c._mounted_bundle_metadata(root, None, app_name='Fixture.app').code, 'SYMLINK_COMPONENT')
            plist.unlink()
            contents.rmdir()
            contents.symlink_to(root / 'Real.app/Contents', target_is_directory=True)
            self.assertEqual(c._mounted_bundle_metadata(root, None, app_name='Fixture.app').code, 'SYMLINK_COMPONENT')

    def test_invalid_or_missing_id_and_oversized_plist_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            contents = app_bundle(directory)
            plist = contents / 'Info.plist'
            for identifier in [None, '', 'org.example.bad id', 'x' * 201, 123]:
                info = {'CFBundleShortVersionString': '1.2.3'}
                if identifier is not None:
                    info['CFBundleIdentifier'] = identifier
                plist.write_bytes(plistlib.dumps(info))
                self.assertEqual(c._mounted_bundle_metadata(directory, None, app_name='Fixture.app').code, 'BUNDLE_ID_INVALID')
            plist.write_bytes(b'x' * (1024 * 1024 + 1))
            self.assertEqual(c._mounted_bundle_metadata(directory, None, app_name='Fixture.app').code, 'PLIST_INVALID')

    def test_discovery_cannot_replace_signed_identity_verification(self):
        with patch.object(c, '_stream_signed_dmg') as download:
            refusal = c.inspect_dmg_artifact('https://example.test/app.dmg', None,
                                            team_id='ABCDEFGHIJ', app_name='Fixture.app')
        self.assertEqual(refusal.code, 'SIGNATURE_IDENTITY_INVALID')
        download.assert_not_called()

    def test_discovery_does_not_search_containers(self):
        with tempfile.TemporaryDirectory() as directory:
            app_bundle(Path(directory) / 'Container')
            self.assertEqual(c._mounted_bundle_metadata(directory, None, app_name='Fixture.app').code, 'NOT_FOUND')

    def test_attached_image_cleanup_failure_never_returns_an_observation(self):
        payload = b'fake image, never mounted'
        def download(url, agent, target, **kwargs):
            self.assertEqual(kwargs, {'https_only': True})
            target.write(payload)
            return len(payload)
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory) / 'work'
            work.mkdir()
            with patch.object(c.tempfile, 'mkdtemp', return_value=str(work)), \
                    patch.object(c, '_stream_to_temp_file', side_effect=download), \
                    patch.object(c, '_mounted_bundle_metadata', return_value=('org.example.fixture', '1.2.3', '7')), \
                    patch.object(c.os.path, 'ismount', return_value=True), \
                    patch.object(c.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                result = c.inspect_dmg_artifact('https://example.test/app.dmg', None, app_name='Fixture.app')
            self.assertEqual(result.code, 'CLEANUP_INCOMPLETE')
            self.assertTrue(result.integrity)
            self.assertEqual(sum(call.args[0][1] == 'detach' for call in run.call_args_list), 2)


@unittest.skipUnless(shutil.which('hdiutil'), 'requires macOS disk-image tools')
class DiscoveryDiskImageTests(unittest.TestCase):
    def test_real_udzo_checks_hash_before_mount_and_detaches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            app_bundle(source)
            dmg = root / 'fixture.dmg'
            subprocess.run(['hdiutil', 'create', '-format', 'UDZO', '-srcfolder', str(source),
                            '-volname', 'IntuneBrewDiscoveryFixture', str(dmg)],
                           capture_output=True, check=True, timeout=60)
            data = dmg.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            real_run = subprocess.run
            mounts = []
            def run(args, **kwargs):
                if args[:2] == ['hdiutil', 'attach']:
                    mounts.append(args[args.index('-mountpoint') + 1])
                return real_run(args, **kwargs)
            def download(url, agent, target, **kwargs):
                self.assertEqual(kwargs, {'https_only': True})
                target.write(data)
                return len(data)
            with patch.object(c, '_stream_to_temp_file', side_effect=download), \
                    patch.object(c.subprocess, 'run', side_effect=run):
                wrong = c.inspect_dmg_artifact('https://example.test/fixture.dmg', None,
                                               '0' * 64, app_name='Fixture.app')
                self.assertEqual(wrong.code, 'CHECKSUM_MISMATCH')
                self.assertEqual(mounts, [])
                raw = fixture('image-fixture', 'Fixture', digest)
                raw['url'] = 'https://example.test/fixture.dmg'
                info = {'url': raw['url'], 'fileName': 'fixture.dmg', 'version': '1.2.3', 'bundleId': None}
                observed = c.discover_missing_bundle_id(info, None, raw, 'image-fixture')
            self.assertIsInstance(observed, c.BundleObservation)
            self.assertEqual((observed.bundle_id, observed.short_version, observed.artifact_sha256),
                             ('org.example.fixture', '1.2.3', digest))
            self.assertEqual(len(mounts), 1)
            self.assertFalse(any(os.path.ismount(path) for path in mounts))
            self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0, 0))


class DownloadResponse:
    def __init__(self, url, status=200, location=None, body=b'dmg-fixture'):
        self.url = url
        self.status_code = status
        self.headers = {} if location is None else {'Location': location}
        self.body = body
        self.closed = False
        self.body_read = False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise c.requests.HTTPError('Fixture HTTP failure')

    def iter_content(self, chunk_size):
        self.body_read = True
        yield self.body

    def close(self):
        self.closed = True


class DiscoveryRedirectTests(unittest.TestCase):
    def test_plaintext_or_invalid_hop_is_never_requested_or_read(self):
        initial = 'https://vendor.example.test/app.dmg'
        for location in ['http://cdn.example.test/app.dmg', 'ftp://cdn.example.test/app.dmg',
                         'https://user:password@cdn.example.test/app.dmg']:
            with self.subTest(location=location):
                response = DownloadResponse(initial, 302, location)
                target = io.BytesIO(b'previous-attempt')
                with patch.object(c.requests.adapters.HTTPAdapter, 'send', autospec=True, return_value=response) as get:
                    self.assertIsNone(c._stream_to_temp_file(initial, 'fixture', target, https_only=True))
                self.assertEqual(get.call_count, 1)
                self.assertEqual(get.call_args.args[1].url, initial)
                self.assertTrue(get.call_args.kwargs['stream'])
                self.assertIsNot(get.call_args.kwargs['verify'], False)
                self.assertEqual(target.getvalue(), b'')
                self.assertTrue(response.closed)
                self.assertFalse(response.body_read)
        with patch.object(c.requests.adapters.HTTPAdapter, 'send') as get:
            with c._https_discovery_response('http://vendor.example.test/app.dmg', 'fixture') as response:
                self.assertIsNone(response)
            get.assert_not_called()

    def test_https_relative_and_cross_host_redirects_preserve_binary(self):
        urls = ['https://vendor.example.test/start', 'https://vendor.example.test/download',
                'https://cdn.example.test/app.dmg']
        responses = [DownloadResponse(urls[0], 302, '/download'),
                     DownloadResponse(urls[1], 307, '//cdn.example.test/app.dmg'),
                     DownloadResponse(urls[2], body=b'validated-fixture-bytes')]
        target = io.BytesIO()
        with patch.object(c.requests.adapters.HTTPAdapter, 'send', autospec=True, side_effect=responses) as get:
            count = c._stream_to_temp_file(urls[0], 'fixture', target, https_only=True)
        self.assertEqual([call.args[1].url for call in get.call_args_list], urls)
        self.assertTrue(all(call.kwargs['stream'] is True for call in get.call_args_list))
        self.assertEqual(count, len(b'validated-fixture-bytes'))
        self.assertEqual(target.getvalue(), b'validated-fixture-bytes')
        self.assertTrue(all(response.closed for response in responses))
        self.assertFalse(any(response.body_read for response in responses[:-1]))
        self.assertTrue(responses[-1].body_read)

    def test_missing_location_and_redirect_cycles_are_bounded_and_closed(self):
        url = 'https://vendor.example.test/app.dmg'
        for location, count in [(None, 1), ('', 1), (url, 11)]:
            with self.subTest(location=location):
                responses = [DownloadResponse(url, 302, location) for _ in range(count)]
                with patch.object(c.requests.adapters.HTTPAdapter, 'send', autospec=True, side_effect=responses) as get:
                    self.assertIsNone(c._stream_to_temp_file(url, 'fixture', io.BytesIO(), https_only=True))
                self.assertEqual(get.call_count, count)
                self.assertTrue(all(response.closed and not response.body_read for response in responses))

    def test_normal_download_keeps_existing_redirect_behaviour(self):
        url = 'https://vendor.example.test/app.dmg'
        response = DownloadResponse(url)
        with patch.object(c.requests, 'get', return_value=response) as get:
            self.assertEqual(c._stream_to_temp_file(url, 'fixture', io.BytesIO()), len(response.body))
        self.assertNotIn('allow_redirects', get.call_args.kwargs)
        self.assertTrue(response.closed)

    def test_no_check_discovery_downgrade_holds_before_any_mount(self):
        raw = fixture(checksum='no_check')
        info = {'url': raw['url'], 'fileName': 'future-one.dmg', 'version': '1.2.3', 'bundleId': None}
        responses = []
        def get(adapter, request, **kwargs):
            self.assertEqual(request.url, raw['url'])
            self.assertTrue(kwargs['stream'])
            response = DownloadResponse(request.url, 302, 'http://attacker.example.test/app.dmg')
            responses.append(response)
            return response
        with patch.object(c.shutil, 'which', return_value='hdiutil'), \
                patch.object(c.requests.adapters.HTTPAdapter, 'send', autospec=True, side_effect=get), \
                patch.object(c.subprocess, 'run') as run:
            with self.assertRaises(c.CatalogVersionHold) as held:
                c.discover_missing_bundle_id(info, None, raw, raw['token'])
        self.assertEqual(held.exception.code, 'BUNDLE_ID_DOWNLOAD_FAILED')
        self.assertEqual(len(responses), len(c.DOWNLOAD_USER_AGENTS))
        self.assertTrue(all(response.closed and not response.body_read for response in responses))
        run.assert_not_called()
        self.assertIsNone(info['bundleId'])

    def test_real_requests_redirect_body_is_never_preloaded(self):
        class TrackedBody(io.BytesIO):
            bytes_read = 0
            def read(self, *args, **kwargs):
                data = super().read(*args, **kwargs)
                self.bytes_read += len(data)
                return data
        url = 'https://vendor.example.test/app.dmg'
        body = TrackedBody(b'x' * 4096)
        def send(adapter, request, **kwargs):
            self.assertEqual(request.url, url)
            self.assertTrue(kwargs['stream'])
            self.assertIsNot(kwargs['verify'], False)
            response = c.requests.Response()
            response.url = url
            response.request = request
            response.status_code = 302
            response.headers['Location'] = 'http://attacker.example.test/app.dmg'
            response.raw = body
            return response
        target = io.BytesIO()
        with patch.object(c.requests.adapters.HTTPAdapter, 'send', autospec=True, side_effect=send) as transport, \
                patch.object(c, 'MAX_DOWNLOAD_BYTES', 8):
            self.assertIsNone(c._stream_to_temp_file(url, 'fixture', target, https_only=True))
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(body.bytes_read, 0)
        self.assertTrue(body.closed)
        self.assertEqual(target.getvalue(), b'')

    def test_terminal_body_still_obeys_size_cap_and_closes_transport(self):
        url = 'https://vendor.example.test/app.dmg'
        response = DownloadResponse(url, body=b'x' * 9)
        with patch.object(c.requests.adapters.HTTPAdapter, 'send', autospec=True, return_value=response), \
                patch.object(c, 'MAX_DOWNLOAD_BYTES', 8):
            with self.assertRaises(c._OversizedDownload):
                c._stream_to_temp_file(url, 'fixture', io.BytesIO(), https_only=True)
        self.assertTrue(response.closed)


if __name__ == '__main__':
    unittest.main()
