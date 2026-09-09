from html.parser import HTMLParser
from pathlib import Path

source = Path('index.html').read_text(encoding='utf-8')

class StructureAudit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.in_body = False
        self.depth = 0
        self.findings = []
        self.events = []
        self.between_head_body = []
        self.head_closed = False
        self.body_started = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = dict(attrs)
        if tag in ('html', 'head', 'body', 'style', 'meta'):
            self.events.append((self.getpos(), 'start', tag, attrs_dict.get('id', ''), attrs_dict.get('name', '')))
        if self.head_closed and not self.body_started and tag in ('style', 'meta'):
            self.between_head_body.append((self.getpos(), tag, attrs_dict.get('id', ''), attrs_dict.get('name', '')))
        if tag == 'body':
            self.body_started = True
            self.in_body = True
            self.depth = 0
            return
        if self.in_body:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = dict(attrs)
        if tag == 'meta':
            self.events.append((self.getpos(), 'startend', tag, attrs_dict.get('id', ''), attrs_dict.get('name', '')))
            if self.head_closed and not self.body_started:
                self.between_head_body.append((self.getpos(), tag, attrs_dict.get('id', ''), attrs_dict.get('name', '')))

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ('html', 'head', 'body'):
            self.events.append((self.getpos(), 'end', tag, '', ''))
        if tag == 'head':
            self.head_closed = True
        if tag == 'body':
            self.in_body = False
            return
        if self.in_body:
            self.depth = max(0, self.depth - 1)

    def handle_data(self, data):
        if self.head_closed and not self.body_started and data.strip():
            self.between_head_body.append((self.getpos(), '#text', repr(data[:120]), ''))
        if self.in_body and self.depth == 0 and data.strip():
            self.findings.append((self.getpos(), data))

parser = StructureAudit()
parser.feed(source)

print('--- exact legacy style prefixes ---')
for style_id in ('v422-editor-layout-hotfix', 'v423-ui-hardening'):
    marker = f'<style id="{style_id}">'
    offset = source.find(marker)
    print(style_id, 'offset=', offset)
    if offset >= 0:
        print('prefix repr=', repr(source[max(0, offset - 80):offset + len(marker) + 20]))
        print('prefix codepoints=', [ord(ch) for ch in source[max(0, offset - 20):offset]])

print('--- structural events ---')
for event in parser.events:
    pos, kind, tag, ident, name = event
    if tag in ('html', 'head', 'body') or ident.startswith('v42') or ident.startswith('v43') or name.startswith('manuscript-'):
        print(pos, kind, tag, f'id={ident!r}', f'name={name!r}')

print('--- head-close -> body-start content ---')
print(f'count: {len(parser.between_head_body)}')
for item in parser.between_head_body[:100]:
    print(item)

print(f'body root text nodes in raw parser: {len(parser.findings)}')
for (line_col, data) in parser.findings:
    print(f'line={line_col[0]} col={line_col[1]} repr={data!r}')

print('--- escaped-newline source scan ---')
for needle in (r'\n', r'\n \n', r'\n\n', r'\n  \n', r'\n \n '):
    offsets = []
    pos = 0
    while True:
        pos = source.find(needle, pos)
        if pos < 0:
            break
        offsets.append(pos)
        pos += max(1, len(needle))
    print(f'{needle!r}: {len(offsets)} occurrences')
    for offset in offsets[:8]:
        line = source.count('\n', 0, offset) + 1
        col = offset - source.rfind('\n', 0, offset) - 1
        context = source[max(0, offset-120):min(len(source), offset+len(needle)+160)]
        print(f'  line={line} col={col} offset={offset} context={context!r}')

if parser.between_head_body or parser.findings:
    raise SystemExit(1)
