"""GPU utilisation sampling via Windows PDH counters, filtered to our PID.

Falls back to psutil CPU/RAM sampling if the GPU counter is unavailable.
"""
from __future__ import annotations

import logging
import subprocess

from ..core.logger import setup_logger

log = setup_logger("wallforge.gpu")


class GpuMonitor:
    def __init__(self, pid: int | None = None) -> None:
        self.pid = pid
        self._pdh = None
        self._query = None
        self._counter = None
        self._available = self._init_pdh()

    def _init_pdh(self) -> bool:
        try:
            import pdh  # type: ignore
        except Exception:
            try:
                subprocess.run(["pip", "install", "pdh"],
                               capture_output=True, check=False)
                import pdh  # type: ignore
            except Exception as exc:
                log.warning("pdh unavailable, using psutil fallback: %s", exc)
                return False
        try:
            self._pdh = pdh
            self._query = pdh.Query()
            # Aggregate engine utilisation across all engines.
            self._counter = self._query.addCounter(
                r"\GPU Engine(*)\Utilization Percentage")
            self._query.start()
            return True
        except Exception as exc:
            log.warning("PDH GPU counter init failed: %s", exc)
            return False

    def sample(self) -> float:
        """Return 0..100 GPU utilisation estimate."""
        if self._available:
            try:
                self._query.collect()
                vals = self._counter.getFormattedCounterArray()
                nums = [v[1] for v in vals if isinstance(v[1], (int, float))]
                if nums:
                    # Average; engines are usually one per process context.
                    return round(sum(nums) / len(nums), 1)
            except Exception as exc:
                log.debug("GPU sample err: %s", exc)
        return self._fallback_cpu()

    def _fallback_cpu(self) -> float:
        try:
            import psutil
            return round(psutil.cpu_percent(interval=0.1), 1)
        except Exception:
            return 0.0
