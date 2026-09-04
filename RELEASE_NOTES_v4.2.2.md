# Manuscript v4.2.2 Stable

v4.2.2 is a focused editor-layout hotfix built from the certified v4.2.1 Stable release.

## Fixed

- **Desktop Write mode:** now displays only the Markdown editor instead of leaving the rendered preview visible.
- **Desktop Preview mode:** now displays only the rendered document instead of leaving the editor visible.
- **Desktop Split mode:** continues to display the editor and preview together with the resize splitter.
- **Mobile editor layout:** restores the bounded flex-height chain below the viewport-locked app shell so CodeMirror receives a usable height.
- **Mobile preview layout:** preserves a usable preview scroll surface in both portrait and landscape layouts.
- **Mobile mode switching:** switching Preview → Write restores the editor correctly.
- **Offline update path:** service-worker cache version is bumped to v4.2.2 so clients can receive the repaired shell.

## Regression certification

The Stable artifact is certified with Playwright across seven browser/device profiles:

- Chromium desktop
- Firefox desktop
- WebKit desktop
- Chromium mobile portrait
- WebKit mobile portrait
- Chromium mobile landscape
- WebKit mobile landscape

The certification explicitly exercises Write, Split, and Preview pane exclusivity; CodeMirror/editor dimensions; preview dimensions; mobile bottom-navigation switching; viewport locking; and root overflow behavior.

## Integrity

`index.html` SHA-256:

`deb838e5868c4f944fab92aa508170c1f046dd5faa66f2ce4bcf2951c5269606`
