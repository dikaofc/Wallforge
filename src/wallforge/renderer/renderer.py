"""Renderer base class + shared window plumbing.

Every renderer is a QWidget whose native HWND is reparented under the desktop
WorkerW (see windows/desktop.py). Subclasses implement the actual media.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from ..core.logger import setup_logger

log = setup_logger("wallforge.renderer")


class Renderer(ABC):
    def __init__(self, monitor: dict) -> None:
        self.monitor = monitor          # from windows.monitors.get_monitors()
        self.window: Optional[QWidget] = None
        self.running = False
        self.muted = False
        self.volume = 1.0

    # ---- window helpers ------------------------------------------------
    def _create_window(self) -> QWidget:
        w = QWidget()
        w.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnBottomHint
            | Qt.SubWindow
            | Qt.NoDropShadowWindowHint
        )
        r = self.monitor["monitor"]
        w.setGeometry(r[0], r[1], r[2] - r[0], r[3] - r[1])
        w.show()
        int(w.winId())                   # force native handle creation
        return w

    def attach(self) -> bool:
        from ..windows.desktop import attach_to_desktop
        if self.window is None:
            return False
        return attach_to_desktop(int(self.window.winId()))

    def resize_to_monitor(self) -> None:
        if self.window is None:
            return
        r = self.monitor["monitor"]
        self.window.setGeometry(r[0], r[1], r[2] - r[0], r[3] - r[1])

    # ---- lifecycle API -------------------------------------------------
    @abstractmethod
    def init(self, content_path: str) -> None: ...

    @abstractmethod
    def start(self) -> None: ...

    def pause(self) -> None:
        self.running = False

    def resume(self) -> None:
        self.running = True

    def set_volume(self, v: float) -> None:
        self.volume = max(0.0, min(1.0, v))

    def mute(self) -> None:
        self.muted = True

    def unmute(self) -> None:
        self.muted = False

    def handle_input(self, event) -> None:
        pass

    @abstractmethod
    def stop(self) -> None: ...

    def hwnd(self) -> Optional[int]:
        return int(self.window.winId()) if self.window else None
