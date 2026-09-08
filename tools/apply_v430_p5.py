#!/usr/bin/env python3
from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

STYLE_ID = 'v430-p5-mobile-first'
SCRIPT_ID = 'v430-p5-runtime'
CONTRACT = 'mobile-first-interaction-v1'

if f'id="{STYLE_ID}"' in text and f'id="{SCRIPT_ID}"' in text:
    print('V430-P5 mobile-first contract already applied')
    raise SystemExit(0)

for required in (
    'id="v430-p1-simplified-navigation"',
    'id="v430-p2-compact-density"',
    'id="v430-p3-focus-mode"',
    'id="v430-p3-runtime"',
    'id="v430-p4-command-palette"',
    'id="v430-p4-runtime"',
):
    if required not in text:
        raise SystemExit(f'Prerequisite contract missing: {required}')

# P3 deliberately deferred mobile focus to P5. Keep one Focus state machine by
# broadening its eligibility here rather than introducing a second mobile-only
# focus implementation. P5 supplies the <768 presentation layer below.
p3_media = "const media = window.matchMedia('(min-width: 768px)');"
if p3_media not in text:
    raise SystemExit('P3 focus eligibility anchor missing')
text = text.replace(p3_media, "const media = window.matchMedia('(min-width: 0px)');", 1)

if '</head>' not in text or '</body>' not in text:
    raise SystemExit('HTML injection anchors missing')

