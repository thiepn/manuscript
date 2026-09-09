from pathlib import Path
import hashlib
import json

INDEX = Path('index.html')
SW = Path('sw.js')

EXAMPLES = [
    {
        'id': 'markdown-basics',
        'name': 'Markdown Basics',
        'category': 'Learn Markdown',
        'desc': 'A beginner-friendly tour of headings, emphasis, links, quotes, code, rules, and line breaks.',
        'markdown': '''# Markdown Basics

> **How to use this example:** keep Manuscript in **Split** view. Edit the Markdown on the left and watch the rendered document change on the right.

## 1. Headings

Headings create the structure of a document. Add more `#` characters for smaller heading levels.

# Heading level 1
## Heading level 2
### Heading level 3
#### Heading level 4

Most documents use one main `#` heading, then organize sections with `##` and `###`.

## 2. Paragraphs and line breaks

A blank line starts a new paragraph. This is one paragraph.

This is a second paragraph.

Two spaces at the end of a line create a manual line break.  
This line starts directly below it.

## 3. Emphasis

- `**bold**` becomes **bold**
- `*italic*` becomes *italic*
- `***bold italic***` becomes ***bold italic***
- `~~strikethrough~~` becomes ~~strikethrough~~

Use emphasis sparingly so important text remains meaningful.

## 4. Links and inline code

A link looks like `[visible text](https://example.com)`.

Visit the [Markdown Guide](https://www.markdownguide.org/) for another reference.

Wrap short technical terms in backticks: `npm install`, `Ctrl+K`, or `example.txt`.

## 5. Blockquotes

> A blockquote starts with `>`.
>
> It is useful for quotations, notes from a source, or text you want to visually separate.

## 6. Horizontal rules

Three hyphens create a thematic break:

---

The rule above separates two parts of a document.

## Try it yourself

Change a heading, make this **bold text** italic instead, replace the link, and add your own blockquote.
'''
    },
    {
        'id': 'markdown-lists-tables',
        'name': 'Lists, Tasks & Tables',
        'category': 'Learn Markdown',
        'desc': 'Learn bullet lists, numbered steps, nested items, task checkboxes, and Markdown tables.',
        'markdown': '''# Lists, Tasks & Tables

> Edit the source and preview side by side. Lists and tables are easiest to understand by changing them yourself.

## 1. Bullet lists

Use `-`, `*`, or `+` followed by a space. Using one marker consistently is easier to read.

- First item
- Second item
- Third item

### Nested lists

Indent child items beneath their parent:

- Plan the project
  - Define the goal
  - Gather the material
- Write the draft
  - Create an outline
  - Fill each section
- Review the result

## 2. Numbered lists

Use a number followed by a period:

1. Write the Markdown.
2. Check the preview.
3. Revise the content.
4. Export the finished document.

Markdown can keep numbering sensible even while you edit. Many writers simply use `1.` for every source line, but explicit numbers are often easier for beginners to inspect.

## 3. Task lists

Task lists add checkboxes:

- [x] Learn headings
- [x] Learn emphasis
- [ ] Practice tables
- [ ] Write a document from scratch

Change `[ ]` to `[x]` to mark a task complete.

## 4. Tables

A Markdown table uses pipes (`|`) for columns and a separator row below the header.

| Feature | Markdown | Purpose |
|---|---|---|
| Bold | `**text**` | Strong emphasis |
| Link | `[text](url)` | Connect to another resource |
| Code | `` `code` `` | Show literal commands or names |
| Task | `- [ ] item` | Track work |

### A practical table

| Day | Focus | Done? |
|---|---|---|
| Monday | Outline | Yes |
| Tuesday | Draft | Yes |
| Wednesday | Review | No |

## 5. Combining structures

1. Prepare the document.
   - Add a clear title.
   - Create section headings.
2. Add the content.
   - Use lists for grouped ideas.
   - Use tables for comparisons.
3. Review the result.
   - [ ] Check spelling
   - [ ] Check links
   - [ ] Preview every page

## Try it yourself

Add another row to the table, nest one more bullet level, and check the remaining tasks.
'''
    },
    {
        'id': 'markdown-code-math-footnotes',
        'name': 'Code, Math & Footnotes',
        'category': 'Learn Markdown',
        'desc': 'Practice inline code, fenced code blocks, equations, and footnotes in one technical example.',
        'markdown': '''# Code, Math & Footnotes

This example covers Markdown features that are especially useful for technical, academic, and study notes.

## 1. Inline code

Use single backticks for short code or literal text: `print()`, `git status`, `index.html`, or `x = 4`.

Inline code tells the reader, “interpret this literally rather than as normal prose.”

## 2. Fenced code blocks

Use three backticks before and after a larger code sample. Add a language name after the opening fence for syntax highlighting.

```python
def average(values):
    return sum(values) / len(values)

scores = [8, 9, 10]
print(average(scores))
```

Another example:

```bash
git status
git add .
git commit -m "Update notes"
```

Inside a fenced block, characters such as `#`, `*`, and `_` are shown as code instead of being treated as Markdown formatting.

## 3. Inline mathematics

Put a short expression between dollar signs: $a^2 + b^2 = c^2$.

For example, the arithmetic mean of values $x_1, \\ldots, x_n$ is written as $\\bar{x}$.

## 4. Display mathematics

Use double dollar signs for an equation on its own line:

$$
\\bar{x} = \\frac{1}{n}\\sum_{i=1}^{n} x_i
$$

A second example:

$$
P(A \\mid B) = \\frac{P(B \\mid A)P(A)}{P(B)}
$$

## 5. Footnotes

A footnote reference looks like this.[^first]

You can continue writing normally after the reference. The footnote definition can appear later in the Markdown source.[^source]

[^first]: This is the text of the first footnote.
[^source]: Footnotes are useful for citations, side comments, definitions, or details that would interrupt the main paragraph.

## 6. Combine the features

Suppose a script computes an estimate $\\hat{\\theta}$ from a sample:

```python
estimate = sum(sample) / len(sample)
```

The code is short, the equation explains the notation, and a footnote can hold an implementation detail.[^detail]

[^detail]: In a real project, you would also decide how missing values should be handled.

## Try it yourself

Change the Python example, add another footnote, and replace one equation with a formula from something you are currently studying.
'''
    },
    {
        'id': 'manuscript-publishing-extras',
        'name': 'Manuscript Publishing Extras',
        'category': 'Learn Markdown',
        'desc': 'Learn which publishing syntax is Manuscript-specific: front matter, title pages, TOC, callouts, anchors, and page breaks.',
        'markdown': '''---
title: My First Published Document
subtitle: Manuscript-specific publishing syntax
author: Your Name
date: YYYY-MM-DD
keywords: markdown, manuscript, example
---

[[titlepage]]

<!-- manuscript:mainmatter -->

# Manuscript Publishing Extras

> **Important:** the earlier learning examples focus on standard Markdown or common Markdown extensions. The features in this document are **Manuscript-specific publishing tools** layered on top of Markdown.

[[toc]]

## 1. Front matter {#sec-frontmatter}

The block at the very top between `---` lines stores document metadata such as title, author, date, and keywords. Manuscript can use this information when generating publication elements.

## 2. Generated elements {#sec-generated}

`[[titlepage]]` creates a title page from your metadata.

`[[toc]]` creates a table of contents from the headings in the document.

These are Manuscript directives, not ordinary Markdown syntax.

## 3. Callouts {#sec-callouts}

Callouts make important information stand out:

::: note {title="A useful note"}
This is a Manuscript callout. Change `note` to another supported callout type or edit the title.
:::

::: warning {title="Keep the distinction clear"}
If you copy this source into a basic Markdown viewer, Manuscript-specific directives may appear as plain text instead of rendered publishing elements.
:::

## 4. Heading anchors {#sec-anchors}

The `{#sec-anchors}` text attached to this heading gives it a stable identifier. Stable IDs are useful when a document needs cross-references or predictable internal targets.

## 5. Manual page breaks

The comment below forces the next content onto a new page in paginated output.

<!-- manuscript:pagebreak -->

## 6. New page

This section begins after a Manuscript page-break directive.

### What to remember

- **Markdown** describes the document content and structure.
- **Manuscript settings** control typography, page geometry, headers, and publishing behavior.
- **Manuscript directives** add publication-specific elements that normal Markdown does not define.

## Try it yourself

Change the metadata at the top, rename a heading, edit the callout, and remove the page-break comment to see how the document changes.
'''
    },
]


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def learning_block() -> str:
    lines = []
    for item in EXAMPLES:
        lines.append(
            "        { id: %s, name: %s, category: %s, desc: %s, markdown: %s },\n" % tuple(
                js_string(item[key]) for key in ('id', 'name', 'category', 'desc', 'markdown')
            )
        )
    return ''.join(lines)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 1:
        return text.replace(old, new, 1)
    if count == 0 and new in text:
        return text
    raise SystemExit(f'{label}: expected one old anchor, found {count}')


