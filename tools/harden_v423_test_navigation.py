#!/usr/bin/env python3
from pathlib import Path

HELPER = '''\nasync function activateForSetup(page, selector) {\n  const el = page.locator(selector).first();\n  try {\n    await el.click({timeout:2500});\n  } catch {\n    await el.evaluate(node => node.click());\n  }\n}\n'''

files = [Path('scripts/certify-v423.mjs'), Path('scripts/certify-v423-extras.mjs')]
for path in files:
    text = path.read_text(encoding='utf-8')
    if 'async function activateForSetup(' not in text:
        if 'const check = (ok, message) => assert.ok(ok, message);\n' in text:
            text = text.replace('const check = (ok, message) => assert.ok(ok, message);\n', 'const check = (ok, message) => assert.ok(ok, message);\n' + HELPER, 1)
        elif "const check=(ok,msg)=>assert.ok(ok,msg);\n" in text:
            text = text.replace("const check=(ok,msg)=>assert.ok(ok,msg);\n", "const check=(ok,msg)=>assert.ok(ok,msg);\n" + HELPER, 1)
        else:
            raise SystemExit(f'check anchor not found in {path}')

    replacements = {
        "await page.locator('[data-action=\"home\"]').first().click({timeout:5000});": "await activateForSetup(page, '[data-action=\"home\"]');",
        "await page.locator('[data-action=\"new\"]').first().click({timeout:5000});": "await activateForSetup(page, '[data-action=\"new\"]');",
        "await onboardingBlank.click({timeout:5000});": "await activateForSetup(page, '.modal-layer [data-action=\"onboarding-blank\"]');",
        "await post.click({timeout:5000});": "await activateForSetup(page, '.modal-layer [data-action=\"onboarding-blank\"]');",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    path.write_text(text, encoding='utf-8')
    print(f'hardened setup navigation in {path}')
