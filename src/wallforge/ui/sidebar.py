"""Left navigation sidebar."""
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
        ("Settings", "settings"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setFixedWidth(150)
        self.setStyleSheet("background:#1b1d23; color:#e6e6e6;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.list = QListWidget()
        self.list.setStyleSheet("QListWidget{border:0;} "
                                "QListWidget::item{padding:10px 14px;}"
                                "QListWidget::item:selected{background:#2d6cdf;}")
        for label, key in self.PAGES:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.list.addItem(item)
        self.list.currentRowChanged.connect(self._on_select)
        layout.addWidget(self.list)

    def _on_select(self, row: int) -> None:
        item = self.list.item(row)
        if item:
            self.pageSelected.emit(item.data(Qt.UserRole))

    def select(self, key: str) -> None:
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == key:
                self.list.setCurrentRow(i)
                return
