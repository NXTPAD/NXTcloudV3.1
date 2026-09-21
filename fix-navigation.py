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



def apply_mobile_header_nav(text):
    """On small screens, replace the wallet CTA with the existing ecosystem pill."""
    if 'id="nxt-mobile-ecosystem-nav"' in text:
        return text

    mobile_css = r'''
<style id="nxt-mobile-ecosystem-nav">
@media (max-width: 768px) {
  header .connect-wallet,
  header .connectWallet,
  header [class*="connect-wallet"],
  header [class*="connectWallet"],
  header button[aria-label*="Connect Wallet" i],
  header button[data-action*="connect-wallet" i],
  header a[aria-label*="Connect Wallet" i] {
    display: none !important;
  }

  /* Free the mobile header space used by the theme switch. */
  header button[aria-label*="theme" i],
  header button[title*="theme" i],
  header button[aria-label*="dark mode" i],
  header button[aria-label*="light mode" i],
  header button[data-theme-toggle],
  header .theme-toggle,
  header .theme-switch,
  header .theme-button,
  header .dark-mode-toggle,
  header .light-mode-toggle {
    display: none !important;
  }

  header .nxt-ecosystem,
  .mobile-header .nxt-ecosystem,
  .site-header .nxt-ecosystem {
    display: inline-flex !important;
    align-items: center;
    flex: 0 0 180px !important;
    width: 180px !important;
    max-width: 180px !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    visibility: visible !important;
    opacity: 1 !important;
  }

  .nxt-ecosystem [data-pill],
  .nxt-ecosystem a {
    -webkit-tap-highlight-color: transparent;
    min-width: 0 !important;
    flex: 1 1 0 !important;
    width: 25% !important;
    padding-left: 3px !important;
    padding-right: 3px !important;
    font-size: 0.68rem !important;
    white-space: nowrap !important;
    text-align: center !important;
    box-sizing: border-box !important;
  }

  .nxt-ecosystem [data-pill].active,
  .nxt-ecosystem [data-pill][aria-current="page"] {
    opacity: 1 !important;
    transform: translateY(-1px);
  }
}
</style>
'''
    mobile_js = r'''
<script id="nxt-mobile-ecosystem-nav">
(function () {
  function setupMobileNav() {
    var pill = document.querySelector('.nxt-ecosystem');
    if (!pill) return;

    var isMobile = window.matchMedia('(max-width: 768px)').matches;
    var header = pill.closest('header') || document.querySelector('header');

    // Hide the mobile theme/dark-light switch to give the ecosystem pill room.
    if (isMobile && header) {
      header.querySelectorAll('button, a').forEach(function (control) {
        var label = (
          (control.textContent || '') + ' ' +
          (control.getAttribute('aria-label') || '') + ' ' +
          (control.getAttribute('title') || '') + ' ' +
          (control.getAttribute('data-testid') || '') + ' ' +
          (control.className || '')
        ).replace(/\\s+/g, ' ').toLowerCase();

        if (/theme|dark.?mode|light.?mode|theme.?toggle|theme.?switch/.test(label)) {
          control.setAttribute('data-nxt-mobile-theme-hidden', 'true');
          control.style.setProperty('display', 'none', 'important');
        }
      });
    }

    var walletControl = null;

    if (header) {
      var controls = header.querySelectorAll('button, a');
      controls.forEach(function (control) {
        var label = (control.textContent || '').replace(/\s+/g, ' ').trim().toLowerCase();
        var aria = (control.getAttribute('aria-label') || '').toLowerCase();
        var action = (control.getAttribute('data-action') || '').toLowerCase();
        var classes = (control.className || '').toString().toLowerCase();
        if (!walletControl &&
            (label.indexOf('connect wallet') !== -1 ||
             aria.indexOf('connect wallet') !== -1 ||
             action.indexOf('connect-wallet') !== -1 ||
             classes.indexOf('connect-wallet') !== -1 ||
             classes.indexOf('connectwallet') !== -1)) {
          walletControl = control;
        }
      });
    }

    if (isMobile && walletControl && pill !== walletControl) {
      // Put the ecosystem pill in the wallet button's exact DOM slot.
      walletControl.parentNode.insertBefore(pill, walletControl);
      walletControl.setAttribute('data-nxt-mobile-wallet-hidden', 'true');
      walletControl.style.setProperty('display', 'none', 'important');
    } else if (!isMobile) {
      document.querySelectorAll('[data-nxt-mobile-wallet-hidden="true"]').forEach(function (control) {
        control.style.removeProperty('display');
        control.removeAttribute('data-nxt-mobile-wallet-hidden');
      });
    }

    var current = (location.hash || '#home').replace(/^#/, '').toLowerCase();
    pill.querySelectorAll('[data-pill]').forEach(function (item) {
      var target = (item.getAttribute('href') || '').split('#')[1] || item.getAttribute('data-pill') || '';
      var active = target.toLowerCase() === current ||
                   (current === 'home' && item.getAttribute('data-pill') === 'cloud');
      item.classList.toggle('active', active);
      if (active) item.setAttribute('aria-current', 'page');
      else item.removeAttribute('aria-current');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupMobileNav);
  } else {
    setupMobileNav();
  }
  window.addEventListener('hashchange', setupMobileNav);
  window.addEventListener('resize', setupMobileNav);
})();
</script>
'''
    if '</head>' in text:
        text = text.replace('</head>', mobile_css + '\n</head>', 1)
    if '</body>' in text:
        text = text.replace('</body>', mobile_js + '\n</body>', 1)
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
        text = apply_mobile_header_nav(text)

    text = apply_coin_logos(text, path)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated {path}")

print(f"Navigation + coin-logo fix complete. Changed {changed} file(s).")
