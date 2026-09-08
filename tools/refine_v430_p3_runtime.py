#!/usr/bin/env python3
from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

if 'id="v430-p3-runtime"' not in text:
    raise SystemExit('V430-P3 runtime missing; apply base P3 first')

old = """    if (active && (!media.matches || !editorReady() || !['editor','split'].includes(workspaceMode()))) {
      exit({ restoreFocus: false });
    }"""
new = """    if (active && (!media.matches || !editorReady())) {
      exit({ restoreFocus: false });
    }"""

if new in text:
    print('V430-P3 active-state refinement already applied')
    raise SystemExit(0)
if old not in text:
    raise SystemExit('Expected P3 active-state guard not found')

text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('Refined V430-P3 active focus state to survive responsive workspace-control changes')
