"""Known bundle identities require exact artifact-bound evidence, not old metadata."""
import copy
import json
import unittest
from unittest.mock import patch
import test_bundle_id_discovery as discovery

c = discovery.c
SHA = discovery.DIGEST


class IdentityPlanTests(unittest.TestCase):
    def test_every_artifact_selection_binding_is_required(self):
        evidence = dict(inspector=c.IDENTITY_INSPECTOR_VERSION, artifactSha256=SHA,
                        url='https://example.test/app.dmg', appName='Fixture.app', bundleId='org.example.fixture')
        args = (evidence, evidence['url'], SHA, SHA, evidence['appName'], evidence['bundleId'])
        self.assertEqual(c.identity_plan(*args), 'REUSE')
        self.assertEqual(c.identity_plan(evidence, evidence['url'], None, SHA, evidence['appName'], evidence['bundleId']), 'REUSE')
        for field in evidence:
            changed = {**evidence, field: 'different'}
            self.assertEqual(c.identity_plan(changed, *args[1:]), 'INSPECT', field)
        self.assertEqual(c.identity_plan(evidence, evidence['url'], 'b'*64, SHA, evidence['appName'], evidence['bundleId']), 'INSPECT')
        self.assertEqual(c.identity_plan(evidence, evidence['url'], None, 'b'*64, evidence['appName'], evidence['bundleId']), 'INSPECT')
        self.assertEqual(c.identity_plan(None, *args[1:]), 'INSPECT')

    def test_budget_bounds_attempts_bytes_and_time(self):
        with patch.object(c.time, 'monotonic', return_value=10):
            budget = c.IdentityBudget(artifacts=1, byte_limit=4, seconds=2)
            self.assertTrue(budget.reserve())
            self.assertFalse(budget.reserve())
            budget.charge(4)
            with self.assertRaises(c._IdentityBudgetExceeded):
                budget.charge(1)
        with patch.object(c.time, 'monotonic', return_value=13):
            self.assertFalse(budget.reserve())
            with self.assertRaises(c._IdentityBudgetExceeded):
                budget.charge(0)


