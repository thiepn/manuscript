import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const outDir = 'diagnostics/page-fit';
fs.mkdirSync(outDir, { recursive: true });

const profiles = [
  { name: 'phone-320', width: 320, height: 568, mobile: true },
  { name: 'phone-360', width: 360, height: 800, mobile: true },
  { name: 'phone-390', width: 390, height: 844, mobile: true },
  { name: 'phone-480', width: 480, height: 800, mobile: true },
  { name: 'mobile-767', width: 767, height: 900, mobile: true },
  { name: 'desktop-1024', width: 1024, height: 768, mobile: false },
];

const report = { generatedAt: new Date().toISOString(), findings: [], profiles: [] };
const finding = (profile, severity, code, message, data = {}) => report.findings.push({ profile, severity, code, message, data });

async function visible(locator) {
  return (await locator.count()) > 0 && await locator.first().isVisible().catch(() => false);
}

async function closeModal(page) {
  const layer = page.locator('.modal-layer').first();
  if (!await visible(layer)) return;
  const close = layer.locator('[data-action="modal-close"],.modal-close').first();
  if (await visible(close)) await close.click({ timeout: 5000 });
  else await page.keyboard.press('Escape');
  await layer.waitFor({ state: 'detached', timeout: 5000 }).catch(() => {});
}

async function goHome(page) {
  await closeModal(page);
  if (await page.locator('html').getAttribute('data-screen') === 'home') return;
  const home = page.locator('[data-action="home"]').first();
  if (await home.count()) await home.click({ force: true });
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'home', null, { timeout: 10000 });
  await closeModal(page);
}

async function openExample(page) {
  await goHome(page);
  const templates = page.locator('[data-action="templates"]:visible').first();
  await templates.click();
  await page.locator('.modal-layer .modal').waitFor({ state: 'visible', timeout: 8000 });
  const use = page.locator('[data-action="use-template"][data-id="markdown-basics"]').first();
  await use.click();
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, { timeout: 10000 });
  await page.waitForSelector('.codemirror-editor .cm-scroller', { timeout: 10000 });
  await page.waitForTimeout(200);
}

async function showPages(page, mobile) {
  if (mobile) {
    const preview = page.locator('[data-mobile="preview"]:visible').first();
    if (!await visible(preview)) throw new Error('Mobile Preview action is missing');
    await preview.click();
  } else {
    const preview = page.locator('[data-workspace="preview"]:visible').first();
    if (!await visible(preview)) throw new Error('Desktop Preview workspace action is missing');
    await preview.click();
  }
  const pages = page.locator('[data-preview="pages"]:visible').first();
  if (await visible(pages)) await pages.click();
  await page.waitForSelector('#pages-wrap .page', { state: 'visible', timeout: 10000 });
  await page.waitForTimeout(180);
}

async function metrics(page) {
  return page.evaluate(() => {
    const preview = document.querySelector('.preview-scroll');
    const wrap = document.querySelector('#pages-wrap');
    const first = wrap?.querySelector('.page');
    if (!preview || !wrap || !first) return null;
    const rr = el => {
      const r = el.getBoundingClientRect();
      return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
    };
    const pr = rr(preview), wr = rr(wrap), fr = rr(first);
    const visibleLeft = Math.max(pr.left, fr.left);
    const visibleRight = Math.min(pr.right, fr.right);
    const visibleWidth = Math.max(0, visibleRight - visibleLeft);
    return {
      viewport: { width: document.documentElement.clientWidth, height: document.documentElement.clientHeight },
      preview: { ...pr, clientWidth: preview.clientWidth, scrollWidth: preview.scrollWidth, scrollLeft: preview.scrollLeft },
      wrap: {
        ...wr,
        cssWidth: wrap.style.width,
        cssZoom: wrap.style.zoom,
        cssTransform: wrap.style.transform,
        scaleMode: wrap.dataset.previewScaleMode || '',
        scale: Number(wrap.dataset.previewScale || 0),
      },
      page: fr,
      centerDelta: ((fr.left + fr.right) / 2) - ((pr.left + pr.right) / 2),
      visibleRatio: fr.width > 0 ? visibleWidth / fr.width : 0,
    };
  });
}

