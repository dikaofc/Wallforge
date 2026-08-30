"""Rotating file logger under %LOCALAPPDATA%/Wallforge/logs."""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from .config import DATA_DIR

_LOG_DIR = DATA_DIR / "logs"


def setup_logger(name: str = "wallforge") -> logging.Logger:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    fh = logging.handlers.RotatingFileHandler(
        _LOG_DIR / "wallforge.log", maxBytes=5_000_000, backupCount=5,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console only when run from a terminal (not the frozen .exe GUI).
    try:
        import sys
        if sys.stdout is not None and hasattr(sys.stdout, "fileno"):
            ch = logging.StreamHandler()
            ch.setFormatter(fmt)
            logger.addHandler(ch)
    except Exception:
        pass
    return logger


if __name__ == "__main__":
    log = setup_logger()
    log.info("logger online")
