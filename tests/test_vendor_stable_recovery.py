"""Offline availability recovery fixtures; no real app, publisher or network."""
from dataclasses import replace
import contextlib
import io
import json
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import test_dmg_reconciliation as integration
import version_relation as policy

c = integration.c
SHA, BUNDLE = integration.SHA, integration.BUNDLE
TEAM = 'TESTTEAM01'
STABLE = 'https://example.invalid/download/latest'
RESOLVED = 'https://example.invalid/Fixture-161.dmg'
CURRENT = 'https://example.invalid/Fixture-162.dmg'
SOURCE = c.StableSource(STABLE, TEAM, frozenset({'example.invalid'}))


def signed(short='161', **changes):
    return replace(policy.SignedBundleObservation(SHA, BUNDLE, short, '1067', team_id=TEAM), **changes)


def recovery(**changes):
    return replace(policy.RecoveryInput(404, '162', 'a' * 64, STABLE, RESOLVED,
        BUNDLE, TEAM, signed(), prior=policy.PriorEntry('162', 'a' * 64, CURRENT)), **changes)


class RecoveryPolicyTests(unittest.TestCase):
    def test_verified_older_or_equal_stable_version_can_replace_unavailable_release(self):
        for status in [404, 410]:
            for version in ['161', '162', '161.2']:
                decision = policy.availability_recovery(recovery(current_status=status, observation=signed(version),
                    resolved_url='https://example.invalid/Fixture-'+version+'.dmg'))
                self.assertEqual((decision.action, decision.version, decision.sha, decision.relation, decision.verified),
                                 ('REFRESH' if version == '162' else 'WRITE', version, SHA, 'AVAILABILITY_RECOVERY', True))

    def test_wrong_identity_signature_inspector_or_hash_never_recovers(self):
        for observation in [signed(bundle_id='org.example.other'), signed(team_id='OTHERTEAM1'),
                            signed(inspector=policy.INSPECTOR_VERSION), signed(artifact_sha256='invalid'),
                            policy.BundleObservation(SHA, BUNDLE, '161'),
                            policy.InspectionRefusal('SIGNATURE_UNVERIFIED', True)]:
            self.assertEqual(policy.availability_recovery(recovery(observation=observation)).action, 'HOLD')
        for declared in [None, 'no_check', 'A' * 64]:
            self.assertEqual(policy.availability_recovery(recovery(declared_sha256=declared)).action, 'HOLD')

    def test_uncertain_availability_mutable_url_and_prerelease_or_newer_version_hold(self):
        for status in [200, 301, 403, 429, 500, None, True]:
            self.assertEqual(policy.availability_recovery(recovery(current_status=status)).action, 'HOLD')
        self.assertEqual(policy.availability_recovery(recovery(resolved_url=STABLE)).action, 'HOLD')
        for url in ['https://example.invalid/latest.dmg', 'https://example.invalid/Fixture-161.2.dmg',
                    RESOLVED+'?token=fake', 'http://example.invalid/Fixture-161.dmg']:
            self.assertEqual(policy.availability_recovery(recovery(resolved_url=url)).action, 'HOLD')
        for version in ['163', '162.1', '161rc1', '0161', '161\n', '١٦١', 'x' * 65]:
            self.assertEqual(policy.availability_recovery(recovery(observation=signed(version))).action, 'HOLD')

    def test_optional_sidecar_mismatch_holds_and_verified_same_release_is_noop(self):
        self.assertEqual(policy.availability_recovery(recovery(vendor_sha256='b' * 64)).reason,
                         'VENDOR_CHECKSUM_MISMATCH')
        self.assertTrue(policy.availability_recovery(recovery(vendor_sha256=SHA)).verified)
        prior = policy.PriorEntry('161', SHA, RESOLVED)
        self.assertEqual(policy.availability_recovery(recovery(prior=prior)).action, 'NOOP')
        self.assertEqual(policy.availability_recovery(recovery(prior=replace(prior, sha='b' * 64))).action, 'REFRESH')


