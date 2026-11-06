"""Stable-cask channel policy with synthetic identities, digests and artifact IO."""
from dataclasses import replace
import json
from pathlib import Path
import unittest

import test_dmg_reconciliation as integration
import test_version_relation as original

policy = original.policy
SHA = original.SHA
ROWS = json.loads((Path(__file__).parent / 'fixtures/hyphen_build_versions.json').read_text())


def request(raw='27.1.0-58756', short='27.1.0', build='58756', prior='27.0.3-58680', cask='fixture'):
    i = original.request(raw, short, prior)
    return replace(i, source_cask=cask, observation=replace(i.observation, bundle_version=build))


class HyphenBuildTests(unittest.TestCase):
    def test_twenty_measured_rows_write_two_and_hold_eighteen(self):
        writes = []
        for row in ROWS:
            with self.subTest(case=row['case']):
                d = policy.reconcile(request(row['source'], row['short'], row['build'], row['prior'], row['case']))
                if row['relation']:
                    self.assertEqual((d.action, d.version, d.sha, d.relation, d.verified),
                                     ('WRITE', row['short'], SHA, row['relation'], True))
                    writes.append(row['case'])
                else:
                    self.assertEqual((d.action, d.reason), ('HOLD', 'RELATION_UNPROVEN'))
        self.assertEqual(set(writes), {'parallels', '8x8-work'})

    def test_complete_binding_and_canonical_bounded_grammar(self):
        bad = [('1.2.3-' + n, '1.2.3', n) for n in ['0', '01', 'beta', '1' * 19]]
        bad += [('01.2.3-4', '01.2.3', '4'), ('1.2-4', '1.2', '4'),
                ('1.2.3.4-5', '1.2.3.4', '5'), ('1000000000.2.3-4', '1000000000.2.3', '4'),
                ('1.2.3-4,1.2.3', '1.2.3', '4'), ('1.2.3-4 ', '1.2.3', '4'),
                ('1.2.3-٤', '1.2.3', '٤'), ('1.2.3-4', '1.2.4', '4')]
        bad += [('1.2.3-4', '1.2.3', build) for build in ['1.2.3.5', '4.0', ' 4', '4 ',
                '4\n', None, 4, '', '4' * 65]]
        class Text(str):
            pass
        bad += [(Text('1.2.3-4'), '1.2.3', '4'), ('1.2.3-4', Text('1.2.3'), '4'),
                ('1.2.3-4', '1.2.3', Text('4')), ('x' * 257, '1.2.3', '4'),
                ('1.2.3-4', '1.' + '2' * 63, '4')]
        for raw, short, build in bad:
            with self.subTest(raw=raw, short=short, build=build):
                self.assertIsNone(policy.hyphen_build_relationship(raw, short, build, 'fixture'))
        for short, build in [('0.0.0', '1'), ('999999999.999999999.999999999', '9' * 18)]:
            for observed in [build, short + '.' + build]:
                self.assertEqual(policy.hyphen_build_relationship(short + '-' + build, short,
                                 observed, 'fixture'), 'SOURCE_HYPHEN_BUILD')

    def test_known_prerelease_or_versioned_casks_do_not_gain_stable_authority(self):
        for cask in [None, 1, '', 'fixture@27', 'fixture@beta', 'fixture-beta', 'beta-fixture',
                     'fixture-developer-edition', 'fixture-preview', 'fixture-dev', 'fixture-nightly',
                     'fixture-canary', 'fixture-rc', 'fixture-unstable', 'fixture-insiders',
                     'fixture-alpha', 'fixture-prerelease', 'fixture-testing', 'Fixture',
                     'fixture/other', 'fixture--other', 'a' * 129]:
            with self.subTest(cask=cask):
                self.assertEqual(policy.reconcile(request(cask=cask)).reason, 'RELATION_UNPROVEN')

    def test_numeric_prerelease_residual_is_explicitly_accepted(self):
        # Stable cask authority is a policy choice, not proof from bundle fields.
        # This could be a prerelease; its final version later REFRESHes, not WRITE.
        for build in ['1', '1.2.3.1']:
            d = policy.reconcile(request('1.2.3-1', '1.2.3', build, '1.1.0'))
            self.assertEqual((d.action, d.version), ('WRITE', '1.2.3'))
        final = policy.reconcile(request('1.2.3', '1.2.3', '2', '1.2.3'))
        self.assertEqual((final.action, final.reason), ('REFRESH', 'EXACT_TEXT_UNCHANGED'))

    def test_prior_migration_requires_strict_core_advance(self):
        for prior, action, reason in [
                ('27.0.3-58680', 'WRITE', 'PROVEN_DETECTION_TEXT'),
                ('27.0.3-0', 'WRITE', 'PROVEN_DETECTION_TEXT'),
                ('27.0.3-' + '9' * 18, 'WRITE', 'PROVEN_DETECTION_TEXT'),
                ('27.1.0-58756', 'HOLD', 'EQUAL_ORDER_TEXT_DIFFERS'),
                ('27.1.0-1', 'HOLD', 'EQUAL_ORDER_TEXT_DIFFERS'),
                ('27.1.1-1', 'HOLD', 'DETECTION_REGRESSION'),
                ('27.0.3-beta', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                ('27.0.03-1', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                ('27.0-1', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                ('9007199254740993.0.0-1', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                ('1000000000.0.0-1', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                ('27.0.3-01', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                ('27.0.3-' + '1' * 19, 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                ('27.0.3-1,x', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                ('opaque', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                ('27.0.3', 'WRITE', 'PROVEN_DETECTION_TEXT'),
                ('27.1.1', 'HOLD', 'DETECTION_REGRESSION')]:
            with self.subTest(prior=prior):
                d = policy.reconcile(request(prior=prior))
                self.assertEqual((d.action, d.reason), (action, reason))

    def test_migration_does_not_change_other_relations_or_global_parser(self):
        self.assertIsNone(policy.parse_detection('27.0.3-58680'))
        cases = [('1.2.0', '1.2', '0', 'PAD'),
                 ('1.2.3', '1.2', '3', 'SOURCE_SHORT_DOT_BUILD'),
                 ('1.2,3', '1.2+3', '3', 'RENDER_PLUS')]
        for raw, short, build, relation in cases:
            d = policy.reconcile(request(raw, short, build, '1.1.0-7'))
            self.assertEqual((d.relation, d.action, d.reason), (relation, 'HOLD', 'PRIOR_ORDER_UNKNOWN'))
        exact = policy.reconcile(request('1.2.3', '1.2.3', '4', 'opaque'))
        self.assertEqual((exact.relation, exact.action), ('EXACT', 'WRITE'))

    def test_wrong_bundle_digest_inspector_and_integrity_are_still_held(self):
        i = request()
        for bad in [replace(i.observation, bundle_id='org.example.other'),
                    replace(i.observation, artifact_sha256='c' * 64),
                    replace(i.observation, inspector='other')]:
            self.assertEqual(policy.reconcile(replace(i, observation=bad)).reason,
                             'OBSERVATION_INCONSISTENT')
        d = policy.reconcile(replace(i, observation=policy.InspectionRefusal('CHECKSUM_MISMATCH', True)))
        self.assertEqual((d.action, d.reason), ('HOLD', 'CHECKSUM_MISMATCH'))

    def test_same_short_build_change_refreshes_or_noops_without_an_update(self):
        i = request(raw='27.1.0-58800', build='58800', prior='27.1.0')
        self.assertEqual(policy.reconcile(i).action, 'REFRESH')
        same = replace(i, prior=policy.PriorEntry('27.1.0', SHA, i.url))
        self.assertEqual(policy.reconcile(same).action, 'NOOP')
        self.assertEqual((policy.plan(same).action, policy.plan(same).version), ('NOOP', '27.1.0'))

    def test_single_character_raw_and_build_mutations_break_exact_binding(self):
        for core in ['1.2.3', '0.8.9', '999.0.8']:
            for n in ['1', '17', '123456789012345678']:
                raw = core + '-' + n
                for build in [n, core + '.' + n]:
                    for field in [0, 2]:
                        fields = [raw, core, build]
                        text = fields[field]
                        for index in range(len(text)):
                            for mutated in [text[:index] + text[index+1:],
                                    text[:index] + '9' + text[index:],
                                    text[:index] + ('8' if text[index]=='9' else '9') + text[index+1:]]:
                                changed = fields.copy(); changed[field] = mutated
                                self.assertIsNone(policy.hyphen_build_relationship(*changed, 'fixture'))


class HyphenBuildCollectorTests(unittest.TestCase):
    run_case = integration.CollectorIntegrationTests.run_case

    def test_all_twenty_current_rows_preserve_holds_and_publish_exact_proven_text(self):
        for row in ROWS:
            with self.subTest(case=row['case']):
                obs = integration.c.BundleObservation(integration.SHA, integration.BUNDLE,
                                                       row['short'], row['build'])
                old, new, report = self.run_case(obs, raw=row['source'], prior=row['prior'])
                if row['relation']:
                    self.assertEqual((json.loads(new)['version'], json.loads(new)['sha']),
                                     (row['short'], integration.SHA))
                    self.assertEqual(report['versionEvidence'][0]['relation'], row['relation'])
                    self.assertEqual(report['failures'], [])
                else:
                    self.assertEqual(new, old)
                    self.assertEqual(report['failures'][0]['reason'], 'RELATION_UNPROVEN')

    def test_ambiguous_or_unordered_release_preserves_prior_bytes(self):
        obs = integration.c.BundleObservation(integration.SHA, integration.BUNDLE, '27.1.0', '58756')
        for prior, reason in [('27.1.0-1', 'EQUAL_ORDER_TEXT_DIFFERS'),
                              ('27.1.1-1', 'DETECTION_REGRESSION'),
                              ('27.0.3-beta', 'PRIOR_ORDER_UNKNOWN')]:
            old, new, report = self.run_case(obs, raw='27.1.0-58756', prior=prior)
            self.assertEqual(new, old)
            self.assertEqual(report['failures'][0]['reason'], reason)


if __name__ == '__main__':
    unittest.main()
