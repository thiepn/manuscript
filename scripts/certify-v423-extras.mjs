import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const baseURL=process.env.MANUSCRIPT_URL||'http://127.0.0.1:4173/index.html';
const check=(ok,msg)=>assert.ok(ok,msg);

async function closeModal(page){const l=page.locator('.modal-layer').first();if(!(await l.count())||!(await l.isVisible().catch(()=>false)))return;const c=l.locator('[data-action="modal-close"],.modal-close').first();if(await c.count())await c.click();else await page.keyboard.press('Escape');await l.waitFor({state:'detached',timeout:5000}).catch(()=>{});}
async function openHome(page){
  let screen=await page.locator('html').getAttribute('data-screen');
  if(screen==='landing'){
    await closeModal(page);
    screen=await page.locator('html').getAttribute('data-screen');
    if(screen==='landing'){
      const home=page.locator('[data-action="home"]:visible').first();
      if(await home.count()) await home.click({timeout:5000});
      else await page.evaluate(()=>document.querySelector('[data-action="home"]')?.click());
    }
  }
  await page.waitForFunction(()=>document.documentElement.dataset.screen==='home',null,{timeout:15000});
}
async function openEditor(page){await openHome(page);const b=page.locator('.modal-layer [data-action="onboarding-blank"]:visible').first();if(await b.count())await b.click();else{await closeModal(page);await page.locator('[data-action="new"]:visible').first().click();const p=page.locator('.modal-layer [data-action="onboarding-blank"]:visible').first();if(await p.count())await p.click();}await page.waitForFunction(()=>document.documentElement.dataset.screen==='editor',null,{timeout:15000});await page.waitForSelector('.codemirror-editor .cm-scroller',{timeout:15000});}
const fits=async locator=>locator.evaluate(el=>el.scrollWidth<=el.clientWidth+1);
const rect=async locator=>locator.evaluate(el=>{const r=el.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};});

async function desktopUtilityButtons(){
  const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:1440,height:900}});const page=await context.newPage();page.setDefaultTimeout(7000);await page.goto(baseURL,{waitUntil:'load'});try{
    await openEditor(page);
    for(const panel of['references','settings']){
      await page.locator(`[data-panel="${panel}"]`).first().click();await page.waitForTimeout(80);
      const actions=panel==='references'?['export-csl']:['request-persistence','backup-library','backup-restore-file'];
      for(const action of actions){
        const b=page.locator(`[data-action="${action}"]:visible`).first();
        check(await b.count()===1,`desktop: visible ${action} missing in ${panel}`);
        check(await fits(b),`desktop: ${action} label clipped`);
        const r=await rect(b);check(r.width>70&&r.height>=28,`desktop: ${action} unusable ${JSON.stringify(r)}`);
      }
      await page.locator(`[data-panel="${panel}"]`).first().click().catch(()=>{});
    }
  }finally{await context.close();await browser.close();}
}

async function tabletExport(){
  const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:768,height:1024},isMobile:true,hasTouch:true});const page=await context.newPage();page.setDefaultTimeout(7000);await page.goto(baseURL,{waitUntil:'load'});try{
    await openEditor(page);const b=page.locator('.appbar > .btn.primary[data-action="export"]').first();check(await b.count()===1,'tablet: appbar Export missing');check(await fits(b),'tablet: appbar Export label clipped');const r=await rect(b);check(r.width>=76,`tablet: Export width ${r.width}`);
  }finally{await context.close();await browser.close();}
}

async function mobileAdd(width,height){
  const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width,height},isMobile:true,hasTouch:true});const page=await context.newPage();page.setDefaultTimeout(7000);await page.goto(baseURL,{waitUntil:'load'});try{
    await openEditor(page);await page.locator('.mobile-bottom-nav [data-action="workflow-content"]:visible').click();await page.waitForTimeout(80);
    const panel=page.locator('.left-panel:visible').first();check(await panel.count()===1,`${width}: Add panel not visible`);const r=await rect(panel);check(r.width>=width-2,`${width}: Add panel width ${r.width}`);check(r.height>=Math.max(180,height-130),`${width}: Add panel height ${r.height}`);check((await panel.evaluate(el=>getComputedStyle(el).position))==='fixed',`${width}: Add panel not fixed overlay`);
  }finally{await context.close();await browser.close();}
}

async function landscapeOnboarding(){
  const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:740,height:390},isMobile:true,hasTouch:true});const page=await context.newPage();page.setDefaultTimeout(7000);await page.goto(baseURL,{waitUntil:'load'});try{
    const layer=page.locator('.modal-layer').first();if(await layer.count()&&await layer.isVisible().catch(()=>false)){const modal=layer.locator('.modal').first();const r=await rect(modal);check(r.left>=-1&&r.right<=741&&r.top>=-1&&r.bottom<=391,`landscape onboarding outside viewport ${JSON.stringify(r)}`);}
    await closeModal(page);await openHome(page);const homeModal=page.locator('.modal-layer').first();if(await homeModal.count()&&await homeModal.isVisible().catch(()=>false)){const r=await rect(homeModal.locator('.modal').first());check(r.left>=-1&&r.right<=741&&r.top>=-1&&r.bottom<=391,`landscape home modal outside viewport ${JSON.stringify(r)}`);}
  }finally{await context.close();await browser.close();}
}

await desktopUtilityButtons();console.log('PASS desktop utility labels');
await tabletExport();console.log('PASS tablet Export');
for(const [w,h] of [[390,844],[360,800],[320,568],[740,390]]){await mobileAdd(w,h);console.log(`PASS mobile Add ${w}x${h}`);}
await landscapeOnboarding();console.log('PASS landscape modal fit');
console.log('v4.2.3 extra UI certification PASS');
