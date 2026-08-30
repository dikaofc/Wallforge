"""Collections page: create collections and assign wallpapers to them."""
from __future__ import annotations

from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QVBoxLayout, QWidget)

from ..database.database import Database


class CollectionsPage(QWidget):
    def __init__(self, db: Database, manager) -> None:
        super().__init__()
        self.db = db
        self.manager = manager
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("COLLECTIONS"))

        top = QHBoxLayout()
        self.combo = QComboBox()
        self.refresh_collections()
        add = QPushButton("New")
        add.clicked.connect(self._new)
        top.addWidget(self.combo)
        top.addWidget(add)
        layout.addLayout(top)

        mid = QHBoxLayout()
        self.all_list = QListWidget()
        self.members = QListWidget()
        self._fill_all()
        mid.addWidget(self.all_list)
        mid.addWidget(self.members)
        layout.addLayout(mid)

        btns = QHBoxLayout()
        addm = QPushButton("Add →")
        addm.clicked.connect(self._add_member)
        rem = QPushButton("← Remove")
        rem.clicked.connect(self._remove_member)
        btns.addWidget(addm)
        btns.addWidget(rem)
        layout.addLayout(btns)
        self.combo.currentIndexChanged.connect(self._show_members)

    def refresh_collections(self) -> None:
        self.combo.clear()
        for c in self.db.list_collections():
            self.combo.addItem(c.name, c.id)

    def _new(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New collection", "Name:")
        if ok and name:
            self.db.create_collection(name)
            self.refresh_collections()

    def _fill_all(self) -> None:
        self.all_list.clear()
        for w in self.db.list_wallpapers():
            it = QListWidgetItem(w.title)
            it.setData(0, w.id)
            self.all_list.addItem(it)

    def _show_members(self) -> None:
        self.members.clear()
        cid = self.combo.currentData()
        if cid is None:
            return
        members = self.db.list_wallpapers(collection_id=cid)
        for w in members:
            it = QListWidgetItem(w.title)
            it.setData(0, w.id)
            self.members.addItem(it)

    def _add_member(self) -> None:
        item = self.all_list.currentItem()
        cid = self.combo.currentData()
        if item and cid is not None:
            self.db.add_to_collection(cid, item.data(0))
            self._show_members()

    def _remove_member(self) -> None:
        item = self.members.currentItem()
        cid = self.combo.currentData()
        if item and cid is not None:
            self.db.remove_from_collection(cid, item.data(0))
            self._show_members()
