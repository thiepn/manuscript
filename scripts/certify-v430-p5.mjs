import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  { name: 'desktop-wide', viewport: { width: 1440, height: 900 }, kind: 'desktop' },
  { name: 'desktop-compact', viewport: { width: 1024, height: 768 }, kind: 'desktop' },
  { name: 'tablet-edge', viewport: { width: 768, height: 1024 }, kind: 'tablet', isMobile: true, hasTouch: true },
  { name: 'mobile-upper-boundary', viewport: { width: 767, height: 900 }, kind: 'mobile', isMobile: true, hasTouch: true },
  { name: 'mobile-portrait', viewport: { width: 390, height: 844 }, kind: 'mobile', isMobile: true, hasTouch: true },
  { name: 'mobile-standard', viewport: { width: 360, height: 800 }, kind: 'mobile', isMobile: true, hasTouch: true },
  { name: 'mobile-small', viewport: { width: 320, height: 568 }, kind: 'mobile', isMobile: true, hasTouch: true },
  { name: 'mobile-landscape', viewport: { width: 740, height: 390 }, kind: 'landscape', isMobile: true, hasTouch: true },
];

const check = (ok, message) => assert.ok(ok, message);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function visible(locator) {
  return (await locator.count()) > 0 && await locator.isVisible().catch(() => false);
}

async function rootFits(page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2);
}

async function viewport(page) {
  return page.evaluate(() => ({ width: innerWidth, height: innerHeight }));
}

async function box(locator) {
  return locator.evaluate(el => {
    const r = el.getBoundingClientRect();
    return { left:r.left, right:r.right, top:r.top, bottom:r.bottom, width:r.width, height:r.height };
  });
}

async function inViewport(page, locator, tolerance = 2) {
  const [r, v] = await Promise.all([box(locator), viewport(page)]);
  return r.left >= -tolerance && r.right <= v.width + tolerance && r.top >= -tolerance && r.bottom <= v.height + tolerance;
}

async function targetAtLeast(locator, size, message) {
  const r = await box(locator);
  check(r.width >= size && r.height >= size, `${message} ${JSON.stringify(r)}`);
  return r;
}

async function closeTransient(page) {
  const layer = page.locator('.modal-layer').first();
  if (await visible(layer)) {
    const close = layer.locator('[data-action="modal-close"],.modal-close').first();
    if (await visible(close)) await close.click({ timeout: 3000 }).catch(() => {});
    else await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(60);
  }
  const menu = page.locator('#v430-utility-menu[data-open="true"]').first();
  if (await visible(menu)) await page.keyboard.press('Escape').catch(() => {});
}

async function clickVisible(page, selector) {
  const deadline = Date.now() + 6000;
  do {
    const nodes = page.locator(selector);
    for (let i = 0; i < await nodes.count(); i += 1) {
      const node = nodes.nth(i);
      await node.scrollIntoViewIfNeeded().catch(() => {});
      if (await node.isVisible().catch(() => false)) {
        try { await node.click({ timeout: 2500 }); }
        catch { await node.evaluate(el => el.click()); }
        return node;
      }
    }
    await sleep(100);
  } while (Date.now() < deadline);
  throw new Error(`No visible element for ${selector}`);
}

async function openEditor(page) {
  await page.waitForFunction(
    () => ['landing','home','editor'].includes(document.documentElement.dataset.screen || ''),
    null,
    { timeout: 15000 },
  );
  let screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'editor') {
    await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout: 15000 });
    return;
  }
  if (screen === 'landing') {
    await closeTransient(page);
    await clickVisible(page, '[data-action="home"]');
    await page.waitForFunction(
      () => ['home','editor'].includes(document.documentElement.dataset.screen || ''),
      null,
      { timeout: 15000 },
    );
    screen = await page.locator('html').getAttribute('data-screen');
    if (screen === 'editor') {
      await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout: 15000 });
      return;
    }
  }
  check(screen === 'home', `setup: expected home/editor, got ${screen}`);
  const blank = page.locator('.modal-layer [data-action="onboarding-blank"]:visible').first();
  if (await blank.count()) {
    await blank.click({ timeout: 4000 });
  } else {
    await closeTransient(page);
    await clickVisible(page, '[data-action="new"]');
    const post = page.locator('.modal-layer [data-action="onboarding-blank"]:visible').first();
    if (await post.count()) await post.click({ timeout: 4000 });
  }
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, { timeout: 15000 });
  await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout: 15000 });
}

