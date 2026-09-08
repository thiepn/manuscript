#!/usr/bin/env python3
from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

if 'id="v430-p3-focus-mode"' not in text or 'id="v430-p3-runtime"' not in text:
    raise SystemExit('V430-P3 focus contract missing; apply base P3 first')

layout_old = '''  html[data-screen="editor"][data-v430-focus="true"] .editor-preview,
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

layout_new = '''  html[data-screen="editor"][data-v430-focus="true"] .editor-preview,
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

  /* The inherited v4.2.2 tablet Split hotfix force-shows .mobile-hidden
     panes with a highly specific display:flex!important rule. Focus Mode
     intentionally preserves the underlying Split state, so beat that rule
     only while Focus is active instead of mutating workspace state. */
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview:not(.editor-only):not(.preview-only) > .preview-pane,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview:not(.editor-only):not(.preview-only) > .preview-pane.mobile-hidden,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview > .preview-pane.mobile-hidden {
    display: none !important;
    flex: 0 0 0 !important;
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    visibility: hidden !important;
    pointer-events: none !important;
    border-top: 0 !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .editor-preview:not(.editor-only):not(.preview-only) > .splitter,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview > .splitter {
    display: none !important;
    flex: 0 0 0 !important;
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    visibility: hidden !important;
    pointer-events: none !important;
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

runtime_old = """    if (active && (!media.matches || !editorReady() || !['editor','split'].includes(workspaceMode()))) {
      exit({ restoreFocus: false });
    }"""
runtime_new = """    if (active && (!media.matches || !editorReady())) {
      exit({ restoreFocus: false });
    }"""

changed = False

if layout_old in text:
    text = text.replace(layout_old, layout_new, 1)
    changed = True
elif layout_new not in text:
    raise SystemExit('Expected P3 focus layout block not found')

if runtime_old in text:
    text = text.replace(runtime_old, runtime_new, 1)
    changed = True
elif runtime_new not in text:
    raise SystemExit('Expected P3 active-state guard not found')

if not changed:
    print('V430-P3 focus layout and active-state refinements already applied')
    raise SystemExit(0)

path.write_text(text, encoding='utf-8')
print('Refined V430-P3 focus layout, tablet preview hiding, and active-state stability')
