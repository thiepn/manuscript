import { chromium } from 'playwright';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  { name: 'desktop-wide', viewport: { width: 1440, height: 900 }, trigger: true, wide: true },
  { name: 'desktop-compact', viewport: { width: 1024, height: 768 }, trigger: true },
  { name: 'tablet-edge', viewport: { width: 768, height: 1024 }, trigger: true, isMobile: true, hasTouch: true },
  { name: 'mobile-portrait', viewport: { width: 390, height: 844 }, trigger: false, isMobile: true, hasTouch: true },
  { name: 'mobile-landscape', viewport: { width: 740, height: 390 }, trigger: false, isMobile: true, hasTouch: true },
];

function check(condition, message) {
  if (!condition) throw new Error(message);
}

async function visible(locator) {
  return (await locator.count()) > 0 && await locator.isVisible().catch(() => false);
}

async function rootFits(page) {
  return page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth <= 2);
}

async function closeModal(page) {
  const layer = page.locator('.modal-layer').first();
  if (!(await visible(layer))) return;
  const close = layer.locator('[data-action="modal-close"],.modal-close').first();
  if (await visible(close)) await close.click({ timeout: 3000 }).catch(() => {});
  else await page.keyboard.press('Escape').catch(() => {});
}

async function settleBoot(page) {
  await page.waitForFunction(
    () => ['landing', 'home', 'editor'].includes(document.documentElement.dataset.screen || ''),
    null,
    { timeout: 15000 },
  );
}

async function openEditor(page) {
  await settleBoot(page);
  let screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'editor') {
    await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout: 15000 });
    return;
  }
  if (screen === 'landing') {
    await closeModal(page);
    const home = page.locator('[data-action="home"]:visible').first();
    if (await home.count()) await home.click({ timeout: 5000 });
    await page.waitForFunction(
      () => ['home', 'editor'].includes(document.documentElement.dataset.screen || ''),
      null,
      { timeout: 12000 },
    );
    screen = await page.locator('html').getAttribute('data-screen');
    if (screen === 'editor') {
      await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout: 15000 });
      return;
    }
  }
  await closeModal(page);
  let blank = page.locator('.modal-layer [data-action="onboarding-blank"]:visible').first();
  if (await blank.count()) {
    await blank.click({ timeout: 5000 });
  } else {
    const fresh = page.locator('[data-action="new"]:visible').first();
    check(await fresh.count() === 1, 'Unable to locate New action');
    await fresh.click({ timeout: 5000 });
    blank = page.locator('.modal-layer [data-action="onboarding-blank"]:visible').first();
    if (await blank.count()) await blank.click({ timeout: 5000 });
  }
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, { timeout: 15000 });
  await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout: 15000 });
}

async function openPaletteByShortcut(page) {
  await page.keyboard.press('Control+k');
  await page.waitForSelector('.command-layer .command-palette', { state: 'visible', timeout: 5000 });
  await page.waitForSelector('.command-layer[data-v430-p4="true"] .v430-command-fast', { state: 'visible', timeout: 5000 });
}

async function closePalette(page) {
  await page.keyboard.press('Escape');
  await page.waitForSelector('.command-layer', { state: 'detached', timeout: 5000 });
}

