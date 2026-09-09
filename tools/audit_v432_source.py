from html.parser import HTMLParser
from pathlib import Path

source = Path('index.html').read_text(encoding='utf-8')

class RootTextAudit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.in_body = False
        self.depth = 0
        self.findings = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'body':
            self.in_body = True
            self.depth = 0
            return
        if self.in_body:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag.lower() == 'body':
            self.in_body = False
            return
        if self.in_body:
            self.depth = max(0, self.depth - 1)

    def handle_data(self, data):
        if self.in_body and self.depth == 0 and data.strip():
            self.findings.append((self.getpos(), data))

parser = RootTextAudit()
parser.feed(source)
print(f'body root text nodes: {len(parser.findings)}')
for (line_col, data) in parser.findings:
    line, col = line_col
    print(f'line={line} col={col} repr={data!r}')

print('--- escaped-newline source scan ---')
for needle in (r'\n \n', r'\n\n', r'\n  \n', r'\n \n '):
    offsets = []
    pos = 0
    while True:
        pos = source.find(needle, pos)
        if pos < 0:
            break
        offsets.append(pos)
        pos += max(1, len(needle))
    print(f'{needle!r}: {len(offsets)} occurrences')
    for offset in offsets[:20]:
        line = source.count('\n', 0, offset) + 1
        col = offset - source.rfind('\n', 0, offset) - 1
        context = source[max(0, offset-140):min(len(source), offset+len(needle)+180)]
        print(f'  line={line} col={col} offset={offset} context={context!r}')

if parser.findings:
    raise SystemExit(1)