class RecoveryProducerTests(unittest.TestCase):
    def app(self, token='fixture'):
        return {'version': '162', 'url': CURRENT, 'vendor_url': CURRENT, 'bundleId': BUNDLE,
                'fileName': 'fixture.dmg', 'homebrew_cask': token}

    def test_two_different_registered_publishers_use_the_same_generic_path(self):
        for token, team, host in [('fixture', TEAM, 'example.invalid'),
                                  ('another', 'SECONDTEAM', 'second.invalid')]:
            source = c.StableSource('https://'+host+'/latest', team, frozenset({host}))
            resolved = 'https://'+host+'/Release-161.dmg'
            app = self.app(token); app['url'] = 'https://'+host+'/Release-162.dmg'
            prior = dict(app)
            obs = signed(team_id=team)
            with patch.dict(c.VENDOR_STABLE_SOURCES, {token: source}, clear=True), \
                    patch.object(c, '_current_vendor_status', return_value=404), \
                    patch.object(c, '_resolve_vendor_stable', return_value=resolved), \
                    patch.object(c, 'inspect_dmg_artifact', return_value=obs) as inspect, \
                    patch.object(c, 'read_vendor_sha256', side_effect=lambda url:
                        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0, 0))) as sidecar:
                self.assertTrue(c._recover_vendor_stable(app, prior,
                    {'version': '162', 'url': prior['url'], 'sha256': 'a' * 64}, token))
            self.assertEqual((app['version'], app['sha'], app['url'], app['vendor_url'], app['fileName']),
                             ('161', SHA, resolved, resolved, 'Release-161.dmg'))
            inspect.assert_called_once()
            self.assertEqual(inspect.call_args.kwargs['team_id'], team)
            sidecar.assert_called_once_with(resolved)

    def test_no_recovery_on_healthy_forbidden_or_uncertain_current_response(self):
        for status in [200, 403, 429, None]:
            with patch.dict(c.VENDOR_STABLE_SOURCES, {'fixture': SOURCE}, clear=True), \
                    patch.object(c, '_current_vendor_status', return_value=status), \
                    patch.object(c, '_resolve_vendor_stable') as resolve:
                app = self.app()
                self.assertFalse(c._recover_vendor_stable(app, dict(app),
                    {'version': '162', 'url': CURRENT, 'sha256': 'a' * 64}, 'fixture'))
                resolve.assert_not_called()
                self.assertEqual(app['version'], '162')

    def test_unregistered_cask_never_probes(self):
        with patch.object(c, '_current_vendor_status') as probe:
            self.assertFalse(c._recover_vendor_stable(self.app('unregistered'), {}, {}, 'unregistered'))
        probe.assert_not_called()

    def test_original_cask_recovers_automatically_when_its_download_returns(self):
        app = self.app(); prior = dict(app, version='161', sha=SHA, url=RESOLVED)
        with patch.dict(c.VENDOR_STABLE_SOURCES, {'fixture': SOURCE}, clear=True), \
                patch.object(c, '_current_vendor_status', return_value=200), \
                patch.object(c, '_resolve_vendor_stable') as resolve, \
                patch.object(c.shutil, 'which', return_value='/fake/hdiutil'), \
                patch.object(c, 'inspect_dmg_artifact', return_value=policy.BundleObservation(SHA, BUNDLE, '162')):
            c.reconcile_vendor_dmg(app, prior, {'version': '162', 'url': CURRENT, 'sha256': SHA}, 'fixture')
        self.assertEqual((app['version'], app['url']), ('162', CURRENT))
        resolve.assert_not_called()

    def test_collector_writes_all_artifact_fields_together_and_failure_retains_prior_bytes(self):
        helper = integration.CollectorIntegrationTests()
        for obs, vendor, accepted in [(signed(), None, True), (signed(team_id='WRONGTEAM1'), None, False),
                                      (signed(), 'b' * 64, False)]:
            with patch.dict(c.VENDOR_STABLE_SOURCES, {'fixture': SOURCE}, clear=True), \
                    patch.object(c, '_current_vendor_status', return_value=404), \
                    patch.object(c, '_resolve_vendor_stable', return_value=RESOLVED):
                old, new, report = helper.run_case(obs, raw='162', prior='162',
                                                  declared_sha='a' * 64, vendor_sha=vendor, current_url=CURRENT)
            if accepted:
                data = json.loads(new)
                self.assertEqual((data['version'], data['sha'], data['url'], data['vendor_url'], data['fileName']),
                                 ('161', SHA, RESOLVED, RESOLVED, 'Fixture-161.dmg'))
                self.assertEqual(report['versionEvidence'][0]['relation'], 'AVAILABILITY_RECOVERY')
                self.assertEqual(report['failures'], [])
            else:
                self.assertEqual(old, new)
                self.assertTrue(report['failures'])


