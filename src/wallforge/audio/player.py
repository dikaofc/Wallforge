"""Audio mixer/player facade.

Volume/mute is delegated to the active renderers (VLC handles its own audio).
This module provides a single place to set global volume and mute that the
manager fans out to every live renderer.
"""
from __future__ import annotations

from ..core.logger import setup_logger

log = setup_logger("wallforge.audio")


class AudioPlayer:
    def __init__(self, default_volume: float = 1.0) -> None:
        self.volume = default_volume
        self.muted = False

    def set_volume(self, v: float) -> None:
        self.volume = max(0.0, min(1.0, v))

    def set_muted(self, muted: bool) -> None:
        self.muted = muted
