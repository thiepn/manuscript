#!/usr/bin/env python3
"""Apply the V430-P1 simplified-navigation contract to the certified v4.2.3 shell.

The production app is deliberately distributed as one self-contained HTML file.  This
patcher keeps the v4.2.3 source byte-for-byte intact except for a documented P1 meta
contract plus one isolated style/runtime layer.  It is idempotent and refuses to patch
an unexpected baseline.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

INDEX = Path("index.html")
BASE_SHA256 = "0c675f6145de6b18b27ff97ceb7fa827b948cc7db47fc5a9db702efef101fc44"
MARKER = 'id="v430-p1-simplified-navigation"'

STYLE = r'''<style id="v430-p1-simplified-navigation">
/* Manuscript v4.3.0 P1 — simplified navigation + quieter chrome. */
:root {
  --v430-line: color-mix(in srgb, currentColor 13%, transparent);
  --v430-soft: color-mix(in srgb, currentColor 6%, transparent);
  --v430-hover: color-mix(in srgb, currentColor 9%, transparent);
  --v430-active: color-mix(in srgb, currentColor 14%, transparent);
  --v430-muted: color-mix(in srgb, currentColor 67%, transparent);
}

html[data-screen="editor"] .v430-nav-host {
  border-color: var(--v430-line) !important;
  box-shadow: none !important;
}

html[data-screen="editor"] .v430-nav-item,
html[data-screen="editor"] .v430-utility-trigger,
html[data-screen="editor"] .v430-secondary-action {
  box-shadow: none !important;
  transition: background-color 120ms ease, color 120ms ease, opacity 120ms ease !important;
}

html[data-screen="editor"] .v430-nav-item {
  background: transparent !important;
  border-color: transparent !important;
  opacity: .76;
}

html[data-screen="editor"] .v430-nav-item:hover,
html[data-screen="editor"] .v430-nav-item:focus-visible {
  background: var(--v430-hover) !important;
  opacity: 1;
}

html[data-screen="editor"] .v430-nav-item.active,
html[data-screen="editor"] .v430-nav-item.is-active,
html[data-screen="editor"] .v430-nav-item[aria-current="page"],
html[data-screen="editor"] .v430-nav-item[aria-pressed="true"],
html[data-screen="editor"] .v430-nav-item[data-active="true"] {
  background: var(--v430-active) !important;
  border-color: transparent !important;
  opacity: 1;
}

html[data-screen="editor"] .v430-nav-divider {
  display: block;
  align-self: stretch;
  height: 1px;
  min-height: 1px;
  margin: 7px 7px;
  padding: 0;
  border: 0;
  background: var(--v430-line);
  pointer-events: none;
}

html[data-screen="editor"] .v430-utility-trigger {
  min-width: 34px;
  min-height: 34px;
  border: 1px solid transparent !important;
  background: transparent !important;
  color: inherit;
  opacity: .68;
}

html[data-screen="editor"] .v430-utility-trigger:hover,
html[data-screen="editor"] .v430-utility-trigger[aria-expanded="true"],
html[data-screen="editor"] .v430-utility-trigger:focus-visible {
  background: var(--v430-hover) !important;
  opacity: 1;
}

.v430-utility-trigger .v430-more-glyph {
  font-size: 18px;
  letter-spacing: 1px;
  line-height: 1;
}

.v430-utility-trigger .v430-more-label {
  margin-inline-start: 6px;
  font-size: 12px;
}

#v430-utility-menu {
  position: fixed;
  z-index: 100000;
  display: none;
  width: min(268px, calc(100vw - 16px));
  max-height: min(440px, calc(100dvh - 16px));
  overflow: auto;
  padding: 6px;
  border: 1px solid var(--v430-line);
  border-radius: 10px;
  background: var(--surface, var(--panel-bg, Canvas));
  color: inherit;
  box-shadow: 0 12px 36px color-mix(in srgb, #000 18%, transparent);
}

#v430-utility-menu[data-open="true"] { display: block; }

#v430-utility-menu .v430-menu-title {
  padding: 6px 9px 5px;
  color: var(--v430-muted);
  font-size: 11px;
  font-weight: 650;
  letter-spacing: .055em;
  text-transform: uppercase;
}

#v430-utility-menu .v430-utility-item,
#v430-utility-menu .v430-utility-proxy {
  display: flex !important;
  align-items: center;
  justify-content: flex-start;
  gap: 9px;
  width: 100% !important;
  min-width: 0 !important;
  min-height: 38px;
  height: auto !important;
  margin: 0 !important;
  padding: 7px 9px !important;
  border: 0 !important;
  border-radius: 7px !important;
  background: transparent !important;
  color: inherit !important;
  box-shadow: none !important;
  text-align: left;
  opacity: .88;
}

#v430-utility-menu .v430-utility-item:hover,
#v430-utility-menu .v430-utility-item:focus-visible,
#v430-utility-menu .v430-utility-proxy:hover,
#v430-utility-menu .v430-utility-proxy:focus-visible {
  background: var(--v430-hover) !important;
  opacity: 1;
}

#v430-utility-menu .v430-utility-copy {
  overflow: hidden;
  font-size: 13px !important;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

html[data-screen="editor"] .v430-mode-button {
  min-height: 30px;
  padding-block: 4px !important;
  border-color: transparent !important;
  background: transparent !important;
  box-shadow: none !important;
}

html[data-screen="editor"] .v430-mode-button:hover,
html[data-screen="editor"] .v430-mode-button:focus-visible {
  background: var(--v430-hover) !important;
}

html[data-screen="editor"] .v430-mode-button.active,
html[data-screen="editor"] .v430-mode-button.is-active,
html[data-screen="editor"] .v430-mode-button[aria-pressed="true"],
html[data-screen="editor"] .v430-mode-button[data-active="true"] {
  background: var(--v430-active) !important;
  box-shadow: none !important;
}

html[data-screen="editor"] .v430-mode-host {
  padding: 2px !important;
  border: 1px solid var(--v430-line) !important;
  border-radius: 8px !important;
  background: var(--v430-soft) !important;
  box-shadow: none !important;
}

html[data-screen="editor"] .v430-appbar {
  border-color: var(--v430-line) !important;
  box-shadow: none !important;
}

html[data-screen="editor"] .v430-secondary-action {
  background: transparent !important;
  border-color: transparent !important;
  opacity: .66;
}

html[data-screen="editor"] .v430-secondary-action:hover,
html[data-screen="editor"] .v430-secondary-action:focus-visible {
  background: var(--v430-hover) !important;
  opacity: 1;
}

html[data-screen="editor"] .v430-toolbar,
html[data-screen="editor"] .v430-preview-toolbar {
  border-color: var(--v430-line) !important;
  box-shadow: none !important;
}

html[data-screen="editor"] .v430-toolbar button,
html[data-screen="editor"] .v430-preview-toolbar button {
  box-shadow: none !important;
}

html[data-screen="editor"] .left-panel {
  border-color: var(--v430-line) !important;
  box-shadow: 8px 0 26px color-mix(in srgb, #000 9%, transparent) !important;
}

@media (max-width: 1199px) {
  .v430-utility-trigger .v430-more-label { display: none; }
}

@media (max-width: 767px) {
  #v430-utility-menu,
  .v430-utility-trigger,
  .v430-nav-divider { display: none !important; }
}

@media (prefers-reduced-motion: reduce) {
  html[data-screen="editor"] .v430-nav-item,
  html[data-screen="editor"] .v430-utility-trigger,
  html[data-screen="editor"] .v430-secondary-action { transition: none !important; }
}
</style>'''

SCRIPT = r'''<script id="v430-p1-runtime">
(() => {
  'use strict';
  if (window.__manuscriptV430P1) return;
  window.__manuscriptV430P1 = true;

  const PANEL_LABELS = {
    files: 'Files', outline: 'Outline', search: 'Search',
    insert: 'Insert', assets: 'Media', references: 'References',
    diagnostics: 'Checks', history: 'History', templates: 'Templates',
    settings: 'Settings', help: 'Help'
  };
  const GROUPS = {
    files: 'document', outline: 'document', search: 'document',
    insert: 'add', assets: 'add', references: 'add',
    diagnostics: 'review', history: 'review',
    templates: 'utilities', settings: 'utilities', help: 'utilities'
  };
  const UTILITY_PANELS = ['templates', 'settings', 'help'];
  const GROUP_ORDER = ['document', 'add', 'review'];
  const media = window.matchMedia('(min-width: 768px)');
  let menu = null;
  let trigger = null;
  let observer = null;
  let scheduled = false;
  let listenersInstalled = false;

  const isElement = node => node && node.nodeType === 1;
  const inMobileSurface = el => !!el.closest('.mobile-bottom-nav');
  const inPanelContent = el => !!el.closest('.left-panel,.inspector,.modal-layer,#v430-utility-menu');
  const desktopPanelButtons = () => [...document.querySelectorAll('[data-panel]')]
    .filter(isElement)
    .filter(el => !inMobileSurface(el) && !inPanelContent(el));

  function bestHost(buttons) {
    if (!buttons.length) return null;
    const scores = new Map();
    for (const button of buttons) {
      let node = button.parentElement;
      for (let depth = 0; node && node !== document.body && depth < 4; depth += 1, node = node.parentElement) {
        if (node.closest('.left-panel,.inspector,.modal-layer')) break;
        if (!scores.has(node)) scores.set(node, new Set());
        scores.get(node).add(button);
      }
    }
    const candidates = [...scores.entries()]
      .filter(([, set]) => set.size >= Math.min(4, buttons.length))
      .sort((a, b) => b[1].size - a[1].size || a[0].querySelectorAll('*').length - b[0].querySelectorAll('*').length);
    return candidates[0]?.[0] || buttons[0].parentElement;
  }

  function labelFor(button, id) {
    return PANEL_LABELS[id] || button.getAttribute('aria-label') || button.getAttribute('title') ||
      (button.textContent || '').trim() || id;
  }

  function normalizePanelButtons(host, buttons) {
    for (const button of buttons) {
      if (!host.contains(button)) continue;
      const id = button.getAttribute('data-panel');
      if (!id || !GROUPS[id]) continue;
      button.classList.add('v430-nav-item');
      button.dataset.v430Group = GROUPS[id];
      const label = labelFor(button, id);
      if (!button.getAttribute('aria-label')) button.setAttribute('aria-label', label);
      if (!button.getAttribute('title')) button.setAttribute('title', label);
    }
  }

  function addGroupDividers(host, buttons) {
    host.querySelectorAll(':scope > .v430-nav-divider').forEach(el => el.remove());
    let previous = null;
    for (const group of GROUP_ORDER) {
      const first = buttons.find(button => host.contains(button) && button.dataset.v430Group === group && !UTILITY_PANELS.includes(button.dataset.panel));
      if (!first) continue;
      if (previous) {
        const divider = document.createElement('span');
        divider.className = 'v430-nav-divider';
        divider.dataset.v430DividerFor = group;
        divider.setAttribute('aria-hidden', 'true');
        first.before(divider);
      }
      previous = group;
    }
  }

  function ensureMenu() {
    if (menu?.isConnected) return menu;
    menu = document.getElementById('v430-utility-menu');
    if (!menu) {
      menu = document.createElement('div');
      menu.id = 'v430-utility-menu';
      menu.setAttribute('role', 'menu');
      menu.setAttribute('aria-label', 'More tools');
      menu.dataset.open = 'false';
      const title = document.createElement('div');
      title.className = 'v430-menu-title';
      title.textContent = 'Utilities';
      menu.append(title);
      document.body.append(menu);
    }
    return menu;
  }

  function ensureUtilityCopy(button, label) {
    if (button.querySelector(':scope > .v430-utility-copy')) return;
    const existing = (button.textContent || '').trim().toLowerCase();
    if (existing.includes(label.toLowerCase())) return;
    const copy = document.createElement('span');
    copy.className = 'v430-utility-copy';
    copy.textContent = label;
    button.append(copy);
  }

  function moveUtilityPanels(host) {
    const utilityMenu = ensureMenu();
    for (const id of UTILITY_PANELS) {
      let button = [...document.querySelectorAll(`[data-panel="${id}"]`)]
        .find(el => !inMobileSurface(el) && !el.closest('.left-panel,.inspector,.modal-layer'));
      if (!button) continue;
      button.classList.add('v430-utility-item');
      button.dataset.v430UtilityItem = id;
      const label = PANEL_LABELS[id];
      if (!button.getAttribute('aria-label')) button.setAttribute('aria-label', label);
      button.setAttribute('title', label);
      ensureUtilityCopy(button, label);
      if (button.parentElement !== utilityMenu) utilityMenu.append(button);
    }

    let themeProxy = utilityMenu.querySelector('[data-v430-utility-proxy="theme"]');
    if (!themeProxy) {
      themeProxy = document.createElement('button');
      themeProxy.type = 'button';
      themeProxy.className = 'v430-utility-proxy';
      themeProxy.dataset.v430UtilityProxy = 'theme';
      themeProxy.setAttribute('role', 'menuitem');
      themeProxy.innerHTML = '<span aria-hidden="true">◐</span><span class="v430-utility-copy">Theme</span>';
      themeProxy.addEventListener('click', () => {
        const original = [...document.querySelectorAll('[data-action="theme"]')]
          .find(el => el !== themeProxy && !el.closest('#v430-utility-menu'));
        closeMenu();
        if (original) original.click();
      });
      utilityMenu.append(themeProxy);
    }
  }

  function ensureTrigger(host, preferredAnchor) {
    if (trigger?.isConnected && trigger.parentElement === host) return trigger;
    trigger = host.querySelector(':scope > .v430-utility-trigger');
    if (!trigger) {
      trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'v430-utility-trigger';
      trigger.setAttribute('aria-label', 'More tools');
      trigger.setAttribute('title', 'More tools');
      trigger.setAttribute('aria-haspopup', 'menu');
      trigger.setAttribute('aria-controls', 'v430-utility-menu');
      trigger.setAttribute('aria-expanded', 'false');
      trigger.innerHTML = '<span class="v430-more-glyph" aria-hidden="true">•••</span><span class="v430-more-label">More</span>';
      trigger.addEventListener('click', event => {
        event.stopPropagation();
        if (menu?.dataset.open === 'true') closeMenu(); else openMenu();
      });
      if (preferredAnchor?.parentElement === host) preferredAnchor.before(trigger);
      else host.append(trigger);
    }
    return trigger;
  }

  function positionMenu() {
    if (!menu || !trigger || menu.dataset.open !== 'true') return;
    const tr = trigger.getBoundingClientRect();
    const mr = menu.getBoundingClientRect();
    const margin = 8;
    let left = tr.right + margin;
    if (left + mr.width > window.innerWidth - margin) left = tr.left - mr.width - margin;
    left = Math.max(margin, Math.min(left, window.innerWidth - mr.width - margin));
    let top = Math.min(tr.top, window.innerHeight - mr.height - margin);
    top = Math.max(margin, top);
    menu.style.left = `${Math.round(left)}px`;
    menu.style.top = `${Math.round(top)}px`;
  }

  function openMenu() {
    if (!media.matches) return;
    ensureMenu();
    menu.dataset.open = 'true';
    trigger?.setAttribute('aria-expanded', 'true');
    positionMenu();
    const first = menu.querySelector('button,[role="menuitem"]');
    first?.focus({preventScroll: true});
  }

  function closeMenu({restoreFocus = false} = {}) {
    if (!menu) return;
    menu.dataset.open = 'false';
    trigger?.setAttribute('aria-expanded', 'false');
    if (restoreFocus) trigger?.focus({preventScroll: true});
  }

  function markWorkspaceModes() {
    const buttons = [...document.querySelectorAll('[data-workspace]')].filter(el => !el.closest('.modal-layer,.left-panel'));
    for (const button of buttons) button.classList.add('v430-mode-button');
    const parents = new Map();
    for (const button of buttons) parents.set(button.parentElement, (parents.get(button.parentElement) || 0) + 1);
    const best = [...parents.entries()].sort((a,b) => b[1] - a[1])[0];
    if (best && best[1] >= 2) best[0]?.classList.add('v430-mode-host');
  }

  function markChrome() {
    const theme = [...document.querySelectorAll('[data-action="theme"]')].find(el => !el.closest('#v430-utility-menu,.modal-layer'));
    theme?.classList.add('v430-secondary-action');

    const exportButton = [...document.querySelectorAll('[data-action="export"]')].find(el => !el.closest('.mobile-bottom-nav,.modal-layer'));
    const mode = document.querySelector('.v430-mode-host');
    const appBar = exportButton?.closest('header,.app-bar,.appbar,.top-bar,.topbar,.app-header,.editor-header') ||
      mode?.closest('header,.app-bar,.appbar,.top-bar,.topbar,.app-header,.editor-header');
    appBar?.classList.add('v430-appbar');

    document.querySelectorAll('.editor-toolbar,.format-toolbar,.formatting-toolbar,.toolbar').forEach(el => {
      if (!el.closest('.modal-layer,.left-panel,.inspector,.mobile-bottom-nav')) el.classList.add('v430-toolbar');
    });
    const marginGuides = document.querySelector('[data-action="margin-guides"]');
    const previewToolbar = marginGuides?.parentElement;
    if (previewToolbar && !previewToolbar.closest('.modal-layer')) previewToolbar.classList.add('v430-preview-toolbar');
  }

  function enhance() {
    scheduled = false;
    markWorkspaceModes();
    markChrome();
    if (!media.matches) {
      closeMenu();
      return;
    }
    const buttons = desktopPanelButtons();
    if (!buttons.length) return;
    const host = bestHost(buttons);
    if (!host || host === document.body || host === document.documentElement) return;
    host.classList.add('v430-nav-host');
    normalizePanelButtons(host, buttons);
    const utilityAnchor = buttons.find(button => UTILITY_PANELS.includes(button.dataset.panel));
    ensureTrigger(host, utilityAnchor);
    moveUtilityPanels(host);
    addGroupDividers(host, desktopPanelButtons().filter(button => host.contains(button)));
  }

  function scheduleEnhance() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(enhance);
  }

  function installListeners() {
    if (listenersInstalled) return;
    listenersInstalled = true;
    document.addEventListener('pointerdown', event => {
      if (menu?.dataset.open !== 'true') return;
      if (menu.contains(event.target) || trigger?.contains(event.target)) return;
      closeMenu();
    }, true);
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || menu?.dataset.open !== 'true') return;
      event.preventDefault();
      closeMenu({restoreFocus: true});
    }, true);
    document.addEventListener('click', event => {
      if (menu?.dataset.open === 'true' && event.target.closest('#v430-utility-menu button')) closeMenu();
    });
    window.addEventListener('resize', () => { closeMenu(); scheduleEnhance(); }, {passive: true});
    media.addEventListener?.('change', scheduleEnhance);
  }

  function start() {
    installListeners();
    scheduleEnhance();
    observer = new MutationObserver(scheduleEnhance);
    observer.observe(document.body, {subtree: true, childList: true});
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
  else start();
})();
</script>'''

META = '<meta name="manuscript-writing-ui-contract" content="simplified-navigation-v1">'


def main() -> None:
    text = INDEX.read_text(encoding="utf-8")
    if MARKER in text:
        print("V430-P1 marker already present; no-op")
        return

    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual != BASE_SHA256:
        raise SystemExit(
            f"Refusing to patch unexpected index.html: sha256={actual}, expected={BASE_SHA256}"
        )
    if '</head>' not in text or '</body>' not in text:
        raise SystemExit("Required HTML anchors not found")
    for required in (
        'id="v422-editor-layout-hotfix"',
        'id="v423-ui-hardening"',
        'manuscript-ui-contract" content="responsive-ui-hardening-v1',
    ):
        if required not in text:
            raise SystemExit(f"Required v4.2.x contract missing: {required}")

    text = text.replace('</head>', f'{META}\n{STYLE}\n</head>', 1)
    body_close = text.rfind('</body>')
    if body_close < 0:
        raise SystemExit('Document closing </body> anchor not found')
    text = text[:body_close] + SCRIPT + '\n' + text[body_close:]
    INDEX.write_text(text, encoding="utf-8")

    patched = INDEX.read_text(encoding="utf-8")
    assert MARKER in patched
    assert 'manuscript-writing-ui-contract" content="simplified-navigation-v1' in patched
    assert 'id="v422-editor-layout-hotfix"' in patched
    assert 'id="v423-ui-hardening"' in patched
    print("Applied V430-P1 simplified navigation contract")
    print("patched sha256:", hashlib.sha256(patched.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
