"""Scrollable grid of wallpaper thumbnails."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QGridLayout, QLabel, QScrollArea, QVBoxLayout,
                               QWidget)

from ..database.models import Wallpaper


class WallpaperGrid(QWidget):
    wallpaperClicked = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(12)
        self.scroll.setWidget(self.container)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)
        self.cols = 4

    def set_wallpapers(self, wallpapers: list[Wallpaper]) -> None:
        # Clear existing.
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        for i, w in enumerate(wallpapers):
            cell = self._cell(w)
            r, c = divmod(i, self.cols)
            self.grid.addWidget(cell, r, c)

    def _cell(self, w: Wallpaper) -> QWidget:
        cell = QWidget()
        vbox = QVBoxLayout(cell)
        vbox.setContentsMargins(0, 0, 0, 0)
        thumb = QLabel()
        thumb.setFixedSize(180, 101)
        thumb.setStyleSheet("background:#000;border-radius:4px;")
        if w.thumbnail and Path(w.thumbnail).exists():
            thumb.setPixmap(QPixmap(w.thumbnail).scaled(
                180, 101, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            thumb.setText(w.type)
            thumb.setAlignment(Qt.AlignCenter)
        label = QLabel(w.title)
        label.setStyleSheet("color:#ccc;font-size:11px;")
        label.setFixedWidth(180)
        label.setWordWrap(True)
        cell.mousePressEvent = lambda e, wid=w.id: self.wallpaperClicked.emit(wid)
        vbox.addWidget(thumb)
        vbox.addWidget(label)
        return cell
