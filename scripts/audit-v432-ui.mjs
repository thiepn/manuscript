import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const outDir = 'diagnostics/v432-ui';
fs.mkdirSync(outDir, { recursive: true });

const profiles = [
  { name: 'phone-320', width: 320, height: 568, mobile: true },
  { name: 'phone-360', width: 360, height: 800, mobile: true },
  { name: 'phone-390', width: 390, height: 844, mobile: true },
  { name: 'phone-480', width: 480, height: 800, mobile: true },
  { name: 'mobile-boundary-767', width: 767, height: 900, mobile: true },
  { name: 'desktop-boundary-768', width: 768, height: 900, mobile: false },
  { name: 'tablet-900', width: 900, height: 900, mobile: false },
  { name: 'desktop-boundary-901', width: 901, height: 900, mobile: false },
  { name: 'desktop-1024', width: 1024, height: 768, mobile: false },
  { name: 'desktop-1440', width: 1440, height: 900, mobile: false },
];

const report = { generatedAt: new Date().toISOString(), baseURL, findings: [], profiles: [] };
const add = (profile, stage, severity, code, message, data = {}) => report.findings.push({ profile, stage, severity, code, message, data });

async function visible(locator) {
  return (await locator.count()) > 0 && await locator.first().isVisible().catch(() => false);
}

async function closeModal(page) {
  const layer = page.locator('.modal-layer').first();
  if (!await visible(layer)) return;
  const close = layer.locator('[data-action="modal-close"], .modal-close').first();
  if (await visible(close)) await close.click({ timeout: 5000 }); else await page.keyboard.press('Escape');
  await layer.waitFor({ state: 'detached', timeout: 5000 }).catch(async () => {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(100);
  });
}

async function goHome(page) {
  await closeModal(page);
  let screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'home') return;
  const home = page.locator('[data-action="home"]:visible').first();
  if (await visible(home)) await home.click({ timeout: 5000 });
  else if (screen === 'landing') {
    const fallback = page.locator('[data-action="home"]').first();
    if (await fallback.count()) await fallback.click({ timeout: 5000, force: true });
  }
  try {
    await page.waitForFunction(() => document.documentElement.dataset.screen === 'home', null, { timeout: 8000 });
  } catch {
    // A fresh navigation removes any transient modal/state race without preserving profile state.
    await page.goto(baseURL, { waitUntil: 'load', timeout: 45000 });
    await closeModal(page);
    screen = await page.locator('html').getAttribute('data-screen');
    if (screen !== 'home') {
      const retry = page.locator('[data-action="home"]').first();
      if (await retry.count()) await retry.click({ timeout: 5000, force: true });
    }
    await page.waitForFunction(() => document.documentElement.dataset.screen === 'home', null, { timeout: 10000 });
  }
  await closeModal(page);
}

async function openTemplates(page) {
  const button = page.locator('[data-action="templates"]:visible').first();
  if (!await visible(button)) throw new Error('Visible Templates trigger not found');
  await button.click();
  await page.locator('.modal-layer .modal').waitFor({ state: 'visible', timeout: 8000 });
  // Let the short modal entrance animation finish before geometry/screenshots are sampled.
  await page.waitForTimeout(240);
}

async function openLearningExample(page, id = 'markdown-basics') {
  await openTemplates(page);
  const use = page.locator(`[data-action="use-template"][data-id="${id}"]`).first();
  if (!await visible(use)) throw new Error(`Learning template ${id} not visible`);
  await use.click();
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, { timeout: 10000 });
  await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout: 10000 });
  await page.waitForTimeout(180);
}

async function screenshot(page, profile, stage) {
  await page.screenshot({ path: path.join(outDir, `${profile}-${stage}.png`), fullPage: false });
}

