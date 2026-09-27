import fs from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

export async function readAllVersions(supabase) {
  const rows = [];
  for (let start = 0; ; start += 500) {
    const { data, error } = await supabase.from('app_versions').select('*').order('id').range(start, start + 499);
    if (error) throw error;
    rows.push(...data);
    if (data.length < 500) return rows;
  }
}

export async function synchronize(supabase, apps, notify) {
  if (!apps.length) throw new Error('Refusing to synchronize an empty catalog');
  const existing = await readAllVersions(supabase);
  const byApp = new Map();
  for (const row of existing) {
    if (!byApp.has(row.app_name)) byApp.set(row.app_name, []);
    byApp.get(row.app_name).push(row);
  }
  for (const app of apps) {
    const history = (byApp.get(app.app_name) || []).sort((a,b) => Date.parse(b.created_at) - Date.parse(a.created_at));
    const current = history.find(row => row.version === app.version);
    const result = current
      ? await supabase.from('app_versions').update({...app, last_checked: new Date().toISOString()}).eq('id', current.id)
      : await supabase.from('app_versions').insert({...app, previous_version: history[0]?.version ?? null,
          notification_sent_at: history.length ? null : new Date().toISOString()});
    if (result.error) throw result.error;
  }
  // Re-read after insertion. Pending delivery survives crashes and future runs.
  const updated = await readAllVersions(supabase);
  const pending = updated.filter(row => row.notification_sent_at === null)
    .sort((a,b) => a.id.localeCompare(b.id));
  // One digest per publication, not one email per small app batch. The API's
  // recipient delivery ledger skips successful recipients on retry.
  if (pending.length) {
    await notify(pending.map(row => ({appName:row.app_name, version:row.version, changelog:row.changelog || ''})));
  }
  // Bound database filter URLs while acknowledging the delivered digest.
  for (let start = 0; start < pending.length; start += 100) {
    const batch = pending.slice(start, start + 100);
    const { error } = await supabase.from('app_versions')
      .update({notification_sent_at:new Date().toISOString()}).in('id', batch.map(row => row.id));
    if (error) throw error;
  }
  // Never delete undelivered rows; retain two most recent versions per app.
  const all = await readAllVersions(supabase);
  const groups = new Map();
  for (const row of all) {
    if (!groups.has(row.app_name)) groups.set(row.app_name, []);
    groups.get(row.app_name).push(row);
  }
  for (const rows of groups.values()) {
    const oldIds = rows.sort((a,b) => Date.parse(b.created_at)-Date.parse(a.created_at))
      .slice(2).filter(row => row.notification_sent_at !== null).map(row=>row.id);
    if (oldIds.length) {
      const { error } = await supabase.from('app_versions').delete().in('id', oldIds);
      if (error) throw error;
    }
  }
  console.log(`Synchronized ${apps.length} apps; delivered ${pending.length} pending updates`);
}

async function main() {
  const {createClient} = await import('@supabase/supabase-js');
  for (const key of ['SUPABASE_URL','SUPABASE_KEY','NOTIFICATIONS_API_KEY']) {
    if (!process.env[key]) throw new Error(`Missing ${key}`);
  }
  const index = JSON.parse(await fs.readFile('supported_apps.json','utf8'));
  const apps = [];
  for (const name of Object.keys(index)) {
    if (!/^[\w.-]+$/.test(name)) throw new Error(`Invalid catalog identifier: ${name}`);
    const data = JSON.parse(await fs.readFile(`Apps/${name}.json`,'utf8'));
    if (data.deprecated) continue;
    if (!data.version) throw new Error(`Missing version: ${name}`);
    apps.push({app_name:name, display_name:data.name || name, version:data.version,
      description:data.description || '', changelog:data.changelog || '', homepage:data.homepage || '', url:data.url || ''});
  }
  const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_KEY);
  await synchronize(supabase, apps, async updates => {
    const response = await fetch(process.env.NOTIFICATIONS_API_URL || 'https://www.intunebrew.com/api/notifications/send', {
      method:'POST', redirect:'error', headers:{'Content-Type':'application/json', Authorization:`Bearer ${process.env.NOTIFICATIONS_API_KEY}`},
      body:JSON.stringify({updates}), signal:AbortSignal.timeout(330_000)
    });
    const data = await response.json();
    if (!response.ok || data.success === false || data.results?.some(result => result.success === false) ||
        (data.webhookResults && data.webhookResults.sent < data.webhookResults.total)) {
      const reasons = [...new Set((data.results || []).filter(result => result.success === false)
        .map(result => String(result.error || 'recipient delivery failed')
          .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[recipient]')
          .replace(/https?:\/\/\S+/g, '[URL]').slice(0, 200)))];
      throw new Error(`Notification delivery failed (${response.status}); pending updates retained for retry${reasons.length ? ': ' + reasons.join('; ') : ''}`);
    }
  });
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { console.error(error.message); process.exitCode=1; });
}
