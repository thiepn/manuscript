# Manuscript v4.2.3 Stable

v4.2.3 is a responsive-UI hardening release built from the certified v4.2.2 Stable artifact.

## Fixed

- Restored the intended overlay behavior for the left workspace panel below 1200px so opening Files, Outline, Search, Insert, Media, References, Checks, and related tools no longer consumes a phantom grid column.
- Removed rigid Split-pane minimum widths in compact layouts so the editor workspace no longer exceeds the viewport around 1024px.
- Reworked the 768–900px Split layout into a usable vertical editor/preview stack instead of collapsing the editor into a narrow grid cell or silently behaving like Write mode.
- Prevented compact preview controls from extending past the right edge by simplifying direct page-jump controls where horizontal space is constrained.
- Made modal action footers wrap safely rather than shrinking labels into clipped buttons.
- Made the mobile onboarding primary action occupy a full footer row, with all modal footer actions stacking cleanly on very narrow screens.
- Preserved the v4.2.2 Write/Preview exclusivity and mobile editor-height fixes.
- Bumped the offline shell cache to v4.2.3 so deployed clients can receive the corrected UI.

## Certification

The release gate covers desktop, compact desktop, the 768px tablet boundary, narrow mobile, small mobile, and mobile landscape. It exercises Chromium, Firefox, and WebKit where applicable, plus a separate broad Chromium UI sweep across major screens, workspace modes, panels, modals, and responsive breakpoints.

The final release is published only after both the dedicated v4.2.3 certification and broad UI sweep report no actionable UI findings.
