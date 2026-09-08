#!/usr/bin/env python3
from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

STYLE_ID = 'v430-p3-focus-mode'
SCRIPT_ID = 'v430-p3-runtime'
CONTRACT = 'distraction-free-writing-v1'

if f'id="{STYLE_ID}"' in text and f'id="{SCRIPT_ID}"' in text:
    print('V430-P3 focus-mode contract already applied')
    raise SystemExit(0)

for required in (
    'id="v430-p1-simplified-navigation"',
    'id="v430-p1-runtime"',
    'id="v430-p2-compact-density"',
):
    if required not in text:
        raise SystemExit(f'Prerequisite contract missing: {required}')
if '</head>' not in text or '</body>' not in text:
    raise SystemExit('HTML injection anchors missing')

style = r'''
<meta name="manuscript-focus-mode-contract" content="distraction-free-writing-v1">
<style id="v430-p3-focus-mode">
/* V430-P3 — Focus Mode
   A reversible presentation layer over the certified editor state. It never
   mutates workspace mode, panel state, inspector state, document content, or
   mobile navigation. Mobile-first focus interaction remains deferred to P5. */
html[data-screen="editor"] .v430-focus-trigger {
  flex: 0 0 auto;
  width: auto !important;
  min-width: 34px;
  height: 32px;
  padding: 0 9px !important;
  gap: 6px;
  border: 1px solid transparent !important;
  background: transparent !important;
  box-shadow: none !important;
  color: inherit;
  opacity: .72;
}

html[data-screen="editor"] .v430-focus-trigger:hover,
html[data-screen="editor"] .v430-focus-trigger:focus-visible,
html[data-screen="editor"] .v430-focus-trigger[aria-pressed="true"] {
  background: var(--v430-hover, var(--surface-hover)) !important;
  opacity: 1;
}

.v430-focus-glyph {
  display: inline-grid;
  place-items: center;
  width: 16px;
  height: 16px;
  font-size: 14px;
  line-height: 1;
}

.v430-focus-label {
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
}

@media (min-width: 768px) and (max-width: 1199px) {
  html[data-screen="editor"] .v430-focus-trigger:not([aria-pressed="true"]) {
    width: 34px !important;
    padding-inline: 0 !important;
  }
  html[data-screen="editor"] .v430-focus-trigger:not([aria-pressed="true"]) .v430-focus-label {
    display: none;
  }
}

@media (min-width: 768px) {
  html[data-screen="editor"][data-v430-focus="true"] .appbar {
    height: 44px !important;
    flex-basis: 44px !important;
    gap: 8px !important;
    padding-inline: clamp(12px, 3vw, 36px) !important;
    border-bottom-color: var(--v430-line, var(--border-subtle)) !important;
    box-shadow: none !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .appbar > :not(.doc-title-wrap):not(.appbar-spacer):not(.v430-focus-trigger) {
    display: none !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .doc-title-wrap {
    flex: 0 1 620px;
    min-width: 0;
  }

  html[data-screen="editor"][data-v430-focus="true"] .doc-title {
    width: min(620px, 52vw) !important;
    max-width: 100%;
  }

  html[data-screen="editor"][data-v430-focus="true"] .v430-focus-trigger {
    width: auto !important;
    min-width: 88px;
    padding-inline: 10px !important;
    border-color: var(--v430-line, var(--border-default)) !important;
    background: var(--v430-soft, var(--surface-2)) !important;
    opacity: 1;
  }

  html[data-screen="editor"][data-v430-focus="true"] .v430-focus-label {
    display: inline !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .toolbar,
  html[data-screen="editor"][data-v430-focus="true"] .activity-rail,
  html[data-screen="editor"][data-v430-focus="true"] .left-panel,
  html[data-screen="editor"][data-v430-focus="true"] .inspector,
  html[data-screen="editor"][data-v430-focus="true"] .preview-pane,
  html[data-screen="editor"][data-v430-focus="true"] .splitter,
  html[data-screen="editor"][data-v430-focus="true"] .statusbar,
  html[data-screen="editor"][data-v430-focus="true"] #v430-utility-menu {
    display: none !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .workspace,
  html[data-screen="editor"][data-v430-focus="true"] .workspace.left-open,
  html[data-screen="editor"][data-v430-focus="true"] .workspace.inspector-closed,
  html[data-screen="editor"][data-v430-focus="true"] .workspace.left-open.inspector-closed {
    grid-template-columns: minmax(0, 1fr) !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .main-stage {
    min-width: 0;
    width: 100%;
  }

  html[data-screen="editor"][data-v430-focus="true"] .editor-preview,
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
  }

  html[data-screen="editor"][data-v430-focus="true"] .editor-pane .pane-head {
    display: none !important;
  }

  html[data-screen="editor"][data-v430-focus="true"] .editor-shell {
    width: 100%;
    min-width: 0;
  }
}

@media (max-width: 767px) {
  .v430-focus-trigger { display: none !important; }
  html[data-v430-focus="true"] { --v430-focus-mobile-leak: 0; }
}

@media (prefers-reduced-motion: reduce) {
  html[data-screen="editor"] .v430-focus-trigger { transition: none !important; }
}
</style>
'''

