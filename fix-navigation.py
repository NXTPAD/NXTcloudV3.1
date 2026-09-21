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





def apply_launchpad_social_links(text):
    """Add optional project social links directly below Description in Launchpad Step 2 for every chain."""
    # Remove any earlier injected versions, including a malformed version that was
    # rendered as literal JavaScript at the bottom of the page.
    text = re.sub(r'<style[^>]*id=["\']nxt-launchpad-social-links-css(?:-v3)?["\'][^>]*>.*?</style>', '', text, flags=re.S | re.I)
    text = re.sub(r'<script[^>]*id=["\']nxt-launchpad-social-links-v3["\'][^>]*>.*?</script>', '', text, flags=re.S | re.I)
    text = re.sub(r'\(function\s*\(\)\s*\{\s*var ID\s*=\s*[\'"]nxt-launchpad-social-links-v3[\'"].*?\}\)\(\)\s*;?', '', text, flags=re.S)
    if 'id="nxt-launchpad-social-links-v4"' in text:
        return text

    """Add the same optional social-link section to Launchpad Step 2 for every supported chain."""
    if 'id="nxt-launchpad-social-links-v4"' in text:
        return text

    css = r'''
<style id="nxt-launchpad-social-links-css-v4">
#nxt-launchpad-social-links-v4 {
  display: block !important;
  width: 100% !important;
  margin: 20px 0 0 !important;
  padding: 18px 0 0 !important;
  border-top: 1px solid rgba(120,160,200,.16);
  box-sizing: border-box !important;
  clear: both !important;
}
#nxt-launchpad-social-links-v4 h3 { margin: 0 0 6px; font-size: 1rem; }
#nxt-launchpad-social-links-v4 > p { margin: 0 0 14px; opacity: .68; font-size: .88rem; line-height: 1.45; }
#nxt-launchpad-social-links-v4 .nxt-social-grid {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;
}
#nxt-launchpad-social-links-v4 .nxt-social-field { min-width: 0; }
#nxt-launchpad-social-links-v4 label { display: block; margin: 0 0 7px; font-size: .9rem; }
#nxt-launchpad-social-links-v4 input {
  display: block !important; width: 100% !important; min-width: 0 !important;
  min-height: 46px !important; box-sizing: border-box !important;
}
@media (max-width: 640px) {
  #nxt-launchpad-social-links-v4 .nxt-social-grid { grid-template-columns: 1fr; }
}
</style>
'''

    js = r'''
<script id="nxt-launchpad-social-links-v4">
(function () {
  var ID = 'nxt-launchpad-social-links-v4';
  var running = false;

  function clean(s) {
    return (s || '').replace(/\s+/g, ' ').trim();
  }

  function isLaunchpadStep2() {
    var body = clean(document.body && document.body.innerText);
    return /define\s+your\s+token/i.test(body) &&
           /token\s+name/i.test(body) &&
           /total\s+supply/i.test(body);
  }

  function directText(el) {
    var out = '';
    for (var i = 0; i < el.childNodes.length; i++) {
      if (el.childNodes[i].nodeType === 3) out += ' ' + el.childNodes[i].nodeValue;
    }
    return clean(out);
  }

  function findDescriptionField() {
    var fields = document.querySelectorAll('textarea, input, [contenteditable="true"]');

    // Prefer an actual form control whose attributes identify it as Description.
    for (var i = 0; i < fields.length; i++) {
      var field = fields[i];
      var attrs = clean(
        (field.getAttribute('name') || '') + ' ' +
        (field.getAttribute('id') || '') + ' ' +
        (field.getAttribute('placeholder') || '') + ' ' +
        (field.getAttribute('aria-label') || '')
      ).toLowerCase();
      if (/\bdescription\b|\bdesc\b/.test(attrs)) return field;
    }

    // Find the visible Description label, then locate its nearest field.
    var candidates = document.querySelectorAll('label, div, span, p');
    for (var j = 0; j < candidates.length; j++) {
      var label = candidates[j];
      var own = directText(label);
      var full = clean(label.textContent);

      if (!/^description(?:\s+optional)?$/i.test(own) &&
          !/^description(?:\s+optional)?$/i.test(full)) continue;

      // If it is a label with a "for" target, use that exact control.
      var targetId = label.getAttribute('for');
      if (targetId) {
        var target = document.getElementById(targetId);
        if (target && !target.closest('#' + ID)) return target;
      }

      // Walk upward, but only accept a small wrapper containing one field.
      var node = label;
      for (var level = 0; level < 8 && node; level++, node = node.parentElement) {
        var inside = node.querySelectorAll('textarea, input, [contenteditable="true"]');
        if (inside.length === 1 && !inside[0].closest('#' + ID)) return inside[0];
      }
    }

    // Final fallback: the Description field is normally the last textarea/input
    // in Step 2 before the Back/Review controls.
    if (isLaunchpadStep2()) {
      var textareas = document.querySelectorAll('textarea');
      if (textareas.length) return textareas[textareas.length - 1];
    }

    return null;
  }

  function createBox() {
    var box = document.createElement('div');
    box.id = ID;
    box.innerHTML =
      '<h3>Social links <span style="opacity:.55;font-weight:400">optional</span></h3>' +
      '<p>Add the official links for this project. These fields are available on every Launchpad chain.</p>' +
      '<div class="nxt-social-grid">' +
        '<div class="nxt-social-field"><label for="nxt-social-website">Website</label><input id="nxt-social-website" name="website" type="url" autocomplete="url" placeholder="https://yourproject.com"></div>' +
        '<div class="nxt-social-field"><label for="nxt-social-x">X / Twitter</label><input id="nxt-social-x" name="twitter" type="url" placeholder="https://x.com/yourproject"></div>' +
        '<div class="nxt-social-field"><label for="nxt-social-telegram">Telegram</label><input id="nxt-social-telegram" name="telegram" type="url" placeholder="https://t.me/yourproject"></div>' +
        '<div class="nxt-social-field"><label for="nxt-social-discord">Discord</label><input id="nxt-social-discord" name="discord" type="url" placeholder="https://discord.gg/yourinvite"></div>' +
      '</div>';
    return box;
  }

  function addSocialLinks() {
    if (!document.body || !isLaunchpadStep2()) return;
    if (document.getElementById(ID) || running) return;

    var desc = findDescriptionField();
    if (!desc || !desc.parentNode) return;

    running = true;
    var box = createBox();

    // Put the block immediately after the Description control itself.
    // This avoids depending on framework-specific wrapper class names.
    desc.parentNode.insertBefore(box, desc.nextSibling);
    running = false;
  }

  function run() {
    addSocialLinks();
    [100, 300, 700, 1200, 2000, 3500, 6000, 10000].forEach(function (ms) {
      setTimeout(addSocialLinks, ms);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }

  if (window.MutationObserver) {
    var observer = new MutationObserver(function () {
      if (!document.getElementById(ID)) addSocialLinks();
    });
    observer.observe(document.documentElement || document.body, {childList:true, subtree:true});
  }

  window.addEventListener('hashchange', run);
})();
</script>
'''

    if '</head>' in text:
        text = text.replace('</head>', css + '\n' + js + '\n</head>', 1)
    elif '<body' in text:
        text = text.replace('<body', js + '\n<body', 1)
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
        text = apply_launchpad_social_links(text)

    text = apply_coin_logos(text, path)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated {path}")

print(f"Navigation + coin-logo fix complete. Changed {changed} file(s).")
