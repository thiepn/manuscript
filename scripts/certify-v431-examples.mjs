import fs from 'node:fs/promises';
import process from 'node:process';

const html = await fs.readFile('index.html', 'utf8');
const sw = await fs.readFile('sw.js', 'utf8');
const digest = (await fs.readFile('V431_SHA256.txt', 'utf8')).trim();
const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };
const countText = (text, needle) => text.split(needle).length - 1;

const examples = [
  ['markdown-basics', 'Markdown Basics', ['# Markdown Basics', '**bold**', '[Markdown Guide]', '~~strikethrough~~']],
  ['markdown-lists-tables', 'Lists, Tasks & Tables', ['# Lists, Tasks & Tables', '- [x] Learn headings', '| Feature | Markdown | Purpose |']],
  ['markdown-code-math-footnotes', 'Code, Math & Footnotes', ['# Code, Math & Footnotes', '```python', '[^first]:', '$$']],
  ['manuscript-publishing-extras', 'Manuscript Publishing Extras', ['# Manuscript Publishing Extras', '[[titlepage]]', '[[toc]]', '{#sec-frontmatter}', '::: note', '<!-- manuscript:pagebreak -->']],
];

check(html.includes('<title>Manuscript v4.3.1 Stable</title>'), 'v4.3.1 title missing');
check(html.includes("exports.APP_VERSION = '4.3.1';"), 'APP_VERSION is not 4.3.1');
check(html.includes("exports.RELEASE_NAME = 'Manuscript v4.3.1 Stable';"), 'RELEASE_NAME is not v4.3.1 Stable');
check(html.includes("exports.RELEASE_PHASE = 'V431 — Markdown Learning Examples';"), 'V431 release phase missing');
check(html.includes('manuscript-learning-contract" content="markdown-examples-v1'), 'learning contract missing');
check(html.includes('New to Markdown?'), 'Template Gallery learning hint missing');
check(sw.includes('`${CACHE_PREFIX}v4.3.1`'), 'service-worker cache not bumped to v4.3.1');
check(/^[a-f0-9]{64}$/.test(digest), 'V431_SHA256.txt is invalid');

for (const [id, name, tokens] of examples) {
  const idMatches = html.match(new RegExp(`id: ["']${id}["']`, 'g')) || [];
  check(idMatches.length === 1, `${id}: expected exactly one template id, found ${idMatches.length}`);
  check(html.includes(`name: "${name}"`) || html.includes(`name: '${name}'`), `${id}: name missing`);
  check(html.includes('category: "Learn Markdown"') || html.includes("category: 'Learn Markdown'"), `${id}: Learn Markdown category missing`);
  for (const token of tokens) check(html.includes(token), `${id}: missing teaching token ${token}`);
}

if (failures.length) {
  console.error(`V431 static certification failed (${failures.length}):`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log('V431 static certification: PASS');

if (process.env.MANUSCRIPT_URL) {
  const { chromium } = await import('playwright');
  const browser = await chromium.launch({ headless: true });
  try {
    const expected = {
      'markdown-basics': ['Markdown Basics', 'Heading level 2', 'strikethrough'],
      'markdown-lists-tables': ['Lists, Tasks & Tables', 'Practice tables', 'Monday'],
      'markdown-code-math-footnotes': ['Code, Math & Footnotes', 'average(values)', 'first footnote'],
      'manuscript-publishing-extras': ['Manuscript Publishing Extras', 'A useful note', 'What to remember'],
    };

    async function openGallery(page) {
      await page.goto(process.env.MANUSCRIPT_URL, { waitUntil: 'load' });
      const trigger = page.locator('[data-action="templates"]:visible').first();
      await trigger.click();
      await page.locator('.modal').waitFor({ state: 'visible' });
    }

    {
      const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      await openGallery(page);
      check((await page.title()) === 'Manuscript v4.3.1 Stable', 'browser: wrong page title');
      check((await page.locator('.modal').innerText()).includes('New to Markdown?'), 'browser: learning hint not visible');
      for (const id of Object.keys(expected)) check(await page.locator(`[data-action="use-template"][data-id="${id}"]`).count() === 1, `browser: ${id} card missing`);
      check(errors.length === 0, `browser: page errors in gallery: ${errors.join(' | ')}`);
      await context.close();
    }

    for (const [id, tokens] of Object.entries(expected)) {
      const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      await openGallery(page);
      await page.locator(`[data-action="use-template"][data-id="${id}"]`).click();
      await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor');
      await page.waitForTimeout(350);
      const source = await page.locator('.cm-content').innerText().catch(() => '');
      const preview = await page.locator('#flow-document').innerText().catch(() => '');
      for (const token of tokens) check(source.includes(token) || preview.includes(token), `browser: ${id} did not expose ${token}`);
      if (id === 'markdown-lists-tables') {
        check(await page.locator('#flow-document table').count() >= 2, 'browser: list/table example did not render two tables');
        check(await page.locator('#flow-document input[type="checkbox"]').count() >= 4, 'browser: task list checkboxes missing');
      }
      if (id === 'markdown-code-math-footnotes') {
        check(await page.locator('#flow-document pre').count() >= 2, 'browser: fenced code blocks missing');
        check(await page.locator('#flow-document .footnotes').count() >= 1, 'browser: footnotes missing');
        check(await page.locator('#flow-document .math-display').count() >= 2, 'browser: display math missing');
      }
      if (id === 'manuscript-publishing-extras') {
        check(source.includes('{#sec-frontmatter}'), 'browser: heading-label syntax missing from source');
        check(!preview.includes('{#sec-frontmatter}'), 'browser: heading-label syntax leaked as literal preview text');
        check(!preview.includes('[[toc]]'), 'browser: TOC directive leaked as literal preview text');
        check(countText(preview, 'Front matter') >= 2, 'browser: generated TOC did not include Front matter');
        check(countText(preview, 'Generated elements') >= 2, 'browser: generated TOC did not include Generated elements');
        check(await page.locator('#flow-document .callout').count() >= 2, 'browser: callouts missing');
      }
      check(errors.length === 0, `browser: ${id} page errors: ${errors.join(' | ')}`);
      await context.close();
    }
  } finally {
    await browser.close();
  }

  if (failures.length) {
    console.error(`V431 browser certification failed (${failures.length}):`);
    for (const failure of failures) console.error(`- ${failure}`);
    process.exit(1);
  }
  console.log('V431 browser certification: PASS');
}
