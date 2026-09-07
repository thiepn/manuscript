import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  {name:'desktop-wide',viewport:{width:1440,height:900},kind:'desktop'},
  {name:'desktop-compact',viewport:{width:1024,height:768},kind:'compact'},
  {name:'tablet-edge',viewport:{width:768,height:1024},isMobile:true,hasTouch:true,kind:'tablet'},
  {name:'mobile-portrait',viewport:{width:390,height:844},isMobile:true,hasTouch:true,kind:'mobile'},
  {name:'mobile-small',viewport:{width:320,height:568},isMobile:true,hasTouch:true,kind:'mobile'},
  {name:'mobile-landscape',viewport:{width:740,height:390},isMobile:true,hasTouch:true,kind:'landscape'},
];

const check = (ok, message) => assert.ok(ok, message);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function rootFits(page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
}

async function rect(page, selector) {
  return page.locator(selector).first().evaluate(el => {
    const r = el.getBoundingClientRect();
    return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};
  });
}

async function hidden(page, selector) {
  return page.locator(selector).first().evaluate(el => {
    const s=getComputedStyle(el), r=el.getBoundingClientRect();
    return s.display==='none' || s.visibility==='hidden' || r.width<1 || r.height<1;
  });
}

async function clickVisible(page, selector) {
  const nodes = page.locator(selector);
  for (let i=0;i<await nodes.count();i++) {
    const node=nodes.nth(i);
    if (await node.isVisible().catch(()=>false)) {
      try { await node.click({timeout:4000}); }
      catch { await node.evaluate(el=>el.click()); }
      return node;
    }
  }
  throw new Error(`No visible element for ${selector}`);
}

async function closeTransient(page) {
  const menu=page.locator('#v430-utility-menu[data-open="true"]');
  if (await menu.count()) await page.keyboard.press('Escape').catch(()=>{});
  const layer=page.locator('.modal-layer').first();
  if (await layer.count() && await layer.isVisible().catch(()=>false)) {
    const close=layer.locator('[data-action="modal-close"],.modal-close').first();
    if (await close.count() && await close.isVisible().catch(()=>false)) await close.click({timeout:3000}).catch(()=>{});
    else await page.keyboard.press('Escape').catch(()=>{});
  }
}

async function openHome(page) {
  const screen=await page.locator('html').getAttribute('data-screen');
  if (screen==='landing') {
    await closeTransient(page);
    await clickVisible(page,'[data-action="home"]');
  }
  await page.waitForFunction(()=>document.documentElement.dataset.screen==='home',null,{timeout:10000});
}

async function openEditor(page) {
  await openHome(page);
  const blank=page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await blank.count() && await blank.isVisible().catch(()=>false)) {
    try { await blank.click({timeout:3000}); } catch { await blank.evaluate(el=>el.click()); }
  } else {
    await closeTransient(page);
    await clickVisible(page,'[data-action="new"]');
    const post=page.locator('.modal-layer [data-action="onboarding-blank"]').first();
    if (await post.count() && await post.isVisible().catch(()=>false)) {
      try { await post.click({timeout:3000}); } catch { await post.evaluate(el=>el.click()); }
    }
  }
  await page.waitForFunction(()=>document.documentElement.dataset.screen==='editor',null,{timeout:15000});
  await page.waitForSelector('.codemirror-editor .cm-scroller',{timeout:15000});
  await page.waitForFunction(()=>!!document.querySelector('.v430-nav-host') || innerWidth<768,null,{timeout:8000});
}

async function verifyContract(page,name) {
  check(await page.locator('#v430-p1-simplified-navigation').count()===1,`${name}: P1 style marker missing`);
  check(await page.locator('#v430-p1-runtime').count()===1,`${name}: P1 runtime marker missing`);
  const contract=await page.locator('meta[name="manuscript-writing-ui-contract"]').getAttribute('content');
  check(contract==='simplified-navigation-v1',`${name}: writing UI contract mismatch`);
  check(await page.locator('#v422-editor-layout-hotfix').count()===1,`${name}: v4.2.2 contract missing`);
  check(await page.locator('#v423-ui-hardening').count()===1,`${name}: v4.2.3 contract missing`);
  check(await rootFits(page),`${name}: root overflows`);
}

