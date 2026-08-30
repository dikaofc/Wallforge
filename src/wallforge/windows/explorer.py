"""Watch the desktop WorkerW window and re-attach when explorer restarts.

If explorer.exe crashes/restarts, the WorkerW we attached to is destroyed and
our wallpaper window becomes orphaned (desktop goes blank/black). We poll the
worker HWND periodically and signal a re-attach when it changes or disappears.
"""
from __future__ import annotations

import ctypes

from PySide6.QtCore import QTimer

from ..core.events import bus
from ..core.logger import setup_logger
from .desktop import find_desktop_worker_window

user32 = ctypes.windll.user32
log = setup_logger("wallforge.explorer")


class ExplorerWatcher:
    def __init__(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self._check)
        self.last_worker = None

    def start(self, interval_ms: int = 2000) -> None:
        self.last_worker = find_desktop_worker_window()
        self.timer.start(interval_ms)
        log.debug("explorer watcher started, worker=%s", self.last_worker)

    def _check(self) -> None:
        cur = find_desktop_worker_window()
        if cur and cur != self.last_worker:
            log.info("desktop worker changed %s -> %s, re-attach",
                     self.last_worker, cur)
            self.last_worker = cur
            bus.monitor_changed.emit()
        elif cur == 0 and self.last_worker:
            # Worker not found yet (explorer mid-restart); wait.
            self.last_worker = None
