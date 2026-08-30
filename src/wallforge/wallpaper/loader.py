"""Load a wallpaper folder into a Manifest + resolved content path.

Validates the manifest type and that the referenced entry file exists.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..core.logger import setup_logger
from .metadata import Manifest, SUPPORTED_TYPES, read_manifest, VIDEO_EXT, IMAGE_EXT

log = setup_logger("wallforge.loader")


class LoadError(Exception):
    pass


def load(folder: str | Path) -> tuple[Manifest, Path]:
    """Return (manifest, content_path). Raises LoadError if invalid."""
    folder = Path(folder)
    if not folder.is_dir():
        raise LoadError(f"not a directory: {folder}")
    manifest = read_manifest(folder)
    if manifest is None:
        raise LoadError(f"missing manifest.json in {folder}")
    if manifest.type not in SUPPORTED_TYPES:
        raise LoadError(f"unsupported type: {manifest.type}")

    content_dir = folder / "content"
    # Resolve default entry when not specified.
    if not manifest.entry:
        if manifest.type == "image":
            for ext in IMAGE_EXT:
                cand = folder / f"wallpaper{ext}"
                if cand.exists():
                    manifest.entry = f"wallpaper{ext}"
                    break
            else:
                raise LoadError("no image file found (wallpaper.jpg/png/webp)")
        elif manifest.type == "video":
            for ext in VIDEO_EXT:
                cand = content_dir / f"video{ext}"
                if cand.exists():
                    manifest.entry = f"content/video{ext}"
                    break
            else:
                raise LoadError("no video file found (content/video.mp4)")
        elif manifest.type == "web":
            if (content_dir / WEB_ENTRY).exists():
                manifest.entry = f"content/{WEB_ENTRY}"
            else:
                raise LoadError("missing content/index.html")
        elif manifest.type == "interactive":
            manifest.entry = "content/scene.py"

    content_path = (folder / manifest.entry)
    if manifest.type in ("image", "video", "web") and not content_path.exists():
        raise LoadError(f"entry not found: {content_path}")
    return manifest, content_path
