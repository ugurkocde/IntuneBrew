const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const https = require('https');
const http = require('http');

// Only initialize OpenAI if API key is provided (allows running locally for cache sync)
let openai = null;
if (process.env.OPENAI_KEY) {
  const OpenAI = require('openai');
  openai = new OpenAI({ apiKey: process.env.OPENAI_KEY });
}

// Try to load plist parser
let plist = null;
try {
  plist = require('plist');
} catch (e) {
  console.log('Note: plist module not available, using regex fallback for plist parsing');
}

const APPS_DIR = path.join(__dirname, '../../Apps');
const CACHE_FILE = path.join(__dirname, '../data/bundle-id-cache.json');
const OVERRIDES_FILE = path.join(__dirname, '../data/bundle-id-overrides.json');
const TEMP_DIR = path.join(__dirname, '../temp');

// How many days before we re-verify an app's bundle ID
const RECHECK_DAYS = 90;

// Validation function for bundle IDs
function isValidBundleId(bundleId) {
  if (!bundleId || typeof bundleId !== 'string') return false;
  // Must contain at least one dot
  if (!bundleId.includes('.')) return false;
  // Must not contain spaces
  if (bundleId.includes(' ')) return false;
  // Must be reasonable length
  if (bundleId.length < 3 || bundleId.length > 200) return false;
  // Must match reverse domain notation pattern (letters, numbers, dots, hyphens, underscores)
  if (!/^[a-zA-Z0-9._-]+$/.test(bundleId)) return false;
  return true;
}

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

function needsCheck(cache, appKey, currentBundleId, forceRecheck) {
  if (forceRecheck) return { needsApi: true, reason: 'force' };

  // If the app already has a valid bundleId, no API call needed
  // We'll still sync the cache but won't call the API
  if (currentBundleId && typeof currentBundleId === 'string' && currentBundleId.includes('.')) {
    const cached = cache.apps[appKey];
    // If cache matches reality, skip entirely
    if (cached && cached.bundle_id === currentBundleId && cached.status !== 'unknown') {
      return { needsApi: false, needsSync: false, reason: 'already_verified' };
    }
    // Cache is out of sync - sync it without API call
    return { needsApi: false, needsSync: true, reason: 'sync_cache' };
  }

  // No bundleId in file - check cache
  const cached = cache.apps[appKey];
  if (!cached) return { needsApi: true, reason: 'not_in_cache' };

  // Re-check if it's been more than RECHECK_DAYS since last verification
  const lastChecked = new Date(cached.last_checked);
  const daysSince = (Date.now() - lastChecked.getTime()) / (1000 * 60 * 60 * 24);

  if (daysSince > RECHECK_DAYS) {
    return { needsApi: true, reason: 'stale_cache' };
  }

  return { needsApi: false, needsSync: false, reason: 'cached' };
}

// Helper function for HTTP requests
function httpGet(url) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    const request = protocol.get(url, {
      headers: {
        'User-Agent': 'IntuneBrew/1.0',
        'Accept': 'application/json'
      },
      timeout: 30000
    }, (response) => {
      // Handle redirects
      if (response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
        httpGet(response.headers.location).then(resolve).catch(reject);
        return;
      }

      if (response.statusCode !== 200) {
        reject(new Error(`HTTP ${response.statusCode}`));
        return;
      }

      let data = '';
      response.on('data', chunk => data += chunk);
      response.on('end', () => resolve(data));
    });

    request.on('error', reject);
    request.on('timeout', () => {
      request.destroy();
      reject(new Error('Request timeout'));
    });
  });
}

