import { chromium, firefox, webkit } from 'playwright';
import assert from 'node:assert/strict';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/Manuscript_v4.2.1_Stable.html';
const expectedHash = '6d3900a2c973dc2d36099fc596b77b21268c11fdc1cff46bba7e66f08d83aba6';
const themes = ['light','dark','oxford','typesetter','blueprint','ink'];
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

async function rootFits(page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
}

async function openHome(page) {
  const screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'landing') {
    await page.locator('[data-action="home"]').first().click();
  }
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'home');
}

async function closeModalIfOpen(page) {
  const layer = page.locator('.modal-layer');
  if (!(await layer.count())) return;
  if (!(await layer.first().isVisible().catch(() => false))) return;
  const close = layer.first().locator('[data-action="modal-close"],.modal-close').first();
  if (await close.count()) {
    await close.click({ timeout: 5000 });
  } else {
    await page.keyboard.press('Escape');
  }
  await layer.waitFor({ state: 'detached', timeout: 5000 }).catch(async () => {
    await page.keyboard.press('Escape');
    await layer.waitFor({ state: 'detached', timeout: 5000 });
  });
}

async function chooseTheme(page, theme) {
  await closeModalIfOpen(page);
  await page.locator('[data-action="theme"]').first().click({ timeout: 5000 });
  const layer = page.locator('.modal-layer');
  await layer.waitFor({ state: 'visible', timeout: 5000 });
  await layer.locator(`.theme-choice[data-theme-id="${theme}"]`).click({ timeout: 5000 });
  await page.waitForFunction(t => document.documentElement.dataset.theme === t, theme, { timeout: 5000 });
  await closeModalIfOpen(page);
}

async function openEditor(page) {
  await openHome(page);

  const onboardingBlank = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await onboardingBlank.count() && await onboardingBlank.isVisible().catch(() => false)) {
    await onboardingBlank.click({ timeout: 5000 });
    await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
    return;
  }

  await closeModalIfOpen(page);
  await page.locator('[data-action="new"]').first().click({ timeout: 5000 });

  const postNewOnboarding = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await postNewOnboarding.count() && await postNewOnboarding.isVisible().catch(() => false)) {
    await postNewOnboarding.click({ timeout: 5000 });
  }
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
}

