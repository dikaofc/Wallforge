"""Settings page: performance, startup, audio, updates."""
from __future__ import annotations

import threading

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox,
                               QCheckBox, QSlider, QFormLayout, QPushButton,
                               QLineEdit, QHBoxLayout)

from ..core.config import Config
from ..windows.startup import set_startup, is_startup_enabled
from ..services import update as update_svc


class SettingsPage(QWidget):
    def __init__(self, config: Config, manager) -> None:
        super().__init__()
        self.config = config
        self.manager = manager
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # FPS limit
        self.fps = QComboBox()
        self.fps.addItems(["30", "60", "120", "Unlimited"])
        idx = {"30": 0, "60": 1, "120": 2, "0": 3}.get(
            str(config.performance.fps_limit), 1)
        self.fps.setCurrentIndex(idx)
        form.addRow("FPS limit", self.fps)

        # Fullscreen behaviour
        self.pause_fs = QCheckBox("Pause on fullscreen / game")
        self.pause_fs.setChecked(config.performance.pause_on_fullscreen)
        self.mute_fs = QCheckBox("Mute on fullscreen")
        self.mute_fs.setChecked(config.performance.mute_on_fullscreen)
        form.addRow(self.pause_fs)
        form.addRow(self.mute_fs)

        # Battery
        self.pause_batt = QCheckBox("Pause on battery")
        self.pause_batt.setChecked(config.performance.pause_on_battery)
        form.addRow(self.pause_batt)

        # Audio volume
        self.vol = QSlider()
        self.vol.setRange(0, 100)
        self.vol.setValue(int(config.audio_volume * 100))
        form.addRow("Master volume", self.vol)

        # Startup
        self.startup = QCheckBox("Start with Windows")
        self.startup.setChecked(is_startup_enabled())
        self.startup_mode = QComboBox()
        self.startup_mode.addItems(["Normal", "Minimized", "Hidden"])
        self.startup_mode.setCurrentText(
            config.startup.mode.capitalize())
        form.addRow(self.startup)
        form.addRow("Startup mode", self.startup_mode)

        # Updates
        self.update_url = QLineEdit(config.update_url)
        self.update_url.setMinimumWidth(320)
        form.addRow("Update URL", self.update_url)
        upd_row = QHBoxLayout()
        self.check_btn = QPushButton("Check for updates")
        self.check_btn.clicked.connect(self._check_update)
        self.update_status = QLabel("")
        self.update_status.setStyleSheet("color:#9aa;")
        upd_row.addWidget(self.check_btn)
        upd_row.addWidget(self.update_status)
        form.addRow(upd_row)

        layout.addLayout(form)

        save = QPushButton("Save settings")
        save.setStyleSheet("background:#2d6cdf;color:#fff;padding:8px;")
        save.clicked.connect(self._save)
        layout.addWidget(save)
        layout.addStretch()

    def _check_update(self) -> None:
        url = self.update_url.text().strip()
        self.config.update_url = url
        self.config.save()
        self.update_status.setText("Checking…")
        # Run off the UI thread.
        def worker():
            try:
                update_svc.check_and_apply(url, self._on_status)
            except Exception as exc:
                self._on_status(f"Error: {exc}")
        threading.Thread(target=worker, daemon=True).start()

    def _on_status(self, msg: str) -> None:
        # Qt widgets must be touched from the UI thread.
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt
        QMetaObject.invokeMethod(
            self.update_status, "setText",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, msg),
        )

    def _save(self) -> None:
        p = self.config.performance
        p.fps_limit = int(self.fps.currentText()) if self.fps.currentText() != "Unlimited" else 0
        p.pause_on_fullscreen = self.pause_fs.isChecked()
        p.mute_on_fullscreen = self.mute_fs.isChecked()
        p.pause_on_battery = self.pause_batt.isChecked()
        self.config.audio_volume = self.vol.value() / 100
        self.config.startup.mode = self.startup_mode.currentText().lower()
        self.config.update_url = self.update_url.text().strip()
        self.config.save()
        # Apply live.
        self.manager.set_volume(self.config.audio_volume)
        if p.fps_limit:
            for r in self.manager.renderers.values():
                if hasattr(r, "limiter"):
                    r.limiter.set_limit(p.fps_limit)
        # Startup registry.
        import sys
        set_startup(self.startup.isChecked(), sys.executable,
                    self.config.startup.mode)
