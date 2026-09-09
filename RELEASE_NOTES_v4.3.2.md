# Manuscript v4.3.2 Stable

Released: 2026-09-09

## UI regression hardening

- Removes two literal `\n` tokens that caused Chromium to terminate `<head>` early, reparent later style/meta nodes into `<body>`, and render a visible strip above the app.
- Reserves fixed mobile bottom-navigation height so editor and preview content never extend under navigation.
- Enlarges compact coarse-pointer actions and restores mobile toolbar target width while retaining desktop density.
- Keeps bottom-sheet modals within very small phone viewports, including while their entrance transition is settling.
- Retains the v4.3.1 Markdown learning examples and publishing behavior.

## Verification

Certified with the legacy multi-viewport sweep and a deeper Chromium audit covering 320, 360, 390, 480, 767, 768, 900, 901, 1024, and 1440px widths; Template Gallery geometry; editor/preview modes; mobile navigation clearance; touch targets; root DOM structure; overflow; and runtime errors.

Canonical standalone HTML SHA-256:

`23e110fbc28f013a05bd94a0b196b30e76d74d900883403ad67d1734b2a1a9db`