async function measure(page) {
  return page.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;
    const shown = el => {
      if (!el) return false;
      const s = getComputedStyle(el), r = el.getBoundingClientRect();
      return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) !== 0 && r.width > 0.5 && r.height > 0.5;
    };
    const rect = el => {
      const r = el.getBoundingClientRect();
      return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
    };
    const sel = q => document.querySelector(q);
    const all = q => [...document.querySelectorAll(q)].filter(shown);
    const modal = all('.modal-layer .modal')[0] || null;
    const appbar = sel('.appbar');
    const toolbar = sel('.toolbar');
    const workspace = sel('.workspace');
    const nav = sel('.mobile-bottom-nav');
    const cards = all('.template-card');
    const learning = cards.filter(card => /Markdown Basics|Lists, Tasks|Code, Math|Manuscript Publishing Extras/.test(card.textContent || ''));
    const touchButtons = all('button').map(el => ({ text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80), className: el.className, ...rect(el) }));
    const modalParts = modal ? {
      modal: rect(modal),
      opacity: Number(getComputedStyle(modal).opacity || 1),
      head: modal.querySelector('.modal-head') && shown(modal.querySelector('.modal-head')) ? rect(modal.querySelector('.modal-head')) : null,
      body: modal.querySelector('.modal-body') && shown(modal.querySelector('.modal-body')) ? { ...rect(modal.querySelector('.modal-body')), scrollHeight: modal.querySelector('.modal-body').scrollHeight, clientHeight: modal.querySelector('.modal-body').clientHeight, scrollWidth: modal.querySelector('.modal-body').scrollWidth, clientWidth: modal.querySelector('.modal-body').clientWidth } : null,
      foot: modal.querySelector('.modal-foot') && shown(modal.querySelector('.modal-foot')) ? { ...rect(modal.querySelector('.modal-foot')), scrollWidth: modal.querySelector('.modal-foot').scrollWidth, clientWidth: modal.querySelector('.modal-foot').clientWidth } : null,
    } : null;
    const title = sel('.doc-title');
    const bodyTextNodes = [...document.body.childNodes]
      .filter(node => node.nodeType === Node.TEXT_NODE && (node.textContent || '').trim())
      .map(node => ({ text: node.textContent, trimmed: (node.textContent || '').trim().slice(0, 200) }));
    const bodyChildren = [...document.body.childNodes].slice(0, 12).map(node => ({
      type: node.nodeType,
      name: node.nodeName,
      text: node.nodeType === Node.TEXT_NODE ? (node.textContent || '').slice(0, 120) : '',
      id: node.nodeType === Node.ELEMENT_NODE ? node.id || '' : '',
      className: node.nodeType === Node.ELEMENT_NODE ? String(node.className || '').slice(0, 120) : '',
    }));
    const topElement = document.elementFromPoint(Math.min(8, vw - 1), Math.min(8, vh - 1));
    return {
      vw, vh,
      root: { scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth, scrollHeight: document.documentElement.scrollHeight },
      screen: document.documentElement.dataset.screen || '',
      appbar: appbar && shown(appbar) ? rect(appbar) : null,
      toolbar: toolbar && shown(toolbar) ? { ...rect(toolbar), scrollWidth: toolbar.scrollWidth, clientWidth: toolbar.clientWidth } : null,
      workspace: workspace && shown(workspace) ? rect(workspace) : null,
      nav: nav && shown(nav) ? rect(nav) : null,
      modal: modalParts,
      cards: cards.map(rect),
      learningCards: learning.map(card => ({ title: (card.querySelector('h3')?.textContent || '').trim(), ...rect(card) })),
      buttons: touchButtons,
      docTitle: title && shown(title) ? { ...rect(title), scrollWidth: title.scrollWidth, clientWidth: title.clientWidth, value: title.value } : null,
      focusables: all('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href],[tabindex]:not([tabindex="-1"])').length,
      bodyTextNodes,
      bodyChildren,
      bodyTextStart: (document.body.innerText || '').slice(0, 240),
      topElement: topElement ? { tag: topElement.tagName, id: topElement.id || '', className: String(topElement.className || ''), text: (topElement.textContent || '').trim().slice(0, 160) } : null,
    };
  });
}