style = r'''
<meta name="manuscript-mobile-first-contract" content="mobile-first-interaction-v1">
<style id="v430-p5-mobile-first">
/* V430-P5 — Mobile-First Navigation & Interaction
   Existing actions and state remain authoritative. This layer makes the
   certified workflow, command palette, panels, and Focus Mode genuinely
   usable on narrow/coarse-pointer surfaces. */
@media (max-width: 767px) {
  :root {
    --v430-mobile-nav-core: 64px;
    --v430-mobile-nav-h: calc(var(--v430-mobile-nav-core) + env(safe-area-inset-bottom, 0px));
  }

  html[data-screen="editor"] .appbar {
    height: 50px !important;
    flex-basis: 50px !important;
    padding-left: max(6px, env(safe-area-inset-left, 0px)) !important;
    padding-right: max(6px, env(safe-area-inset-right, 0px)) !important;
    gap: 3px !important;
    overflow: hidden !important;
  }

  /* The bottom nav owns publishing on mobile; duplicate top-bar export and
     low-frequency theme chrome only compete with the document title. */
  html[data-screen="editor"] .appbar > [data-action="export"],
  html[data-screen="editor"] .appbar > [data-action="theme"] {
    display: none !important;
  }

  html[data-screen="editor"] .appbar > [data-action="home"],
  html[data-screen="editor"] .appbar > [data-action="more"],
  html[data-screen="editor"] .v430-mobile-command-trigger {
    width: 42px !important;
    min-width: 42px !important;
    height: 42px !important;
    min-height: 42px !important;
    flex: 0 0 42px !important;
    border-radius: 7px !important;
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
  }

  html[data-screen="editor"] .doc-title-wrap {
    flex: 1 1 0 !important;
    width: auto !important;
    min-width: 0 !important;
  }

  html[data-screen="editor"] .doc-title {
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    padding-inline: 6px !important;
    text-overflow: ellipsis;
  }

  html[data-screen="editor"] .save-state { display: none !important; }

  .v430-mobile-command-trigger {
    display: inline-grid !important;
    place-items: center;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: var(--text-secondary);
    box-shadow: none !important;
  }

  .v430-mobile-command-trigger:hover,
  .v430-mobile-command-trigger:focus-visible,
  .v430-mobile-command-trigger[aria-expanded="true"] {
    background: var(--surface-hover) !important;
    color: var(--text-primary);
  }

  .v430-mobile-command-trigger span {
    font-size: 18px;
    line-height: 1;
  }

  html[data-screen="editor"] .mobile-bottom-nav.v430-mobile-nav {
    position: fixed !important;
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    width: 100% !important;
    height: var(--v430-mobile-nav-h) !important;
    min-height: var(--v430-mobile-nav-h) !important;
    padding: 0 env(safe-area-inset-right, 0px) env(safe-area-inset-bottom, 0px) env(safe-area-inset-left, 0px) !important;
    border-top: 1px solid var(--border-default) !important;
    background: var(--surface-1) !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    z-index: 80 !important;
    overflow: hidden;
  }

  html[data-screen="editor"] .v430-mobile-nav .mobile-nav-btn {
    position: relative;
    min-width: 0 !important;
    width: 100% !important;
    min-height: 56px !important;
    height: var(--v430-mobile-nav-core) !important;
    padding: 5px 2px 6px !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: var(--text-secondary);
    display: flex !important;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    font-size: 10px;
    font-weight: 570;
    line-height: 1.05;
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
  }

  html[data-screen="editor"] .v430-mobile-nav .mobile-nav-btn::before {
    display: none !important;
  }

  html[data-screen="editor"] .v430-mobile-nav .mobile-nav-btn svg {
    width: 19px !important;
    height: 19px !important;
  }

  html[data-screen="editor"] .v430-mobile-nav .mobile-nav-btn.active,
  html[data-screen="editor"] .v430-mobile-nav .mobile-nav-btn[aria-current="page"] {
    color: var(--accent) !important;
    background: var(--accent-soft) !important;
  }

  html[data-screen="editor"] .v430-mobile-nav .mobile-nav-btn.active::after,
  html[data-screen="editor"] .v430-mobile-nav .mobile-nav-btn[aria-current="page"]::after {
    content: "";
    position: absolute;
    top: 0;
    left: 50%;
    width: 28px;
    height: 2px;
    border-radius: 0 0 2px 2px;
    background: var(--accent);
    transform: translateX(-50%);
  }

  html[data-screen="editor"] .left-panel,
  html[data-screen="editor"] .inspector {
    top: 50px !important;
    bottom: var(--v430-mobile-nav-h) !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    max-width: none !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    background: var(--surface-1) !important;
    overscroll-behavior: contain;
  }

  html[data-screen="editor"] .left-panel .panel-head,
  html[data-screen="editor"] .inspector .panel-head {
    position: sticky;
    top: 0;
    z-index: 2;
    height: 52px !important;
    flex-basis: 52px !important;
    padding: 0 10px !important;
    background: var(--surface-1);
  }

  html[data-screen="editor"] .mobile-panel-back {
    display: inline-grid !important;
    width: 44px !important;
    min-width: 44px !important;
    height: 44px !important;
    min-height: 44px !important;
    place-items: center;
    touch-action: manipulation;
  }

  html[data-screen="editor"] .panel-body,
  html[data-screen="editor"] .inspector-content {
    min-height: 0;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    overscroll-behavior-y: contain;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 20px;
  }

  html[data-screen="editor"] .inspector-tab {
    min-height: 44px !important;
    touch-action: manipulation;
  }

  /* Mobile command access behaves like a bottom sheet while retaining the
     native command palette's combobox/listbox keyboard semantics. */
  .command-layer {
    align-items: end !important;
    padding: 8px max(8px, env(safe-area-inset-right, 0px)) max(8px, env(safe-area-inset-bottom, 0px)) max(8px, env(safe-area-inset-left, 0px)) !important;
  }

  .command-layer .command-palette.v430-command-palette {
    align-self: end !important;
    width: 100% !important;
    max-width: 100% !important;
    max-height: min(82dvh, 720px) !important;
    margin: 0 !important;
    border-radius: 14px !important;
    overflow: hidden !important;
  }

  .command-layer .command-search {
    height: 56px !important;
    min-height: 56px !important;
    padding-inline: 16px !important;
    font-size: 16px !important;
  }

  .command-layer .command-list {
    min-height: 0;
    max-height: min(42dvh, 360px) !important;
    overflow-y: auto !important;
    overscroll-behavior: contain;
  }

  .command-layer .command-item {
    min-height: 46px !important;
    height: auto !important;
    padding-block: 6px !important;
  }

  .command-layer .v430-command-fast-btn {
    min-height: 48px !important;
  }

  /* Mobile Focus — P3 remains the state machine; P5 defines the narrow-screen
     presentation and a visible, explicit exit path. */
  html[data-screen="editor"][data-v430-focus="true"] .toolbar,
  html[data-screen="editor"][data-v430-focus="true"] .activity-rail,
  html[data-screen="editor"][data-v430-focus="true"] .left-panel,
  html[data-screen="editor"][data-v430-focus="true"] .inspector,
  html[data-screen="editor"][data-v430-focus="true"] .preview-pane,
  html[data-screen="editor"][data-v430-focus="true"] .splitter,
  html[data-screen="editor"][data-v430-focus="true"] .statusbar,
  html[data-screen="editor"][data-v430-focus="true"] .mobile-bottom-nav,
  html[data-screen="editor"][data-v430-focus="true"] .v430-mobile-command-trigger,
  html[data-screen="editor"][data-v430-focus="true"] #v430-utility-menu {
    display: none !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .appbar {
    height: 50px !important;
    flex-basis: 50px !important;
    padding-inline: max(8px, env(safe-area-inset-left, 0px)) max(8px, env(safe-area-inset-right, 0px)) !important;
    gap: 6px !important;
    border-bottom: 1px solid var(--border-default) !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .appbar > :not(.doc-title-wrap):not(.appbar-spacer):not(.v430-focus-trigger) {
    display: none !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .doc-title-wrap {
    display: flex !important;
    flex: 1 1 0 !important;
    min-width: 0 !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .v430-focus-trigger {
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    width: auto !important;
    min-width: 94px !important;
    height: 40px !important;
    min-height: 40px !important;
    padding-inline: 10px !important;
    border: 1px solid var(--border-default) !important;
    border-radius: 7px !important;
    background: var(--surface-2) !important;
    opacity: 1 !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .v430-focus-label {
    display: inline !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .workspace,
  html[data-screen="editor"][data-v430-focus="true"] .workspace.left-open,
  html[data-screen="editor"][data-v430-focus="true"] .workspace.inspector-closed {
    display: block !important;
    width: 100% !important;
    height: calc(100dvh - 50px) !important;
    min-height: 0 !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .main-stage,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview.editor-only,
  html[data-screen="editor"][data-v430-focus="true"] .editor-preview.preview-only {
    display: flex !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    min-width: 0 !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .editor-pane,
  html[data-screen="editor"][data-v430-focus="true"] .editor-pane.mobile-hidden {
    display: flex !important;
    flex: 1 1 auto !important;
    width: 100% !important;
    max-width: none !important;
    height: 100% !important;
    min-height: 0 !important;
    margin: 0 !important;
    border: 0 !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .editor-pane .pane-head {
    display: none !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .editor-shell,
  html[data-screen="editor"][data-v430-focus="true"] .native-editor-host,
  html[data-screen="editor"][data-v430-focus="true"] .codemirror-editor,
  html[data-screen="editor"][data-v430-focus="true"] .codemirror-editor-mount {
    width: 100% !important;
    min-width: 0 !important;
    min-height: 0 !important;
  }
}

@media (pointer: coarse) and (min-width: 768px) {
  /* Tablet-edge controls stay comfortably tappable without changing desktop
     density or the certified >=768 navigation model. */
  html[data-screen="editor"] .v430-command-trigger,
  html[data-screen="editor"] .v430-focus-trigger {
    min-height: 40px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .v430-mobile-command-trigger,
  .mobile-nav-btn { transition: none !important; }
}
</style>
'''

