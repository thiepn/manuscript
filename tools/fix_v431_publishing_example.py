from pathlib import Path
import hashlib
import json

INDEX = Path('index.html')


def encoded_fragment(value: str) -> str:
    """Encode a plain Markdown fragment exactly as it appears inside the JS JSON string."""
    return json.dumps(value, ensure_ascii=False)[1:-1]


def replace_encoded(text: str, old: str, new: str, label: str) -> str:
    old_encoded = encoded_fragment(old)
    new_encoded = encoded_fragment(new)
    count = text.count(old_encoded)
    if count == 1:
        return text.replace(old_encoded, new_encoded, 1)
    if count == 0 and new_encoded in text:
        return text
    raise SystemExit(f'{label}: expected one old fragment, found {count}')


def main():
    text = INDEX.read_text(encoding='utf-8')

    old_desc = 'Learn which publishing syntax is Manuscript-specific: front matter, title pages, TOC, callouts, anchors, and page breaks.'
    new_desc = 'Learn which publishing syntax is Manuscript-specific: front matter, title pages, TOC, callouts, and page breaks.'
    if old_desc in text:
        text = text.replace(old_desc, new_desc, 1)
    elif new_desc not in text:
        raise SystemExit('publishing-example description anchor missing')

    text = replace_encoded(
        text,
        '## 1. Front matter {#sec-frontmatter}',
        '## 1. Front matter',
        'front-matter heading',
    )
    text = replace_encoded(
        text,
        '## 2. Generated elements {#sec-generated}',
        '## 2. Generated elements',
        'generated-elements heading',
    )
    text = replace_encoded(
        text,
        '## 3. Callouts {#sec-callouts}',
        '## 3. Callouts',
        'callouts heading',
    )
    text = replace_encoded(
        text,
        '''## 4. Heading anchors {#sec-anchors}

The `{#sec-anchors}` text attached to this heading gives it a stable identifier. Stable IDs are useful when a document needs cross-references or predictable internal targets.

''',
        '',
        'unsupported heading-anchor lesson',
    )
    text = replace_encoded(
        text,
        '## 5. Manual page breaks',
        '## 4. Manual page breaks',
        'manual-page-break numbering',
    )
    text = replace_encoded(
        text,
        '## 6. New page',
        '## 5. New page',
        'new-page numbering',
    )

    if '{#sec-' in text:
        raise SystemExit('unsupported custom heading attribute remains in v4.3.1 example')
    if 'Heading anchors' in text:
        raise SystemExit('unsupported heading-anchor lesson remains in v4.3.1 example')

    INDEX.write_text(text, encoding='utf-8')

    digest = hashlib.sha256(INDEX.read_bytes()).hexdigest()
    Path('V431_SHA256.txt').write_text(digest + '\n', encoding='utf-8')

    notes = Path('RELEASE_NOTES_v4.3.1.md')
    note_text = notes.read_text(encoding='utf-8')
    note_text = note_text.replace(
        'front matter, generated title pages/TOC, callouts, anchors, and page breaks.',
        'front matter, generated title pages/TOC, callouts, and page breaks.',
    )
    import re
    note_text = re.sub(r'Canonical standalone HTML SHA-256:\n\n`[a-f0-9]{64}`', f'Canonical standalone HTML SHA-256:\n\n`{digest}`', note_text)
    notes.write_text(note_text, encoding='utf-8')

    print(f'Corrected v4.3.1 publishing example; index sha256={digest}')


if __name__ == '__main__':
    main()
