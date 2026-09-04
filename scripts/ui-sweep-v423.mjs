import { chromium } from 'playwright';
import fs from 'node:fs';

const baseURL = process.env.MANUSCRIPT_URL || 'http://127.0.0.1:4173/index.html';
const profiles = [
  {name:'desktop-wide',viewport:{width:1440,height:900}},
  {name:'desktop-compact',viewport:{width:1024,height:768}},
  {name:'tablet-edge',viewport:{width:768,height:1024},isMobile:true,hasTouch:true},
  {name:'mobile-portrait',viewport:{width:390,height:844},isMobile:true,hasTouch:true},
  {name:'mobile-narrow',viewport:{width:360,height:800},isMobile:true,hasTouch:true},
  {name:'mobile-small',viewport:{width:320,height:568},isMobile:true,hasTouch:true},
  {name:'mobile-landscape',viewport:{width:740,height:390},isMobile:true,hasTouch:true},
];

const report={generatedAt:new Date().toISOString(),baseURL,profiles:[],summary:{}};

async function closeModal(page){
  const layer=page.locator('.modal-layer').first();
  if(!(await layer.count())||!(await layer.isVisible().catch(()=>false)))return;
  const close=layer.locator('[data-action="modal-close"],.modal-close').first();
  if(await close.count())await close.click({timeout:5000});else await page.keyboard.press('Escape');
  await layer.waitFor({state:'detached',timeout:5000}).catch(async()=>{await page.keyboard.press('Escape');});
}

async function openHome(page){
  if(await page.locator('html').getAttribute('data-screen')==='landing'){
    await closeModal(page);
    await page.locator('[data-action="home"]').first().click({timeout:5000});
  }
  await page.waitForFunction(()=>document.documentElement.dataset.screen==='home');
}

async function openEditor(page){
  await openHome(page);
  const blank=page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if(await blank.count()&&await blank.isVisible().catch(()=>false))await blank.click({timeout:5000});
  else{
    await closeModal(page);
    await page.locator('[data-action="new"]').first().click({timeout:5000});
    const post=page.locator('.modal-layer [data-action="onboarding-blank"]').first();
    if(await post.count()&&await post.isVisible().catch(()=>false))await post.click({timeout:5000});
  }
  await page.waitForFunction(()=>document.documentElement.dataset.screen==='editor',null,{timeout:15000});
  await page.waitForSelector('.codemirror-editor .cm-scroller',{timeout:15000});
}

