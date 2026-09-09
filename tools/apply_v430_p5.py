#!/usr/bin/env python3
from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

STYLE_ID = 'v430-p5-mobile-first'
SCRIPT_ID = 'v430-p5-runtime'
CONTRACT = 'mobile-first-interaction-v1'
META = f'<meta name="manuscript-mobile-first-contract" content="{CONTRACT}">'
P3_DESKTOP_MEDIA = "const media = window.matchMedia('(min-width: 768px)');"
P3_ALL_WIDTHS_MEDIA = "const media = window.matchMedia('(min-width: 0px)');"
P4_COMMAND_GUARD_OLD = 'html[data-screen="editor"] .appbar > [data-action="command"]:not(.v430-command-trigger) {'
P4_COMMAND_GUARD_P5 = 'html[data-screen="editor"] .appbar > [data-action="command"]:not(.v430-command-trigger):not(.v430-mobile-command-trigger) {'

style_marker = f'id="{STYLE_ID}"'
script_marker = f'id="{SCRIPT_ID}"'
marker_state = (style_marker in text, script_marker in text, META in text)

# Be idempotent when fully applied, but fail closed on a partially injected P5
# contract. Re-running a partially injected patcher must never duplicate style,
# runtime, or metadata blocks.
if any(marker_state):
    if not all(marker_state):
        raise SystemExit(f'Partial V430-P5 contract detected: style={marker_state[0]} runtime={marker_state[1]} meta={marker_state[2]}')
    if text.count(style_marker) != 1 or text.count(script_marker) != 1 or text.count(META) != 1:
        raise SystemExit('Duplicate V430-P5 contract markers detected')
    p3_start = text.find('<script id="v430-p3-runtime">')
    p3_end = text.find('</script>', p3_start)
    if p3_start < 0 or p3_end < 0:
        raise SystemExit('P3 runtime block missing while validating applied P5 contract')
    p3_runtime = text[p3_start:p3_end]
    if P3_DESKTOP_MEDIA in p3_runtime or p3_runtime.count(P3_ALL_WIDTHS_MEDIA) != 1:
        raise SystemExit('V430-P5 markers exist but P3 Focus eligibility is not in the certified all-width state')
    p4_start = text.find('<style id="v430-p4-command-palette">')
    p4_end = text.find('</style>', p4_start)
    if p4_start < 0 or p4_end < 0:
        raise SystemExit('P4 style block missing while validating applied P5 contract')
    p4_style = text[p4_start:p4_end]
    if p4_style.count(P4_COMMAND_GUARD_P5) != 1 or P4_COMMAND_GUARD_OLD in p4_style:
        raise SystemExit('V430-P5 markers exist but the P4 command guard is not P5-aware')
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
    if text.count(required) != 1:
        raise SystemExit(f'Prerequisite contract missing or duplicated: {required}')

# P3 deliberately deferred mobile Focus to P5. Keep P3 as the only Focus state
# machine; P5 broadens only P3 eligibility and supplies narrow-screen layout.
p3_start = text.find('<script id="v430-p3-runtime">')
p3_end = text.find('</script>', p3_start)
if p3_start < 0 or p3_end < 0:
    raise SystemExit('P3 runtime block missing')
p3_runtime = text[p3_start:p3_end]
if p3_runtime.count(P3_DESKTOP_MEDIA) == 1 and P3_ALL_WIDTHS_MEDIA not in p3_runtime:
    p3_runtime = p3_runtime.replace(P3_DESKTOP_MEDIA, P3_ALL_WIDTHS_MEDIA, 1)
    text = text[:p3_start] + p3_runtime + text[p3_end:]
elif p3_runtime.count(P3_ALL_WIDTHS_MEDIA) == 1 and P3_DESKTOP_MEDIA not in p3_runtime:
    # Safe recovery point if a previous process broadened P3 but stopped before
    # inserting any P5 contract markers.
    pass
else:
    raise SystemExit('P3 Focus eligibility anchor is missing, duplicated, or ambiguous inside the P3 runtime')

