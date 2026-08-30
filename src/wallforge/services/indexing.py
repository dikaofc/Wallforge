"""Scan wallpaper folders and synchronise the database + thumbnails.

Looks in the configured wallpapers_dir for subfolders containing a
manifest.json. Generates a thumbnail AND a preview image for every type:
  - image       -> Pillow downscale of the source
  - video       -> VLC snapshot (falls back to a colored placeholder)
  - web         -> colored gradient placeholder
  - interactive -> colored gradient placeholder
New wallpapers are added; removed ones are dropped from the DB.
"""
from __future__ import annotations

from pathlib import Path

from ..core.config import Config
from ..core.logger import setup_logger
from ..database.database import Database
from ..wallpaper.loader import load
from ..wallpaper.metadata import Manifest

log = setup_logger("wallforge.indexing")

THUMB_SIZE = (320, 180)
PREVIEW_SIZE = (640, 360)


def _make_thumbnail(src: Path, dst: Path, size=THUMB_SIZE) -> bool:
    try:
        from PIL import Image
        dst.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail(size, Image.LANCZOS)
            im.save(dst, "JPEG", quality=82)
        return True
    except Exception as exc:
        log.warning("thumbnail failed for %s: %s", src, exc)
        return False


def _make_video_snapshot(src: Path, dst: Path, size=THUMB_SIZE) -> bool:
    """Try a VLC snapshot; fall back to placeholder on any failure."""
    try:
        import vlc
        import time
        inst = vlc.Instance("--no-audio", "--quiet", "--intf", "dummy")
        player = inst.media_player_new()
        media = inst.media_new(str(src))
        player.set_media(media)
        player.play()
        # wait for the first frame
        for _ in range(50):
            if player.get_length() > 0:
                break
            time.sleep(0.05)
        player.set_time(max(1, int(player.get_length() * 0.1)))
        time.sleep(0.3)
        player.video_take_snapshot(0, str(dst), *size)
        player.stop()
        inst.release()
        if dst.exists() and dst.stat().st_size > 0:
            return True
    except Exception as exc:
        log.debug("vlc snapshot failed for %s: %s", src, exc)
    return False


def _make_placeholder(dst: Path, title: str, hue: int, size=THUMB_SIZE) -> bool:
    """Draw a gradient placeholder so every wallpaper has a visible thumbnail."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        dst.parent.mkdir(parents=True, exist_ok=True)
        w, h = size
        im = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(im)
        c1 = _hsv(hue % 360, 0.55, 0.30)
        c2 = _hsv((hue + 40) % 360, 0.70, 0.55)
        for y in range(h):
            t = y / h
            r = int(c1[0] * (1 - t) + c2[0] * t)
            g = int(c1[1] * (1 - t) + c2[1] * t)
            b = int(c1[2] * (1 - t) + c2[2] * t)
            draw.line([(0, y), (w, y)], fill=(r, g, b))
        # label
        try:
            font = ImageFont.load_default()
            draw.text((10, h - 26), title[:28], fill=(235, 235, 235), font=font)
        except Exception:
            pass
        im.save(dst, "JPEG", quality=82)
        return True
    except Exception as exc:
        log.warning("placeholder failed for %s: %s", dst, exc)
        return False


def _hsv(h, s, v):
    import colorsys
    return tuple(int(255 * x) for x in colorsys.hsv_to_rgb(h / 360.0, s, v))


def index_directory(db: Database, root: Path) -> int:
    count = 0
    seen = set()
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        try:
            manifest, content = load(folder)
        except Exception as exc:
            log.debug("skip %s: %s", folder, exc)
            continue
        seen.add(str(folder))

        thumb = folder / "thumbnail.jpg"
        preview = folder / "preview.jpg"
        if not thumb.exists() or not preview.exists():
            if manifest.type == "image":
                ok_t = _make_thumbnail(Path(content), thumb)
                ok_p = _make_thumbnail(Path(content), preview, PREVIEW_SIZE)
            elif manifest.type == "video":
                ok_t = _make_video_snapshot(Path(content), thumb) or _make_placeholder(
                    thumb, manifest.name, hash(manifest.name) % 360)
                ok_p = _make_video_snapshot(Path(content), preview, PREVIEW_SIZE) or _make_placeholder(
                    preview, manifest.name, hash(manifest.name) % 360, PREVIEW_SIZE)
            else:
                hue = hash(manifest.name) % 360
                ok_t = _make_placeholder(thumb, manifest.name, hue)
                ok_p = _make_placeholder(preview, manifest.name, hue, PREVIEW_SIZE)
            if not (ok_t and ok_p):
                log.debug("thumbnail/preview not generated for %s", folder)

        w = db.upsert_wallpaper(_row_from(folder, manifest, thumb, preview))

        # If this wallpaper has no DB id yet and is brand new, log it.
        if w is not None:
            count += 1
        log.info("indexed: %s (%s)", manifest.name, manifest.type)
    # Drop folders that no longer exist.
    for w in db.list_wallpapers():
        if str(w.path) not in seen and not Path(w.path).exists():
            db.delete_wallpaper(w.id)
    return count


def _row_from(folder: Path, m: Manifest, thumb: Path, preview: Path):
    from ..database.models import Wallpaper
    return Wallpaper(
        id=None, title=m.name, author=m.author, type=m.type, path=str(folder),
        thumbnail=str(thumb) if thumb.exists() else None,
        preview=str(preview) if preview.exists() else None,
        favorite=0, created_at=None, tags=",".join(m.tags),
    )


def index_all(db: Database, config: Config) -> int:
    root = Path(config.wallpapers_dir)
    root.mkdir(parents=True, exist_ok=True)
    return index_directory(db, root)


if __name__ == "__main__":
    from ..core.config import Config
    from ..database.database import Database
    c = Config.load()
    d = Database()
    print("indexed", index_all(d, c), "wallpapers")
    d.close()
