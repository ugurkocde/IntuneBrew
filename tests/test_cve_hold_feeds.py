"""Test the workflow's exact inline compact producer and full-corpus pairing gate."""
import ast
import hashlib
import json
import os
from pathlib import Path
import pathlib
import re
import tempfile
import unittest
from test_cve_collection import collector_source


def producer(directory):
    names = {'hold_feed_bytes', 'save_hold_feed', 'verify_hold_feed_pairs'}
    nodes = [node for node in ast.parse(collector_source()).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(nodes) == len(names)
    namespace = dict(json=json, hashlib=hashlib, re=re, os=os, tempfile=tempfile,
                     pathlib=pathlib, CVE_DIR=directory)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual-inline-producer>', 'exec'), namespace)
    return namespace


class HoldFeedTests(unittest.TestCase):
    def test_entire_committed_corpus_is_paired(self):
        producer(Path(__file__).resolve().parents[1] / 'CVE')['verify_hold_feed_pairs']()

    def test_preserves_records_types_presence_and_exact_bytes_digest(self):
        namespace = producer(Path('unused'))
        payload = b'{"vulnerabilities":[null,1,"x",[],{"cve_id":"fixture","is_kev":null,"severity":false,"unused":"description"}]}'
        compact = json.loads(namespace['hold_feed_bytes'](payload, 'fixture'))
        self.assertEqual(compact['source_sha256'], hashlib.sha256(payload).hexdigest())
        self.assertEqual(compact['vulnerabilities'], [None, 1, 'x', [], {'cve_id':'fixture','is_kev':None,'severity':False}])
        self.assertEqual(set(compact), {'schema_version','app_key','source_sha256','vulnerabilities'})
        self.assertEqual(namespace['hold_feed_bytes'](payload, 'fixture'), namespace['hold_feed_bytes'](payload, 'fixture'))

    def test_every_evaluator_field_is_retained_without_coercion(self):
        record = dict(cve_id='CVE-2099-0001', severity='HIGH', is_kev=True,
                      affected_version_start='1.0', affected_version_start_type='including',
                      affected_version_end='3.0', affected_version_end_type='excluding', fixed_version=None)
        payload = json.dumps({'vulnerabilities':[record]}).encode()
        result = json.loads(producer(Path('unused'))['hold_feed_bytes'](payload, 'fixture'))
        self.assertEqual(result['vulnerabilities'], [record])

    def test_ambiguous_keys_and_nonfinite_values_rejected_at_all_depths(self):
        build = producer(Path('unused'))['hold_feed_bytes']
        for fragment in ['{"A":1,"a":2}', '{"a":1,"a":2}', '{"":1}', '{"SEVERITY":"HIGH"}',
                         '{"is_\\u212aev":true}', '{"PSObject":{}}', '{"n":NaN}']:
            for payload in [fragment, '{"vulnerabilities":[],"metadata":[' + fragment + ']}', '{"vulnerabilities":[' + fragment + ']}']:
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    build(payload.encode(), 'fixture')

    def test_missing_or_stale_pair_and_orphan_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); directory = root / 'CVE'; directory.mkdir()
            full = directory / 'fixture.json'; full.write_text('{"vulnerabilities":[]}')
            namespace = producer(directory)
            with self.assertRaises(ValueError): namespace['verify_hold_feed_pairs']()
            namespace['save_hold_feed']('fixture'); namespace['verify_hold_feed_pairs']()
            full.write_text('{"vulnerabilities":[]}\n')
            with self.assertRaises(ValueError): namespace['verify_hold_feed_pairs']()
            namespace['save_hold_feed']('fixture'); namespace['verify_hold_feed_pairs']()
            (root / 'CVE-Holds/orphan.json').write_text('{}')
            with self.assertRaises(ValueError): namespace['verify_hold_feed_pairs']()

    def test_workflow_checks_pairs_before_staging_and_after_every_rebase(self):
        workflow = Path(__file__).resolve().parents[1] / '.github/workflows/check-app-cves.yml'
        text = workflow.read_text(); step = text.split('- name: Commit and push CVE files',1)[1].split('- name: Sync CVE',1)[0]
        self.assertIn('git status --porcelain -- CVE/ CVE-Holds/', step)
        self.assertIn('git add CVE/ CVE-Holds/', step)
        self.assertLess(step.index('python check_cves.py --verify-hold-pairs'), step.index('git add'))
        self.assertIn('git pull --rebase origin main\n              python check_cves.py --verify-hold-pairs', step)
        self.assertNotIn('always()', step)