// Method 1: Mac App Store API Lookup
async function lookupMacAppStore(appData) {
  const appName = appData.name;
  if (!appName) return null;

  try {
    // Search the iTunes API for macOS apps
    const searchQuery = encodeURIComponent(appName);
    const url = `https://itunes.apple.com/search?term=${searchQuery}&entity=macSoftware&limit=10`;

    const response = await httpGet(url);
    const data = JSON.parse(response);

    if (!data.results || data.results.length === 0) {
      return null;
    }

    // Try to find an exact or close match
    const normalizedAppName = appName.toLowerCase().replace(/[^a-z0-9]/g, '');

    for (const result of data.results) {
      const resultName = (result.trackName || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      const sellerName = (result.sellerName || '').toLowerCase();

      // Check for exact match or if the app name is contained
      if (resultName === normalizedAppName ||
          resultName.includes(normalizedAppName) ||
          normalizedAppName.includes(resultName)) {
        if (result.bundleId && isValidBundleId(result.bundleId)) {
          return result.bundleId;
        }
      }

      // Also check if publisher matches
      if (appData.publisher) {
        const normalizedPublisher = appData.publisher.toLowerCase().replace(/[^a-z0-9]/g, '');
        if (sellerName.includes(normalizedPublisher) || normalizedPublisher.includes(sellerName)) {
          if (result.bundleId && isValidBundleId(result.bundleId)) {
            return result.bundleId;
          }
        }
      }
    }

    return null;
  } catch (error) {
    console.log(`    Mac App Store lookup error: ${error.message}`);
    return null;
  }
}

// Method 2: PKG/DMG File Inspection
async function extractBundleIdFromPackage(appData) {
  // Get download URL from app data
  const downloadUrl = appData.url;
  if (!downloadUrl) return null;

  // Only process PKG files for now (DMG is more complex)
  if (!downloadUrl.toLowerCase().endsWith('.pkg')) {
    return null;
  }

  // Create temp directory
  if (!fs.existsSync(TEMP_DIR)) {
    fs.mkdirSync(TEMP_DIR, { recursive: true });
  }

  const pkgPath = path.join(TEMP_DIR, 'temp.pkg');
  const extractDir = path.join(TEMP_DIR, 'extract');

  try {
    // Download the PKG file (just the first 50MB to save time/bandwidth)
    console.log(`    Downloading PKG for inspection...`);

    // Use curl with range to get partial download if possible
    try {
      execSync(`curl -sL -o "${pkgPath}" --max-filesize 52428800 "${downloadUrl}"`, {
        timeout: 120000,
        stdio: ['pipe', 'pipe', 'pipe']
      });
    } catch (e) {
      // If max-filesize fails, try without it but with timeout
      execSync(`curl -sL -o "${pkgPath}" --max-time 60 "${downloadUrl}"`, {
        timeout: 120000,
        stdio: ['pipe', 'pipe', 'pipe']
      });
    }

    if (!fs.existsSync(pkgPath)) {
      return null;
    }

    // Create extraction directory
    if (fs.existsSync(extractDir)) {
      fs.rmSync(extractDir, { recursive: true, force: true });
    }
    fs.mkdirSync(extractDir, { recursive: true });

    // Extract PKG using 7z (works on Ubuntu, unlike xar)
    try {
      execSync(`7z x "${pkgPath}" -o"${extractDir}" -y`, {
        timeout: 30000,
        stdio: ['pipe', 'pipe', 'pipe']
      });
    } catch (e) {
      console.log(`    PKG extraction failed: ${e.message}`);
      cleanup();
      return null;
    }

    // Look for Info.plist in various locations
    let bundleId = null;

    // Method A: Check PackageInfo files first (usually has bundle-identifier)
    const packageInfoFiles = findFiles(extractDir, 'PackageInfo');
    for (const file of packageInfoFiles) {
      try {
        const content = fs.readFileSync(file, 'utf8');
        // PackageInfo is XML, look for bundle-identifier attribute
        const match = content.match(/identifier="([^"]+)"/);
        if (match && isValidBundleId(match[1])) {
          bundleId = match[1];
          break;
        }
      } catch (e) {
        // Continue to next file
      }
    }

    if (bundleId) {
      cleanup();
      return bundleId;
    }

    // Method B: Extract and check Payload for Info.plist
    const payloadFiles = findFiles(extractDir, 'Payload');
    for (const payloadPath of payloadFiles) {
      try {
        const payloadDir = path.join(path.dirname(payloadPath), 'payload_contents');
        fs.mkdirSync(payloadDir, { recursive: true });

        // Payload is usually a gzipped cpio archive - use 7z to extract
        try {
          execSync(`7z x "${payloadPath}" -o"${payloadDir}" -y`, {
            timeout: 30000,
            stdio: ['pipe', 'pipe', 'pipe']
          });
        } catch (e) {
          // 7z might fail on some payload formats, continue
        }

        // Find Info.plist files
        const infoPlistFiles = findFiles(payloadDir, 'Info.plist');
        for (const plistFile of infoPlistFiles) {
          const extractedId = extractBundleIdFromPlist(plistFile);
          if (extractedId) {
            bundleId = extractedId;
            break;
          }
        }

        if (bundleId) break;
      } catch (e) {
        // Continue to next payload
      }
    }

    // Method C: Check Distribution file (flat packages)
    const distFiles = findFiles(extractDir, 'Distribution');
    for (const distFile of distFiles) {
      try {
        const content = fs.readFileSync(distFile, 'utf8');
        // Look for bundle identifier patterns
        const match = content.match(/identifier="([^"]+)"/) ||
                     content.match(/CFBundleIdentifier[^>]*>([^<]+)</);
        if (match && isValidBundleId(match[1])) {
          bundleId = match[1];
          break;
        }
      } catch (e) {
        // Continue
      }
    }

    cleanup();
    return bundleId;

  } catch (error) {
    console.log(`    PKG inspection error: ${error.message}`);
    cleanup();
    return null;
  }

  function cleanup() {
    try {
      if (fs.existsSync(pkgPath)) fs.unlinkSync(pkgPath);
      if (fs.existsSync(extractDir)) fs.rmSync(extractDir, { recursive: true, force: true });
    } catch (e) {
      // Ignore cleanup errors
    }
  }
}

