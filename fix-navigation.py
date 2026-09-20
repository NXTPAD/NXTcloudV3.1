#!/usr/bin/env python3
import re
import sys
from pathlib import Path

site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
index = site / "index.html"

if not index.exists():
    raise SystemExit(f"Missing {index}")

html = index.read_text(encoding="utf-8")

nav = """<div class="nxt-ecosystem" aria-label="NXT ecosystem">
        <a class="active" href="https://nxtcloudv31.nxtpadsupport.workers.dev/">CLOUD</a>
        <a href="https://nxtpad.nxtpadsupport.workers.dev/">PAD</a>
        <a href="https://nxtdex.nxtpadsupport.workers.dev/">DEX</a>
        <a href="https://nxtai.nxtpadsupport.workers.dev/">AI</a>
      </div>"""

pattern = r'<div class="nxt-ecosystem"\s+aria-label="NXT ecosystem">.*?</div>'
updated, count = re.subn(pattern, nav, html, count=1, flags=re.S)

if count != 1:
    raise SystemExit("Could not find the NXT ecosystem navigation in index.html")

index.write_text(updated, encoding="utf-8")
print("NXT ecosystem navigation fixed: CLOUD / PAD / DEX / AI")
