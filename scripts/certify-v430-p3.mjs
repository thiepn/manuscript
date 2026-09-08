import { chromium } from 'playwright';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  { name: 'desktop-wide', viewport: { width: 1440, height: 900 }, focus: true },
  { name: 'desktop-compact', viewport: { width: 1024, height: 768 }, focus: true },
  { name: 'tablet-edge', viewport: { width: 768, height: 1024 }, focus: true, isMobile: true, hasTouch: true },
  { name: 'mobile-portrait', viewport: { width: 390, height: 844 }, focus: false, isMobile: true, hasTouch: true },
  { name: 'mobile-landscape', viewport: { width: 740, height: 390 }, focus: false, isMobile: true, hasTouch: true },
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

async function clickVisible(page, selector) {
  const deadline = Date.now() + 6000;
  do {
    const nodes = page.locator(selector);
    for (let i = 0; i < await nodes.count(); i += 1) {
      const node = nodes.nth(i);
      await node.scrollIntoViewIfNeeded().catch(() => {});
      if (await node.isVisible().catch(() => false)) {
        try { await node.click({ timeout: 3000 }); }
        catch { await node.evaluate(el => el.click()); }
        return node;
      }
    }
    await page.waitForTimeout(100);
  } while (Date.now() < deadline);
  throw new Error(`No visible element for ${selector}`);
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

async function activeWorkspace(page) {
  return page.evaluate(() => {
    const node = [...document.querySelectorAll('[data-workspace].active,[data-workspace][aria-pressed="true"]')]
      .find(el => !el.closest('.modal-layer,.left-panel,.inspector,.mobile-bottom-nav'));
    return node?.getAttribute('data-workspace') || '';
  });
}

async function waitForTrigger(page) {
  await page.waitForFunction(
    () => !!document.querySelector('.v430-focus-trigger'),
    null,
    { timeout: 8000 },
  );
  return page.locator('.v430-focus-trigger').first();
}

async function triggerMutationCount(page) {
  return page.evaluate(async () => {
    const trigger = document.querySelector('.v430-focus-trigger');
    if (!trigger) return -1;
    let count = 0;
    const observer = new MutationObserver(records => { count += records.length; });
    observer.observe(trigger, { subtree: true, childList: true, attributes: true, characterData: true });
    await new Promise(resolve => setTimeout(resolve, 300));
    observer.disconnect();
    return count;
  });
}

async function certifyFocusProfile(page, profile) {
  const trigger = await waitForTrigger(page);
  check(await visible(trigger), `${profile.name}: focus trigger not visible`);
  check(!(await trigger.isDisabled()), `${profile.name}: focus trigger unexpectedly disabled in Split`);
  check(await trigger.getAttribute('aria-pressed') === 'false', `${profile.name}: initial focus pressed state wrong`);

  const mutations = await triggerMutationCount(page);
  check(mutations >= 0 && mutations <= 2, `${profile.name}: focus trigger mutation churn detected (${mutations})`);

  check(await activeWorkspace(page) === 'split', `${profile.name}: expected initial Split workspace`);
  await clickVisible(page, '.v430-nav-host [data-panel="diagnostics"]');
  await page.waitForTimeout(100);
  check(await visible(page.locator('.left-panel').first()), `${profile.name}: pre-focus diagnostics panel not visible`);

  const before = await page.evaluate(() => ({
    workspaceClass: document.querySelector('.workspace')?.className || '',
    panelTitle: document.querySelector('.left-panel .panel-title')?.textContent || '',
    title: document.querySelector('.doc-title')?.value || '',
  }));

  await trigger.click();
  await page.waitForFunction(() => document.documentElement.dataset.v430Focus === 'true', null, { timeout: 5000 });
  check(await page.evaluate(() => window.__manuscriptV430P3?.active === true), `${profile.name}: runtime active flag false`);
  check(await trigger.getAttribute('aria-pressed') === 'true', `${profile.name}: trigger did not expose active state`);
  check((await trigger.getAttribute('aria-label')) === 'Exit focus mode', `${profile.name}: exit label missing`);

  for (const selector of ['.toolbar', '.activity-rail', '.left-panel', '.preview-pane', '.statusbar']) {
    const node = page.locator(selector).first();
    if (await node.count()) check(!(await node.isVisible().catch(() => false)), `${profile.name}: ${selector} still visible in focus`);
  }

  const editor = page.locator('.editor-pane').first();
  check(await visible(editor), `${profile.name}: editor pane hidden in focus`);
  const geometry = await page.evaluate(() => {
    const workspace = document.querySelector('.workspace')?.getBoundingClientRect();
    const stage = document.querySelector('.main-stage')?.getBoundingClientRect();
    const editor = document.querySelector('.editor-pane')?.getBoundingClientRect();
    const appbar = document.querySelector('.appbar')?.getBoundingClientRect();
    const title = document.querySelector('.doc-title-wrap')?.getBoundingClientRect();
    const exit = document.querySelector('.v430-focus-trigger')?.getBoundingClientRect();
    return { workspace, stage, editor, appbar, title, exit };
  });
  check(geometry.workspace && geometry.stage && geometry.editor && geometry.appbar && geometry.title && geometry.exit, `${profile.name}: focus geometry incomplete`);
  check(Math.abs(geometry.workspace.width - geometry.stage.width) <= 2, `${profile.name}: focus stage does not own workspace width`);
  check(geometry.editor.width > 500 || profile.viewport.width === 768, `${profile.name}: editor too narrow in focus (${geometry.editor.width})`);
  check(geometry.editor.width <= 982, `${profile.name}: editor exceeds reading width (${geometry.editor.width})`);
  check(geometry.editor.left >= geometry.stage.left - 1 && geometry.editor.right <= geometry.stage.right + 1, `${profile.name}: editor outside stage`);
  check(geometry.appbar.height <= 46, `${profile.name}: focus appbar not compact (${geometry.appbar.height})`);
  check(geometry.title.width > 100 && geometry.exit.width >= 80, `${profile.name}: focus topbar controls unusable`);
  check(await rootFits(page), `${profile.name}: horizontal overflow in focus`);

  const hiddenPaneHead = page.locator('.editor-pane .pane-head').first();
  if (await hiddenPaneHead.count()) check(!(await hiddenPaneHead.isVisible()), `${profile.name}: pane heading still visible in focus`);

  await page.keyboard.press('Escape');
  await page.waitForFunction(() => !document.documentElement.dataset.v430Focus, null, { timeout: 5000 });
  check(await page.evaluate(() => window.__manuscriptV430P3?.active === false), `${profile.name}: runtime remained active after Escape`);
  check(await activeWorkspace(page) === 'split', `${profile.name}: Split state not restored after focus`);
  check(await visible(page.locator('.left-panel').first()), `${profile.name}: open side panel not restored after focus`);
  check(await visible(page.locator('.preview-pane').first()), `${profile.name}: preview not restored after focus`);
  check(await visible(page.locator('.toolbar').first()), `${profile.name}: toolbar not restored after focus`);
  check(await trigger.getAttribute('aria-pressed') === 'false', `${profile.name}: trigger pressed state not reset`);
  const after = await page.evaluate(() => ({
    workspaceClass: document.querySelector('.workspace')?.className || '',
    panelTitle: document.querySelector('.left-panel .panel-title')?.textContent || '',
    title: document.querySelector('.doc-title')?.value || '',
  }));
  check(after.workspaceClass === before.workspaceClass, `${profile.name}: workspace classes changed across focus`);
  check(after.panelTitle === before.panelTitle, `${profile.name}: panel state changed across focus`);
  check(after.title === before.title, `${profile.name}: title changed across focus`);
  check(await rootFits(page), `${profile.name}: overflow after focus exit`);

  await clickVisible(page, '[data-workspace="preview"]');
  await page.waitForTimeout(150);
  const previewTrigger = await waitForTrigger(page);
  check(await previewTrigger.isDisabled(), `${profile.name}: focus should be disabled in Preview-only mode`);
  const apiEnter = await page.evaluate(() => window.__manuscriptV430P3?.enter());
  check(apiEnter === false, `${profile.name}: runtime entered focus from Preview-only mode`);
  check(!await page.locator('html').getAttribute('data-v430-focus'), `${profile.name}: focus attribute leaked in Preview-only mode`);
}

async function certifyMobileProfile(page, profile) {
  await page.waitForTimeout(200);
  const p5 = await page.locator('#v430-p5-mobile-first').count() === 1;
  const focusTrigger = page.locator('.v430-focus-trigger').first();
  const mobileNav = page.locator('.mobile-bottom-nav:visible').first();
  check(await visible(mobileNav), `${profile.name}: mobile navigation missing`);

  if (!p5) {
    check(await page.locator('.v430-focus-trigger').count() === 0, `${profile.name}: desktop focus trigger leaked into mobile DOM`);
    const enter = await page.evaluate(() => ({
      eligible: window.__manuscriptV430P3?.eligible,
      result: window.__manuscriptV430P3?.enter(),
      attr: document.documentElement.dataset.v430Focus || '',
    }));
    check(enter.eligible === false && enter.result === false && !enter.attr, `${profile.name}: focus runtime leaked into mobile ${JSON.stringify(enter)}`);
  } else {
    // P5 deliberately broadens the P3 state machine to mobile. The trigger is
    // retained in DOM for the explicit Focus exit path but hidden while Focus
    // is inactive. P5's own suite certifies entry, exit, and mobile geometry.
    check(await focusTrigger.count() === 1, `${profile.name}: P5 did not extend the P3 Focus trigger to mobile`);
    check(!(await focusTrigger.isVisible().catch(() => false)), `${profile.name}: inactive mobile Focus trigger should remain hidden`);
    check(!await page.locator('html').getAttribute('data-v430-focus'), `${profile.name}: mobile Focus activated without user action`);
    check(await page.evaluate(() => !!window.__manuscriptV430P3), `${profile.name}: P3 Focus runtime missing under P5`);
  }

  const targets = await mobileNav.locator('button:visible').evaluateAll(buttons => buttons.map(button => {
    const r = button.getBoundingClientRect();
    return { width: r.width, height: r.height };
  }));
  check(targets.length > 0, `${profile.name}: mobile nav has no buttons`);
  for (const target of targets) check(target.width >= 30 && target.height >= 30, `${profile.name}: mobile target regressed ${JSON.stringify(target)}`);
  check(await rootFits(page), `${profile.name}: mobile root overflow`);
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
    const contract = await page.locator('meta[name="manuscript-focus-mode-contract"]').getAttribute('content');
    check(contract === 'distraction-free-writing-v1', `${profile.name}: P3 contract mismatch ${contract}`);
    check(await page.locator('#v430-p3-focus-mode').count() === 1, `${profile.name}: P3 style marker missing`);
    check(await page.locator('#v430-p3-runtime').count() === 1, `${profile.name}: P3 runtime marker missing`);
    check(await page.locator('#v430-p1-simplified-navigation').count() === 1, `${profile.name}: P1 contract missing`);
    check(await page.locator('#v430-p2-compact-density').count() === 1, `${profile.name}: P2 contract missing`);

    if (profile.focus) await certifyFocusProfile(page, profile);
    else await certifyMobileProfile(page, profile);

    check(pageErrors.length === 0, `${profile.name}: page errors: ${pageErrors.join(' | ')}`);
  } finally {
    await context.close();
    await browser.close();
  }
}

let passed = 0;
for (const profile of profiles) {
  process.stdout.write(`Certifying P3 ${profile.name}... `);
  await certify(profile);
  passed += 1;
  console.log('PASS');
}
console.log(`V430-P3 certification PASS — ${passed}/${profiles.length} profiles`);