class KnownIdentityCollectorTests(unittest.TestCase):
    def collect(self, data, observation, prior):
        return discovery.DiscoveryCollectorTests().collect(data, observation, prior)

    def prior(self, data):
        return dict(name=data['name'][0], homebrew_cask=data['token'], version=data['version'],
                    bundleId='org.example.old', url=data['url'], sha=SHA)

    def test_same_pinned_artifact_corrects_id_without_asserting_prefix_version_relation(self):
        data = discovery.fixture(); prior = self.prior(data)
        obs = c.BundleObservation(SHA, 'org.example.new', 'v1.2.3', 'v1.2.3')
        raw, _, failures, calls, hashes = self.collect(data, obs, prior)
        result = json.loads(raw)
        self.assertEqual(result['bundleId'], obs.bundle_id)
        self.assertEqual((result['version'], result['sha'], result['url']), (prior['version'], SHA, prior['url']))
        self.assertEqual(result['bundleIdEvidence']['appName'], 'Future One.app')
        self.assertEqual((len(calls), hashes, failures), (1, 0, []))
        self.assertEqual(c.version_evidence[-1]['action'], 'IDENTITY_CORRECTION')
        self.assertFalse(c.version_evidence[-1]['versionVerified'])
        self.assertEqual(c.identity_evidence[-1]['status'], 'CORRECTED')

    def test_bound_evidence_reuse_and_stale_evidence_invalidated_before_version_shortcut(self):
        data = discovery.fixture(); prior = self.prior(data)
        prior['bundleIdEvidence'] = dict(inspector=c.IDENTITY_INSPECTOR_VERSION, artifactSha256=SHA,
            url=data['url'], appName='Future One.app', bundleId=prior['bundleId'])
        obs = c.BundleObservation(SHA, prior['bundleId'], '1.2.3', '7')
        raw, _, failures, calls, _ = self.collect(data, obs, prior)
        self.assertEqual((len(calls), failures), (0, []))
        self.assertEqual(json.loads(raw)['bundleIdEvidence'], prior['bundleIdEvidence'])
        changed = copy.deepcopy(prior); changed['bundleIdEvidence']['appName'] = 'Helper.app'
        raw, _, failures, calls, _ = self.collect(data, obs, changed)
        self.assertEqual((len(calls), failures), (1, []))
        self.assertEqual(json.loads(raw)['bundleIdEvidence']['appName'], 'Future One.app')

    def test_changed_artifact_unproven_version_preserves_previous_file(self):
        data = discovery.fixture(); prior = self.prior(data); prior['sha'] = 'b'*64
        obs = c.BundleObservation(SHA, 'org.example.new', 'v1.2.3', 'v1.2.3')
        raw, before, failures, calls, _ = self.collect(data, obs, prior)
        self.assertEqual(raw, before)
        self.assertEqual(failures[0]['reason'], 'IDENTITY_MISMATCH_HELD')
        self.assertEqual(len(calls), 1)
        self.assertEqual(c.identity_evidence[-1]['status'], 'REFUSED')

    def test_known_id_integrity_or_missing_root_refusals_preserve_file(self):
        data = discovery.fixture(); prior = self.prior(data)
        for code, integrity in [('CHECKSUM_MISMATCH', True), ('NOT_FOUND', False), ('CLEANUP_INCOMPLETE', True)]:
            with self.subTest(code=code):
                raw, before, failures, _, _ = self.collect(data, c.InspectionRefusal(code, integrity), prior)
                self.assertEqual(raw, before)
                self.assertEqual(failures[0]['reason'], 'BUNDLE_ID_' + code)

    def test_unavailable_download_defers_without_fabricating_proof(self):
        data = discovery.fixture(); prior = self.prior(data)
        raw, _, failures, calls, _ = self.collect(data, c.InspectionRefusal('DOWNLOAD_FAILED', False), prior)
        self.assertEqual(failures, [])
        self.assertEqual(len(calls), 1)
        self.assertNotIn('bundleIdEvidence', json.loads(raw))
        self.assertEqual(c.identity_evidence[-1]['status'], 'DEFERRED')

    def test_changed_artifact_with_proven_version_updates_id_and_version_once(self):
        data = discovery.fixture(); prior = self.prior(data); prior['version'] = '1.2.2'; prior['sha'] = 'b'*64
        obs = c.BundleObservation(SHA, 'org.example.new', '1.2.3', '7')
        raw, _, failures, calls, _ = self.collect(data, obs, prior)
        result = json.loads(raw)
        self.assertEqual((result['bundleId'], result['version'], result['sha']), (obs.bundle_id, '1.2.3', SHA))
        self.assertEqual((len(calls), failures), (1, []))
        self.assertTrue(c.version_evidence[-1]['versionVerified'])

    def test_zero_backfill_budget_preserves_entry_without_attaching_evidence(self):
        data = discovery.fixture(); prior = self.prior(data)
        with patch.object(c.IdentityBudget, 'reserve', return_value=False):
            raw, _, failures, calls, _ = self.collect(data, None, prior)
        self.assertEqual((len(calls), failures), (0, []))
        self.assertEqual(json.loads(raw)['bundleId'], prior['bundleId'])
        self.assertNotIn('bundleIdEvidence', json.loads(raw))
        self.assertEqual(c.identity_evidence[-1]['status'], 'DEFERRED')

    def test_same_id_same_artifact_records_identity_without_inventing_version_proof(self):
        data = discovery.fixture(); prior = self.prior(data)
        obs = c.BundleObservation(SHA, prior['bundleId'], 'v1.2.3', 'v1.2.3')
        raw, _, failures, calls, _ = self.collect(data, obs, prior)
        result = json.loads(raw)
        self.assertEqual((len(calls), failures), (1, []))
        self.assertEqual(result['version'], prior['version'])
        self.assertEqual(result['bundleIdEvidence']['bundleId'], prior['bundleId'])
        self.assertFalse(c.version_evidence[-1]['versionVerified'])

    def test_no_check_same_bytes_correct_or_confirm_identity_without_version_claim(self):
        data = discovery.fixture(checksum='no_check'); prior = self.prior(data)
        for bundle in [prior['bundleId'], 'org.example.new']:
            with self.subTest(bundle=bundle):
                obs = c.BundleObservation(SHA, bundle, 'v1.2.3', 'v1.2.3')
                raw, _, failures, calls, hashes = self.collect(data, obs, prior)
                result = json.loads(raw)
                self.assertEqual((failures, len(calls), hashes), ([], 1, 0))
                self.assertEqual((result['version'], result['sha'], result['bundleId']),
                                 (prior['version'], SHA, bundle))
                self.assertFalse(c.version_evidence[-1]['versionVerified'])

    def test_matching_identity_does_not_add_hold_to_unchanged_version_legacy_lane(self):
        for checksum in [SHA, 'no_check']:
            with self.subTest(checksum=checksum):
                data = discovery.fixture(checksum=checksum); prior = self.prior(data); prior['sha'] = 'b'*64
                obs = c.BundleObservation(SHA, prior['bundleId'], 'v1.2.3', 'v1.2.3')
                raw, _, failures, calls, hashes = self.collect(data, obs, prior)
                result = json.loads(raw)
                self.assertEqual((failures, len(calls), hashes), ([], 1, 0))
                self.assertEqual((result['version'], result['sha']), (prior['version'], SHA))
                self.assertEqual(result['bundleIdEvidence']['artifactSha256'], SHA)
                self.assertFalse(c.version_evidence[-1]['versionVerified'])

    def test_no_check_reuses_prior_catalog_evidence_but_invalidates_after_fresh_hash_change(self):
        data = discovery.fixture(checksum='no_check'); prior = self.prior(data)
        prior['bundleIdEvidence'] = dict(inspector=c.IDENTITY_INSPECTOR_VERSION, artifactSha256=SHA,
            url=data['url'], appName='Future One.app', bundleId=prior['bundleId'])
        # run_collector's fresh legacy hash fixture returns zeroes; identity reuse
        # must not suppress that read, nor carry the old proof onto those new bytes.
        raw, _, failures, calls, hashes = self.collect(data, None, prior)
        result = json.loads(raw)
        self.assertEqual((failures, len(calls), hashes), ([], 0, 1))
        self.assertEqual(result['sha'], '0'*64)
        self.assertNotIn('bundleIdEvidence', result)
        self.assertEqual(c.identity_evidence[-1]['status'], 'DEFERRED')

    def test_no_check_second_collection_reuses_identity_for_unchanged_catalog_hash(self):
        data = discovery.fixture(checksum='no_check'); prior = self.prior(data)
        obs = c.BundleObservation('0'*64, prior['bundleId'], 'v1.2.3', 'v1.2.3')
        raw, _, failures, calls, _ = self.collect(data, obs, prior)
        self.assertEqual((failures, len(calls)), ([], 1))
        raw, _, failures, calls, hashes = self.collect(data, None, json.loads(raw))
        result = json.loads(raw)
        self.assertEqual((failures, len(calls), hashes), ([], 0, 1))
        self.assertEqual(result['bundleIdEvidence']['artifactSha256'], result['sha'])
        self.assertEqual(c.identity_evidence[-1]['reason'], 'BOUND_EVIDENCE_REUSED')


