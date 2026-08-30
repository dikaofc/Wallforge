"""Frame-rate limiter for interactive/OpenGL renderers.

Throttle a render loop to a target FPS. `limit=0` means unlimited.
"""
from __future__ import annotations

import time

from ..core.logger import setup_logger

log = setup_logger("wallforge.fps")


class FpsLimiter:
    def __init__(self, limit: int = 60) -> None:
        self.limit = limit
        self._last = 0.0                 # first frame always renders
        self._frames = 0
        self._acc = 0.0

    def set_limit(self, limit: int) -> None:
        self.limit = limit

    def tick(self) -> bool:
        """Return True if a frame should be drawn now (else skip)."""
        now = time.perf_counter()
        elapsed = now - self._last
        if self.limit <= 0:
            self._last = now
            return True
        min_dt = 1.0 / self.limit
        if elapsed >= min_dt:
            self._last = now
            return True
        return False

    def measured_fps(self) -> float:
        self._frames += 1
        self._acc += 1.0 / max(self.limit, 1)
        return self.limit if self.limit > 0 else 0.0