async function openPaletteFromMobileTrigger(page) {
  const trigger = page.locator('.v430-mobile-command-trigger:visible').first();
  check(await visible(trigger), 'mobile command trigger missing');
  await trigger.click();
  const layer = page.locator('.command-layer[data-v430-p4="true"]').first();
  await layer.waitFor({ state: 'visible', timeout: 5000 });
  return { trigger, layer };
}

async function closePalette(page) {
  await page.keyboard.press('Escape');
  await page.locator('.command-layer').first().waitFor({ state: 'detached', timeout: 5000 }).catch(() => {});
}

async function verifyContract(page, name) {
  const contract = await page.locator('meta[name="manuscript-mobile-first-contract"]').getAttribute('content');
  check(contract === 'mobile-first-interaction-v1', `${name}: P5 contract mismatch ${contract}`);
  for (const marker of [
    '#v430-p1-simplified-navigation',
    '#v430-p2-compact-density',
    '#v430-p3-focus-mode',
    '#v430-p3-runtime',
    '#v430-p4-command-palette',
    '#v430-p4-runtime',
    '#v430-p5-mobile-first',
    '#v430-p5-runtime',
  ]) check(await page.locator(marker).count() === 1, `${name}: missing or duplicated ${marker}`);
  check(await page.locator('meta[name="manuscript-mobile-first-contract"]').count() === 1, `${name}: duplicate P5 contract metadata`);
  check(await rootFits(page), `${name}: root overflow`);
}

async function verifyDesktopBoundary(page, name, tablet = false) {
  check(await page.locator('.v430-mobile-command-trigger').count() === 0, `${name}: mobile command trigger leaked at >=768px`);
  check(!(await page.locator('html').getAttribute('data-v430-mobile-panel')), `${name}: mobile panel state leaked at >=768px`);
  check(!(await page.locator('html').getAttribute('data-v430-mobile-surface')), `${name}: P5 parallel mobile-surface state leaked at >=768px`);
  const p4 = page.locator('.v430-command-trigger:visible').first();
  check(await visible(p4), `${name}: P4 command trigger disappeared`);
  if (tablet) await targetAtLeast(p4, 44, `${name}: coarse-pointer command target too small`);
  check(await rootFits(page), `${name}: >=768 boundary overflow`);
}

async function mobileNavState(page, name) {
  const nav = page.locator('.mobile-bottom-nav.v430-mobile-nav:visible').first();
  check(await visible(nav), `${name}: enhanced mobile nav missing`);
  check(await nav.getAttribute('aria-label') === 'Mobile document workflow', `${name}: mobile nav label missing`);
  const buttons = nav.locator('.mobile-nav-btn:visible');
  check(await buttons.count() === 5, `${name}: expected five mobile actions, got ${await buttons.count()}`);
  const expected = [
    '[data-mobile="write"]',
    '[data-mobile="preview"]',
    '[data-mobile="style"]',
    '[data-action="workflow-content"]',
    '[data-action="export"]',
  ];
  for (const selector of expected) check(await nav.locator(selector).count() === 1, `${name}: required action ${selector} missing`);

  const rects = await buttons.evaluateAll(nodes => nodes.map(node => {
    const r = node.getBoundingClientRect();
    return { left:r.left, right:r.right, width:r.width, height:r.height, label:(node.getAttribute('aria-label') || node.textContent || '').trim() };
  }));
  const v = await viewport(page);
  for (const r of rects) {
    check(r.width >= 50 && r.height >= 56, `${name}: mobile nav target too small ${JSON.stringify(r)}`);
    check(r.left >= -2 && r.right <= v.width + 2, `${name}: mobile nav target out of viewport ${JSON.stringify(r)}`);
    check(r.label.length > 0, `${name}: mobile nav action has no accessible name`);
  }
  const current = nav.locator('[aria-current="page"]');
  check(await current.count() === 1, `${name}: expected exactly one aria-current item, got ${await current.count()}`);
  return nav;
}

