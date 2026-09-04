import { chromium, firefox, webkit } from 'playwright';
import assert from 'node:assert/strict';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  { name:'chromium-desktop-wide', browser:chromium, viewport:{width:1440,height:900}, kind:'desktop' },
  { name:'firefox-desktop', browser:firefox, viewport:{width:1366,height:768}, kind:'desktop' },
  { name:'webkit-desktop-wide', browser:webkit, viewport:{width:1440,height:900}, kind:'desktop' },
  { name:'chromium-compact-desktop', browser:chromium, viewport:{width:1024,height:768}, kind:'compact' },
  { name:'webkit-compact-desktop', browser:webkit, viewport:{width:1024,height:768}, kind:'compact' },
  { name:'chromium-tablet-edge', browser:chromium, viewport:{width:768,height:1024}, isMobile:true, hasTouch:true, kind:'tablet' },
  { name:'chromium-mobile-portrait', browser:chromium, viewport:{width:390,height:844}, isMobile:true, hasTouch:true, kind:'mobile' },
  { name:'webkit-mobile-portrait', browser:webkit, viewport:{width:390,height:844}, isMobile:true, hasTouch:true, kind:'mobile' },
  { name:'chromium-mobile-small', browser:chromium, viewport:{width:320,height:568}, isMobile:true, hasTouch:true, kind:'mobile-small' },
  { name:'chromium-mobile-landscape', browser:chromium, viewport:{width:740,height:390}, isMobile:true, hasTouch:true, kind:'mobile' },
  { name:'webkit-mobile-landscape', browser:webkit, viewport:{width:740,height:390}, isMobile:true, hasTouch:true, kind:'mobile' },
];

const themes = ['light','dark','oxford','typesetter','blueprint','ink'];
const check = (ok, message) => assert.ok(ok, message);

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
    const s = getComputedStyle(el), r = el.getBoundingClientRect();
    return s.display === 'none' || s.visibility === 'hidden' || r.width < 1 || r.height < 1;
  });
}

async function rootFits(page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
}

async function surfaceFits(page, selector, tolerance = 2) {
  return page.locator(selector).evaluate((el, t) => el.scrollWidth <= el.clientWidth + t, tolerance);
}

async function closeModalIfOpen(page) {
  const layer = page.locator('.modal-layer').first();
  if (!(await layer.count()) || !(await layer.isVisible().catch(() => false))) return;
  const close = layer.locator('[data-action="modal-close"],.modal-close').first();
  if (await close.count()) await close.click({timeout:5000});
  else await page.keyboard.press('Escape');
  await layer.waitFor({state:'detached',timeout:5000}).catch(async () => {
    await page.keyboard.press('Escape');
    await layer.waitFor({state:'detached',timeout:5000});
  });
}

async function verifyVisibleModalButtons(page, name) {
  const layer = page.locator('.modal-layer').first();
  if (!(await layer.count()) || !(await layer.isVisible().catch(() => false))) return;
  const bad = await layer.locator('.modal-foot button').evaluateAll(buttons => buttons
    .filter(b => getComputedStyle(b).display !== 'none')
    .map(b => ({text:(b.textContent || '').trim(), client:b.clientWidth, scroll:b.scrollWidth, width:b.getBoundingClientRect().width}))
    .filter(b => b.scroll > b.client + 1));
  check(bad.length === 0, `${name}: modal footer button text clipped: ${JSON.stringify(bad)}`);
  const foot = layer.locator('.modal-foot').first();
  if (await foot.count()) check(await surfaceFits(page, '.modal-layer .modal-foot'), `${name}: modal footer overflows horizontally`);
}

async function verifyOnboardingIfPresent(page, name, width) {
  const layer = page.locator('.modal-layer').first();
  if (!(await layer.count()) || !(await layer.isVisible().catch(() => false))) return;
  const blank = layer.locator('[data-action="onboarding-blank"]').first();
  if (!(await blank.count())) return;
  await verifyVisibleModalButtons(page, name);
  if (width <= 767) {
    const blankRect = await rect(page, '.modal-layer [data-action="onboarding-blank"]');
    const footRect = await rect(page, '.modal-layer .modal-foot');
    check(blankRect.width >= Math.min(220, footRect.width - 32), `${name}: onboarding primary remains squeezed ${blankRect.width}px`);
  }
}

async function openHome(page) {
  const screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'landing') {
    await closeModalIfOpen(page);
    await page.locator('[data-action="home"]').first().click({timeout:5000});
  }
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'home');
}