async function certifyDesktop(page, profile) {
  await page.waitForFunction(() => !!document.querySelector('.v430-command-trigger'), null, { timeout: 8000 });
  const trigger = page.locator('.v430-command-trigger').first();
  check(await visible(trigger), `${profile.name}: P4 command trigger not visible`);
  check(await trigger.getAttribute('data-action') === 'command', `${profile.name}: trigger does not delegate to native command action`);
  check(await trigger.getAttribute('aria-haspopup') === 'dialog', `${profile.name}: trigger dialog semantics missing`);

  const oldTrigger = page.locator('.appbar > [data-action="command"]:not(.v430-command-trigger)').first();
  if (await oldTrigger.count()) check(!(await oldTrigger.isVisible()), `${profile.name}: legacy command trigger remains visible`);

  const triggerRect = await trigger.boundingBox();
  check(triggerRect, `${profile.name}: command trigger geometry missing`);
  if (profile.wide) {
    check(triggerRect.width >= 120 && triggerRect.width <= 180, `${profile.name}: wide command trigger width unexpected (${triggerRect.width})`);
    check(await visible(trigger.locator('.v430-command-label')), `${profile.name}: wide command label hidden`);
    check(await visible(trigger.locator('.v430-command-shortcut')), `${profile.name}: wide command shortcut hidden`);
  } else {
    check(triggerRect.width >= 34 && triggerRect.width <= 50, `${profile.name}: compact command trigger width unexpected (${triggerRect.width})`);
    check(!(await trigger.locator('.v430-command-label').isVisible().catch(() => false)), `${profile.name}: compact command label should collapse`);
  }
  check(await rootFits(page), `${profile.name}: overflow before palette open`);

  await trigger.focus();
  await trigger.click();
  await page.waitForSelector('.command-layer[data-v430-p4="true"] .v430-command-fast', { state: 'visible', timeout: 5000 });
  check(await trigger.getAttribute('aria-expanded') === 'true', `${profile.name}: trigger expanded state not synchronized`);

  const layer = page.locator('.command-layer').first();
  const palette = layer.locator('.command-palette').first();
  const input = layer.locator('#command-search').first();
  const quick = layer.locator('.v430-command-fast').first();
  const hint = layer.locator('#v430-command-hint').first();
  check(await visible(palette), `${profile.name}: command palette missing`);
  check(await visible(quick), `${profile.name}: quick actions missing`);
  check(await visible(hint), `${profile.name}: command hint missing`);
  check((await input.getAttribute('placeholder'))?.includes('actions'), `${profile.name}: improved command-search hint missing`);
  check(await input.getAttribute('aria-describedby') === 'v430-command-hint', `${profile.name}: command-search description not connected`);

  const quickButtons = quick.locator('[data-command-action]');
  check(await quickButtons.count() === 6, `${profile.name}: expected six quick actions, got ${await quickButtons.count()}`);
  for (const id of ['save-local', 'export', 'focus-mode', 'workflow-write', 'workflow-preview', 'workflow-publish']) {
    check(await quick.locator(`[data-command-action="${id}"]`).count() === 1, `${profile.name}: quick action ${id} missing`);
  }
  const focusQuick = quick.locator('[data-command-action="focus-mode"]').first();
  check(!(await focusQuick.isDisabled()), `${profile.name}: Focus quick action unexpectedly disabled in Split`);
  check(await rootFits(page), `${profile.name}: overflow with palette open`);

  await input.fill('focus');
  await page.waitForTimeout(100);
  check(!(await quick.isVisible()), `${profile.name}: quick actions should hide while filtering`);
  const focusResult = layer.locator('[data-command-action="focus-mode"]').filter({ hasText: 'Toggle Focus Mode' }).first();
  check(await visible(focusResult), `${profile.name}: Focus command not registered in native searchable list`);

  await input.fill('bibliography');
  await page.waitForTimeout(100);
  const bibliography = layer.locator('#command-list [data-command-action="bibliography"]').first();
  check(await visible(bibliography), `${profile.name}: native registry filtering regressed`);

  await closePalette(page);
  await page.waitForTimeout(50);
  check(await trigger.getAttribute('aria-expanded') === 'false', `${profile.name}: trigger expanded state not reset`);
  check(await page.evaluate(() => document.activeElement?.classList?.contains('v430-command-trigger')), `${profile.name}: palette did not restore trigger focus`);

  await openPaletteByShortcut(page);
  check(await visible(page.locator('.command-layer .v430-command-fast').first()), `${profile.name}: Ctrl+K palette lacks P4 fast actions`);
  const shortcutFocus = page.locator('.command-layer .v430-command-fast [data-command-action="focus-mode"]').first();
  check(!(await shortcutFocus.isDisabled()), `${profile.name}: shortcut-opened Focus action disabled`);
  await shortcutFocus.click();
  await page.waitForSelector('.command-layer', { state: 'detached', timeout: 5000 });
  await page.waitForFunction(() => window.__manuscriptV430P3?.active === true, null, { timeout: 5000 });
  check(await page.locator('html').getAttribute('data-v430-focus') === 'true', `${profile.name}: Focus quick action did not activate P3`);

  await openPaletteByShortcut(page);
  const exitFocus = page.locator('.command-layer .v430-command-fast [data-command-action="focus-mode"]').first();
  check(!(await exitFocus.isDisabled()), `${profile.name}: Exit Focus quick action disabled`);
  check((await exitFocus.textContent())?.includes('Exit Focus'), `${profile.name}: Focus quick action did not reflect active state`);
  await exitFocus.click();
  await page.waitForSelector('.command-layer', { state: 'detached', timeout: 5000 });
  await page.waitForFunction(() => window.__manuscriptV430P3?.active === false, null, { timeout: 5000 });
  check(!await page.locator('html').getAttribute('data-v430-focus'), `${profile.name}: P3 focus attribute remained after fast exit`);

  const preview = page.locator('[data-workspace="preview"]:visible').first();
  check(await preview.count() === 1, `${profile.name}: Preview workspace control missing`);
  await preview.click();
  await page.waitForTimeout(120);
  await trigger.click();
  await page.waitForSelector('.command-layer[data-v430-p4="true"] .v430-command-fast', { state: 'visible', timeout: 5000 });
  const previewFocus = page.locator('.command-layer .v430-command-fast [data-command-action="focus-mode"]').first();
  check(await previewFocus.isDisabled(), `${profile.name}: Focus quick action should be disabled in Preview-only mode`);
  await closePalette(page);
  check(await rootFits(page), `${profile.name}: overflow after P4 interactions`);
}

