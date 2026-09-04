#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

VERSION = "4.2.2"
BASE_SHA256 = "6d3900a2c973dc2d36099fc596b77b21268c11fdc1cff46bba7e66f08d83aba6"
MARKER = 'id="v422-editor-layout-hotfix"'
CONTRACT_META = '<meta name="manuscript-editor-layout-contract" content="exclusive-workspace-panes+mobile-flex-height-v1">'

HOTFIX_STYLE = r'''\n<style id="v422-editor-layout-hotfix">
/* Manuscript v4.2.2 — editor mode + mobile height-chain repair. */

/* Workspace modes are mutually exclusive at every viewport width. */
.editor-preview.editor-only > .preview-pane{
  display:none!important;
}
.editor-preview.preview-only > .editor-pane{
  display:none!important;
}

/*
   The legacy <=767px rule changes .workspace to display:block. That breaks the
   flex/grid height chain beneath the viewport-locked editor shell and can leave
   CodeMirror / preview with no usable block-size. Re-establish a bounded flex
   chain for the editor only; fixed overlay panels remain out of flow.
*/
@media(max-width:767px){
  html[data-screen="editor"] .workspace,
  html[data-screen="editor"] .workspace.left-open{
    display:flex!important;
    flex:1 1 auto;
    flex-direction:column;
    min-height:0;
    overflow:hidden;
  }
  html[data-screen="editor"] .main-stage{
    flex:1 1 auto;
    width:100%;
    height:auto;
    min-height:0!important;
    overflow:hidden;
  }
  html[data-screen="editor"] .editor-preview{
    flex:1 1 auto;
    width:100%;
    height:auto;
    min-height:0;
    overflow:hidden;
  }
  html[data-screen="editor"] .editor-pane,
  html[data-screen="editor"] .preview-pane,
  html[data-screen="editor"] .editor-shell,
  html[data-screen="editor"] .native-editor-host,
  html[data-screen="editor"] .codemirror-editor,
  html[data-screen="editor"] .codemirror-editor-mount{
    min-height:0;
  }
  html[data-screen="editor"] .native-editor-host,
  html[data-screen="editor"] .codemirror-editor,
  html[data-screen="editor"] .codemirror-editor-mount{
    height:100%;
  }
  html[data-screen="editor"] .preview-scroll{
    min-height:0;
    padding-bottom:calc(72px + env(safe-area-inset-bottom,0px));
  }
}
</style>
'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_html(path: Path) -> bool:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    current_sha = sha256(raw)

    if MARKER in text:
        validate_html(text)
        print(f"HTML already hotfixed — SHA256 {current_sha}")
        return False

    if current_sha != BASE_SHA256:
        raise SystemExit(
            f"Refusing to patch unexpected index.html: {current_sha} (expected {BASE_SHA256})"
        )

    if "</head>" not in text:
        raise SystemExit("index.html has no </head> insertion point")

    # v4.2.2 is a hotfix release of the exact certified v4.2.1 Stable bytes.
    text = text.replace("4.2.1", VERSION)

    if CONTRACT_META not in text:
        title_close = "</title>"
        if title_close not in text:
            raise SystemExit("index.html has no </title> metadata insertion point")
        text = text.replace(title_close, title_close + "\n" + CONTRACT_META, 1)

    text = text.replace("</head>", HOTFIX_STYLE + "\n</head>", 1)
    validate_html(text)
    path.write_text(text, encoding="utf-8", newline="")
    print(f"HTML hotfix applied — SHA256 {sha256(path.read_bytes())}")
    return True


def patch_service_worker(path: Path) -> bool:
    if not path.exists():
        raise SystemExit(f"Missing service worker: {path}")
    text = path.read_text(encoding="utf-8")
    new = re.sub(
        r"(const CACHE_NAME = `\$\{CACHE_PREFIX\})v4\.2\.1(`;)",
        rf"\g<1>v{VERSION}\g<2>",
        text,
        count=1,
    )
    if new == text:
        if f"${{CACHE_PREFIX}}v{VERSION}" not in text:
            raise SystemExit("Unexpected service-worker cache version state")
        return False
    path.write_text(new, encoding="utf-8", newline="")
    print(f"Service worker cache bumped to v{VERSION}")
    return True


def validate_html(text: str) -> None:
    checks = {
        "v4.2.2 title": "<title>Manuscript v4.2.2 Stable</title>" in text,
        "single hotfix style": text.count(MARKER) == 1,
        "editor layout contract": text.count(CONTRACT_META) == 1,
        "desktop editor-only hides preview": ".editor-preview.editor-only > .preview-pane" in text,
        "desktop preview-only hides editor": ".editor-preview.preview-only > .editor-pane" in text,
        "mobile workspace flex repair": 'html[data-screen="editor"] .workspace' in text and "display:flex!important" in text,
        "mobile native editor height": ".native-editor-host" in text and "height:100%" in text,
        "renderer editor-only state": "state.workspaceMode === 'editor' ? 'editor-only'" in text,
        "renderer preview-only state": "state.workspaceMode === 'preview' || state.workspaceMode === 'pages' ? 'preview-only'" in text,
        "write control": 'data-workspace="editor"' in text,
        "split control": 'data-workspace="split"' in text,
        "preview control": 'data-workspace="preview"' in text,
        "mobile write control": 'data-mobile="write"' in text,
        "mobile preview control": 'data-mobile="preview"' in text,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit("v4.2.2 hotfix validation failed: " + ", ".join(failed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("html", nargs="?", type=Path, default=Path("index.html"))
    parser.add_argument("--service-worker", type=Path, default=Path("sw.js"))
    args = parser.parse_args()
    html_changed = patch_html(args.html)
    sw_changed = patch_service_worker(args.service_worker)
    print(f"Changed: html={html_changed} sw={sw_changed}")
