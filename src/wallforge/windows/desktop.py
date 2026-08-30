"""Desktop integration: attach render windows BEHIND desktop icons.

Proven technique (used by Wallpaper Engine-class apps):
  1. Send magic message 0x052C to Progman -> spawns a WorkerW window.
  2. Find the WorkerW that does NOT contain SHELLDLL_DefView (the one that
     sits behind the desktop icon listview).
  3. SetParent(render_hwnd, workerW) with toolwindow/noactivate styles and
     HWND_BOTTOM z-order.

Also handles saving/restoring the static wallpaper so the desktop never ends
up blank on exit or crash.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes, WINFUNCTYPE

import logging

user32 = ctypes.windll.user32

# Window style/flag constants
GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_CHILD = 0x40000000
WS_VISIBLE = 0x10000000
WS_POPUP = 0x80000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
HWND_BOTTOM = 1
SWP_NOACTIVATE = 0x0010
SWP_NOZORDER = 0x0004
SWP_NOOWNERZORDER = 0x0200

SPI_GETDESKWALLPAPER = 0x0073
SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02

logger = logging.getLogger("wallforge.desktop")


def _find_progman() -> int:
    return user32.FindWindowW("Progman", None)


def _spawn_workerw() -> None:
    progman = _find_progman()
    if progman:
        user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, None)


def find_desktop_worker_window() -> int:
    """Return the WorkerW window that sits behind the desktop icons."""
    _spawn_workerw()
    targets: list[int] = []

    @WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_cb(hwnd, _lparam):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        if buf.value == "WorkerW":
            # The WorkerW we want does NOT parent SHELLDLL_DefView.
            defview = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
            if not defview:
                targets.append(hwnd)
        return True

    user32.EnumWindows(enum_cb, 0)
    if targets:
        return targets[0]
    # Fallback: attach straight to Progman.
    return _find_progman()


def attach_to_desktop(hwnd: int) -> bool:
    """Reparent a render window under the desktop layer."""
    try:
        worker = find_desktop_worker_window()
        if not worker:
            return False
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        style = (style & ~WS_POPUP) | WS_CHILD | WS_VISIBLE
        user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex = ex | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
        user32.SetParent(hwnd, worker)
        user32.SetWindowPos(
            hwnd, HWND_BOTTOM, 0, 0, 0, 0,
            SWP_NOACTIVATE | SWP_NOZORDER | SWP_NOOWNERZORDER,
        )
        logger.debug("attached hwnd=%s to worker=%s", hwnd, worker)
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("attach_to_desktop failed: %s", exc)
        return False


def get_original_wallpaper() -> str:
    buf = ctypes.create_unicode_buffer(260)
    user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 260, buf, 0)
    return buf.value


def restore_wallpaper(path: str) -> None:
    """Restore the static desktop wallpaper (call on exit/crash)."""
    try:
        user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        logger.info("restored wallpaper: %s", path)
    except Exception as exc:  # pragma: no cover
        logger.exception("restore_wallpaper failed: %s", exc)
