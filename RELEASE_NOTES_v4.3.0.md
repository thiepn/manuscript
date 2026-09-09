# Manuscript v4.3.0 Stable

Released: 2026-09-09

Manuscript v4.3.0 is the release-hardened writing-experience update built on the v4.2.3 stable baseline. It keeps the local-first, single-file publishing model while substantially refining navigation, focus, commands, mobile interaction, keyboard accessibility, responsive behavior, and release reliability.

## Highlights

- **Simplified navigation:** clearer editor hierarchy with lower-frequency actions consolidated without duplicating application state.
- **Compact writing density:** tighter, more efficient workspace geometry while preserving readability and existing document behavior.
- **Focus Mode:** distraction-reduced writing using the existing editor state rather than a parallel workflow.
- **Command palette:** keyboard-first command access with the existing command/action system as the source of truth.
- **Mobile-first interaction:** preserved five-action bottom navigation, dedicated mobile command access, viewport-safe sheets/modals, safe-area handling, and 44px+ touch targets.
- **Accessibility and keyboard refinement:** dialog semantics, focus containment/restoration, keyboard menu navigation, accessible preview/splitter semantics, unique rendered IDs, and WCAG AA contrast hardening.
- **Responsive hardening:** dense breakpoint coverage, live 767/768 transitions, low-height command containment, 200% text scaling, forced-colors/reduced-motion coverage, long-content stress, and repeated Chromium/Firefox/WebKit resize testing.
- **Stable release hardening:** v4.3.0 release identity, service-worker cache namespace `manuscript-shell-v4.3.0`, offline-shell verification, and a final toast-title AA correction found by the complete release ladder.

## Certification

The final release candidate passed:

- P8 stable-release certification: **5/5 suites**
- P1: **6/6**
- P2: **5/5**
- P3: **5/5**
- P4: **5/5**
- P5: **8/8**
- P6: **6/6**
- P7: **9/9**
- inherited v4.2.3 Chromium/Firefox/WebKit certification
- inherited targeted UI certification
- broad UI sweep with **0 findings / 0 fatal findings**
- service-worker offline reload using the v4.3.0 shell cache

## Integrity

Canonical standalone HTML SHA-256:

`11155dbeac358f6c0706a2d7c4f45db4ffc50ab8327846aa2dec9b7692509a7e`

The downloadable Stable HTML published with this release is required to match that digest exactly.
