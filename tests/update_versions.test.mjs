import test from 'node:test';
import assert from 'node:assert/strict';
import { readAllVersions, synchronize } from '../.github/scripts/update_versions.mjs';
test('reads beyond the API row limit', async () => {
  const records=Array.from({length:1251},(_,id)=>({id}));
  const client={from:()=>({select:()=>({order:()=>({range:async (a,b)=>({data:records.slice(a,b+1),error:null})})})})};
  assert.equal((await readAllVersions(client)).length,1251);
});
test('database failures reject rather than pretending the table is empty', async () => {
  const client={from:()=>({select:()=>({order:()=>({range:async ()=>({data:null,error:new Error('denied')})})})})};
  await assert.rejects(readAllVersions(client), /denied/);
});
test('notification failure keeps a pending version for the next run', async () => {
  const rows=[{id:'a',app_name:'app',version:'1',created_at:'2026-01-01',notification_sent_at:'2026-01-01'}];
  const client={from:()=>({
    select:()=>({order:()=>({range:async (a,b)=>({data:structuredClone(rows.slice(a,b+1)),error:null})})}),
    insert:async row=>{rows.push({...row,id:'b',created_at:'2026-09-27'});return {error:null}},
    update:values=>({eq:async (_,id)=>{Object.assign(rows.find(r=>r.id===id),values);return {error:null}},in:async (_,ids)=>{rows.filter(r=>ids.includes(r.id)).forEach(r=>Object.assign(r,values));return {error:null}}}),
    delete:()=>({in:async ()=>({error:null})})
  })};
  await assert.rejects(synchronize(client,[{app_name:'app',version:'2'}],async()=>{throw new Error('unavailable')}),/unavailable/);
  assert.equal(rows[1].notification_sent_at,null);
  let delivered=0;
  await synchronize(client,[{app_name:'app',version:'2'}],async updates=>{delivered+=updates.length});
  assert.equal(delivered,1);
  assert.equal(rows.length,2);
  assert.ok(rows[1].notification_sent_at);
});

test('catch-up updates are sent in one digest, with bounded database acknowledgements', async () => {
  const rows=Array.from({length:225},(_,i)=>({id:String(i).padStart(3,'0'),app_name:`app${i}`,version:'2',created_at:'2026-09-27',notification_sent_at:null}));
  const acknowledgements=[];
  const client={from:()=>({
    select:()=>({order:()=>({range:async(a,b)=>({data:structuredClone(rows.slice(a,b+1)),error:null})})}),
    update:values=>({eq:async()=>({error:null}),in:async(_,ids)=>{acknowledgements.push(ids.length);rows.filter(r=>ids.includes(r.id)).forEach(r=>Object.assign(r,values));return {error:null}}})
  })};
  const calls=[];
  await synchronize(client,rows.map(r=>({app_name:r.app_name,version:r.version})),async updates=>{calls.push(updates.length)});
  assert.deepEqual(calls,[225]);
  assert.deepEqual(acknowledgements,[100,100,25]);
});
