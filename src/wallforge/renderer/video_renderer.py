"""Video wallpaper renderer using libVLC.

VLC renders straight into our QWidget's HWND via set_hwnd(), giving hardware
decode + audio without us touching the video pipeline. Falls back gracefully
if libVLC is not installed (logs a clear error, skips playback).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from ..core.logger import setup_logger
from .renderer import Renderer

log = setup_logger("wallforge.video")


def _bundled_vlc_dir() -> str | None:
    """Return the bundled VLC folder if present next to the executable."""
    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(sys.executable), "vlc"),
        os.path.join(os.path.dirname(sys.executable), "_internal", "vlc"),
        os.path.join(base, "..", "..", "vlc"),
        os.path.join(base, "..", "vlc"),
    ]
    for c in candidates:
        if os.path.isfile(os.path.join(c, "vlc.exe")) or \
           os.path.isfile(os.path.join(c, "libvlc.dll")):
            return os.path.abspath(c)
    return None


class VideoRenderer(Renderer):
    _instance = None

    def __init__(self, monitor: dict) -> None:
        super().__init__(monitor)
        self.player = None
        self._vlc_ok = True

    @classmethod
    def _vlc_instance(cls):
        if cls._instance is None:
            try:
                import vlc
                args = ["--no-video-title-show", "--no-osd", "--quiet"]
                vlc_dir = _bundled_vlc_dir()
                if vlc_dir:
                    # Help libVLC locate its DLLs/plugins when bundled.
                    os.environ["PATH"] = vlc_dir + os.pathsep + os.environ.get("PATH", "")
                    args = ["--plugin-path=" + os.path.join(vlc_dir, "plugins")] + args
                cls._instance = vlc.Instance(args)
            except Exception as exc:
                log.error("libVLC unavailable: %s", exc)
                cls._instance = False
        return cls._instance

    def init(self, content_path: str) -> None:
        self.content_path = content_path
        self.window = self._create_window()
        inst = self._vlc_instance()
        if not inst:
            self._vlc_ok = False
            return
        self.player = inst.media_player_new()
        media = inst.media_new_path(str(content_path))
        media.add_option("input-repeat=65535")  # loop
        self.player.set_media(media)
        self.player.set_hwnd(int(self.window.winId()))
        self.player.audio_set_volume(int(self.volume * 100))

    def start(self) -> None:
        if self.player and self._vlc_ok:
            self.player.play()
            self.player.set_rate(1.0)
        self.running = True

    def pause(self) -> None:
        self.running = False
        if self.player:
            self.player.pause()

    def resume(self) -> None:
        self.running = True
        if self.player:
            self.player.play()

    def set_volume(self, v: float) -> None:
        super().set_volume(v)
        if self.player:
            self.player.audio_set_volume(int(v * 100))

    def mute(self) -> None:
        super().mute()
        if self.player:
            self.player.audio_set_mute(True)

    def unmute(self) -> None:
        super().unmute()
        if self.player:
            self.player.audio_set_mute(False)

    def stop(self) -> None:
        self.running = False
        if self.player:
            try:
                self.player.stop()
            except Exception:
                pass
        if self.window:
            self.window.close()
            self.window = None
