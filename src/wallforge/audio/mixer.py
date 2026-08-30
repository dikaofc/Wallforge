"""Audio mixer: fans global volume/mute out to all live renderers."""
from __future__ import annotations

from ..core.logger import setup_logger

log = setup_logger("wallforge.mixer")


class Mixer:
    def __init__(self, manager) -> None:
        self.manager = manager

    def apply_volume(self, v: float) -> None:
        for r in self.manager.renderers.values():
            try:
                r.set_volume(v)
            except Exception:
                pass

    def apply_mute(self, muted: bool) -> None:
        for r in self.manager.renderers.values():
            try:
                r.mute() if muted else r.unmute()
            except Exception:
                pass
