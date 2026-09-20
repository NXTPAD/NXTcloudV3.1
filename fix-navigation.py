#!/usr/bin/env python3
import re
import sys
from pathlib import Path

site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not site.exists():
    raise SystemExit(f"Missing {site}")

cloud = "https://nxtcloudv31.nxtpadsupport.workers.dev"

targets = {
    "CLOUD": f"{cloud}/#home",
    "PAD": f"{cloud}/#pad",
    "DEX": f"{cloud}/#dex",
    "AI": f"{cloud}/#ai",
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

    # Replace ecosystem links by their visible button label.
    # This catches old links even if the ZIP contains a different URL.
    for label, url in targets.items():
        pattern = rf'(<a\b[^>]*\bhref=["\''])[^"\'']*(["\''][^>]*>\s*{label}\s*</a>)'
        text = re.sub(pattern, rf'\\g<1>{url}\\g<2>', text, flags=re.I)

    # Also remove the known old PAD destination anywhere it occurs.
    text = text.replace(
        "https://nxtpad.nxtpadsupport.workers.dev/",
        f"{cloud}/#pad"
    ).replace(
        "https://nxtpad.nxtpadsupport.workers.dev",
        f"{cloud}/#pad"
    )

    # Force the primary index navigation to the exact requested destinations.
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
            print(f"Forced exact ecosystem pill in {path}")

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated {path}")

print(f"Navigation fix complete. Changed {changed} file(s).")
