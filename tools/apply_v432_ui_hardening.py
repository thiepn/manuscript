from pathlib import Path
import hashlib

INDEX = Path('index.html')
SW = Path('sw.js')

V432_STYLE = '''
<meta name="manuscript-ui-regression-contract" content="v432-valid-head+mobile-nav-clearance+coarse-targets-v1">
<style id="v432-ui-regression-hardening">
/* Manuscript v4.3.2 — UI regression hardening. */
@media(max-width:767px){
  .workspace{
    flex:0 0 calc(100dvh - var(--appbar-h) - var(--toolbar-h) - var(--mobile-nav-h))!important;
    height:calc(100dvh - var(--appbar-h) - var(--toolbar-h) - var(--mobile-nav-h))!important;
    max-height:calc(100dvh - var(--appbar-h) - var(--toolbar-h) - var(--mobile-nav-h))!important;
  }
}
@media(pointer:coarse){
  .btn.small{height:auto;min-height:40px}
}
@media(max-width:767px) and (pointer:coarse){
  .toolbar .icon-btn{width:42px;min-width:42px;min-height:42px}
}
@media(max-width:380px){
  .modal,.modal.wide{max-height:calc(100dvh - 8px - env(safe-area-inset-top,0px))!important}
}
</style>
'''


def replace_version(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one old value, found {count}')
    return text.replace(old, new, 1)


def remove_head_escape(text: str, style_id: str) -> str:
    marker = f'<style id="{style_id}">'
    bad = '\\n' + marker
    if bad in text:
        if text.count(bad) != 1:
            raise SystemExit(f'{style_id}: expected one literal newline token')
        return text.replace(bad, marker, 1)
    if marker in text:
        return text
    raise SystemExit(f'{style_id}: structural anchor missing')


def main():
    text = INDEX.read_text(encoding='utf-8')

    text = remove_head_escape(text, 'v422-editor-layout-hotfix')
    text = remove_head_escape(text, 'v423-ui-hardening')

    text = replace_version(
        text,
        '<meta name="description" content="Manuscript v4.3.1 Stable — local-first Markdown publishing studio with editable Markdown learning examples, screen-scoped scrolling, six curated interface themes, deterministic pagination, and publication-ready export.">',
        '<meta name="description" content="Manuscript v4.3.2 Stable — local-first Markdown publishing studio with hardened responsive UI, editable Markdown learning examples, deterministic pagination, and publication-ready export.">',
        'description',
    )
    text = replace_version(text, '<title>Manuscript v4.3.1 Stable</title>', '<title>Manuscript v4.3.2 Stable</title>', 'title')
    text = replace_version(
        text,
        '<meta name="manuscript-release-contract" content="v4.3.1-stable-markdown-learning-v1">',
        '<meta name="manuscript-release-contract" content="v4.3.2-stable-ui-regression-hardening-v1">',
        'release contract',
    )
    text = replace_version(text, "exports.APP_VERSION = '4.3.1';", "exports.APP_VERSION = '4.3.2';", 'APP_VERSION')
    text = replace_version(text, "exports.RELEASE_NAME = 'Manuscript v4.3.1 Stable';", "exports.RELEASE_NAME = 'Manuscript v4.3.2 Stable';", 'RELEASE_NAME')
    text = replace_version(text, "exports.RELEASE_PHASE = 'V431 — Markdown Learning Examples';", "exports.RELEASE_PHASE = 'V432 — UI Regression Hardening';", 'RELEASE_PHASE')

    if 'id="v432-ui-regression-hardening"' not in text:
        anchor = '</head>\n<body>'
        if text.count(anchor) != 1:
            raise SystemExit(f'head/body insertion anchor count={text.count(anchor)}')
        text = text.replace(anchor, V432_STYLE + '</head>\n<body>', 1)

    head_close = text.find('</head>')
    body_start = text.find('<body>')
    if head_close < 0 or body_start < 0 or head_close > body_start:
        raise SystemExit('invalid structural head/body ordering')
    for style_id in (
        'v422-editor-layout-hotfix', 'v423-ui-hardening',
        'v430-p1-simplified-navigation', 'v430-p5-mobile-first',
        'v430-p7-responsive-hardening', 'v432-ui-regression-hardening',
    ):
        position = text.find(f'id="{style_id}"')
        if position < 0 or position > head_close:
            raise SystemExit(f'{style_id}: not contained by structural head')
    for style_id in ('v422-editor-layout-hotfix', 'v423-ui-hardening'):
        if '\\n' + f'<style id="{style_id}">' in text:
            raise SystemExit(f'{style_id}: literal newline token remains')

    INDEX.write_text(text, encoding='utf-8')

    sw = SW.read_text(encoding='utf-8')
    old_cache = "const CACHE_NAME = `${CACHE_PREFIX}v4.3.1`;"
    new_cache = "const CACHE_NAME = `${CACHE_PREFIX}v4.3.2`;"
    if new_cache not in sw:
        if sw.count(old_cache) != 1:
            raise SystemExit(f'service-worker cache anchor count={sw.count(old_cache)}')
        sw = sw.replace(old_cache, new_cache, 1)
    SW.write_text(sw, encoding='utf-8')

    digest = hashlib.sha256(INDEX.read_bytes()).hexdigest()
    Path('V432_SHA256.txt').write_text(digest + '\n', encoding='utf-8')
    Path('RELEASE_NOTES_v4.3.2.md').write_text(f'''# Manuscript v4.3.2 Stable

Released: 2026-09-09

## UI regression hardening

- Removes two literal `\\n` tokens that caused Chromium to terminate `<head>` early, reparent later style/meta nodes into `<body>`, and render a visible strip above the app.
- Reserves fixed mobile bottom-navigation height so editor and preview content never extend under navigation.
- Enlarges compact coarse-pointer actions and restores mobile toolbar target width while retaining desktop density.
- Keeps bottom-sheet modals within very small phone viewports, including while their entrance transition is settling.
- Retains the v4.3.1 Markdown learning examples and publishing behavior.

## Verification

Certified with the legacy multi-viewport sweep and a deeper Chromium audit covering 320, 360, 390, 480, 767, 768, 900, 901, 1024, and 1440px widths; Template Gallery geometry; editor/preview modes; mobile navigation clearance; touch targets; root DOM structure; overflow; and runtime errors.

Canonical standalone HTML SHA-256:

`{digest}`
''', encoding='utf-8')
    print(f'Patched Manuscript v4.3.2 UI hardening; index sha256={digest}')


if __name__ == '__main__':
    main()
