"""WebView2 runtime availability + bootstrap for web wallpapers.

Web wallpapers need the WebView2 (Edge) runtime. We check the registry;
if absent, we can download Microsoft's evergreen bootstrapper. The runtime is
large, so we don't bundle it — we fetch on demand (or the installer does).
"""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys

from ..core.logger import setup_logger

log = setup_logger("wallforge.webview2")

BOOTSTRAPPER_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
REG_PATH = r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"


def is_available() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH) as k:
            winreg.QueryValueEx(k, "pv")
        return True
    except Exception:
        # Also accept a locally bundled fixed runtime.
        local = os.path.join(os.path.dirname(sys.executable), "webview2")
        return os.path.isdir(local)


def ensure_runtime() -> bool:
    """Return True if WebView2 is ready; otherwise try to install it."""
    if is_available():
        return True
    log.warning("WebView2 runtime missing; attempting bootstrap install")
    try:
        import tempfile
        path = os.path.join(tempfile.gettempdir(), "webview2_bootstrapper.exe")
        import urllib.request
        urllib.request.urlretrieve(BOOTSTRAPPER_URL, path)
        subprocess.run([path, "/silent", "/install"], check=False)
        return is_available()
    except Exception as exc:
        log.error("WebView2 bootstrap failed: %s", exc)
        return False
