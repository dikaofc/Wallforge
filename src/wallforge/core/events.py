"""Tiny application-wide event bus built on Qt signals.

Usage:
    from wallforge.core.events import bus
    bus.wallpaper_applied.emit(wallpaper_id)
    bus.wallpaper_applied.connect(handler)
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class _EventBus(QObject):
    # lifecycle / wallpaper
    wallpaper_applied = Signal(int)          # wallpaper_id
    wallpaper_paused = Signal()
    wallpaper_resumed = Signal()
    monitor_changed = Signal()               # monitor layout changed
    # performance
    performance_state_changed = Signal(str)  # "fullscreen" | "normal" | "battery"
    fps_limit_changed = Signal(int)


bus = _EventBus()
