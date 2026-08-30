"""Tiny local HTTP server that serves a version.json + a dummy update zip.

Useful for testing the auto-updater end-to-end without a remote host.
Run:  python -m src.wallforge.services.update_server
Then point the app's update URL at http://127.0.0.1:8765/version.json
"""
from __future__ import annotations

import hashlib
import http.server
import socketserver
import threading
import zipfile
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
ROOT = Path(__file__).resolve().parent.parent.parent.parent  # project root
DIST = ROOT / "dist" / "Wallforge"


def _make_update_zip() -> tuple[str, str]:
    """Create a fake update zip (just the exe) and return (path, sha256)."""
    out = ROOT / "installer" / "Wallforge-Update.zip"
    exe = DIST / "Wallforge.exe"
    if exe.exists():
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(exe, "Wallforge.exe")
    sha = hashlib.sha256()
    if out.exists():
        sha.update(out.read_bytes())
    return str(out), sha.hexdigest()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/version.json"):
            _, sha = _make_update_zip()
            import json
            body = json.dumps({
                "version": "0.1.1",
                "url": f"http://{HOST}:{PORT}/update.zip",
                "sha256": sha,
                "notes": "Test update served locally.",
                "mandatory": False,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/update.zip"):
            z = ROOT / "installer" / "Wallforge-Update.zip"
            if z.exists():
                data = z.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def log_message(self, *a):
        pass


def run() -> None:
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        print(f"update test server on http://{HOST}:{PORT}/version.json")
        httpd.serve_forever()


if __name__ == "__main__":
    run()
