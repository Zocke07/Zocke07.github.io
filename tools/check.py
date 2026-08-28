#!/usr/bin/env python3
"""Regression checks for the site. Run after any edit; run before any commit.

    python3 tools/check.py

Sixteen checks, each independent and each printing its own verdict, in the
order CHECKS runs them:

  1. structure   tag balance, invalid nesting, duplicate ids, heading order
  2. links       every internal URL resolves on disk, absolute ones included
  3. alternates  canonical and hreflang agree in both directions across a pair
  4. parity      each EN page and its zh twin share an id= and class= sequence
  5. chrome      the shared header/footer is identical, and present, per language
  6. css         style.css braces and comments balance
  7. deadcss     no class is declared without a user, or used without a definer
  8. assets      every file under assets/ is referenced by some page
  9. tracked     git tracks nothing outside the published site
 10. stamps      every ?v= matches the hash of the file it points at
 11. cv          the CV in assets/ still matches the one built in CV/
 12. og          each page points at its own social card and declares its locale
 13. cards       each generated social card still matches its page's metadata
 14. copy        English prose keeps one spelling and punctuation convention
 15. sitemap     sitemap.xml still matches the pages it is generated from
 16. cjk         no line break in Chinese prose renders as a stray space

Exits non-zero if any check fails, so it can gate a commit.
"""

import collections
import glob
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