function inspect(profile, stage, m) {
  const p = profile.name;
  if (m.root.scrollWidth > m.vw + 2) add(p, stage, 'high', 'ROOT_X_OVERFLOW', 'Root document overflows horizontally.', { scrollWidth: m.root.scrollWidth, viewport: m.vw });
  if (m.bodyTextNodes.length) add(p, stage, 'high', 'STRAY_ROOT_TEXT', 'Unexpected direct text node is rendered at the body root.', { nodes: m.bodyTextNodes, children: m.bodyChildren, bodyTextStart: m.bodyTextStart, topElement: m.topElement });

  if (m.modal) {
    const r = m.modal.modal;
    if (r.left < -1 || r.right > m.vw + 1 || r.top < -1 || r.bottom > m.vh + 1) add(p, stage, 'high', 'MODAL_CLIPPED', 'Modal extends outside the viewport.', r);
    if (m.modal.opacity < 0.98) add(p, stage, 'medium', 'MODAL_NOT_SETTLED', 'Modal is still partly transparent after its entrance animation.', { opacity: m.modal.opacity });
    if (m.modal.body?.scrollWidth > m.modal.body?.clientWidth + 2) add(p, stage, 'high', 'MODAL_BODY_X_OVERFLOW', 'Modal body has unintended horizontal scrolling.', m.modal.body);
    if (m.modal.foot?.scrollWidth > m.modal.foot?.clientWidth + 2) add(p, stage, 'high', 'MODAL_FOOT_X_OVERFLOW', 'Modal footer overflows horizontally.', m.modal.foot);
    if (m.modal.head && m.modal.body && m.modal.head.bottom > m.modal.body.top + 1) add(p, stage, 'high', 'MODAL_HEAD_BODY_OVERLAP', 'Modal header overlaps body.');
    if (m.modal.body && m.modal.foot && m.modal.body.bottom > m.modal.foot.top + 1) add(p, stage, 'high', 'MODAL_BODY_FOOT_OVERLAP', 'Modal body overlaps footer.');
  }

  if (stage === 'templates') {
    if (m.learningCards.length !== 4) add(p, stage, 'high', 'LEARNING_CARDS_MISSING', 'Template Gallery does not expose exactly four Markdown learning examples.', { count: m.learningCards.length, titles: m.learningCards.map(x => x.title) });
    for (const card of m.cards) if (card.width < 180) add(p, stage, 'medium', 'TEMPLATE_CARD_TOO_NARROW', 'A template card is too narrow for readable content.', card);
  }

  if (m.screen === 'editor') {
    if (m.appbar && m.toolbar && Math.abs(m.appbar.bottom - m.toolbar.top) > 1.5) add(p, stage, 'high', 'APPBAR_TOOLBAR_GAP_OR_OVERLAP', 'App bar and toolbar do not meet cleanly.', { appbar: m.appbar, toolbar: m.toolbar });
    if (m.toolbar && m.workspace && Math.abs(m.toolbar.bottom - m.workspace.top) > 1.5) add(p, stage, 'high', 'TOOLBAR_WORKSPACE_GAP_OR_OVERLAP', 'Toolbar and workspace do not meet cleanly.', { toolbar: m.toolbar, workspace: m.workspace });
    if (profile.width <= 767) {
      if (!m.nav) add(p, stage, 'high', 'MOBILE_NAV_MISSING', 'Mobile bottom navigation is absent.');
      else if (m.workspace && m.workspace.bottom > m.nav.top + 1) add(p, stage, 'high', 'WORKSPACE_UNDER_MOBILE_NAV', 'Editor workspace extends underneath the fixed mobile navigation.', { workspace: m.workspace, nav: m.nav });
    } else if (m.nav) add(p, stage, 'high', 'MOBILE_NAV_AT_DESKTOP_BREAKPOINT', 'Mobile navigation remains visible at or above 768px.', { nav: m.nav });
  }

  if (profile.mobile || profile.width <= 767) {
    const tooSmall = m.buttons.filter(b => b.width < 40 || b.height < 40);
    if (tooSmall.length) add(p, stage, 'medium', 'COARSE_TARGETS_UNDERSIZED', 'Visible touch controls below 40×40px were found.', { count: tooSmall.length, examples: tooSmall.slice(0, 12) });
  }
}

