#!/usr/bin/env python3
"""Apply V430-P7 full regression and responsive hardening to certified P6.

P7 remains a hardening layer. P1 navigation, P3 Focus, P4 commands, P5 mobile
workflow state, and P6 accessibility state remain authoritative. P7 closes only
verified edge cases from the adversarial regression audit: stale responsive
semantics, WebKit live-breakpoint lag, deterministic compact-control contrast,
and low-height command-palette containment.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

INDEX = Path("index.html")
BASE_SHA256 = "3224df3334142b33992b9d7bd60d215fed16304fe8e8ad0b294a50c60cc5ff76"
STYLE_MARKER = 'id="v430-p7-responsive-hardening"'
RUNTIME_MARKER = 'id="v430-p7-runtime"'
META = '<meta name="manuscript-hardening-contract" content="full-regression-responsive-v1">'
P5_SCRIPT_OPEN = '<script id="v430-p5-runtime">'
P5_MOBILE_DECL = "  const mobile = window.matchMedia('(max-width: 767px)');"
P5_LIVE_WIDTH_DECL = "  const mobileNow = () => window.innerWidth <= 767;"
P5_DYNAMIC_TRIGGER_GUARD = "    if (!mobileNow() || root.dataset.screen !== 'editor') {"
P5_STATIC_TRIGGER_GUARD = "    if (root.dataset.screen !== 'editor') {"

STYLE = r'''<style id="v430-p7-responsive-hardening">
/* Manuscript v4.3.0 P7 — full regression + responsive hardening. */

/* P1 quieted More by applying opacity to the whole control. Parent opacity
   composites text below AA in paper themes. Keep de-emphasis on the icon only. */
html[data-screen="editor"] .v430-utility-trigger {
  opacity: 1 !important;
}
html[data-screen="editor"] .v430-utility-trigger > svg {
  opacity: .68;
}
html[data-screen="editor"] .v430-utility-trigger:hover > svg,
html[data-screen="editor"] .v430-utility-trigger:focus-visible > svg,
html[data-screen="editor"] .v430-utility-trigger[aria-expanded="true"] > svg {
  opacity: 1;
}
html[data-screen="editor"] .v430-more-label {
  opacity: 1 !important;
}

/* Verified compact labels that sit below AA in specific muted themes. The tiny
   Checks action and theme toast body are intentionally readable in every theme. */
html[data-screen="editor"] .toast .toast-text,
html[data-screen="editor"] .status-action[data-panel="diagnostics"] {
  color: var(--text-primary) !important;
}
html[data-screen="editor"][data-theme="typesetter"] :where(
  .toolbar button[data-workspace],
  .preview-toolbar button[data-preview]
),
html[data-screen="editor"][data-theme="blueprint"] :where(
  .toolbar button[data-workspace],
  .preview-toolbar button[data-preview]
) {
  color: var(--text-primary) !important;
}

/* WebKit updates CSS media queries and viewport metrics immediately but may
   defer JS resize/rAF delivery for hundreds of milliseconds. Keep P5's mobile
   command trigger mounted while the editor exists and make both command entry
   points mutually exclusive through CSS at the actual layout breakpoint. */
@media (max-width: 767px) {
  html[data-screen="editor"] .v430-command-trigger {
    display: none !important;
  }
}
@media (min-width: 768px) {
  html[data-screen="editor"] .v430-mobile-command-trigger {
    display: none !important;
  }
}

/* P4's desktop palette uses a viewport-relative top margin. At short desktop
   heights that margin is added after max-height calculation and pushes the
   palette below the viewport. Collapse only that decorative offset and keep
   scrolling inside the existing command list. */
@media (min-width: 768px) and (max-height: 520px) {
  html[data-screen="editor"] .command-layer {
    padding: 8px !important;
    align-items: start !important;
  }
  html[data-screen="editor"] .command-layer .command-palette.v430-command-palette {
    margin: 0 auto !important;
    max-height: calc(100dvh - 16px) !important;
  }
  html[data-screen="editor"] .command-layer .command-list {
    min-height: 0 !important;
  }
}
</style>'''

SCRIPT = r'''<script id="v430-p7-runtime">
(() => {
  'use strict';
  if (window.__manuscriptV430P7) return;

  const root = document.documentElement;
  const mobileMedia = window.matchMedia('(max-width: 767px)');
  const mobileNow = () => window.innerWidth <= 767;
  let scheduled = false;
  let widthObserver = null;

  function cleanupMobileSemantics() {
    if (mobileNow()) return;
    document.querySelectorAll('.left-panel[data-v430-p6-mobile-dialog="true"],.inspector[data-v430-p6-mobile-dialog="true"]').forEach(surface => {
      const kind = surface.matches('.left-panel') ? 'add' : 'style';
      surface.removeAttribute('data-v430-p6-mobile-dialog');
      if (surface.getAttribute('role') === 'dialog') surface.removeAttribute('role');
      if (surface.getAttribute('aria-modal') === 'true') surface.removeAttribute('aria-modal');
      const p6Label = kind === 'add' ? 'Add content' : 'Style';
      if (!surface.hasAttribute('aria-labelledby') && surface.getAttribute('aria-label') === p6Label) {
        surface.removeAttribute('aria-label');
      }
    });
  }

  function resyncResponsiveOwners() {
    // P5 and P6 remain authoritative. P7 only prompts their existing schedulers.
    window.__manuscriptV430P5?.sync?.();
    window.__manuscriptV430P6?.refresh?.();
  }

  function sync() {
    scheduled = false;
    if (root.dataset.screen !== 'editor') return;
    cleanupMobileSemantics();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(sync);
  }

  function handleResize() {
    resyncResponsiveOwners();
    schedule();
    requestAnimationFrame(resyncResponsiveOwners);
    setTimeout(() => {
      resyncResponsiveOwners();
      schedule();
    }, 60);
  }

  const rootObserver = new MutationObserver(records => {
    if (records.some(record => record.type === 'attributes' && record.attributeName === 'data-screen')) {
      // P5 creates/removes the mobile trigger on screen ownership changes; CSS
      // handles breakpoint visibility for both command entry points.
      resyncResponsiveOwners();
      schedule();
    }
  });

  function boot() {
    rootObserver.observe(root, {attributes:true,attributeFilter:['data-screen']});
    window.addEventListener('resize', handleResize, {passive:true});
    window.visualViewport?.addEventListener?.('resize', handleResize, {passive:true});
    mobileMedia.addEventListener?.('change', handleResize);
    if ('ResizeObserver' in window) {
      widthObserver = new ResizeObserver(() => handleResize());
      widthObserver.observe(root);
    }
    resyncResponsiveOwners();
    schedule();
  }

  window.__manuscriptV430P7 = {
    version:'full-regression-responsive-v1',
    refresh:schedule,
    syncResponsive:handleResize,
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})();
</script>'''


def _p5_runtime_bounds(text: str) -> tuple[int, int]:
    start = text.find(P5_SCRIPT_OPEN)
    if start < 0:
        raise SystemExit("P5 runtime block missing")
    end = text.find('</script>', start)
    if end < 0:
        raise SystemExit("P5 runtime closing tag missing")
    return start, end


def _validate_p5_compat(runtime: str) -> None:
    if runtime.count(P5_LIVE_WIDTH_DECL) != 1:
        raise SystemExit("P5 live-width compatibility predicate missing or duplicated")
    if 'mobile.matches' in runtime:
        raise SystemExit("P5 still contains stale mobile.matches reads after P7 compatibility hardening")
    # The command trigger no longer needs a width predicate because CSS owns its
    # visibility; P5 still uses live width for nav enhancement and its public getter.
    if runtime.count('mobileNow()') != 2:
        raise SystemExit("P5 live-width compatibility read count is not the certified 2")
    if runtime.count(P5_STATIC_TRIGGER_GUARD) != 1:
        raise SystemExit("P5 static command-trigger editor guard missing or duplicated")
    if P5_DYNAMIC_TRIGGER_GUARD in runtime:
        raise SystemExit("P5 command trigger still depends on viewport-event timing")


def _harden_p5_responsive_ownership(text: str) -> str:
    """Keep P5 authoritative while making its command trigger CSS-responsive."""
    start, end = _p5_runtime_bounds(text)
    runtime = text[start:end]

    if P5_LIVE_WIDTH_DECL not in runtime:
        if runtime.count(P5_MOBILE_DECL) != 1:
            raise SystemExit("P5 mobile MediaQueryList declaration missing or duplicated")
        stale_reads = runtime.count('mobile.matches')
        if stale_reads != 3:
            raise SystemExit(f"Unexpected P5 mobile.matches read count: {stale_reads}, expected 3")
        runtime = runtime.replace(P5_MOBILE_DECL, P5_MOBILE_DECL + '\n' + P5_LIVE_WIDTH_DECL, 1)
        runtime = runtime.replace('mobile.matches', 'mobileNow()')

    if P5_DYNAMIC_TRIGGER_GUARD in runtime:
        runtime = runtime.replace(P5_DYNAMIC_TRIGGER_GUARD, P5_STATIC_TRIGGER_GUARD, 1)

    _validate_p5_compat(runtime)
    return text[:start] + runtime + text[end:]


def main() -> None:
    text = INDEX.read_text(encoding="utf-8")
    p7_present = STYLE_MARKER in text or RUNTIME_MARKER in text or META in text
    if p7_present:
        if text.count(STYLE_MARKER) != 1 or text.count(RUNTIME_MARKER) != 1 or text.count(META) != 1:
            raise SystemExit("Refusing partially applied V430-P7 contract")
        start, end = _p5_runtime_bounds(text)
        _validate_p5_compat(text[start:end])
        print("V430-P7 hardening contract already applied")
        return

    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual != BASE_SHA256:
        raise SystemExit(f"Refusing unexpected P6 baseline: sha256={actual}, expected={BASE_SHA256}")

    required = (
        'id="v430-p1-simplified-navigation"',
        'id="v430-p2-compact-density"',
        'id="v430-p3-focus-mode"',
        'id="v430-p3-runtime"',
        'id="v430-p4-command-palette"',
        'id="v430-p4-runtime"',
        'id="v430-p5-mobile-first"',
        'id="v430-p5-runtime"',
        'id="v430-p6-accessibility"',
        'id="v430-p6-runtime"',
        'manuscript-accessibility-contract" content="keyboard-accessibility-v1',
    )
    for marker in required:
        if marker not in text:
            raise SystemExit(f"Required inherited V430 contract missing: {marker}")
    if '</head>' not in text or '</body>' not in text:
        raise SystemExit("Document closing anchors missing")

    text = _harden_p5_responsive_ownership(text)
    text = text.replace('</head>', f'{META}\n{STYLE}\n</head>', 1)
    body_close = text.rfind('</body>')
    text = text[:body_close] + SCRIPT + '\n' + text[body_close:]
    INDEX.write_text(text, encoding="utf-8")

    patched = INDEX.read_text(encoding="utf-8")
    assert patched.count(STYLE_MARKER) == 1
    assert patched.count(RUNTIME_MARKER) == 1
    assert patched.count(META) == 1
    start, end = _p5_runtime_bounds(patched)
    _validate_p5_compat(patched[start:end])
    print("Applied V430-P7 full regression and responsive hardening")
    print("patched sha256:", hashlib.sha256(patched.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