script = r'''
<script id="v430-p5-runtime">
(() => {
  'use strict';
  if (window.__manuscriptV430P5) return;

  const root = document.documentElement;
  const mobile = window.matchMedia('(max-width: 767px)');
  let commandTrigger = null;
  let observer = null;
  let scheduled = false;

  function setAttr(el, name, value) {
    if (value == null || value === false) {
      if (el.hasAttribute(name)) el.removeAttribute(name);
      return;
    }
    const next = String(value);
    if (el.getAttribute(name) !== next) el.setAttribute(name, next);
  }

  function ensureCommandTrigger() {
    if (!mobile.matches || root.dataset.screen !== 'editor') {
      commandTrigger?.remove();
      commandTrigger = null;
      return;
    }

    const appbar = document.querySelector('.appbar,.v430-appbar');
    if (!appbar) return;

    commandTrigger = appbar.querySelector(':scope > .v430-mobile-command-trigger');
    if (!commandTrigger) {
      commandTrigger = document.createElement('button');
      commandTrigger.type = 'button';
      commandTrigger.className = 'icon-btn v430-mobile-command-trigger';
      commandTrigger.dataset.action = 'command';
      commandTrigger.setAttribute('aria-label', 'Open command palette');
      commandTrigger.setAttribute('aria-haspopup', 'dialog');
      commandTrigger.setAttribute('aria-expanded', 'false');
      commandTrigger.setAttribute('title', 'Commands');
      commandTrigger.innerHTML = '<span aria-hidden="true">⌕</span>';
      const more = [...appbar.children].find(el => el.matches?.('[data-action="more"]'));
      if (more) more.before(commandTrigger);
      else appbar.append(commandTrigger);
    }
  }

  function enhanceMobileNav() {
    const nav = document.querySelector('.mobile-bottom-nav');
    if (!nav) return;
    nav.classList.add('v430-mobile-nav');
    setAttr(nav, 'aria-label', 'Mobile document workflow');

    const buttons = [...nav.querySelectorAll('.mobile-nav-btn')];
    buttons.forEach(button => {
      const active = button.classList.contains('active');
      setAttr(button, 'aria-current', active ? 'page' : null);
      setAttr(button, 'aria-pressed', null);
    });

    const publish = nav.querySelector('[data-action="export"]');
    if (publish) {
      setAttr(publish, 'aria-label', 'Publish: export, print, or save the document');
      if (publish.dataset.v430PublishLabel !== 'true') {
        const textNode = [...publish.childNodes].find(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
        if (textNode) textNode.textContent = 'Publish';
        publish.dataset.v430PublishLabel = 'true';
      }
    }
  }

  function syncOverlayState() {
    const commandOpen = !!document.querySelector('.command-layer');
    if (commandTrigger?.isConnected) setAttr(commandTrigger, 'aria-expanded', commandOpen ? 'true' : 'false');

    const surface = document.querySelector('.command-layer') ? 'command'
      : document.querySelector('.left-panel:not(.mobile-hidden),.inspector:not(.mobile-hidden)') ? 'panel'
      : 'document';
    if (mobile.matches && root.dataset.screen === 'editor') root.dataset.v430MobileSurface = surface;
    else delete root.dataset.v430MobileSurface;
  }

  function sync() {
    scheduled = false;
    ensureCommandTrigger();
    if (mobile.matches && root.dataset.screen === 'editor') enhanceMobileNav();
    syncOverlayState();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(sync);
  }

  function boot() {
    sync();
    observer = new MutationObserver(schedule);
    observer.observe(document.documentElement, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['data-screen', 'data-v430-focus', 'class'],
    });
    mobile.addEventListener?.('change', schedule);
  }

  window.__manuscriptV430P5 = {
    sync: schedule,
    get mobile() { return mobile.matches; },
    get commandTrigger() { return commandTrigger; },
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
</script>
'''

text = text.replace('</head>', style + '\n</head>', 1)
body_pos = text.rfind('</body>')
if body_pos < 0:
    raise SystemExit('Final body closing anchor missing')
text = text[:body_pos] + script + '\n' + text[body_pos:]
path.write_text(text, encoding='utf-8')
print('Applied V430-P5 mobile-first navigation and interaction')