async function inspect(page,stage){
  await page.waitForTimeout(70);
  return page.evaluate(stage=>{
    const vw=document.documentElement.clientWidth,vh=document.documentElement.clientHeight;
    const screen=document.documentElement.dataset.screen||'';
    const modal=[...document.querySelectorAll('.modal-layer')].find(el=>{
      const s=getComputedStyle(el),r=el.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>1&&r.height>1;
    })||null;
    const issues=[];
    const visible=el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0&&r.width>.5&&r.height>.5;};
    const desc=el=>{if(!el)return'document';if(el.id)return'#'+el.id;let x=el.tagName.toLowerCase();if(el.classList.length)x+='.'+[...el.classList].slice(0,3).join('.');for(const a of['data-action','data-workspace','data-mobile','data-panel'])if(el.hasAttribute(a))x+=`[${a}="${el.getAttribute(a)}"]`;return x;};
    const add=(severity,code,message,el=null,data={})=>issues.push({severity,code,message,selector:desc(el),data});
    const inScope=el=>!modal||!!el.closest('.modal-layer');
    const scrollXAncestor=el=>{for(let p=el.parentElement;p;p=p.parentElement){const s=getComputedStyle(p);if(['auto','scroll'].includes(s.overflowX)&&p.scrollWidth>p.clientWidth+2)return true;}return false;};

    if(document.documentElement.scrollWidth>vw+2)add('high','ROOT_X_OVERFLOW',`Root width ${document.documentElement.scrollWidth}px exceeds ${vw}px`,document.documentElement);

    document.querySelectorAll('button,input,select,textarea,[role="button"]').forEach(el=>{
      if(!visible(el)||el.disabled||!inScope(el))return;
      const r=el.getBoundingClientRect();
      if((r.left<-2||r.right>vw+2)&&!scrollXAncestor(el))add('high','CONTROL_OFFSCREEN','Visible interactive control extends outside viewport',el,{left:r.left,right:r.right,width:r.width,vw});
      if(vw<768&&el.tagName==='BUTTON'&&r.width<30&&r.height<30)add('medium','TINY_TOUCH_TARGET','Visible mobile button is below 30×30px',el,{width:r.width,height:r.height});
      if(el.tagName==='BUTTON'&&(el.textContent||'').trim()&&el.scrollWidth>el.clientWidth+2&&!scrollXAncestor(el))add('medium','BUTTON_TEXT_CLIPPED','Visible button label is clipped',el,{clientWidth:el.clientWidth,scrollWidth:el.scrollWidth,text:(el.textContent||'').trim()});
    });

    if(screen==='editor'&&!modal){
      for(const sel of['.workspace','.main-stage','.editor-preview']){
        const el=document.querySelector(sel);if(el&&visible(el)&&el.scrollWidth>el.clientWidth+2)add('high','EDITOR_CONTAINER_X_OVERFLOW','Editor layout container overflows horizontally',el,{clientWidth:el.clientWidth,scrollWidth:el.scrollWidth});
      }
      for(const sel of['.editor-pane','.preview-pane','.preview-scroll','.native-editor-host','.codemirror-editor']){
        const el=document.querySelector(sel);if(el&&visible(el)){const r=el.getBoundingClientRect();if(r.height<60)add('high','COLLAPSED_EDITOR_SURFACE','Visible editor surface has unusably small height',el,{width:r.width,height:r.height});}
      }
      const left=document.querySelector('.left-panel');
      if(left&&visible(left)&&vw>=768&&vw<1200){const s=getComputedStyle(left),r=left.getBoundingClientRect();if(s.position!=='fixed')add('high','LEFT_PANEL_NOT_OVERLAY','Responsive left panel is consuming grid flow instead of overlaying',left,{position:s.position});if(r.left<-1||r.right>vw+1)add('high','LEFT_PANEL_OFFSCREEN','Responsive left panel exceeds viewport',left,{left:r.left,right:r.right,vw});}
      const split=document.querySelector('.editor-preview:not(.editor-only):not(.preview-only)');
      if(split&&visible(split)&&vw>=768&&vw<=900){const e=document.querySelector('.editor-pane'),p=document.querySelector('.preview-pane');if(!e||!p||!visible(e)||!visible(p))add('high','TABLET_SPLIT_INCOMPLETE','Tablet Split does not display both panes',split);else{const er=e.getBoundingClientRect(),pr=p.getBoundingClientRect();if(er.width<400||pr.width<400||er.height<140||pr.height<140)add('high','TABLET_SPLIT_UNUSABLE','Tablet Split panes are too small',split,{editor:{width:er.width,height:er.height},preview:{width:pr.width,height:pr.height}});}}
      if(vw<768){const nav=document.querySelector('.mobile-bottom-nav');if(!nav||!visible(nav))add('high','MOBILE_NAV_MISSING','Mobile bottom navigation is not visible');}
    }

    if(modal){
      const box=modal.querySelector('.modal');
      if(box&&visible(box)){const r=box.getBoundingClientRect();if(r.left<-2||r.right>vw+2||r.top<-2||r.bottom>vh+2)add('high','MODAL_OUTSIDE_VIEWPORT','Modal does not fit viewport',box,{left:r.left,right:r.right,top:r.top,bottom:r.bottom,vw,vh});}
      const foot=modal.querySelector('.modal-foot');
      if(foot&&visible(foot)&&foot.scrollWidth>foot.clientWidth+2)add('high','MODAL_FOOT_OVERFLOW','Modal footer overflows horizontally',foot,{clientWidth:foot.clientWidth,scrollWidth:foot.scrollWidth});
    }
    return {stage,screen,viewport:{width:vw,height:vh},issues};
  },stage);
}

