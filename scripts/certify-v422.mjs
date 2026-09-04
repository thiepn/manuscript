import { chromium, firefox, webkit } from 'playwright';
import assert from 'node:assert/strict';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  { name:'chromium-desktop', browser:chromium, viewport:{width:1440,height:900} },
  { name:'firefox-desktop', browser:firefox, viewport:{width:1366,height:768} },
  { name:'webkit-desktop', browser:webkit, viewport:{width:1440,height:900} },
  { name:'chromium-mobile-portrait', browser:chromium, viewport:{width:390,height:844}, isMobile:true, hasTouch:true },
  { name:'webkit-mobile-portrait', browser:webkit, viewport:{width:390,height:844}, isMobile:true, hasTouch:true },
  { name:'chromium-mobile-landscape', browser:chromium, viewport:{width:740,height:390}, isMobile:true, hasTouch:true },
  { name:'webkit-mobile-landscape', browser:webkit, viewport:{width:740,height:390}, isMobile:true, hasTouch:true },
];

function check(ok, message) { assert.ok(ok, message); }

async function computed(page, selector, property) {
  return page.locator(selector).evaluate((el, prop) => getComputedStyle(el).getPropertyValue(prop), property);
}

async function rect(page, selector) {
  return page.locator(selector).evaluate(el => {
    const r = el.getBoundingClientRect();
    return { width:r.width, height:r.height, top:r.top, bottom:r.bottom, left:r.left, right:r.right };
  });
}

async function hidden(page, selector) {
  return page.locator(selector).evaluate(el => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return s.display === 'none' || s.visibility === 'hidden' || r.width < 1 || r.height < 1;
  });
}

async function rootFits(page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
}

async function closeModalIfOpen(page) {
  const layer = page.locator('.modal-layer').first();
  if (!(await layer.count()) || !(await layer.isVisible().catch(() => false))) return;
  const close = layer.locator('[data-action="modal-close"],.modal-close').first();
  if (await close.count()) await close.click({ timeout:5000 });
  else await page.keyboard.press('Escape');
  await layer.waitFor({ state:'detached', timeout:5000 }).catch(async () => {
    await page.keyboard.press('Escape');
    await layer.waitFor({ state:'detached', timeout:5000 });
  });
}

async function openHome(page) {
  const screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'landing') await page.locator('[data-action="home"]').first().click();
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'home');
}

async function openEditor(page) {
  await openHome(page);
  const onboardingBlank = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await onboardingBlank.count() && await onboardingBlank.isVisible().catch(() => false)) {
    await onboardingBlank.click({ timeout:5000 });
    await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, { timeout:15000 });
    return;
  }
  await closeModalIfOpen(page);
  await page.locator('[data-action="new"]').first().click({ timeout:5000 });
  const postNewOnboarding = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await postNewOnboarding.count() && await postNewOnboarding.isVisible().catch(() => false)) {
    await postNewOnboarding.click({ timeout:5000 });
  }
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, { timeout:15000 });
}

async function verifyDesktopModes(page, name) {
  const editorButton = page.locator('[data-workspace="editor"]');
  const splitButton = page.locator('[data-workspace="split"]');
  const previewButton = page.locator('[data-workspace="preview"]');
  check(await editorButton.count() === 1 && await splitButton.count() === 1 && await previewButton.count() === 1,
    `${name}: workspace mode controls missing`);

  await editorButton.click();
  await page.waitForFunction(() => document.querySelector('.editor-preview')?.classList.contains('editor-only'));
  let e = await rect(page, '.editor-pane');
  check(e.width > 250 && e.height > 180, `${name}: Write editor unusable ${JSON.stringify(e)}`);
  check(await hidden(page, '.preview-pane'), `${name}: Write still renders preview pane`);
  let cm = await rect(page, '.codemirror-editor .cm-scroller');
  check(cm.height > 100, `${name}: Write CodeMirror height collapsed ${cm.height}`);

  await previewButton.click();
  await page.waitForFunction(() => document.querySelector('.editor-preview')?.classList.contains('preview-only'));
  let p = await rect(page, '.preview-pane');
  check(p.width > 250 && p.height > 180, `${name}: Preview pane unusable ${JSON.stringify(p)}`);
  check(await hidden(page, '.editor-pane'), `${name}: Preview still renders editor pane`);
  let ps = await rect(page, '.preview-scroll');
  check(ps.height > 100, `${name}: Preview scroll height collapsed ${ps.height}`);

  await splitButton.click();
  await page.waitForFunction(() => {
    const el = document.querySelector('.editor-preview');
    return el && !el.classList.contains('editor-only') && !el.classList.contains('preview-only');
  });
  e = await rect(page, '.editor-pane');
  p = await rect(page, '.preview-pane');
  check(e.width > 200 && e.height > 180, `${name}: Split editor unusable ${JSON.stringify(e)}`);
  check(p.width > 200 && p.height > 180, `${name}: Split preview unusable ${JSON.stringify(p)}`);
  check(!(await hidden(page, '.splitter')), `${name}: Splitter missing in Split mode`);
}

