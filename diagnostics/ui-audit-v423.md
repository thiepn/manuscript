# Manuscript UI audit v4.2.3

Generated: 2026-09-04T22:16:55.597Z

## Summary

- High: 7
- Medium: 4
- Fatal profile failures: 0
- Total unique findings: 11

## desktop-wide — 1440×900

No findings.

## desktop-compact — 1024×768

- **HIGH CONTROL_OFFSCREEN** · panel-diagnostics · `button.icon-btn[data-action="margin-guides"]` — Interactive control extends outside viewport · {"rect":{"left":1025.625,"right":1050,"width":24.375},"vw":1024}

## tablet-edge — 768×1024

- **MEDIUM CONTROL_TEXT_CLIPPED** · modal-export · `button.btn.primary[data-action="export"]` — Control content is horizontally clipped · {"clientWidth":69,"scrollWidth":73}
- **HIGH MOBILE_NAV_MISSING** · editor-default · `document` — Mobile editor navigation is not visible · {}
- **HIGH COLLAPSED_EDITOR_SURFACE** · panel-insert · `section.editor-pane` — Editor/preview surface has unusably small height · {"height":32,"width":46}

## mobile-portrait — 390×844

- **MEDIUM CONTROL_TEXT_CLIPPED** · home · `button.btn.primary[data-action="onboarding-blank"]` — Control content is horizontally clipped · {"clientWidth":98,"scrollWidth":129}
- **HIGH COLLAPSED_EDITOR_SURFACE** · mobile-theme-modal · `section.editor-pane` — Editor/preview surface has unusably small height · {"height":20.0625,"width":390}

## mobile-narrow — 360×800

- **MEDIUM CONTROL_TEXT_CLIPPED** · home · `button.btn.primary[data-action="onboarding-blank"]` — Control content is horizontally clipped · {"clientWidth":68,"scrollWidth":114}
- **HIGH COLLAPSED_EDITOR_SURFACE** · mobile-theme-modal · `section.editor-pane` — Editor/preview surface has unusably small height · {"height":18.875,"width":360}

## mobile-small — 320×568

- **MEDIUM CONTROL_TEXT_CLIPPED** · home · `button.btn.primary[data-action="onboarding-blank"]` — Control content is horizontally clipped · {"clientWidth":28,"scrollWidth":94}
- **HIGH COLLAPSED_EDITOR_SURFACE** · mobile-theme-modal · `section.editor-pane` — Editor/preview surface has unusably small height · {"height":12.640625,"width":320}

## mobile-landscape — 740×390

- **HIGH COLLAPSED_EDITOR_SURFACE** · mobile-theme-modal · `section.editor-pane` — Editor/preview surface has unusably small height · {"height":7.859375,"width":740}