class StableTransportTests(unittest.TestCase):
    def response(self, status=200, url=RESOLVED, body=b'fake DMG', **headers):
        result = Mock(status_code=status, url=url, headers={'content-type': 'application/x-apple-diskimage', **headers})
        result.iter_content.return_value = [body]
        return result

    def test_redirects_are_bounded_and_stay_within_publisher_hosts(self):
        first = self.response(302, STABLE, Location=RESOLVED)
        last = self.response()
        with patch.object(c.requests, 'get', side_effect=[first, last]) as get:
            self.assertEqual(c._resolve_vendor_stable(SOURCE), RESOLVED)
        self.assertEqual(get.call_count, 2)
        self.assertTrue(all(call.kwargs['allow_redirects'] is False for call in get.call_args_list))
        first.close.assert_called_once(); last.close.assert_called_once()
        for location in ['https://other.invalid/file.dmg', RESOLVED+'?secret=fake',
                         'http://example.invalid/file.dmg', 'https://user@example.invalid/file.dmg', STABLE]:
            with patch.object(c.requests, 'get', return_value=self.response(302, STABLE, Location=location)) as get:
                with self.assertRaises(c.CatalogVersionHold): c._resolve_vendor_stable(SOURCE)
            get.assert_called_once()

    def test_mutable_final_endpoint_or_too_many_redirects_hold(self):
        with patch.object(c.requests, 'get', return_value=self.response(url=STABLE)):
            with self.assertRaises(c.CatalogVersionHold): c._resolve_vendor_stable(SOURCE)
        responses = [self.response(302, STABLE, Location='/hop'+str(i)) for i in range(4)]
        with patch.object(c.requests, 'get', side_effect=responses) as get:
            with self.assertRaises(c.CatalogVersionHold): c._resolve_vendor_stable(SOURCE)
        self.assertEqual(get.call_count, 4)

    def test_signed_download_has_no_redirect_retry_and_checks_body_size_and_type(self):
        reply = self.response()
        with patch.object(c.requests, 'get', return_value=reply) as get:
            target = io.BytesIO(); c._stream_signed_dmg(RESOLVED, target)
            self.assertEqual(target.getvalue(), b'fake DMG')
        get.assert_called_once(); self.assertFalse(get.call_args.kwargs['allow_redirects'])
        for reply in [self.response(status=302), self.response(url=STABLE),
                      self.response(body=b'<html>error</html>'), self.response(body=b''),
                      self.response(**{'content-type': 'text/html'}),
                      self.response(**{'content-length': '100'})]:
            with patch.object(c.requests, 'get', return_value=reply), self.assertRaises(c.CatalogVersionHold):
                c._stream_signed_dmg(RESOLVED, io.BytesIO())
            reply.close.assert_called_once()

    def test_deadline_escapes_broad_inspector_handlers_and_restores_alarm(self):
        handler = signal.getsignal(signal.SIGALRM)
        def stalled(*args): time.sleep(0.3)
        with patch.object(c, '_stream_signed_dmg', side_effect=stalled), \
                patch.object(c.subprocess, 'run') as process, self.assertRaises(c.CatalogVersionHold):
            with c._stable_budget(0.02):
                c.inspect_dmg_artifact(RESOLVED, BUNDLE, team_id=TEAM,
                                      _cleanup_deadline=lambda: signal.setitimer(signal.ITIMER_REAL, 0))
        process.assert_not_called()
        self.assertEqual(signal.getsignal(signal.SIGALRM), handler)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0, 0))

    def test_current_probe_timeout_uses_normal_path_and_closes_responses(self):
        with patch.object(c.requests, 'get', side_effect=c.requests.Timeout):
            self.assertIsNone(c._current_vendor_status(CURRENT, SOURCE))
        reply = self.response(404, CURRENT)
        with patch.object(c.requests, 'get', return_value=reply):
            self.assertEqual(c._current_vendor_status(CURRENT, SOURCE), 404)
        reply.close.assert_called_once(); reply.iter_content.assert_not_called()

    def test_late_deadline_during_context_cleanup_stays_a_per_app_hold(self):
        @contextlib.contextmanager
        def late(seconds):
            yield
            raise c._StableReleaseDeadline()
        reply = self.response(404, CURRENT)
        with patch.object(c, '_stable_budget', late), patch.object(c.requests, 'get', return_value=reply):
            self.assertIsNone(c._current_vendor_status(CURRENT, SOURCE))
        app = RecoveryProducerTests().app(); original = dict(app)
        with patch.dict(c.VENDOR_STABLE_SOURCES, {'fixture': SOURCE}, clear=True), \
                patch.object(c, '_current_vendor_status', return_value=404), \
                patch.object(c, '_stable_budget', late), \
                patch.object(c, '_resolve_vendor_stable', return_value=RESOLVED), \
                patch.object(c, 'inspect_dmg_artifact', return_value=signed()):
            with self.assertRaises(c.CatalogVersionHold) as result:
                c._recover_vendor_stable(app, original, {'version': '162', 'url': CURRENT,
                                         'sha256': 'a' * 64}, 'fixture')
        self.assertEqual(result.exception.code, 'STABLE_DEADLINE_EXCEEDED')
        self.assertEqual(app, original)


