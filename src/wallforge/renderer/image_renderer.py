"""Image wallpaper renderer: a QLabel drawing a scaled, cached pixmap.

Very low overhead — one widget, no decode loop. Re-scales on resize.
"""
from __future__ import annotations

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

from .renderer import Renderer


class ImageRenderer(Renderer):
    def init(self, content_path: str) -> None:
        self.content_path = content_path
        self.window = self._create_window()
        self.label = QLabel(self.window)
        self.label.setScaledContents(True)
        self.label.setStyleSheet("background:black;")
        self._pixmap = QPixmap(content_path)
        if self._pixmap.isNull():
            from PySide6.QtCore import Qt
            self.label.setText("image failed to load")
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.label.setPixmap(self._pixmap)
        self.resize_to_monitor()

    def resize_to_monitor(self) -> None:
        super().resize_to_monitor()
        if self.window:
            self.label.setGeometry(0, 0, self.window.width(), self.window.height())

    def start(self) -> None:
        self.running = True
        if self.window:
            self.window.show()

    def pause(self) -> None:
        self.running = False
        if self.window:
            self.window.hide()

    def resume(self) -> None:
        self.running = True
        if self.window:
            self.window.show()

    def stop(self) -> None:
        self.running = False
        if self.window:
            self.window.close()
            self.window = None
