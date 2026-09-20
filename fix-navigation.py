#!/usr/bin/env python3
import re
import sys
from pathlib import Path

site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not site.exists():
    raise SystemExit(f"Missing {site}")

cloud = "https://nxtcloudv31.nxtpadsupport.workers.dev"
changed = 0

def remove_extra_header_nav(text):
    header_pattern = r"(<header\b[^>]*>)(.*?)(</header>)"

    def clean_header(match):
        opening, body, closing = match.groups()
        protected = []
        pill_pattern = r'<div class="nxt-ecosystem"\s+aria-label="NXT ecosystem">.*?</div>'

        def protect(pill_match):
            protected.append(pill_match.group(0))
            return f"__NXT_ECOSYSTEM_PILL_{len(protected)-1}__"

        body = re.sub(pill_pattern, protect, body, count=1, flags=re.S)
        body = re.sub(
            r'<a\b[^>]*>\s*(?:DEX|Launchpad|NXT AI)\s*</a>',
            "",
            body,
            flags=re.I,
        )

        for i, pill in enumerate(protected):
            body = body.replace(f"__NXT_ECOSYSTEM_PILL_{i}__", pill)

        return opening + body + closing

    return re.sub(header_pattern, clean_header, text, flags=re.S | re.I)

for path in site.rglob("*"):
    if not path.is_file():
        continue

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue

    original = text

    text = text.replace(
        "https://nxtpad.nxtpadsupport.workers.dev/",
        f"{cloud}/#launchpad"
    )
    text = text.replace(
        "https://nxtpad.nxtpadsupport.workers.dev",
        f"{cloud}/#launchpad"
    )

    if path.name == "index.html":
        nav = f'''<div class="nxt-ecosystem" aria-label="NXT ecosystem">
        <a href="{cloud}/#home">CLOUD</a>
        <a href="{cloud}/#launchpad">PAD</a>
        <a href="{cloud}/#dex">DEX</a>
        <a href="{cloud}/#ai">AI</a>
      </div>'''

        pattern = r'<div class="nxt-ecosystem"\s+aria-label="NXT ecosystem">.*?</div>'
        text, nav_count = re.subn(pattern, nav, text, count=1, flags=re.S)

        if nav_count:
            print("Forced ecosystem pill: CLOUD / PAD(#launchpad) / DEX / AI")

        cleaned = remove_extra_header_nav(text)
        if cleaned != text:
            text = cleaned
            print("Removed standalone header links: DEX / Launchpad / NXT AI")

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated {path}")

print(f"Navigation fix complete. Changed {changed} file(s).")
