import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  { name:'desktop-wide', viewport:{width:1440,height:900}, kind:'desktop' },
  { name:'desktop-compact', viewport:{width:1024,height:768}, kind:'desktop' },
  { name:'tablet-edge', viewport:{width:768,height:1024}, kind:'tablet', isMobile:true, hasTouch:true },
  { name:'mobile-portrait', viewport:{width:390,height:844}, kind:'mobile', isMobile:true, hasTouch:true },
  { name:'mobile-small', viewport:{width:320,height:568}, kind:'mobile', isMobile:true, hasTouch:true },
  { name:'mobile-landscape', viewport:{width:740,height:390}, kind:'mobile-landscape', isMobile:true, hasTouch:true },
];

const check = (ok, message) => assert.ok(ok, message);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function visible(locator) {
  return (await locator.count()) > 0 && await locator.isVisible().catch(() => false);
}

async function closeTransient(page) {
  const layer = page.locator('.modal-layer').first();
  if (await visible(layer)) {
    const close = layer.locator('[data-action="modal-close"],.modal-close').first();
    if (await visible(close)) await close.click({timeout:3000}).catch(() => {});
    else await page.keyboard.press('Escape').catch(() => {});
    await sleep(70);
  }
  const menu = page.locator('#v430-utility-menu[data-open="true"]').first();
  if (await visible(menu)) await page.keyboard.press('Escape').catch(() => {});
  const command = page.locator('.command-layer .command-palette').first();
  if (await visible(command)) await page.keyboard.press('Escape').catch(() => {});
}

