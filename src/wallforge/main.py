"""Wallforge entry point.

Responsibilities:
  - set DPI awareness (Per-Monitor V2) BEFORE any window is created
  - install a global excepthook + atexit to restore the static wallpaper
    so the desktop never ends up blank on crash/exit
  - build the application and run the Qt event loop
"""
from __future__ import annotations

import atexit
import ctypes
import sys
import traceback

from .core.config import Config
from .core.events import bus
from .core.logger import setup_logger
from .database.database import Database
from .wallpaper.manager import WallpaperManager
from .performance.pause_manager import PauseManager
from .windows.explorer import ExplorerWatcher
from .windows.startup import set_startup
from .tray.system_tray import SystemTray
from .ui.main_window import MainWindow


def _set_dpi_aware() -> None:
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_int(-4))  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main() -> int:
    from . import __version__
    log = setup_logger("wallforge.main")
    log.info("Wallforge %s starting", __version__)

    _set_dpi_aware()

    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Wallforge")

    # Apply shared theme + icon before any window is shown.
    from .ui.theme import apply_theme
    apply_theme(app)

    # --- restore wallpaper on exit/crash -------------------------------
    from .windows.desktop import get_original_wallpaper, restore_wallpaper
    original_wp = get_original_wallpaper()

    def _restore():
        try:
            if original_wp:
                restore_wallpaper(original_wp)
        except Exception:
            pass
    atexit.register(_restore)

    def _excepthook(etype, value, tb):
        log.error("UNCAUGHT: %s", "".join(traceback.format_exception(etype, value, tb)))
        _restore()
        sys.exit(1)
    sys.excepthook = _excepthook

    # --- subsystems -----------------------------------------------------
    config = Config.load()
    db = Database()
    manager = WallpaperManager(config, db)
    pause_mgr = PauseManager(config, manager)
    explorer = ExplorerWatcher()

    window = MainWindow(app, config, db, manager, pause_mgr)
    tray = SystemTray(app, window, manager, pause_mgr)

    # CLI modes
    minimized = "--minimized" in sys.argv
    hidden = "--hidden" in sys.argv

    # --- signal wiring --------------------------------------------------
    def on_monitor_changed():
        manager.refresh_monitors()
        manager.on_monitor_changed()
    bus.monitor_changed.connect(on_monitor_changed)

    # --- start ----------------------------------------------------------
    window.show() if not (minimized or hidden) else None
    if hidden:
        window.hide()
    tray.start()
    pause_mgr.start()
    explorer.start()

    # Apply last-used wallpaper if any.
    profiles = db.get_monitor_profiles()
    if profiles and profiles[0].wallpaper_id:
        manager.apply(profiles[0].wallpaper_id)

    # Periodic update check (once after launch, then hourly).
    _schedule_update_check(config)

    log.info("Wallforge running")
    rc = app.exec()
    manager.stop_all()
    db.close()
    return rc


def _schedule_update_check(config) -> None:
    from PySide6.QtCore import QTimer
    from .services import update as update_svc
    import logging
    log = logging.getLogger("wallforge.update")

    def check():
        try:
            info = update_svc.check_for_update(config.update_url)
            if info:
                log.info("update available: %s", info.get("version"))
        except Exception as exc:
            log.debug("update check skipped: %s", exc)
    QTimer.singleShot(30_000, check)        # first check 30s after launch
    hourly = QTimer()
    hourly.timeout.connect(check)
    hourly.start(3_600_000)                  # then every hour


if __name__ == "__main__":
    raise SystemExit(main())