script = r'''
<script id="v430-p3-runtime">
(() => {
  'use strict';
  if (window.__manuscriptV430P3) return;

  const root = document.documentElement;
  const media = window.matchMedia('(min-width: 768px)');
  let active = false;
  let trigger = null;
  let observer = null;
  let scheduled = false;

  function workspaceMode() {
    const activeButton = [...document.querySelectorAll('[data-workspace].active,[data-workspace][aria-pressed="true"]')]
      .find(el => !el.closest('.modal-layer,.left-panel,.inspector,.mobile-bottom-nav'));
    return activeButton?.getAttribute('data-workspace') || '';
  }

  function editorReady() {
    return root.dataset.screen === 'editor' && !!document.querySelector('.editor-pane,.codemirror-editor,.native-editor-host');
  }

  function eligible() {
    const mode = workspaceMode();
    return media.matches && editorReady() && (mode === 'editor' || mode === 'split');
  }

  function setAttr(el, name, value) {
    if (el.getAttribute(name) !== value) el.setAttribute(name, value);
  }

  function setTriggerState() {
    if (!trigger?.isConnected) return;
    const pressed = active ? 'true' : 'false';
    const ariaLabel = active ? 'Exit focus mode' : 'Enter focus mode';
    const title = active ? 'Exit focus mode · Esc' : 'Focus mode';
    const copy = active ? 'Exit Focus' : 'Focus';
    setAttr(trigger, 'aria-pressed', pressed);
    setAttr(trigger, 'aria-label', ariaLabel);
    setAttr(trigger, 'title', title);
    const label = trigger.querySelector('.v430-focus-label');
    if (label && label.textContent !== copy) label.textContent = copy;
    const disabled = !active && !eligible();
    if (trigger.disabled !== disabled) trigger.disabled = disabled;
  }

  function focusEditor() {
    const candidates = [
      '.codemirror-editor .cm-content',
      '.codemirror-editor .cm-scroller',
      '.markdown-editor',
      'textarea[aria-label*="Markdown"]',
      '#native-editor-host',
    ];
    for (const selector of candidates) {
      const node = document.querySelector(selector);
      if (!node) continue;
      if (node instanceof HTMLElement) {
        try { node.focus({ preventScroll: true }); } catch {}
      }
      break;
    }
  }

  function enter() {
    if (active || !eligible()) return false;
    active = true;
    root.dataset.v430Focus = 'true';
    setTriggerState();
    requestAnimationFrame(focusEditor);
    return true;
  }

  function exit({ restoreFocus = true } = {}) {
    if (!active) return false;
    active = false;
    delete root.dataset.v430Focus;
    setTriggerState();
    if (restoreFocus && trigger?.isConnected) {
      requestAnimationFrame(() => trigger?.focus({ preventScroll: true }));
    }
    return true;
  }

  function toggle() {
    return active ? exit() : enter();
  }

  function ensureTrigger() {
    if (!media.matches || root.dataset.screen !== 'editor') {
      if (active) exit({ restoreFocus: false });
      trigger?.remove();
      trigger = null;
      return;
    }

    const appbar = document.querySelector('.appbar,.v430-appbar');
    if (!appbar) return;

    trigger = appbar.querySelector('.v430-focus-trigger');
    if (!trigger) {
      trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'icon-btn v430-focus-trigger';
      trigger.dataset.v430FocusTrigger = 'true';
      trigger.innerHTML = '<span class="v430-focus-glyph" aria-hidden="true">◐</span><span class="v430-focus-label">Focus</span>';
      trigger.addEventListener('click', event => {
        event.preventDefault();
        event.stopPropagation();
        toggle();
      });
      const spacer = [...appbar.children].find(el => el.classList?.contains('appbar-spacer'));
      if (spacer) spacer.before(trigger);
      else appbar.append(trigger);
    }
    setTriggerState();
  }

  function sync() {
    scheduled = false;
    if (active && (!media.matches || !editorReady() || !['editor','split'].includes(workspaceMode()))) {
      exit({ restoreFocus: false });
    }
    ensureTrigger();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(sync);
  }

  function onKeydown(event) {
    if (!active || event.key !== 'Escape' || event.defaultPrevented) return;
    const modal = [...document.querySelectorAll('.modal-layer')].find(el => {
      if (!(el instanceof HTMLElement)) return false;
      const s = getComputedStyle(el);
      return s.display !== 'none' && s.visibility !== 'hidden' && el.getBoundingClientRect().width > 0;
    });
    if (modal) return;
    event.preventDefault();
    event.stopPropagation();
    exit();
  }

  function boot() {
    ensureTrigger();
    observer = new MutationObserver(schedule);
    observer.observe(document.documentElement, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['data-screen', 'class', 'aria-pressed'],
    });
    document.addEventListener('keydown', onKeydown, true);
    media.addEventListener?.('change', schedule);
  }

  window.__manuscriptV430P3 = {
    get active() { return active; },
    get eligible() { return eligible(); },
    enter,
    exit,
    toggle,
    sync: schedule,
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
print('Applied V430-P3 reversible focus mode')
