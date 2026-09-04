# Manuscript UI audit v4.2.3

Generated: 2026-09-04T22:14:17.872Z

## Summary

- High: 0
- Medium: 0
- Fatal profile failures: 7
- Total unique findings: 0

## desktop-wide — 1440×900

**FATAL:** locator.click: Timeout 7000ms exceeded.
Call log:
  - waiting for locator('[data-panel="templates"]').first()
    - locator resolved to <button class="rail-btn " title="Templates" data-panel="templates" aria-label="Templates">…</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="modal-layer">…</div> intercepts pointer events
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="modal-layer">…</div> intercepts pointer events
    - retrying click action
      - waiting 100ms
    13 × waiting for element to be visible, enabled and stable
       - element is visible, enabled and stable
       - scrolling into view if needed
       - done scrolling
       - <div class="modal-layer">…</div> intercepts pointer events
     - retrying click action
       - waiting 500ms

    at runProfile (/home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:156:21)
    at async file:///home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:187:17

## desktop-compact — 1024×768

**FATAL:** locator.click: Timeout 7000ms exceeded.
Call log:
  - waiting for locator('[data-panel="templates"]').first()
    - locator resolved to <button class="rail-btn " title="Templates" data-panel="templates" aria-label="Templates">…</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="modal-layer">…</div> intercepts pointer events
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="modal-layer">…</div> intercepts pointer events
    - retrying click action
      - waiting 100ms
    13 × waiting for element to be visible, enabled and stable
       - element is visible, enabled and stable
       - scrolling into view if needed
       - done scrolling
       - <div class="modal-layer">…</div> intercepts pointer events
     - retrying click action
       - waiting 500ms

    at runProfile (/home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:156:21)
    at async file:///home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:187:17

## tablet-edge — 768×1024

**FATAL:** locator.click: Timeout 7000ms exceeded.
Call log:
  - waiting for locator('[data-panel="templates"]').first()
    - locator resolved to <button class="rail-btn " title="Templates" data-panel="templates" aria-label="Templates">…</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="modal-layer">…</div> intercepts pointer events
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="modal-layer">…</div> intercepts pointer events
    - retrying click action
      - waiting 100ms
    13 × waiting for element to be visible, enabled and stable
       - element is visible, enabled and stable
       - scrolling into view if needed
       - done scrolling
       - <div class="modal-layer">…</div> intercepts pointer events
     - retrying click action
       - waiting 500ms

    at runProfile (/home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:156:21)
    at async file:///home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:187:17

## mobile-portrait — 390×844

**FATAL:** locator.click: Timeout 7000ms exceeded.
Call log:
  - waiting for locator('[data-action="workflow-content"]').first()
    - locator resolved to <button class="" data-action="workflow-content">Add</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
      - waiting 100ms
    13 × waiting for element to be visible, enabled and stable
       - element is not visible
     - retrying click action
       - waiting 500ms

    at runProfile (/home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:172:39)
    at async file:///home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:187:17

## mobile-narrow — 360×800

**FATAL:** locator.click: Timeout 7000ms exceeded.
Call log:
  - waiting for locator('[data-action="workflow-content"]').first()
    - locator resolved to <button class="" data-action="workflow-content">Add</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
      - waiting 100ms
    13 × waiting for element to be visible, enabled and stable
       - element is not visible
     - retrying click action
       - waiting 500ms

    at runProfile (/home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:172:39)
    at async file:///home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:187:17

## mobile-small — 320×568

**FATAL:** locator.click: Timeout 7000ms exceeded.
Call log:
  - waiting for locator('[data-action="workflow-content"]').first()
    - locator resolved to <button class="" data-action="workflow-content">Add</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
      - waiting 100ms
    13 × waiting for element to be visible, enabled and stable
       - element is not visible
     - retrying click action
       - waiting 500ms

    at runProfile (/home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:172:39)
    at async file:///home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:187:17

## mobile-landscape — 740×390

**FATAL:** locator.click: Timeout 7000ms exceeded.
Call log:
  - waiting for locator('[data-action="workflow-content"]').first()
    - locator resolved to <button class="" data-action="workflow-content">Add</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
      - waiting 100ms
    13 × waiting for element to be visible, enabled and stable
       - element is not visible
     - retrying click action
       - waiting 500ms

    at runProfile (/home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:172:39)
    at async file:///home/runner/work/manuscript/manuscript/scripts/audit-ui-v423.mjs:187:17

