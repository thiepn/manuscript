#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

VERSION = "4.2.3"
BASE_SHA256 = "deb838e5868c4f944fab92aa508170c1f046dd5faa66f2ce4bcf2951c5269606"
MARKER = 'id="v423-ui-hardening"'
CONTRACT_META = '<meta name="manuscript-ui-contract" content="responsive-ui-hardening-v1">'

HOTFIX_STYLE = r'''\n<style id="v423-ui-hardening">
/* Manuscript v4.2.3 — responsive UI hardening. */

/* Modal actions must wrap instead of shrinking labels into clipped controls. */
.modal-foot{
  flex-wrap:wrap;
  min-width:0;
}
.modal-foot > .btn{
  flex-shrink:0;
  max-width:100%;
}

/* Long utility actions must remain readable wherever the renderer places them. */
.btn[data-action="export-csl"],
.btn[data-action="request-persistence"],
.btn[data-action="backup-library"],
.btn[data-action="backup-restore-file"]{
  box-sizing:border-box!important;
  display:block!important;
  width:100%!important;
  max-width:100%!important;
  min-width:0!important;
  height:auto!important;
  min-height:32px;
  padding:6px 8px!important;
  white-space:normal!important;
  line-height:1.25;
  text-align:center;
  overflow-wrap:anywhere!important;
  word-break:break-word;
}

/*
   The late visual layer accidentally returned the left tool panel to normal
   grid flow, overriding the established <=1199px overlay contract. Restore
   the overlay and remove the phantom grid column it was consuming.
*/
@media (min-width:768px) and (max-width:1199px){
  html[data-screen="editor"] .left-panel{
    position:fixed!important;
    left:var(--rail-w)!important;
    top:calc(var(--appbar-h) + var(--toolbar-h))!important;
    bottom:var(--status-h)!important;
    width:min(var(--leftpanel-w),calc(100vw - var(--rail-w)))!important;
    height:auto!important;
    max-height:none!important;
    z-index:50!important;
    box-shadow:var(--shadow-menu)!important;
  }

  /* Compact Split may shrink, but it must never widen the application root. */
  html[data-screen="editor"] .editor-preview:not(.editor-only):not(.preview-only){
    grid-template-columns:minmax(0,1fr) 5px minmax(0,1.2fr)!important;
  }

  /* Preserve current-page status while dropping the bulky direct-jump editor. */
  html[data-screen="editor"] .editor-preview:not(.editor-only):not(.preview-only) .page-go-input,
  html[data-screen="editor"] .editor-preview:not(.editor-only):not(.preview-only) .page-position [data-action="go-page"]{
    display:none!important;
  }
  html[data-screen="editor"] .preview-toolbar{
    min-width:0;
    overflow-x:auto!important;
    overflow-y:hidden!important;
    overscroll-behavior-x:contain;
  }
}

@media (min-width:901px) and (max-width:1199px){
  html[data-screen="editor"] .workspace.left-open{
    grid-template-columns:var(--rail-w) minmax(0,1fr) var(--inspector-w)!important;
  }
  html[data-screen="editor"] .workspace.left-open.inspector-closed{
    grid-template-columns:var(--rail-w) minmax(0,1fr)!important;
  }
}

/*
   768–900px keeps the desktop/tablet controls but intentionally collapses the
   side-by-side layout. Make Split honest and useful by stacking both panes.
*/
@media (min-width:768px) and (max-width:900px){
  html[data-screen="editor"] .workspace,
  html[data-screen="editor"] .workspace.left-open,
  html[data-screen="editor"] .workspace.left-open.inspector-closed{
    grid-template-columns:var(--rail-w) minmax(0,1fr)!important;
  }

  html[data-screen="editor"] .appbar > .btn.primary[data-action="export"]{
    flex-shrink:0;
    min-width:76px;
  }

  html[data-screen="editor"] .editor-preview.editor-only,
  html[data-screen="editor"] .editor-preview.preview-only{
    grid-template-columns:1fr!important;
    grid-template-rows:minmax(0,1fr)!important;
  }

  html[data-screen="editor"] .editor-preview:not(.editor-only):not(.preview-only){
    grid-template-columns:1fr!important;
    grid-template-rows:minmax(0,1fr) minmax(0,1fr)!important;
  }
  html[data-screen="editor"] .editor-preview:not(.editor-only):not(.preview-only) > .editor-pane.mobile-hidden,
  html[data-screen="editor"] .editor-preview:not(.editor-only):not(.preview-only) > .preview-pane.mobile-hidden{
    display:flex!important;
  }
  html[data-screen="editor"] .editor-preview:not(.editor-only):not(.preview-only) > .editor-pane{
    border-right:0;
  }
  html[data-screen="editor"] .editor-preview:not(.editor-only):not(.preview-only) > .preview-pane{
    border-top:1px solid var(--border-default);
  }
}

@media (max-width:767px){
  /* Mobile Add/Style/inspector surfaces are full-screen overlays above the editor. */
  html[data-screen="editor"] .left-panel,
  html[data-screen="editor"] .inspector{
    position:fixed!important;
    left:0!important;
    right:0!important;
    top:var(--appbar-h)!important;
    bottom:56px!important;
    width:100%!important;
    max-width:none!important;
    height:auto!important;
    max-height:none!important;
    z-index:70!important;
  }

  .modal-foot > [data-action="onboarding-blank"]{
    flex:1 1 100%;
    width:100%;
    white-space:normal;
  }
}

@media (max-width:480px){
  .modal-foot > .btn{
    flex:1 1 100%;
    width:100%;
    white-space:normal;
  }
}

/* Short landscape viewports need a hard viewport-fit contract for wide modals. */
@media (max-height:480px) and (orientation:landscape){
  .modal-layer{
    padding:4px 8px!important;
    align-items:center!important;
  }
  .modal-layer .modal{
    max-height:calc(100dvh - 8px)!important;
    animation:none!important;
    transform:none!important;
  }
  .modal-layer .modal-body{
    min-height:0;
    overflow-y:auto;
  }
}
</style>
'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_html(text: str) -> None:
    checks = {
        "v4.2.3 title": "<title>Manuscript v4.2.3 Stable</title>" in text,
        "single v423 style": text.count(MARKER) == 1,
        "UI contract": text.count(CONTRACT_META) == 1,
        "left panel overlay": 'html[data-screen="editor"] .left-panel' in text and 'position:fixed!important' in text,
        "left-open compact grid": '.workspace.left-open.inspector-closed' in text,
        "compact split flexible columns": 'grid-template-columns:minmax(0,1fr) 5px minmax(0,1.2fr)!important' in text,
        "tablet vertical split": 'grid-template-rows:minmax(0,1fr) minmax(0,1fr)!important' in text,
        "tablet split panes restored": '> .preview-pane.mobile-hidden' in text and 'display:flex!important' in text,
        "modal footer wrapping": '.modal-foot{' in text and 'flex-wrap:wrap' in text,
        "utility actions wrap globally": '.btn[data-action="backup-library"]' in text and 'display:block!important' in text and 'overflow-wrap:anywhere!important' in text,
        "tablet export protected": 'min-width:76px' in text,
        "mobile panels fixed": 'html[data-screen="editor"] .inspector{' in text and 'bottom:56px!important' in text and 'z-index:70!important' in text,
        "landscape modal fit": 'max-height:calc(100dvh - 8px)!important' in text and 'animation:none!important' in text and 'transform:none!important' in text,
        "mobile onboarding primary": '[data-action="onboarding-blank"]' in text,
        "v422 retained": 'id="v422-editor-layout-hotfix"' in text,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit("v4.2.3 UI validation failed: " + ", ".join(failed))


def patch_html(path: Path) -> bool:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    current = sha256(raw)
    if MARKER in text:
        validate_html(text)
        print(f"HTML already v4.2.3 UI-hotfixed — SHA256 {current}")
        return False
    if current != BASE_SHA256:
        raise SystemExit(f"Refusing unexpected index.html: {current} (expected {BASE_SHA256})")
    if "</head>" not in text or "</title>" not in text:
        raise SystemExit("Missing HTML insertion anchors")
    text = text.replace("4.2.2", VERSION)
    text = text.replace("</title>", "</title>\n" + CONTRACT_META, 1)
    text = text.replace("</head>", HOTFIX_STYLE + "\n</head>", 1)
    validate_html(text)
    path.write_text(text, encoding="utf-8", newline="")
    print(f"HTML v4.2.3 UI hotfix applied — SHA256 {sha256(path.read_bytes())}")
    return True


def patch_service_worker(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    new = re.sub(
        r"(const CACHE_NAME = `\$\{CACHE_PREFIX\})v4\.2\.2(`;)",
        rf"\g<1>v{VERSION}\g<2>",
        text,
        count=1,
    )
    if new == text:
        if f"${{CACHE_PREFIX}}v{VERSION}" not in text:
            raise SystemExit("Unexpected service-worker cache version")
        return False
    path.write_text(new, encoding="utf-8", newline="")
    print(f"Service worker cache bumped to v{VERSION}")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("html", nargs="?", type=Path, default=Path("index.html"))
    ap.add_argument("--service-worker", type=Path, default=Path("sw.js"))
    args = ap.parse_args()
    hc = patch_html(args.html)
    sc = patch_service_worker(args.service_worker)
    print(f"Changed: html={hc} sw={sc}")
