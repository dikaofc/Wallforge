"""Application orchestrator (thin wrapper kept for future non-Qt harnesses).

The real runtime entry is wallforge/main.py -> main(). This module exposes
WallforgeApp for completeness and tests.
"""
from __future__ import annotations

from .config import Config
from .logger import setup_logger


class WallforgeApp:
    def __init__(self) -> None:
        self.config = Config.load()
        self.log = setup_logger()

    def run(self) -> int:
        from .main import main
        return main()


def main() -> int:
    return WallforgeApp().run()


if __name__ == "__main__":
    raise SystemExit(main())
