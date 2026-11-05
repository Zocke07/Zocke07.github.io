#!/usr/bin/env python3
"""Local preview that resolves URLs the way GitHub Pages does.

The site links to pages without the .html suffix (/case-study-lmad), which
GitHub Pages resolves for free. `python3 -m http.server` does not, so it would
404 on every internal link. This adds that rule, and answers a URL that truly is
bad with 404.html, as GitHub Pages does.

    python3 tools/serve.py            # http://127.0.0.1:8000
    python3 tools/serve.py 8080

Binds to 127.0.0.1, so the preview stays off the local network.
"""

import http.server
import os
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        local = Path(super().translate_path(path))
        # A bare name with no extension: prefer name.html, then name/index.html,
        # which is exactly the order GitHub Pages tries.
        if not local.exists() and not local.suffix:
            for candidate in (local.with_suffix(".html"), local / "index.html"):
                if candidate.is_file():
                    return str(candidate)
        return str(local)

    def send_error(self, code, message=None, explain=None) -> None:
        # A bad URL gets 404.html, the same page GitHub Pages answers with.
        page = ROOT / "404.html"
        if code != 404 or not page.is_file():
            super().send_error(code, message, explain)
            return
        body = page.read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def end_headers(self) -> None:
        # Never cache during preview, so an edit shows up on reload.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("  %s\n" % (fmt % args))


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
os.chdir(ROOT)
socketserver.TCPServer.allow_reuse_address = True
# Threaded, because one clip streaming to the browser would otherwise hold up
# every other request on the page until it finished.
with socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler) as httpd:
    print(f"serving {ROOT} at http://127.0.0.1:{port}  (ctrl-c to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
