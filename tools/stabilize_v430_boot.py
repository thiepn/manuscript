#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [
    Path('scripts/certify-v423.mjs'),
    Path('scripts/certify-v423-extras.mjs'),
    Path('scripts/certify-v430-p1.mjs'),
    Path('scripts/ui-sweep-v423.mjs'),
]

WAIT = "await page.waitForFunction(()=>['landing','home','editor'].includes(document.documentElement.dataset.screen||''),null,{timeout:15000});"

for path in TARGETS:
    text = path.read_text(encoding='utf-8')
    match = re.search(r'async function openHome\(page\)\s*\{\n(?P<indent>[ \t]*)', text)
    if not match:
        raise SystemExit(f'openHome setup anchor missing in {path}')
    body_preview = text[match.end():match.end()+260]
    if WAIT in body_preview or 'await settleBoot(page);' in body_preview:
        print(f'boot wait already present in {path}')
        continue
    indent = match.group('indent')
    insertion = match.group(0) + indent + WAIT + '\n' + indent
    text = text[:match.start()] + insertion + text[match.end():]
    path.write_text(text, encoding='utf-8')
    print(f'added deterministic boot wait to {path}')
