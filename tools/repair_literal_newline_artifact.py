from pathlib import Path
import hashlib
import re
import subprocess

INDEX = Path("index.html")
text = INDEX.read_text(encoding="utf-8")

# Remove the temporary runtime guard, including any malformed escaped-newline copy.
guard_re = re.compile(r'(?is)<script id="literal-newline-artifact-guard">.*?</script>')
text = guard_re.sub("", text)

# Normalize the known generated TBC v3.4.0 style block. This block is absent in Manuscript.
style_re = re.compile(r'(?is)(<style id="v340-product-polish">)(.*?)(</style>)')
match = style_re.search(text)
if match:
    inner = match.group(2).replace("\\r", "\n").replace("\\n", "\n")
    text = text[:match.start()] + match.group(1) + inner + match.group(3) + text[match.end():]

# Literal escaped-newline-only text between structural elements in <head> is invalid HTML text.
head_re = re.compile(r"(?is)(<head\b[^>]*>)(.*?)(</head>)")
head = head_re.search(text)
if not head:
    raise SystemExit("missing structural <head>")

gap_re = re.compile(r"(?s)(?<=>)((?:[ \t\r\n]|\\[nr])+)(?=<)")
head_inner = gap_re.sub(
    lambda m: m.group(1).replace("\\r", "\n").replace("\\n", "\n"),
    head.group(2),
)
head_inner = re.sub(
    r"^(?:\s|\\[nr])+",
    lambda m: m.group(0).replace("\\r", "\n").replace("\\n", "\n"),
    head_inner,
)
head_inner = re.sub(
    r"(?:\s|\\[nr])+$",
    lambda m: m.group(0).replace("\\r", "\n").replace("\\n", "\n"),
    head_inner,
)
text = text[:head.start()] + head.group(1) + head_inner + head.group(3) + text[head.end():]

# Repair escaped-newline-only text immediately after <body>.
body = re.search(r"(?is)<body\b[^>]*>", text)
if not body:
    raise SystemExit("missing structural <body>")
first_child = text.find("<", body.end())
if first_child > body.end():
    prefix = text[body.end():first_child]
    if re.fullmatch(r"(?:\s|\\[nr])*", prefix):
        prefix = prefix.replace("\\r", "\n").replace("\\n", "\n")
        text = text[:body.end()] + prefix + text[first_child:]

# Verify the exact failure mode cannot remain.
head = head_re.search(text)
bad_gaps = [
    m.group(1)
    for m in gap_re.finditer(head.group(2))
    if "\\n" in m.group(1) or "\\r" in m.group(1)
]
if bad_gaps:
    raise SystemExit(f"escaped structural newline remains in <head>: {bad_gaps!r}")

body = re.search(r"(?is)<body\b[^>]*>", text)
first_child = text.find("<", body.end())
body_prefix = text[body.end():first_child]
if "\\n" in body_prefix or "\\r" in body_prefix:
    raise SystemExit(f"escaped structural newline remains after <body>: {body_prefix!r}")

match = style_re.search(text)
if match and ("\\n" in match.group(2) or "\\r" in match.group(2)):
    raise SystemExit("escaped newline remains in v340-product-polish")

if "literal-newline-artifact-guard" in text:
    raise SystemExit("temporary runtime guard was not fully removed")

INDEX.write_text(text, encoding="utf-8")

# Manuscript caches its shell with a service worker. Ensure existing clients recache the repaired HTML.
sw = Path("sw.js")
if sw.exists():
    marker = "// literal-newline-cache-refresh: 2026-09-10\n"
    sw_text = sw.read_text(encoding="utf-8")
    if marker not in sw_text:
        sw.write_text(marker + sw_text, encoding="utf-8")

digest_file = Path("V432_SHA256.txt")
if digest_file.exists():
    digest_file.write_text(hashlib.sha256(INDEX.read_bytes()).hexdigest() + "\n", encoding="utf-8")

subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
subprocess.run(
    ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
    check=True,
)
paths = ["index.html"]
if sw.exists():
    paths.append("sw.js")
if digest_file.exists():
    paths.append("V432_SHA256.txt")
subprocess.run(["git", "add", *paths], check=True)

changed = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
if changed:
    subprocess.run(["git", "commit", "-m", "fix: fully remove literal newline rendering artifacts"], check=True)
    subprocess.run(["git", "push"], check=True)
else:
    print("literal newline artifact repair: no changes required")

print("literal newline artifact repair: PASS")
