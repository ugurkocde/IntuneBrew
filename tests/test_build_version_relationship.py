"""Recorded public version strings with synthetic identities, hashes and mounts."""
from dataclasses import replace
import json
from pathlib import Path
import unittest

import test_dmg_reconciliation as integration
import test_version_relation as original

policy = original.policy
SHA = original.SHA
ROWS = json.loads((Path(__file__).parent / 'fixtures/source_build_versions.json').read_text())


class BuildRelationshipTests(unittest.TestCase):
    def reconcile_case(self, raw='139.0.6053.38', short='139.0', build='139.0.6053.38', prior='138.0'):
        i = original.request(raw, short, prior)
        return policy.reconcile(replace(i, source_cask='fixture',
                                        observation=replace(i.observation, bundle_version=build)))

    def test_measured_candidates_and_remaining_holds(self):
        for row in ROWS:
            with self.subTest(case=row['case']):
                result = self.reconcile_case(row['source'], row['short'], row['build'], row['prior'])
                if row['relation']:
                    self.assertEqual((result.action, result.version, result.sha, result.relation, result.verified),
                                     ('WRITE', row['short'], SHA, row['relation'], True))
                else:
                    self.assertEqual((result.action, result.reason), ('HOLD', 'RELATION_UNPROVEN'))

    def test_invalid_or_unbound_build_metadata_is_not_a_relation(self):
        triples = [('139.0.6053.38', '139.0', v) for v in [None, 42, '', '139.0.6053.39',
                   '139.0.6053.38 ', '١٣٩.0.6053.38', '139.0.6053.38\n', '1' * 65]]
        triples += [('139.06053.38', '139.0', '139.06053.38'), ('1.2', '1', '1.2'),
                    ('139.00.6053.38', '139.00', '139.00.6053.38'),
                    ('0139.0.6053.38', '0139.0', '0139.0.6053.38'),
                    ('3.35.0743', '3.35', '0743'), ('3.035.743', '3.035', '743'),
                    ('3.35.743.1', '3.35', '743.1'), ('3.35.743,beta', '3.35', '743'),
                    ('3.35.743,3.35,0', '3.35', '743'), ('3.35.743,3.36', '3.35', '743'),
                    ('3.35.743', '3.35 ', '743'), ('3.35.743x', '3.35', '743'),
                    ('9' * 257, '3.35', '743'), ('3.35.743', '3.' + '9' * 63, '743')]

        class TextSubclass(str):
            pass

        triples += [(TextSubclass('3.35.743'), '3.35', '743'),
                    ('3.35.743', TextSubclass('3.35'), '743'),
                    ('3.35.743', '3.35', TextSubclass('743'))]
        for triple in triples:
            with self.subTest(triple=triple):
                self.assertIsNone(policy.build_relationship(*triple))

    def test_prior_order_and_unchanged_short_contracts(self):
        for prior, action, reason in [('opaque', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                                     ('139.0.0', 'HOLD', 'EQUAL_ORDER_TEXT_DIFFERS'),
                                     ('139.0.6053.40', 'HOLD', 'DETECTION_REGRESSION'),
                                     ('139.0', 'REFRESH', 'EXACT_TEXT_UNCHANGED')]:
            with self.subTest(prior=prior):
                d = self.reconcile_case(prior=prior)
                self.assertEqual((d.action, d.reason), (action, reason))
        i = original.request('139.0.6053.38', '139.0', '139.0')
        i = replace(i, observation=replace(i.observation, bundle_version='139.0.6053.38'),
                    prior=policy.PriorEntry('139.0', SHA, i.url))
        self.assertEqual(policy.reconcile(i).action, 'NOOP')

    def test_exact_padding_and_special_branch_precedence(self):
        for raw, short, build, legacy, relation in [('3.35.0', '3.35', '0', '3.35.0', 'PAD'),
                    ('3.35', '3.35', '7', '3.35', 'EXACT'),
                    ('3.35.7', '3.35', '7', '3.35', 'BRANCH_EXACT')]:
            i = original.request(raw, short, '3.34')
            d = policy.reconcile(replace(i, legacy_version=legacy,
                                        observation=replace(i.observation, bundle_version=build)))
            self.assertEqual(d.relation, relation)

    def test_wrong_identity_digest_or_inspector_cannot_use_build_proof(self):
        i = original.request('3.35.743', '3.35', '3.32')
        obs = replace(i.observation, bundle_version='743')
        for bad in [replace(obs, bundle_id='org.example.other'), replace(obs, artifact_sha256='c' * 64),
                    replace(obs, inspector='other')]:
            self.assertEqual(policy.reconcile(replace(i, observation=bad)).reason, 'OBSERVATION_INCONSISTENT')

    def test_generated_relations_bind_raw_build_and_exact_published_text(self):
        for core in ['2.7', '10.20.30', '7.0.9']:
            for build in ['0', '1', '234']:
                full = core + '.' + build
                for raw, observed in [(full, full), (full, build), (full + ',' + core, build)]:
                    with self.subTest(raw=raw, build=observed):
                        d = self.reconcile_case(raw, core, observed, '1.0')
                        self.assertEqual((d.action, d.version), ('WRITE', core))
                        for field in [0, 2]:
                            original_fields = [raw, core, observed]
                            text = original_fields[field]
                            for index in range(len(text)):
                                for mutation in [text[:index] + text[index+1:],
                                                 text[:index] + '9' + text[index:],
                                                 text[:index] + ('8' if text[index] == '9' else '9') + text[index+1:]]:
                                    changed = original_fields.copy()
                                    changed[field] = mutation
                                    self.assertIsNone(policy.build_relationship(*changed))


class BuildCollectorIntegrationTests(unittest.TestCase):
    run_case = integration.CollectorIntegrationTests.run_case

    def test_recorded_source_build_cases_publish_or_hold_before_writing(self):
        for row in ROWS:
            with self.subTest(case=row['case']):
                obs = integration.c.BundleObservation(integration.SHA, integration.BUNDLE, row['short'], row['build'])
                old, new, report = self.run_case(obs, raw=row['source'], prior=row['prior'])
                if row['relation']:
                    self.assertEqual((json.loads(new)['version'], json.loads(new)['sha']),
                                     (row['short'], integration.SHA))
                    self.assertEqual(report['versionEvidence'][0]['relation'], row['relation'])
                    self.assertEqual(report['failures'], [])
                else:
                    self.assertEqual(old, new)
                    self.assertEqual(report['failures'][0]['reason'], 'RELATION_UNPROVEN')

    def test_no_check_build_mismatch_preserves_prior_bytes(self):
        obs = integration.c.BundleObservation(integration.SHA, integration.BUNDLE, '3.35', '744')
        old, new, report = self.run_case(obs, raw='3.35.743', prior='3.32')
        self.assertEqual(old, new)
        self.assertEqual(report['failures'][0]['reason'], 'RELATION_UNPROVEN')


if __name__ == '__main__':
    unittest.main()
