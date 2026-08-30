"""Wallpaper manager: builds and controls renderers per monitor.

Holds the live renderers keyed by monitor name. Loads a wallpaper (from a
folder path or a DB row), picks the right Renderer subclass by type, attaches
it to the desktop, and supports per-monitor assignment, synchronize mode,
pause/resume/mute across all, and re-attach on explorer restart.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from ..core.config import Config
from ..core.events import bus
from ..core.logger import setup_logger
from ..database.database import Database
from ..wallpaper.loader import load
from ..windows.monitors import get_monitors
from .types import TYPES
from ..renderer.image_renderer import ImageRenderer
from ..renderer.video_renderer import VideoRenderer
from ..renderer.web_renderer import WebRenderer
from ..renderer.interactive_renderer import InteractiveRenderer
from ..audio.capture import AudioCapture

log = setup_logger("wallforge.manager")

_RENDERERS = {
    "image": ImageRenderer,
    "video": VideoRenderer,
    "web": WebRenderer,
    "interactive": InteractiveRenderer,
}


class WallpaperManager:
    def __init__(self, config: Config, db: Database) -> None:
        self.config = config
        self.db = db
        self.renderers: Dict[str, object] = {}      # monitor_name -> Renderer
        self.monitors = get_monitors()
        self.audio = AudioCapture()
        self.synchronize = False
        self.active_wallpaper_id: Optional[int] = None
        self._paused = False
        bus.monitor_changed.connect(self.on_monitor_changed)

    # ---- introspection -------------------------------------------------
    def hwnds(self) -> set[int]:
        return {int(r.hwnd()) for r in self.renderers.values() if r.hwnd()}

    # ---- apply ---------------------------------------------------------
    def apply(self, wallpaper_id: int, monitor_name: Optional[str] = None) -> bool:
        w = self.db.get_wallpaper(wallpaper_id)
        if not w:
            log.error("wallpaper %s not found", wallpaper_id)
            return False
        # Auto-heal: skip (and forget) wallpapers whose source is gone.
        if not Path(w.path).exists():
            log.warning("wallpaper %s source missing, skipping: %s", w.id, w.path)
            try:
                for mp in self.db.get_monitor_profiles():
                    if mp.wallpaper_id == w.id:
                        self.db.clear_monitor_profile(mp.monitor_id)
            except Exception:
                pass
            return False
        try:
            manifest, content = load(w.path)
        except Exception as exc:
            log.error("load failed for %s: %s", w.path, exc)
            return False
        target = monitor_name or self._primary_name()
        self._spawn_for(manifest, str(content), target, w.id)
        self.active_wallpaper_id = w.id
        self.db.set_monitor_profile(_mp(target, w.id, self.config))
        bus.wallpaper_applied.emit(w.id)
        log.info("applied %r on %s", manifest.name, target)
        return True

    def _spawn_for(self, manifest, content: str, monitor_name: str, wid: int) -> None:
        monitors = {m["name"]: m for m in self.monitors}
        mon = monitors.get(monitor_name) or self.monitors[0]
        self._stop_monitor(monitor_name)
        cls = _RENDERERS.get(manifest.type)
        if cls is None:
            log.error("no renderer for type %s", manifest.type)
            return
        audio = self.audio if (manifest.type == "interactive"
                               and "audio_reactive" in manifest.tags) else None
        if audio and not self.audio._running:
            self.audio.start()
        mode = "audio_reactive" if (audio and "audio_reactive" in manifest.tags) \
            else manifest.tags[0] if manifest.tags else "particle"
        try:
            r = cls(mon, mode=mode, audio=audio) if manifest.type == "interactive" \
                else cls(mon)
            r.init(content)
            r.start()
            if r.attach():
                self.renderers[monitor_name] = r
                log.info("renderer attached on %s (hwnd=%s)", monitor_name, r.hwnd())
            else:
                log.error("renderer attach FAILED on %s — wallpaper will not be visible",
                          monitor_name)
        except Exception as exc:
            log.exception("renderer spawn failed: %s", exc)

    # ---- controls ------------------------------------------------------
    def _for_each(self, fn) -> None:
        for r in list(self.renderers.values()):
            try:
                fn(r)
            except Exception as exc:
                log.debug("control err: %s", exc)

    def pause_all(self) -> None:
        self._for_each(lambda r: r.pause())

    def resume_all(self) -> None:
        self._for_each(lambda r: r.resume())

    def mute_all(self) -> None:
        self._for_each(lambda r: r.mute())

    def unmute_all(self) -> None:
        self._for_each(lambda r: r.unmute())

    def set_volume(self, v: float) -> None:
        self._for_each(lambda r: r.set_volume(v))

    # ---- re-attach -----------------------------------------------------
    def on_monitor_changed(self) -> None:
        log.info("monitor/explorer changed; re-attaching renderers")
        for name, r in list(self.renderers.items()):
            try:
                r.resize_to_monitor()
                r.attach()
            except Exception as exc:
                log.debug("re-attach err %s: %s", name, exc)

    def refresh_monitors(self) -> None:
        self.monitors = get_monitors()

    # ---- teardown ------------------------------------------------------
    def _stop_monitor(self, name: str) -> None:
        r = self.renderers.pop(name, None)
        if r:
            try:
                r.stop()
            except Exception:
                pass

    def stop_all(self) -> None:
        for name in list(self.renderers.keys()):
            self._stop_monitor(name)
        self.audio.stop()

    # ---- helpers -------------------------------------------------------
    def _primary_name(self) -> str:
        for m in self.monitors:
            if m["primary"]:
                return m["name"]
        return self.monitors[0]["name"] if self.monitors else ""


def _mp(monitor_id: str, wid: int, config: Config):
    from ..database.models import MonitorProfile
    return MonitorProfile(monitor_id=monitor_id, wallpaper_id=wid,
                          settings="{}")
