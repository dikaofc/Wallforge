"""Home page: quick stats + recently added wallpapers."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QVBoxLayout, QWidget)

from ..database.database import Database
from .wallpaper_grid import WallpaperGrid


class HomePage(QWidget):
    def __init__(self, db: Database, manager, open_library) -> None:
        super().__init__()
        self.db = db
        self.manager = manager
        layout = QVBoxLayout(self)
        title = QLabel("WALLFORGE")
        title.setStyleSheet("font-size:28px;font-weight:bold;color:#e6e6e6;")
        layout.addWidget(title)
        self.stats = QLabel("")
        self.stats.setStyleSheet("color:#9aa;")
        layout.addWidget(self.stats)
        layout.addWidget(QLabel("Recently added"))
        self.grid = WallpaperGrid()
        self.grid.wallpaperClicked.connect(
            lambda wid: self.manager.apply(wid))
        layout.addWidget(self.grid, 1)
        self._refresh()

    def _refresh(self) -> None:
        allw = self.db.list_wallpapers()
        self.stats.setText(
            f"{len(allw)} wallpapers · "
            f"{len(self.db.list_collections())} collections")
        self.grid.set_wallpapers(allw[:8])
