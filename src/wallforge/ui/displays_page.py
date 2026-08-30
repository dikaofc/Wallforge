"""Displays page: assign a wallpaper per monitor + synchronise toggle."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout, QWidget)

from ..core.events import bus
from ..database.database import Database
from ..windows.monitors import get_monitors


class DisplaysPage(QWidget):
    def __init__(self, db: Database, manager) -> None:
        super().__init__()
        self.db = db
        self.manager = manager
        self.monitors = get_monitors()
        self.rows = []          # (monitor_name, combo)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("DISPLAYS"))

        self.sync = QCheckBox("Synchronise all monitors (same wallpaper)")
        self.sync.stateChanged.connect(self._on_sync)
        layout.addWidget(self.sync)

        for m in self.monitors:
            row = QHBoxLayout()
            label = QLabel(f"{m['name']}  "
                           f"({m['monitor'][2]-m['monitor'][0]}x"
                           f"{m['monitor'][3]-m['monitor'][1]})"
                           f"{' [PRIMARY]' if m['primary'] else ''}")
            combo = QComboBox()
            combo.addItem("(none)", None)
            for w in self.db.list_wallpapers():
                combo.addItem(w.title, w.id)
            combo.currentIndexChanged.connect(
                lambda *_i, mn=m["name"], c=combo: self._assign(mn, c))
            row.addWidget(label)
            row.addWidget(combo)
            layout.addLayout(row)
            self.rows.append((m["name"], combo))

        layout.addStretch()
        refresh = QPushButton("Refresh monitors")
        refresh.clicked.connect(self._refresh_monitors)
        layout.addWidget(refresh)

    def _assign(self, monitor_name: str, combo: QComboBox) -> None:
        wid = combo.currentData()
        if wid is None:
            return
        self.manager.apply(wid, monitor_name)
        self.db.set_monitor_profile(
            self._mp(monitor_name, wid))

    def _on_sync(self, state: int) -> None:
        if state == Qt.Checked:
            # apply current primary wallpaper to every monitor
            primary = next((n for n, c in self.rows
                           if c.currentData() is not None), None)
            if primary:
                wid = dict(self.rows)[primary].currentData()
                for n, _ in self.rows:
                    self.manager.apply(wid, n)

    def _refresh_monitors(self) -> None:
        self.monitors = get_monitors()
        bus.monitor_changed.emit()

    def _mp(self, monitor_id, wid):
        from ..database.models import MonitorProfile
        return MonitorProfile(monitor_id=monitor_id, wallpaper_id=wid, settings="{}")
