"""Performance page: live status of fullscreen, battery, GPU, FPS."""
from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QProgressBar, QVBoxLayout,
                               QWidget)

from ..core.config import Config
from ..performance.gpu import GpuMonitor
from ..performance.power import get_power_status
from ..windows.fullscreen import is_fullscreen


class PerformancePage(QWidget):
    def __init__(self, config: Config, manager, pause_mgr) -> None:
        super().__init__()
        self.config = config
        self.manager = manager
        self.pause_mgr = pause_mgr
        self.gpu = GpuMonitor()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("PERFORMANCE"))

        self.fs_label = QLabel("Fullscreen: unknown")
        self.batt_label = QLabel("Power: unknown")
        self.gpu_bar = QProgressBar()
        self.gpu_bar.setRange(0, 100)
        self.gpu_label = QLabel("GPU: 0%")
        self.pause_label = QLabel("Wallpaper: running")
        layout.addWidget(self.fs_label)
        layout.addWidget(self.batt_label)
        layout.addWidget(self.gpu_label)
        layout.addWidget(self.gpu_bar)
        layout.addWidget(self.pause_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(1000)

    def _update(self) -> None:
        self.fs_label.setText(
            "Fullscreen/game: " + ("YES" if is_fullscreen(self.manager.hwnds()) else "no"))
        ps = get_power_status()
        self.batt_label.setText(
            "Power: " + ("AC" if ps["on_ac"] else "battery")
            + (f" ({ps['battery_percent']}%)" if ps["battery_percent"] is not None else ""))
        g = self.gpu.sample()
        self.gpu_bar.setValue(int(g))
        self.gpu_label.setText(f"GPU: {g}%")
        self.pause_label.setText(
            "Wallpaper: " + ("paused" if self.pause_mgr.paused else "running"))
