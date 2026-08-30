"""Main application window — simplified: add / pick / apply.

Layout:
  [ Sidebar ] [ TopBar: + Add | Search | Pause | Next ] [ Grid / Settings ]
Click a wallpaper in the grid -> it is applied immediately.
The "Add wallpaper" button opens a file picker, imports the file as a
new wallpaper, and applies it. Everything else (editor, displays,
performance, collections) lives under Settings so the main UI stays tiny.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QStackedWidget, QVBoxLayout, QWidget, QFileDialog,
                               QMessageBox, QMenu)

from ..core.config import Config
from ..core.logger import setup_logger
from ..database.database import Database
from ..performance.pause_manager import PauseManager
from .sidebar import Sidebar
from .wallpaper_grid import WallpaperGrid
from .settings import SettingsPage

log = setup_logger("wallforge.ui")


class MainWindow(QWidget):
    def __init__(self, app, config: Config, db: Database,
                 manager, pause_mgr: PauseManager) -> None:
        super().__init__()
        self.app = app
        self.config = config
        self.db = db
        self.manager = manager
        self.pause_mgr = pause_mgr
        self.setWindowTitle("Wallforge")
        self.resize(1000, 640)
        self.setStyleSheet("background:#12141a;color:#e6e6e6;")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.sidebar = Sidebar()
        self.sidebar.setMinimumWidth(160)
        root.addWidget(self.sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(10, 10, 10, 10)
        right.setSpacing(8)
        right.addLayout(self._topbar())
        self.stack = QStackedWidget()
        right.addWidget(self.stack, 1)
        root.addLayout(right, 1)

        # Pages
        self.grid = WallpaperGrid()
        self.settings_page = SettingsPage(self.config, self.manager)
        self.stack.addWidget(self.grid)                 # 0 library
        self.stack.addWidget(self.settings_page)        # 1 settings

        self.grid.wallpaperClicked.connect(self._apply_wallpaper)
        self.grid.wallpaperRightClicked.connect(self._fav_toggle)
        self.sidebar.pageSelected.connect(self._show)

        # Index wallpapers from the configured directory on each launch.
        try:
            from ..services import indexing
            indexing.index_all(self.db, self.config)
        except Exception as exc:
            log.warning("indexing failed: %s", exc)

        self._refresh_grid()
        self.sidebar.select("library")

    # ---- top bar -------------------------------------------------------
    def _topbar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(8)

        add = QPushButton("+ Add wallpaper")
        add.setStyleSheet("background:#2d6cdf;color:#fff;font-weight:bold;"
                          "padding:8px 14px;border-radius:6px;font-size:13px;")
        add.clicked.connect(self._add_wallpaper)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search wallpapers…")
        self.search.setMinimumHeight(34)
        self.search.textChanged.connect(self._search)

        pause = QPushButton("Pause")
        pause.setMinimumHeight(34)
        pause.clicked.connect(lambda: self._toggle_pause(pause))

        nxt = QPushButton("Next")
        nxt.setMinimumHeight(34)
        nxt.clicked.connect(self._next)

        bar.addWidget(add)
        bar.addWidget(self.search, 1)
        bar.addWidget(pause)
        bar.addWidget(nxt)
        self._pause_btn = pause
        return bar

    # ---- navigation ----------------------------------------------------
    def _show(self, key: str) -> None:
        if key == "library":
            self.stack.setCurrentIndex(0)
            self._refresh_grid()
        elif key == "settings":
            self.stack.setCurrentIndex(1)

    # ---- wallpaper actions --------------------------------------------
    def _refresh_grid(self, fav: bool = False) -> None:
        items = self.db.list_wallpapers(fav_only=fav)
        self.grid.set_wallpapers(items)

    def _search(self, text: str) -> None:
        items = self.db.list_wallpapers(fav_only=False, search=text or None)
        self.grid.set_wallpapers(items)

    def _apply_wallpaper(self, wid: int) -> None:
        w = self.db.get_wallpaper(wid)
        if not w:
            return
        ok = self.manager.apply(wid)
        if ok:
            self._status(f"Applied: {w.title}")
        else:
            self._status("Failed to apply — see log", error=True)

    def _fav_toggle(self, wid: int) -> None:
        w = self.db.get_wallpaper(wid)
        if not w:
            return
        self.db.set_favorite(wid, not bool(w.favorite))
        self._refresh_grid()

    def _toggle_pause(self, btn: QPushButton) -> None:
        if getattr(self.manager, "_paused", False):
            self.manager.resume_all()
            self.manager._paused = False
            btn.setText("Pause")
        else:
            self.manager.pause_all()
            self.manager._paused = True
            btn.setText("Resume")

    def _next(self) -> None:
        items = self.db.list_wallpapers()
        if not items:
            return
        cur = self.manager.active_wallpaper_id
        idx = 0
        for i, w in enumerate(items):
            if w.id == cur:
                idx = (i + 1) % len(items)
                break
        self._apply_wallpaper(items[idx].id)

    def _add_wallpaper(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Add wallpaper",
            "", "Media (*.jpg *.jpeg *.png *.webp *.bmp *.mp4 *.webm *.mkv)")
        if not path:
            return
        src = Path(path)
        folder = Path(self.config.wallpapers_dir) / src.stem
        folder.mkdir(parents=True, exist_ok=True)
        dst = folder / src.name
        if dst != src:
            shutil.copy(src, dst)
        wtype = "video" if src.suffix.lower() in (".mp4", ".webm", ".mkv") else "image"
        manifest = {
            "name": src.stem,
            "author": "You",
            "type": wtype,
            "version": "1.0",
            "tags": [],
        }
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2))
        from ..services.indexing import index_directory
        index_directory(self.db, Path(self.config.wallpapers_dir))
        w = self.db.get_wallpaper_by_path(str(folder))
        if w:
            self._apply_wallpaper(w.id)
        self._refresh_grid()
        QMessageBox.information(self, "Added", f"Added & applied: {src.stem}")

    # ---- misc ----------------------------------------------------------
    def _status(self, msg: str, error: bool = False) -> None:
        # Lightweight status: briefly raise a tooltip-like message box for errors.
        if error:
            QMessageBox.warning(self, "Wallforge", msg)