class SignatureTests(unittest.TestCase):
    def test_signed_inspector_hashes_one_file_and_detaches_after_signature_check(self):
        fixture = integration.InspectorTests(); fixture.setUp()
        try:
            fixture.prepare = lambda root: integration.fake_app(root, short='161', build='1067')
            def process(args, **kwargs):
                return Mock(returncode=0) if args[0] == '/usr/bin/codesign' else fixture.process_call(args, **kwargs)
            fixture.process.side_effect = process
            with patch.object(c, '_stream_signed_dmg', side_effect=lambda url, target:
                              fixture.download(url, 'fixture', target)) as download:
                obs = c.inspect_dmg_artifact(RESOLVED, BUNDLE, team_id=TEAM)
            self.assertEqual(obs, signed())
            download.assert_called_once()
            self.assertEqual(fixture.received, [integration.ARTIFACT])
            self.assertFalse(fixture.mounted)
            self.assertFalse(fixture.mount_root.parent.exists())
            self.assertEqual(fixture.process.call_args.args[0][1], 'detach')
        finally:
            fixture.doCleanups()

    def test_failed_signed_mount_cleanup_cannot_publish(self):
        fixture = integration.InspectorTests(); fixture.setUp()
        try:
            def process(args, **kwargs):
                if args[0] == '/usr/bin/codesign': return Mock(returncode=0)
                return fixture.process_call(args, **kwargs) if args[1] == 'attach' else Mock(returncode=1)
            fixture.process.side_effect = process
            with patch.object(c, '_stream_signed_dmg', side_effect=lambda url, target:
                              fixture.download(url, 'fixture', target)), patch.object(c.shutil, 'rmtree') as remove:
                refusal = c.inspect_dmg_artifact(RESOLVED, BUNDLE, team_id=TEAM)
                remove.assert_not_called()
            self.assertEqual((refusal.code, refusal.integrity), ('CLEANUP_INCOMPLETE', True))
            fixture.mounted = False
            import shutil
            shutil.rmtree(fixture.mount_root.parent)
        finally:
            fixture.doCleanups()

    def test_requirement_binds_apple_developer_id_team_and_bundle(self):
        with tempfile.TemporaryDirectory() as root:
            integration.fake_app(root, short='161', bundle=BUNDLE)
            with patch.object(c.subprocess, 'run', return_value=Mock(returncode=0)) as run:
                self.assertEqual(c._mounted_bundle_metadata(root, BUNDLE, TEAM), ('161', None))
            args = run.call_args.args[0]
            self.assertEqual(args[:4], ['/usr/bin/codesign', '--verify', '--deep', '--strict'])
            requirement = args[4]
            for text in ['anchor apple generic', '1.2.840.113635.100.6.2.6',
                         '1.2.840.113635.100.6.1.13', TEAM, BUNDLE]:
                self.assertIn(text, requirement)
            self.assertEqual(run.call_args.kwargs['timeout'], 120)
            with patch.object(c.subprocess, 'run', return_value=Mock(returncode=1)):
                result = c._mounted_bundle_metadata(root, BUNDLE, TEAM)
            self.assertEqual((result.code, result.integrity), ('SIGNATURE_UNVERIFIED', True))


if __name__ == '__main__':
    unittest.main()
