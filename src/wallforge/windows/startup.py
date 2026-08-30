"""Register Wallforge to run at Windows startup via the Run registry key."""
from __future__ import annotations

import winreg

from ..core.logger import setup_logger

log = setup_logger("wallforge.startup")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_KEY = "Wallforge"


def set_startup(enabled: bool, exe_path: str, mode: str = "minimized") -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as key:
            if enabled:
                cmd = f'"{exe_path}" --{mode}'
                winreg.SetValueEx(key, APP_KEY, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_KEY)
                except FileNotFoundError:
                    pass
        log.info("startup %s", "enabled" if enabled else "disabled")
        return True
    except Exception as exc:
        log.error("startup toggle failed: %s", exc)
        return False


def is_startup_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_KEY)
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
