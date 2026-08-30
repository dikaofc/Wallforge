"""Smoke tests for Wallforge subsystems that don't need a display."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


def test_monitors_enumerate():
    from src.wallforge.windows.monitors import get_monitors
    monitors = get_monitors()
    assert isinstance(monitors, list)
    assert len(monitors) >= 1
    assert "monitor" in monitors[0]


def test_desktop_worker_found():
    from src.wallforge.windows.desktop import find_desktop_worker_window
    hwnd = find_desktop_worker_window()
    assert hwnd != 0  # Progman fallback guarantees non-zero


def test_loader_image_ok(tmp_path):
    folder = tmp_path / "wp"
    folder.mkdir()
    (folder / "manifest.json").write_text(json.dumps({
        "name": "T", "type": "image", "entry": "wallpaper.jpg"}))
    (folder / "wallpaper.jpg").write_bytes(b"fake")
    from src.wallforge.wallpaper.loader import load
    manifest, content = load(folder)
    assert manifest.type == "image"
    assert content.exists()


def test_loader_rejects_bad_type(tmp_path):
    folder = tmp_path / "wp"
    folder.mkdir()
    (folder / "manifest.json").write_text(json.dumps({"name": "T", "type": "bogus"}))
    from src.wallforge.wallpaper.loader import load, LoadError
    with pytest.raises(LoadError):
        load(folder)


def test_database_roundtrip(tmp_path):
    from src.wallforge.database.database import Database
    from src.wallforge.database.models import Wallpaper
    db = Database(tmp_path / "t.db")
    wid = db.upsert_wallpaper(Wallpaper(None, "X", "A", "image", "C:/x", None, None, 0, None, "neon"))
    assert wid > 0
    rows = db.list_wallpapers(search="neon")
    assert len(rows) == 1
    db.set_favorite(wid, True)
    assert db.list_wallpapers(fav_only=True)[0].favorite == 1
    db.close()


def test_config_persist(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    # re-import config so DATA_DIR resolves under tmp
    import importlib
    from src.wallforge.core import config
    importlib.reload(config)
    c = config.Config.load()
    c.audio_volume = 0.5
    c.save()
    assert config.CONFIG_PATH.exists()


def test_fps_limiter():
    from src.wallforge.performance.fps import FpsLimiter
    lim = FpsLimiter(limit=0)
    assert lim.tick() is True
    lim2 = FpsLimiter(limit=1000)   # ~1ms throttling
    assert lim2.tick() is True       # first frame always renders
    assert lim2.tick() is False      # immediate 2nd call too soon


def test_fullscreen_callable():
    from src.wallforge.windows.fullscreen import is_fullscreen
    # Should not raise; value depends on foreground window.
    _ = is_fullscreen()
