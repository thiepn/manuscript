#!/usr/bin/env python3
from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

STYLE_ID = 'v430-p4-command-palette'
SCRIPT_ID = 'v430-p4-runtime'
CONTRACT = 'discoverable-fast-actions-v1'

if f'id="{STYLE_ID}"' in text and f'id="{SCRIPT_ID}"' in text:
    print('V430-P4 command-palette contract already applied')
    raise SystemExit(0)

for required in (
    'id="v430-p1-simplified-navigation"',
    'id="v430-p1-runtime"',
    'id="v430-p2-compact-density"',
    'id="v430-p3-focus-mode"',
    'id="v430-p3-runtime"',
):
    if required not in text:
        raise SystemExit(f'Prerequisite contract missing: {required}')

if '</head>' not in text or '</body>' not in text:
    raise SystemExit('HTML injection anchors missing')

# Register Focus Mode in the existing command registry. Execution still flows
# through the application's normal application-command executor.
registry_anchor = "    { id: 'toggle-inspector', label: 'Toggle inspector', kind: 'application', category: 'view', editorOnly: true },"
focus_definition = "    { id: 'focus-mode', label: 'Toggle Focus Mode', kind: 'application', category: 'view', editorOnly: true, keywords: ['focus', 'distraction free', 'writing'] },"
if focus_definition not in text:
    if registry_anchor not in text:
        raise SystemExit('Command-registry insertion anchor missing')
    text = text.replace(registry_anchor, registry_anchor + '\n' + focus_definition, 1)

# Delegate the new registry command to the already-certified P3 runtime.
action_anchor = """            case 'command':
                openCommandPalette();
                break;"""
focus_action = """            case 'focus-mode':
                window.__manuscriptV430P3?.toggle();
                break;
            case 'command':
                openCommandPalette();
                break;"""
if focus_action not in text:
    if action_anchor not in text:
        raise SystemExit('Application-command execution anchor missing')
    text = text.replace(action_anchor, focus_action, 1)

