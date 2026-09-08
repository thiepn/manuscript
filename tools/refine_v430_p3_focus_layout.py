#!/usr/bin/env python3
from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

if 'id="v430-p3-focus-mode"' not in text:
    raise SystemExit('V430-P3 focus style missing; apply base P3 first')

old = '''  html[data-screen="editor"][data-v430-focus="true"] .editor-preview,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview.editor-only,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview.preview-only {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) !important;
    width: 100%;
  }

  html[data-screen="editor"][data-v430-focus="true"] .editor-pane,
  html[data-screen="editor"][data-v430-focus="true"] .editor-pane.mobile-hidden {
    display: flex !important;
    width: min(100%, 980px);
    max-width: 980px;
    min-width: 0;
    margin-inline: auto;
    border-right: 0 !important;
    box-shadow: none !important;
  }'''

new = '''  html[data-screen="editor"][data-v430-focus="true"] .editor-preview,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview.editor-only,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview.preview-only {
    display: flex !important;
    flex-direction: row !important;
    justify-content: center !important;
    align-items: stretch !important;
    grid-template-columns: none !important;
    width: 100% !important;
    min-width: 0 !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .editor-pane,
  html[data-screen="editor"][data-v430-focus="true"] .editor-pane.mobile-hidden {
    display: flex !important;
    flex: 1 1 auto !important;
    grid-column: auto !important;
    width: min(100%, 980px) !important;
    max-width: 980px !important;
    min-width: 0 !important;
    margin-inline: auto !important;
    border-right: 0 !important;
    box-shadow: none !important;
  }'''

if new in text:
    print('V430-P3 flex focus layout already refined')
    raise SystemExit(0)
if old not in text:
    raise SystemExit('Expected P3 focus layout block not found')

text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('Refined V430-P3 focus layout to a single centered flex editor')
