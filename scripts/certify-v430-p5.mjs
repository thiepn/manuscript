import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  { name: 'desktop-wide', viewport: { width: 1440, height: 900 }, kind: 'desktop' },
  { name: 'desktop-compact', viewport: { width: 1024, height: 768 }, kind: 'desktop' },
  { name: 'tablet-edge', viewport: { width: 768, height: 1024 }, kind: 'tablet', isMobile: true, hasTouch: true },
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
  ]) check(await page.locator(marker).count() === 1, `${name}: missing ${marker}`);
  check(await rootFits(page), `${name}: root overflow`);
}

async function verifyDesktopBoundary(page, name, tablet = false) {
  check(await page.locator('.v430-mobile-command-trigger').count() === 0, `${name}: mobile command trigger leaked at >=768px`);
  check(!(await page.locator('html').getAttribute('data-v430-mobile-panel')), `${name}: mobile panel state leaked at >=768px`);
  const p4 = page.locator('.v430-command-trigger:visible').first();
  check(await visible(p4), `${name}: P4 command trigger disappeared`);
  if (tablet) {
    const r = await box(p4);
    check(r.width >= 40 && r.height >= 40, `${name}: coarse-pointer command target too small ${JSON.stringify(r)}`);
  }
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
  for (const selector of expected) {
    check(await nav.locator(selector).count() === 1, `${name}: required action ${selector} missing`);
  }
  const rects = await buttons.evaluateAll(nodes => nodes.map(node => {
    const r = node.getBoundingClientRect();
    return { left:r.left, right:r.right, width:r.width, height:r.height };
  }));
  const v = await viewport(page);
  for (const r of rects) {
    check(r.width >= 50 && r.height >= 55, `${name}: mobile nav target too small ${JSON.stringify(r)}`);
    check(r.left >= -2 && r.right <= v.width + 2, `${name}: mobile nav target out of viewport ${JSON.stringify(r)}`);
  }
  const current = nav.locator('[aria-current="page"]');
  check(await current.count() === 1, `${name}: expected exactly one aria-current item, got ${await current.count()}`);
  return nav;
}

async function verifyPublishRelabel(page, name, nav) {
  const publish = nav.locator('[data-action="export"]').first();
  check(await visible(publish), `${name}: Publish action not visible`);
  const text = (await publish.textContent() || '').replace(/\s+/g, ' ').trim();
  check(/publish/i.test(text), `${name}: Export visible copy was not relabeled to Publish (${text})`);
  check(await publish.getAttribute('data-action') === 'export', `${name}: Publish no longer delegates to export action`);
  check((await publish.getAttribute('data-v430-publish-label')) !== null, `${name}: original publish label was not preserved`);
}

async function verifyModeSync(page, name, nav) {
  const write = nav.locator('[data-mobile="write"]').first();
  const preview = nav.locator('[data-mobile="preview"]').first();
  await write.click();
  await sleep(100);
  check(await write.getAttribute('aria-current') === 'page', `${name}: Write did not become current`);
  check(await visible(page.locator('.editor-pane').first()), `${name}: editor pane hidden in Write`);
  check(!(await page.locator('.preview-pane').first().isVisible().catch(() => false)), `${name}: preview visible in Write`);

  await preview.click();
  await sleep(100);
  check(await preview.getAttribute('aria-current') === 'page', `${name}: Preview did not become current`);
  check(await visible(page.locator('.preview-pane').first()), `${name}: preview pane hidden in Preview`);
  check(!(await page.locator('.editor-pane').first().isVisible().catch(() => false)), `${name}: editor visible in Preview`);

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
  check(await page.locator('html').getAttribute('data-v430-mobile-panel') === 'true', `${name}: mobile panel state not exposed`);
  check(await page.locator('body').getAttribute('data-v430-mobile-surface') === 'panel', `${name}: body mobile surface not marked panel`);
  check(await inViewport(page, panel), `${name}: mobile panel outside viewport`);
  const back = panel.locator('.mobile-panel-back:visible').first();
  check(await visible(back), `${name}: panel back action missing`);
  const br = await box(back);
  check(br.width >= 42 && br.height >= 42, `${name}: panel back target too small ${JSON.stringify(br)}`);
  await back.click();
  await sleep(100);
  check(!(await panel.isVisible().catch(() => false)), `${name}: mobile panel did not close`);
  check(await page.locator('html').getAttribute('data-v430-mobile-panel') !== 'true', `${name}: mobile panel state not cleared`);
}