async function verifyMobileModes(page, name) {
  const nav = page.locator('.mobile-bottom-nav');
  check(await nav.count() === 1 && !(await hidden(page, '.mobile-bottom-nav')), `${name}: mobile nav unavailable`);

  const workspaceDisplay = (await computed(page, '.workspace', 'display')).trim();
  check(workspaceDisplay === 'flex', `${name}: mobile workspace height chain is ${workspaceDisplay}, expected flex`);
  let stage = await rect(page, '.main-stage');
  check(stage.height > 120, `${name}: main stage collapsed ${stage.height}`);

  await page.locator('[data-mobile="write"]').click();
  await page.waitForFunction(() => document.querySelector('[data-mobile="write"]')?.classList.contains('active'));
  let e = await rect(page, '.editor-pane');
  check(e.width > 250 && e.height > 100, `${name}: mobile Write pane unusable ${JSON.stringify(e)}`);
  check(await hidden(page, '.preview-pane'), `${name}: mobile Write still renders preview`);
  let host = await rect(page, '.native-editor-host');
  let cm = await rect(page, '.codemirror-editor .cm-scroller');
  check(host.height > 80, `${name}: native editor host collapsed ${host.height}`);
  check(cm.height > 70, `${name}: CodeMirror collapsed ${cm.height}`);

  await page.locator('[data-mobile="preview"]').click();
  await page.waitForFunction(() => document.querySelector('[data-mobile="preview"]')?.classList.contains('active'));
  check(await hidden(page, '.editor-pane'), `${name}: mobile Preview still renders editor`);
  let p = await rect(page, '.preview-pane');
  let ps = await rect(page, '.preview-scroll');
  check(p.width > 250 && p.height > 100, `${name}: mobile Preview pane unusable ${JSON.stringify(p)}`);
  check(ps.height > 70, `${name}: mobile Preview scroll collapsed ${ps.height}`);

  await page.locator('[data-mobile="write"]').click();
  await page.waitForFunction(() => document.querySelector('[data-mobile="write"]')?.classList.contains('active'));
  cm = await rect(page, '.codemirror-editor .cm-scroller');
  check(cm.height > 70, `${name}: editor failed after Preview -> Write switch ${cm.height}`);
  check(await rootFits(page), `${name}: mobile mode switching caused horizontal overflow`);
}

async function certifyProfile(profile) {
  let browser;
  let context;
  try {
    browser = await profile.browser.launch({ headless:true });
    context = await browser.newContext({
      viewport:profile.viewport,
      isMobile:!!profile.isMobile,
      hasTouch:!!profile.hasTouch,
      deviceScaleFactor:profile.isMobile ? 2 : 1,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(7000);
    page.setDefaultNavigationTimeout(20000);

    const pageErrors = [];
    const consoleErrors = [];
    page.on('pageerror', err => pageErrors.push(String(err)));
    page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

    await page.goto(baseURL, { waitUntil:'load', timeout:45000 });
    await page.waitForTimeout(300);
    check(await page.title() === 'Manuscript v4.2.2 Stable', `${profile.name}: wrong title`);
    check(await page.locator('#v422-editor-layout-hotfix').count() === 1, `${profile.name}: v4.2.2 hotfix style missing`);
    const contract = await page.locator('meta[name="manuscript-editor-layout-contract"]').getAttribute('content');
    check(contract === 'exclusive-workspace-panes+mobile-flex-height-v1', `${profile.name}: hotfix contract mismatch`);
    check(await rootFits(page), `${profile.name}: initial horizontal overflow`);

    await openEditor(page);
    await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout:15000 });
    check(await rootFits(page), `${profile.name}: editor horizontal overflow`);
    check((await computed(page, 'html', 'overflow-y')).trim() === 'hidden', `${profile.name}: editor root not locked`);
    check((await computed(page, 'body', 'overflow-y')).trim() === 'hidden', `${profile.name}: editor body not locked`);

    if (profile.viewport.width >= 768) await verifyDesktopModes(page, profile.name);
    else await verifyMobileModes(page, profile.name);

    check(pageErrors.length === 0, `${profile.name}: page errors: ${pageErrors.join(' | ')}`);
    const seriousConsole = consoleErrors.filter(x => !/favicon|source map|deprecated/i.test(x));
    check(seriousConsole.length === 0, `${profile.name}: console errors: ${seriousConsole.join(' | ')}`);
    return { profile:profile.name, passed:true };
  } finally {
    if (context) await context.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
  }
}

const results = [];
for (const profile of profiles) {
  process.stdout.write(`Certifying ${profile.name}... `);
  try {
    results.push(await certifyProfile(profile));
    console.log('PASS');
  } catch (error) {
    console.log('FAIL');
    console.error(error?.stack || error);
    process.exitCode = 1;
    break;
  }
}

if (!process.exitCode) console.log(`v4.2.2 editor/mobile certification PASS — ${results.length}/${profiles.length} profiles`);
