#!/usr/bin/env python3
"""Export the PNG icons from assets/img/favicon.svg, which is the one to edit.

    python3 tools/icons.py

Browser tabs use the SVG itself. The PNGs are for what cannot: older browsers,
and phone home screens through apple-touch-icon. A home screen rounds the corners
for itself and turns any transparency black, so that one is a full square with the
letters pulled in from the edge.

Rendering is Chrome headless, like the social cards, and sips does the scaling, so
this only runs on a Mac. Chrome will not open a window narrower than 500px, which is
why everything is drawn at 512 and scaled down.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets/img"
CHROME = next((p for p in [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    shutil.which("google-chrome") or "",
] if p and Path(p).exists()), None)


def render(svg, out, size, tmp):
    page = tmp / "icon.html"
    shot = tmp / "icon.png"
    sized = svg.replace("<svg ", '<svg width="512" height="512" style="display:block" ', 1)
    page.write_text(f"<!DOCTYPE html><body style='margin:0;background:transparent'>{sized}")
    subprocess.run([
        CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1", "--default-background-color=00000000",
        "--window-size=512,512", f"--user-data-dir={tmp / 'chrome'}",
        f"--screenshot={shot}", page.as_uri(),
    ], check=True, capture_output=True)
    subprocess.run(["sips", "-Z", str(size), str(shot), "--out", str(out)],
                   check=True, capture_output=True)
    print(f"  {out.relative_to(ROOT)}  {size}x{size}")


def main():
    if CHROME is None or shutil.which("sips") is None:
        sys.exit("needs Chrome and sips (macOS)")
    svg = (IMG / "favicon.svg").read_text()
    # Square corners, and the letters scaled toward the center.
    square = svg.replace(' rx="14"', "")
    square = re.sub(r"<g ", '<g transform="translate(32 32) scale(.84) translate(-32 -32)" ', square, count=1)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        render(svg, IMG / "favicon-48.png", 48, tmp)
        render(square, IMG / "apple-touch-icon.png", 180, tmp)


if __name__ == "__main__":
    main()