def main():
    text = INDEX.read_text(encoding='utf-8')

    blank = "        { id: 'blank', name: 'Blank Document', category: 'General', desc: 'A clean document with no starter sections.', markdown: '# Untitled Document\\n\\nStart writing here…\\n' },\n"
    if "id: \"markdown-basics\"" not in text:
        if text.count(blank) != 1:
            raise SystemExit(f'template insertion anchor count={text.count(blank)}')
        text = text.replace(blank, blank + learning_block(), 1)

    text = replace_once(
        text,
        "<meta name=\"description\" content=\"Manuscript v4.3.0 Stable — local-first Markdown publishing studio with screen-scoped scrolling, six curated interface themes, consolidated editorial visual architecture, deterministic pagination, and publication-ready export.\">",
        "<meta name=\"description\" content=\"Manuscript v4.3.1 Stable — local-first Markdown publishing studio with editable Markdown learning examples, screen-scoped scrolling, six curated interface themes, deterministic pagination, and publication-ready export.\">",
        'description version',
    )
    text = replace_once(text, '<title>Manuscript v4.3.0 Stable</title>', '<title>Manuscript v4.3.1 Stable</title>', 'title version')
    text = replace_once(
        text,
        '<meta name="manuscript-release-contract" content="v4.3.0-stable-certified-v1">',
        '<meta name="manuscript-release-contract" content="v4.3.1-stable-markdown-learning-v1">\n<meta name="manuscript-learning-contract" content="markdown-examples-v1">',
        'release contract',
    )
    text = replace_once(text, "exports.APP_VERSION = '4.3.0';", "exports.APP_VERSION = '4.3.1';", 'APP_VERSION')
    text = replace_once(text, "exports.RELEASE_NAME = 'Manuscript v4.3.0 Stable';", "exports.RELEASE_NAME = 'Manuscript v4.3.1 Stable';", 'RELEASE_NAME')
    text = replace_once(text, "exports.RELEASE_PHASE = 'V430-P8 — RC Certification & Stable Release';", "exports.RELEASE_PHASE = 'V431 — Markdown Learning Examples';", 'RELEASE_PHASE')

    old_gallery = "return modalFrame('Template Gallery', `<div class=\"template-grid\">${allTemplates().map(t => templateCard(t)).join('')}</div>`, `<button class=\"btn\" data-action=\"save-current-template\" ${state.project ? '' : 'disabled'}>Save current as template</button><button class=\"btn\" data-action=\"modal-close\">Close</button>`, 'wide');"
    new_gallery = "return modalFrame('Template Gallery', `<div class=\"phase6-help-card\"><strong>New to Markdown?</strong><p>Start with the <strong>Learn Markdown</strong> examples below. Open one in Split view, edit the source, and watch the preview change. The final learning example clearly separates standard Markdown from Manuscript-specific publishing syntax.</p></div><div class=\"template-grid\">${allTemplates().map(t => templateCard(t)).join('')}</div>`, `<button class=\"btn\" data-action=\"save-current-template\" ${state.project ? '' : 'disabled'}>Save current as template</button><button class=\"btn\" data-action=\"modal-close\">Close</button>`, 'wide');"
    text = replace_once(text, old_gallery, new_gallery, 'template gallery hint')

    text = replace_once(
        text,
        'Manuscript ${APP_VERSION} · RC6 scroll ownership repair · Phase 9 release candidate · Local documents and books · Browser Save as PDF',
        'Manuscript ${APP_VERSION} · Markdown learning examples · Local documents and books · Browser Save as PDF',
        'landing footer',
    )

    for template_id in [x['id'] for x in EXAMPLES]:
        token = f'id: {js_string(template_id)}'
        if text.count(token) != 1:
            raise SystemExit(f'{template_id}: duplicate/missing template')

    for token in ('# Markdown Basics', '# Lists, Tasks & Tables', '# Code, Math & Footnotes', '# Manuscript Publishing Extras', 'New to Markdown?', 'markdown-examples-v1'):
        if token not in text:
            raise SystemExit(f'missing expected token: {token}')

    INDEX.write_text(text, encoding='utf-8')

    sw = SW.read_text(encoding='utf-8')
    sw = replace_once(sw, "const CACHE_NAME = `${CACHE_PREFIX}v4.3.0`;", "const CACHE_NAME = `${CACHE_PREFIX}v4.3.1`;", 'service-worker cache')
    SW.write_text(sw, encoding='utf-8')

    digest = hashlib.sha256(INDEX.read_bytes()).hexdigest()
    Path('V431_SHA256.txt').write_text(digest + '\n', encoding='utf-8')
    Path('RELEASE_NOTES_v4.3.1.md').write_text('''# Manuscript v4.3.1 Stable\n\nReleased: 2026-09-09\n\n## Markdown learning examples\n\nThis patch adds four editable learning documents to the built-in Template Gallery so new users can understand Markdown by editing source and watching the preview change.\n\n- **Markdown Basics** — headings, paragraphs, line breaks, emphasis, links, inline code, blockquotes, and horizontal rules.\n- **Lists, Tasks & Tables** — bullet and numbered lists, nesting, task checkboxes, tables, and combined structures.\n- **Code, Math & Footnotes** — inline/fenced code, syntax-highlighted examples, inline/display mathematics, and footnotes.\n- **Manuscript Publishing Extras** — clearly distinguishes standard Markdown from Manuscript-specific front matter, generated title pages/TOC, callouts, anchors, and page breaks.\n\nThe Template Gallery now points beginners toward the **Learn Markdown** examples and recommends using Split view while experimenting.\n\n## Release integrity\n\nCanonical standalone HTML SHA-256:\n\n`''' + digest + '''`\n''', encoding='utf-8')
    print(f'Patched Manuscript v4.3.1 Markdown examples; index sha256={digest}')


if __name__ == '__main__':
    main()
