#!/usr/bin/env python3
import re
import sys
from pathlib import Path

site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

if not site.exists():
    raise SystemExit(f"Missing {site}")

cloud = "https://nxtcloudv31.nxtpadsupport.workers.dev"

# Fix every text file in the extracted site so an old PAD URL cannot survive
# in HTML, JS, JSX, or other source files used by the deployed site.
replacements = {
    "https://nxtpad.nxtpadsupport.workers.dev/": f"{cloud}/#pad",
    "https://nxtpad.nxtpadsupport.workers.dev": f"{cloud}/#pad",
}

changed = 0
for path in site.rglob("*"):
    if not path.is_file():
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue

    original = text
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Force the ecosystem pill in index.html to stay entirely on NXT CLOUD.
    if path.name == "index.html":
        nav = """<div class="nxt-ecosystem" aria-label="NXT ecosystem">
        <a class="active" href="https://nxtcloudv31.nxtpadsupport.workers.dev/#cloud">CLOUD</a>
        <a href="https://nxtcloudv31.nxtpadsupport.workers.dev/#pad">PAD</a>
        <a href="https://nxtcloudv31.nxtpadsupport.workers.dev/#dex">DEX</a>
        <a href="https://nxtcloudv31.nxtpadsupport.workers.dev/#ai">AI</a>
      </div>"""
        pattern = r'<div class="nxt-ecosystem"\s+aria-label="NXT ecosystem">.*?</div>'
        text, nav_count = re.subn(pattern, nav, text, count=1, flags=re.S)
        if nav_count:
            print(f"Fixed ecosystem pill in {path}")

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated {path}")

print(f"Navigation fix complete. Changed {changed} file(s).")
