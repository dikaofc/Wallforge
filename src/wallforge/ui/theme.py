"""Shared UI theme: readable fonts, high contrast, app icon."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon, QFont

ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"

DARK_BG = "#12141a"
PANEL = "#1b1d23"
PANEL_2 = "#23262f"
TEXT = "#e6e6e6"
TEXT_DIM = "#aab"
ACCENT = "#2d6cdf"
ACCENT_HOVER = "#3a7ef0"
BORDER = "#2a2d36"

STYLESHEET = f"""
QWidget {{
    background: {DARK_BG};
    color: {TEXT};
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
}}
QPushButton {{
    background: {PANEL_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 8px 14px;
    border-radius: 5px;
}}
QPushButton:hover {{ background: {BORDER}; }}
QPushButton:pressed {{ background: {ACCENT}; }}
QLineEdit, QComboBox, QSlider, QListWidget, QTextEdit {{
    background: {PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 5px;
}}
QListWidget::item:selected {{ background: {ACCENT}; color: #fff; }}
QLabel {{ color: {TEXT}; }}
QCheckBox {{ spacing: 6px; }}
QScrollArea {{ border: none; }}
QSlider::groove:horizontal {{ background: {PANEL_2}; height: 6px; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {ACCENT}; width: 14px; border-radius: 7px; margin: -4px 0; }}
"""


def app_icon() -> QIcon:
    cand = ASSETS / "icon.ico"
    if cand.exists():
        return QIcon(str(cand))
    return QIcon()


def apply_theme(app) -> None:
    app.setStyleSheet(STYLESHEET)
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    app.setWindowIcon(app_icon())
