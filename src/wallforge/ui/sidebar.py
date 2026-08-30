"""Left navigation sidebar (themed, readable, icon-free labels)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout


class Sidebar(QWidget):
    pageSelected = Signal(str)

    PAGES = [
        ("Home", "home"),
        ("Library", "library"),
        ("Favorites", "favorites"),
        ("Collections", "collections"),
        ("Displays", "displays"),
        ("Performance", "performance"),
        ("Editor", "editor"),
        ("Settings", "settings"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setFixedWidth(180)
        self.setStyleSheet(
            "background:#1b1d23;border-right:1px solid #2a2d36;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)
        self.list = QListWidget()
        self.list.setStyleSheet(
            "QListWidget{border:0;background:#1b1d23;}"
            "QListWidget::item{padding:11px 18px;color:#cfd2da;font-size:14px;}"
            "QListWidget::item:selected{background:#2d6cdf;color:#fff;border-radius:0;}"
            "QListWidget::item:hover{background:#23262f;}")
        for label, key in self.PAGES:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.list.addItem(item)
        self.list.currentRowChanged.connect(self._on_select)
        layout.addWidget(self.list)
        layout.addStretch()

    def _on_select(self, row: int) -> None:
        item = self.list.item(row)
        if item:
            self.pageSelected.emit(item.data(Qt.UserRole))

    def select(self, key: str) -> None:
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == key:
                self.list.setCurrentRow(i)
                return