async function certifyMobile(page, profile) {
  await page.waitForTimeout(200);
  check(await page.locator('.v430-command-trigger').count() === 0, `${profile.name}: P4 desktop/tablet trigger leaked into mobile DOM`);
  const mobileNav = page.locator('.mobile-bottom-nav:visible').first();
  check(await visible(mobileNav), `${profile.name}: mobile navigation missing`);

  await openPaletteByShortcut(page);
  const layer = page.locator('.command-layer').first();
  const quick = layer.locator('.v430-command-fast').first();
  check(await visible(quick), `${profile.name}: keyboard-opened palette lacks quick actions`);
  const buttons = quick.locator('.v430-command-fast-btn');
  check(await buttons.count() === 6, `${profile.name}: mobile quick-action count wrong`);
  const focus = quick.locator('[data-command-action="focus-mode"]').first();
  check(await focus.isDisabled(), `${profile.name}: mobile Focus quick action should be unavailable before P5`);
  const rects = await buttons.evaluateAll(nodes => nodes.map(node => {
    const r = node.getBoundingClientRect();
    return { left: r.left, right: r.right, width: r.width, height: r.height };
  }));
  for (const rect of rects) {
    check(rect.width > 80 && rect.height >= 44, `${profile.name}: unusable mobile quick action ${JSON.stringify(rect)}`);
    check(rect.left >= -1 && rect.right <= profile.viewport.width + 1, `${profile.name}: quick action outside viewport ${JSON.stringify(rect)}`);
  }
  check(await rootFits(page), `${profile.name}: mobile palette overflow`);
  await closePalette(page);
  check(await visible(mobileNav), `${profile.name}: mobile navigation not restored after palette`);
}

async function certify(profile) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: profile.viewport,
    isMobile: !!profile.isMobile,
    hasTouch: !!profile.hasTouch,
    deviceScaleFactor: profile.isMobile ? 2 : 1,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(7000);
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));

  try {
    await page.goto(baseURL, { waitUntil: 'load', timeout: 45000 });
    await openEditor(page);
    await closeModal(page);

    const contract = await page.locator('meta[name="manuscript-command-palette-contract"]').getAttribute('content');
    check(contract === 'discoverable-fast-actions-v1', `${profile.name}: P4 contract mismatch ${contract}`);
    check(await page.locator('#v430-p4-command-palette').count() === 1, `${profile.name}: P4 style marker missing`);
    check(await page.locator('#v430-p4-runtime').count() === 1, `${profile.name}: P4 runtime marker missing`);
    check(await page.locator('#v430-p1-simplified-navigation').count() === 1, `${profile.name}: P1 contract missing`);
    check(await page.locator('#v430-p2-compact-density').count() === 1, `${profile.name}: P2 contract missing`);
    check(await page.locator('#v430-p3-focus-mode').count() === 1, `${profile.name}: P3 contract missing`);

    if (profile.trigger) await certifyDesktop(page, profile);
    else await certifyMobile(page, profile);

    check(pageErrors.length === 0, `${profile.name}: page errors: ${pageErrors.join(' | ')}`);
  } finally {
    await context.close();
    await browser.close();
  }
}

let passed = 0;
for (const profile of profiles) {
  process.stdout.write(`Certifying P4 ${profile.name}... `);
  await certify(profile);
  passed += 1;
  console.log('PASS');
}
console.log(`V430-P4 certification PASS — ${passed}/${profiles.length} profiles`);
