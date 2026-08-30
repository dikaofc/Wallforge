"""SQLite database layer with forward migration.

All access goes through this module so we control schema upgrades and never
lose user data. Paths are resolved from core.config.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from ..core.config import DATA_DIR
from ..core.logger import setup_logger
from .models import (
    Wallpaper, Collection, Playlist, PlaylistItem, MonitorProfile,
)

log = setup_logger("wallforge.db")
DB_PATH = DATA_DIR / "wallforge.db"
SCHEMA_VERSION = 1

_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);

CREATE TABLE IF NOT EXISTS wallpapers (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    author      TEXT,
    type        TEXT NOT NULL,
    path        TEXT NOT NULL,
    thumbnail   TEXT,
    preview     TEXT,
    favorite    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    tags        TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS collections (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS collection_items (
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    wallpaper_id  INTEGER NOT NULL REFERENCES wallpapers(id) ON DELETE CASCADE,
    PRIMARY KEY (collection_id, wallpaper_id)
);

CREATE TABLE IF NOT EXISTS playlists (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS playlist_items (
    playlist_id  INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    wallpaper_id INTEGER NOT NULL REFERENCES wallpapers(id) ON DELETE CASCADE,
    position     INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, wallpaper_id)
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS monitor_profiles (
    monitor_id   TEXT NOT NULL PRIMARY KEY,
    wallpaper_id INTEGER REFERENCES wallpapers(id) ON DELETE SET NULL,
    settings     TEXT NOT NULL DEFAULT '{}'
);
"""


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._migrate()
        log.info("database ready at %s", path)

    # ---- migration -----------------------------------------------------
    def _migrate(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
        )
        row = cur.execute("SELECT version FROM schema_version").fetchone()
        version = row["version"] if row else 0
        if version == 0:
            cur.executescript(_SCHEMA)
            cur.execute("INSERT INTO schema_version (version) VALUES (?)",
                        (SCHEMA_VERSION,))
            self.conn.commit()
            return
        # Future forward migrations go here (elif version == N: ...).
        if version < SCHEMA_VERSION:
            # Example placeholder; add ALTER statements as schema grows.
            cur.execute("UPDATE schema_version SET version = ?",
                        (SCHEMA_VERSION,))
            self.conn.commit()

    # ---- wallpapers ----------------------------------------------------
    def upsert_wallpaper(self, w: Wallpaper) -> int:
        cur = self.conn.cursor()
        existing = cur.execute(
            "SELECT id FROM wallpapers WHERE path = ?", (w.path,)
        ).fetchone()
        if existing:
            cur.execute(
                """UPDATE wallpapers SET title=?, author=?, type=?, path=?,
                       thumbnail=?, preview=?, tags=? WHERE id=?""",
                (w.title, w.author, w.type, w.path, w.thumbnail,
                 w.preview, w.tags, existing["id"]),
            )
            self.conn.commit()
            return existing["id"]
        cur.execute(
            """INSERT INTO wallpapers (title, author, type, path, thumbnail,
                                      preview, tags)
               VALUES (?,?,?,?,?,?,?)""",
            (w.title, w.author, w.type, w.path, w.thumbnail,
             w.preview, w.tags),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_wallpaper(self, wid: int) -> Optional[Wallpaper]:
        row = self.conn.execute(
            "SELECT * FROM wallpapers WHERE id=?", (wid,)
        ).fetchone()
        return Wallpaper(**dict(row)) if row else None

    def list_wallpapers(self, *, fav_only: bool = False,
                        type_filter: Optional[str] = None,
                        search: Optional[str] = None,
                        collection_id: Optional[int] = None
                        ) -> list[Wallpaper]:
        sql = "SELECT w.* FROM wallpapers w"
        args: list = []
        joins = []
        where = []
        if collection_id is not None:
            joins.append(
                "JOIN collection_items ci ON ci.wallpaper_id = w.id")
            where.append("ci.collection_id = ?")
            args.append(collection_id)
        if fav_only:
            where.append("w.favorite = 1")
        if type_filter:
            where.append("w.type = ?")
            args.append(type_filter)
        if search:
            where.append("(w.title LIKE ? OR w.author LIKE ? OR w.tags LIKE ?)")
            like = f"%{search}%"
            args.extend([like, like, like])
        if joins:
            sql += " " + " ".join(joins)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY w.favorite DESC, w.created_at DESC"
        rows = self.conn.execute(sql, args).fetchall()
        return [Wallpaper(**dict(r)) for r in rows]

    def set_favorite(self, wid: int, value: bool) -> None:
        self.conn.execute(
            "UPDATE wallpapers SET favorite = ? WHERE id = ?",
            (1 if value else 0, wid))
        self.conn.commit()

    def delete_wallpaper(self, wid: int) -> None:
        self.conn.execute("DELETE FROM wallpapers WHERE id = ?", (wid,))
        self.conn.commit()

    # ---- collections ---------------------------------------------------
    def create_collection(self, name: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO collections (name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def list_collections(self) -> list[Collection]:
        rows = self.conn.execute(
            "SELECT * FROM collections ORDER BY name").fetchall()
        return [Collection(**dict(r)) for r in rows]

    def add_to_collection(self, cid: int, wid: int) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO collection_items VALUES (?,?)", (cid, wid))
        self.conn.commit()

    def remove_from_collection(self, cid: int, wid: int) -> None:
        self.conn.execute(
            "DELETE FROM collection_items WHERE collection_id=? AND wallpaper_id=?",
            (cid, wid))
        self.conn.commit()

    # ---- playlists -----------------------------------------------------
    def create_playlist(self, name: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO playlists (name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def list_playlists(self) -> list[Playlist]:
        rows = self.conn.execute("SELECT * FROM playlists ORDER BY name").fetchall()
        return [Playlist(**dict(r)) for r in rows]

    def set_playlist_items(self, pid: int, wids: list[int]) -> None:
        self.conn.execute("DELETE FROM playlist_items WHERE playlist_id=?", (pid,))
        self.conn.executemany(
            "INSERT INTO playlist_items VALUES (?,?,?)",
            [(pid, wid, i) for i, wid in enumerate(wids)])
        self.conn.commit()

    def get_playlist_items(self, pid: int) -> list[int]:
        rows = self.conn.execute(
            "SELECT wallpaper_id FROM playlist_items WHERE playlist_id=? "
            "ORDER BY position", (pid,)).fetchall()
        return [r["wallpaper_id"] for r in rows]

    # ---- settings ------------------------------------------------------
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value))
        self.conn.commit()

    # ---- monitor profiles ---------------------------------------------
    def set_monitor_profile(self, mp: MonitorProfile) -> None:
        self.conn.execute(
            "INSERT INTO monitor_profiles (monitor_id, wallpaper_id, settings) "
            "VALUES (?,?,?) ON CONFLICT(monitor_id) DO UPDATE SET "
            "wallpaper_id=excluded.wallpaper_id, settings=excluded.settings",
            (mp.monitor_id, mp.wallpaper_id, mp.settings))
        self.conn.commit()

    def get_monitor_profiles(self) -> list[MonitorProfile]:
        rows = self.conn.execute("SELECT * FROM monitor_profiles").fetchall()
        return [MonitorProfile(**dict(r)) for r in rows]

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    db = Database()
    db.upsert_wallpaper(Wallpaper(None, "Test", "Dika", "image",
                                  "C:/x", None, None, 0, None, "neon"))
    print(db.list_wallpapers(search="neon"))
    db.close()