function inspect(profile, m, label) {
  if (!m) {
    finding(profile.name, 'high', 'PAGE_METRICS_MISSING', `${label}: preview/page geometry is unavailable.`);
    return;
  }
  if (m.wrap.cssTransform === 'none' && m.wrap.cssZoom && m.wrap.cssWidth !== '100%') {
    finding(profile.name, 'high', 'ZOOM_DOUBLE_WIDTH_COMPENSATION', `${label}: CSS zoom path must keep the wrapper at 100% width.`, m.wrap);
  }
  if (profile.mobile) {
    if (m.wrap.scaleMode !== 'fit-width') finding(profile.name, 'high', 'MOBILE_NOT_FIT_WIDTH', `${label}: mobile Pages preview is not in fit-width mode.`, m.wrap);
    if (Math.abs(m.centerDelta) > 4) finding(profile.name, 'high', 'PAGE_NOT_CENTERED', `${label}: fitted page is horizontally displaced.`, { centerDelta: m.centerDelta, preview: m.preview, page: m.page, wrap: m.wrap });
    if (m.visibleRatio < 0.98) finding(profile.name, 'high', 'PAGE_NOT_FULLY_VISIBLE', `${label}: fitted page is not fully visible horizontally.`, { visibleRatio: m.visibleRatio, preview: m.preview, page: m.page, wrap: m.wrap });
    if (m.preview.scrollWidth > m.preview.clientWidth + 2) finding(profile.name, 'medium', 'MOBILE_PREVIEW_X_SCROLL', `${label}: fit-width mobile Pages preview still has horizontal scrolling.`, m.preview);
    if (m.page.width < m.preview.width * 0.82) finding(profile.name, 'medium', 'PAGE_FIT_TOO_SMALL', `${label}: fitted page wastes excessive horizontal space.`, { previewWidth: m.preview.width, pageWidth: m.page.width });
  }
}

for (const profile of profiles) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: profile.width, height: profile.height },
    isMobile: profile.mobile,
    hasTouch: profile.mobile,
    deviceScaleFactor: profile.mobile ? 2 : 1,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(8000);
  const entry = { ...profile, checks: [] };
  try {
    await page.goto(baseURL, { waitUntil: 'load', timeout: 45000 });
    await openExample(page);
    await showPages(page, profile.mobile);
    let m = await metrics(page);
    inspect(profile, m, 'default');
    entry.checks.push({ label: 'default', metrics: m });
    await page.screenshot({ path: path.join(outDir, `${profile.name}-pages.png`) });

    if (!profile.mobile) {
      const zoomOut = page.locator('[data-action="zoom-out"]:visible').first();
      if (!await visible(zoomOut)) throw new Error('Desktop zoom-out control is missing');
      await zoomOut.click();
      await zoomOut.click();
      await page.waitForTimeout(120);
      m = await metrics(page);
      inspect(profile, m, 'zoom-out');
      if (m && Math.abs(m.centerDelta) > 5) finding(profile.name, 'high', 'DESKTOP_ZOOM_NOT_CENTERED', 'Desktop zoom-out displaces the page horizontally.', m);
      entry.checks.push({ label: 'zoom-out', metrics: m });
      await page.screenshot({ path: path.join(outDir, `${profile.name}-zoom-out.png`) });
    }
  } catch (error) {
    finding(profile.name, 'fatal', 'PROFILE_FATAL', String(error?.stack || error));
  } finally {
    report.profiles.push(entry);
    await context.close();
    await browser.close();
  }
}

const high = report.findings.filter(x => x.severity === 'high').length;
const medium = report.findings.filter(x => x.severity === 'medium').length;
const fatal = report.findings.filter(x => x.severity === 'fatal').length;
report.summary = { high, medium, fatal, total: report.findings.length };
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
let md = `# Page preview fit audit\n\n- High: ${high}\n- Medium: ${medium}\n- Fatal: ${fatal}\n- Total: ${report.findings.length}\n\n`;
if (!report.findings.length) md += 'No findings.\n';
else for (const f of report.findings) md += `- **${f.severity.toUpperCase()} ${f.code}** · ${f.profile} — ${f.message} ${JSON.stringify(f.data || {})}\n`;
fs.writeFileSync(path.join(outDir, 'report.md'), md);
console.log(md);
if (report.findings.length) process.exitCode = 1;
