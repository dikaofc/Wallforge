"""Generate a tiny 32x32 ICO for the installer (no external deps)."""
from __future__ import annotations

import struct
from pathlib import Path


def make_ico(path: Path) -> None:
    # 32x32 32-bit BGRA xor bitmap + 1-bit AND mask.
    w = h = 32
    xor = bytearray()
    and_mask = bytearray()
    for y in range(h):
        for x in range(w):
            # Simple blue rounded square-ish gradient.
            r = int(45 + x * 4)
            g = int(108 + y * 3)
            b = 223
            a = 255 if (4 < x < 28 and 4 < y < 28) else 0
            xor += bytes((b, g, r, a))
    # AND mask: 32 rows of 4 bytes (32 bits).
    for y in range(h):
        row = 0
        for x in range(w):
            if not (4 < x < 28 and 4 < y < 28):
                row |= (1 << (31 - x))
        and_mask += struct.pack("<I", row)
    # ICONDIR
    icondir = struct.pack("<HHH", 0, 1, 1)
    # ICONDIRENTRY
    img = bytes(xor) + bytes(and_mask)
    entry = struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32,
                        len(img), 6 + 16)
    Path(path).write_bytes(icondir + entry + img)
    print("wrote", path, len(icondir + entry + img), "bytes")


if __name__ == "__main__":
    dest = Path(__file__).parent / "assets" / "icon.ico"
    dest.parent.mkdir(parents=True, exist_ok=True)
    make_ico(dest)
