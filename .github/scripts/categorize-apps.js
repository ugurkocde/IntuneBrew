const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const CATEGORIES = [
  'Productivity',
  'Developer Tools',
  'Communication',
  'Browsers',
  'Utilities',
  'Media',
  'Design',
  'Security',
  'Other'
];

async function getAppInfo(appData, needsCategory, needsPublisher) {
  // Build prompt based on what we need
  let requestParts = [];
  if (needsCategory) {
    requestParts.push(`CATEGORY: Categorize into exactly ONE of: ${CATEGORIES.join(', ')}`);
  }
  if (needsPublisher) {
    requestParts.push(`PUBLISHER: The company or developer who publishes this app (e.g., "Microsoft Corporation", "Adobe Inc.", "Slack Technologies")`);
  }

  const prompt = `For this macOS application:

App Name: ${appData.name}
Description: ${appData.description || 'N/A'}
Homepage: ${appData.homepage || 'N/A'}

Provide the following:
${requestParts.join('\n')}

Respond in this exact format (only include lines for what was requested):
${needsCategory ? 'CATEGORY: <category name>' : ''}
${needsPublisher ? 'PUBLISHER: <publisher name>' : ''}`.trim();

  const response = await openai.chat.completions.create({
    model: 'gpt-5-nano',
    messages: [{ role: 'user', content: prompt }]
  });

  const content = response.choices[0].message.content.trim();

  // Parse response
  let category = null;
  let publisher = null;

  const categoryMatch = content.match(/CATEGORY:\s*(.+)/i);
  if (categoryMatch) {
    const cat = categoryMatch[1].trim();
    category = CATEGORIES.includes(cat) ? cat : 'Other';
  }

  const publisherMatch = content.match(/PUBLISHER:\s*(.+)/i);
  if (publisherMatch) {
    publisher = publisherMatch[1].trim();
  }

  return { category, publisher };
}

function hasValidValue(value) {
  return value && typeof value === 'string' && value.trim() !== '';
}

async function processApps() {
  const appsDir = path.join(__dirname, '../../Apps');
  const recategorizeAll = process.env.RECATEGORIZE_ALL === 'true';

  // Get all JSON files
  const files = fs.readdirSync(appsDir).filter(f => f.endsWith('.json'));

  console.log(`Found ${files.length} app JSON files`);
  console.log(`Recategorize all: ${recategorizeAll}\n`);

  let updated = 0;
  let skipped = 0;
  let errors = 0;

  for (const file of files) {
    const filePath = path.join(appsDir, file);

    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const appData = JSON.parse(content);

      const hasCategory = hasValidValue(appData.category);
      const hasPublisher = hasValidValue(appData.publisher);

      // Determine what we need to fetch
      let needsCategory = !hasCategory || recategorizeAll;
      let needsPublisher = !hasPublisher || recategorizeAll;

      // Skip if both already exist (unless recategorize_all is true)
      if (!needsCategory && !needsPublisher) {
        skipped++;
        continue;
      }

      // Log what we're doing
      const actions = [];
      if (needsCategory) actions.push('category');
      if (needsPublisher) actions.push('publisher');

      console.log(`[${updated + skipped + errors + 1}/${files.length}] ${appData.name || file} - fetching: ${actions.join(', ')}`);

      const { category, publisher } = await getAppInfo(appData, needsCategory, needsPublisher);

      // Update fields
      let changed = false;
      if (needsCategory && category) {
        appData.category = category;
        changed = true;
      }
      if (needsPublisher && publisher) {
        appData.publisher = publisher;
        changed = true;
      }

      if (changed) {
        fs.writeFileSync(filePath, JSON.stringify(appData, null, 2) + '\n');
        console.log(`  -> category: ${appData.category || '(unchanged)'}, publisher: ${appData.publisher || '(unchanged)'}`);
        updated++;
      } else {
        skipped++;
      }

      // Small delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 50));
    } catch (error) {
      console.error(`Error processing ${file}:`, error.message);
      errors++;
    }
  }

  console.log(`\n========================================`);
  console.log(`Done!`);
  console.log(`  Updated: ${updated}`);
  console.log(`  Skipped (already complete): ${skipped}`);
  console.log(`  Errors: ${errors}`);
  console.log(`========================================`);
}

processApps().catch(console.error);
