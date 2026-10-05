import assert from 'node:assert/strict';
import test from 'node:test';
import { createRequire } from 'node:module';
const { notifyRequests } = createRequire(import.meta.url)('../.github/scripts/notify_app_requests.cjs');
const item = {issue: 42, kind: 'live', marker: '<!-- intunebrew-request:revision -->', apps: [{name: 'Requested', version: '1'}]};
function fixture() {
  const comments = [], updates = [], labels = [];
  let failComment = false, failUpdate = false;
  const issues = {
    listComments: () => {},
    createComment: async params => {
      if (failComment) throw new Error('API unavailable');
      comments.push({...params, user: {login: 'github-actions[bot]'}});
    },
    removeLabel: async params => labels.push(params),
    addLabels: async params => labels.push(params),
    update: async params => {
      if (failUpdate) throw new Error('API unavailable');
      updates.push(params);
    }
  };
  return {comments, updates, labels, github: {rest: {issues}, paginate: async () => comments},
    failComment: value => {failComment = value}, failUpdate: value => {failUpdate = value}};
}
const send = (f, notifications = [item]) => notifyRequests({github: f.github, owner: 'owner', repo: 'repo', notifications, log: () => {}});
test('successful notification closes only a fully fulfilled issue', async () => {
  const f = fixture();
  assert.deepEqual(await send(f), [item]);
  assert.equal(f.comments.length, 1);
  assert.equal(f.updates[0].state, 'closed');
  assert.match(f.comments[0].body, /Now live/);
});
test('failed delivery stays unacknowledged and succeeds on retry', async () => {
  const f = fixture();f.failComment(true);
  assert.deepEqual(await send(f), []);
  assert.equal(f.updates.length, 0);
  f.failComment(false);
  assert.deepEqual(await send(f), [item]);
});
test('comment succeeds but closure fails: retry completes without duplicating the comment', async () => {
  const f = fixture();f.failUpdate(true);
  assert.deepEqual(await send(f), []);
  assert.equal(f.comments.length, 1);
  f.failUpdate(false);
  assert.deepEqual(await send(f), [item]);
  assert.equal(f.comments.length, 1);
});
test('a comment marker forged by an issue participant does not suppress notification', async () => {
  const f = fixture();f.comments.push({body: item.marker, user: {login: 'requester'}});
  assert.deepEqual(await send(f), [item]);
  assert.equal(f.comments.length, 2);
});
test('partial fulfillment leaves the issue open for review', async () => {
  const f = fixture();const partial = {...item, needs_review: true};
  assert.deepEqual(await send(f, [partial]), [partial]);
  assert.equal(f.updates[0].state, 'open');
  assert.deepEqual(f.labels[0].labels, ['needs-review']);
});
test('stale requests receive a review notice and remain open', async () => {
  const f = fixture();const stale = {...item, kind: 'needs-review', missing: ['requested']};
  assert.deepEqual(await send(f, [stale]), [stale]);
  assert.equal(f.updates[0].state, 'open');
  assert.match(f.comments[0].body, /Build needs review/);
});
test('one unavailable issue does not prevent another delivery', async () => {
  const f = fixture();const original = f.github.rest.issues.createComment;
  f.github.rest.issues.createComment = async params => {
    if (params.issue_number === 42) throw new Error('Locked issue');
    return original(params);
  };
  const other = {...item, issue: 43};
  assert.deepEqual(await send(f, [item, other]), [other]);
});