async function verifyModes(page,name) {
  for (const mode of ['editor','preview','split']) {
    await clickVisible(page,`[data-workspace="${mode}"]`);
    await sleep(70);
    const eHidden=await hidden(page,'.editor-pane');
    const pHidden=await hidden(page,'.preview-pane');
    if (mode==='editor') check(!eHidden&&pHidden,`${name}: Write exclusivity failed`);
    if (mode==='preview') check(eHidden&&!pHidden,`${name}: Preview exclusivity failed`);
    if (mode==='split') check(!eHidden&&!pHidden,`${name}: Split panes not both visible`);
    check(await rootFits(page),`${name}: overflow in ${mode}`);
  }
}

async function openUtilityMenu(page,name) {
  await closeTransient(page);
  const trigger=page.locator('.v430-utility-trigger:visible').first();
  check(await trigger.count()===1 && await trigger.isVisible(),`${name}: More tools trigger unavailable`);
  await trigger.click();
  const menu=page.locator('#v430-utility-menu[data-open="true"]');
  await menu.waitFor({state:'visible',timeout:4000});
  const box=await rect(page,'#v430-utility-menu');
  const viewport=await page.evaluate(()=>({w:innerWidth,h:innerHeight}));
  check(box.left>=-1&&box.right<=viewport.w+1&&box.top>=-1&&box.bottom<=viewport.h+1,`${name}: utility menu outside viewport ${JSON.stringify({box,viewport})}`);
  check(await trigger.getAttribute('aria-expanded')==='true',`${name}: utility trigger state not exposed`);
}

async function verifyNavigation(page,name) {
  const nav=page.locator('.v430-nav-host').first();
  check(await nav.count()===1 && await nav.isVisible(),`${name}: simplified nav host missing`);
  const expectedGroups=['document','add','review'];
  for (const group of expectedGroups) {
    check(await page.locator(`.v430-nav-host .v430-nav-item[data-v430-group="${group}"]`).count()>0,`${name}: ${group} group missing`);
  }

  for (const id of ['files','outline','search','insert','assets','references','diagnostics','history']) {
    const selector=`.v430-nav-host [data-panel="${id}"]`;
    if (await page.locator(selector).count()) {
      await clickVisible(page,selector);
      await sleep(60);
      check(await rootFits(page),`${name}: overflow opening ${id}`);
    }
  }

  for (const id of ['templates','settings','help']) {
    await openUtilityMenu(page,name);
    const item=page.locator(`#v430-utility-menu [data-v430-utility-item="${id}"]`).first();
    check(await item.count()===1 && await item.isVisible(),`${name}: ${id} not consolidated in More tools`);
    await item.click();
    await sleep(60);
    check(await rootFits(page),`${name}: overflow opening utility ${id}`);
    await closeTransient(page);
  }

  await openUtilityMenu(page,name);
  const theme=page.locator('#v430-utility-menu [data-v430-utility-proxy="theme"]').first();
  check(await theme.count()===1 && await theme.isVisible(),`${name}: theme proxy missing`);
  await theme.click();
  await sleep(80);
  const modal=page.locator('.modal-layer').first();
  check(await modal.count()===1 && await modal.isVisible().catch(()=>false),`${name}: theme surface did not open`);
  await closeTransient(page);

  const exportButton=await clickVisible(page,'[data-action="export"]');
  check(await exportButton.isVisible(),`${name}: Export not persistently reachable`);
  await sleep(80);
  await closeTransient(page);
}

async function verifyCompact(page,name) {
  await clickVisible(page,'[data-workspace="split"]');
  await clickVisible(page,'.v430-nav-host [data-panel="diagnostics"]');
  await sleep(80);
  const position=await page.locator('.left-panel').first().evaluate(el=>getComputedStyle(el).position);
  check(position==='fixed',`${name}: compact left panel no longer overlay-fixed`);
  check(await rootFits(page),`${name}: compact panel causes root overflow`);
}