// Helper function to find files recursively
function findFiles(dir, filename) {
  const results = [];

  function search(currentDir) {
    try {
      const items = fs.readdirSync(currentDir);
      for (const item of items) {
        const fullPath = path.join(currentDir, item);
        try {
          const stat = fs.statSync(fullPath);
          if (stat.isDirectory()) {
            search(fullPath);
          } else if (item === filename || item.endsWith(filename)) {
            results.push(fullPath);
          }
        } catch (e) {
          // Skip files we can't stat
        }
      }
    } catch (e) {
      // Skip directories we can't read
    }
  }

  search(dir);
  return results;
}

// Helper function to extract bundle ID from Info.plist
function extractBundleIdFromPlist(plistPath) {
  try {
    const content = fs.readFileSync(plistPath, 'utf8');

    // Try using plist module if available
    if (plist) {
      try {
        const parsed = plist.parse(content);
        if (parsed.CFBundleIdentifier && isValidBundleId(parsed.CFBundleIdentifier)) {
          return parsed.CFBundleIdentifier;
        }
      } catch (e) {
        // Fall through to regex
      }
    }

    // Fallback: regex extraction
    const match = content.match(/<key>CFBundleIdentifier<\/key>\s*<string>([^<]+)<\/string>/);
    if (match && isValidBundleId(match[1])) {
      return match[1];
    }

    return null;
  } catch (e) {
    return null;
  }
}