async function clickVisible(page, selector) {
  const deadline = Date.now() + 6000;
  do {
    const nodes = page.locator(selector);
    for (let i = 0; i < await nodes.count(); i += 1) {
      const node = nodes.nth(i);
      await node.scrollIntoViewIfNeeded().catch(() => {});
      if (await node.isVisible().catch(() => false)) {
        try { await node.click({timeout:2500}); }
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
    {timeout:15000},
  );
  let screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'editor') {
    await page.waitForSelector('.codemirror-editor .cm-scroller', {timeout:15000});
    return;
  }
  if (screen === 'landing') {
    await closeTransient(page);
    await clickVisible(page, '[data-action="home"]');
    await page.waitForFunction(
      () => ['home','editor'].includes(document.documentElement.dataset.screen || ''),
      null,
      {timeout:15000},
    );
    screen = await page.locator('html').getAttribute('data-screen');
    if (screen === 'editor') {
      await page.waitForSelector('.codemirror-editor .cm-scroller', {timeout:15000});
      return;
    }
  }
  check(screen === 'home', `setup: expected home/editor, got ${screen}`);
  const blank = page.locator('.modal-layer [data-action="onboarding-blank"]:visible').first();
  if (await blank.count()) await blank.click({timeout:4000});
  else {
    await closeTransient(page);
    await clickVisible(page, '[data-action="new"]');
    const post = page.locator('.modal-layer [data-action="onboarding-blank"]:visible').first();
    if (await post.count()) await post.click({timeout:4000});
  }
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
  await page.waitForSelector('.codemirror-editor .cm-scroller', {timeout:15000});
}

async function active(page) {
  return page.evaluate(() => {
    const el = document.activeElement;
    return {
      tag:el?.tagName || '', id:el?.id || '', cls:String(el?.className || ''),
      action:el?.getAttribute?.('data-action') || '', mobile:el?.getAttribute?.('data-mobile') || '',
      aria:el?.getAttribute?.('aria-label') || '',
    };
  });
}

async function seriousAxe(page, label) {
  await sleep(180);
  const result = await new AxeBuilder({page})
    .withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa'])
    .analyze();
  const serious = result.violations.filter(v => v.impact === 'critical' || v.impact === 'serious');
  check(serious.length === 0, `${label}: serious axe violations: ${serious.map(v => `${v.id}(${v.nodes.length})`).join(', ')}`);
  return result.violations;
}

async function checkStaticRuntimeContract(page, name) {
  check(await page.locator('meta[name="manuscript-accessibility-contract"]').count() === 1, `${name}: P6 meta missing/duplicated`);
  check(await page.locator('meta[name="manuscript-accessibility-contract"]').getAttribute('content') === 'keyboard-accessibility-v1', `${name}: P6 meta content wrong`);
  for (const marker of [
    '#v430-p1-simplified-navigation','#v430-p2-compact-density','#v430-p3-focus-mode','#v430-p3-runtime',
    '#v430-p4-command-palette','#v430-p4-runtime','#v430-p5-mobile-first','#v430-p5-runtime',
    '#v430-p6-accessibility','#v430-p6-runtime',
  ]) check(await page.locator(marker).count() === 1, `${name}: missing/duplicated ${marker}`);
  check(await page.evaluate(() => window.__manuscriptV430P6?.version) === 'keyboard-accessibility-v1', `${name}: P6 runtime not initialized`);
}

async function checkSemantics(page, name) {
  await page.evaluate(() => window.__manuscriptV430P6?.refresh?.());
  await sleep(160);
  const findings = await page.evaluate(() => {
    const isVisible = el => {
      const s=getComputedStyle(el), r=el.getBoundingClientRect();
      return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
    };
    const labelledBy = el => (el.getAttribute('aria-labelledby')||'').split(/\s+/).filter(Boolean)
      .map(id => document.getElementById(id)?.textContent?.trim() || '').join(' ').trim();
    const nameFor = el => (el.getAttribute('aria-label') || labelledBy(el) || el.getAttribute('alt') || el.getAttribute('title') ||
      ((el.tagName==='INPUT'||el.tagName==='TEXTAREA') ? el.getAttribute('placeholder') : '') || el.textContent || '').replace(/\s+/g,' ').trim();
    const interactives = [...document.querySelectorAll('button,a[href],input,select,textarea,[role="button"],[role="tab"],[role="menuitem"],[tabindex]')].filter(isVisible);
    const ids=[...document.querySelectorAll('[id]')].map(el=>el.id).filter(Boolean); const counts={}; ids.forEach(id=>counts[id]=(counts[id]||0)+1);
    return {
      unnamed:interactives.filter(el=>!nameFor(el)).map(el=>el.outerHTML.slice(0,180)),
      positive:interactives.filter(el=>Number(el.getAttribute('tabindex'))>0).map(el=>el.outerHTML.slice(0,180)),
      hiddenFocusable:interactives.filter(el=>el.closest('[aria-hidden="true"]')).map(el=>el.outerHTML.slice(0,180)),
      duplicates:Object.entries(counts).filter(([,n])=>n>1),
    };
  });
  check(findings.unnamed.length === 0, `${name}: unnamed interactive controls ${JSON.stringify(findings.unnamed)}`);
  check(findings.positive.length === 0, `${name}: positive tabindex ${JSON.stringify(findings.positive)}`);
  check(findings.hiddenFocusable.length === 0, `${name}: focusable content under aria-hidden ${JSON.stringify(findings.hiddenFocusable)}`);
  check(findings.duplicates.length === 0, `${name}: duplicate ids ${JSON.stringify(findings.duplicates)}`);

  const preview = page.locator('#preview-scroll').first();
  if (await preview.count()) {
    check(await preview.getAttribute('tabindex') === '0', `${name}: preview scroll is not keyboard focusable`);
    check(await preview.getAttribute('role') === 'region', `${name}: preview scroll region semantics missing`);
    check((await preview.getAttribute('aria-label') || '').length > 0 || (await preview.getAttribute('aria-labelledby') || '').length > 0, `${name}: preview region has no accessible name`);
  }

  const splitters = page.locator('.splitter[role="separator"]');
  for (let i=0;i<await splitters.count();i+=1) {
    const splitter=splitters.nth(i);
    const value=Number(await splitter.getAttribute('aria-valuenow'));
    const min=Number(await splitter.getAttribute('aria-valuemin'));
    const max=Number(await splitter.getAttribute('aria-valuemax'));
    check(Number.isFinite(value), `${name}: splitter aria-valuenow missing`);
    check(value>=min && value<=max, `${name}: splitter aria-valuenow outside bounds ${value}/${min}-${max}`);
    check(await splitter.getAttribute('aria-orientation') === 'vertical', `${name}: splitter orientation missing`);
    check((await splitter.getAttribute('aria-valuetext') || '').includes('%'), `${name}: splitter value text missing`);
  }

  const workspaceButtons = page.locator('[data-workspace]');
  for (let i=0;i<await workspaceButtons.count();i+=1) {
    check(['true','false'].includes(await workspaceButtons.nth(i).getAttribute('aria-pressed')), `${name}: workspace mode missing aria-pressed`);
  }
}

async function cycleContained(page, root, count, name) {
  for (let i=0;i<count;i+=1) {
    await page.keyboard.press('Tab');
    const inside = await root.evaluate((node) => node.contains(document.activeElement));
    check(inside, `${name}: focus escaped after Tab ${i+1}: ${JSON.stringify(await active(page))}`);
  }
  for (let i=0;i<Math.min(count,6);i+=1) {
    await page.keyboard.press('Shift+Tab');
    const inside = await root.evaluate((node) => node.contains(document.activeElement));
    check(inside, `${name}: focus escaped after Shift+Tab ${i+1}: ${JSON.stringify(await active(page))}`);
  }
}

async function checkCommandKeyboard(page, name) {
  const editor = page.locator('.cm-content').first();
  await editor.focus();
  await page.keyboard.press('Control+k');
  const palette = page.locator('.command-layer .command-palette:visible').first();
  await palette.waitFor({state:'visible',timeout:5000});
  await sleep(180);
  check(await palette.getAttribute('role') === 'dialog', `${name}: command palette role lost`);
  check(await palette.getAttribute('aria-modal') === 'true', `${name}: command palette aria-modal lost`);
  check((await palette.getAttribute('aria-label') || '').length > 0, `${name}: command palette accessible name lost`);
  check((await active(page)).id === 'command-search', `${name}: Ctrl+K did not focus command search`);
  await cycleContained(page,palette,14,`${name}: command palette`);
  await seriousAxe(page, `${name}: command palette`);
  await page.keyboard.press('Escape');
  await page.locator('.command-layer').first().waitFor({state:'detached',timeout:5000}).catch(()=>{});
  await sleep(100);
  check((await active(page)).cls.includes('cm-content'), `${name}: Ctrl+K close did not restore editor focus ${JSON.stringify(await active(page))}`);
}

async function checkUtilityMenu(page, name) {
  const trigger = page.locator('.v430-utility-trigger:visible').first();
  if (!(await visible(trigger))) return;
  await trigger.focus();
  await page.keyboard.press('Enter');
  const menu = page.locator('#v430-utility-menu:visible').first();
  await menu.waitFor({state:'visible',timeout:3000});
  const items=menu.locator('[role="menuitem"]:visible');
  check(await items.count()>=3, `${name}: utility menu items missing`);
  check(await items.first().evaluate(el=>el===document.activeElement), `${name}: utility menu did not focus first item`);
  await page.keyboard.press('ArrowDown');
  check(await items.nth(1).evaluate(el=>el===document.activeElement), `${name}: ArrowDown did not move utility menu focus`);
  await page.keyboard.press('End');
  check(await items.last().evaluate(el=>el===document.activeElement), `${name}: End did not move to last utility item`);
  await page.keyboard.press('Home');
  check(await items.first().evaluate(el=>el===document.activeElement), `${name}: Home did not move to first utility item`);
  await page.keyboard.press('ArrowUp');
  check(await items.last().evaluate(el=>el===document.activeElement), `${name}: ArrowUp did not wrap utility item focus`);
  await page.keyboard.press('Escape');
  await sleep(90);
  check(!(await visible(menu)), `${name}: Escape did not close utility menu`);
  check(await trigger.evaluate(el=>el===document.activeElement), `${name}: utility Escape did not restore trigger focus`);
}

async function checkPublishDialog(page, name) {
  const publish = page.locator('[data-action="export"]:visible').first();
  check(await visible(publish), `${name}: visible publish/export action missing`);
  await publish.focus();
  await page.keyboard.press('Enter');
  const modal = page.locator('.modal-layer .modal:visible').first();
  await modal.waitFor({state:'visible',timeout:4000});
  await sleep(180);
  check(await modal.getAttribute('role') === 'dialog', `${name}: Publish role dialog missing`);
  check(await modal.getAttribute('aria-modal') === 'true', `${name}: Publish aria-modal missing`);
  check((await modal.getAttribute('aria-label') || '').length > 0 || (await modal.getAttribute('aria-labelledby') || '').length > 0, `${name}: Publish accessible name missing`);
  check(await modal.evaluate(node=>node.contains(document.activeElement)), `${name}: Publish initial focus outside dialog`);
  const focusableCount = await modal.locator('button:visible,a[href]:visible,input:visible,select:visible,textarea:visible,[tabindex]:visible').count();
  await cycleContained(page,modal,Math.max(8,focusableCount+3),`${name}: Publish`);
  await seriousAxe(page, `${name}: Publish`);
  await page.keyboard.press('Escape');
  await modal.waitFor({state:'detached',timeout:4000}).catch(async()=>{check(!(await visible(modal)),`${name}: Publish did not close with Escape`);});
  await sleep(100);
  check(await publish.evaluate(el=>el===document.activeElement), `${name}: Publish close did not restore origin ${JSON.stringify(await active(page))}`);
}

async function checkFocusMode(page, name) {
  const trigger = page.locator('.v430-focus-trigger:visible').first();
  if (!(await visible(trigger))) return;
  await trigger.focus();
  await page.keyboard.press('Enter');
  await page.waitForFunction(()=>document.documentElement.dataset.v430Focus==='true',null,{timeout:5000});
  await page.keyboard.press('Escape');
  await page.waitForFunction(()=>!document.documentElement.dataset.v430Focus,null,{timeout:5000});
  await sleep(80);
  check(await trigger.evaluate(el=>el===document.activeElement) || (await active(page)).cls.includes('cm-content'), `${name}: Focus Mode did not restore a logical origin`);
}

async function checkMobileSurface(page, name, selector, rootSelector, expectedLabel) {
  const origin=page.locator(selector).first();
  check(await visible(origin), `${name}: mobile origin ${selector} missing`);
  await origin.focus();
  await page.keyboard.press('Enter');
  const root=page.locator(`${rootSelector}:visible`).first();
  await root.waitFor({state:'visible',timeout:4000});
  await sleep(180);
  check(await root.getAttribute('role')==='dialog', `${name}: ${expectedLabel} mobile surface role missing`);
  check(await root.getAttribute('aria-modal')==='true', `${name}: ${expectedLabel} mobile surface aria-modal missing`);
  check((await root.getAttribute('aria-label') || await root.getAttribute('aria-labelledby') || '').length>0, `${name}: ${expectedLabel} mobile surface accessible name missing`);
  check(await root.evaluate(node=>node.contains(document.activeElement)), `${name}: ${expectedLabel} opening focus outside surface ${JSON.stringify(await active(page))}`);
  await cycleContained(page,root,10,`${name}: ${expectedLabel}`);
  await page.keyboard.press('Escape');
  await sleep(260);
  check(!(await root.isVisible().catch(()=>false)), `${name}: Escape did not close ${expectedLabel}`);
  check(await origin.evaluate(el=>el===document.activeElement), `${name}: ${expectedLabel} close did not restore origin ${JSON.stringify(await active(page))}`);
}

async function run(profile) {
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:profile.viewport,isMobile:!!profile.isMobile,hasTouch:!!profile.hasTouch,deviceScaleFactor:profile.isMobile?2:1});
  const page=await context.newPage();
  page.setDefaultTimeout(8000);
  const pageErrors=[];
  page.on('pageerror',error=>pageErrors.push(String(error)));
  try {
    await page.goto(baseURL,{waitUntil:'load',timeout:45000});
    await openEditor(page);
    await closeTransient(page);
    await sleep(180);
    await checkStaticRuntimeContract(page,profile.name);
    await checkSemantics(page,profile.name);
    await seriousAxe(page,`${profile.name}: editor baseline`);
    await checkCommandKeyboard(page,profile.name);
    await checkPublishDialog(page,profile.name);
    if (profile.viewport.width>=768) {
      await checkUtilityMenu(page,profile.name);
      await checkFocusMode(page,profile.name);
    } else if (profile.kind !== 'mobile-landscape') {
      await checkMobileSurface(page,profile.name,'.mobile-bottom-nav [data-action="workflow-content"]:visible','.left-panel','Add');
      await checkMobileSurface(page,profile.name,'.mobile-bottom-nav [data-mobile="style"]:visible','.inspector','Style');
    }
    check(pageErrors.length===0,`${profile.name}: page errors ${pageErrors.join(' | ')}`);
  } finally {
    await context.close();
    await browser.close();
  }
}

let passed=0;
for(const profile of profiles){
  process.stdout.write(`Certifying P6 ${profile.name}... `);
  try { await run(profile); passed+=1; console.log('PASS'); }
  catch(error){ console.log('FAIL'); console.error(error?.stack||error); process.exitCode=1; break; }
}
if(!process.exitCode) console.log(`V430-P6 accessibility certification PASS — ${passed}/${profiles.length} profiles`);