async function verifyMobileChrome(page, name) {
  const trigger = page.locator('.v430-mobile-command-trigger:visible').first();
  check(await visible(trigger), `${name}: mobile command trigger missing`);
  check(await trigger.getAttribute('aria-label') === 'Open command palette', `${name}: command trigger accessible name wrong`);
  check(await trigger.getAttribute('aria-haspopup') === 'dialog', `${name}: command trigger dialog semantics missing`);
  check(await trigger.getAttribute('aria-expanded') === 'false', `${name}: command trigger initial expanded state wrong`);
  await targetAtLeast(trigger, 44, `${name}: command trigger below 44px`);
  check(await inViewport(page, trigger), `${name}: command trigger outside viewport`);

  for (const selector of ['.appbar > [data-action="home"]:visible', '.appbar > [data-action="more"]:visible']) {
    const node = page.locator(selector).first();
    if (await visible(node)) await targetAtLeast(node, 44, `${name}: appbar target ${selector} below 44px`);
  }
  check(await page.locator('.appbar > [data-action="export"]:visible').count() === 0, `${name}: duplicate appbar export remains visible`);
  check(await page.locator('.appbar > [data-action="theme"]:visible').count() === 0, `${name}: low-frequency theme action remains in mobile appbar`);
  check(!(await page.locator('html').getAttribute('data-v430-mobile-surface')), `${name}: P5 created a parallel root mobile-surface state`);
}

async function verifyPublishRelabel(page, name, nav) {
  const publish = nav.locator('[data-action="export"]').first();
  check(await visible(publish), `${name}: Publish action not visible`);
  const text = (await publish.textContent() || '').replace(/\s+/g, ' ').trim();
  check(/publish/i.test(text), `${name}: Export visible copy was not relabeled to Publish (${text})`);
  check(await publish.getAttribute('data-action') === 'export', `${name}: Publish no longer delegates to export action`);
  check(await publish.getAttribute('aria-label') === 'Publish: export, print, or save the document', `${name}: Publish accessible name missing`);
  check(await publish.getAttribute('data-v430-publish-label') === 'true', `${name}: Publish enhancement marker missing`);
}

async function verifyModeSync(page, name, nav) {
  const write = nav.locator('[data-mobile="write"]').first();
  const preview = nav.locator('[data-mobile="preview"]').first();
  await write.click();
  await sleep(100);
  check(await write.getAttribute('aria-current') === 'page', `${name}: Write did not become current`);
  check(await nav.locator('[aria-current="page"]').count() === 1, `${name}: multiple current actions after Write`);
  check(await visible(page.locator('.editor-pane').first()), `${name}: editor pane hidden in Write`);
  check(!(await page.locator('.preview-pane').first().isVisible().catch(() => false)), `${name}: preview visible in Write`);
  check(await rootFits(page), `${name}: overflow after Write`);

  await preview.click();
  await sleep(100);
  check(await preview.getAttribute('aria-current') === 'page', `${name}: Preview did not become current`);
  check(await nav.locator('[aria-current="page"]').count() === 1, `${name}: multiple current actions after Preview`);
  check(await visible(page.locator('.preview-pane').first()), `${name}: preview pane hidden in Preview`);
  check(!(await page.locator('.editor-pane').first().isVisible().catch(() => false)), `${name}: editor visible in Preview`);
  check(await rootFits(page), `${name}: overflow after Preview`);

  await write.click();
  await sleep(80);
  check(await write.getAttribute('aria-current') === 'page', `${name}: Write state did not restore`);
}

