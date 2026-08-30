"""Main application window: sidebar + stacked pages (all real views)."""
from __future__ import annotations

from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QStackedWidget,
                               QVBoxLayout, QWidget)

from ..core.config import Config
from ..database.database import Database
from ..performance.pause_manager import PauseManager
from .sidebar import Sidebar
from .wallpaper_grid import WallpaperGrid
from .settings import SettingsPage
from .home_page import HomePage
from .collections_page import CollectionsPage
from .displays_page import DisplaysPage
from .performance_page import PerformancePage
from .editor_page import EditorPage
from .preview import PreviewDialog


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
        self.resize(1080, 680)
        self.setStyleSheet("background:#12141a;color:#e6e6e6;")

        root = QHBoxLayout(self)
        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        right = QVBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search wallpapers…")
        self.search.textChanged.connect(self._search)
        right.addWidget(self.search)

        self.stack = QStackedWidget()
        right.addWidget(self.stack, 1)
        root.addLayout(right, 1)

        self._build_pages()
        self.sidebar.pageSelected.connect(self._show)
        self._show("home")

        self.grid.wallpaperClicked.connect(self._open_preview)

    def _build_pages(self) -> None:
        self.home = HomePage(self.db, self.manager, self._show)
        self.grid = WallpaperGrid()
        self.fav = WallpaperGrid()
        self.collections = CollectionsPage(self.db, self.manager)
        self.displays = DisplaysPage(self.db, self.manager)
        self.performance = PerformancePage(self.config, self.manager, self.pause_mgr)
        self.editor = EditorPage(self.manager)
        self.editor.export_requested.connect(self._on_export)
        self.settings_page = SettingsPage(self.config, self.manager)

        self.stack.addWidget(self.home)        # home
        self.stack.addWidget(self.grid)        # library
        self.stack.addWidget(self.fav)         # favorites
        self.stack.addWidget(self.collections) # collections
        self.stack.addWidget(self.displays)    # displays
        self.stack.addWidget(self.performance) # performance
        self.stack.addWidget(self.editor)      # editor
        self.stack.addWidget(self.settings_page)  # settings

        self._pages = {
            "home": 0, "library": 1, "favorites": 2, "collections": 3,
            "displays": 4, "performance": 5, "editor": 6, "settings": 7,
        }

    def _show(self, key: str) -> None:
        idx = self._pages.get(key, 1)
        self.stack.setCurrentIndex(idx)
        if key == "library":
            self._refresh_grid(fav=False)
        elif key == "favorites":
            self._refresh_grid(fav=True)
        elif key == "home":
            self.home._refresh()
        self.sidebar.select(key)

    def _search(self, text: str) -> None:
        if self.stack.currentIndex() in (1, 2):
            fav = self.stack.currentIndex() == 2
            items = self.db.list_wallpapers(fav_only=fav, search=text or None)
            (self.fav if fav else self.grid).set_wallpapers(items)

    def _refresh_grid(self, fav: bool) -> None:
        items = self.db.list_wallpapers(fav_only=fav)
        (self.fav if fav else self.grid).set_wallpapers(items)

    def _open_preview(self, wid: int) -> None:
        w = self.db.get_wallpaper(wid)
        if not w:
            return
        dlg = PreviewDialog(
            w, self.db,
            on_apply=lambda i: self.manager.apply(i),
            on_favorite=lambda: (self._refresh_grid(True),
                                 self.home._refresh()),
        )
        dlg.exec()

    def _on_export(self, folder: str) -> None:
        from ..services.indexing import index_directory
        from pathlib import Path
        index_directory(self.db, Path(self.config.wallpapers_dir))
        self.home._refresh()
        self._refresh_grid(fav=False)
