#!/usr/bin/env python3
"""Apply V430-P6 accessibility and keyboard refinement to the certified P5 tree.

P6 is deliberately additive: P1 remains authoritative for the More menu, P3 for
Focus Mode, P4 for command execution, and P5 for mobile workflow state. This layer
adds accessibility semantics, focus containment/restoration, keyboard navigation,
contrast correction, and dynamic ARIA synchronization without replacing those
state machines.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

INDEX = Path("index.html")
BASE_SHA256 = "749cf78193cb183b26eb8689601014d9bccf48e53b1b7c20f851bdcac5f4be84"
STYLE_MARKER = 'id="v430-p6-accessibility"'
RUNTIME_MARKER = 'id="v430-p6-runtime"'
META = '<meta name="manuscript-accessibility-contract" content="keyboard-accessibility-v1">'

STYLE = r'''<style id="v430-p6-accessibility">
/* Manuscript v4.3.0 P6 — accessibility + keyboard refinement. */
html[data-screen="editor"] :where(
  button,
  a[href],
  input,
  select,
  textarea,
  [role="button"],
  [role="tab"],
  [role="menuitem"],
  [tabindex]:not([tabindex="-1"])
):focus-visible {
  outline: 2px solid currentColor !important;
  outline-offset: 2px !important;
}

#preview-scroll[data-v430-p6-preview="true"]:focus-visible {
  outline: 2px solid currentColor !important;
  outline-offset: -3px !important;
}

#command-search::placeholder {
  color: inherit !important;
  opacity: 1 !important;
}

[data-v430-p6-mobile-dialog="true"] {
  isolation: isolate;
}

@media (forced-colors: active) {
  html[data-screen="editor"] :where(button,a[href],input,select,textarea,[tabindex]):focus-visible,
  #preview-scroll[data-v430-p6-preview="true"]:focus-visible {
    outline-color: Highlight !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  .modal,
  .command-palette,
  .left-panel,
  .inspector,
  .v430-focus-trigger,
  .v430-mobile-command-trigger {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}
</style>'''

SCRIPT = r'''<script id="v430-p6-runtime">
(() => {
  'use strict';
  if (window.__manuscriptV430P6) return;

  const mobileMedia = window.matchMedia('(max-width: 767px)');
  const contrastOriginal = new WeakMap();
  const splitterEnhanced = new WeakSet();
  const mobileOrigins = new Map();
  let activeMobileSurface = null;
  let scheduled = false;
  let lastThemeSignature = '';

  const CONTRAST_SELECTORS = [
    '.save-state',
    '.pane-head',
    '.pane-head > span',
    '#cursor-status',
    '.statusbar > span',
    'footer > span',
    '.v430-command-shortcut',
    '.v430-command-fast-head',
    '.v430-command-fast-head > span',
    '.v430-command-fast-btn [data-v430-fast-label]',
    '.v430-command-fast-btn kbd',
    '#command-search'
  ].join(',');

  function isVisible(el) {
    if (!el || !el.isConnected) return false;
    const style = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
  }

  function focusables(root) {
    if (!root) return [];
    const selector = [
      'button:not([disabled])', 'a[href]', 'input:not([disabled])',
      'select:not([disabled])', 'textarea:not([disabled])',
      '[role="button"]:not([aria-disabled="true"])',
      '[role="menuitem"]:not([aria-disabled="true"])',
      '[tabindex]:not([tabindex="-1"])'
    ].join(',');
    return [...root.querySelectorAll(selector)].filter(el =>
      isVisible(el) && !el.closest('[aria-hidden="true"],[inert]') && el.tabIndex >= 0
    );
  }

  function parseColor(value) {
    if (!value || value === 'transparent') return null;
    const parts = value.match(/[\d.]+/g);
    if (!parts || parts.length < 3) return null;
    return {
      r: Math.max(0, Math.min(255, Number(parts[0]))),
      g: Math.max(0, Math.min(255, Number(parts[1]))),
      b: Math.max(0, Math.min(255, Number(parts[2]))),
      a: parts.length > 3 ? Math.max(0, Math.min(1, Number(parts[3]))) : 1,
    };
  }

  function luminance(color) {
    const channel = value => {
      const n = value / 255;
      return n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4;
    };
    return 0.2126 * channel(color.r) + 0.7152 * channel(color.g) + 0.0722 * channel(color.b);
  }

  function contrastRatio(a, b) {
    const l1 = luminance(a);
    const l2 = luminance(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  }

  function backgroundFor(el) {
    for (let node = el; node; node = node.parentElement) {
      const color = parseColor(getComputedStyle(node).backgroundColor);
      if (color && color.a >= 0.95) return color;
    }
    const body = parseColor(getComputedStyle(document.body).backgroundColor);
    if (body && body.a >= 0.95) return body;
    const html = parseColor(getComputedStyle(document.documentElement).backgroundColor);
    if (html && html.a >= 0.95) return html;
    return {r:255, g:255, b:255, a:1};
  }

  function mixColor(from, to, amount) {
    return {
      r: from.r + (to.r - from.r) * amount,
      g: from.g + (to.g - from.g) * amount,
      b: from.b + (to.b - from.b) * amount,
      a: 1,
    };
  }

  function restoreContrastOverrides() {
    document.querySelectorAll('[data-v430-p6-contrast="true"]').forEach(el => {
      const original = contrastOriginal.get(el);
      if (original) {
        if (original.value) el.style.setProperty('color', original.value, original.priority);
        else el.style.removeProperty('color');
      }
      el.removeAttribute('data-v430-p6-contrast');
    });
  }

  function ensureContrast(el, minimum = 4.6) {
    if (!isVisible(el)) return;
    if (!contrastOriginal.has(el)) {
      contrastOriginal.set(el, {
        value: el.style.getPropertyValue('color'),
        priority: el.style.getPropertyPriority('color'),
      });
    }
    const foreground = parseColor(getComputedStyle(el).color);
    const background = backgroundFor(el);
    if (!foreground || !background || contrastRatio(foreground, background) >= minimum) return;

    const black = {r:0, g:0, b:0, a:1};
    const white = {r:255, g:255, b:255, a:1};
    const target = contrastRatio(black, background) >= contrastRatio(white, background) ? black : white;
    let low = 0;
    let high = 1;
    for (let i = 0; i < 24; i += 1) {
      const mid = (low + high) / 2;
      if (contrastRatio(mixColor(foreground, target, mid), background) >= minimum) high = mid;
      else low = mid;
    }
    const fixed = mixColor(foreground, target, Math.min(1, high + 0.015));
    el.style.setProperty('color', `rgb(${Math.round(fixed.r)} ${Math.round(fixed.g)} ${Math.round(fixed.b)})`, 'important');
    el.dataset.v430P6Contrast = 'true';
  }

  function enhanceContrast(force = false) {
    if (force) restoreContrastOverrides();
    document.querySelectorAll(CONTRAST_SELECTORS).forEach(el => ensureContrast(el));
  }

  function updateSplitterValue(splitter) {
    if (!splitter?.isConnected) return;
    const parent = splitter.parentElement;
    const pr = parent?.getBoundingClientRect();
    const sr = splitter.getBoundingClientRect();
    const minimum = Number(splitter.getAttribute('aria-valuemin') || 0);
    const maximum = Number(splitter.getAttribute('aria-valuemax') || 100);
    let value = Number(splitter.getAttribute('aria-valuenow'));
    if (pr && pr.width > 0 && sr.width >= 0) {
      value = ((sr.left + sr.width / 2 - pr.left) / pr.width) * 100;
    }
    if (!Number.isFinite(value)) value = (minimum + maximum) / 2;
    value = Math.round(Math.max(minimum, Math.min(maximum, value)));
    splitter.setAttribute('aria-valuenow', String(value));
    splitter.setAttribute('aria-valuetext', `${value}% editor width`);
  }

  function enhanceSplitters() {
    document.querySelectorAll('.splitter[role="separator"]').forEach(splitter => {
      if (!splitter.getAttribute('aria-orientation')) splitter.setAttribute('aria-orientation', 'vertical');
      updateSplitterValue(splitter);
      if (splitterEnhanced.has(splitter)) return;
      splitterEnhanced.add(splitter);
      splitter.dataset.v430P6Splitter = 'true';
      const resync = () => requestAnimationFrame(() => updateSplitterValue(splitter));
      splitter.addEventListener('keyup', resync);
      splitter.addEventListener('pointerup', resync);
      splitter.addEventListener('pointercancel', resync);
    });
  }

  function enhancePreviewScroll() {
    const preview = document.getElementById('preview-scroll');
    if (!preview) return;
    if (!preview.hasAttribute('tabindex')) preview.tabIndex = 0;
    if (!preview.getAttribute('role')) preview.setAttribute('role', 'region');
    if (!preview.getAttribute('aria-label') && !preview.getAttribute('aria-labelledby')) {
      preview.setAttribute('aria-label', 'Document preview');
    }
    preview.dataset.v430P6Preview = 'true';
  }

  function dedupeRenderedDocumentIds() {
    const nodes = [...document.querySelectorAll('.doc [id], .doc [data-v430-p6-original-id]')];
    const groups = new Map();
    for (const node of nodes) {
      const id = node.dataset.v430P6OriginalId || node.id;
      if (!id) continue;
      if (!groups.has(id)) groups.set(id, []);
      groups.get(id).push(node);
    }
    for (const [id, group] of groups) {
      if (group.length < 2) continue;
      const signatures = new Set(group.map(node => `${node.tagName}\n${(node.textContent || '').trim()}`));
      if (signatures.size !== 1) continue;
      const visible = group.filter(isVisible);
      const hidden = group.filter(node => !isVisible(node));
      if (!visible.length || !hidden.length) continue;
      const keeper = visible[0];
      for (const node of group) {
        node.dataset.v430P6OriginalId = id;
        if (node === keeper) {
          if (node.id !== id) node.id = id;
        } else if (node.id === id) {
          node.removeAttribute('id');
        }
      }
    }
  }

  function enhanceSelectionStates() {
    const workspaceButtons = [...document.querySelectorAll('[data-workspace]')]
      .filter(button => !button.closest('.modal-layer,.left-panel,.inspector'));
    const hosts = new Set(workspaceButtons.map(button => button.parentElement).filter(Boolean));
    hosts.forEach(host => {
      if (!host.getAttribute('role')) host.setAttribute('role', 'group');
      if (!host.getAttribute('aria-label')) host.setAttribute('aria-label', 'Editor layout');
    });
    workspaceButtons.forEach(button => {
      const active = button.classList.contains('active') || button.classList.contains('is-active') || button.dataset.active === 'true';
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });

    const workflow = [...document.querySelectorAll('[data-action^="workflow-"]')]
      .filter(button => !button.closest('.mobile-bottom-nav,.modal-layer,.left-panel,.inspector'));
    workflow.forEach(button => {
      const active = button.classList.contains('active') || button.classList.contains('is-active') || button.dataset.active === 'true';
      if (active) button.setAttribute('aria-current', 'page');
      else if (button.getAttribute('aria-current') === 'page') button.removeAttribute('aria-current');
    });
  }

  function visibleMobileSurface() {
    if (!mobileMedia.matches) return null;
    const panel = [...document.querySelectorAll('.left-panel')].find(isVisible);
    if (panel) return {kind:'add', root:panel, label:'Add content'};
    const inspector = [...document.querySelectorAll('.inspector')].find(isVisible);
    if (inspector) return {kind:'style', root:inspector, label:'Style'};
    return null;
  }

  function restoreMobileOrigin(previous) {
    if (!previous?.origin?.isConnected || !isVisible(previous.origin)) return;
    const active = document.activeElement;
    if (active === document.body || active === document.documentElement || !isVisible(active) || previous.root.contains(active)) {
      previous.origin.focus({preventScroll:true});
    }
  }

  function enhanceMobileSurface() {
    if (!mobileMedia.matches) {
      if (activeMobileSurface) restoreMobileOrigin(activeMobileSurface);
      activeMobileSurface = null;
      return;
    }
    const surface = visibleMobileSurface();
    if (!surface) {
      if (activeMobileSurface) restoreMobileOrigin(activeMobileSurface);
      activeMobileSurface = null;
      return;
    }
    surface.root.dataset.v430P6MobileDialog = 'true';
    surface.root.setAttribute('role', 'dialog');
    surface.root.setAttribute('aria-modal', 'true');
    if (!surface.root.getAttribute('aria-label') && !surface.root.getAttribute('aria-labelledby')) {
      surface.root.setAttribute('aria-label', surface.label);
    }

    if (!activeMobileSurface || activeMobileSurface.root !== surface.root || activeMobileSurface.kind !== surface.kind) {
      if (activeMobileSurface && activeMobileSurface.root !== surface.root) restoreMobileOrigin(activeMobileSurface);
      activeMobileSurface = {
        ...surface,
        origin: mobileOrigins.get(surface.kind) || document.activeElement,
      };
    }
    if (!surface.root.contains(document.activeElement)) {
      const preferred = surface.root.querySelector('.mobile-panel-back,[data-action="close-panel"],[data-action="toggle-inspector"]');
      const target = isVisible(preferred) ? preferred : focusables(surface.root)[0];
      if (target) target.focus({preventScroll:true});
      else {
        surface.root.tabIndex = -1;
        surface.root.focus({preventScroll:true});
      }
    }
  }

  function dialogRoot() {
    const command = [...document.querySelectorAll('.command-layer .command-palette')].find(isVisible);
    if (command) return command;
    const modal = [...document.querySelectorAll('.modal-layer .modal')].find(isVisible);
    if (modal) return modal;
    return visibleMobileSurface()?.root || null;
  }

  function trapTab(event) {
    if (event.key !== 'Tab') return false;
    const root = dialogRoot();
    if (!root) return false;
    const items = focusables(root);
    if (!items.length) {
      event.preventDefault();
      root.tabIndex = -1;
      root.focus({preventScroll:true});
      return true;
    }
    const active = document.activeElement;
    if (!root.contains(active)) {
      event.preventDefault();
      (event.shiftKey ? items[items.length - 1] : items[0]).focus({preventScroll:true});
      return true;
    }
    if (!event.shiftKey && active === items[items.length - 1]) {
      event.preventDefault();
      items[0].focus({preventScroll:true});
      return true;
    }
    if (event.shiftKey && active === items[0]) {
      event.preventDefault();
      items[items.length - 1].focus({preventScroll:true});
      return true;
    }
    return false;
  }

  function navigateUtilityMenu(event) {
    const menu = document.getElementById('v430-utility-menu');
    if (!menu || menu.dataset.open !== 'true') return false;
    if (!menu.contains(event.target) && !event.target.closest?.('.v430-utility-trigger')) return false;
    const items = focusables(menu).filter(item => item.matches('[role="menuitem"],button'));
    if (!items.length) return false;
    const current = items.indexOf(document.activeElement);
    let next = null;
    if (event.key === 'ArrowDown') next = items[(current + 1 + items.length) % items.length];
    else if (event.key === 'ArrowUp') next = items[(current - 1 + items.length) % items.length];
    else if (event.key === 'Home') next = items[0];
    else if (event.key === 'End') next = items[items.length - 1];
    if (!next) return false;
    event.preventDefault();
    next.focus({preventScroll:true});
    return true;
  }

  function closeMobileSurfaceFromEscape(event) {
    if (event.key !== 'Escape' || !mobileMedia.matches) return false;
    if ([...document.querySelectorAll('.command-layer .command-palette,.modal-layer .modal')].some(isVisible)) return false;
    const surface = visibleMobileSurface();
    if (!surface) return false;
    const close = [...surface.root.querySelectorAll('.mobile-panel-back,[data-action="close-panel"],[data-action="toggle-inspector"]')]
      .find(isVisible);
    if (!close) return false;
    event.preventDefault();
    event.stopPropagation();
    close.click();
    requestAnimationFrame(scheduleEnhance);
    return true;
  }

  function themeSignature() {
    const html = document.documentElement;
    const body = document.body;
    return [html.dataset.theme || '', html.className || '', body?.dataset.theme || '', body?.className || ''].join('|');
  }

  function enhance() {
    scheduled = false;
    if (document.documentElement.dataset.screen !== 'editor') {
      if (activeMobileSurface) restoreMobileOrigin(activeMobileSurface);
      activeMobileSurface = null;
      return;
    }
    const signature = themeSignature();
    const themeChanged = signature !== lastThemeSignature;
    lastThemeSignature = signature;
    enhanceSplitters();
    enhancePreviewScroll();
    dedupeRenderedDocumentIds();
    enhanceSelectionStates();
    enhanceMobileSurface();
    enhanceContrast(themeChanged);
  }

  function scheduleEnhance() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(enhance);
  }

  document.addEventListener('click', event => {
    if (!mobileMedia.matches) return;
    const add = event.target.closest?.('.mobile-bottom-nav [data-action="workflow-content"]');
    const style = event.target.closest?.('.mobile-bottom-nav [data-mobile="style"]');
    if (add) mobileOrigins.set('add', add);
    if (style) mobileOrigins.set('style', style);
    if (add || style || event.target.closest?.('.mobile-panel-back,[data-action="close-panel"],[data-action="toggle-inspector"]')) {
      requestAnimationFrame(scheduleEnhance);
    }
  }, true);

  document.addEventListener('keydown', event => {
    if (navigateUtilityMenu(event)) return;
    if (trapTab(event)) return;
    closeMobileSurfaceFromEscape(event);
    if (event.target.closest?.('.splitter[role="separator"]')) requestAnimationFrame(scheduleEnhance);
  }, true);

  window.addEventListener('resize', scheduleEnhance, {passive:true});
  mobileMedia.addEventListener?.('change', scheduleEnhance);

  const observer = new MutationObserver(scheduleEnhance);
  function start() {
    lastThemeSignature = themeSignature();
    observer.observe(document.documentElement, {
      childList:true,
      subtree:true,
      attributes:true,
      attributeFilter:['class','data-theme','data-screen','hidden','aria-current','aria-pressed']
    });
    scheduleEnhance();
  }

  window.__manuscriptV430P6 = {
    version:'keyboard-accessibility-v1',
    refresh:scheduleEnhance,
    get activeMobileSurface() { return activeMobileSurface?.kind || null; },
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})();
</script>'''


def main() -> None:
    text = INDEX.read_text(encoding="utf-8")
    if STYLE_MARKER in text or RUNTIME_MARKER in text:
        if STYLE_MARKER in text and RUNTIME_MARKER in text and META in text:
            print("V430-P6 accessibility contract already applied")
            return
        raise SystemExit("Refusing partially applied V430-P6 contract")

    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual != BASE_SHA256:
        raise SystemExit(f"Refusing unexpected P5 baseline: sha256={actual}, expected={BASE_SHA256}")

    required = (
        'id="v430-p1-simplified-navigation"',
        'id="v430-p2-compact-density"',
        'id="v430-p3-focus-mode"',
        'id="v430-p3-runtime"',
        'id="v430-p4-command-palette"',
        'id="v430-p4-runtime"',
        'id="v430-p5-mobile-first"',
        'id="v430-p5-runtime"',
        'manuscript-mobile-first-contract" content="mobile-first-interaction-v1',
    )
    for marker in required:
        if marker not in text:
            raise SystemExit(f"Required inherited V430 contract missing: {marker}")
    if text.count('</head>') != 1 or text.count('</body>') != 1:
        raise SystemExit("Expected unique document closing anchors")

    text = text.replace('</head>', f'{META}\n{STYLE}\n</head>', 1)
    body_close = text.rfind('</body>')
    text = text[:body_close] + SCRIPT + '\n' + text[body_close:]
    INDEX.write_text(text, encoding="utf-8")

    patched = INDEX.read_text(encoding="utf-8")
    assert patched.count(STYLE_MARKER) == 1
    assert patched.count(RUNTIME_MARKER) == 1
    assert patched.count(META) == 1
    print("Applied V430-P6 accessibility and keyboard refinement")
    print("patched sha256:", hashlib.sha256(patched.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
