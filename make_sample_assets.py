"""Generate a sample Aurora Drift wallpaper image (pure Pillow, no external asset)."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


def make_aurora(path: Path, w: int = 1920, h: int = 1080) -> None:
    img = Image.new("RGB", (w, h), (6, 8, 16))
    px = img.load()
    for y in range(h):
        for x in range(0, w, 2):  # step 2 for speed
            nx = x / w
            ny = y / h
            band = 0.5 + 0.5 * math.sin(nx * 6 + ny * 2 + math.sin(ny * 4) * 2)
            g = max(0, min(255, int(120 * band * (1 - ny) + 40)))
            r = int(30 + 60 * math.sin(nx * 3))
            b = int(120 + 100 * band)
            for dx in (0, 1):
                if x + dx < w:
                    px[x + dx, y] = (r, g, b)
    img.save(path, "JPEG", quality=85)
    print("wrote", path)


if __name__ == "__main__":
    dest = Path(__file__).parent / "wallpapers" / "Aurora Drift" / "wallpaper.jpg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    make_aurora(dest)