async function verifyPanelSheet(page, name, nav) {
  const add = nav.locator('[data-action="workflow-content"]').first();
  await add.click();
  await sleep(120);
  const panel = page.locator('.left-panel:visible').first();
  check(await visible(panel), `${name}: Add did not open a mobile panel`);
  check(await page.locator('.workspace').first().evaluate(el => el.classList.contains('left-open')), `${name}: native workspace state did not open Add panel`);
  check(await add.getAttribute('aria-current') === 'page', `${name}: Add action did not become current while panel is open`);
  check(!(await page.locator('html').getAttribute('data-v430-mobile-surface')), `${name}: P5 duplicated panel state on root`);
  check(await inViewport(page, panel), `${name}: mobile panel outside viewport`);
  const back = panel.locator('.mobile-panel-back:visible').first();
  check(await visible(back), `${name}: panel back action missing`);
  await targetAtLeast(back, 44, `${name}: panel back target below 44px`);
  const backName = ((await back.getAttribute('aria-label')) || (await back.textContent()) || '').trim();
  check(backName.length > 0, `${name}: panel back action has no accessible name`);
  await back.click();
  await sleep(100);
  check(!(await panel.isVisible().catch(() => false)), `${name}: mobile panel did not close`);
  check(!(await page.locator('.workspace').first().evaluate(el => el.classList.contains('left-open'))), `${name}: native workspace panel state did not clear`);
  check(await rootFits(page), `${name}: overflow after Add panel`);
}

async function verifyStyleSheet(page, name, nav) {
  const style = nav.locator('[data-mobile="style"]').first();
  await style.click();
  await sleep(120);
  const inspector = page.locator('.inspector:visible').first();
  check(await visible(inspector), `${name}: Style did not open inspector`);
  check(await style.getAttribute('aria-current') === 'page', `${name}: Style action did not become current while inspector is open`);
  check(!(await page.locator('html').getAttribute('data-v430-mobile-surface')), `${name}: P5 duplicated inspector state on root`);
  check(await inViewport(page, inspector), `${name}: inspector outside viewport`);
  const tabs = inspector.locator('.inspector-tab:visible');
  for (let i = 0; i < await tabs.count(); i += 1) await targetAtLeast(tabs.nth(i), 44, `${name}: inspector tab ${i} below 44px`);
  const back = inspector.locator('.mobile-panel-back:visible,[data-action="toggle-inspector"]:visible,[data-action="close-panel"]:visible').first();
  if (await visible(back)) {
    await targetAtLeast(back, 44, `${name}: inspector close/back target below 44px`);
    await back.click().catch(() => {});
  } else await page.keyboard.press('Escape').catch(() => {});
  await sleep(80);
  check(await rootFits(page), `${name}: overflow after Style inspector`);
}

