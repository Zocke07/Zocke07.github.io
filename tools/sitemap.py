#!/usr/bin/env python3
"""Regenerate sitemap.xml from the pages themselves.

    python3 tools/sitemap.py            # write sitemap.xml
    python3 tools/sitemap.py --check    # exit 1 if it is stale

Every URL is read out of the page's own <link rel="canonical">, and the
hreflang alternates out of its <link rel="alternate">, so the sitemap cannot
name a URL the page disagrees with. Hand-maintaining it would mean a 17th
place to remember when a page is added, next to the four this site already
has; tools/check.py asserts this file instead.

No <lastmod>, <changefreq> or <priority>. Search engines ignore the latter two,
and a lastmod that is merely the file's mtime is worse than none: it claims a
freshness nobody verified. That also keeps this file stable, so a diff here
means a page was added or removed and nothing else.
"""

import glob
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sitemap.xml"

# The 404 is noindex: it exists to catch bad URLs, not to be one.
SKIP = {"404.html"}


def pages():
    return sorted(
        f for f in glob.glob("*.html") + glob.glob("zh/*.html") if f not in SKIP
    )


def link(text, rel, extra=""):
    m = re.search(rf'<link rel="{rel}"[^>]*{extra}[^>]*href="([^"]+)"', text)
    return m.group(1) if m else None


def build():
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for f in pages():
        text = (ROOT / f).read_text(encoding="utf-8")
        loc = link(text, "canonical")
        if not loc:
            sys.exit(f"sitemap: {f} has no <link rel=canonical>")
        out.append("  <url>")
        out.append(f"    <loc>{loc}</loc>")
        # Both twins of a pair carry the same alternate block, which is what
        # tells a crawler the two are one page in two languages rather than
        # duplicates competing with each other.
        for lang in ("en", "zh-Hant-TW", "x-default"):
            href = link(text, "alternate", f'hreflang="{lang}"')
            if href:
                out.append(
                    f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{href}"/>'
                )
        out.append("  </url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def main(argv):
    want = build()
    check = "--check" in argv
    have = OUT.read_text(encoding="utf-8") if OUT.is_file() else None
    if check:
        if have != want:
            print("sitemap.xml is stale; run python3 tools/sitemap.py", file=sys.stderr)
            return 1
        print(f"sitemap.xml current, {len(pages())} URLs")
        return 0
    OUT.write_text(want, encoding="utf-8")
    print(f"wrote sitemap.xml, {len(pages())} URLs")
    return 0


if __name__ == "__main__":
    import os

    os.chdir(ROOT)
    sys.exit(main(sys.argv[1:]))
