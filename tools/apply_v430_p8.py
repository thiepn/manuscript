#!/usr/bin/env python3
"""Apply Manuscript v4.3.0 P8 stable-release identity to certified P7.

P8 promotes the already-certified P1-P7 product to stable release identity,
bumps the service-worker cache, closes the one release-ladder AA toast-title
edge case, and writes the canonical SHA-256 file used by release CI.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

INDEX = Path("index.html")
SW = Path("sw.js")
HASH_FILE = Path("V430_SHA256.txt")
BASE_SHA256 = "8619c74a18ad80eb76b8ce6a67787509058b0ae70d7f0823cbdc8fce8359af3d"
RELEASE_META = '<meta name="manuscript-release-contract" content="v4.3.0-stable-certified-v1">'
OLD_NAME = "Manuscript v4.2.3 Stable"
NEW_NAME = "Manuscript v4.3.0 Stable"
TOAST_AA_OLD = '''html[data-screen="editor"] .toast .toast-text,
html[data-screen="editor"] .status-action[data-panel="diagnostics"] {'''
TOAST_AA_NEW = '''html[data-screen="editor"] .toast .toast-title,
html[data-screen="editor"] .toast .toast-text,
html[data-screen="editor"] .status-action[data-panel="diagnostics"] {'''


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_applied(index: str, sw: str) -> None:
    required = (
        RELEASE_META,
        '<title>Manuscript v4.3.0 Stable</title>',
        'content="Manuscript v4.3.0 Stable — local-first Markdown publishing studio',
        "exports.APP_VERSION = '4.3.0';",
        "exports.RELEASE_NAME = 'Manuscript v4.3.0 Stable';",
        "exports.RELEASE_PHASE = 'V430-P8 — RC Certification & Stable Release';",
        'id="v430-p7-responsive-hardening"',
        'id="v430-p7-runtime"',
        'manuscript-hardening-contract" content="full-regression-responsive-v1',
    )
    for marker in required:
        if index.count(marker) != 1:
            raise SystemExit(f"Applied P8 identity missing/duplicated: {marker}")
    if index.count('<meta name="manuscript-release-contract"') != 1:
        raise SystemExit("Release contract meta duplicated")
    if index.count(TOAST_AA_NEW) != 1 or TOAST_AA_OLD in index:
        raise SystemExit("Stable toast-title AA correction missing, duplicated, or stale")
    if "exports.APP_VERSION = '4.2.3';" in index or "exports.RELEASE_NAME = 'Manuscript v4.2.3 Stable';" in index:
        raise SystemExit("Stale live v4.2.3 release identity remains")
    if sw.count("`${CACHE_PREFIX}v4.3.0`") != 1 or "`${CACHE_PREFIX}v4.2.3`" in sw:
        raise SystemExit("Service-worker stable cache identity is not v4.3.0")
    if not HASH_FILE.exists():
        raise SystemExit("V430_SHA256.txt missing")
    stored = HASH_FILE.read_text(encoding="utf-8").strip()
    actual = digest(index)
    if stored != actual:
        raise SystemExit(f"V430_SHA256.txt mismatch: {stored} != {actual}")


def main() -> None:
    index = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")

    if RELEASE_META in index:
        validate_applied(index, sw)
        print("V430-P8 stable release identity already applied")
        print("stable sha256:", digest(index))
        return

    actual = digest(index)
    if actual != BASE_SHA256:
        raise SystemExit(f"Refusing unexpected P7 baseline: sha256={actual}, expected={BASE_SHA256}")

    inherited = (
        'id="v430-p1-simplified-navigation"',
        'id="v430-p2-compact-density"',
        'id="v430-p3-focus-mode"',
        'id="v430-p3-runtime"',
        'id="v430-p4-command-palette"',
        'id="v430-p4-runtime"',
        'id="v430-p5-mobile-first"',
        'id="v430-p5-runtime"',
        'id="v430-p6-accessibility"',
        'id="v430-p6-runtime"',
        'id="v430-p7-responsive-hardening"',
        'id="v430-p7-runtime"',
    )
    for marker in inherited:
        if index.count(marker) != 1:
            raise SystemExit(f"Certified P1-P7 marker missing or duplicated: {marker}")

    if index.count(TOAST_AA_OLD) != 1 or TOAST_AA_NEW in index:
        raise SystemExit("P7 toast contrast anchor missing, duplicated, or already ambiguous")
    index = index.replace(TOAST_AA_OLD, TOAST_AA_NEW, 1)

    replacements = (
        (f'<title>{OLD_NAME}</title>', f'<title>{NEW_NAME}</title>'),
        (f'content="{OLD_NAME} — local-first Markdown publishing studio', f'content="{NEW_NAME} — local-first Markdown publishing studio'),
        ("exports.APP_VERSION = '4.2.3';", "exports.APP_VERSION = '4.3.0';"),
        (f"exports.RELEASE_NAME = '{OLD_NAME}';", f"exports.RELEASE_NAME = '{NEW_NAME}';"),
    )
    for old, new in replacements:
        if index.count(old) != 1:
            raise SystemExit(f"Release identity anchor missing or duplicated: {old}")
        index = index.replace(old, new, 1)

    phase_pattern = r"exports\.RELEASE_PHASE = '[^']+';"
    matches = list(re.finditer(phase_pattern, index))
    if len(matches) != 1:
        raise SystemExit(f"RELEASE_PHASE anchor count={len(matches)}")
    index = re.sub(phase_pattern, "exports.RELEASE_PHASE = 'V430-P8 — RC Certification & Stable Release';", index, count=1)

    title = '<title>Manuscript v4.3.0 Stable</title>'
    if index.count(title) != 1:
        raise SystemExit("Updated stable title missing or duplicated before release meta injection")
    index = index.replace(title, title + "\n" + RELEASE_META, 1)

    old_cache = "const CACHE_NAME = `${CACHE_PREFIX}v4.2.3`;"
    new_cache = "const CACHE_NAME = `${CACHE_PREFIX}v4.3.0`;"
    if sw.count(old_cache) != 1 or new_cache in sw:
        raise SystemExit("Service-worker cache anchor missing, duplicated, or already ambiguous")
    sw = sw.replace(old_cache, new_cache, 1)

    INDEX.write_text(index, encoding="utf-8")
    SW.write_text(sw, encoding="utf-8")
    stable_sha = digest(index)
    HASH_FILE.write_text(stable_sha + "\n", encoding="utf-8")

    validate_applied(index, sw)
    print("Applied V430-P8 stable release identity")
    print("stable sha256:", stable_sha)


if __name__ == "__main__":
    main()
