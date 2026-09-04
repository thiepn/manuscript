import { chromium } from 'playwright';
import fs from 'node:fs';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  {name:'desktop-wide', viewport:{width:1440,height:900}},
  {name:'desktop-compact', viewport:{width:1024,height:768}},
  {name:'tablet-edge', viewport:{width:768,height:1024}, isMobile:true, hasTouch:true},
  {name:'mobile-portrait', viewport:{width:390,height:844}, isMobile:true, hasTouch:true},
  {name:'mobile-narrow', viewport:{width:360,height:800}, isMobile:true, hasTouch:true},
  {name:'mobile-small', viewport:{width:320,height:568}, isMobile:true, hasTouch:true},
  {name:'mobile-landscape', viewport:{width:740,height:390}, isMobile:true, hasTouch:true},
];

const report = { generatedAt:new Date().toISOString(), baseURL, profiles:[], summary:{} };

const uniq = arr => [...new Map(arr.map(x => [JSON.stringify([x.code,x.selector,x.message]),x])).values()];

async function closeModalIfOpen(page) {
  const layer = page.locator('.modal-layer').first();
  if (!(await layer.count()) || !(await layer.isVisible().catch(() => false))) return;
  const close = layer.locator('[data-action="modal-close"],.modal-close').first();
  if (await close.count()) await close.click({timeout:5000});
  else await page.keyboard.press('Escape');
  await layer.waitFor({state:'detached',timeout:5000}).catch(async()=>{await page.keyboard.press('Escape');});
}

async function openHome(page) {
  const screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'landing') await page.locator('[data-action="home"]').first().click();
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'home');
}

async function openEditor(page) {
  await openHome(page);
  const onboardingBlank = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await onboardingBlank.count() && await onboardingBlank.isVisible().catch(()=>false)) {
    await onboardingBlank.click({timeout:5000});
    await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
    return;
  }
  await closeModalIfOpen(page);
  await page.locator('[data-action="new"]').first().click({timeout:5000});
  const post = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await post.count() && await post.isVisible().catch(()=>false)) await post.click({timeout:5000});
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
}

