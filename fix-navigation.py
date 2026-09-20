#!/usr/bin/env python3
import re
import sys
from pathlib import Path

site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not site.exists():
    raise SystemExit(f"Missing {site}")

cloud = "https://nxtcloudv31.nxtpadsupport.workers.dev"

changed = 0

for path in site.rglob("*"):
    if not path.is_file():
        continue

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue

    original = text

    # Replace old NXT PAD destination anywhere in the extracted site.
    text = text.replace(
        "https://nxtpad.nxtpadsupport.workers.dev/",
        f"{cloud}/#pad"
    )
    text = text.replace(
        "https://nxtpad.nxtpadsupport.workers.dev",
        f"{cloud}/#pad"
    )

    # Force the exact NXT ecosystem pill in the main page.
    if path.name == "index.html":
        nav = f'''<div class="nxt-ecosystem" aria-label="NXT ecosystem">
        <a class="active" href="{cloud}/#home">CLOUD</a>
        <a href="{cloud}/#pad">PAD</a>
        <a href="{cloud}/#dex">DEX</a>
        <a href="{cloud}/#ai">AI</a>
      </div>'''

        pattern = r'<div class="nxt-ecosystem"\s+aria-label="NXT ecosystem">.*?</div>'
        text, nav_count = re.subn(pattern, nav, text, count=1, flags=re.S)

        if nav_count:
            print("Forced ecosystem pill: HOME / PAD / DEX / AI")

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated {path}")

print(f"Navigation fix complete. Changed {changed} file(s).")