# Extend P4's command guard only for the P5-owned mobile presentation trigger.
p4_start = text.find('<style id="v430-p4-command-palette">')
p4_end = text.find('</style>', p4_start)
if p4_start < 0 or p4_end < 0:
    raise SystemExit('P4 command-palette style block missing')
p4_style = text[p4_start:p4_end]
if p4_style.count(P4_COMMAND_GUARD_OLD) == 1 and P4_COMMAND_GUARD_P5 not in p4_style:
    p4_style = p4_style.replace(P4_COMMAND_GUARD_OLD, P4_COMMAND_GUARD_P5, 1)
    text = text[:p4_start] + p4_style + text[p4_end:]
elif p4_style.count(P4_COMMAND_GUARD_P5) == 1 and P4_COMMAND_GUARD_OLD not in p4_style:
    pass
else:
    raise SystemExit('P4 command guard is missing, duplicated, or ambiguous')

head_close = text.find('</head>')
body_open = text.find('<body')
if head_close < 0 or body_open < 0 or head_close > body_open or '</body>' not in text:
    raise SystemExit('HTML injection anchors missing or out of document order')

style = r'''
<meta name="manuscript-mobile-first-contract" content="mobile-first-interaction-v1">
<style id="v430-p5-mobile-first">
/* V430-P5 — Mobile-First Navigation & Interaction
   Existing Manuscript actions and state remain authoritative. P5 changes the
   presentation, target geometry and semantics of those controls; it does not
   create a second workflow, panel, command, or Focus state machine. */
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

  /* Publishing is already available in the five-action bottom nav. Removing
     duplicate low-frequency top-bar chrome protects title space at 320px. */
  html[data-screen="editor"] .appbar > [data-action="export"],
  html[data-screen="editor"] .appbar > [data-action="theme"] {
    display: none !important;
  }

  html[data-screen="editor"] .appbar > [data-action="home"],
  html[data-screen="editor"] .appbar > [data-action="more"],
  html[data-screen="editor"] .v430-mobile-command-trigger {
    width: 44px !important;
    min-width: 44px !important;
    height: 44px !important;
    min-height: 44px !important;
    flex: 0 0 44px !important;
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
    padding-inline: 5px !important;
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

  /* Existing mobile-hidden/body surface logic still owns panel state. P5 only
     turns an open panel into a viewport-safe sheet between app bar and nav. */
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

  /* Utility and modal controls are high-frequency touch surfaces reached from
     mobile navigation. Keep them usable without changing their business logic. */
  html[data-screen="editor"] #v430-utility-menu button,
  html[data-screen="editor"] .modal-layer button,
  html[data-screen="editor"] .modal-layer [role="button"] {
    min-height: 44px;
    touch-action: manipulation;
  }

  html[data-screen="editor"] .modal-layer {
    box-sizing: border-box;
    padding: max(8px, env(safe-area-inset-top, 0px)) max(8px, env(safe-area-inset-right, 0px)) max(8px, env(safe-area-inset-bottom, 0px)) max(8px, env(safe-area-inset-left, 0px)) !important;
    overflow: hidden !important;
  }

  html[data-screen="editor"] .modal-layer .modal {
    box-sizing: border-box;
    max-width: calc(100vw - 16px) !important;
    max-height: calc(100dvh - 16px - env(safe-area-inset-top, 0px) - env(safe-area-inset-bottom, 0px)) !important;
    margin: auto !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch;
  }

  /* Mobile command access behaves like a bottom sheet while retaining P4's
     native command palette, registry and keyboard semantics. */
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

  /* P3 remains the only Focus state machine. P5 provides its narrow-screen
     presentation and keeps one explicit, reachable exit control. */
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
    height: 44px !important;
    min-height: 44px !important;
    padding-inline: 10px !important;
    border: 1px solid var(--border-default) !important;
    border-radius: 7px !important;
    background: var(--surface-2) !important;
    opacity: 1 !important;
    touch-action: manipulation;
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
  html[data-screen="editor"] .v430-command-trigger {
    min-width: 44px;
    min-height: 44px;
  }
  html[data-screen="editor"] .v430-focus-trigger {
    min-height: 44px;
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
  let rootObserver = null;
  let navObserver = null;
  let observedNav = null;
  let scheduled = false;

  function setAttr(el, name, value) {
    if (!el) return;
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

  function relabelPublish(publish) {
    if (!publish || publish.dataset.v430PublishLabel === 'true') return;
    let changed = false;
    const walker = document.createTreeWalker(publish, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (/export/i.test(node.textContent || '')) {
        node.textContent = node.textContent.replace(/export/i, 'Publish');
        changed = true;
        break;
      }
    }
    if (!changed && !/publish/i.test(publish.textContent || '')) {
      const label = document.createElement('span');
      label.className = 'v430-publish-label';
      label.textContent = 'Publish';
      publish.append(label);
    }
    publish.dataset.v430PublishLabel = 'true';
  }

  function observeNav(nav) {
    if (observedNav === nav) return;
    navObserver?.disconnect();
    observedNav = nav || null;
    if (!nav) return;
    navObserver = new MutationObserver(schedule);
    navObserver.observe(nav, { subtree: true, attributes: true, attributeFilter: ['class'] });
  }

  function enhanceMobileNav() {
    const nav = document.querySelector('.mobile-bottom-nav');
    if (!nav) {
      observeNav(null);
      return;
    }
    nav.classList.add('v430-mobile-nav');
    setAttr(nav, 'aria-label', 'Mobile document workflow');
    observeNav(nav);

    const buttons = [...nav.querySelectorAll('.mobile-nav-btn')];
    for (const button of buttons) {
      const active = button.classList.contains('active');
      setAttr(button, 'aria-current', active ? 'page' : null);
      // Preserve any native aria-pressed semantics already owned by Manuscript.
    }

    const publish = nav.querySelector('[data-action="export"]');
    if (publish) {
      setAttr(publish, 'aria-label', 'Publish: export, print, or save the document');
      relabelPublish(publish);
    }
  }

  function syncCommandState() {
    const commandOpen = !!document.querySelector('.command-layer');
    if (commandTrigger?.isConnected) setAttr(commandTrigger, 'aria-expanded', commandOpen ? 'true' : 'false');
  }

  function sync() {
    scheduled = false;
    ensureCommandTrigger();
    if (mobile.matches && root.dataset.screen === 'editor') enhanceMobileNav();
    else observeNav(null);
    syncCommandState();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(sync);
  }

  function boot() {
    sync();
    rootObserver = new MutationObserver(schedule);
    rootObserver.observe(document.documentElement, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['data-screen', 'data-v430-focus'],
    });
    mobile.addEventListener?.('change', schedule);
    document.addEventListener('click', schedule, true);
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

# Final structural postconditions prevent silently writing a corrupt partial
# patch if an upstream anchor changes.
for marker in (style_marker, script_marker, META):
    if text.count(marker) != 1:
        raise SystemExit(f'V430-P5 postcondition failed for {marker!r}: count={text.count(marker)}')
p3_start = text.find('<script id="v430-p3-runtime">')
p3_end = text.find('</script>', p3_start)
if p3_start < 0 or p3_end < 0:
    raise SystemExit('V430-P5 postcondition failed: P3 runtime block missing')
p3_runtime = text[p3_start:p3_end]
if p3_runtime.count(P3_ALL_WIDTHS_MEDIA) != 1 or P3_DESKTOP_MEDIA in p3_runtime:
    raise SystemExit('V430-P5 postcondition failed: P3 runtime eligibility is not exactly all-width')

p4_start = text.find('<style id="v430-p4-command-palette">')
p4_end = text.find('</style>', p4_start)
if p4_start < 0 or p4_end < 0:
    raise SystemExit('V430-P5 postcondition failed: P4 style block missing')
p4_style = text[p4_start:p4_end]
if p4_style.count(P4_COMMAND_GUARD_P5) != 1 or P4_COMMAND_GUARD_OLD in p4_style:
    raise SystemExit('V430-P5 postcondition failed: P4 command guard is not P5-aware')

path.write_text(text, encoding='utf-8')
print('Applied V430-P5 mobile-first navigation and interaction')
