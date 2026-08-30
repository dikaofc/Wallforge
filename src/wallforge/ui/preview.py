"""Wallpaper preview dialog with Apply / Favorite actions."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QDialog, QLabel, QPushButton, QHBoxLayout,
                               QVBoxLayout, QMessageBox)

from ..database.database import Database
from ..database.models import Wallpaper


class PreviewDialog(QDialog):
    def __init__(self, wallpaper: Wallpaper, db: Database,
                 on_apply, on_favorite, manager=None) -> None:
        super().__init__()
        self.setWindowTitle(wallpaper.title)
        self.resize(720, 480)
        self.wallpaper = wallpaper
        self.db = db
        self.on_apply = on_apply
        self.on_favorite = on_favorite
        self.manager = manager

        layout = QVBoxLayout(self)
        self.preview = QLabel("No preview available")
        self.preview.setMinimumHeight(320)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet(
            "background:#0c0e14;border:1px solid #2a2d36;border-radius:8px;"
            "color:#9aa;font-size:13px;")
        # Prefer a dedicated preview image, else fall back to the thumbnail.
        img = None
        for cand in (wallpaper.preview, wallpaper.thumbnail):
            if cand and Path(cand).exists():
                img = cand
                break
        if img:
            pix = QPixmap(img)
            self.preview.setPixmap(pix.scaled(
                680, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Last resort: try the wallpaper's own image content.
            try:
                from ..wallpaper.loader import load
                _, content = load(Path(wallpaper.path))
                if content.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".bmp"):
                    pix = QPixmap(str(content))
                    self.preview.setPixmap(pix.scaled(
                        680, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception:
                pass
        layout.addWidget(self.preview)

        info = QLabel(f"<b>{wallpaper.title}</b><br>by {wallpaper.author or 'Unknown'}"
                      f"<br><span style='color:#9aa'>type: {wallpaper.type}</span>")
        info.setStyleSheet("color:#e6e6e6;font-size:13px;padding:6px;")
        layout.addWidget(info)

        self.status = QLabel("")
        self.status.setStyleSheet("color:#7fd17f;font-size:12px;")
        layout.addWidget(self.status)

        btns = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet("background:#2d6cdf;color:#fff;padding:9px 22px;"
                                "font-weight:bold;border-radius:4px;")
        fav_btn = QPushButton("Favorite ☆" if not wallpaper.favorite else "Favorite ★")
        fav_btn.setStyleSheet("padding:9px 16px;border-radius:4px;")
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding:9px 16px;border-radius:4px;")
        apply_btn.clicked.connect(self._apply)
        fav_btn.clicked.connect(lambda: self._toggle_fav(fav_btn))
        close_btn.clicked.connect(self.reject)
        btns.addWidget(apply_btn)
        btns.addWidget(fav_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        layout.addLayout(btns)

    def _apply(self) -> None:
        try:
            self.on_apply(self.wallpaper.id)
            self.status.setText("✓ Wallpaper applied")
            self.accept()
        except Exception as exc:
            self.status.setText(f"✗ Failed: {exc}")
            self.status.setStyleSheet("color:#ff6b6b;font-size:12px;")

    def _toggle_fav(self, btn: QPushButton) -> None:
        new = 0 if self.wallpaper.favorite else 1
        self.db.set_favorite(self.wallpaper.id, bool(new))
        self.wallpaper.favorite = new
        btn.setText("Favorite ★" if new else "Favorite ☆")
        self.on_favorite()
