"""Wallpaper type descriptors and supported extensions per type."""
from __future__ import annotations

from .image import IMAGE
from .video import VIDEO
from .web import WEB
from .interactive import INTERACTIVE

TYPES = {
    "image": IMAGE,
    "video": VIDEO,
    "web": WEB,
    "interactive": INTERACTIVE,
}
