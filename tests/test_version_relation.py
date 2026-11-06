"""Synthetic fixtures and recorded strings; none are live installation evidence."""
import ast
from dataclasses import fields, replace
import sys
from pathlib import Path
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))
import version_relation as policy

SHA = 'a' * 64
BUNDLE = 'org.example.fixture'


def request(raw='2.0,2', short='2.0+2', prior='1.0', caps=frozenset({'plus_build', 'decorated_text'})):
    return policy.ReconcileInput(raw, policy.generic_legacy_truncate(raw), SHA,
                                 'https://example.invalid/app.dmg', BUNDLE,
                                 policy.PriorEntry(prior, 'b' * 64, 'https://example.invalid/old.dmg') if prior else None,
                                 policy.BundleObservation(SHA, BUNDLE, short), caps)


class RelationshipTests(unittest.TestCase):
    def test_recorded_and_generic_relationships(self):
        cases = [('0.4.28,2', '0.4.28+2', 'RENDER_PLUS'),
                 ('10.0.2,6590', '10.0.2 (build 6590)', 'RENDER_PAREN_BUILD'),
                 ('2.152.0,stable.3,8636580', '2.152.0-stable.3', 'RENDER_CHANNEL'),
                 ('1.207.0.0', '1.207.0', 'PAD'), ('0.99.0.0', '0.99', 'PAD'),
                 ('3.1,77', '3.1+77', 'RENDER_PLUS'), ('5.0,12', '5.0 (build 12)', 'RENDER_PAREN_BUILD'),
                 ('9.9.9,stable', '9.9.9-stable', 'RENDER_CHANNEL'), ('7.84', '7.84.0', 'PAD')]
        for raw, short, relation in cases:
            with self.subTest(raw=raw, short=short):
                self.assertEqual(policy.relationship(raw, short), relation)

    def test_unproven_channels_builds_dialects_and_near_misses(self):
        cases = [('6.6.1', '6.6.1-demo'), ('6.6.1,demo', '6.6.1-demo'),
                 ('2.0,beta.1', '2.0-beta.1'), ('2,1', '2+1'),
                 ('2.0,02', '2.0+02'), ('2.0,2', '2.0+3'),
                 ('2.0,2,3', '2.0+3'), ('2.0,2,beta', '2.0+2'),
                 ('2.0,stable.3,trial', '2.0-stable.3'),
                 ('2.0,2', '2.0(build 2)'), ('2.0,2', '2.0 (Build 2)'),
                 ('2.0,2', '2.0 (build 2) '), ('2.0,٢', '2.0+٢'), ('2.0_2', '2.0+2'),
                 ('18.7.0', '18.6.6'), ('2026.11.03.912', '2026.11.05'),
                 ('26.8.2', '26.8.2.2'), ('12.11.12', '12.11.12.2'), ('4.5', '4.5.102000'),
                 ('1.207.0', '1.207.0.1'), ('1.207.0', '1.207.00'), ('1.207.0,2', '1.207.0.0'),
                 ('1.99.55.0', '157.1.99.55'), ('160.0b5', '160.0'),
                 ('5.8.2', '5.8.2(095C)'), ('7.85', '7.85.0_19ce87au')]
        for raw, short in cases:
            with self.subTest(raw=raw, short=short):
                self.assertIsNone(policy.relationship(raw, short))

    def test_legacy_truncation_parity(self):
        for raw in ['1.2.3,45', '1.2_45', '1.2_45,67', '1.2+3', '1.2-stable.3', 'opaque']:
            self.assertEqual(policy.generic_legacy_truncate(raw), raw.split(',')[0].split('_')[0])