class IdentityStreamingAndProgressTests(unittest.TestCase):
    def test_stream_charges_all_attempts_against_one_cumulative_budget(self):
        import contextlib
        import io
        from types import SimpleNamespace
        budget = c.IdentityBudget(byte_limit=5)
        response = SimpleNamespace(raise_for_status=lambda: None, iter_content=lambda **kw: iter([b'ab', b'cd']))
        with patch.object(c, '_https_discovery_response', side_effect=lambda *a: contextlib.nullcontext(response)):
            self.assertEqual(c._stream_to_temp_file('https://example.test/a.dmg', 'fixture', io.BytesIO(), https_only=True, charge=budget.charge), 4)
            with self.assertRaises(c._IdentityBudgetExceeded):
                c._stream_to_temp_file('https://example.test/a.dmg', 'second-agent', io.BytesIO(), https_only=True, charge=budget.charge)
        self.assertEqual(budget.bytes_left, 1)

    def test_progress_rotates_after_actual_attempt_so_a_failed_first_vendor_cannot_starve_later_apps(self):
        import tempfile
        import pathlib
        import os
        with tempfile.TemporaryDirectory() as root:
            previous = os.getcwd()
            try:
                os.chdir(root); pathlib.Path('Apps').mkdir()
                urls = ['https://example.test/' + token + '.json' for token in ['a', 'b', 'c']]
                self.assertEqual(c.identity_scan_order(urls, 'Apps'), urls)
                pathlib.Path('catalog-sync.json').write_text(json.dumps({'identityBackfill': {'lastAttempted': 'b'}}))
                self.assertEqual(c.identity_scan_order(urls, 'Apps'), [urls[2], urls[0], urls[1]])
                pathlib.Path('catalog-sync.json').write_text(json.dumps({'identityBackfill': None}))
                self.assertEqual(c.identity_scan_order(urls, 'Apps'), urls)
            finally:
                os.chdir(previous)

    def test_metadata_id_conflicts_set_priority_but_do_not_supply_identity(self):
        import tempfile
        import pathlib
        import os
        with tempfile.TemporaryDirectory() as root:
            previous = os.getcwd()
            try:
                os.chdir(root); pathlib.Path('Apps').mkdir()
                urls = ['https://example.test/a.json', 'https://example.test/z.json']
                pathlib.Path('Apps/z.json').write_text(json.dumps({'homebrew_cask': 'z', 'bundleId': 'org.example.old'}))
                with patch.dict(c.cask_cache, {urls[1]: {'artifacts': [{'uninstall': [{'quit': 'org.example.new'}]}]}}, clear=True):
                    self.assertEqual(c.identity_scan_order(urls, 'Apps'), urls[::-1])
                self.assertEqual(json.loads(pathlib.Path('Apps/z.json').read_text())['bundleId'], 'org.example.old')
            finally:
                os.chdir(previous)

    def test_inspector_stops_agent_cascade_when_the_shared_byte_budget_is_exhausted(self):
        budget = c.IdentityBudget(byte_limit=5)
        def partial(*args, **kwargs):
            kwargs['charge'](4)
            return None
        with patch.object(c, '_stream_to_temp_file', side_effect=partial) as stream, patch.object(c.subprocess, 'run') as mount:
            observation = c.inspect_dmg_artifact('https://example.test/a.dmg', None, app_name='Fixture.app', _download_charge=budget.charge)
        self.assertEqual(observation.code, 'IDENTITY_BUDGET_EXHAUSTED')
        self.assertFalse(observation.integrity)
        self.assertEqual(stream.call_count, 2)
        mount.assert_not_called()


