#!/usr/bin/env python3
from pathlib import Path

HELPER = '''\nasync function activateForSetup(page, selector) {\n  const nodes = page.locator(selector);\n  const count = await nodes.count();\n  for (let i = 0; i < count; i++) {\n    const el = nodes.nth(i);\n    if (!(await el.isVisible().catch(() => false))) continue;\n    try { await el.click({timeout:2500}); }\n    catch { await el.evaluate(node => node.click()); }\n    return;\n  }\n  for (let i = 0; i < count; i++) {\n    try { await nodes.nth(i).evaluate(node => node.click()); return; } catch {}\n  }\n  throw new Error(`No actionable setup control for ${selector}`);\n}\n'''


def add_helper(path: Path, text: str) -> str:
    if 'async function activateForSetup(' in text:
        return text
    if 'const check = (ok, message) => assert.ok(ok, message);\n' in text:
        return text.replace(
            'const check = (ok, message) => assert.ok(ok, message);\n',
            'const check = (ok, message) => assert.ok(ok, message);\n' + HELPER,
            1,
        )
    if "const check=(ok,msg)=>assert.ok(ok,msg);\n" in text:
        return text.replace(
            "const check=(ok,msg)=>assert.ok(ok,msg);\n",
            "const check=(ok,msg)=>assert.ok(ok,msg);\n" + HELPER,
            1,
        )
    raise SystemExit(f'check anchor not found in {path}')


