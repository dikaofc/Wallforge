"""Left navigation sidebar (minimal: Library + Settings)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QLabel, QWidget


class Sidebar(QWidget):
    pageSelected = Signal(str)

    PAGES = [
        ("library", "Wallpapers"),
        ("settings", "Settings"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(
            "background:#0c0e14;border-right:1px solid #23262f;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)
        self.list = QListWidget()
        self.list.setStyleSheet("""
            QListWidget { background:transparent; border:none;
                          font-size:14px; color:#e6e6e6; }
            QListWidget::item { padding:11px 14px; }
            QListWidget::item:selected { background:#2d6cdf; color:#fff;
                                         border-radius:6px; }
            QListWidget::item:hover:!selected { background:#1b1e26; }
        """)
        for key, label in self.PAGES:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.list.addItem(item)
        self.list.currentItemChanged.connect(self._changed)
        layout.addWidget(self.list)
        layout.addStretch(1)

    def _changed(self, cur, _prev):
        if cur:
            self.pageSelected.emit(cur.data(Qt.UserRole))

    def select(self, key: str) -> None:
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == key:
                self.list.setCurrentRow(i)
                break
