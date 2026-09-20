#!/usr/bin/env python3
import re
import sys
from pathlib import Path

site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not site.exists():
    raise SystemExit(f"Missing {site}")

cloud = "https://nxtcloudv31.nxtpadsupport.workers.dev"

changed = 0

router = r"""
<script id="nxt-hash-router">
(function () {
  const routes = ["home", "pad", "dex", "ai"];

  function currentRoute() {
    const raw = (window.location.hash || "#home").replace(/^#/, "").toLowerCase();
    return routes.includes(raw) ? raw : "home";
  }

  function setActive(route) {
    document.querySelectorAll(".nxt-ecosystem a").forEach(function (a) {
      const href = (a.getAttribute("href") || "").toLowerCase();
      a.classList.toggle("active", href.endsWith("#" + route));
      a.setAttribute("aria-current", href.endsWith("#" + route) ? "page" : "false");
    });
  }

  function showRoute(route) {
    setActive(route);

    const selectors = [
      '[data-page="' + route + '"]',
      '[data-section="' + route + '"]',
      '#page-' + route,
      '.page-' + route
    ];

    const target = document.querySelector(selectors.join(","));
    const candidates = Array.from(document.querySelectorAll(
      "[data-page], [data-section], [id^='page-'], [class*='page-']"
    ));

    if (target && candidates.length) {
      candidates.forEach(function (el) {
        const matches =
          el === target ||
          el.getAttribute("data-page") === route ||
          el.getAttribute("data-section") === route ||
          el.id === "page-" + route ||
          el.classList.contains("page-" + route);

        el.classList.toggle("nxt-route-hidden", !matches);
        el.setAttribute("aria-hidden", matches ? "false" : "true");
      });
    }

    document.body.setAttribute("data-nxt-route", route);
  }

  function navigate(route) {
    route = routes.includes(route) ? route : "home";
    if (window.location.hash !== "#" + route) {
      window.location.hash = route;
    } else {
      showRoute(route);
    }
  }

  document.addEventListener("click", function (event) {
    const link = event.target.closest(".nxt-ecosystem a");
    if (!link) return;

    const href = link.getAttribute("href") || "";
    const match = href.match(/#(home|pad|dex|ai)$/i);
    if (!match) return;

    event.preventDefault();
    navigate(match[1].toLowerCase());
  });

  window.addEventListener("hashchange", function () {
    showRoute(currentRoute());
  });

  document.addEventListener("DOMContentLoaded", function () {
    showRoute(currentRoute());
  });

  showRoute(currentRoute());
})();
</script>
"""

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
        f"{cloud}/#pad"
    )
    text = text.replace(
        "https://nxtpad.nxtpadsupport.workers.dev",
        f"{cloud}/#pad"
    )

    if path.name == "index.html":
        nav = f'''<div class="nxt-ecosystem" aria-label="NXT ecosystem">
        <a href="{cloud}/#home">CLOUD</a>
        <a href="{cloud}/#pad">PAD</a>
        <a href="{cloud}/#dex">DEX</a>
        <a href="{cloud}/#ai">AI</a>
      </div>'''

        pattern = r'<div class="nxt-ecosystem"\s+aria-label="NXT ecosystem">.*?</div>'
        text, nav_count = re.subn(pattern, nav, text, count=1, flags=re.S)

        if nav_count:
            print("Forced ecosystem pill: HOME / PAD / DEX / AI")

        if 'id="nxt-hash-router"' not in text:
            text = text.replace("</body>", """
<style id="nxt-hash-router-style">
.nxt-route-hidden { display: none !important; }
</style>
""" + router + "\n</body>", 1)
            print("Installed hash router")

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated {path}")

print(f"Navigation fix complete. Changed {changed} file(s).")