async function verifyCommandSheetAndFocus(page, name, nav) {
  const trigger = page.locator('.v430-mobile-command-trigger:visible').first();
  check(await trigger.getAttribute('data-action') === 'command', `${name}: command trigger no longer delegates to native command action`);
  await targetAtLeast(trigger, 44, `${name}: mobile command trigger below 44px`);

  const opened = await openPaletteFromMobileTrigger(page);
  await sleep(180);
  check(await opened.trigger.getAttribute('aria-expanded') === 'true', `${name}: mobile command trigger expanded state missing`);
  const palette = opened.layer.locator('.command-palette.v430-command-palette').first();
  check(await visible(palette), `${name}: command bottom sheet missing`);
  check(await inViewport(page, palette), `${name}: command sheet outside viewport`);
  check(!(await page.locator('html').getAttribute('data-v430-mobile-surface')), `${name}: P5 duplicated command state on root`);
  const search = opened.layer.locator('#command-search').first();
  const sr = await box(search);
  check(sr.height >= 56, `${name}: command search target too short ${JSON.stringify(sr)}`);
  check((await search.getAttribute('aria-describedby') || '').includes('v430-command-hint'), `${name}: command search helper relationship missing`);
  const fast = opened.layer.locator('.v430-command-fast').first();
  check(await visible(fast), `${name}: P4 fast actions missing in mobile sheet`);
  const fastButtons = fast.locator('.v430-command-fast-btn:visible');
  check(await fastButtons.count() === 6, `${name}: expected six P4 fast actions`);
  const fRects = await fastButtons.evaluateAll(nodes => nodes.map(node => {
    const r = node.getBoundingClientRect(); return { width:r.width, height:r.height, left:r.left, right:r.right };
  }));
  const v = await viewport(page);
  for (const r of fRects) {
    check(r.height >= 48 && r.width > 70, `${name}: fast action too small ${JSON.stringify(r)}`);
    check(r.left >= -2 && r.right <= v.width + 2, `${name}: fast action outside viewport ${JSON.stringify(r)}`);
  }
  check(await rootFits(page), `${name}: overflow with command sheet`);

  const focus = fast.locator('[data-command-action="focus-mode"]').first();
  check(await visible(focus), `${name}: Focus fast action missing`);
  check(!(await focus.isDisabled()), `${name}: Focus should be available on mobile Write after P5`);
  await focus.click();
  await opened.layer.waitFor({ state: 'detached', timeout: 5000 });
  await page.waitForFunction(() => window.__manuscriptV430P3?.active === true, null, { timeout: 5000 });
  check(await page.locator('html').getAttribute('data-v430-focus') === 'true', `${name}: mobile Focus did not activate`);
  check(!(await nav.isVisible().catch(() => false)), `${name}: bottom nav still visible in Focus`);
  check(!(await page.locator('.toolbar').first().isVisible().catch(() => false)), `${name}: toolbar still visible in Focus`);
  check(!(await page.locator('.preview-pane').first().isVisible().catch(() => false)), `${name}: preview still visible in Focus`);
  check(!(await trigger.isVisible().catch(() => false)), `${name}: mobile command trigger still visible in Focus`);
  const exit = page.locator('.v430-focus-trigger:visible').first();
  check(await visible(exit), `${name}: explicit Focus exit missing`);
  await targetAtLeast(exit, 44, `${name}: Focus exit target below 44px`);
  const exitName = ((await exit.getAttribute('aria-label')) || (await exit.textContent()) || '').trim();
  check(exitName.length > 0, `${name}: Focus exit has no accessible name`);
  const editor = page.locator('.editor-pane:visible').first();
  check(await visible(editor), `${name}: editor hidden in Focus`);
  const ed = await box(editor);
  const vv = await viewport(page);
  check(ed.width >= vv.width - 4, `${name}: focused editor does not fill viewport ${JSON.stringify({ed,vv})}`);
  check(ed.height > vv.height * 0.65, `${name}: focused editor too short ${JSON.stringify({ed,vv})}`);
  check(await rootFits(page), `${name}: overflow in mobile Focus`);

  await exit.click();
  await page.waitForFunction(() => window.__manuscriptV430P3?.active === false, null, { timeout: 5000 });
  await sleep(100);
  check(await visible(nav), `${name}: bottom nav not restored after Focus`);
  check(await visible(trigger), `${name}: command trigger not restored after Focus`);
  check(await nav.locator('[data-mobile="write"]').getAttribute('aria-current') === 'page', `${name}: Write state not restored after Focus`);

  await nav.locator('[data-mobile="preview"]').click();
  await sleep(100);
  const previewOpened = await openPaletteFromMobileTrigger(page);
  const previewFocus = previewOpened.layer.locator('.v430-command-fast [data-command-action="focus-mode"]').first();
  check(await visible(previewFocus), `${name}: Preview Focus action missing`);
  check(await previewFocus.isDisabled(), `${name}: Focus must remain unavailable in Preview-only mode`);
  await closePalette(page);
  await page.waitForFunction(
    () => document.querySelector('.v430-mobile-command-trigger')?.getAttribute('aria-expanded') === 'false',
    null,
    { timeout: 2000 },
  );
  check(await trigger.getAttribute('aria-expanded') === 'false', `${name}: command trigger expanded state leaked after close`);
  await nav.locator('[data-mobile="write"]').click();
  await sleep(80);
}