// Method 3: GitHub Code Search
async function searchGitHubForBundleId(appData) {
  const githubToken = process.env.GITHUB_TOKEN;
  if (!githubToken) {
    return null;
  }

  const appName = appData.name;
  if (!appName) return null;

  try {
    // Search for Info.plist files containing the app name
    const searchQuery = encodeURIComponent(`CFBundleIdentifier ${appName} filename:Info.plist`);
    const url = `https://api.github.com/search/code?q=${searchQuery}&per_page=5`;

    const response = await new Promise((resolve, reject) => {
      const request = https.get(url, {
        headers: {
          'User-Agent': 'IntuneBrew/1.0',
          'Accept': 'application/vnd.github.v3+json',
          'Authorization': `token ${githubToken}`
        },
        timeout: 15000
      }, (response) => {
        if (response.statusCode !== 200) {
          reject(new Error(`GitHub API: ${response.statusCode}`));
          return;
        }
        let data = '';
        response.on('data', chunk => data += chunk);
        response.on('end', () => resolve(data));
      });
      request.on('error', reject);
      request.on('timeout', () => {
        request.destroy();
        reject(new Error('Request timeout'));
      });
    });

    const data = JSON.parse(response);

    if (!data.items || data.items.length === 0) {
      return null;
    }

    // Try to fetch and parse the first few results
    for (const item of data.items.slice(0, 3)) {
      try {
        // Get raw file content
        const rawUrl = item.html_url
          .replace('github.com', 'raw.githubusercontent.com')
          .replace('/blob/', '/');

        const fileContent = await httpGet(rawUrl);

        // Extract bundle ID
        const match = fileContent.match(/<key>CFBundleIdentifier<\/key>\s*<string>([^<]+)<\/string>/);
        if (match && isValidBundleId(match[1])) {
          // Verify it seems related to the app
          const bundleId = match[1].toLowerCase();
          const appNameLower = appName.toLowerCase().replace(/[^a-z0-9]/g, '');

          // Check if bundle ID contains app name or vice versa
          if (bundleId.includes(appNameLower) ||
              appNameLower.includes(bundleId.split('.').pop())) {
            return match[1];
          }
        }
      } catch (e) {
        // Continue to next result
      }
    }

    return null;
  } catch (error) {
    console.log(`    GitHub search error: ${error.message}`);
    return null;
  }
}

// Method 4: Improved OpenAI Prompt
async function getBundleIdWithImprovedPrompt(appData) {
  if (!openai) {
    return null;
  }

  // Extract domain from homepage for context
  let domainHint = '';
  if (appData.homepage) {
    try {
      const url = new URL(appData.homepage);
      const parts = url.hostname.replace('www.', '').split('.');
      if (parts.length >= 2) {
        domainHint = `Based on the homepage domain, the bundle ID likely starts with: com.${parts[0]} or ${parts.reverse().join('.')}`;
      }
    } catch (e) {
      // Ignore URL parsing errors
    }
  }

  const prompt = `You are a macOS MDM (Mobile Device Management) expert. Search the web to find the EXACT macOS bundle identifier (CFBundleIdentifier) for this application.

Application Details:
- Name: ${appData.name}
- Description: ${appData.description || 'N/A'}
- Homepage: ${appData.homepage || 'N/A'}
- Publisher: ${appData.publisher || 'N/A'}
- Download URL: ${appData.url || 'N/A'}
${domainHint ? `- ${domainHint}` : ''}

SEARCH INSTRUCTIONS:
1. Search for "${appData.name} macOS bundle identifier" or "${appData.name} CFBundleIdentifier"
2. Look specifically in these sources:
   - JAMF Nation / JAMF Pro documentation
   - Microsoft Intune app deployment guides
   - Kandji library or documentation
   - Mosyle MDM documentation
   - MacAdmins Slack archives
   - GitHub repositories with Info.plist files
   - Official vendor documentation
3. The bundle ID is found in the app's Info.plist as CFBundleIdentifier

Bundle ID Format Examples:
- com.microsoft.Excel
- com.apple.Safari
- org.mozilla.firefox
- com.google.Chrome
- com.linear (for Linear app)
- com.figma.Desktop (for Figma)

CRITICAL RULES:
- Only return bundle IDs you find from reliable web sources
- If you cannot find a verified bundle ID, respond with "UNKNOWN"
- Do not guess or fabricate bundle IDs
- The bundle ID must be exact - enterprise MDM systems require precision

Response format: Return ONLY the bundle ID string or "UNKNOWN"`;

  try {
    const response = await openai.responses.create({
      model: 'gpt-5-nano',
      tools: [{ type: 'web_search' }],
      input: prompt
    });

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

    if (!content || content === 'UNKNOWN' || content.toLowerCase() === 'unknown') {
      return null;
    }

    // Clean up response
    const lines = content.split('\n').map(l => l.trim()).filter(l => l);
    const bundleIdLine = lines.find(l => l.includes('.') && !l.includes(' ') && l.length < 200) || lines[0];

    if (bundleIdLine && isValidBundleId(bundleIdLine)) {
      return bundleIdLine;
    }

    return null;
  } catch (error) {
    console.error(`    OpenAI API error: ${error.message}`);
    return null;
  }
}

