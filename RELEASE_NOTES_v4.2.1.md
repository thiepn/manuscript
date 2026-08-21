# Manuscript v4.2.1 Stable

This release promotes the certified Manuscript v4.2.1 production build.

## Release highlights

- Reconstructed screen-scoped scroll ownership: ordinary document scrolling on Landing/Home; viewport locking only in the editor.
- Explicit editor scroll owners for CodeMirror, preview, left-panel content, Inspector content, and modal bodies.
- Six persistent interface themes: Editorial Ivory, Graphite Studio, Oxford, Typesetter, Blueprint, and Ink.
- Fixed persistence for all curated themes so Oxford, Typesetter, Blueprint, and Ink survive reloads just like light/dark.
- WCAG-AA-hardened theme text/accent contrast and semantic dark-mode behavior.
- Consolidated editorial visual architecture with quieter chrome, compact geometry, flatter panels, and stronger document focus.
- Production integration against the exact RC6 source with deterministic SHA-256 verification.

## Certified artifact

`Manuscript_v4.2.1_Stable.html`

SHA-256:

`6d3900a2c973dc2d36099fc596b77b21268c11fdc1cff46bba7e66f08d83aba6`

## Browser certification

The release workflow certifies the real Stable bytes in Chromium, Firefox, and WebKit, plus mobile/touch viewport emulation. This is multi-engine browser certification; it is not a substitute for a final physical Android/iOS hardware spot-check.