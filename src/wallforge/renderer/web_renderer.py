"""Web wallpaper renderer using pywebview with the WebView2 (Edge) backend.

We create a pywebview window and reparent its native HWND to the desktop
WorkerW layer. pywebview runs its own GUI thread; we bridge callbacks via
Qt signals so the main app can control it.
"""
from __future__ import annotations

from ..core.logger import setup_logger
from ..windows.webview2 import ensure_runtime
from .renderer import Renderer

log = setup_logger("wallforge.web")


class WebRenderer(Renderer):
    def __init__(self, monitor: dict) -> None:
        super().__init__(monitor)
        self.webview_window = None
        self._thread = None

    def init(self, content_path: str) -> None:
        self.content_path = content_path
        self.window = self._create_window()
        # Reparent immediately so the (initially hidden) webview sits behind icons.
        self.attach()
        # Make sure the WebView2 runtime is present before we spin up pywebview.
        ensure_runtime()
        # pywebview requires running on the Python main thread, so schedule it
        # via a Qt timer (runs on the Qt/main thread) rather than a raw thread.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._start_webview)

    def _start_webview(self) -> None:
        import webview
        r = self.monitor["monitor"]
        try:
            self.webview_window = webview.create_window(
                "wallforge-web",
                url="file://" + str(self.content_path),
                width=r[2] - r[0], height=r[3] - r[1],
                background_color="#000000",
            )
            # Reparent the webview's native window under our desktop window.
            hwnd = getattr(self.webview_window, "_native_window", None)
            if hwnd and self.window:
                import ctypes
                user32 = ctypes.windll.user32
                user32.SetParent(int(hwnd), int(self.window.winId()))
            webview.start(gui="edgechromium")
        except Exception as exc:
            log.error("webview start failed: %s", exc)

    def start(self) -> None:
        # WebView startup is scheduled via QTimer in init(); nothing to do here
        # except mark the renderer as running.
        self.running = True

    def pause(self) -> None:
        self.running = False
        if self.webview_window:
            try:
                self.webview_window.evaluate_js(
                    "document.visibilityState && document.dispatchEvent("
                    "new Event('wallforge-pause'))")
            except Exception:
                pass

    def resume(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False
        if self.webview_window:
            try:
                self.webview_window.destroy()
            except Exception:
                pass
        if self.window:
            self.window.close()
            self.window = None
