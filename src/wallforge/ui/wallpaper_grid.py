"""Scrollable grid of wallpaper thumbnails (click = apply, right-click = favorite)."""
from __future__ import annotations

import colorsys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (QGridLayout, QLabel, QScrollArea, QVBoxLayout,
                               QWidget)

from ..database.models import Wallpaper


class WallpaperGrid(QWidget):
    wallpaperClicked = Signal(int)        # left click -> apply
    wallpaperRightClicked = Signal(int)   # right click -> favorite

    def __init__(self) -> None:
        super().__init__()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background:#12141a;border:none;")
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(12)
        self.scroll.setWidget(self.container)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)
        self.cols = 4

    def set_wallpapers(self, wallpapers: list[Wallpaper]) -> None:
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        if not wallpapers:
            empty = QLabel("No wallpapers yet.\nClick '+ Add wallpaper' to add one.")
            empty.setStyleSheet("color:#9aa;font-size:14px;padding:30px;")
            empty.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(empty, 0, 0)
            return
        for i, w in enumerate(wallpapers):
            cell = self._cell(w)
            r, c = divmod(i, self.cols)
            self.grid.addWidget(cell, r, c)

    def _cell(self, w: Wallpaper) -> QWidget:
        cell = QWidget()
        cell.setFixedSize(190, 132)
        vbox = QVBoxLayout(cell)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)
        thumb = QLabel()
        thumb.setFixedSize(190, 107)
        thumb.setStyleSheet("background:#000;border-radius:4px;")
        if w.thumbnail and Path(w.thumbnail).exists():
            thumb.setPixmap(QPixmap(w.thumbnail).scaled(
                190, 107, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            thumb.setPixmap(self._placeholder(w.title))
        thumb.setScaledContents(True)
        label = QLabel(w.title)
        label.setStyleSheet("color:#e6e6e6;font-size:11px;")
        label.setFixedWidth(190)
        label.setWordWrap(True)
        cell.setToolTip(f"{w.title}\nby {w.author or 'Unknown'}\ntype: {w.type}"
                        f"{'  ★' if w.favorite else ''}")

        def _press(e):
            if e.button() == Qt.RightButton:
                self.wallpaperRightClicked.emit(w.id)
            else:
                self.wallpaperClicked.emit(w.id)
        cell.mousePressEvent = _press
        vbox.addWidget(thumb)
        vbox.addWidget(label)
        return cell

    @staticmethod
    def _placeholder(title: str) -> QPixmap:
        hue = (hash(title) % 360) / 360.0
        w, h = 190, 107
        img = QImage(w, h, QImage.Format.Format_RGB32)
        p = QPainter(img)
        for y in range(h):
            t = y / h
            r1, g1, b1 = colorsys.hsv_to_rgb(hue, 0.55, 0.30)
            r2, g2, b2 = colorsys.hsv_to_rgb((hue + 0.11) % 1.0, 0.70, 0.55)
            col = QColor(int((r1 * (1 - t) + r2 * t) * 255),
                         int((g1 * (1 - t) + g2 * t) * 255),
                         int((b1 * (1 - t) + b2 * t) * 255))
            p.fillRect(0, y, w, 1, col)
        p.end()
        return QPixmap.fromImage(img)