async function certifyProfile(profile) {
  let browser = null;
  let context = null;
  try {
    browser = await profile.browser.launch({headless:true});
    context = await browser.newContext({
      viewport: profile.viewport,
      isMobile: !!profile.isMobile,
      hasTouch: !!profile.hasTouch,
      deviceScaleFactor: profile.isMobile ? 2 : 1,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(7000);
    page.setDefaultNavigationTimeout(20000);
    const pageErrors = [];
    const consoleErrors = [];
    page.on('pageerror', err => pageErrors.push(String(err)));
    page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

    await page.goto(baseURL, {waitUntil:'load', timeout:45000});
    await page.waitForTimeout(400);

    check(await page.title() === 'Manuscript v4.2.1 Stable', `${profile.name}: wrong title`);
    const contracts = await page.evaluate(() => Object.fromEntries([
      'release','stable','certification','scroll','mobile','theme','visual'
    ].map(k => [k, document.querySelector(`meta[name="manuscript-${k === 'release' ? 'release-channel' : k === 'stable' ? 'stable-contract' : k === 'certification' ? 'certification-contract' : k === 'scroll' ? 'scroll-contract' : k === 'mobile' ? 'mobile-viewport-contract' : k === 'theme' ? 'theme-contract' : 'visual-contract'}"]`)?.content || ''])));
    check(contracts.release === 'stable', `${profile.name}: release channel`);
    check(contracts.stable === 'production-stable-v1', `${profile.name}: stable contract`);
    check(contracts.scroll === 'screen-scoped-scroll-ownership-v2', `${profile.name}: scroll contract`);
    check(contracts.mobile === 'dvh-keyboard-safe-v3', `${profile.name}: mobile viewport contract`);
    check(contracts.theme === 'curated-interface-themes-v2', `${profile.name}: theme contract`);
    check(contracts.visual === 'editorial-interface-v1.1', `${profile.name}: visual contract`);
    check(await rootFits(page), `${profile.name}: initial horizontal overflow`);

    await openHome(page);
    check(await rootFits(page), `${profile.name}: home horizontal overflow`);
    const bodyOverflowY = await computed(page, 'body', 'overflow-y');
    check(bodyOverflowY !== 'hidden', `${profile.name}: home body unexpectedly locked`);

    for (const theme of themes) {
      await chooseTheme(page, theme);
      check(await page.locator('html').getAttribute('data-theme') === theme, `${profile.name}: theme ${theme} not applied`);
      const paper = (await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--paper'))).trim().toLowerCase();
      check(['#fffefa','rgb(255, 254, 250)'].includes(paper), `${profile.name}: theme ${theme} changed paper (${paper})`);
      check(await rootFits(page), `${profile.name}: ${theme} horizontal overflow`);
    }

    await chooseTheme(page, 'oxford');
    await page.reload({waitUntil:'load'});
    await page.waitForTimeout(250);
    check(await page.locator('html').getAttribute('data-theme') === 'oxford', `${profile.name}: theme persistence failed`);

    await openEditor(page);
    check(await rootFits(page), `${profile.name}: editor horizontal root overflow`);
    const rootOverflow = await computed(page, 'html', 'overflow-y');
    const bodyOverflow = await computed(page, 'body', 'overflow-y');
    check(rootOverflow === 'hidden' && bodyOverflow === 'hidden', `${profile.name}: editor viewport not locked`);

    const preview = page.locator('.preview-scroll');
    check(await preview.count() > 0, `${profile.name}: preview scroller missing`);
    const previewOverflow = await computed(page, '.preview-scroll', 'overflow-y');
    check(['auto','scroll'].includes(previewOverflow), `${profile.name}: preview is not a scroll owner (${previewOverflow})`);

    const cm = page.locator('.codemirror-editor .cm-scroller');
    check(await cm.count() > 0, `${profile.name}: CodeMirror scroller missing`);
    const cmOverflow = await computed(page, '.codemirror-editor .cm-scroller', 'overflow-y');
    check(['auto','scroll'].includes(cmOverflow), `${profile.name}: CodeMirror not scrollable (${cmOverflow})`);

    if (profile.viewport.width >= 768) {
      const appbarH = Math.round(await page.locator('.appbar').evaluate(el => el.getBoundingClientRect().height));
      const toolbarH = Math.round(await page.locator('.toolbar').evaluate(el => el.getBoundingClientRect().height));
      check(appbarH === 48, `${profile.name}: appbar height ${appbarH}`);
      check(toolbarH === 42, `${profile.name}: toolbar height ${toolbarH}`);
    } else {
      const mobileNav = page.locator('.mobile-bottom-nav');
      check(await mobileNav.count() > 0, `${profile.name}: mobile nav missing`);
      const navDisplay = await computed(page, '.mobile-bottom-nav', 'display');
      check(navDisplay !== 'none', `${profile.name}: mobile nav hidden`);
    }

    await page.locator('[data-action="theme"]').first().click({ timeout: 5000 });
    const modalBody = page.locator('.modal-body');
    check(await modalBody.count() > 0, `${profile.name}: theme modal missing`);
    const modalOverflow = await computed(page, '.modal-body', 'overflow-y');
    check(['auto','scroll'].includes(modalOverflow), `${profile.name}: modal body not scroll owner (${modalOverflow})`);
    check(await rootFits(page), `${profile.name}: modal caused horizontal root overflow`);

    check(pageErrors.length === 0, `${profile.name}: page errors: ${pageErrors.join(' | ')}`);
    const seriousConsole = consoleErrors.filter(x => !/favicon|source map|deprecated/i.test(x));
    check(seriousConsole.length === 0, `${profile.name}: console errors: ${seriousConsole.join(' | ')}`);

    return {profile:profile.name, passed:true};
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

if (!process.exitCode) {
  console.log(`Browser certification PASS — ${results.length}/${profiles.length} profiles`);
  console.log(`Expected Stable SHA-256: ${expectedHash}`);
}