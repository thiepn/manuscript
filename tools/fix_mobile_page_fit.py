from pathlib import Path
import hashlib

INDEX = Path('index.html')
HASH = Path('V432_SHA256.txt')
NOTES = Path('RELEASE_NOTES_v4.3.2.md')

OLD = """        if ('zoom' in wrap.style) {
            wrap.style.transform = 'none';
            wrap.style.marginBottom = '0px';
            wrap.style.zoom = String(scale);
            wrap.style.width = `${100 / scale}%`;
        } else {
"""

NEW = """        if ('zoom' in wrap.style) {
            wrap.style.transform = 'none';
            wrap.style.marginBottom = '0px';
            wrap.style.zoom = String(scale);
            // CSS zoom already participates in layout and changes the effective
            // containing block. Expanding to 100/scale here double-compensates
            // the width and pushes centered pages to the right, most visibly on
            // phones. Keep the zoomed wrapper at the viewport/layout width.
            wrap.style.width = '100%';
        } else {
"""

NOTE_BULLET = '- Corrects Pages preview fit/zoom alignment so scaled pages remain centered and fully visible instead of being displaced to the right, especially on phones.\n'


def main():
    text = INDEX.read_text(encoding='utf-8')
    old_count = text.count(OLD)
    new_count = text.count(NEW)

    if old_count == 1 and new_count == 0:
        text = text.replace(OLD, NEW, 1)
        INDEX.write_text(text, encoding='utf-8')
        print('Applied page-preview zoom width fix')
    elif old_count == 0 and new_count == 1:
        print('Page-preview zoom width fix already applied')
    else:
        raise SystemExit(f'Unexpected page-preview scale anchors: old={old_count} new={new_count}')

    # Fail closed if the transform fallback loses its required width compensation.
    current = INDEX.read_text(encoding='utf-8')
    fallback = """        } else {
            wrap.style.zoom = '';
            wrap.style.width = `${100 / scale}%`;
"""
    if current.count(fallback) != 1:
        raise SystemExit('Transform fallback width compensation is missing or duplicated')

    digest = hashlib.sha256(INDEX.read_bytes()).hexdigest()
    HASH.write_text(digest + '\n', encoding='utf-8')

    notes = NOTES.read_text(encoding='utf-8')
    if NOTE_BULLET not in notes:
        anchor = '- Retains the v4.3.1 Markdown learning examples and publishing behavior.\n'
        if notes.count(anchor) != 1:
            raise SystemExit('Release-note insertion anchor missing or duplicated')
        notes = notes.replace(anchor, NOTE_BULLET + anchor, 1)
    marker = 'Canonical standalone HTML SHA-256:\n\n`'
    start = notes.find(marker)
    if start < 0:
        raise SystemExit('Release-note digest marker missing')
    value_start = start + len(marker)
    value_end = notes.find('`', value_start)
    if value_end < 0:
        raise SystemExit('Release-note digest terminator missing')
    notes = notes[:value_start] + digest + notes[value_end:]
    NOTES.write_text(notes, encoding='utf-8')

    print(f'index sha256={digest}')


if __name__ == '__main__':
    main()
