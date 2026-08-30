"""Standalone updater stub.

When Wallforge downloads a new version it spawns this (or copies itself with
--apply-update). The updater waits for the main process to exit, extracts the
zip over the install dir, then relaunches Wallforge.exe.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import zipfile


def apply_update(zip_path: str) -> int:
    # Wait for the running Wallforge.exe to release its files.
    target_dir = os.path.dirname(sys.executable)
    for _ in range(30):
        try:
            if not _exe_running():
                break
        except Exception:
            pass
        time.sleep(1)
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(target_dir)
        # Relaunch.
        subprocess.Popen([os.path.join(target_dir, "Wallforge.exe")])
        return 0
    except Exception as exc:
        print("update failed:", exc)
        return 1


def _exe_running() -> bool:
    import psutil
    name = os.path.basename(sys.executable).lower()
    for p in psutil.process_iter(["name"]):
        if p.info.get("name", "").lower() == name:
            return True
    return False


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--apply-update":
        raise SystemExit(apply_update(sys.argv[2]))
