"""System tray icon + menu.

Closing the main window minimises to tray (app keeps running in background).
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QMessageBox

from ..core.logger import setup_logger

log = setup_logger("wallforge.tray")


class SystemTray:
    def __init__(self, app, window, manager, pause_mgr) -> None:
        self.app = app
        self.window = window
        self.manager = manager
        self.pause_mgr = pause_mgr
        self.icon = QSystemTrayIcon(window)
        self.icon.setToolTip("Wallforge")
        self._build_menu()
        self.icon.activated.connect(self._on_activate)

    def _build_menu(self) -> None:
        menu = QMenu()
        show = menu.addAction("Show")
        show.triggered.connect(self.show_window)
        pause = menu.addAction("Pause wallpaper")
        pause.triggered.connect(lambda: self.pause_mgr.set_manual_pause(True))
        resume = menu.addAction("Resume")
        resume.triggered.connect(lambda: self.pause_mgr.set_manual_pause(False))
        menu.addSeparator()
        exit_a = menu.addAction("Exit")
        exit_a.triggered.connect(self.quit)
        self.icon.setContextMenu(menu)

    def _on_activate(self, reason) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon as STI
        if reason in (STI.Trigger, STI.DoubleClick):
            self.show_window()

    def show_window(self) -> None:
        self.window.showNormal()
        self.window.activateWindow()

    def quit(self) -> None:
        self.manager.stop_all()
        self.app.quit()

    def start(self) -> None:
        self.icon.show()
        log.info("tray started")
