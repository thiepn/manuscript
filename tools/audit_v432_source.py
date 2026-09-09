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
    lines = source.splitlines()
    lo = max(0, line - 3)
    hi = min(len(lines), line + 2)
    print('\n'.join(f'{i+1}: {lines[i]}' for i in range(lo, hi)))
    print('---')

if parser.findings:
    raise SystemExit(1)
