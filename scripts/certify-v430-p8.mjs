import { chromium, firefox, webkit } from 'playwright';
import assert from 'node:assert/strict';

const baseURL=process.env.MANUSCRIPT_URL||'http://127.0.0.1:4173/index.html';
const check=(ok,msg)=>assert.ok(ok,msg);
const swURL=new URL('./sw.js',baseURL).href;

async function certifyEngine(name,browserType,viewport){
  const browser=await browserType.launch({headless:true});
  const context=await browser.newContext({viewport,serviceWorkers:'allow'});
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  try{
    await page.goto(baseURL,{waitUntil:'load',timeout:45000});
    check(await page.title()==='Manuscript v4.3.0 Stable',`${name}: document title mismatch`);
    const desc=await page.locator('meta[name="description"]').getAttribute('content');
    check(desc?.startsWith('Manuscript v4.3.0 Stable —'),`${name}: stable description mismatch`);
    check(await page.locator('meta[name="manuscript-release-contract"]').count()===1,`${name}: release contract missing/duplicated`);
    check(await page.locator('meta[name="manuscript-release-contract"]').getAttribute('content')==='v4.3.0-stable-certified-v1',`${name}: release contract value mismatch`);
    for(const marker of[
      '#v430-p1-simplified-navigation','#v430-p2-compact-density','#v430-p3-focus-mode','#v430-p3-runtime',
      '#v430-p4-command-palette','#v430-p4-runtime','#v430-p5-mobile-first','#v430-p5-runtime',
      '#v430-p6-accessibility','#v430-p6-runtime','#v430-p7-responsive-hardening','#v430-p7-runtime'
    ]) check(await page.locator(marker).count()===1,`${name}: inherited marker missing/duplicated ${marker}`);
    const swResponse=await context.request.get(swURL,{headers:{'cache-control':'no-cache'}});
    check(swResponse.ok(),`${name}: service-worker request failed ${swResponse.status()} ${swResponse.statusText()}`);
    const sw=await swResponse.text();
    check(sw.includes('`${CACHE_PREFIX}v4.3.0`'),`${name}: service-worker cache is not v4.3.0`);
    check(!sw.includes('`${CACHE_PREFIX}v4.2.3`'),`${name}: stale v4.2.3 service-worker cache remains`);
    check(errors.length===0,`${name}: page errors ${errors.join(' | ')}`);
  }finally{
    await context.close();
    await browser.close();
  }
}

async function offlineShell(){
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1024,height:768},serviceWorkers:'allow'});
  const page=await context.newPage();
  try{
    await page.goto(baseURL,{waitUntil:'load',timeout:45000});
    await page.evaluate(async()=>{
      const regs=await navigator.serviceWorker.getRegistrations();
      if(!regs.length){await navigator.serviceWorker.register('./sw.js');}
      await navigator.serviceWorker.ready;
    });
    await page.waitForFunction(async()=>{
      const keys=await caches.keys();
      return keys.includes('manuscript-shell-v4.3.0');
    },null,{timeout:10000});
    const keys=await page.evaluate(()=>caches.keys());
    check(keys.filter(k=>k.startsWith('manuscript-shell-')).every(k=>k==='manuscript-shell-v4.3.0'),`offline: stale Manuscript shell caches remain ${JSON.stringify(keys)}`);
    await context.setOffline(true);
    await page.reload({waitUntil:'domcontentloaded',timeout:15000});
    check(await page.title()==='Manuscript v4.3.0 Stable','offline: cached shell title mismatch');
  }finally{
    await context.setOffline(false).catch(()=>{});
    await context.close();
    await browser.close();
  }
}

const suites=[
  ['chromium desktop',()=>certifyEngine('chromium desktop',chromium,{width:1440,height:900})],
  ['chromium mobile',()=>certifyEngine('chromium mobile',chromium,{width:390,height:844})],
  ['firefox desktop',()=>certifyEngine('firefox desktop',firefox,{width:1024,height:768})],
  ['webkit mobile',()=>certifyEngine('webkit mobile',webkit,{width:390,height:844})],
  ['offline service-worker shell',offlineShell],
];
let passed=0;
for(const[name,fn]of suites){process.stdout.write(`Certifying P8 ${name}... `);try{await fn();passed++;console.log('PASS');}catch(e){console.log('FAIL');console.error(e?.stack||e);process.exitCode=1;break;}}
if(!process.exitCode)console.log(`V430-P8 stable release certification PASS — ${passed}/${suites.length} suites`);
