#!/usr/bin/env python3
from pathlib import Path

# P5 intentionally extends two older phase boundaries:
# - P3 Focus becomes available below 768px.
# - P4's mobile Focus fast action changes from disabled to enabled in Write.
# Keep the older tests strict when the P5 marker is absent, while allowing the
# later phase to extend those exact boundaries without weakening desktop tests.

p3 = Path('scripts/certify-v430-p3.mjs')
text = p3.read_text(encoding='utf-8')
old = '''async function certifyMobileProfile(page, profile) {
  await page.waitForTimeout(200);
  check(await page.locator('.v430-focus-trigger').count() === 0, `${profile.name}: desktop focus trigger leaked into mobile DOM`);
  const mobileNav = page.locator('.mobile-bottom-nav:visible').first();
  check(await visible(mobileNav), `${profile.name}: mobile navigation missing`);
  const enter = await page.evaluate(() => ({
    eligible: window.__manuscriptV430P3?.eligible,
    result: window.__manuscriptV430P3?.enter(),
    attr: document.documentElement.dataset.v430Focus || '',
  }));
  check(enter.eligible === false && enter.result === false && !enter.attr, `${profile.name}: focus runtime leaked into mobile ${JSON.stringify(enter)}`);
  const targets = await mobileNav.locator('button:visible').evaluateAll(buttons => buttons.map(button => {
    const r = button.getBoundingClientRect();
    return { width: r.width, height: r.height };
  }));
  check(targets.length > 0, `${profile.name}: mobile nav has no buttons`);
  for (const target of targets) check(target.width >= 30 && target.height >= 30, `${profile.name}: mobile target regressed ${JSON.stringify(target)}`);
  check(await rootFits(page), `${profile.name}: mobile root overflow`);
}'''
new = '''async function certifyMobileProfile(page, profile) {
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
}'''
if old in text:
    p3.write_text(text.replace(old, new, 1), encoding='utf-8')
elif new not in text:
    raise SystemExit('P3 mobile contract block not found')

p4 = Path('scripts/certify-v430-p4.mjs')
text = p4.read_text(encoding='utf-8')
old = "  check(await focus.isDisabled(), `${profile.name}: mobile Focus quick action should be unavailable before P5`);"
new = '''  const p5 = await page.locator('#v430-p5-mobile-first').count() === 1;
  if (p5) check(!(await focus.isDisabled()), `${profile.name}: P5 should enable the mobile Focus quick action in Write`);
  else check(await focus.isDisabled(), `${profile.name}: mobile Focus quick action should be unavailable before P5`);'''
if old in text:
    p4.write_text(text.replace(old, new, 1), encoding='utf-8')
elif new not in text:
    raise SystemExit('P4 mobile Focus boundary assertion not found')

print('Made P3/P4 mobile boundary tests P5-aware')