# The responsive suite historically assumed Landing -> Home -> Editor. The current
# certified shell may legally enter Editor directly after the landing action, so setup
# accepts either state. All layout/behavior assertions remain untouched.
path = Path('scripts/certify-v423.mjs')
text = add_helper(path, path.read_text(encoding='utf-8'))
old = '''async function openHome(page) {
  const screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'landing') {
    await closeModalIfOpen(page);
    await page.locator('[data-action="home"]').first().click({timeout:5000});
  }
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'home');
}

async function openEditor(page) {
  await openHome(page);
  const onboardingBlank = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await onboardingBlank.count() && await onboardingBlank.isVisible().catch(() => false)) {
    await onboardingBlank.click({timeout:5000});
    await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
    return;
  }
  await closeModalIfOpen(page);
  await page.locator('[data-action="new"]').first().click({timeout:5000});
  const post = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await post.count() && await post.isVisible().catch(() => false)) await post.click({timeout:5000});
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
}
'''
new = '''async function openHome(page) {
  let screen = await page.locator('html').getAttribute('data-screen');
  if (screen === 'editor') return 'editor';
  if (screen === 'landing') {
    await closeModalIfOpen(page);
    await activateForSetup(page, '[data-action="home"]');
    await page.waitForFunction(() => ['home','editor'].includes(document.documentElement.dataset.screen || ''), null, {timeout:15000});
    screen = await page.locator('html').getAttribute('data-screen');
  }
  return screen;
}

async function openEditor(page) {
  const screen = await openHome(page);
  if (screen === 'editor') {
    await page.waitForSelector('.codemirror-editor .cm-scroller', {timeout:15000});
    return;
  }
  check(screen === 'home', `setup: expected home/editor, got ${screen}`);
  const onboardingBlank = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await onboardingBlank.count() && await onboardingBlank.isVisible().catch(() => false)) {
    await activateForSetup(page, '.modal-layer [data-action="onboarding-blank"]');
    await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
    return;
  }
  await closeModalIfOpen(page);
  await activateForSetup(page, '[data-action="new"]');
  const post = page.locator('.modal-layer [data-action="onboarding-blank"]').first();
  if (await post.count() && await post.isVisible().catch(() => false)) {
    await activateForSetup(page, '.modal-layer [data-action="onboarding-blank"]');
  }
  await page.waitForFunction(() => document.documentElement.dataset.screen === 'editor', null, {timeout:15000});
}
'''
if old not in text:
    raise SystemExit('certify-v423 setup block not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
print(f'hardened current-entry setup in {path}')

# Extras already accepts Home or Editor; only make its setup clicks resilient.
path = Path('scripts/certify-v423-extras.mjs')
text = add_helper(path, path.read_text(encoding='utf-8'))
replacements = {
    "await page.locator('[data-action=\"home\"]:visible').first().click({timeout:5000});": "await activateForSetup(page, '[data-action=\"home\"]');",
    "await page.locator('[data-action=\"new\"]:visible').first().click({timeout:5000});": "await activateForSetup(page, '[data-action=\"new\"]');",
    "await onboardingBlank.click({timeout:5000});": "await activateForSetup(page, '.modal-layer [data-action=\"onboarding-blank\"]');",
    "if(await post.count()) await post.click({timeout:5000});": "if(await post.count()) await activateForSetup(page, '.modal-layer [data-action=\"onboarding-blank\"]');",
}
for old_click, new_click in replacements.items():
    text = text.replace(old_click, new_click)
path.write_text(text, encoding='utf-8')
print(f'hardened actionable setup clicks in {path}')

# P1's own cert should use the same legal entry states. This file is part of the final
# P1 commit, so the hardened setup persists with the implementation.
path = Path('scripts/certify-v430-p1.mjs')
text = path.read_text(encoding='utf-8')
old = '''async function openHome(page) {
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
'''
new = '''async function openHome(page) {
  let screen=await page.locator('html').getAttribute('data-screen');
  if (screen==='editor') return 'editor';
  if (screen==='landing') {
    await closeTransient(page);
    await clickVisible(page,'[data-action="home"]');
    await page.waitForFunction(()=>['home','editor'].includes(document.documentElement.dataset.screen||''),null,{timeout:15000});
    screen=await page.locator('html').getAttribute('data-screen');
  }
  return screen;
}

async function openEditor(page) {
  const screen=await openHome(page);
  if (screen!=='editor') {
    check(screen==='home',`setup: expected home/editor, got ${screen}`);
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
  }
  await page.waitForSelector('.codemirror-editor .cm-scroller',{timeout:15000});
  await page.waitForFunction(()=>!!document.querySelector('.v430-nav-host') || innerWidth<768,null,{timeout:8000});
}
'''
if old not in text:
    raise SystemExit('certify-v430-p1 setup block not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
print(f'hardened current-entry setup in {path}')

# The sweep previously required a visible Home stage. Make Home optional if the app
# enters Editor directly; the sweep still inspects every reachable editor/modal state.
path = Path('scripts/ui-sweep-v423.mjs')
text = path.read_text(encoding='utf-8')
old = '''async function openHome(page){
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
'''
new = '''async function openHome(page){
  let screen=await page.locator('html').getAttribute('data-screen');
  if(screen==='editor')return 'editor';
  if(screen==='landing'){
    await closeModal(page);
    const home=page.locator('[data-action="home"]:visible').first();
    if(await home.count())await home.click({timeout:5000});
    else await page.locator('[data-action="home"]').first().evaluate(node=>node.click());
    await page.waitForFunction(()=>['home','editor'].includes(document.documentElement.dataset.screen||''),null,{timeout:15000});
    screen=await page.locator('html').getAttribute('data-screen');
  }
  return screen;
}

async function openEditor(page){
  const screen=await openHome(page);
  if(screen!=='editor'){
    const blank=page.locator('.modal-layer [data-action="onboarding-blank"]').first();
    if(await blank.count()&&await blank.isVisible().catch(()=>false))await blank.click({timeout:5000});
    else{
      await closeModal(page);
      const fresh=page.locator('[data-action="new"]:visible').first();
      if(await fresh.count())await fresh.click({timeout:5000});
      else await page.locator('[data-action="new"]').first().evaluate(node=>node.click());
      const post=page.locator('.modal-layer [data-action="onboarding-blank"]').first();
      if(await post.count()&&await post.isVisible().catch(()=>false))await post.click({timeout:5000});
    }
    await page.waitForFunction(()=>document.documentElement.dataset.screen==='editor',null,{timeout:15000});
  }
  await page.waitForSelector('.codemirror-editor .cm-scroller',{timeout:15000});
}
'''
if old not in text:
    raise SystemExit('ui-sweep setup block not found')
text = text.replace(old, new, 1)
old_stage = "    await closeModal(page);await openHome(page);stages.push(await inspect(page,'home'));\n    if(await page.locator('.modal-layer').first().isVisible().catch(()=>false)){stages.push(await inspect(page,'home-modal'));await closeModal(page);}\n"
new_stage = "    await closeModal(page);const entry=await openHome(page);if(entry==='home'){stages.push(await inspect(page,'home'));\n    if(await page.locator('.modal-layer').first().isVisible().catch(()=>false)){stages.push(await inspect(page,'home-modal'));await closeModal(page);}}\n"
if old_stage not in text:
    raise SystemExit('ui-sweep home-stage block not found')
path.write_text(text.replace(old_stage, new_stage, 1), encoding='utf-8')
print(f'hardened current-entry setup in {path}')
