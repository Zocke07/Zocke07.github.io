#!/usr/bin/env python3
"""Regression checks for the site. Run after any edit; run before any commit.

    python3 tools/check.py

Seven checks, each independent and each printing its own verdict:

  1. structure   tag balance, invalid nesting, duplicate ids, heading order
  2. links       every internal href/src/poster resolves on disk
  3. parity      each EN page and its zh twin share an id= and class= sequence
  4. chrome      the shared header/footer text is identical within each language
  5. deadcss     every class in style.css is used by some page or by main.js
  6. assets      every file under assets/ is referenced by some page
  7. stamps      every ?v= matches the hash of the file it points at

Exits non-zero if any check fails, so it can gate a commit.
"""

import collections
import glob
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

PAGES = sorted(glob.glob("*.html") + glob.glob("zh/*.html"))
CSS = Path("assets/css/style.css")
JS = Path("assets/js/main.js")

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}
# Elements that may not contain flow content, so a block child is a nesting bug.
PHRASING_ONLY = {"p"}
BLOCK = {"div", "p", "ul", "ol", "table", "section", "article", "figure",
         "pre", "aside", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"}

failures = []


def fail(check, msg):
    failures.append((check, msg))


# ---------- 1. structure ----------
class Structure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.ids = collections.Counter()
        self.headings = []
        self.errors = []
        self.svg_depth = 0
        self.tags = 0

    def handle_starttag(self, tag, attrs):
        self.tags += 1
        d = dict(attrs)
        if "id" in d:
            self.ids[d["id"]] += 1
        if tag == "svg":
            self.svg_depth += 1
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and not self.svg_depth:
            self.headings.append((self.getpos()[0], int(tag[1])))
        if tag in VOID:
            return
        # Inside <svg> the content model is XML; the parser cannot know which
        # elements self-close, so balance is not checked there.
        if self.svg_depth:
            return
        if self.stack and self.stack[-1][0] in PHRASING_ONLY and tag in BLOCK:
            self.errors.append(
                f"L{self.getpos()[0]}: <{tag}> inside <{self.stack[-1][0]}>")
        self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        self.tags += 1
        d = dict(attrs)
        if "id" in d:
            self.ids[d["id"]] += 1

    def handle_endtag(self, tag):
        if tag == "svg":
            self.svg_depth = max(0, self.svg_depth - 1)
            return
        if tag in VOID or self.svg_depth:
            return
        if not self.stack:
            self.errors.append(f"L{self.getpos()[0]}: stray </{tag}>")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for bad, ln in self.stack[i + 1:]:
                    self.errors.append(
                        f"L{ln}: <{bad}> never closed "
                        f"(hit </{tag}> at L{self.getpos()[0]})")
                del self.stack[i:]
                return
        self.errors.append(f"L{self.getpos()[0]}: stray </{tag}>")


# Malformed markup that html.parser silently reinterprets as text rather than
# reporting. `<<th` parses as a stray "<" plus a valid tag, so tag balance stays
# green while the rendered page shows a literal angle bracket.
MALFORMED = (
    ("<<", "doubled angle bracket"),
    ("< /", "space after </"),
    ('=""" ', "stray quote"),
    ("</>", "empty end tag"),
)


def check_structure():
    total = 0
    for f in PAGES:
        raw = Path(f).read_text(encoding="utf-8")
        for needle, why in MALFORMED:
            if needle in raw:
                ln = raw[:raw.index(needle)].count("\n") + 1
                fail("structure", f"{f}:L{ln}: {why} ({needle!r})")
        p = Structure()
        p.feed(Path(f).read_text(encoding="utf-8"))
        total += p.tags
        for e in p.errors:
            fail("structure", f"{f}:{e}")
        for tag, ln in p.stack:
            if tag not in ("html", "body", "head"):
                fail("structure", f"{f}:L{ln}: <{tag}> unclosed at EOF")
        for k, v in p.ids.items():
            if v > 1:
                fail("structure", f"{f}: duplicate id {k!r} ({v}x)")
        h1 = sum(1 for _, lv in p.headings if lv == 1)
        if h1 != 1:
            fail("structure", f"{f}: {h1} <h1> (want exactly 1)")
        prev = 0
        for ln, lv in p.headings:
            if prev and lv > prev + 1:
                fail("structure", f"{f}:L{ln}: h{lv} skips a level (prev h{prev})")
            prev = lv
    return f"{len(PAGES)} pages, {total} tags"


# ---------- 2. links ----------
def resolve(ref):
    """Resolve an internal reference the way GitHub Pages does."""
    ref = ref.split("#")[0].split("?")[0]
    if not ref:
        return True
    if re.match(r"^(https?:|mailto:|data:|tel:)", ref):
        return True
    if not ref.startswith("/"):
        return True  # relative refs are not used on this site; ignore
    stem = ref.lstrip("/")
    if stem in ("", "zh/"):
        stem += "index.html"
    local = Path(stem)
    if local.is_file():
        return True
    if not local.suffix:
        return local.with_suffix(".html").is_file() or (local / "index.html").is_file()
    return False


def check_links():
    n = 0
    seen = set()
    for f in PAGES:
        text = Path(f).read_text(encoding="utf-8")
        for attr in ("href", "src", "poster"):
            for m in re.finditer(rf'\b{attr}="([^"]+)"', text):
                ref = m.group(1)
                if not ref.startswith("/"):
                    continue
                seen.add(ref)
                n += 1
                if not resolve(ref):
                    fail("links", f"{f}: {attr}={ref!r} does not resolve")
    # Fragment targets on the two index pages.
    for f in ("index.html", "zh/index.html"):
        text = Path(f).read_text(encoding="utf-8")
        ids = set(re.findall(r'\bid="([^"]+)"', text))
        for m in re.finditer(r'href="#([^"]+)"', text):
            if m.group(1) not in ids:
                fail("links", f"{f}: #{m.group(1)} has no target")
    return f"{n} refs, {len(seen)} unique"


# ---------- 3. EN/ZH parity ----------
def seq(path, attr):
    text = Path(path).read_text(encoding="utf-8")
    # Only the <main> body; chrome is compared separately by check_chrome.
    m = re.search(r"<main\b.*?</main>", text, re.S)
    body = m.group(0) if m else text
    return re.findall(rf'\b{attr}="([^"]*)"', body)


def check_parity():
    pairs = [(f, f"zh/{f}") for f in glob.glob("*.html")]
    for en, zh in pairs:
        if not Path(zh).is_file():
            fail("parity", f"{en} has no zh twin")
            continue
        for attr in ("id", "class"):
            a, b = seq(en, attr), seq(zh, attr)
            if a != b:
                diff = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                            min(len(a), len(b)))
                fail("parity",
                     f"{en} vs {zh}: {attr} sequence diverges at #{diff} "
                     f"({a[diff] if diff < len(a) else '<end>'!r} vs "
                     f"{b[diff] if diff < len(b) else '<end>'!r})")
    return f"{len(pairs)} pairs"


