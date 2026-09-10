from html.parser import HTMLParser
from pathlib import Path
import re

source = Path('index.html').read_text(encoding='utf-8')
failures = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


class StructuralTags(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.starts = []
        self.ends = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {'html', 'head', 'body'}:
            self.starts.append((tag.lower(), self.getpos()))

    def handle_endtag(self, tag):
        if tag.lower() in {'html', 'head', 'body'}:
            self.ends.append((tag.lower(), self.getpos()))


parser = StructuralTags()
parser.feed(source)

for tag in ('html', 'head', 'body'):
    starts = [pos for current, pos in parser.starts if current == tag]
    ends = [pos for current, pos in parser.ends if current == tag]
    check(len(starts) == 1, f'expected exactly one structural <{tag}>, found {len(starts)}')
    check(len(ends) == 1, f'expected exactly one structural </{tag}>, found {len(ends)}')

head_close = source.find('</head>')
body_match = re.search(r'<body\b[^>]*>', source, flags=re.I)
body_start = body_match.start() if body_match else -1
check(head_close >= 0 and body_start > head_close, 'body must start after the structural head closes')

for style_id in (
    'v422-editor-layout-hotfix',
    'v423-ui-hardening',
    'v430-p1-simplified-navigation',
    'v430-p5-mobile-first',
    'v430-p6-accessibility',
    'v430-p7-responsive-hardening',
    'v432-ui-regression-hardening',
):
    marker = f'id="{style_id}"'
    position = source.find(marker)
    check(position >= 0, f'{style_id}: missing')
    check(position < head_close, f'{style_id}: must remain inside <head>')

for style_id in ('v422-editor-layout-hotfix', 'v423-ui-hardening'):
    marker = f'<style id="{style_id}">'
    check('\\n' + marker not in source, f'{style_id}: literal \\n token must not precede style')

# Regression guard for the browser-visible "\\n" strip: escaped newline tokens
# must never become structural text before a head child or immediately after body.
head_source = source[:head_close] if head_close >= 0 else ''
check(
    re.search(r'\\[nr][ \t]*<(?:style|script|meta|link|title)\b', head_source, flags=re.I) is None,
    'literal escaped newline must not appear as structural text inside <head>',
)
if body_match:
    first_child = source.find('<', body_match.end())
    body_prefix = source[body_match.end():first_child] if first_child >= 0 else source[body_match.end():]
    check('\\n' not in body_prefix and '\\r' not in body_prefix,
          'literal escaped newline must not appear immediately after <body>')
check('literal-newline-artifact-guard' not in source,
      'temporary literal-newline runtime guard must not ship')

check('manuscript-ui-regression-contract' in source, 'v4.3.2 UI regression contract missing')
check('<title>Manuscript v4.3.2 Stable</title>' in source, 'v4.3.2 title missing')
check("exports.APP_VERSION = '4.3.2';" in source, 'APP_VERSION is not v4.3.2')

if failures:
    print(f'V432 structure audit failed ({len(failures)}):')
    for failure in failures:
        print(f'- {failure}')
    raise SystemExit(1)

print('V432 document structure audit: PASS')