style = r'''
<meta name="manuscript-command-palette-contract" content="discoverable-fast-actions-v1">
<style id="v430-p4-command-palette">
/* V430-P4 — Command Palette & Fast Actions
   The existing native command registry remains authoritative. P4 improves
   discoverability and exposes a curated fast-action surface without adding a
   parallel command executor. Mobile navigation changes remain deferred to P5. */
html[data-screen="editor"] .appbar > [data-action="command"]:not(.v430-command-trigger) {
  display: none !important;
}

html[data-screen="editor"] .v430-command-trigger {
  flex: 0 0 auto;
  width: 34px !important;
  min-width: 34px;
  height: 32px;
  min-height: 32px;
  padding: 0 !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 1px solid transparent !important;
  background: transparent !important;
  box-shadow: none !important;
  color: inherit;
  opacity: .72;
}

html[data-screen="editor"] .v430-command-trigger:hover,
html[data-screen="editor"] .v430-command-trigger:focus-visible,
html[data-screen="editor"] .v430-command-trigger[aria-expanded="true"] {
  background: var(--v430-hover, var(--surface-hover)) !important;
  opacity: 1;
}

.v430-command-glyph {
  width: 16px;
  height: 16px;
  display: inline-grid;
  place-items: center;
  font-size: 16px;
  line-height: 1;
}

.v430-command-label,
.v430-command-shortcut {
  display: none;
}

@media (min-width: 1200px) {
  html[data-screen="editor"] .v430-command-trigger {
    width: auto !important;
    min-width: 132px;
    padding-inline: 10px !important;
  }

  .v430-command-label {
    display: inline;
    font-size: 12px;
    line-height: 1;
    white-space: nowrap;
  }

  .v430-command-shortcut {
    display: inline-flex;
    align-items: center;
    min-height: 20px;
    padding: 0 5px;
    border: 1px solid var(--v430-line, var(--border-default));
    border-radius: 4px;
    background: var(--v430-soft, var(--surface-2));
    color: var(--text-muted);
    font: 10px/1 var(--mono);
    white-space: nowrap;
  }
}

@media (max-width: 767px) {
  .v430-command-trigger { display: none !important; }
}

.command-layer .v430-command-palette {
  width: min(660px, 94vw);
}

.v430-command-fast {
  padding: 10px 12px 11px;
  border-bottom: 1px solid var(--divider);
  background: var(--surface-2);
}

.v430-command-fast[hidden] {
  display: none !important;
}

.v430-command-fast-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 7px;
  color: var(--text-muted);
  font-size: 10px;
  line-height: 1.2;
  letter-spacing: .07em;
  text-transform: uppercase;
}

.v430-command-fast-head span:last-child {
  letter-spacing: 0;
  text-transform: none;
  font-family: var(--mono);
  font-size: 9px;
}

.v430-command-fast-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}

.v430-command-fast-btn {
  min-width: 0;
  min-height: 38px;
  padding: 0 9px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  background: var(--surface-1);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 7px;
  font-size: 11px;
  font-weight: 600;
  text-align: left;
}

/* Touch users need a genuine target, not a nominal 38px rule that can be
   compressed by inherited mobile/coarse-pointer styles. Keep desktop compact
   while making tablet/mobile quick actions comfortably tappable. */
@media (pointer: coarse) {
  .command-layer .v430-command-fast-btn {
    min-height: 46px !important;
  }
}

.v430-command-fast-btn:hover,
.v430-command-fast-btn:focus-visible {
  background: var(--surface-hover);
  border-color: var(--border-strong);
}

.v430-command-fast-btn:disabled {
  opacity: .43;
  cursor: not-allowed;
}

.v430-command-fast-btn kbd {
  flex: 0 0 auto;
  padding: 2px 4px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  color: var(--text-muted);
  background: var(--surface-2);
  font: 9px/1 var(--mono);
}

.v430-command-hint {
  min-height: 28px;
  padding: 6px 12px;
  border-top: 1px solid var(--divider);
  color: var(--text-muted);
  background: var(--surface-2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 10px;
}

.v430-command-hint kbd {
  font-family: var(--mono);
  font-size: 9px;
  white-space: nowrap;
}

@media (max-width: 520px) {
  .v430-command-fast-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .v430-command-fast-head span:last-child { display: none; }
  .v430-command-hint { font-size: 9px; }
}

@media (prefers-reduced-motion: reduce) {
  html[data-screen="editor"] .v430-command-trigger { transition: none !important; }
}
</style>
'''