class DecisionTests(unittest.TestCase):
    def test_newer_proven_release_and_new_app(self):
        for i in [request(), request(prior=None), request('1.207.0.0', '1.207.0', '1.202.0.0')]:
            with self.subTest(i=i):
                d = policy.reconcile(i)
                self.assertEqual(d.action, 'WRITE')
                self.assertEqual(d.version, i.observation.short_version)
                self.assertTrue(d.verified)

    def test_verified_caps_and_explicit_missing_caps_do_not_release_rows(self):
        self.assertIn('plus_build', policy.CATALOG_CONSUMER_CAPABILITIES)
        self.assertIn('decorated_text', policy.CATALOG_CONSUMER_CAPABILITIES)
        for raw, short in [('2.0,2', '2.0+2'), ('2.0,2', '2.0 (build 2)'), ('2.0,stable.3', '2.0-stable.3')]:
            d = policy.reconcile(request(raw, short, caps=frozenset()))
            self.assertEqual((d.action, d.reason), ('HOLD', 'CONSUMER_CAPABILITY_PENDING'))

    def test_checksum_or_prefix_is_never_semantic_proof(self):
        for raw, short in [('2.0', '2.0-demo'), ('2.0', '2.0.99'), ('18.7.0', '18.6.6')]:
            d = policy.reconcile(request(raw, short))
            self.assertEqual((d.action, d.reason), ('HOLD', 'RELATION_UNPROVEN'))

    def test_order_and_detection_string_are_distinct(self):
        for i, reason in [(request('1.207.0.0', '1.207.0', '1.207.0.0'), 'EQUAL_ORDER_TEXT_DIFFERS'),
                          (request('0.4.28', '0.4.28', '0.4.28+2'), 'EQUAL_ORDER_TEXT_DIFFERS'),
                          (request('2.0', '2.0', '3.0'), 'DETECTION_REGRESSION'),
                          (request('2.0,2', '2.0+2', 'opaque'), 'PRIOR_ORDER_UNKNOWN')]:
            d = policy.reconcile(i)
            self.assertEqual((d.action, d.reason), ('HOLD', reason))

    def test_refresh_requires_identical_detection_text(self):
        i = request(prior='2.0+2')
        self.assertEqual(policy.reconcile(i).action, 'REFRESH')
        same = replace(i, prior=policy.PriorEntry('2.0+2', SHA, i.url))
        self.assertEqual(policy.reconcile(same).action, 'NOOP')

    def test_no_positive_cache_and_no_check_is_fresh(self):
        i = request(prior='2.0+2')
        same = replace(i, prior=policy.PriorEntry('2.0+2', SHA, i.url))
        self.assertEqual(policy.plan(same).reason, 'SAME_PINNED_ARTIFACT')
        self.assertEqual(policy.plan(replace(same, declared_sha256=None)).action, 'INSPECT')
        self.assertEqual(policy.plan(replace(same, url='https://example.invalid/new.dmg')).action, 'INSPECT')
        self.assertEqual(policy.plan(request('2.0', '2.0', '2.0')).action, 'LEGACY')

    def test_refusals_and_observation_binding(self):
        i = request()
        for obs in [policy.InspectionRefusal('AMBIGUOUS', True),
                    policy.InspectionRefusal('CHECKSUM_MISMATCH', True)]:
            self.assertEqual(policy.reconcile(replace(i, observation=obs)).action, 'HOLD')
        legacy = policy.reconcile(replace(i, observation=policy.InspectionRefusal('MOUNT_FAILED', False, SHA)))
        self.assertEqual((legacy.action, legacy.version, legacy.verified), ('LEGACY_PASS', '2.0', False))
        for obs in [replace(i.observation, bundle_id='org.example.wrong'),
                    replace(i.observation, artifact_sha256='b' * 64), replace(i.observation, inspector='old')]:
            self.assertEqual(policy.reconcile(replace(i, observation=obs)).reason, 'OBSERVATION_INCONSISTENT')

    def test_existing_transform_requires_exact_bundle(self):
        i = replace(request('2.0,90', '90'), legacy_version='90')
        self.assertEqual(policy.reconcile(i).relation, 'BRANCH_EXACT')
        self.assertEqual(policy.reconcile(replace(i, observation=replace(i.observation, short_version='2.0+90'))).action, 'HOLD')

    def test_pure_module_and_no_tenant_authority(self):
        tree = ast.parse((SCRIPTS / 'version_relation.py').read_text())
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        imports |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual(imports, {'re', 'dataclasses'})
        self.assertEqual({f.name for f in fields(policy.Decision)}, {'action', 'version', 'sha', 'relation', 'reason', 'verified'})
        self.assertEqual(policy.reconcile(request()), policy.reconcile(request()))


if __name__ == '__main__':
    unittest.main()
