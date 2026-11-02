#!/usr/bin/env python3
"""Render the 1200x630 social card for a page, from that page's own metadata.

    python3 tools/og.py                  # every Chinese page
    python3 tools/og.py zh/index.html    # just one
    python3 tools/og.py --all            # English pages too (see below)
    python3 tools/og.py --check          # exit 1 if a card has gone stale

The card text is read out of the page: the summary strip's format and project,
og:title, and og:description. Nothing is restated here, so a card cannot drift
from the page it belongs to.

Every card, English and Chinese, is drawn by this script in the site's dark
theme: warm charcoal, the faint dot grid, the one orange, and Recursive from
assets/fonts. --all redraws the English set as well.

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

# The site's dark theme, so a card looks like the page it opens.
CSS = """
  @font-face{font-family:"Recursive";src:url("{FONT}") format("woff2");font-weight:300 1000}
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:1200px;height:630px}
  body{
    background-color:#181A17;
    background-image:
      radial-gradient(55% 70% at 86% 8%, rgba(255,148,71,.17), transparent 70%),
      radial-gradient(circle, rgba(236,232,220,.10) 1px, transparent 1.6px);
    background-size:auto, 22px 22px;
    font-family:"Recursive","PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;
    color:#ECE8DC;
    -webkit-font-smoothing:antialiased;
    padding:84px 88px;
    display:flex;flex-direction:column;
  }
  .top{flex:1;display:flex;flex-direction:column;justify-content:flex-start}
  .kicker{display:flex;align-items:center;gap:18px;font-size:22px;line-height:1.2}
  .fmt{display:inline-flex;align-items:center;gap:14px;color:#FF9447;font-weight:700}
  .fmt::before{content:"";width:14px;height:14px;border-radius:50%;background:#FF9447;
    box-shadow:0 0 0 6px rgba(255,148,71,.18)}
  .sep{width:6px;height:6px;border-radius:50%;background:#737869}
  .proj{color:#ABA799}
  .cjk .fmt,.cjk .proj{font-size:24px}
  h1{
    font-size:66px;font-weight:800;line-height:1.12;letter-spacing:-.025em;margin-top:44px;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
    text-wrap:balance;
  }
  h1.cjk{font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;
    font-weight:600;letter-spacing:.02em;font-size:70px;line-height:1.25}
  h1.long{font-size:56px}
  h1.cjk.long{font-size:60px}
  .wire{position:relative;width:150px;height:3px;margin:40px 0 0 7px;border-radius:2px;
    background:linear-gradient(90deg,#FF9447,#FFB680)}
  .wire::before{content:"";position:absolute;left:-7px;top:-6px;width:15px;height:15px;
    border-radius:50%;background:#FF9447}
  p{
    color:#ABA799;font-size:25px;line-height:1.55;margin-top:34px;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
    text-wrap:balance;
  }
  p.cjk{font-size:26px;line-height:1.7;margin-top:38px}
  .foot{display:flex;align-items:center;height:56px}
  .ring{width:30px;height:30px;border-radius:50%;border:5px solid #FF9447}
  .who{font-size:27px;font-weight:760;margin-left:16px}
  .site{color:#959285;font-size:23px;margin-left:auto}
"""

TEMPLATE = """<!DOCTYPE html><html lang="{lang}"><head><meta charset="UTF-8">
<style>{css}</style></head><body>
<div class="top">
  <div class="kicker {cjk}"><span class="fmt">{fmt}</span><span class="sep"></span><span class="proj">{proj}</span></div>
  <h1 class="{cjk}{long}">{title}</h1>
  <div class="wire"></div>
  <p class="{cjk}">{desc}</p>
</div>
<div class="foot">
  <div class="ring"></div>
  <div class="who">{who}</div>
  <div class="site">zocke07.github.io</div>
</div>
</body></html>"""


def meta(text, prop):
    m = re.search(rf'<meta property="{prop}" content="([^"]*)"', text)
    return html.unescape(m.group(1)) if m else ""


def summary_of(text):
    """The summary strip's format and project, the two facts a card leads with."""
    fmt = re.search(r'<dd class="format">\s*(.*?)\s*</dd>', text, re.S)
    if not fmt:
        return "", ""
    proj = re.search(r"<dd>\s*(.*?)\s*</dd>", text[fmt.end():], re.S)

    def clean(m):
        return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""

    project = clean(proj)
    # A long project line keeps its first clause: the card has one line for it.
    if len(project) > 34:
        project = re.split(r"[;,；，]", project)[0].strip()
    return clean(fmt), project


def card_for(page):
    text = (ROOT / page).read_text(encoding="utf-8")
    zh = page.startswith("zh/")
    title = meta(text, "og:title")
    fmt, proj = summary_of(text)
    desc = meta(text, "og:description")
    # The home page is the one card not derived from an article. Its hero kicker
    # is a location and its og:description is a tagline, neither of which is
    # card copy, so the two lines it needs are written here.
    if page in ("index.html", "zh/index.html"):
        fmt, proj = ("作品集", "新北市") if zh else ("Portfolio", "New Taipei, Taiwan")
        title = "黃家輝" if zh else "Rivan Wong"
        desc = ("軟體工程師，資訊工程碩士。自動化測試、後端服務"
                "與聯邦式學習安全。") if zh else \
               "Software engineer with an M.S. in Computer Science: test automation, backend services and federated learning security."
    return dict(
        lang="zh-Hant-TW" if zh else "en",
        cjk="cjk" if zh else "",
        long=" long" if (zh and len(title) > 15) or (not zh and len(title) > 46) else "",
        fmt=html.escape(fmt),
        proj=html.escape(proj),
        title=html.escape(title),
        desc=html.escape(desc),
        who="黃家輝" if zh else "Rivan Wong",
    )


def render(page, out_png):
    if CHROME is None:
        sys.exit("No Chrome or Chromium found; cannot render cards.")
    spec = card_for(page)
    css = CSS.replace("{FONT}", (ROOT / "assets/fonts/recursive.woff2").as_uri())
    doc = TEMPLATE.format(css=css, **spec)
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
    "case-study-agentbase.html": "agentbase",
    "case-study-capstone.html": "capstone",
    "case-study-event-courier.html": "event-courier",
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
