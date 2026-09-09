from pathlib import Path

source = Path('index.html').read_text(encoding='utf-8')
failures = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


check(source.count('<head>') == 1, 'expected exactly one <head>')
check(source.count('</head>') == 1, 'expected exactly one </head>')
check(source.count('<body>') == 1, 'expected exactly one <body>')
check(source.count('</body>') == 1, 'expected exactly one </body>')

head_close = source.find('</head>')
body_start = source.find('<body>')
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

check('manuscript-ui-regression-contract' in source, 'v4.3.2 UI regression contract missing')
check('<title>Manuscript v4.3.2 Stable</title>' in source, 'v4.3.2 title missing')
check("exports.APP_VERSION = '4.3.2';" in source, 'APP_VERSION is not v4.3.2')

if failures:
    print(f'V432 structure audit failed ({len(failures)}):')
    for failure in failures:
        print(f'- {failure}')
    raise SystemExit(1)

print('V432 document structure audit: PASS')