PAGES = sorted(glob.glob("*.html") + glob.glob("zh/*.html"))
# Pages that deliberately ship in one copy. GitHub Pages serves the root
# 404.html for every bad URL on the site, /zh/ ones included, so there is no
# second file to keep in step and nothing for parity or og to compare. It is
# still held to structure, links, chrome and copy like every other page.
SINGLETON = {"404.html"}
CSS = Path("assets/css/style.css")
JS = Path("assets/js/main.js")
ORIGIN = "https://zocke07.github.io"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}
# Elements that may not contain flow content, so a block child is a nesting bug.
PHRASING_ONLY = {"p"}
BLOCK = {"div", "p", "ul", "ol", "table", "section", "article", "figure",
         "pre", "aside", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"}

failures = []


def fail(check, msg):
    failures.append((check, msg))


_text = {}


def read(path):
    """Read a UTF-8 file once. Sixteen checks read the same seventeen pages."""
    path = str(path)
    if path not in _text:
        _text[path] = Path(path).read_text(encoding="utf-8")
    return _text[path]


def git(*args):
    """Run a git command from the repo root and return its stdout lines."""
    r = subprocess.run(("git",) + args, capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        return None
    return [line for line in r.stdout.split("\n") if line]


def run_tool(check, script, note, scan=None):
    """Run a sibling generator in --check mode; its exit code is the assertion.

    `scan` pulls the readable detail out of stdout. When it finds nothing in a
    run that failed anyway, the raw output is reported, so a traceback cannot
    pass for silence.
    """
    r = subprocess.run([sys.executable, f"tools/{script}", "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    before = len(failures)
    if scan:
        for line in r.stdout.splitlines():
            found = scan(line)
            if found:
                fail(check, found)
    if r.returncode and len(failures) == before:
        fail(check, (r.stderr or r.stdout).strip() or f"tools/{script} --check failed")
    return r.stdout.strip() if note is None else note


# ---------- structure ----------
class Structure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.ids = collections.Counter()
        self.headings = []
        self.errors = []
        self.svg_depth = 0
        self.tags = 0

    def note(self, attrs):
        """Every tag is counted and its id recorded, self-closing or not."""
        self.tags += 1
        d = dict(attrs)
        if "id" in d:
            self.ids[d["id"]] += 1

    def handle_starttag(self, tag, attrs):
        self.note(attrs)
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
        # <img ... /> and friends: counted and id-checked, never stacked.
        self.note(attrs)

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
        raw = read(f)
        for needle, why in MALFORMED:
            if needle in raw:
                ln = raw[:raw.index(needle)].count("\n") + 1
                fail("structure", f"{f}:L{ln}: {why} ({needle!r})")
        p = Structure()
        p.feed(read(f))
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


# ---------- links ----------
def internal(ref):
    """The site-root path a reference points at, or None if it is not one.

    og:image, canonical, og:url and every hreflang name this site by its full
    URL, so the origin has to come off before the leading-slash test.
    """
    ref = ref.split("#")[0].split("?")[0]
    if ref.startswith(ORIGIN):
        ref = ref[len(ORIGIN):] or "/"
    return ref if ref.startswith("/") else None


def target(path):
    """The file GitHub Pages would serve for a site-root path, or None."""
    stem = path.lstrip("/")
    if stem in ("", "zh/"):
        stem += "index.html"
    local = Path(stem)
    if local.is_file():
        return str(local)
    if not local.suffix:
        for candidate in (local.with_suffix(".html"), local / "index.html"):
            if candidate.is_file():
                return str(candidate)
    return None


def check_links():
    n = 0
    seen = set()
    for f in PAGES:
        text = read(f)
        # content= carries og:image and og:url, the only internal URLs on the
        # site that never appear in an href, src or poster.
        for attr in ("href", "src", "poster", "content"):
            for m in re.finditer(rf'\b{attr}="([^"]+)"', text):
                ref = internal(m.group(1))
                if ref is None:
                    continue
                seen.add(ref)
                n += 1
                if target(ref) is None:
                    fail("links", f"{f}: {attr}={m.group(1)!r} does not resolve")
    # Fragment targets on the two index pages.
    for f in ("index.html", "zh/index.html"):
        text = read(f)
        ids = set(re.findall(r'\bid="([^"]+)"', text))
        for m in re.finditer(r'href="#([^"]+)"', text):
            if m.group(1) not in ids:
                fail("links", f"{f}: #{m.group(1)} has no target")
    return f"{n} refs, {len(seen)} unique"


# ---------- canonical + hreflang reciprocity ----------
def head_link(text, rel, extra=""):
    m = re.search(rf'<link rel="{rel}"[^>]*{extra}[^>]*href="([^"]+)"', text)
    return m.group(1) if m else None


def check_alternates():
    """Assert a pair agrees with itself about where its two halves live.

    Not something check_sitemap can cover: sitemap.py reads these canonicals as
    ground truth, so a wrong one survives into the expected output.
    """
    pairs = [(f, f"zh/{f}") for f in sorted(glob.glob("*.html"))
             if f not in SINGLETON and Path(f"zh/{f}").is_file()]
    for en, zh in pairs:
        canon = {}
        for lang, f in (("en", en), ("zh-Hant-TW", zh)):
            c = head_link(read(f), "canonical")
            if not c:
                fail("alternates", f"{f} has no canonical")
            elif (p := internal(c)) is None or target(p) != f:
                fail("alternates", f"{f}: canonical {c!r} does not name this page")
            canon[lang] = c
        # Both twins must publish the same block, and it must name each twin by
        # the URL that twin claims for itself.
        for f in (en, zh):
            text = read(f)
            for lang, want in canon.items():
                got = head_link(text, "alternate", f'hreflang="{lang}"')
                if got != want:
                    fail("alternates",
                         f"{f}: hreflang={lang} is {got!r}, but that page's "
                         f"canonical is {want!r}")
            xd = head_link(text, "alternate", 'hreflang="x-default"')
            if xd != canon["en"]:
                fail("alternates", f"{f}: x-default is {xd!r}, want {canon['en']!r}")
    return f"{len(pairs)} pairs, canonical + 3 alternates each"


# ---------- EN/ZH parity ----------
# The three regions every page is built from. check_chrome compares the words
# inside the header and footer; comparing structure here too is what catches an
# <li> dropped from one nav or a wrapper class lost on one page, neither of
# which changes any string chrome looks at.
REGIONS = ("main", "header", "footer")


def seq(path, attr, tag):
    m = re.search(rf"<{tag}\b.*?</{tag}>", read(path), re.S)
    return re.findall(rf'\b{attr}="([^"]*)"', m.group(0) if m else "")


def check_parity():
    pairs = [(f, f"zh/{f}") for f in glob.glob("*.html") if f not in SINGLETON]
    for en, zh in pairs:
        if not Path(zh).is_file():
            fail("parity", f"{en} has no zh twin")
            continue
        for tag in REGIONS:
            for attr in ("id", "class"):
                a, b = seq(en, attr, tag), seq(zh, attr, tag)
                if a == b:
                    continue
                diff = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                            min(len(a), len(b)))
                fail("parity",
                     f"{en} vs {zh}: <{tag}> {attr} sequence diverges at #{diff} "
                     f"({a[diff] if diff < len(a) else '<end>'!r} vs "
                     f"{b[diff] if diff < len(b) else '<end>'!r})")
    # The pass above enumerates English pages, so an orphaned Chinese page
    # would otherwise be examined by nothing.
    for zh in sorted(glob.glob("zh/*.html")):
        if not Path(Path(zh).name).is_file():
            fail("parity", f"{zh} has no English twin")
    return f"{len(pairs)} pairs x {len(REGIONS)} regions"


# ---------- chrome consistency ----------
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
                text = read(f)
                m = re.search(pat, text, re.S)
                if m:
                    # Every pattern captures text, not markup, so nav-brand's
                    # href (#top on the index page, / everywhere else) is
                    # outside the capture and needs no exemption here.
                    found[m.group(1).strip()].append(f)
            # Coverage, not just agreement: a pattern that matches nothing has
            # compared nothing, which is what a renamed class looks like.
            matched = sum(len(fs) for fs in found.values())
            if matched != len(files):
                missing = sorted(set(files) - {f for fs in found.values() for f in fs})
                fail("chrome", f"[{lang}] {name} is missing from {len(missing)} "
                               f"page(s): {', '.join(missing[:3])}")
            elif len(found) > 1:
                variants = "; ".join(
                    f"{v!r} in {len(fs)} ({', '.join(fs[:2])}…)"
                    for v, fs in sorted(found.items(), key=lambda kv: -len(kv[1])))
                fail("chrome", f"[{lang}] {name} has {len(found)} variants: {variants}")
    return f"{len(CHROME_PATTERNS)} strings x en + zh"


# ---------- stylesheet structure ----------
def uncomment(css):
    """Blank out /* */ comments, keeping every newline so lines still line up."""
    return re.sub(r"/\*.*?\*/",
                  lambda m: re.sub(r"[^\n]", " ", m.group(0)), css, flags=re.S)


def check_css():
    """Nothing else in the repo would notice style.css losing a brace.

    deadcss harvests tokens with a regex and reports its usual counts whether
    or not the file parses, while a missing } swallows every rule to the next.
    """
    text = read(CSS)
    if text.count("/*") != text.count("*/"):
        fail("css", f"{text.count('/*')} /* against {text.count('*/')} */")
    depth, line = 0, 1
    for ch in uncomment(text):
        if ch == "\n":
            line += 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                fail("css", f"line {line}: closing brace with nothing open")
                depth = 0
    if depth:
        fail("css", f"{depth} block(s) left open at end of file")
    return f"{len(text.splitlines())} lines, {text.count('{')} blocks"


# ---------- dead CSS ----------
def js_classes():
    """The class names main.js knows about, split by how it uses them.

      runtime  added, removed or toggled at runtime, so a rule for one is not
               dead even though no page carries the class
      hooks    named in a selector, so the markup carries the class for the
               script to find even where no rule matches it
    """
    js = read(JS)
    runtime = set(re.findall(r'classList\.(?:add|remove|toggle)\(\s*"([\w-]+)"', js))
    hooks = set(runtime)
    for literal in re.findall(r'"([^"\n]*)"', js):
        if "." in literal:
            hooks.update(re.findall(r"\.([a-zA-Z][\w-]*)", literal))
    return runtime, hooks


def check_deadcss():
    declared = set(re.findall(r"\.([a-zA-Z][\w-]*)", uncomment(read(CSS))))
    used = set()
    for f in PAGES:
        for m in re.finditer(r'class="([^"]*)"', read(f)):
            used.update(m.group(1).split())
    runtime, hooks = js_classes()
    for c in sorted(declared - used - runtime):
        fail("deadcss", f"style.css declares .{c} but nothing uses it")
    # The other direction. A class in the markup that no rule and no script
    # recognises is the one that gets tidied away as obviously useless:
    # .contact has no rule at all and exists only so main.js can find the
    # contact row to animate.
    for c in sorted(used - declared - hooks):
        fail("deadcss", f"markup uses .{c} but neither style.css nor main.js defines it")
    return f"{len(declared)} declared, {len(used)} used, {len(runtime)} runtime"


# ---------- unreferenced assets ----------
def check_assets():
    refs = set()
    for f in PAGES + [str(CSS)]:
        text = read(f)
        # Both root-relative (/assets/...) and the absolute og:image form.
        for m in re.finditer(r'(?:https?://[^"\'()]*?)?(/assets/[^"\')?]+)', text):
            refs.add(m.group(1).lstrip("/"))
    on_disk = {
        str(p) for p in Path("assets").rglob("*")
        if p.is_file() and not p.name.startswith(".")
    }
    # Only files git tracks are shipped; local-only originals are excluded.
    tracked = set(git("ls-files", "assets") or [])
    for a in sorted(on_disk & tracked):
        if a not in refs:
            fail("assets", f"{a} is tracked but referenced by no page")
    return f"{len(on_disk & tracked)} tracked assets, {len(refs)} referenced"


# ---------- tracked files ----------
# What the published site is allowed to consist of. Every other check scopes
# itself to pages and assets it already knows about, so a whole tree of
# unrelated files could be staged and all fifteen would still pass. .gitignore
# is the first line against that; this is the one that fails loudly.
TRACKED_DIRS = {".github", ".githooks", "assets", "tools", "zh"}
TRACKED_FILES = {".gitignore", "README.md", "robots.txt", "sitemap.xml"}


def check_tracked():
    files = git("ls-files")
    if files is None:
        fail("tracked", "git ls-files failed; cannot verify the manifest")
        return "unavailable"
    for f in files:
        top = f.split("/", 1)[0]
        if top in TRACKED_DIRS or f in TRACKED_FILES:
            continue
        # Pages live at the root next to the directories above.
        if top == f and f.endswith(".html"):
            continue
        fail("tracked", f"{f} is tracked but is not part of the published site")
    return f"{len(files)} files, {len(TRACKED_DIRS)} dirs"


# ---------- copy conventions ----------
# The English pages are US English and use straight apostrophes. The first pass
# only looked at rendered prose, which missed an alt attribute and an SVG
# <desc>; this reads the whole file so a stray cannot hide in metadata.
# Words spelled the same in both conventions (analysis, characteristic,
# realistic) are deliberately excluded by the word boundaries below.
BRITISH = (
    r"analogue|initialis\w*|labell\w*|recognis\w*|behaviour|colour|centre|defence|"
    r"organis\w*|optimis\w*|normalis\w*|generalis\w*|serialis\w*|specialis\w*|"
    r"summaris\w*|minimis\w*|maximis\w*|prioritis\w*|standardis\w*|customis\w*|"
    r"synchronis\w*|categoris\w*|utilis\w*|visualis\w*|authoris\w*|criticis\w*|"
    r"catalogue|dialogue|monologue|analyse|analysed|analyses|analysing|paralys\w*|"
    r"artefact\w*|"
    r"grey|whilst|amongst|towards|programme|judgement|practise|licence|offence|"
    r"pretence|fulfil|skilful|instalment|travell\w*|modell\w*|signall\w*|cancell\w*|"
    r"marvellous|jewellery|storey|sceptic\w*|mould|smoulder|moustache|aeroplane|"
    r"ageing|metre|litre|theatre|fibre|calibre|manoeuvre|favour|flavour|honour|"
    r"humour|labour|neighbour|rumour|vapour|endeavour|armour|learnt|spelt|dreamt|burnt"
)
PROSE_RULES = [
    (rf"\b(?:{BRITISH})\b", "British spelling; the site is US English"),
    ("\u2019", "curly apostrophe; the site uses straight"),
    (r"\bwhich compiled\b", "restrictive clause wants 'that'"),
]


def check_copy():
    for f in PAGES:
        if f.startswith("zh/"):
            continue
        raw = read(f)
        # Keep alt/aria-label/meta and SVG text; drop only code and comments,
        # where a British spelling may be someone else's identifier.
        body = re.sub(r"<(script|style|pre)\b.*?</\1>", " ", raw, flags=re.S)
        body = re.sub(r"<code\b.*?</code>", " ", body, flags=re.S)
        body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
        body = body.replace("aria-labelledby", " ")   # attribute name, not prose
        seen = set()
        for pat, why in PROSE_RULES:
            for m in re.finditer(pat, body, re.I):
                word = m.group(0).lower()
                if word in seen:
                    continue
                seen.add(word)
                fail("copy", f"{f}: {m.group(0)!r} ({why})")
    return "US English + punctuation, prose and metadata"


# ---------- social cards ----------
def check_og():
    cards = [f for f in PAGES if f not in SINGLETON]
    for f in cards:
        text = read(f)
        zh = f.startswith("zh/")
        m = re.search(r'og:image" content="([^"]+)"', text)
        if not m:
            fail("og", f"{f}: no og:image")
            continue
        card = m.group(1)
        if zh and not card.endswith("-zh.png"):
            fail("og", f"{f}: shares the English card {Path(card).name}")
        if not zh and card.endswith("-zh.png"):
            fail("og", f"{f}: points at a Chinese card {Path(card).name}")
        want = "zh_TW" if zh else "en_US"
        if f'og:locale" content="{want}"' not in text:
            fail("og", f"{f}: og:locale should be {want}")
    return f"{len(cards)} cards + locales"


# ---------- checks delegated to the sibling generators ----------
# Each one owns an artifact and already knows how to say whether it is stale;
# run_tool turns that into a verdict here rather than restating the rule.
def check_cv():
    return run_tool("cv", "cv.py", "assets/cv/rivan-wong-cv.pdf",
                    lambda l: l.strip() if "STALE" in l or "MISSING" in l else None)


def check_stamps():
    return run_tool("stamps", "bump.py", "style.css + main.js",
                    lambda l: l.split("stale:", 1)[1].strip() if "stale:" in l else None)


def check_cjk():
    return run_tool("cjk", "cjk.py", None)


def check_sitemap():
    return run_tool("sitemap", "sitemap.py", None)


def check_cards():
    return run_tool("cards", "og.py", None)


CHECKS = [
    ("structure", check_structure),
    ("links", check_links),
    ("alternates", check_alternates),
    ("parity", check_parity),
    ("chrome", check_chrome),
    ("css", check_css),
    ("deadcss", check_deadcss),
    ("assets", check_assets),
    ("tracked", check_tracked),
    ("stamps", check_stamps),
    ("cv", check_cv),
    ("og", check_og),
    ("cards", check_cards),
    ("copy", check_copy),
    ("sitemap", check_sitemap),
    ("cjk", check_cjk),
]

if __name__ == "__main__":
    names = [name for name, _ in CHECKS]
    only = sys.argv[1:] or None
    unknown = [a for a in only or () if a not in names]
    if unknown:
        sys.exit(f"check.py: no such check: {', '.join(unknown)}\n"
                 f"usage: python3 tools/check.py [{' | '.join(names)}]")
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