async function runProfile(profile){
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:profile.viewport,isMobile:!!profile.isMobile,hasTouch:!!profile.hasTouch,deviceScaleFactor:profile.isMobile?2:1});
  const page=await context.newPage();page.setDefaultTimeout(7000);
  const stages=[],pageErrors=[],consoleErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  try{
    await page.goto(baseURL,{waitUntil:'load',timeout:45000});
    stages.push(await inspect(page,'landing'));
    if(await page.locator('.modal-layer').first().isVisible().catch(()=>false))stages.push(await inspect(page,'landing-modal'));
    await closeModal(page);await openHome(page);stages.push(await inspect(page,'home'));
    if(await page.locator('.modal-layer').first().isVisible().catch(()=>false)){stages.push(await inspect(page,'home-modal'));await closeModal(page);}
    await openEditor(page);stages.push(await inspect(page,'editor-default'));
    if(profile.viewport.width>=768){
      for(const mode of['editor','split','preview']){await page.locator(`[data-workspace="${mode}"]`).click();stages.push(await inspect(page,`workspace-${mode}`));}
      await page.locator('[data-workspace="split"]').click();
      for(const panel of['files','outline','search','insert','assets','references','diagnostics','history','templates','settings','help']){
        const btn=page.locator(`[data-panel="${panel}"]`).first();if(await btn.count()&&await btn.isVisible().catch(()=>false)){await btn.click();stages.push(await inspect(page,`panel-${panel}`));await closeModal(page);}
      }
    }else{
      for(const mode of['write','preview','write']){const b=page.locator(`[data-mobile="${mode}"]`).first();if(await b.count()){await b.click();stages.push(await inspect(page,`mobile-${mode}`));}}
      const style=page.locator('[data-mobile="style"]').first();if(await style.count()){await style.click();stages.push(await inspect(page,'mobile-format'));}
      const add=page.locator('.mobile-bottom-nav [data-action="workflow-content"]').first();if(await add.count()){await add.click();stages.push(await inspect(page,'mobile-add'));}
    }
    const theme=page.locator('[data-action="theme"]').first();if(await theme.count()&&await theme.isVisible().catch(()=>false)){await theme.click();stages.push(await inspect(page,'modal-theme'));await closeModal(page);}
    const exp=(profile.viewport.width<768?page.locator('.mobile-bottom-nav [data-action="export"]').first():page.locator('[data-action="export"]').first());if(await exp.count()&&await exp.isVisible().catch(()=>false)){await exp.click();stages.push(await inspect(page,'modal-export'));await closeModal(page);}
  }finally{await context.close();await browser.close();}
  const unique=[...new Map(stages.flatMap(s=>s.issues.map(i=>({...i,stage:s.stage}))).map(i=>[JSON.stringify([i.code,i.selector,i.stage,i.message]),i])).values()];
  return {...profile,stages,issues:unique,pageErrors,consoleErrors};
}

for(const p of profiles){process.stdout.write(`Sweeping ${p.name}... `);try{const r=await runProfile(p);report.profiles.push(r);console.log(`${r.issues.length} findings`);}catch(e){report.profiles.push({...p,fatal:String(e?.stack||e),stages:[],issues:[]});console.log('FATAL');}}
const all=report.profiles.flatMap(p=>p.issues||[]);report.summary={total:all.length,high:all.filter(i=>i.severity==='high').length,medium:all.filter(i=>i.severity==='medium').length,fatal:report.profiles.filter(p=>p.fatal).length};
fs.mkdirSync('diagnostics',{recursive:true});fs.writeFileSync('diagnostics/ui-sweep-v423.json',JSON.stringify(report,null,2));
let md=`# Manuscript UI sweep v4.2.3\n\n- High: ${report.summary.high}\n- Medium: ${report.summary.medium}\n- Fatal: ${report.summary.fatal}\n- Total: ${report.summary.total}\n\n`;for(const p of report.profiles){md+=`## ${p.name} — ${p.viewport.width}×${p.viewport.height}\n\n`;if(p.fatal)md+=`**FATAL:** ${p.fatal}\n\n`;else if(!p.issues.length)md+='No findings.\n\n';else for(const i of p.issues)md+=`- **${i.severity.toUpperCase()} ${i.code}** · ${i.stage} · \`${i.selector}\` — ${i.message} ${JSON.stringify(i.data||{})}\n`;}
fs.writeFileSync('diagnostics/ui-sweep-v423.md',md);
console.log(`UI sweep complete — ${report.summary.high} high, ${report.summary.medium} medium, ${report.summary.fatal} fatal`);
if(report.summary.total||report.summary.fatal)process.exitCode=1;
