"""Dataclasses mapping database rows to Python objects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Wallpaper:
    id: Optional[int]
    title: str
    author: Optional[str]
    type: str                       # image | video | web | interactive
    path: str                      # absolute folder path
    thumbnail: Optional[str] = None
    preview: Optional[str] = None
    favorite: int = 0
    created_at: Optional[str] = None
    tags: str = ""


@dataclass
class Collection:
    id: Optional[int]
    name: str


@dataclass
class Playlist:
    id: Optional[int]
    name: str


@dataclass
class PlaylistItem:
    playlist_id: int
    wallpaper_id: int
    position: int


@dataclass
class MonitorProfile:
    monitor_id: str
    wallpaper_id: Optional[int] = None
    settings: str = "{}"           # JSON: fps, audio, sync, dst rect