async function verifyTablet(page,name) {
  await clickVisible(page,'[data-workspace="split"]');
  await sleep(80);
  const e=await rect(page,'.editor-pane'), p=await rect(page,'.preview-pane');
  check(e.width>500&&p.width>500&&e.height>240&&p.height>240,`${name}: tablet Split collapsed ${JSON.stringify({e,p})}`);
  check(Math.abs(e.top-p.top)>100,`${name}: tablet Split is not stacked`);
  await clickVisible(page,'.v430-nav-host [data-panel="insert"]');
  await sleep(70);
  const position=await page.locator('.left-panel').first().evaluate(el=>getComputedStyle(el).position);
  check(position==='fixed',`${name}: tablet panel is not overlay-fixed`);
  check(await rootFits(page),`${name}: tablet overflow`);
  await closeTransient(page);
  await clickVisible(page,'[data-action="export"]');
  await sleep(70);
  const modal=await rect(page,'.modal-layer .modal');
  const viewport=await page.evaluate(()=>({w:innerWidth,h:innerHeight}));
  check(modal.left>=-1&&modal.right<=viewport.w+1&&modal.top>=-1&&modal.bottom<=viewport.h+1,`${name}: Export modal outside viewport`);
  await closeTransient(page);
}

async function verifyMobile(page,name,landscape=false) {
  const nav=page.locator('.mobile-bottom-nav').first();
  check(await nav.count()===1 && await nav.isVisible(),`${name}: existing mobile bottom nav missing`);
  check(!(await page.locator('.v430-utility-trigger').first().isVisible().catch(()=>false)),`${name}: desktop More tools leaked onto mobile`);
  for (const mode of ['write','preview','write']) {
    await clickVisible(page,`[data-mobile="${mode}"]`);
    await sleep(60);
    check(await rootFits(page),`${name}: mobile overflow after ${mode}`);
  }
  if (!landscape) {
    const style=page.locator('[data-mobile="style"]').first();
    if (await style.count() && await style.isVisible().catch(()=>false)) {
      await style.click(); await sleep(60); check(await rootFits(page),`${name}: Style overlay overflow`);
    }
    await closeTransient(page);
    const add=page.locator('.mobile-bottom-nav [data-action="workflow-content"]').first();
    if (await add.count() && await add.isVisible().catch(()=>false)) {
      await add.click(); await sleep(60); check(await rootFits(page),`${name}: Add overlay overflow`);
    }
    await closeTransient(page);
  }
  const exp=page.locator('.mobile-bottom-nav [data-action="export"]').first();
  if (await exp.count() && await exp.isVisible().catch(()=>false)) {
    await exp.click(); await sleep(70);
    const box=page.locator('.modal-layer .modal').first();
    if (await box.count() && await box.isVisible().catch(()=>false)) {
      const r=await rect(page,'.modal-layer .modal');
      const viewport=await page.evaluate(()=>({w:innerWidth,h:innerHeight}));
      check(r.left>=-1&&r.right<=viewport.w+1&&r.top>=-1&&r.bottom<=viewport.h+1,`${name}: mobile Export modal outside viewport`);
    }
    await closeTransient(page);
  }
}

async function run(profile) {
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:profile.viewport,isMobile:!!profile.isMobile,hasTouch:!!profile.hasTouch,deviceScaleFactor:profile.isMobile?2:1});
  const page=await context.newPage();
  page.setDefaultTimeout(7000);
  const pageErrors=[],consoleErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  try {
    await page.goto(baseURL,{waitUntil:'load',timeout:45000});
    await verifyContract(page,profile.name);
    await openEditor(page);
    await verifyContract(page,profile.name);
    if (profile.kind==='desktop') { await verifyNavigation(page,profile.name); await verifyModes(page,profile.name); }
    if (profile.kind==='compact') { await verifyNavigation(page,profile.name); await verifyModes(page,profile.name); await verifyCompact(page,profile.name); }
    if (profile.kind==='tablet') { await verifyNavigation(page,profile.name); await verifyTablet(page,profile.name); }
    if (profile.kind==='mobile') await verifyMobile(page,profile.name,false);
    if (profile.kind==='landscape') await verifyMobile(page,profile.name,true);
    check(await rootFits(page),`${profile.name}: final root overflow`);
    check(pageErrors.length===0,`${profile.name}: page errors ${pageErrors.join(' | ')}`);
    const serious=consoleErrors.filter(x=>!/favicon|source map|deprecated/i.test(x));
    check(serious.length===0,`${profile.name}: console errors ${serious.join(' | ')}`);
  } finally { await context.close(); await browser.close(); }
}

let passed=0;
for (const profile of profiles) {
  process.stdout.write(`Certifying P1 ${profile.name}... `);
  try { await run(profile); passed++; console.log('PASS'); }
  catch (error) { console.log('FAIL'); console.error(error?.stack||error); process.exitCode=1; break; }
}
if (!process.exitCode) console.log(`V430-P1 certification PASS — ${passed}/${profiles.length} profiles`);
