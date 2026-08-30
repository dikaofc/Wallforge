"""Wallpaper metadata derived from a manifest + DB row."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


SUPPORTED_TYPES = {"image", "video", "web", "interactive"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXT = {".mp4", ".webm", ".mkv", ".mov", ".avi"}
WEB_ENTRY = "index.html"


@dataclass
class Manifest:
    name: str
    author: Optional[str] = None
    type: str = "image"
    version: str = "1.0"
    resolution: Optional[str] = None
    fps: int = 60
    audio: bool = False
    entry: str = ""
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Manifest":
        return cls(
            name=d.get("name", "Untitled"),
            author=d.get("author"),
            type=d.get("type", "image"),
            version=str(d.get("version", "1.0")),
            resolution=d.get("resolution"),
            fps=int(d.get("fps", 60)),
            audio=bool(d.get("audio", False)),
            entry=d.get("entry", ""),
            tags=list(d.get("tags", [])),
        )


def read_manifest(folder: Path) -> Optional[Manifest]:
    mfile = folder / "manifest.json"
    if not mfile.exists():
        return None
    try:
        data = json.loads(mfile.read_text(encoding="utf-8"))
    except Exception:
        return None
    return Manifest.from_dict(data)
