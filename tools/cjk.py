#!/usr/bin/env python3
"""Find and remove line breaks that render as a stray space in CJK text.

    python3 tools/cjk.py            # join the offending lines
    python3 tools/cjk.py --check    # exit 1 if any remain

HTML collapses a newline in the source into a space. Between two English words
that is exactly right, which is why the English pages wrap freely. Between two
Chinese characters there is no space to represent, and the browser inserts one
anyway: CSS Text's rule for dropping the break applies only in cases Chrome
does not apply here, verified by rendering both forms and comparing.

So a Chinese paragraph cannot be soft-wrapped in the source the way an English
one can. It goes on one line, however long, and this file is what stops the
next edit from quietly reintroducing the wrap.

Breaks between a Chinese character and a Latin one are left alone: that space
is wanted, and the pages already write it by hand.
"""

import glob
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# CJK ideographs, the fullwidth punctuation that goes with them, and kana.
CJK = re.compile(r"[⺀-〿぀-ヿ㐀-䶿一-鿿"
                 r"豈-﫿︰-﹏＀-￯]")


# Inside <pre> a newline is content, not layout: joining two lines there would
# silently reflow a code listing. Nothing in the site trips this today, and
# that is an accident of the snippets being Latin, not a property worth
# relying on.
PRE = re.compile(r"<pre\b.*?</pre>", re.S)


def protected(text):
    """Line numbers that fall inside a <pre> block."""
    out = set()
    for m in PRE.finditer(text):
        first = text.count("\n", 0, m.start())
        last = first + m.group(0).count("\n")
        out.update(range(first, last + 1))
    return out


def joinable(a, b):
    a, b = a.rstrip(), b.lstrip()
    return bool(a and b and CJK.match(a[-1]) and CJK.match(b[0]))


def offenders(text):
    """Indexes i where the break after line i renders a space it should not."""
    lines = text.split("\n")
    keep = protected(text)
    return [i for i in range(len(lines) - 1)
            if i not in keep and i + 1 not in keep
            and joinable(lines[i], lines[i + 1])]


def join(text):
    changed = 0
    while True:
        hits = offenders(text)
        if not hits:
            return text, changed
        # One at a time, recomputing: a join shifts every later line number.
        i = hits[0]
        lines = text.split("\n")
        lines[i] = lines[i].rstrip() + lines[i + 1].lstrip()
        del lines[i + 1]
        text = "\n".join(lines)
        changed += 1


def main(argv):
    check = "--check" in argv
    files = sorted(glob.glob("zh/*.html")) + ["404.html"]
    total = 0
    for f in files:
        p = ROOT / f
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        if check:
            n = len(offenders(text))
            if n:
                print(f"{f}: {n} line breaks render a stray space", file=sys.stderr)
            total += n
        else:
            new, n = join(text)
            if n:
                p.write_text(new, encoding="utf-8")
                print(f"  {f}: joined {n}")
            total += n
    if check:
        if total:
            print("run python3 tools/cjk.py", file=sys.stderr)
            return 1
        print(f"{len(files)} Chinese pages, no stray spaces")
        return 0
    print(f"joined {total} line breaks")
    return 0


if __name__ == "__main__":
    import os
    os.chdir(ROOT)
    sys.exit(main(sys.argv[1:]))