async function auditStage(page, stage, mobile) {
  const result = await page.evaluate(({stage,mobile}) => {
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;
    const issues = [];
    const note = (severity,code,message,el=null,data={}) => issues.push({severity,code,message,selector:el ? describe(el) : '',data});
    const visible = el => {
      const s=getComputedStyle(el), r=el.getBoundingClientRect();
      return s.display!=='none' && s.visibility!=='hidden' && Number(s.opacity)!==0 && r.width>0.5 && r.height>0.5;
    };
    const describe = el => {
      if (!el) return '';
      if (el.id) return '#'+el.id;
      let s=el.tagName.toLowerCase();
      if (el.classList?.length) s+='.'+[...el.classList].slice(0,3).join('.');
      for (const a of ['data-action','data-workspace','data-mobile','data-panel','data-inspector','data-preview']) if (el.hasAttribute?.(a)) s+=`[${a}="${el.getAttribute(a)}"]`;
      return s;
    };
    const hasXScrollAncestor = el => {
      for(let p=el.parentElement;p;p=p.parentElement){const s=getComputedStyle(p);if(['auto','scroll'].includes(s.overflowX)&&p.scrollWidth>p.clientWidth+2)return true;}
      return false;
    };

    const rootOverflow = document.documentElement.scrollWidth - vw;
    if (rootOverflow > 2) note('high','ROOT_X_OVERFLOW',`Root is ${rootOverflow}px wider than viewport`,document.documentElement,{scrollWidth:document.documentElement.scrollWidth,vw});

    document.querySelectorAll('button,input,select,textarea,[role="button"]').forEach(el => {
      if (!visible(el) || el.disabled) return;
      const r=el.getBoundingClientRect();
      if ((r.left < -2 || r.right > vw+2) && !hasXScrollAncestor(el)) note('high','CONTROL_OFFSCREEN','Interactive control extends outside viewport',el,{rect:{left:r.left,right:r.right,width:r.width},vw});
      if (mobile && el.tagName==='BUTTON' && r.width < 30 && r.height < 30) note('medium','TINY_TOUCH_TARGET','Visible button is smaller than 30×30px',el,{width:r.width,height:r.height});
      const s=getComputedStyle(el);
      if ((s.overflowX==='hidden'||s.overflow==='hidden') && el.scrollWidth>el.clientWidth+3 && !el.classList.contains('doc-title')) note('medium','CONTROL_TEXT_CLIPPED','Control content is horizontally clipped',el,{clientWidth:el.clientWidth,scrollWidth:el.scrollWidth});
    });

    document.querySelectorAll('.appbar,.toolbar,.mobile-bottom-nav,.left-panel,.inspector,.modal,.modal-body,.workspace,.main-stage,.editor-preview,.editor-pane,.preview-pane,.preview-scroll,.native-editor-host,.codemirror-editor,.cm-scroller,.home-content,.landing-screen').forEach(el => {
      if (!visible(el)) return;
      const r=el.getBoundingClientRect(), s=getComputedStyle(el);
      if ((s.position==='fixed'||s.position==='sticky') && (r.left < -2 || r.right > vw+2 || r.top < -2 || r.bottom > vh+2)) note('high','FIXED_SURFACE_OFFSCREEN','Fixed/sticky surface extends outside viewport',el,{rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom},vw,vh});
      if (['.editor-pane','.preview-pane','.preview-scroll','.native-editor-host','.codemirror-editor','.cm-scroller'].some(sel=>el.matches(sel)) && document.documentElement.dataset.screen==='editor' && r.height < 60) note('high','COLLAPSED_EDITOR_SURFACE','Editor/preview surface has unusably small height',el,{height:r.height,width:r.width});
    });

    const modal=document.querySelector('.modal-layer .modal');
    if (modal && visible(modal)) {
      const r=modal.getBoundingClientRect();
      if (r.width > vw+2 || r.height > vh+2 || r.left < -2 || r.top < -2) note('high','MODAL_OUTSIDE_VIEWPORT','Modal does not fit viewport',modal,{rect:{left:r.left,top:r.top,width:r.width,height:r.height},vw,vh});
      const body=modal.querySelector('.modal-body');
      if (body && visible(body) && body.scrollHeight>body.clientHeight+2 && !['auto','scroll'].includes(getComputedStyle(body).overflowY)) note('high','MODAL_NOT_SCROLLABLE','Overflowing modal body is not scrollable',body,{clientHeight:body.clientHeight,scrollHeight:body.scrollHeight});
    }

    const appbar=document.querySelector('.appbar');
    if (appbar && visible(appbar)) {
      const controls=[...appbar.querySelectorAll('button,input,select')].filter(visible).map(el=>({el,r:el.getBoundingClientRect()}));
      for(let i=0;i<controls.length;i++) for(let j=i+1;j<controls.length;j++) {
        const a=controls[i],b=controls[j];
        const overlap=Math.min(a.r.right,b.r.right)-Math.max(a.r.left,b.r.left);
        const vo=Math.min(a.r.bottom,b.r.bottom)-Math.max(a.r.top,b.r.top);
        if(overlap>3&&vo>3) note('high','APPBAR_CONTROL_OVERLAP','App-bar controls overlap',a.el,{with:describe(b.el),overlapX:overlap,overlapY:vo});
      }
    }

    if (mobile && document.documentElement.dataset.screen==='editor') {
      const nav=document.querySelector('.mobile-bottom-nav');
      if (!nav || !visible(nav)) note('high','MOBILE_NAV_MISSING','Mobile editor navigation is not visible');
      const toolbar=document.querySelector('.toolbar');
      if (toolbar && visible(toolbar) && toolbar.scrollWidth>toolbar.clientWidth+8 && !['auto','scroll'].includes(getComputedStyle(toolbar).overflowX)) note('high','MOBILE_TOOLBAR_CLIPPED','Mobile toolbar overflows without horizontal scrolling',toolbar,{clientWidth:toolbar.clientWidth,scrollWidth:toolbar.scrollWidth});
    }

    return {stage,screen:document.documentElement.dataset.screen||'',theme:document.documentElement.dataset.theme||'',viewport:{width:vw,height:vh},issues};
  }, {stage,mobile});
  return result;
}