async function openEditor(page) {
  await openHome(page);
  const onboardingBlank = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await onboardingBlank.count() && await onboardingBlank.isVisible().catch(() => false)) {
    await onboardingBlank.click({timeout:5000});
    await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
    return;
  }
  await closeModalIfOpen(page);
  await page.locator('[data-action="new"]').first().click({timeout:5000});
  const post = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await post.count() && await post.isVisible().catch(() => false)) await post.click({timeout:5000});
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
}

async function chooseTheme(page, theme) {
  await closeModalIfOpen(page);
  await page.locator('[data-action="theme"]').first().click({timeout:5000});
  const layer = page.locator('.modal-layer');
  await layer.waitFor({state:'visible',timeout:5000});
  await layer.locator(`.theme-choice[data-theme-id="${theme}"]`).click({timeout:5000});
  await page.waitForFunction(t => document.documentElement.dataset.theme === t, theme, {timeout:5000});
  await closeModalIfOpen(page);
}

async function verifyDesktopModes(page, name) {
  for (const mode of ['editor','preview','split']) {
    await page.locator(`[data-workspace="${mode}"]`).click();
    await page.waitForTimeout(80);
    check(await rootFits(page), `${name}: root overflow in ${mode}`);
    const eHidden = await hidden(page,'.editor-pane');
    const pHidden = await hidden(page,'.preview-pane');
    if (mode === 'editor') check(!eHidden && pHidden, `${name}: Write pane exclusivity failed`);
    if (mode === 'preview') check(eHidden && !pHidden, `${name}: Preview pane exclusivity failed`);
    if (mode === 'split') {
      check(!eHidden && !pHidden, `${name}: Split panes not both visible`);
      const e = await rect(page,'.editor-pane'), p = await rect(page,'.preview-pane');
      check(e.width > 200 && p.width > 200 && e.height > 180 && p.height > 180, `${name}: Split panes unusable ${JSON.stringify({e,p})}`);
    }
  }
}

async function verifyCompactDesktop(page, name) {
  await page.locator('[data-workspace="split"]').click();
  await page.locator('[data-panel="diagnostics"]').first().click();
  await page.waitForTimeout(100);
  check((await computed(page,'.left-panel','position')).trim() === 'fixed', `${name}: left panel not overlay-fixed`);
  check(await surfaceFits(page,'.workspace'), `${name}: workspace internally overflows`);
  check(await surfaceFits(page,'.main-stage'), `${name}: main stage internally overflows`);
  check(await surfaceFits(page,'.editor-preview'), `${name}: Split layout internally overflows`);
  check(await rootFits(page), `${name}: root overflow with left panel open`);
  const viewport = await page.evaluate(() => document.documentElement.clientWidth);
  const margin = await rect(page,'[data-action="margin-guides"]');
  check(margin.right <= viewport + 1, `${name}: margin-guides offscreen ${JSON.stringify(margin)}`);
  const panel = await rect(page,'.left-panel');
  check(panel.left >= 40 && panel.right <= viewport, `${name}: left panel outside viewport ${JSON.stringify(panel)}`);
  await page.locator('[data-panel="diagnostics"]').first().click();
}

async function verifyTablet(page, name) {
  await page.locator('[data-workspace="split"]').click();
  await page.waitForTimeout(80);
  let e = await rect(page,'.editor-pane'), p = await rect(page,'.preview-pane');
  check(!(await hidden(page,'.editor-pane')) && !(await hidden(page,'.preview-pane')), `${name}: tablet Split does not expose both panes`);
  check(e.width > 500 && p.width > 500, `${name}: tablet Split panes too narrow ${JSON.stringify({e,p})}`);
  check(e.height > 250 && p.height > 250, `${name}: tablet Split panes too short ${JSON.stringify({e,p})}`);
  check(Math.abs(e.top - p.top) > 100, `${name}: tablet Split is not stacked vertically`);
  check(await rootFits(page), `${name}: tablet Split root overflow`);

  await page.locator('[data-panel="insert"]').first().click();
  await page.waitForTimeout(80);
  check((await computed(page,'.left-panel','position')).trim() === 'fixed', `${name}: tablet left panel not overlay-fixed`);
  const stage = await rect(page,'.main-stage');
  const host = await rect(page,'.native-editor-host');
  check(stage.width > 650 && stage.height > 700, `${name}: tablet main stage collapsed ${JSON.stringify(stage)}`);
  check(host.width > 500 && host.height > 200, `${name}: tablet editor host collapsed ${JSON.stringify(host)}`);
  check(await surfaceFits(page,'.workspace'), `${name}: tablet workspace internally overflows`);
  check(await rootFits(page), `${name}: tablet panel root overflow`);

  const exportBtn = page.locator('[data-action="export"]').first();
  await exportBtn.click();
  await page.waitForTimeout(80);
  await verifyVisibleModalButtons(page,name);
  const modal = await rect(page,'.modal-layer .modal');
  const viewport = await page.evaluate(() => ({w:document.documentElement.clientWidth,h:document.documentElement.clientHeight}));
  check(modal.left >= -1 && modal.right <= viewport.w + 1 && modal.top >= -1 && modal.bottom <= viewport.h + 1, `${name}: export modal outside viewport ${JSON.stringify({modal,viewport})}`);
  await closeModalIfOpen(page);
}

