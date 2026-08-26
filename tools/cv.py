#!/usr/bin/env python3
"""Copy the built CV into the site, and say when the copy has gone stale.

    python3 tools/cv.py            # refresh the copy
    python3 tools/cv.py --check    # report only, non-zero if stale

CV/ is a separate git repository with its own remote, so git treats it as a
submodule boundary and cannot track files inside it as ordinary files. The site
therefore carries a copy rather than a reference, and a copy can drift from what
it was copied from. This is the thing that notices.

The source is a local build artefact, so it is absent on a fresh clone and in
CI. That is not a failure: with no source to compare against, the copy in the
repo is taken as authoritative and the check passes.
"""

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "CV/build/cv.pdf"
TARGET = ROOT / "assets/cv/rivan-wong-cv.pdf"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(check_only=False):
    if not SOURCE.exists():
        print(f"  {SOURCE.relative_to(ROOT)} not present; keeping the copy in the repo")
        return 0
    if not TARGET.exists():
        if check_only:
            print(f"  MISSING {TARGET.relative_to(ROOT)}")
            return 1
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE, TARGET)
        print(f"  created {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size:,} bytes)")
        return 0

    if digest(SOURCE) == digest(TARGET):
        print(f"  {TARGET.relative_to(ROOT)} matches {SOURCE.relative_to(ROOT)}")
        return 0

    if check_only:
        print(f"  STALE {TARGET.relative_to(ROOT)} differs from {SOURCE.relative_to(ROOT)}")
        print("        run: python3 tools/cv.py")
        return 1

    shutil.copy2(SOURCE, TARGET)
    print(f"  refreshed {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
