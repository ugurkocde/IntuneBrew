const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');

const openai = new OpenAI({ apiKey: process.env.OPENAI_KEY });

const APPS_DIR = path.join(__dirname, '../../Apps');
const CACHE_FILE = path.join(__dirname, '../data/bundle-id-cache.json');
const OVERRIDES_FILE = path.join(__dirname, '../data/bundle-id-overrides.json');

// How many days before we re-verify an app's bundle ID
const RECHECK_DAYS = 90;

function loadOverrides() {
  try {
    if (fs.existsSync(OVERRIDES_FILE)) {
      const data = JSON.parse(fs.readFileSync(OVERRIDES_FILE, 'utf8'));
      return data.overrides || {};
    }
  } catch (error) {
    console.error('Error loading overrides:', error.message);
  }
  return {};
}

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
  const prompt = `You are a macOS application expert. Search the web to find the EXACT macOS bundle identifier (CFBundleIdentifier) for this application.

Application Name: ${appData.name}
Description: ${appData.description || 'N/A'}
Homepage: ${appData.homepage || 'N/A'}
Publisher: ${appData.publisher || 'N/A'}
Current bundleId (may be incorrect): ${appData.bundleId || 'N/A'}

INSTRUCTIONS:
1. Search the web for the official bundle ID of this macOS application
2. Look for sources like:
   - Official documentation
   - GitHub repositories with Info.plist files
   - macOS admin guides (JAMF, Intune, Kandji, etc.)
   - Developer forums discussing this app's bundle ID
3. The bundle ID is found in the app's Info.plist file as CFBundleIdentifier

macOS bundle identifiers follow reverse domain notation, examples:
- com.microsoft.Excel
- com.apple.Safari
- org.mozilla.firefox
- com.google.Chrome

CRITICAL:
- Only provide bundle IDs you find from reliable web sources
- If you cannot find a verified bundle ID from web search, respond with "UNKNOWN"
- Do not guess or make up bundle IDs
- The bundle ID must be exact - this is critical for enterprise app management

Respond with ONLY the bundle ID or "UNKNOWN":`;

  try {
    const response = await openai.responses.create({
      model: 'gpt-5-nano',
      tools: [{ type: 'web_search' }],
      input: prompt
    });

    // Extract text content from the response
    let content = '';
    for (const item of response.output) {
      if (item.type === 'message') {
        for (const block of item.content) {
          if (block.type === 'output_text') {
            content = block.text.trim();
            break;
          }
        }
      }
    }

    // Validate bundle ID format
    if (!content || content === 'UNKNOWN' || content.toLowerCase() === 'unknown') {
      return null;
    }

    // Clean up response - remove any extra text, just get the bundle ID
    const lines = content.split('\n').map(l => l.trim()).filter(l => l);
    const bundleIdLine = lines.find(l => l.includes('.') && !l.includes(' ') && l.length < 200) || lines[0];

    // Basic validation: should contain at least one dot and no spaces
    if (bundleIdLine && bundleIdLine.includes('.') && !bundleIdLine.includes(' ') && bundleIdLine.length < 200) {
      return bundleIdLine;
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
  const overrides = loadOverrides();
  const files = fs.readdirSync(APPS_DIR).filter(f => f.endsWith('.json'));

  console.log(`Found ${files.length} app JSON files`);
  console.log(`Apps in cache: ${Object.keys(cache.apps).length}`);
  console.log(`Manual overrides: ${Object.keys(overrides).length}`);
  console.log();

  let processed = 0;
  let updated = 0;
  let skipped = 0;
  let errors = 0;
  let unknown = 0;
  let fromOverride = 0;
  const unknownApps = [];

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

      // Check for manual override first
      let newBundleId = null;
      let source = 'api';

      if (overrides[appKey]) {
        newBundleId = overrides[appKey];
        source = 'override';
        console.log(`  -> Using manual override`);
        fromOverride++;
      } else {
        newBundleId = await getBundleId(appData);
      }

      if (!newBundleId) {
        console.log(`  -> Could not determine bundle ID (unknown)`);
        unknown++;
        unknownApps.push({ key: appKey, name: appData.name, currentBundleId: appData.bundleId });

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
        console.log(`  -> Updating bundle ID (source: ${source}):`);
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
          source: source,
          name: appData.name
        };
      } else {
        console.log(`  -> Bundle ID verified: ${newBundleId}`);

        cache.apps[appKey] = {
          last_checked: new Date().toISOString(),
          bundle_id: newBundleId,
          status: 'verified',
          source: source,
          name: appData.name
        };
      }

      // Rate limiting delay (only for API calls)
      if (source === 'api') {
        await new Promise(resolve => setTimeout(resolve, 100));
      }

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
  console.log(`From overrides: ${fromOverride}`);
  console.log(`Skipped (cached): ${skipped}`);
  console.log(`Unknown: ${unknown}`);
  console.log(`Errors: ${errors}`);
  console.log('='.repeat(50));

  // Write unknown apps to a JSON file for the workflow to pick up
  const unknownAppsFile = path.join(__dirname, '../data/unknown-apps.json');
  fs.writeFileSync(unknownAppsFile, JSON.stringify(unknownApps, null, 2) + '\n');
  console.log(`\nUnknown apps written to: ${unknownAppsFile}`);
}

processApps().catch(console.error);
