import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
const read = file => readFileSync(new URL(`../.github/workflows/${file}`, import.meta.url), 'utf8');
const auto = read('auto-approve-app-request.yml');
const manual = read('approve-app-request.yml');
const build = read('build-app-packages.yml');
test('both eligible approval jobs share a queue and fetch current main', () => {
  for (const workflow of [auto, manual]) {
    assert.match(workflow, /    concurrency:\n      group: app-request-approvals\n      queue: max\n      cancel-in-progress: false/);
    assert.match(workflow, /token: \$\{\{ secrets.PAT \}\}\n          ref: main/);
    assert.match(workflow, /pending_requests\.py record/);
    assert.match(workflow, /NEEDS_REVIEW: \$\{\{ steps.add-app.outputs.needs_review \}\}/);
    assert.match(workflow, /commit_catalog\.py --approval/);
    const approved = workflow.split('      - name: Mark request approved')[1].split('      - name:')[0];
    assert.match(approved, /state: 'open'/);
    assert.doesNotMatch(approved, /state: 'closed'/);
    assert.match(workflow, /name: Comment needs review/);
  }
  assert.match(build, /group: build-app-packages\n  queue: max\n  cancel-in-progress: false/);
});
test('catalog is published before delivery and durable acknowledgement follows delivery', () => {
  const steps = ['Commit and push changes', 'Resolve pending app requests', 'Notify requesters', 'Acknowledge delivered request notifications', 'Commit acknowledged requests'];
  let previous = -1;
  for (const step of steps) {
    const position = build.indexOf(`- name: ${step}`);
    assert.ok(position > previous, `${step} must follow its prerequisite`);
    previous = position;
  }
  assert.match(build, /pending_requests\.py acknowledge/);
  assert.match(build, /revert_out_of_scope\.py/);
});
test('GitHub script blocks in the request workflows remain valid JavaScript', () => {
  const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
  for (const workflow of [auto, manual, build]) {
    for (const match of workflow.matchAll(/\n {10}script: \|\n((?: {12}[^\n]*\n|\n)+)/g)) {
      const script = match[1].replace(/^ {12}/gm, '').replace(/\$\{\{[^}]+\}\}/g, '0');
      assert.doesNotThrow(() => new AsyncFunction('github', 'context', 'core', 'require', script));
    }
  }
});
