"""Detect fullscreen / game windows so we can pause wallpapers.

A window counts as "fullscreen/game" when its rect covers an entire physical
monitor AND it is not our own app, not the desktop shell, and not a
cloaked/tool window. We also flag maximized borderless windows (WS_POPUP with
a monitor-sized rect).
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

from ..core.logger import setup_logger

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi

DWMWA_CLOAKED = 14

log = setup_logger("wallforge.fullscreen")


def _get_window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    r = wt.RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(r)):
        return (r.left, r.top, r.right, r.bottom)
    return None


def _is_cloaked(hwnd: int) -> bool:
    cloaked = ctypes.c_int32(0)
    res = dwmapi.DwmGetWindowAttribute(
        hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
    return res == 0 and cloaked.value != 0


def is_fullscreen(our_hwnds: set[int] = set()) -> bool:
    fg = user32.GetForegroundWindow()
    if not fg or fg in our_hwnds:
        return False
    rect = _get_window_rect(fg)
    if not rect:
        return False
    left, top, right, bottom = rect
    w, h = right - left, bottom - top
    if w <= 0 or h <= 0:
        return False

    mon = user32.MonitorFromWindow(fg, 2)  # MONITOR_DEFAULTTONEAREST
    if not mon:
        return False
    mi = wt.RECT()
    # MONITORINFO structure (cbSize, rcMonitor, rcWork, dwFlags)
    class MONITORINFO(ctypes.Structure):
        _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT),
                    ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    if not user32.GetMonitorInfoW(mon, ctypes.byref(info)):
        return False
    m = info.rcMonitor
    # Cover the whole monitor (allow a few px tolerance).
    tol = 4
    covers = (abs(left - m.left) <= tol and abs(top - m.top) <= tol
              and abs(right - m.right) <= tol and abs(bottom - m.bottom) <= tol)
    if not covers:
        return False
    if _is_cloaked(fg):
        return False
    # Reject the desktop shell windows.
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(fg, buf, 256)
    if buf.value in ("Progman", "WorkerW", "Shell_TrayWnd"):
        return False
    return True


if __name__ == "__main__":
    print("fullscreen now:", is_fullscreen())
