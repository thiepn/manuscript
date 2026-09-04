# Manuscript v4.2.3 Stable

v4.2.3 is a responsive-UI hardening release built from the certified v4.2.2 Stable artifact.

## Fixed

- Restored the intended overlay behavior for the left workspace panel below 1200px so opening Files, Outline, Search, Insert, Media, References, Checks, and related tools no longer consumes a phantom grid column.
- Removed rigid Split-pane minimum widths in compact layouts so the editor workspace no longer exceeds the viewport around 1024px.
- Reworked the 768–900px Split layout into a usable vertical editor/preview stack instead of collapsing the editor into a narrow grid cell or silently behaving like Write mode.
- Prevented compact preview controls from extending past the right edge by simplifying direct page-jump controls where horizontal space is constrained.
- Made References and Settings utility actions wrap safely so long labels such as CSL export, persistence, backup export, and restore are no longer clipped.
- Protected the 768px app-bar Export control from flex shrink so its label remains fully visible.
- Made modal action footers wrap safely rather than shrinking labels into clipped buttons.
- Made the mobile onboarding primary action occupy a full footer row, with all modal footer actions stacking cleanly on very narrow screens.
- Restored fixed full-screen overlay positioning for mobile Add, Style, and inspector surfaces so they no longer participate in the editor document flow.
- Constrained short-landscape modals to the visual viewport and removed transform-based modal entrance motion only in that constrained layout so no animation frame can extend below the screen.
- Preserved the v4.2.2 Write/Preview exclusivity and mobile editor-height fixes.
- Bumped the offline shell cache to v4.2.3 so deployed clients can receive the corrected UI.

## Certification

The release gate covers desktop, compact desktop, the exact 768px tablet boundary, narrow mobile, 320px small mobile, and mobile landscape. It exercises Chromium, Firefox, and WebKit where applicable, verifies long utility controls and mobile overlays explicitly, and runs a separate broad Chromium UI sweep across major screens, workspace modes, panels, modals, themes, overflow, clipping, and responsive breakpoints.

The final release is published only after the dedicated v4.2.3 multi-engine certification, targeted responsive checks, and broad UI sweep report no unresolved UI findings.