async function verifyMobile(page, name) {
  const nav = page.locator('.mobile-bottom-nav');
  check(await nav.count() === 1 && !(await hidden(page,'.mobile-bottom-nav')), `${name}: mobile nav unavailable`);
  check((await computed(page,'.workspace','display')).trim() === 'flex', `${name}: mobile workspace height chain not flex`);
  for (const mode of ['write','preview','write']) {
    await page.locator(`[data-mobile="${mode}"]`).click();
    await page.waitForTimeout(70);
    check(await rootFits(page), `${name}: root overflow after mobile ${mode}`);
  }
  const cm = await rect(page,'.codemirror-editor .cm-scroller');
  check(cm.width > 250 && cm.height > 70, `${name}: mobile CodeMirror unusable ${JSON.stringify(cm)}`);
}

async function certifyProfile(profile) {
  let browser, context;
  try {
    browser = await profile.browser.launch({headless:true});
    context = await browser.newContext({viewport:profile.viewport,isMobile:!!profile.isMobile,hasTouch:!!profile.hasTouch,deviceScaleFactor:profile.isMobile?2:1});
    const page = await context.newPage();
    page.setDefaultTimeout(7000);
    page.setDefaultNavigationTimeout(20000);
    const pageErrors=[], consoleErrors=[];
    page.on('pageerror', e => pageErrors.push(String(e)));
    page.on('console', m => { if (m.type()==='error') consoleErrors.push(m.text()); });

    await page.goto(baseURL,{waitUntil:'load',timeout:45000});
    await page.waitForTimeout(300);
    check(await page.title() === 'Manuscript v4.2.3 Stable', `${profile.name}: wrong title`);
    check(await page.locator('#v422-editor-layout-hotfix').count() === 1, `${profile.name}: v4.2.2 editor fix missing`);
    check(await page.locator('#v423-ui-hardening').count() === 1, `${profile.name}: v4.2.3 UI fix missing`);
    check(await page.locator('meta[name="manuscript-ui-contract"]').getAttribute('content') === 'responsive-ui-hardening-v1', `${profile.name}: UI contract mismatch`);
    check(await rootFits(page), `${profile.name}: initial root overflow`);
    await verifyOnboardingIfPresent(page,profile.name,profile.viewport.width);

    await openEditor(page);
    await page.waitForSelector('.codemirror-editor .cm-scroller',{timeout:15000});
    check(await rootFits(page), `${profile.name}: editor root overflow`);
    check((await computed(page,'html','overflow-y')).trim()==='hidden', `${profile.name}: editor root not viewport-locked`);

    if (profile.kind === 'desktop') await verifyDesktopModes(page,profile.name);
    if (profile.kind === 'compact') { await verifyDesktopModes(page,profile.name); await verifyCompactDesktop(page,profile.name); }
    if (profile.kind === 'tablet') await verifyTablet(page,profile.name);
    if (profile.kind === 'mobile' || profile.kind === 'mobile-small') await verifyMobile(page,profile.name);

    if (profile.name === 'chromium-desktop-wide') {
      for (const theme of themes) {
        await chooseTheme(page,theme);
        check(await rootFits(page), `${profile.name}: ${theme} theme root overflow`);
      }
    }

    check(pageErrors.length===0, `${profile.name}: page errors: ${pageErrors.join(' | ')}`);
    const serious=consoleErrors.filter(x=>!/favicon|source map|deprecated/i.test(x));
    check(serious.length===0, `${profile.name}: console errors: ${serious.join(' | ')}`);
    return {profile:profile.name,passed:true};
  } finally {
    if (context) await context.close().catch(()=>{});
    if (browser) await browser.close().catch(()=>{});
  }
}

const results=[];
for (const profile of profiles) {
  process.stdout.write(`Certifying ${profile.name}... `);
  try { results.push(await certifyProfile(profile)); console.log('PASS'); }
  catch (error) { console.log('FAIL'); console.error(error?.stack||error); process.exitCode=1; break; }
}
if (!process.exitCode) console.log(`v4.2.3 responsive UI certification PASS — ${results.length}/${profiles.length} profiles`);
