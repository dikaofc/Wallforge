"""Playlist playback controller.

Cycles through a list of wallpaper ids on a timer, advancing per the active
playlist's order. Uses the wallpaper manager to swap the active wallpaper.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer

from ..core.logger import setup_logger

log = setup_logger("wallforge.playlist")


class PlaylistPlayer:
    def __init__(self, manager, db) -> None:
        self.manager = manager
        self.db = db
        self.timer = QTimer()
        self.timer.timeout.connect(self._advance)
        self.items: list[int] = []
        self.index = 0
        self.playlist_id: int | None = None

    def load(self, playlist_id: int, interval_ms: int = 30_000) -> None:
        self.playlist_id = playlist_id
        self.items = self.db.get_playlist_items(playlist_id)
        self.index = 0
        if self.items:
            self.manager.apply(self.items[0])
        self.timer.start(interval_ms)
        log.info("playlist %s loaded with %d items", playlist_id, len(self.items))

    def _advance(self) -> None:
        if not self.items:
            return
        self.index = (self.index + 1) % len(self.items)
        self.manager.apply(self.items[self.index])
        log.debug("playlist advanced to %d", self.items[self.index])

    def stop(self) -> None:
        self.timer.stop()
        self.playlist_id = None
        self.items = []
