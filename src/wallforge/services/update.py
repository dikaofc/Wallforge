"""Auto-updater: check version.json, download, verify SHA256, apply.

The actual file replacement must be done by a separate updater process
because the running .exe cannot overwrite itself. This module downloads the
new zip and spawns `updater.exe` (or a copy of ourselves with `--apply-update`)
then exits.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

from ..core.config import DATA_DIR
from ..core.logger import setup_logger

log = setup_logger("wallforge.update")


def current_version() -> str:
    try:
        from .. import __version__
        return __version__
    except Exception:
        return "0.0.0"


def check_for_update(url: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        data["_url"] = url
        if _is_newer(data.get("version", "0"), current_version()):
            return data
        return None
    except Exception as exc:
        log.warning("update check failed: %s", exc)
        return None


def check_and_apply(url: str, on_status=None) -> bool:
    """Convenience: check, report status, apply if newer. Returns applied?"""
    if on_status:
        on_status("Checking…")
    info = check_for_update(url)
    if not info:
        if on_status:
            on_status("Up to date.")
        return False
    if on_status:
        on_status(f"Update available: {info.get('version')}")
    ok = apply_update(info)
    if ok and on_status:
        on_status("Updating — restarting…")
    return ok


def _is_newer(remote: str, local: str) -> bool:
    def parse(v):
        return [int(x) for x in v.split(".") if x.isdigit()]
    try:
        return parse(remote) > parse(local)
    except Exception:
        return False


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: str) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as exc:
        log.error("download failed: %s", exc)
        return False


def apply_update(version_json: dict) -> bool:
    """Download + verify, then spawn updater and exit the app."""
    tmp = os.path.join(tempfile.gettempdir(), f"wallforge_update_{version_json['version']}.zip")
    if not download(version_json["url"], tmp):
        return False
    expected = version_json.get("sha256")
    if expected and _sha256(tmp) != expected:
        log.error("update checksum mismatch; aborting")
        return False
    updater = os.path.join(os.path.dirname(sys.executable), "updater.exe")
    if not os.path.exists(updater):
        # Fallback: let this exe apply the update on next launch.
        updater = sys.executable
    try:
        subprocess.Popen([updater, "--apply-update", tmp])
        log.info("spawned updater; exiting for update")
        return True
    except Exception as exc:
        log.error("spawn updater failed: %s", exc)
        return False
