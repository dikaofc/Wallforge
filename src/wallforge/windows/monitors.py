"""Enumerate physical monitors via EnumDisplayMonitors.

Returns a list of dicts with the device name, primary flag, full monitor rect
and work-area rect (in virtual-screen coordinates). Used to place one renderer
window per monitor.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes, Structure, WINFUNCTYPE

import logging

user32 = ctypes.windll.user32
logger = logging.getLogger("wallforge.monitors")


class RECT(Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFOEX(Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


def get_monitors() -> list[dict]:
    monitors: list[dict] = []

    @WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE, wintypes.HDC,
                 ctypes.POINTER(RECT), wintypes.LPARAM)
    def cb(hmon, _hdc, _lprect, _lparam):
        info = MONITORINFOEX()
        info.cbSize = ctypes.sizeof(MONITORINFOEX)
        user32.GetMonitorInfoW(hmon, ctypes.byref(info))
        monitors.append({
            "handle": int(hmon),
            "name": info.szDevice,
            "primary": bool(info.dwFlags & 1),
            "monitor": (info.rcMonitor.left, info.rcMonitor.top,
                        info.rcMonitor.right, info.rcMonitor.bottom),
            "work": (info.rcWork.left, info.rcWork.top,
                     info.rcWork.right, info.rcWork.bottom),
        })
        return True

    user32.EnumDisplayMonitors(0, None, cb, 0)
    logger.debug("found %d monitor(s)", len(monitors))
    return monitors


if __name__ == "__main__":
    for m in get_monitors():
        print(m)
