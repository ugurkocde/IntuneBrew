import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const workflow=readFileSync(new URL('../.github/workflows/url-health-check.yml',import.meta.url),'utf8');
const steps=workflow.split(/^      - name: /m).slice(1).map(text=>({name:text.split('\n')[0],text}));
const issueSteps=new Set(['Find existing report issue','Create or update report issue','Close report issue when everything is healthy']);

test('manual report mode retains the scheduled full monitor and existing permissions',()=>{
  assert.equal(workflow.split('on:\n')[1].split('\npermissions:')[0],
    '  workflow_dispatch:\n    inputs:\n      report_only:\n        description: "Run the full check and upload its report without changing the tracking issue"\n        type: boolean\n        default: false\n  schedule:\n    - cron: "0 6 * * 1,4" # Mondays and Thursdays at 06:00 UTC\n');
  assert.equal(workflow.split('permissions:\n')[1].split('\nenv:')[0],'  contents: read\n  issues: write\n');
  assert.equal((workflow.match(/^permissions:/gm)||[]).length,1);
  assert.doesNotMatch(workflow,/^ +permissions:|id-token|secrets\.|github\.event\.inputs|continue-on-error|pull_request_target/mi);
  assert.match(workflow,/    runs-on: ubuntu-latest/);
  assert.deepEqual([...workflow.matchAll(/uses: (.+)/g)].map(x=>x[1]),['actions/checkout@v7','actions/setup-python@v6','actions/upload-artifact@v7']);
});

test('report-only mode skips every issue interaction, preserving full checks and artifacts',()=>{
  assert.deepEqual(steps.map(s=>s.name),['Checkout repository','Set up Python','Install dependencies','Check download URLs','Find existing report issue','Create or update report issue','Close report issue when everything is healthy','Upload report artifact']);
  for(const step of steps){
    if(issueSteps.has(step.name))assert.match(step.text,/\n        if: \$\{\{ !inputs\.report_only(?: &&[^\n]+)? \}\}\n/);
    else assert.doesNotMatch(step.text,/report_only|gh issue/);
    if(step.text.includes('gh issue'))assert.ok(issueSteps.has(step.name));
  }
  const check=steps.find(s=>s.name==='Check download URLs').text;
  assert.match(check,/run: python \.github\/scripts\/check_download_urls\.py/);
  assert.doesNotMatch(check,/\n        if:|APPS_FOLDER|filter|subset/);
  assert.match(steps.find(s=>s.name==='Install dependencies').text,/requests==2\.34\.2/);
  assert.match(steps.find(s=>s.name==='Upload report artifact').text,/if: always\(\)/);
  assert.match(steps.find(s=>s.name==='Upload report artifact').text,/name: url-health-report\n          path: url-health-report\.md/);
});

test('boolean input preserves scheduled and default dispatch issue decisions',()=>{
  const find=steps.find(s=>s.name==='Find existing report issue').text;
  const update=steps.find(s=>s.name==='Create or update report issue').text;
  const close=steps.find(s=>s.name==='Close report issue when everything is healthy').text;
  assert.match(find,/if: \$\{\{ !inputs\.report_only \}\}/);
  assert.match(update,/if: \$\{\{ !inputs\.report_only && steps\.check\.outputs\.broken_count != '0' \}\}/);
  assert.match(close,/if: \$\{\{ !inputs\.report_only && steps\.check\.outputs\.broken_count == '0' && steps\.issue\.outputs\.number != '' \}\}/);
  for(const reportOnly of [undefined,false,true])for(const count of ['0','4'])for(const number of ['','331']){
    const actual={find:!reportOnly,update:!reportOnly&&count!=='0',close:!reportOnly&&count==='0'&&number!==''};
    const expected=reportOnly?{find:false,update:false,close:false}:{find:true,update:count!=='0',close:count==='0'&&number!==''};
    assert.deepEqual(actual,expected);
  }
});