// Method 5: Alternative OpenAI Prompt (Retry with different approach)
async function getBundleIdWithAlternativePrompt(appData) {
  if (!openai) {
    return null;
  }

  // More direct, focused prompt
  const prompt = `Find the macOS CFBundleIdentifier for: ${appData.name}

Search for:
- "${appData.name} Info.plist CFBundleIdentifier"
- "${appData.name} bundle id mac"

Common patterns: com.company.appname, org.company.appname

Return ONLY the bundle ID or UNKNOWN if not found.`;

  try {
    const response = await openai.responses.create({
      model: 'gpt-5-nano',
      tools: [{ type: 'web_search' }],
      input: prompt
    });

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

    if (!content || content === 'UNKNOWN' || content.toLowerCase() === 'unknown') {
      return null;
    }

    const lines = content.split('\n').map(l => l.trim()).filter(l => l);
    const bundleIdLine = lines.find(l => l.includes('.') && !l.includes(' ') && l.length < 200) || lines[0];

    if (bundleIdLine && isValidBundleId(bundleIdLine)) {
      return bundleIdLine;
    }

    return null;
  } catch (error) {
    console.error(`    OpenAI alternative prompt error: ${error.message}`);
    return null;
  }
}

// Main bundle ID lookup with fallback methods
async function getBundleId(appData) {
  const methods = [
    { name: 'mac_app_store', fn: lookupMacAppStore },
    { name: 'pkg_inspection', fn: extractBundleIdFromPackage },
    { name: 'github_search', fn: searchGitHubForBundleId },
    { name: 'openai_improved', fn: getBundleIdWithImprovedPrompt },
    { name: 'openai_alternative', fn: getBundleIdWithAlternativePrompt }
  ];

  const methodsTried = [];

  for (const method of methods) {
    console.log(`    Trying: ${method.name}...`);
    methodsTried.push(method.name);

    try {
      const bundleId = await method.fn(appData);
      if (bundleId && isValidBundleId(bundleId)) {
        console.log(`    Found via ${method.name}: ${bundleId}`);
        return { bundleId, source: method.name, methods_tried: methodsTried };
      }
    } catch (error) {
      console.log(`    ${method.name} failed: ${error.message}`);
    }
  }

  return { bundleId: null, source: null, methods_tried: methodsTried };
}

