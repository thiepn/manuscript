#!/usr/bin/env python3
from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

STYLE_ID = 'v430-p2-compact-density'
META_NAME = 'manuscript-density-ui-contract'
CONTRACT = 'compact-density-v1'

if f'id="{STYLE_ID}"' in text:
    print('V430-P2 compact density contract already applied')
    raise SystemExit(0)

if 'id="v430-p1-simplified-navigation"' not in text:
    raise SystemExit('V430-P1 contract missing; P2 must build on certified P1')
if '</head>' not in text:
    raise SystemExit('head closing anchor missing')

injection = r'''
<meta name="manuscript-density-ui-contract" content="compact-density-v1">
<style id="v430-p2-compact-density">
/* V430-P2 — Compact Views & Information Density
   Deliberately limited to non-mobile secondary/editor chrome. Writing
   typography, document rendering, modals, mobile touch surfaces, and the
   certified V430-P1 navigation host retain their existing geometry. */
@media (min-width: 768px) {
  html[data-screen="editor"] #v430-utility-menu {
    padding: 4px !important;
    gap: 2px !important;
  }

  html[data-screen="editor"] #v430-utility-menu button,
  html[data-screen="editor"] #v430-utility-menu [role="menuitem"] {
    min-height: 32px !important;
    padding: 6px 10px !important;
  }

  html[data-screen="editor"] .left-panel,
  html[data-screen="editor"] .inspector {
    --v430-density-control-height: 30px;
    --v430-density-section-gap: 6px;
  }

  html[data-screen="editor"] .left-panel h2,
  html[data-screen="editor"] .left-panel h3,
  html[data-screen="editor"] .left-panel h4,
  html[data-screen="editor"] .inspector h2,
  html[data-screen="editor"] .inspector h3,
  html[data-screen="editor"] .inspector h4 {
    margin-top: 6px !important;
    margin-bottom: 6px !important;
  }

  html[data-screen="editor"] .left-panel ul,
  html[data-screen="editor"] .left-panel ol,
  html[data-screen="editor"] .inspector ul,
  html[data-screen="editor"] .inspector ol {
    margin-top: 4px !important;
    margin-bottom: 4px !important;
  }

  html[data-screen="editor"] .left-panel li,
  html[data-screen="editor"] .left-panel [role="listitem"],
  html[data-screen="editor"] .inspector li,
  html[data-screen="editor"] .inspector [role="listitem"] {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
  }

  html[data-screen="editor"] .left-panel input:not([type="checkbox"]):not([type="radio"]),
  html[data-screen="editor"] .left-panel select,
  html[data-screen="editor"] .inspector input:not([type="checkbox"]):not([type="radio"]),
  html[data-screen="editor"] .inspector select {
    min-height: var(--v430-density-control-height) !important;
    padding-top: 3px !important;
    padding-bottom: 3px !important;
  }

  html[data-screen="editor"] .left-panel > header,
  html[data-screen="editor"] .left-panel > .header,
  html[data-screen="editor"] .inspector > header,
  html[data-screen="editor"] .inspector > .header {
    padding-top: 6px !important;
    padding-bottom: 6px !important;
  }
}
</style>
'''

text = text.replace('</head>', injection + '\n</head>', 1)
path.write_text(text, encoding='utf-8')
print('Applied V430-P2 compact views and information-density contract')