async function runProfile(profile) {
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:profile.viewport,isMobile:!!profile.isMobile,hasTouch:!!profile.hasTouch,deviceScaleFactor:profile.isMobile?2:1});
  const page=await context.newPage();
  page.setDefaultTimeout(7000);
  const stages=[];
  const pageErrors=[]; const consoleErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  try {
    await page.goto(baseURL,{waitUntil:'load',timeout:45000});
    await page.waitForTimeout(300);
    stages.push(await auditStage(page,'landing',!!profile.isMobile));

    const onboarding=page.locator('.modal-layer').first();
    if(await onboarding.count()&&await onboarding.isVisible().catch(()=>false)) stages.push(await auditStage(page,'landing-modal',!!profile.isMobile));
    await closeModalIfOpen(page);
    await openHome(page);
    stages.push(await auditStage(page,'home',!!profile.isMobile));

    await openEditor(page);
    await page.waitForSelector('.codemirror-editor .cm-scroller',{timeout:15000});
    stages.push(await auditStage(page,'editor-default',!!profile.isMobile));

    if(profile.viewport.width>=768){
      for(const mode of ['editor','split','preview']){
        await page.locator(`[data-workspace="${mode}"]`).click();
        await page.waitForTimeout(80);
        stages.push(await auditStage(page,`workspace-${mode}`,false));
      }
      await page.locator('[data-workspace="split"]').click();
      for(const panel of ['files','outline','search','insert','assets','references','diagnostics','history','templates','settings','help']){
        const btn=page.locator(`[data-panel="${panel}"]`).first();
        if(await btn.count() && await btn.isVisible().catch(()=>false)){
          await btn.click(); await page.waitForTimeout(60);
          stages.push(await auditStage(page,`panel-${panel}`,false));
        }
      }
      const theme=page.locator('[data-action="theme"]').first();
      if(await theme.count()){await theme.click();await page.waitForTimeout(50);stages.push(await auditStage(page,'modal-theme',false));await closeModalIfOpen(page);}
      const exp=page.locator('[data-action="export"]').first();
      if(await exp.count()){await exp.click();await page.waitForTimeout(80);stages.push(await auditStage(page,'modal-export',false));await closeModalIfOpen(page);}
    } else {
      for(const mode of ['write','preview','write']){
        const btn=page.locator(`[data-mobile="${mode}"]`).first();
        if(await btn.count()){await btn.click();await page.waitForTimeout(70);stages.push(await auditStage(page,`mobile-${mode}`,true));}
      }
      const style=page.locator('[data-mobile="style"]').first();
      if(await style.count()){await style.click();await page.waitForTimeout(70);stages.push(await auditStage(page,'mobile-format',true));}
      const add=page.locator('[data-action="workflow-content"]').first();
      if(await add.count()){await add.click();await page.waitForTimeout(70);stages.push(await auditStage(page,'mobile-add',true));}
      const exp=page.locator('.mobile-bottom-nav [data-action="export"]').first();
      if(await exp.count()){await exp.click();await page.waitForTimeout(80);stages.push(await auditStage(page,'mobile-export-modal',true));await closeModalIfOpen(page);}
      const theme=page.locator('[data-action="theme"]').first();
      if(await theme.count() && await theme.isVisible().catch(()=>false)){await theme.click();await page.waitForTimeout(50);stages.push(await auditStage(page,'mobile-theme-modal',true));await closeModalIfOpen(page);}
    }
  } finally {
    await context.close(); await browser.close();
  }
  const issues=uniq(stages.flatMap(s=>s.issues.map(i=>({...i,stage:s.stage}))));
  return {...profile,stages,issues,pageErrors,consoleErrors};
}

for(const profile of profiles){
  process.stdout.write(`Auditing ${profile.name}... `);
  try { const r=await runProfile(profile); report.profiles.push(r); console.log(`${r.issues.length} issues`); }
  catch(e){ report.profiles.push({...profile,fatal:String(e?.stack||e),stages:[],issues:[]}); console.log('FATAL'); }
}

const all=report.profiles.flatMap(p=>p.issues||[]);
report.summary={total:all.length,high:all.filter(i=>i.severity==='high').length,medium:all.filter(i=>i.severity==='medium').length,fatal:report.profiles.filter(p=>p.fatal).length};
fs.mkdirSync('diagnostics',{recursive:true});
fs.writeFileSync('diagnostics/ui-audit-v423.json',JSON.stringify(report,null,2));
let md=`# Manuscript UI audit v4.2.3\n\nGenerated: ${report.generatedAt}\n\n## Summary\n\n- High: ${report.summary.high}\n- Medium: ${report.summary.medium}\n- Fatal profile failures: ${report.summary.fatal}\n- Total unique findings: ${report.summary.total}\n\n`;
for(const p of report.profiles){md+=`## ${p.name} — ${p.viewport.width}×${p.viewport.height}\n\n`;if(p.fatal){md+=`**FATAL:** ${p.fatal}\n\n`;continue;}if(!p.issues.length){md+='No findings.\n\n';continue;}for(const i of p.issues) md+=`- **${i.severity.toUpperCase()} ${i.code}** · ${i.stage} · \`${i.selector||'document'}\` — ${i.message}${i.data?` · ${JSON.stringify(i.data)}`:''}\n`;md+='\n';}
fs.writeFileSync('diagnostics/ui-audit-v423.md',md);
console.log(`UI audit complete: ${report.summary.high} high, ${report.summary.medium} medium, ${report.summary.fatal} fatal`);
