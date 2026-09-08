#!/usr/bin/env python3
"""Render the 1200x630 social card for a page, from that page's own metadata.

    python3 tools/og.py                  # every Chinese page
    python3 tools/og.py zh/index.html    # just one
    python3 tools/og.py --all            # English pages too (see below)
    python3 tools/og.py --check          # exit 1 if a card has gone stale

The card text is read out of the page: the hero kicker, og:title, and
og:description. Nothing is restated here, so a card cannot drift from the page
it belongs to.

The English cards were drawn by hand before this existed and are not identical
to what this produces, so they are left alone unless --all is passed. The
palette and geometry below were measured off assets/img/og/lmad.png, so the two
sets sit in the same family.

Rendering is Chrome headless at exactly 1200x630. That means the system's own
CJK font (PingFang TC) does the Chinese, which is what the site uses too.

A rendered PNG is not reproducible byte for byte (Chrome version, font build),
so --check compares the text a card is drawn from against tools/og-cards.json,
written when it was last rendered.
"""

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/img/og"
# Kept out of assets/ on purpose: everything tracked under there has to be
# referenced by a page, and this is a record for the tools, not a served file.
SIDECAR = ROOT / "tools/og-cards.json"

CHROME = next((p for p in [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
] if p and Path(p).exists()), None)

# Measured off the hand-drawn cards, so a generated card matches the family.
CSS = """
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:1200px;height:630px}
  body{
    background:#0f141c;
    background-image:radial-gradient(60% 75% at 78% 42%,
      rgba(36,86,166,.34) 0%, rgba(36,86,166,.10) 45%, transparent 72%);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
      "Helvetica Neue",Arial,"PingFang TC","Noto Sans TC",
      "Microsoft JhengHei",sans-serif;
    -webkit-font-smoothing:antialiased;
    padding:88px;
    display:flex;flex-direction:column;
  }
  /* Top-anchored, as the hand-drawn cards are: the kicker sits on the
     padding line and the footer is pinned to the bottom. */
  .top{flex:1;display:flex;flex-direction:column;justify-content:flex-start}
  .kicker{
    color:#7aa7e8;font-size:19px;font-weight:700;
    text-transform:uppercase;letter-spacing:.18em;line-height:1;
  }
  /* uppercase and tight tracking do nothing for CJK, and 19px Han strokes
     read far lighter than 19px caps, so the Chinese kicker is set larger. */
  .kicker.cjk{font-size:23px;letter-spacing:.08em;text-transform:none}
  h1{
    color:#f2f5fa;font-size:64px;font-weight:700;line-height:1.19;
    letter-spacing:-.015em;margin-top:40px;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
    overflow:hidden;
    /* Two even lines rather than a long one and an orphan. */
    text-wrap:balance;
  }
  h1.cjk{letter-spacing:.01em;font-size:72px;line-height:1.24}
  h1.long{font-size:56px}
  h1.cjk.long{font-size:60px}
  .rule{width:117px;height:5px;background:#2f6fd0;margin-top:42px;border-radius:3px}
  .cjk ~ .rule,
  h1.cjk + .rule{margin-top:48px}
  p{
    color:#9aa7ba;font-size:24px;line-height:1.58;margin-top:36px;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
    overflow:hidden;
    text-wrap:balance;
  }
  p.cjk{font-size:25px;line-height:1.66;margin-top:40px}
  .foot{display:flex;align-items:center;height:62px}
  .badge{
    width:62px;height:62px;border-radius:15px;background:#2456a6;
    color:#fff;font-family:Georgia,serif;font-size:27px;font-weight:700;
    display:flex;align-items:center;justify-content:center;letter-spacing:.01em;
  }
  .who{color:#f2f5fa;font-size:26px;font-weight:700;margin-left:19px}
  .site{color:#8593a6;font-size:23px;margin-left:auto}
"""

TEMPLATE = """<!DOCTYPE html><html lang="{lang}"><head><meta charset="UTF-8">
<style>{css}</style></head><body>
<div class="top">
  <div class="kicker {cjk}">{kicker}</div>
  <h1 class="{cjk}{long}">{title}</h1>
  <div class="rule"></div>
  <p class="{cjk}">{desc}</p>
</div>
<div class="foot">
  <div class="badge">RW</div>
  <div class="who">{who}</div>
  <div class="site">zocke07.github.io</div>
</div>
</body></html>"""


def meta(text, prop):
    m = re.search(rf'<meta property="{prop}" content="([^"]*)"', text)
    return html.unescape(m.group(1)) if m else ""


