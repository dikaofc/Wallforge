"""Wallpaper preview dialog with Apply / Favorite actions."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QDialog, QLabel, QPushButton, QHBoxLayout,
                               QVBoxLayout)

from ..database.database import Database
from ..database.models import Wallpaper


class PreviewDialog(QDialog):
    applied = None  # set by caller via callback

    def __init__(self, wallpaper: Wallpaper, db: Database,
                 on_apply, on_favorite) -> None:
        super().__init__()
        self.setWindowTitle(wallpaper.title)
        self.setMinimumSize(640, 420)
        self.wallpaper = wallpaper
        self.db = db
        self.on_apply = on_apply
        self.on_favorite = on_favorite

        layout = QVBoxLayout(self)
        self.preview = QLabel("Preview")
        self.preview.setMinimumHeight(300)
        self.preview.setStyleSheet("background:#000;border-radius:6px;")
        if wallpaper.preview and __import__("pathlib").Path(wallpaper.preview).exists():
            self.preview.setPixmap(QPixmap(wallpaper.preview).scaledToWidth(620))
        layout.addWidget(self.preview)

        info = QLabel(f"{wallpaper.title}\nby {wallpaper.author or 'Unknown'}")
        info.setStyleSheet("color:#ddd;")
        layout.addWidget(info)

        btns = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet("background:#2d6cdf;color:#fff;padding:8px 16px;")
        fav_btn = QPushButton("Favorite ☆")
        close_btn = QPushButton("Close")
        apply_btn.clicked.connect(lambda: (self.on_apply(wallpaper.id), self.accept()))
        fav_btn.clicked.connect(lambda: self._toggle_fav(fav_btn))
        close_btn.clicked.connect(self.reject)
        btns.addWidget(apply_btn)
        btns.addWidget(fav_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        layout.addLayout(btns)

    def _toggle_fav(self, btn: QPushButton) -> None:
        new = 0 if self.wallpaper.favorite else 1
        self.db.set_favorite(self.wallpaper.id, bool(new))
        self.wallpaper.favorite = new
        btn.setText("Favorite ★" if new else "Favorite ☆")
        self.on_favorite()