# ---------- 4. chrome consistency ----------
CHROME_PATTERNS = {
    "skip-link": r'class="skip-link"[^>]*>([^<]*)<',
    "nav-brand": r'class="nav-brand"[^>]*>([^<]*)<',
    "nav-toggle aria-label": r'class="nav-toggle"[^>]*aria-label="([^"]*)"',
    "theme-toggle aria-label": r'class="theme-toggle"[^>]*aria-label="([^"]*)"',
    "to-top aria-label": r'class="to-top"[^>]*aria-label="([^"]*)"',
    "footer": r'<footer class="site-footer">.*?<p>(.*?)</p>',
}


def check_chrome():
    for lang, files in (("en", glob.glob("*.html")), ("zh", glob.glob("zh/*.html"))):
        for name, pat in CHROME_PATTERNS.items():
            found = collections.defaultdict(list)
            for f in sorted(files):
                text = Path(f).read_text(encoding="utf-8")
                m = re.search(pat, text, re.S)
                if m:
                    # nav-brand legitimately differs on the index page only.
                    found[m.group(1).strip()].append(f)
            if len(found) > 1:
                variants = "; ".join(
                    f"{v!r} in {len(fs)} ({', '.join(fs[:2])}…)"
                    for v, fs in sorted(found.items(), key=lambda kv: -len(kv[1])))
                fail("chrome", f"[{lang}] {name} has {len(found)} variants: {variants}")
    return "en + zh"


# ---------- 5. dead CSS ----------
# Classes main.js adds at runtime; they will never appear in the markup.
RUNTIME = {"active", "is-paused", "is-ready", "open", "reveal",
           "scrolled", "show", "swap", "visible"}


def check_deadcss():
    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    declared = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))
    used = set()
    for f in PAGES:
        for m in re.finditer(r'class="([^"]*)"', Path(f).read_text(encoding="utf-8")):
            used.update(m.group(1).split())
    dead = declared - used - RUNTIME
    for c in sorted(dead):
        fail("deadcss", f"style.css declares .{c} but nothing uses it")
    return f"{len(declared)} classes declared, {len(used)} used"


# ---------- 6. unreferenced assets ----------
def check_assets():
    refs = set()
    for f in PAGES + [str(CSS)]:
        text = Path(f).read_text(encoding="utf-8")
        # Both root-relative (/assets/...) and the absolute og:image form.
        for m in re.finditer(r'(?:https?://[^"\'()]*?)?(/assets/[^"\')?]+)', text):
            refs.add(m.group(1).lstrip("/"))
    on_disk = {
        str(p) for p in Path("assets").rglob("*")
        if p.is_file() and not p.name.startswith(".")
    }
    # Only files git tracks are shipped; local-only originals are excluded.
    tracked = set(os.popen("git ls-files assets").read().split("\n")) - {""}
    for a in sorted(on_disk & tracked):
        if a not in refs:
            fail("assets", f"{a} is tracked but referenced by no page")
    return f"{len(on_disk & tracked)} tracked assets, {len(refs)} referenced"


# ---------- 7. cache stamps ----------
def check_stamps():
    import subprocess
    r = subprocess.run([sys.executable, "tools/bump.py", "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    for line in r.stdout.splitlines():
        if "stale:" in line:
            fail("stamps", line.split("stale:", 1)[1].strip())
    return "style.css + main.js"


CHECKS = [
    ("structure", check_structure),
    ("links", check_links),
    ("parity", check_parity),
    ("chrome", check_chrome),
    ("deadcss", check_deadcss),
    ("assets", check_assets),
    ("stamps", check_stamps),
]

if __name__ == "__main__":
    only = sys.argv[1:] or None
    for name, fn in CHECKS:
        if only and name not in only:
            continue
        before = len(failures)
        note = fn()
        bad = len(failures) - before
        mark = "FAIL" if bad else " ok "
        print(f"[{mark}] {name:10s} {note}" + (f"  ({bad} problems)" if bad else ""))
    if failures:
        print()
        for check, msg in failures:
            print(f"  {check}: {msg}")
        print(f"\n{len(failures)} problems")
    sys.exit(1 if failures else 0)