for (const profile of profiles) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: profile.width, height: profile.height }, isMobile: profile.mobile, hasTouch: profile.mobile, deviceScaleFactor: profile.mobile ? 2 : 1 });
  const page = await context.newPage();
  page.setDefaultTimeout(8000);
  const pageErrors = [], consoleErrors = [], stages = [];
  page.on('pageerror', e => pageErrors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  try {
    await page.goto(baseURL, { waitUntil: 'load', timeout: 45000 });
    await closeModal(page);
    await goHome(page);
    await screenshot(page, profile.name, 'home');
    let m = await measure(page); inspect(profile, 'home', m); stages.push({ stage: 'home', metrics: m });

    await openTemplates(page);
    await screenshot(page, profile.name, 'templates');
    m = await measure(page); inspect(profile, 'templates', m); stages.push({ stage: 'templates', metrics: m });
    await closeModal(page);

    await openLearningExample(page, 'markdown-basics');
    await screenshot(page, profile.name, 'editor');
    m = await measure(page); inspect(profile, 'editor', m); stages.push({ stage: 'editor', metrics: m });

    if (profile.width <= 767) {
      const preview = page.locator('[data-mobile="preview"]:visible').first();
      if (await visible(preview)) await preview.click();
      await page.waitForTimeout(100);
      await screenshot(page, profile.name, 'mobile-preview');
      m = await measure(page); inspect(profile, 'mobile-preview', m); stages.push({ stage: 'mobile-preview', metrics: m });

      const format = page.locator('[data-mobile="style"]:visible').first();
      if (await visible(format)) await format.click();
      await page.waitForTimeout(100);
      await screenshot(page, profile.name, 'mobile-format');
      m = await measure(page); inspect(profile, 'mobile-format', m); stages.push({ stage: 'mobile-format', metrics: m });
    } else {
      for (const mode of ['editor', 'split', 'preview']) {
        const button = page.locator(`[data-workspace="${mode}"]:visible`).first();
        if (await visible(button)) await button.click();
        await page.waitForTimeout(90);
        m = await measure(page); inspect(profile, `workspace-${mode}`, m); stages.push({ stage: `workspace-${mode}`, metrics: m });
      }
    }
  } catch (error) {
    add(profile.name, 'fatal', 'fatal', 'PROFILE_FATAL', String(error?.stack || error));
  } finally {
    if (pageErrors.length) add(profile.name, 'runtime', 'high', 'PAGE_ERRORS', 'Uncaught page errors occurred.', { errors: pageErrors });
    if (consoleErrors.length) add(profile.name, 'runtime', 'medium', 'CONSOLE_ERRORS', 'Console errors occurred.', { errors: consoleErrors.slice(0, 20) });
    report.profiles.push({ ...profile, stages: stages.map(s => ({ stage: s.stage, metrics: s.metrics })) });
    await context.close();
    await browser.close();
  }
}

report.summary = { total: report.findings.length, high: report.findings.filter(x => x.severity === 'high').length, medium: report.findings.filter(x => x.severity === 'medium').length, fatal: report.findings.filter(x => x.severity === 'fatal').length };
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
let md = `# Manuscript v4.3.2 deep UI audit\n\n- High: ${report.summary.high}\n- Medium: ${report.summary.medium}\n- Fatal: ${report.summary.fatal}\n- Total: ${report.summary.total}\n\n`;
if (!report.findings.length) md += 'No findings.\n';
for (const f of report.findings) md += `- **${f.severity.toUpperCase()} ${f.code}** · ${f.profile} · ${f.stage} — ${f.message} ${JSON.stringify(f.data)}\n`;
fs.writeFileSync(path.join(outDir, 'report.md'), md);
console.log(md);
if (report.summary.high || report.summary.fatal) process.exitCode = 1;
