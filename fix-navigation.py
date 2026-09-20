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


def apply_coin_logos(text, path):
    """Replace known-token letter avatars with real logo images, with initials as fallback."""
    if path.name == "data.js":
        logos = {
            "SOL": "solana", "ETH": "ethereum", "BNB": "bnbchain", "POL": "polygon",
            "AVAX": "avalanche", "SUI": "sui", "ARB": "arbitrum", "JUP": "jupiter",
            "BONK": "bonk", "WBTC": "bitcoin", "USDC": "usdcoin", "USDT": "tether",
        }
        for symbol, logo in logos.items():
            marker = f'{symbol}: {{'
            if marker in text and 'logo:' not in text[text.find(marker):text.find(marker) + 220]:
                line_start = text.find(marker)
                line_end = text.find('\n', line_start)
                line = text[line_start:line_end]
                line = re.sub(r'(cg: "[^"]+")', rf'\1, logo: "{logo}"', line, count=1)
                text = text[:line_start] + line + text[line_end:]
        return text

    if path.name == "ui.js" and "const ICON_CDN = \"https://cdn.simpleicons.org\";" not in text:
        old = '''export function tokenAvatar(token, size = "") {
  const long = token.symbol.length > 3 ? " long" : "";
  return `<span class="tok ${size}${long}" style="--h:${token.hue}" aria-hidden="true">${esc(token.symbol.slice(0, 4))}</span>`;
}

export function chainGlyph(chain, size = "") {
  return `<span class="tok ${size}" style="--h:${chain.hue}" aria-hidden="true">${esc(chain.name[0])}</span>`;
}
'''
        new = '''const ICON_CDN = "https://cdn.simpleicons.org";

function logoAvatar(symbol, hue, size, logo, fallback) {
  const long = symbol.length > 3 ? " long" : "";
  const image = logo
    ? `<img src="${ICON_CDN}/${encodeURIComponent(logo)}" alt="" loading="lazy" decoding="async" onerror="this.remove();this.parentElement.textContent='${esc(fallback)}'">`
    : esc(fallback);
  return `<span class="tok ${size}${long}" style="--h:${hue}" aria-hidden="true">${image}</span>`;
}

export function tokenAvatar(token, size = "") {
  return logoAvatar(token.symbol, token.hue, size, token.logo, token.symbol.slice(0, 4));
}

export function chainGlyph(chain, size = "") {
  const logos = {
    solana: "solana", ethereum: "ethereum", base: "coinbase", bnb: "bnbchain",
    polygon: "polygon", arbitrum: "arbitrum", avalanche: "avalanche", sui: "sui",
  };
  return logoAvatar(chain.name, chain.hue, size, logos[chain.id], chain.name[0]);
}
'''
        if old in text:
            text = text.replace(old, new, 1)
        return text

    if path.name == "styles.css" and ".tok img {" not in text:
        needle = '.tok.long { font-size: .5rem; }\n'
        insert = '.tok img { width: 72%; height: 72%; display: block; object-fit: contain; }\n' + needle
        text = text.replace(needle, insert, 1)
        return text

    if path.name == "index.html":
        text = text.replace(
            '<span class="tok" style="--h:265">SOL</span>',
            '<span class="tok" style="--h:265" aria-hidden="true"><img src="https://cdn.simpleicons.org/solana" alt="" loading="lazy" decoding="async"></span>',
        )
        text = text.replace(
            '<span class="tok long" style="--h:212">USDC</span>',
            '<span class="tok long" style="--h:212" aria-hidden="true"><img src="https://cdn.simpleicons.org/usdcoin" alt="" loading="lazy" decoding="async"></span>',
        )
        return text

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

    text = apply_coin_logos(text, path)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated {path}")

print(f"Navigation + coin-logo fix complete. Changed {changed} file(s).")