async function verifyStyleSheet(page, name, nav) {
  const style = nav.locator('[data-mobile="style"]').first();
  await style.click();
  await sleep(120);
  const inspector = page.locator('.inspector:visible').first();
  check(await visible(inspector), `${name}: Style did not open inspector`);
  check(await page.locator('body').getAttribute('data-v430-mobile-surface') === 'inspector', `${name}: body mobile surface not marked inspector`);
  check(await inViewport(page, inspector), `${name}: inspector outside viewport`);
  const back = inspector.locator('.mobile-panel-back:visible,[data-action="toggle-inspector"]:visible,[data-action="close-panel"]:visible').first();
  if (await visible(back)) await back.click().catch(() => {});
  else await page.keyboard.press('Escape').catch(() => {});
  await sleep(80);
}

async function verifyCommandSheetAndFocus(page, name, nav) {
  const trigger = page.locator('.v430-mobile-command-trigger:visible').first();
  check(await visible(trigger), `${name}: mobile command trigger missing`);
  check(await trigger.getAttribute('data-action') === 'command', `${name}: command trigger no longer delegates to native command action`);
  check(await trigger.getAttribute('aria-haspopup') === 'dialog', `${name}: command trigger dialog semantics missing`);
  const tr = await box(trigger);
  check(tr.width >= 40 && tr.height >= 40, `${name}: mobile command trigger too small ${JSON.stringify(tr)}`);
  check(await inViewport(page, trigger), `${name}: command trigger outside viewport`);

  const opened = await openPaletteFromMobileTrigger(page);
  check(await opened.trigger.getAttribute('aria-expanded') === 'true', `${name}: mobile command trigger expanded state missing`);
  const palette = opened.layer.locator('.command-palette.v430-command-palette').first();
  check(await visible(palette), `${name}: command bottom sheet missing`);
  check(await inViewport(page, palette), `${name}: command sheet outside viewport`);
  check(await page.locator('body').getAttribute('data-v430-mobile-surface') === 'commands', `${name}: command surface state missing`);
  const search = opened.layer.locator('#command-search').first();
  const sr = await box(search);
  check(sr.height >= 54, `${name}: command search target too short ${JSON.stringify(sr)}`);
  const fast = opened.layer.locator('.v430-command-fast').first();
  check(await visible(fast), `${name}: P4 fast actions missing in mobile sheet`);
  const fastButtons = fast.locator('.v430-command-fast-btn:visible');
  check(await fastButtons.count() === 6, `${name}: expected six P4 fast actions`);
  const fRects = await fastButtons.evaluateAll(nodes => nodes.map(node => {
    const r = node.getBoundingClientRect(); return { width:r.width, height:r.height, left:r.left, right:r.right };
  }));
  const v = await viewport(page);
  for (const r of fRects) {
    check(r.height >= 46 && r.width > 70, `${name}: fast action too small ${JSON.stringify(r)}`);
    check(r.left >= -2 && r.right <= v.width + 2, `${name}: fast action outside viewport ${JSON.stringify(r)}`);
  }

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
  const er = await box(exit);
  check(er.width >= 90 && er.height >= 38, `${name}: Focus exit target too small ${JSON.stringify(er)}`);
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
  await nav.locator('[data-mobile="write"]').click();
  await sleep(80);
}

async function verifyPublishModal(page, name, nav) {
  const publish = nav.locator('[data-action="export"]').first();
  await publish.click();
  await sleep(120);
  const modal = page.locator('.modal-layer .modal:visible').first();
  check(await visible(modal), `${name}: Publish did not open export modal`);
  check(await inViewport(page, modal), `${name}: Publish modal outside viewport`);
  await closeTransient(page);
}

async function verifyMobile(page, name, landscape = false) {
  await page.waitForFunction(() => !!document.querySelector('.mobile-bottom-nav.v430-mobile-nav'), null, { timeout: 8000 });
  const nav = await mobileNavState(page, name);
  await verifyPublishRelabel(page, name, nav);
  check(await page.locator('.v430-command-trigger').count() === 0 || !(await page.locator('.v430-command-trigger').first().isVisible().catch(() => false)), `${name}: desktop P4 command trigger leaked onto mobile`);
  check(await page.locator('.appbar > [data-action="export"]:visible').count() === 0, `${name}: duplicate appbar export remains visible`);
  check(await page.locator('.appbar > [data-action="theme"]:visible').count() === 0, `${name}: low-frequency theme action remains in mobile appbar`);

  await verifyModeSync(page, name, nav);
  if (!landscape) {
    await verifyPanelSheet(page, name, nav);
    await verifyStyleSheet(page, name, nav);
  }
  await verifyCommandSheetAndFocus(page, name, nav);
  await verifyPublishModal(page, name, nav);
  check(await page.locator('body').getAttribute('data-v430-mobile-surface') !== 'commands', `${name}: command surface state leaked after close`);
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
