"""Decide when to pause/resume/mute wallpapers based on system state.

Consults: fullscreen/game detection, battery state, and a manual override.
Emits bus signals so renderers and tray can react.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer

from ..core.config import Config
from ..core.events import bus
from ..core.logger import setup_logger
from ..windows.fullscreen import is_fullscreen
from .power import get_power_status

log = setup_logger("wallforge.pause")


class PauseManager:
    def __init__(self, config: Config, manager) -> None:
        self.config = config
        self.manager = manager
        self.timer = QTimer()
        self.timer.timeout.connect(self._check)
        self.paused = False
        self.manual_paused = False

    def start(self, interval_ms: int = 1000) -> None:
        self.timer.start(interval_ms)

    def set_manual_pause(self, paused: bool) -> None:
        self.manual_paused = paused
        if paused:
            self._engage("manual")
        else:
            self._release("manual")

    def _check(self) -> None:
        if self.manual_paused:
            return
        perf = self.config.performance
        should_pause = False
        reason = None
        if perf.pause_on_fullscreen and is_fullscreen(self.manager.hwnds()):
            should_pause, reason = True, "fullscreen"
        elif perf.pause_on_battery and not get_power_status()["on_ac"]:
            should_pause, reason = True, "battery"
        if should_pause and not self.paused:
            self._engage(reason)
        elif not should_pause and self.paused:
            self._release(reason)

    def _engage(self, reason: str) -> None:
        self.paused = True
        self.manager.pause_all()
        if self.config.performance.mute_on_fullscreen:
            self.manager.mute_all()
        bus.performance_state_changed.emit(reason)
        bus.wallpaper_paused.emit()
        log.info("wallpapers paused (%s)", reason)

    def _release(self, reason: str) -> None:
        self.paused = False
        self.manager.resume_all()
        bus.performance_state_changed.emit("normal")
        bus.wallpaper_resumed.emit()
        log.info("wallpapers resumed (was %s)", reason)
