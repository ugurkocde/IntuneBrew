"""Manifest authorization and stale-row preservation with a fake database only."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / '.github/scripts/sync_cves_to_supabase.py'


class FakeDatabase:
    def __init__(self, keys):
        self.summaries = {key:{'old':key} for key in keys}
        self.entries = {key:[{'old':key}] for key in keys}
        self.operations = []
        self.failure = None

    def table(self, name):
        database = self
        class Operation:
            def upsert(self, value, **kwargs):
                self.action, self.value, self.key = 'upsert', value, value['app_key']; return self
            def delete(self):
                self.action = 'delete'; return self
            def eq(self, column, key):
                assert column == 'app_key'; self.key = key; return self
            def insert(self, rows):
                self.action, self.value = 'insert', rows
                self.key = rows[0]['app_key']; return self
            def execute(self):
                database.operations.append((name,self.action,self.key))
                if database.failure == self.action:raise RuntimeError('fake database failure')
                if self.action == 'upsert':database.summaries[self.key] = copy.deepcopy(self.value)
                elif self.action == 'delete':database.entries[self.key] = []
                else:database.entries[self.key].extend(copy.deepcopy(self.value))
        return Operation()


class ManifestSyncTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); self.cves = self.root/'CVE'; self.cves.mkdir()
        self.apps = self.root/'Apps'; self.apps.mkdir(); self.manifest_path = self.root/'manifest.json'
        self.keys = [f'good_{i}' for i in range(9)]+['stale']
        self.db = FakeDatabase(self.keys)
        spec = importlib.util.spec_from_file_location('manifest_sync_fixture',SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        fake = types.SimpleNamespace(create_client=mock.Mock(return_value=self.db),Client=object)
        with mock.patch.dict(sys.modules,{'supabase':fake}):spec.loader.exec_module(self.module)
        self.client = self.module.create_client
        self.environment = mock.patch.dict(os.environ,{'SUPABASE_URL':'https://fake.invalid','SUPABASE_SERVICE_ROLE_KEY':'FAKE_TEST_KEY','GITHUB_RUN_ID':'123','GITHUB_RUN_ATTEMPT':'1'})
        self.environment.start(); self.addCleanup(self.environment.stop)
        self.manifest = {'schema':1,'run_id':123,'run_attempt':1,'selected_count':10,
                         'selected_apps':self.keys,'failure_limit_percent':10,'kev_entries':1,
                         'validated':[],'stale':[{'app_key':'stale','reason':'NVD pagination changed'}]}
        for key in self.keys:
            self.write_app(key, [] if key in ['good_0','stale'] else [{'cve_id':'CVE-2099-0001','severity':'HIGH'}])
            if key!='stale':self.authorize(key)
        self.save_manifest()

    def write_app(self,key,cves):
        path=self.cves/(key+'.json')
        path.write_text(json.dumps({'app_key':key,'app_name':key,'total_cves':len(cves),'vulnerabilities':cves,'last_updated':'2099-01-01'}))
        return path

    def authorize(self,key):
        path=self.cves/(key+'.json');data=json.loads(path.read_bytes())
        self.manifest['validated'].append({'app_key':key,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'total_cves':data['total_cves']})

    def save_manifest(self):self.manifest_path.write_text(json.dumps(self.manifest))

    def main(self,include_manifest=True):
        args=['sync','--cve-dir',str(self.cves),'--apps-dir',str(self.apps)]
        if include_manifest:args+=['--manifest',str(self.manifest_path)]
        output=io.StringIO()
        with mock.patch.object(sys,'argv',args),contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
            self.module.main()
        return output.getvalue()

    def rejected_before_client(self):
        with self.assertRaises(SystemExit) as result:self.main()
        self.assertNotEqual(result.exception.code,0);self.client.assert_not_called();self.assertEqual(self.db.operations,[])

    def test_only_manifest_apps_written_stale_rows_untouched(self):
        before=(copy.deepcopy(self.db.summaries['stale']),copy.deepcopy(self.db.entries['stale']))
        output=self.main()
        self.assertEqual(before,(self.db.summaries['stale'],self.db.entries['stale']))
        self.assertEqual({key for table,action,key in self.db.operations},set(self.keys)-{'stale'})
        self.assertNotIn('SYNC_APP stale',output)
        self.assertEqual({line.split(' ',1)[1] for line in output.splitlines() if line.startswith('SYNC_APP ')},set(self.keys)-{'stale'})
        self.assertIn('Apps synced: 9',output)

    def test_validated_empty_app_clears_old_entries(self):
        self.main()
        self.assertEqual(self.db.summaries['good_0']['total_cves'],0)
        self.assertEqual(self.db.entries['good_0'],[])
        self.assertNotIn(('cve_entries','insert','good_0'),self.db.operations)

    def test_unlisted_corrupt_files_ignored(self):
        (self.cves/'unlisted.json').write_text('bad JSON')
        self.main();self.assertFalse(any(key=='unlisted' for table,action,key in self.db.operations))

    def test_missing_required_manifest_argument(self):
        with self.assertRaises(SystemExit):self.main(False)
        self.client.assert_not_called()

    def test_missing_manifest(self):self.manifest_path.unlink();self.rejected_before_client()
    def test_malformed_manifest(self):self.manifest_path.write_text('{');self.rejected_before_client()
    def test_duplicate_json_key(self):self.manifest_path.write_text('{"schema":1,"schema":1}');self.rejected_before_client()
    def test_nonfinite_json_number(self):self.manifest_path.write_text('{"schema":NaN}');self.rejected_before_client()
    def test_empty_validated(self):self.manifest['validated']=[];self.save_manifest();self.rejected_before_client()
    def test_duplicate_validated_key(self):self.manifest['validated'].append(self.manifest['validated'][0]);self.save_manifest();self.rejected_before_client()
    def test_overlapping_stale_key(self):self.manifest['stale'][0]['app_key']='good_0';self.save_manifest();self.rejected_before_client()
    def test_path_traversal_key(self):self.manifest['validated'][0]['app_key']='../escape';self.save_manifest();self.rejected_before_client()
    def test_wrong_attempt(self):self.manifest['run_attempt']=2;self.save_manifest();self.rejected_before_client()
    def test_incomplete_selection(self):self.manifest['selected_count']=11;self.save_manifest();self.rejected_before_client()
    def test_more_than_ten_percent_stale(self):self.manifest['validated'].pop();self.manifest['stale'].append({'app_key':'good_8','reason':'failure'});self.save_manifest();self.rejected_before_client()
    def test_hash_mismatch(self):(self.cves/'good_0.json').write_text('{}');self.rejected_before_client()
    def test_missing_validated_file(self):(self.cves/'good_0.json').unlink();self.rejected_before_client()
    def test_symlink_validated_file(self):
        path=self.cves/'good_0.json';target=self.root/'target.json';path.rename(target);path.symlink_to(target);self.rejected_before_client()
    def test_file_app_key_mismatch_even_with_correct_hash(self):
        path=self.cves/'good_0.json';data=json.loads(path.read_text());data['app_key']='stale';path.write_text(json.dumps(data));self.manifest['validated'][0]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();self.save_manifest();self.rejected_before_client()
    def test_count_mismatch_even_with_correct_hash(self):
        path=self.cves/'good_0.json';data=json.loads(path.read_text());data['total_cves']=1;path.write_text(json.dumps(data));self.manifest['validated'][0]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();self.save_manifest();self.rejected_before_client()
    def test_database_errors_are_failure(self):
        for failure in ['upsert','delete','insert']:
            with self.subTest(failure=failure):
                self.db.failure=failure
                with self.assertRaises(SystemExit) as result:self.main()
                self.assertEqual(result.exception.code,1)
    def test_synced_count_must_equal_validated_count(self):
        with mock.patch.object(self.module,'sync_to_supabase',return_value={'apps_synced':8,'cves_synced':0,'apps_with_recent_cves':0,'errors':0}):
            with self.assertRaises(SystemExit):self.main()


if __name__=='__main__':unittest.main()
