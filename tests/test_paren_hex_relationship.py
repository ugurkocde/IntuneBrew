"""Public strings; fake identities, hashes and disposable collector IO only."""
from dataclasses import replace
from pathlib import Path
import json
import unittest
import test_version_relation as original
import test_dmg_reconciliation as integration
p=original.policy
RELATION='SOURCE_PAREN_HEX_BUILD'
ROWS=json.loads((Path(__file__).parent/'fixtures/paren_hex_versions.json').read_text())
def request(raw='5.8.2',short='5.8.2(095C)',build='5.8.2',prior='5.8.1',caps=None):
    i=original.request(raw,short,prior,caps=p.CATALOG_CONSUMER_CAPABILITIES if caps is None else caps)
    return replace(i,observation=replace(i.observation,bundle_version=build))
class ParenHexTests(unittest.TestCase):
    def test_exact_binding_bounded_grammar_and_refusals(self):
        for raw,short in [('5.8.2','5.8.2(095C)'),('2.5.1','2.5.1(2F17)'),('0.1','0.1(ABCD)'),('999999999.1','999999999.1(F000)')]:
            self.assertEqual(p.paren_hex_build_relationship(raw,short,raw),RELATION)
        bad=[('5.8.2',v,'5.8.2')for v in ['5.8.2(0951)','5.8.2(095c)','5.8.2(ABC)','5.8.2(ABCDE)','5.8.2 (ABCD)','5.8.2(ABCD) ','5.8.2((ABCD))','5.8.2(ABCD)(ABCD)','5.8.2(ＡBCD)','5.8.3(ABCD)','5.8.2-beta(ABCD)','5.8.2(ABCD)\n']]
        bad += [('5.8.2','5.8.2(ABCD)',v)for v in ['5.8.2.0','ABCD','5.8.2(ABCD)',None,12,'','5.8.2 ']]
        bad += [(v,v+'(ABCD)',v)for v in ['5','05.8.2','5.08.2','1000000000.8','5.8,2','5.8-2','5.8b1','x'*257]]
        bad += [('4.5','4.5.1(ABCD)','4.5'),('5.8.2','x'*65,'5.8.2'),('5.8.2','5.8.2(ABCD)','x'*65)]
        class Text(str):pass
        bad += [(Text('5.8.2'),'5.8.2(ABCD)','5.8.2'),('5.8.2',Text('5.8.2(ABCD)'),'5.8.2'),('5.8.2','5.8.2(ABCD)',Text('5.8.2'))]
        for raw,short,build in bad:
            with self.subTest(raw=raw,short=short,build=build):
                self.assertIsNone(p.paren_hex_build_relationship(raw,short,build))
                self.assertEqual(p.reconcile(request(raw,short,build)).reason,'RELATION_UNPROVEN')
    def test_relation_local_ordering_and_equal_core_holds(self):
        for prior,action,reason in [('5.8.1(ABCD)','WRITE','PROVEN_DETECTION_TEXT'),('5.8.1+7','WRITE','PROVEN_DETECTION_TEXT'),('5.8.1 (build 7)','WRITE','PROVEN_DETECTION_TEXT'),('5.8.2(ABCD)','HOLD','EQUAL_ORDER_TEXT_DIFFERS'),('5.8.2','HOLD','EQUAL_ORDER_TEXT_DIFFERS'),('5.8.3(ABCD)','HOLD','DETECTION_REGRESSION'),('5.8.1-1','HOLD','PRIOR_ORDER_UNKNOWN'),('5.8.1(abcd)','HOLD','PRIOR_ORDER_UNKNOWN'),('5.8.1(0951)','HOLD','PRIOR_ORDER_UNKNOWN'),(None,'WRITE','PROVEN_DETECTION_TEXT')]:
            with self.subTest(prior=prior):
                d=p.reconcile(request(prior=prior));self.assertEqual((d.action,d.reason),(action,reason))
        self.assertEqual(p.reconcile(request('5.8.10','5.8.10(ABCD)','5.8.10','5.8.9(ABCD)')).action,'WRITE')
        self.assertIsNone(p.parse_detection('5.8.2(095C)'))
        self.assertEqual(p.reconcile(original.request('2.152.0,stable.4,12','2.152.0-stable.4','2.151.0(ABCD)')).reason,'PRIOR_ORDER_UNKNOWN')
    def test_same_text_refresh_noop_and_no_check(self):
        i=request(prior='5.8.2(095C)');self.assertEqual(p.reconcile(i).action,'REFRESH');i=replace(i,prior=replace(i.prior,sha=original.SHA,url=i.url));self.assertEqual(p.reconcile(i).action,'NOOP');self.assertEqual(p.plan(i).action,'NOOP');self.assertEqual(p.plan(replace(i,declared_sha256=None)).action,'INSPECT')
    def test_capability_and_integrity_guards(self):
        i=request(caps=frozenset({'decorated_text','plus_build'}));d=p.reconcile(i);self.assertEqual((d.action,d.relation,d.reason),('HOLD',RELATION,'CONSUMER_CAPABILITY_PENDING'))
        for obs in [replace(i.observation,bundle_id='org.example.other'),replace(i.observation,artifact_sha256='c'*64),replace(i.observation,inspector='other/1')]:
            self.assertEqual(p.reconcile(replace(i,observation=obs)).reason,'OBSERVATION_INCONSISTENT')
    def test_current_twenty_row_matrix_capability_on_and_off(self):
        self.assertEqual(len(ROWS),20);self.assertEqual(len({r['case']for r in ROWS}),20)
        for enabled in [True,False]:
            counts={}
            for row in ROWS:
                i=request(row['source'],row['short'],row['build'],row['prior'],p.CATALOG_CONSUMER_CAPABILITIES if enabled else frozenset({'decorated_text','plus_build'}));i=replace(i,source_cask=row['case'])
                if row.get('already_published'):i=replace(i,prior=replace(i.prior,sha=original.SHA,url=i.url))
                d=p.reconcile(i);counts[d.action]=counts.get(d.action,0)+1
                if row['case']in {'steermouse','cursorsense'}:self.assertEqual((d.action,d.relation,d.reason),('WRITE',RELATION,'PROVEN_DETECTION_TEXT')if enabled else('HOLD',RELATION,'CONSUMER_CAPABILITY_PENDING'))
                elif row.get('already_published'):self.assertEqual(d.action,'NOOP')
                else:self.assertEqual((d.action,d.reason),('HOLD',row['prior_reason']))
            self.assertEqual(counts,{'WRITE':2,'HOLD':17,'NOOP':1}if enabled else{'HOLD':19,'NOOP':1})
    def test_collector_writes_two_and_preserves_remaining_bytes(self):
        for row in ROWS:
            if row.get('already_published'):continue
            with self.subTest(case=row['case']):
                obs=integration.c.BundleObservation(integration.SHA,integration.BUNDLE,row['short'],row['build']);old,new,report=integration.CollectorIntegrationTests.run_case(self,obs,raw=row['source'],prior=row['prior'])
                if row['case']in {'steermouse','cursorsense'}:
                    self.assertEqual((json.loads(new)['version'],json.loads(new)['sha']),(row['short'],integration.SHA));self.assertEqual(report['versionEvidence'][0]['relation'],RELATION);self.assertEqual(report['failures'],[])
                else:self.assertEqual(new,old);self.assertEqual(report['failures'][0]['reason'],row['prior_reason'])
if __name__=='__main__':unittest.main()