async function verifyPublishModal(page, name, nav) {
  const publish = nav.locator('[data-action="export"]').first();
  await publish.click();
  await sleep(120);
  const modal = page.locator('.modal-layer .modal:visible').first();
  check(await visible(modal), `${name}: Publish did not open export modal`);
  await sleep(180);
  check(await inViewport(page, modal), `${name}: Publish modal outside viewport`);
  const buttons = modal.locator('button:visible,[role="button"]:visible');
  for (let i = 0; i < await buttons.count(); i += 1) await targetAtLeast(buttons.nth(i), 44, `${name}: Publish modal target ${i} below 44px`);
  check(await rootFits(page), `${name}: overflow with Publish modal`);
  await closeTransient(page);
}

async function verifyMobile(page, name, landscape = false) {
  await page.waitForFunction(() => !!document.querySelector('.mobile-bottom-nav.v430-mobile-nav'), null, { timeout: 8000 });
  const nav = await mobileNavState(page, name);
  await verifyMobileChrome(page, name);
  await verifyPublishRelabel(page, name, nav);
  check(await page.locator('.v430-command-trigger').count() === 0 || !(await page.locator('.v430-command-trigger').first().isVisible().catch(() => false)), `${name}: desktop P4 command trigger leaked onto mobile`);

  await verifyModeSync(page, name, nav);
  if (!landscape) {
    await verifyPanelSheet(page, name, nav);
    await verifyStyleSheet(page, name, nav);
  }
  await verifyCommandSheetAndFocus(page, name, nav);
  await verifyPublishModal(page, name, nav);
  check(!(await page.locator('html').getAttribute('data-v430-mobile-surface')), `${name}: P5 parallel root surface state leaked at end`);
  check(await rootFits(page), `${name}: final mobile overflow`);
}

async function run(profile) {
  const browser = await chromium.launch({ headless:true });
  const context = await browser.newContext({
    viewport: profile.viewport,
    isMobile: !!profile.isMobile,
    hasTouch: !!profile.hasTouch,
    deviceScaleFactor: profile.isMobile ? 2 : 1,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(8000);
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });

  try {
    await page.goto(baseURL, { waitUntil:'load', timeout:45000 });
    await openEditor(page);
    await closeTransient(page);
    await verifyContract(page, profile.name);
    if (profile.kind === 'desktop') await verifyDesktopBoundary(page, profile.name, false);
    else if (profile.kind === 'tablet') await verifyDesktopBoundary(page, profile.name, true);
    else await verifyMobile(page, profile.name, profile.kind === 'landscape');
    check(pageErrors.length === 0, `${profile.name}: page errors ${pageErrors.join(' | ')}`);
    const serious = consoleErrors.filter(text => !/favicon|source map|deprecated/i.test(text));
    check(serious.length === 0, `${profile.name}: console errors ${serious.join(' | ')}`);
  } finally {
    await context.close();
    await browser.close();
  }
}

let passed = 0;
for (const profile of profiles) {
  process.stdout.write(`Certifying P5 ${profile.name}... `);
  try {
    await run(profile);
    passed += 1;
    console.log('PASS');
  } catch (error) {
    console.log('FAIL');
    console.error(error?.stack || error);
    process.exitCode = 1;
    break;
  }
}
if (!process.exitCode) console.log(`V430-P5 certification PASS — ${passed}/${profiles.length} profiles`);
