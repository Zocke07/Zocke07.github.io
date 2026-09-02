#!/usr/bin/env python3
"""git diff, with the ?v=<hash> stamp churn filtered out.

    python3 tools/diff.py             # git diff
    python3 tools/diff.py --stat      # any git diff args pass through
    python3 tools/diff.py HEAD~3

Every page carries a query-string hash for style.css and main.js (see
tools/bump.py), so any commit that touches either one restamps all 21 pages.
`git diff -I<regex>` drops a hunk only when every line in it matches the
regex, which is exactly the shape of a stamp-only change: one line, nothing
else. This is that flag with the regex pinned, so the pages with a real edit
still show in full and the ones that only got restamped disappear instead of
padding out the diff.
"""

import subprocess
import sys

STAMP = r"\?v=[0-9a-f]{8}"


def main(argv):
    cmd = ["git", "diff", f"-I{STAMP}", *argv]
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
