# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Wallforge (onedir, windowed).
# Build: pyinstaller build.spec
import os

block_cipher = None

a = Analysis(
    ['src/main_entry.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        # VLC portable for video wallpapers (extracted to installer/vlc).
        ('installer/vlc', 'vlc'),
    ],
    hiddenimports=[
        'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'PySide6.QtOpenGLWidgets',
        'vlc', 'pywebview', 'soundcard', 'psutil', 'OpenGL',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pip'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Wallforge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                 # GUI only
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Wallforge',
)
