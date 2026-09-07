import { chromium } from 'playwright';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  { name: 'desktop-wide', viewport: { width: 1440, height: 900 }, dense: true },
  { name: 'desktop-compact', viewport: { width: 1024, height: 768 }, dense: true },
  { name: 'tablet-edge', viewport: { width: 768, height: 1024 }, dense: true, isMobile: true, hasTouch: true },
  { name: 'mobile-portrait', viewport: { width: 390, height: 844 }, dense: false, isMobile: true, hasTouch: true },
  { name: 'mobile-landscape', viewport: { width: 740, height: 390 }, dense: false, isMobile: true, hasTouch: true },
];

function check(condition, message) {
  if (!condition) throw new Error(message);
}

async function visible(locator) {
  return (await locator.count()) > 0 && await locator.isVisible().catch(() => false);
}

async function closeModal(page) {
  const layer = page.locator('.modal-layer').first();
  if (!(await visible(layer))) return;
  const close = layer.locator('[data-action="modal-close"], .modal-close').first();
  if (await close.count()) await close.click({ timeout: 5000 }).catch(() => {});
  else await page.keyboard.press('Escape');
  await layer.waitFor({ state: 'detached', timeout: 2500 }).catch(async () => {
    await page.keyboard.press('Escape').catch(() => {});
  });
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
      { timeout: 10000 },
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
    const create = page.locator('[data-action="new"]:visible').first();
    check(await create.count() === 1, 'Unable to locate New action from home');
    await create.click({ timeout: 5000 });
    blank = page.locator('.modal-layer [data-action="onboarding-blank"]:visible').first();
    if (await blank.count()) await blank.click({ timeout: 5000 });
  }

  await page.waitForFunction(
    () => document.documentElement.dataset.screen === 'editor',
    null,
    { timeout: 15000 },
  );
  await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout: 15000 });
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

    const contract = await page.locator('meta[name="manuscript-density-ui-contract"]').getAttribute('content');
    check(contract === 'compact-density-v1', `P2 contract missing: ${contract}`);
    check(await page.locator('#v430-p2-compact-density').count() === 1, 'P2 style marker missing');
    check(await page.locator('#v430-p1-simplified-navigation').count() === 1, 'P1 contract regressed');

    const rootOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    check(rootOverflow <= 2, `root horizontal overflow: ${rootOverflow}px`);

    const mediaMatches = await page.evaluate(() => matchMedia('(min-width: 768px)').matches);
    check(mediaMatches === profile.dense, `density breakpoint mismatch: ${mediaMatches}`);

    if (profile.dense) {
      const nav = page.locator('.v430-nav-host:visible').first();
      check(await visible(nav), 'desktop/tablet P1 navigation host missing');
      const navMetrics = await nav.evaluate(el => {
        const s = getComputedStyle(el);
        return {
          gap: parseFloat(s.rowGap || s.gap || '0'),
          paddingTop: parseFloat(s.paddingTop || '0'),
          paddingBottom: parseFloat(s.paddingBottom || '0'),
        };
      });
      check(navMetrics.gap <= 4, `nav gap is not compact: ${JSON.stringify(navMetrics)}`);
      check(navMetrics.paddingTop <= 6 && navMetrics.paddingBottom <= 6, `nav padding is not compact: ${JSON.stringify(navMetrics)}`);

      const densityVar = await page.locator('.left-panel').first().evaluate(el => getComputedStyle(el).getPropertyValue('--v430-density-control-height').trim());
      check(densityVar === '30px', `left-panel density token missing: ${densityVar}`);

      const more = page.locator('.v430-utility-trigger:visible').first();
      check(await visible(more), 'More Tools trigger missing');
      const moreFit = await more.evaluate(el => ({ clientWidth: el.clientWidth, scrollWidth: el.scrollWidth, height: el.getBoundingClientRect().height }));
      check(moreFit.scrollWidth <= moreFit.clientWidth + 2, `More Tools label clipped: ${JSON.stringify(moreFit)}`);
      check(moreFit.height >= 28, `More Tools target too small: ${JSON.stringify(moreFit)}`);

      await more.click();
      const menu = page.locator('#v430-utility-menu:visible').first();
      check(await visible(menu), 'More Tools menu did not open');
      const item = menu.locator('[role="menuitem"]:visible').first();
      check(await visible(item), 'More Tools menu item missing');
      const itemMetrics = await item.evaluate(el => {
        const r = el.getBoundingClientRect();
        return { width: r.width, height: r.height, clientWidth: el.clientWidth, scrollWidth: el.scrollWidth };
      });
      check(itemMetrics.height >= 28 && itemMetrics.height <= 38, `utility row density outside safe range: ${JSON.stringify(itemMetrics)}`);
      check(itemMetrics.scrollWidth <= itemMetrics.clientWidth + 2, `utility row label clipped: ${JSON.stringify(itemMetrics)}`);
      await page.keyboard.press('Escape');
    } else {
      const mobileNav = page.locator('.mobile-bottom-nav:visible').first();
      check(await visible(mobileNav), 'mobile bottom navigation missing');
      const buttonMetrics = await mobileNav.locator('button:visible').evaluateAll(buttons => buttons.map(button => {
        const r = button.getBoundingClientRect();
        return { width: r.width, height: r.height };
      }));
      check(buttonMetrics.length > 0, 'mobile navigation has no visible buttons');
      for (const metric of buttonMetrics) {
        check(metric.width >= 30 && metric.height >= 30, `mobile target regressed: ${JSON.stringify(metric)}`);
      }
      const mobileDensity = await page.locator('.left-panel').first().evaluate(el => getComputedStyle(el).getPropertyValue('--v430-density-control-height').trim());
      check(mobileDensity !== '30px', 'desktop P2 density rules leaked into mobile');
    }

    check(pageErrors.length === 0, `fatal page errors: ${pageErrors.join(' | ')}`);
  } finally {
    await context.close();
    await browser.close();
  }
}

let passed = 0;
for (const profile of profiles) {
  process.stdout.write(`Certifying P2 ${profile.name}... `);
  await certify(profile);
  passed += 1;
  console.log('PASS');
}
console.log(`V430-P2 certification PASS — ${passed}/${profiles.length} profiles`);
