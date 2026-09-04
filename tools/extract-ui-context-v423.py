#!/usr/bin/env python3
from pathlib import Path
import re

src = Path('index.html').read_text(encoding='utf-8')
needles = [
    '.appbar', '.toolbar', '.workspace-switcher', '.workspace', '.main-stage',
    '.editor-preview', '.preview-toolbar', '.page-position', '.left-panel', '.inspector',
    '.inspector-tabs', '.mobile-bottom-nav', '.mobile-nav-btn', '.modal-layer', '.modal-body',
    '.home-content', '.quick-actions', '.recent-grid', '.template-grid', '.landing-nav',
    '.btn{', '.icon-btn', '.rail-btn', '.doc-title',
    '@media (max-width:1199px)', '@media (max-width:900px)', '@media (max-width:767px)',
    '@media(max-width:767px)', 'v422-editor-layout-hotfix',
    'function renderEditor', 'function renderToolbar', 'function renderMobileNav',
    'function renderInspector', 'function modalContent', 'function renderHome', 'function renderLanding'
]

out = [f'bytes={len(src.encode("utf-8"))} chars={len(src)} lines={src.count(chr(10))+1}', '']
seen = set()
for needle in needles:
    matches = list(re.finditer(re.escape(needle), src, re.I))
    out.append(f'===== {needle} :: {len(matches)} matches =====')
    for i, m in enumerate(matches[:16], 1):
        start = max(0, m.start()-1400)
        end = min(len(src), m.end()+2200)
        bucket = (start//500, end//500)
        if bucket in seen:
            continue
        seen.add(bucket)
        line = src.count('\n', 0, m.start()) + 1
        out += [f'--- #{i} line={line} char={m.start()} ---', src[start:end], '']
    out.append('')
Path('diagnostics').mkdir(exist_ok=True)
Path('diagnostics/ui-source-context-v423.txt').write_text('\n'.join(out), encoding='utf-8')
print(f'wrote {len(out)} source-context blocks')
