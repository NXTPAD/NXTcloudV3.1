#!/usr/bin/env python3
import re
import sys
from pathlib import Path

site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not site.exists():
    raise SystemExit(f"Missing {site}")

cloud = "https://nxtcloudv31.nxtpadsupport.workers.dev"
changed = 0

def remove_primary_nav(text):
    # Remove the separate DEX / Launchpad / NXT AI header navigation.
    # This targets only <nav class="nav"> and never touches the ecosystem pill.
    pattern = r'<nav\b[^>]*\bclass=["\'][^"\']*\bnav\b[^"\']*["\'][^>]*>.*?</nav>'
    text, count = re.subn(pattern, "", text, count=1, flags=re.S | re.I)
    if count:
        print("Removed standalone primary navigation")
    return text

for path in site.rglob("*"):
    if not path.is_file():
        continue

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue

    original = text

    # Redirect any old standalone NXT PAD destination to the real Launchpad route.
    text = text.replace(
        "https://nxtpad.nxtpadsupport.workers.dev/",
        f"{cloud}/#launchpad"
    )
    text = text.replace(
        "https://nxtpad.nxtpadsupport.workers.dev",
        f"{cloud}/#launchpad"
    )

    if path.name == "index.html":
        # Preserve and explicitly set ONLY the ecosystem pill.
        nav = f'''<div class="nxt-ecosystem" aria-label="NXT ecosystem">
        <a href="{cloud}/#home" data-pill="cloud">CLOUD</a>
        <a href="{cloud}/#launchpad" data-pill="pad">PAD</a>
        <a href="{cloud}/#dex" data-pill="dex">DEX</a>
        <a href="{cloud}/#ai" data-pill="ai">AI</a>
      </div>'''

        pattern = r'<div class="nxt-ecosystem"\s+aria-label="NXT ecosystem">.*?</div>'
        text, nav_count = re.subn(pattern, nav, text, count=1, flags=re.S)

        if nav_count:
            print("Set ecosystem pill: CLOUD / PAD(#launchpad) / DEX / AI")

        text = remove_primary_nav(text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated {path}")

print(f"Navigation fix complete. Changed {changed} file(s).")
