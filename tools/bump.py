#!/usr/bin/env python3
"""Stamp the asset URLs with a hash of the asset, across every page.

    python3 tools/bump.py            # rewrite if needed
    python3 tools/bump.py --check    # report only, non-zero if stale

style.css and main.js are linked as `?v=<hash>` so a returning visitor is not
served a cached copy of a file that has changed. The number used to be a
counter bumped by hand in 32 places, which is 32 chances to miss one and no way
to tell afterwards. The hash comes from the file, so it cannot drift, and each
asset carries its own: editing the stylesheet no longer re-downloads the script.

There is still no build step. This rewrites the committed HTML in place; the
pages remain the deployed artefact.
"""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = {
    "/assets/css/style.css": ROOT / "assets/css/style.css",
    "/assets/js/main.js": ROOT / "assets/js/main.js",
}


def short_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def main(check_only=False):
    want = {url: short_hash(p) for url, p in ASSETS.items()}
    pages = sorted(list(ROOT.glob("*.html")) + list(ROOT.glob("zh/*.html")))
    stale, rewritten = [], 0

    for page in pages:
        text = original = page.read_text(encoding="utf-8")
        for url, h in want.items():
            pattern = re.compile(re.escape(url) + r"\?v=[\w.]+")
            found = pattern.findall(text)
            if not found:
                stale.append(f"{page.relative_to(ROOT)}: no reference to {url}")
                continue
            if any(f != f"{url}?v={h}" for f in found):
                stale.append(f"{page.relative_to(ROOT)}: {url} stamped {found[0].split('=')[-1]}, want {h}")
            text = pattern.sub(f"{url}?v={h}", text)
        if text != original:
            if not check_only:
                page.write_text(text, encoding="utf-8")
            rewritten += 1

    for url, h in want.items():
        print(f"  {url} -> v={h}")
    if check_only:
        for s in stale:
            print(f"  stale: {s}")
        print(f"{len(stale)} stale reference(s) across {len(pages)} pages")
        return 1 if stale else 0
    print(f"stamped {len(pages)} pages ({rewritten} changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
