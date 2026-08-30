"""Interactive wallpaper type descriptor."""
from __future__ import annotations

INTERACTIVE = {
    "type": "interactive",
    "label": "Interactive (OpenGL)",
    "extensions": [".py"],
    "default_entry": "content/scene.py",
    "modes": ["mouse", "particle", "clock", "audio_reactive"],
}
