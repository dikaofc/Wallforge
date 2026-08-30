"""Application configuration: dataclass Config persisted as JSON.

Stored at %LOCALAPPDATA%/Wallforge/config.json. Versioned so we can migrate.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

DATA_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "Wallforge"
CONFIG_PATH = DATA_DIR / "config.json"
WALLPAPERS_DIR = Path.home() / "Documents" / "Wallforge" / "Wallpapers"

CONFIG_VERSION = 1


@dataclass
class PerformanceConfig:
    fps_limit: int = 60               # 30 | 60 | 120 | 0(unlimited)
    pause_on_fullscreen: bool = True
    mute_on_fullscreen: bool = False
    pause_on_battery: bool = True


@dataclass
class StartupConfig:
    enabled: bool = False
    mode: str = "minimized"           # normal | minimized | hidden


@dataclass
class Config:
    version: int = CONFIG_VERSION
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    startup: StartupConfig = field(default_factory=StartupConfig)
    wallpapers_dir: str = str(WALLPAPERS_DIR)
    update_url: str = "https://raw.githubusercontent.com/dikaofc/Wallforge/main/version.json"
    audio_volume: float = 1.0

    @classmethod
    def load(cls) -> "Config":
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        WALLPAPERS_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_PATH.exists():
            cfg = cls()
            cfg.save()
            return cfg
        try:
            raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            cfg = cls()
            cfg.save()
            return cfg
        # Forward-fill missing keys instead of crashing on old configs.
        perf = raw.get("performance", {})
        start = raw.get("startup", {})
        return cls(
            version=raw.get("version", CONFIG_VERSION),
            performance=PerformanceConfig(**{k: perf.get(k, v) for k, v in
                asdict(PerformanceConfig()).items()}),
            startup=StartupConfig(**{k: start.get(k, v) for k, v in
                asdict(StartupConfig()).items()}),
            wallpapers_dir=raw.get("wallpapers_dir", str(WALLPAPERS_DIR)),
            update_url=raw.get("update_url", "https://example.com/wallforge/version.json"),
            audio_volume=raw.get("audio_volume", 1.0),
        )

    def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        WALLPAPERS_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    c = Config.load()
    print(c)