class UnchangedArtifactVersionHoldTests(unittest.TestCase):
    def test_advanced_cask_text_with_identical_bytes_retains_prior_noop_version(self):
        data = discovery.fixture(); data['version'] = '1.2.4'
        prior = dict(name='Future One', homebrew_cask=data['token'], version='1.2.3',
                     bundleId='org.example.old', url=data['url'], sha=SHA)
        for changed in [False, True]:
            with self.subTest(changed=changed):
                obs = c.BundleObservation(SHA, 'org.example.new' if changed else prior['bundleId'], '1.2.3', '7')
                raw, before, failures, calls, hashes = discovery.DiscoveryCollectorTests().collect(data, obs, prior)
                self.assertEqual((len(calls), hashes), (1, 0))
                if changed:
                    self.assertEqual(raw, before)
                    self.assertEqual(failures[0]['reason'], 'IDENTITY_MISMATCH_HELD')
                else:
                    result = json.loads(raw)
                    self.assertEqual(failures, [])
                    self.assertEqual((result['version'], result['sha']), (prior['version'], prior['sha']))
                    self.assertEqual(result['bundleIdEvidence']['bundleId'], prior['bundleId'])
                    self.assertFalse(c.version_evidence[-1]['versionVerified'])

    def test_real_padded_same_artifact_is_not_held_with_matching_or_changed_id(self):
        for changed in [False, True]:
            data = discovery.fixture(); prior = dict(name='Future One', homebrew_cask=data['token'], version='1.2.3', bundleId='org.example.old', url=data['url'], sha=SHA)
            obs = c.BundleObservation(SHA, 'org.example.new' if changed else prior['bundleId'], '1.2.3.0', '7')
            raw, _, failures, calls, _ = discovery.DiscoveryCollectorTests().collect(data, obs, prior)
            result = json.loads(raw)
            self.assertEqual((failures, len(calls)), ([], 1))
            self.assertEqual((result['bundleId'], result['version'], result['sha']), (obs.bundle_id, prior['version'], SHA))
            self.assertFalse(c.version_evidence[-1]['versionVerified'])
            self.assertEqual(c.identity_evidence[-1]['status'], 'CORRECTED' if changed else 'VERIFIED_MATCH')

    def test_version_policy_holds_preserve_identity_only_and_unchanged_identity_legacy_boundaries(self):
        import version_relation as relation
        from dataclasses import replace
        prior = relation.PriorEntry('1.2.3', SHA, 'https://example.test/a.dmg')
        for changed in [False, True]:
            bundle = 'org.example.new' if changed else 'org.example.old'
            obs = relation.BundleObservation(SHA, bundle, '1.2.3.0', '7')
            request = relation.ReconcileInput('1.2.3', prior.version, SHA, prior.url, bundle, prior, obs)
            for reason in ['PRIOR_ORDER_UNKNOWN', 'DETECTION_REGRESSION', 'CONSUMER_CAPABILITY_PENDING']:
                with patch.object(relation, 'reconcile', return_value=relation.Decision('HOLD', reason=reason)):
                    decision = relation.reconcile_identity(request, 'org.example.old')
                    self.assertEqual((decision.action, decision.version, decision.sha, decision.verified), ('IDENTITY_CORRECTION', prior.version, SHA, False))
                    different = replace(request, declared_sha256='b'*64, observation=replace(obs, artifact_sha256='b'*64))
                    self.assertEqual(relation.reconcile_identity(different, 'org.example.old').action,
                                     'HOLD' if changed else 'LEGACY_PASS')
                    advanced = replace(different, legacy_version='1.2.4', source_release='1.2.4')
                    self.assertEqual(relation.reconcile_identity(advanced, 'org.example.old').action, 'HOLD')
            with patch.object(relation, 'reconcile', return_value=relation.Decision('HOLD', reason='OBSERVATION_INCONSISTENT')):
                self.assertEqual(relation.reconcile_identity(request, 'org.example.old').action, 'HOLD')