async function processApps() {
  const forceRecheck = process.env.FORCE_RECHECK === 'true';
  const maxApps = parseInt(process.env.MAX_APPS || '0', 10) || Infinity;

  console.log('='.repeat(60));
  console.log('Bundle ID Verification Tool (Multi-Method Fallback)');
  console.log('='.repeat(60));
  console.log(`Force recheck: ${forceRecheck}`);
  console.log(`Max apps to process: ${maxApps === Infinity ? 'unlimited' : maxApps}`);
  console.log();
  console.log('Lookup methods (in order):');
  console.log('  1. Manual overrides');
  console.log('  2. Mac App Store API');
  console.log('  3. PKG file inspection');
  console.log('  4. GitHub code search');
  console.log('  5. OpenAI web search (improved)');
  console.log('  6. OpenAI web search (alternative)');
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
  let synced = 0;
  let errors = 0;
  let unknown = 0;
  let fromOverride = 0;
  const unknownApps = [];
  const methodStats = {};

  for (const file of files) {
    const appKey = file.replace('.json', '');
    const filePath = path.join(APPS_DIR, file);

    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const appData = JSON.parse(content);

      // Check if we need to verify this app
      const checkResult = needsCheck(cache, appKey, appData.bundleId, forceRecheck);

      if (!checkResult.needsApi && !checkResult.needsSync) {
        skipped++;
        continue;
      }

      // If we just need to sync the cache (file has bundleId but cache is out of sync)
      if (!checkResult.needsApi && checkResult.needsSync) {
        cache.apps[appKey] = {
          last_checked: new Date().toISOString(),
          bundle_id: appData.bundleId,
          status: 'verified',
          source: 'file',
          name: appData.name
        };
        synced++;
        continue;
      }

      // Need lookup - check max limit
      if (processed >= maxApps) {
        console.log(`\nReached max apps limit (${maxApps}), stopping.`);
        break;
      }

      processed++;
      console.log(`[${processed}] Processing: ${appData.name || appKey} (${checkResult.reason})`);

      // Check for manual override first
      let newBundleId = null;
      let source = null;
      let methodsTried = [];

      if (overrides[appKey]) {
        newBundleId = overrides[appKey];
        source = 'override';
        console.log(`  -> Using manual override: ${newBundleId}`);
        fromOverride++;
        methodsTried = ['override'];
      } else {
        // Use multi-method fallback system
        const result = await getBundleId(appData);
        newBundleId = result.bundleId;
        source = result.source;
        methodsTried = result.methods_tried || [];
      }

      // Track method statistics
      if (source) {
        methodStats[source] = (methodStats[source] || 0) + 1;
      }

      if (!newBundleId) {
        console.log(`  -> Could not determine bundle ID (unknown)`);
        unknown++;
        unknownApps.push({
          key: appKey,
          name: appData.name,
          currentBundleId: appData.bundleId,
          methods_tried: methodsTried
        });

        // Still mark as checked so we don't keep retrying
        cache.apps[appKey] = {
          last_checked: new Date().toISOString(),
          bundle_id: appData.bundleId || null,
          status: 'unknown',
          methods_tried: methodsTried,
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
          methods_tried: methodsTried,
          name: appData.name
        };
      } else {
        console.log(`  -> Bundle ID verified: ${newBundleId}`);

        cache.apps[appKey] = {
          last_checked: new Date().toISOString(),
          bundle_id: newBundleId,
          status: 'verified',
          source: source,
          methods_tried: methodsTried,
          name: appData.name
        };
      }

      // Small delay between apps to be respectful to APIs
      await new Promise(resolve => setTimeout(resolve, 100));

    } catch (error) {
      console.error(`Error processing ${file}: ${error.message}`);
      errors++;
    }
  }

  // Cleanup temp directory
  try {
    if (fs.existsSync(TEMP_DIR)) {
      fs.rmSync(TEMP_DIR, { recursive: true, force: true });
    }
  } catch (e) {
    // Ignore cleanup errors
  }

  // Update cache timestamp
  cache.last_full_scan = new Date().toISOString();
  saveCache(cache);

  console.log();
  console.log('='.repeat(60));
  console.log('Summary');
  console.log('='.repeat(60));
  console.log(`Apps processed: ${processed}`);
  console.log(`Updated: ${updated}`);
  console.log(`From overrides: ${fromOverride}`);
  console.log(`Cache synced (already had bundleId): ${synced}`);
  console.log(`Skipped (already verified): ${skipped}`);
  console.log(`Unknown: ${unknown}`);
  console.log(`Errors: ${errors}`);

  if (Object.keys(methodStats).length > 0) {
    console.log();
    console.log('Lookup method statistics:');
    for (const [method, count] of Object.entries(methodStats).sort((a, b) => b[1] - a[1])) {
      console.log(`  ${method}: ${count}`);
    }
  }

  console.log('='.repeat(60));

  // Write unknown apps to a JSON file for the workflow to pick up
  const unknownAppsFile = path.join(__dirname, '../data/unknown-apps.json');
  fs.writeFileSync(unknownAppsFile, JSON.stringify(unknownApps, null, 2) + '\n');
  console.log(`\nUnknown apps written to: ${unknownAppsFile}`);
}

processApps().catch(console.error);
