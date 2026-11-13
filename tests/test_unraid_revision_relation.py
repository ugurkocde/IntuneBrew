"""Synthetic Unraid relationship fixtures; no tenant or publication authority."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.github/scripts'))
import version_relation as p
import collect_app_info as collector
SHA='a'*64
CAPS=p.CATALOG_CONSUMER_CAPABILITIES

def request(core='2.0.11.1', revision='1', prior=None, caps=CAPS):
    version=f'v{core}-unraid.{revision}'
    url=f'https://github.com/unraid/usb-creator-next/releases/download/{version}/Unraid.USB.Creator-{version}.dmg'
    return p.ReconcileInput(f'{core},{revision}',core,SHA,url,'org.example.unraid',
        p.PriorEntry(prior,'b'*64,'https://example.invalid/prior.dmg') if prior else None,
        p.BundleObservation(SHA,'org.example.unraid',version,version),caps,'unraid-usb-creator')

class UnraidRevisionTests(unittest.TestCase):
    def test_production_capabilities_are_exactly_the_reviewed_consumers(self):
        self.assertEqual(CAPS, frozenset({'decorated_text','plus_build','paren_hex','unraid_revision'}))
        self.assertIs(collector.CATALOG_CONSUMER_CAPABILITIES, CAPS)

    def test_collector_uses_unpatched_production_capability_and_preserves_holds(self):
        value=request()
        def collect(raw_sha=SHA, prior=None, observation=value.observation):
            app={'name':'Example Unraid','version':'2.0.11.1','url':value.url,
                 'bundleId':'org.example.unraid','fileName':'example.dmg'}
            with mock.patch.object(collector.shutil,'which',return_value='/usr/bin/hdiutil'), \
                 mock.patch.object(collector,'inspect_dmg_artifact',return_value=observation) as inspect, \
                 mock.patch.object(collector,'read_vendor_sha256',side_effect=AssertionError('No sidecar fallback')):
                collector.reconcile_vendor_dmg(app, prior,
                    {'version':'2.0.11.1,1','sha256':raw_sha}, 'unraid-usb-creator')
            inspect.assert_called_once()
            return app
        app=collect()
        self.assertEqual((app['version'],app['sha']),('v2.0.11.1-unraid.1',SHA))
        for kwargs in [
            {'raw_sha':'b'*64},
            {'prior':{'version':'2.0.11.1','sha':SHA,'url':value.url}},
            {'observation':p.InspectionRefusal('MOUNT_FAILED',False,SHA)},
        ]:
            with self.subTest(kwargs=kwargs), self.assertRaises(collector.CatalogVersionHold):
                collect(**kwargs)

    def test_exact_vendor_contract_keeps_literal_detection_and_digest(self):
        i=request();d=p.reconcile(i)
        self.assertEqual((d.action,d.version,d.sha,d.relation),('WRITE','v2.0.11.1-unraid.1',SHA,'SOURCE_UNRAID_REVISION'))
        self.assertTrue(d.verified)
    def test_missing_capability_holds(self):
        d=p.reconcile(request(caps=p.CATALOG_CONSUMER_CAPABILITIES - {'unraid_revision'}))
        self.assertEqual((d.action,d.reason,d.relation),('HOLD','CONSUMER_CAPABILITY_PENDING','SOURCE_UNRAID_REVISION'))
    def test_plan_never_bypasses_contract_or_capability_with_prior(self):
        i=request();prior=p.PriorEntry(i.observation.short_version,SHA,i.url)
        self.assertEqual(p.plan(replace(i,prior=prior)).action,'INSPECT')
        self.assertEqual(p.plan(replace(i,prior=p.PriorEntry(i.legacy_version,SHA,i.url))).action,'INSPECT')
    def test_malformed_source_forms_do_not_escape_through_exact_lane(self):
        for raw in ['2.0.11.1','02.0.11.1,1','2.00.11.1,1','2.0.11,1','2.0.11.1.0,1',
                    '2.0.11.1,01','2.0.11.1,1000000000','1000000000.0.11.1,1','2.0.11.1,١','2.0.11.1,1\n']:
            with self.subTest(raw=raw):
                i=request();i=replace(i,source_release=raw,legacy_version=p.generic_legacy_truncate(raw))
                self.assertEqual((p.reconcile(i).action,p.reconcile(i).reason),('HOLD','RELATION_UNPROVEN'))
        i=request();i=replace(i,observation=replace(i.observation,short_version=i.legacy_version,bundle_version=i.legacy_version))
        self.assertEqual(p.reconcile(i).reason,'RELATION_UNPROVEN')
    def test_url_drift_holds(self):
        i=request()
        for url in [i.url+'?download=1',i.url+'#fragment',i.url.replace('https:','http:'),i.url.replace('github.com','example.invalid'),i.url.replace('v2.0.11.1-unraid.1/','v2.0.11.1-unraid.2/'),i.url.replace('.dmg','.pkg')]:
            with self.subTest(url=url):self.assertEqual(p.reconcile(replace(i,url=url)).reason,'RELATION_UNPROVEN')
    def test_declared_hash_and_observed_build_are_required(self):
        i=request()
        for declared in [None,'no_check','b'*64]:
            with self.subTest(declared=declared):self.assertEqual(p.reconcile(replace(i,declared_sha256=declared)).action,'HOLD')
        for short,build in [('v2.0.11.1-unraid.1','2.0.11.1'),('v2.0.11.1-unraid.1',None),('V2.0.11.1-unraid.1','V2.0.11.1-unraid.1'),('v2.0.11.1-Unraid.1','v2.0.11.1-Unraid.1')]:
            with self.subTest(short=short,build=build):self.assertEqual(p.reconcile(replace(i,observation=replace(i.observation,short_version=short,bundle_version=build))).action,'HOLD')
    def test_other_cask_keeps_generic_mismatch_hold(self):
        d=p.reconcile(replace(request(),source_cask='future-release'))
        self.assertEqual((d.action,d.reason),('HOLD','RELATION_UNPROVEN'))
    def test_unreadable_unraid_never_uses_legacy_pass(self):
        for code in ['DOWNLOAD_FAILED','MOUNT_FAILED','NOT_FOUND','CLEANUP_INCOMPLETE']:
            with self.subTest(code=code):
                d=p.reconcile(replace(request(),observation=p.InspectionRefusal(code,False,SHA)))
                self.assertEqual((d.action,d.reason),('HOLD',code))
    def test_numeric_release_and_revision_advance(self):
        for i in [request('10.0.0.0','1','v2.0.11.1-unraid.100'),request(revision='10',prior='v2.0.11.1-unraid.2'),request('2.0.12.0','1','v2.0.11.1-unraid.999999999')]:
            with self.subTest(i=i):self.assertEqual(p.reconcile(i).action,'WRITE')
    def test_numeric_downgrades_and_unknown_prior_hold(self):
        for prior in ['v10.0.0.0-unraid.1','v2.0.11.1-unraid.10']:
            self.assertEqual(p.reconcile(request(prior=prior)).reason,'DETECTION_REGRESSION')
        for prior in ['2.0.11.1','v02.0.11.1-unraid.1','opaque']:
            self.assertEqual(p.reconcile(request(prior=prior)).reason,'PRIOR_ORDER_UNKNOWN')
    def test_identical_text_noop_or_refresh_and_zero_bounds(self):
        i=request(prior='v2.0.11.1-unraid.1')
        self.assertEqual(p.reconcile(i).action,'REFRESH')
        self.assertEqual(p.reconcile(replace(i,prior=p.PriorEntry(i.prior.version,SHA,i.url))).action,'NOOP')
        self.assertEqual(p.reconcile(request('0.0.0.0','0')).action,'WRITE')
        self.assertEqual(p.reconcile(request('999999999.0.0.0','999999999')).action,'WRITE')

if __name__=='__main__':unittest.main()