def kicker_of(text):
    m = re.search(r'<p class="hero-kicker">\s*(.*?)\s*</p>', text, re.S)
    if not m:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()


def card_for(page):
    text = (ROOT / page).read_text(encoding="utf-8")
    zh = page.startswith("zh/")
    title = meta(text, "og:title")
    # The home card is the only one whose og:title is the name; its kicker is a
    # location, which is not what a card wants to lead with.
    kicker = kicker_of(text)
    desc = meta(text, "og:description")
    # The home page is the one card not derived from an article. Its hero kicker
    # is a location and its og:description is a tagline, neither of which is
    # card copy, so the two lines it needs are written here.
    if page in ("index.html", "zh/index.html"):
        kicker = "作品集" if zh else "PORTFOLIO"
        title = "黃家輝" if zh else "Rivan Wong"
        desc = ("國立臺北科技大學資訊工程碩士，專注於軟體工程、"
                "自動化測試與聯邦式學習安全。") if zh else \
               "Computer Science M.S. graduate. Software Engineer, Security, Test Automation, in Taipei."
    return dict(
        lang="zh-Hant-TW" if zh else "en",
        cjk="cjk" if zh else "",
        long=" long" if (zh and len(title) > 15) or (not zh and len(title) > 46) else "",
        kicker=html.escape(kicker),
        title=html.escape(title),
        desc=html.escape(desc),
        who="黃家輝" if zh else "Rivan Wong",
    )


def render(page, out_png):
    if CHROME is None:
        sys.exit("No Chrome or Chromium found; cannot render cards.")
    spec = card_for(page)
    doc = TEMPLATE.format(css=CSS, **spec)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "card.html"
        src.write_text(doc, encoding="utf-8")
        subprocess.run([
            CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=1", "--default-background-color=00000000",
            "--virtual-time-budget=3000", "--window-size=1200,630",
            f"--screenshot={out_png}", src.as_uri(),
        ], capture_output=True)
    return spec


ZH_PAGES = sorted(p.name for p in ROOT.glob("zh/*.html"))
SLUG = {
    "index.html": "home", "case-study-ai-products.html": "ai",
    "case-study-capstone.html": "capstone",
    "case-study-kitaliturgi.html": "kitaliturgi",
    "case-study-lmad.html": "lmad",
    "case-study-makerspace.html": "makerspace",
    "case-study-microprocessors.html": "micro",
    "case-study-sky-scraper-escape.html": "sky",
    "case-study-test-automation.html": "ta",
    "case-study-url-shortener.html": "url-shortener",
    "project-mobile-testing.html": "mobile",
}


def every_page():
    return [f"zh/{n}" for n in ZH_PAGES] + list(SLUG)


def load_sidecar():
    return json.loads(SIDECAR.read_text(encoding="utf-8")) if SIDECAR.is_file() else {}


def save_sidecar(specs):
    SIDECAR.write_text(json.dumps(specs, ensure_ascii=False, indent=2,
                                  sort_keys=True) + "\n", encoding="utf-8")


def check():
    """Compare each page's card copy with what its card was drawn from."""
    recorded = load_sidecar()
    stale = []
    for page in every_page():
        want = card_for(page)
        have = recorded.get(page)
        if have is None:
            stale.append(f"{page}: no card recorded; run python3 tools/og.py --record")
        elif have != want:
            fields = sorted(k for k in want if have.get(k) != want[k])
            stale.append(f"{page}: card is stale, {', '.join(fields)} changed")
    for s in stale:
        print(f"  stale: {s}")
    print(f"{len(stale)} stale card(s) across {len(every_page())} pages")
    return 1 if stale else 0


def main(argv):
    if "--check" in argv:
        return check()
    targets = [a for a in argv if a.endswith(".html")]
    record_all = "--record" in argv
    if not targets:
        targets = [f"zh/{n}" for n in ZH_PAGES]
        if "--all" in argv or record_all:
            targets += list(SLUG)
    specs = load_sidecar()
    for page in targets:
        name = Path(page).name
        slug = SLUG[name]
        suffix = "-zh" if page.startswith("zh/") else ""
        out = OUT / f"{slug}{suffix}.png"
        # --record adopts the cards already in the repo, including the English
        # ones this tool did not draw, without re-rendering anything.
        spec = card_for(page) if record_all else render(page, out)
        specs[page] = spec
        size = out.stat().st_size if out.exists() else 0
        print(f"  {out.relative_to(ROOT)}  {size:>7,} B   {spec['title'][:38]}")
    save_sidecar(specs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
