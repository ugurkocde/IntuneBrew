const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');

const openai = new OpenAI({ apiKey: process.env.OPENAI_KEY });

const APPS_DIR = path.join(__dirname, '../../Apps');
const CACHE_FILE = path.join(__dirname, '../data/bundle-id-cache.json');

// How many days before we re-verify an app's bundle ID
const RECHECK_DAYS = 90;

function loadCache() {
  try {
    if (fs.existsSync(CACHE_FILE)) {
      return JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
    }
  } catch (error) {
    console.error('Error loading cache:', error.message);
  }
  return { version: 1, description: 'Bundle ID verification cache', last_full_scan: null, apps: {} };
}

function saveCache(cache) {
  const dir = path.dirname(CACHE_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2) + '\n');
}

function needsCheck(cache, appKey, forceRecheck) {
  if (forceRecheck) return true;

  const cached = cache.apps[appKey];
  if (!cached) return true;

  // Re-check if it's been more than RECHECK_DAYS since last verification
  const lastChecked = new Date(cached.last_checked);
  const daysSince = (Date.now() - lastChecked.getTime()) / (1000 * 60 * 60 * 24);

  return daysSince > RECHECK_DAYS;
}

async function getBundleId(appData) {
  const prompt = `You are a macOS application expert. Given the following application information, provide the EXACT macOS bundle identifier (bundleId) for this application.

Application Name: ${appData.name}
Description: ${appData.description || 'N/A'}
Homepage: ${appData.homepage || 'N/A'}
Publisher: ${appData.publisher || 'N/A'}
Current bundleId (may be incorrect): ${appData.bundleId || 'N/A'}

macOS bundle identifiers follow reverse domain notation, typically like:
- com.company.appname
- org.organization.appname
- io.company.appname

Research and provide the CORRECT bundle identifier for this macOS application.

IMPORTANT:
- Only provide the bundle ID, nothing else
- If you're not confident about the exact bundle ID, respond with "UNKNOWN"
- The bundle ID should be the one that appears in the Info.plist of the .app bundle
- Do not guess - only provide if you're confident

Respond with ONLY the bundle ID (e.g., "com.apple.Safari") or "UNKNOWN":`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.1,
      max_tokens: 100
    });

    const content = response.choices[0].message.content.trim();

    // Validate bundle ID format
    if (content === 'UNKNOWN' || content.toLowerCase() === 'unknown') {
      return null;
    }

    // Basic validation: should contain at least one dot and no spaces
    if (content.includes('.') && !content.includes(' ') && content.length < 200) {
      return content;
    }

    return null;
  } catch (error) {
    console.error(`  OpenAI API error: ${error.message}`);
    return null;
  }
}

async function processApps() {
  const forceRecheck = process.env.FORCE_RECHECK === 'true';
  const maxApps = parseInt(process.env.MAX_APPS || '0', 10) || Infinity;

  console.log('='.repeat(50));
  console.log('Bundle ID Verification Tool');
  console.log('='.repeat(50));
  console.log(`Force recheck: ${forceRecheck}`);
  console.log(`Max apps to process: ${maxApps === Infinity ? 'unlimited' : maxApps}`);
  console.log();

  const cache = loadCache();
  const files = fs.readdirSync(APPS_DIR).filter(f => f.endsWith('.json'));

  console.log(`Found ${files.length} app JSON files`);
  console.log(`Apps in cache: ${Object.keys(cache.apps).length}`);
  console.log();

  let processed = 0;
  let updated = 0;
  let skipped = 0;
  let errors = 0;
  let unknown = 0;

  for (const file of files) {
    if (processed >= maxApps) {
      console.log(`\nReached max apps limit (${maxApps}), stopping.`);
      break;
    }

    const appKey = file.replace('.json', '');
    const filePath = path.join(APPS_DIR, file);

    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const appData = JSON.parse(content);

      // Check if we need to verify this app
      if (!needsCheck(cache, appKey, forceRecheck)) {
        skipped++;
        continue;
      }

      processed++;
      console.log(`[${processed}] Processing: ${appData.name || appKey}`);

      const newBundleId = await getBundleId(appData);

      if (!newBundleId) {
        console.log(`  -> Could not determine bundle ID (unknown)`);
        unknown++;

        // Still mark as checked so we don't keep retrying
        cache.apps[appKey] = {
          last_checked: new Date().toISOString(),
          bundle_id: appData.bundleId || null,
          status: 'unknown',
          name: appData.name
        };
        continue;
      }

      const oldBundleId = appData.bundleId;

      if (newBundleId !== oldBundleId) {
        console.log(`  -> Updating bundle ID:`);
        console.log(`     Old: ${oldBundleId || '(empty)'}`);
        console.log(`     New: ${newBundleId}`);

        appData.bundleId = newBundleId;
        fs.writeFileSync(filePath, JSON.stringify(appData, null, 2) + '\n');
        updated++;

        cache.apps[appKey] = {
          last_checked: new Date().toISOString(),
          bundle_id: newBundleId,
          previous_bundle_id: oldBundleId || null,
          status: 'updated',
          name: appData.name
        };
      } else {
        console.log(`  -> Bundle ID verified: ${newBundleId}`);

        cache.apps[appKey] = {
          last_checked: new Date().toISOString(),
          bundle_id: newBundleId,
          status: 'verified',
          name: appData.name
        };
      }

      // Rate limiting delay
      await new Promise(resolve => setTimeout(resolve, 100));

    } catch (error) {
      console.error(`Error processing ${file}: ${error.message}`);
      errors++;
    }
  }

  // Update cache timestamp
  cache.last_full_scan = new Date().toISOString();
  saveCache(cache);

  console.log();
  console.log('='.repeat(50));
  console.log('Summary');
  console.log('='.repeat(50));
  console.log(`Processed: ${processed}`);
  console.log(`Updated: ${updated}`);
  console.log(`Skipped (cached): ${skipped}`);
  console.log(`Unknown: ${unknown}`);
  console.log(`Errors: ${errors}`);
  console.log('='.repeat(50));
}

processApps().catch(console.error);