script = r'''
<script id="v430-p4-runtime">
(() => {
  'use strict';
  if (window.__manuscriptV430P4) return;

  const root = document.documentElement;
  const desktop = window.matchMedia('(min-width: 768px)');
  const fastActions = [
    { id: 'save-local', label: 'Save', shortcut: 'mod+s' },
    { id: 'export', label: 'Export', shortcut: 'mod+shift+e' },
    { id: 'focus-mode', label: 'Focus', shortcut: '' },
    { id: 'workflow-write', label: 'Write', shortcut: '' },
    { id: 'workflow-preview', label: 'Preview', shortcut: '' },
    { id: 'workflow-publish', label: 'Publish', shortcut: '' },
  ];

  let trigger = null;
  let scheduled = false;
  let observer = null;

  function isMac() {
    return /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent || '');
  }

  function shortcutLabel(token) {
    if (!token) return '';
    const mac = isMac();
    return token
      .replace('mod', mac ? '⌘' : 'Ctrl')
      .replace('shift', mac ? '⇧' : 'Shift')
      .replaceAll('+', mac ? '' : '+')
      .replace(/\b([a-z])\b/gi, value => value.toUpperCase());
  }

  function commandShortcut() {
    return isMac() ? '⌘K' : 'Ctrl K';
  }

  function ensureTrigger() {
    if (!desktop.matches || root.dataset.screen !== 'editor') {
      trigger?.remove();
      trigger = null;
      return;
    }

    const appbar = document.querySelector('.appbar,.v430-appbar');
    if (!appbar) return;

    trigger = appbar.querySelector(':scope > .v430-command-trigger');
    if (!trigger) {
      trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'icon-btn v430-command-trigger';
      trigger.dataset.action = 'command';
      trigger.setAttribute('aria-label', 'Open command palette');
      trigger.setAttribute('aria-haspopup', 'dialog');
      trigger.setAttribute('aria-expanded', 'false');
      trigger.setAttribute('title', 'Command palette · Ctrl/Cmd+K');
      trigger.innerHTML = `<span class="v430-command-glyph" aria-hidden="true">⌕</span><span class="v430-command-label">Commands</span><kbd class="v430-command-shortcut">${commandShortcut()}</kbd>`;

      const exportButton = [...appbar.children].find(el => el.matches?.('[data-action="export"]'));
      const moreButton = [...appbar.children].find(el => el.matches?.('[data-action="more"]'));
      if (exportButton) exportButton.before(trigger);
      else if (moreButton) moreButton.before(trigger);
      else appbar.append(trigger);
    }
  }

  function syncFocusFastAction(section) {
    const button = section?.querySelector('[data-command-action="focus-mode"]');
    if (!button) return;
    const focus = window.__manuscriptV430P3;
    const active = focus?.active === true;
    const eligible = focus?.eligible === true;
    button.disabled = !active && !eligible;
    button.setAttribute('aria-disabled', String(button.disabled));
    const label = button.querySelector('[data-v430-fast-label]');
    if (label) label.textContent = active ? 'Exit Focus' : 'Focus';
  }

  function decoratePalette(layer) {
    if (!(layer instanceof HTMLElement) || layer.dataset.v430P4 === 'true') return;
    const palette = layer.querySelector('.command-palette');
    const input = layer.querySelector('#command-search');
    const list = layer.querySelector('#command-list');
    if (!palette || !input || !list) return;

    layer.dataset.v430P4 = 'true';
    palette.classList.add('v430-command-palette');
    input.setAttribute('placeholder', 'Search commands or actions…');
    input.setAttribute('aria-describedby', 'v430-command-hint');

    const section = document.createElement('section');
    section.className = 'v430-command-fast';
    section.setAttribute('aria-label', 'Quick actions');
    section.innerHTML = `
      <div class="v430-command-fast-head"><span>Quick actions</span><span>${commandShortcut()} · all commands</span></div>
      <div class="v430-command-fast-grid">
        ${fastActions.map(action => `<button type="button" class="v430-command-fast-btn" data-command-action="${action.id}"><span data-v430-fast-label>${action.label}</span>${action.shortcut ? `<kbd>${shortcutLabel(action.shortcut)}</kbd>` : ''}</button>`).join('')}
      </div>`;
    palette.insertBefore(section, list);

    const hint = document.createElement('div');
    hint.id = 'v430-command-hint';
    hint.className = 'v430-command-hint';
    hint.innerHTML = '<span>Type to filter commands</span><kbd>↑ ↓ navigate · Enter run · Esc close</kbd>';
    palette.append(hint);

    const sync = () => {
      section.hidden = !!input.value.trim();
      syncFocusFastAction(section);
    };
    input.addEventListener('input', sync);
    layer.addEventListener('focusin', () => syncFocusFastAction(section));
    sync();
  }

  function syncPalette() {
    const layer = document.querySelector('.command-layer');
    if (layer) {
      decoratePalette(layer);
      if (trigger?.isConnected) trigger.setAttribute('aria-expanded', 'true');
    } else if (trigger?.isConnected) {
      trigger.setAttribute('aria-expanded', 'false');
    }
  }

  function sync() {
    scheduled = false;
    ensureTrigger();
    syncPalette();
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
      attributeFilter: ['data-screen', 'class'],
    });
    desktop.addEventListener?.('change', schedule);
  }

  window.__manuscriptV430P4 = {
    sync: schedule,
    get trigger() { return trigger; },
    get fastActions() { return fastActions.map(item => ({ ...item })); },
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
print('Applied V430-P4 discoverable command palette and fast actions')
