"""Interactive wallpaper renderer: PyOpenGL + Qt timer loop.

Renders into a QOpenGLWidget that is reparented to the desktop layer. Supports
several built-in scenes (particle field reacting to mouse, audio-reactive FFT
bars via WASAPI loopback capture) selected from the manifest. The render loop is
throttled by the FPS limiter.
"""
from __future__ import annotations

import ctypes
import math
import time
from pathlib import Path

import numpy as np
from PySide6.QtCore import QElapsedTimer, Qt, QTimer
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from ..core.logger import setup_logger
from ..performance.fps import FpsLimiter
from .renderer import Renderer

log = setup_logger("wallforge.interactive")


def _silent_log(*a, **k):
    pass


try:
    import OpenGL.GL as GL  # noqa: F401
except Exception:
    log.warning("PyOpenGL not available; interactive scene rendering disabled")


class GLScene(QOpenGLWidget):
    """Minimal particle + audio-reactive scene (pure OpenGL, no textures)."""

    def __init__(self, mode: str = "particle", get_audio=None) -> None:
        super().__init__()
        self.mode = mode
        self.get_audio = get_audio
        self.particles = np.random.rand(400, 2).astype("f4")  # x,y in 0..1
        self.vel = (np.random.rand(400, 2).astype("f4") - 0.5) * 0.002
        self.mouse = (0.5, 0.5)
        self.t = 0.0

    def initializeGL(self) -> None:
        GL.glClearColor(0.02, 0.02, 0.05, 1.0)
        GL.glEnable(GL.GL_POINT_SMOOTH)
        GL.glPointSize(3.0)

    def resizeGL(self, w, h) -> None:
        GL.glViewport(0, 0, w, h)

    def paintGL(self) -> None:
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        self.t += 0.01
        if self.mode == "particle":
            self._draw_particles()
        elif self.mode == "audio_reactive":
            self._draw_audio()
        elif self.mode == "clock":
            self._draw_clock()
        else:
            self._draw_particles()

    def _draw_particles(self) -> None:
        mx, my = self.mouse
        for i in range(len(self.particles)):
            p = self.particles[i]
            d = p - (mx, my)
            d2 = d[0] * d[0] + d[1] * d[1] + 1e-4
            self.particles[i] += self.vel[i] + d / d2 * 0.0008
            if self.particles[i][0] < 0: self.particles[i][0] = 1
            if self.particles[i][0] > 1: self.particles[i][0] = 0
            if self.particles[i][1] < 0: self.particles[i][1] = 1
            if self.particles[i][1] > 1: self.particles[i][1] = 0
        GL.glBegin(GL.GL_POINTS)
        for p in self.particles:
            GL.glColor3f(0.3 + p[0] * 0.7, 0.5 + p[1] * 0.5, 1.0)
            GL.glVertex2f(p[0] * 2 - 1, p[1] * 2 - 1)
        GL.glEnd()

    def _draw_audio(self) -> None:
        spec = self.get_audio() if self.get_audio else None
        if spec is None:
            spec = np.zeros(32)
        GL.glBegin(GL.GL_QUADS)
        n = len(spec)
        bw = 2.0 / n
        for i, v in enumerate(spec):
            x = -1 + i * bw
            h = float(v) * 1.8
            GL.glColor3f(0.2 + i / n, 0.4, 1.0 - i / n)
            GL.glVertex2f(x, -1)
            GL.glVertex2f(x + bw * 0.8, -1)
            GL.glVertex2f(x + bw * 0.8, -1 + h)
            GL.glVertex2f(x, -1 + h)
        GL.glEnd()

    def _draw_clock(self) -> None:
        # Simple rotating sweep as a placeholder clock face.
        GL.glBegin(GL.GL_LINES)
        for i in range(12):
            a = i / 12 * 2 * math.pi
            GL.glColor3f(0.6, 0.8, 1.0)
            GL.glVertex2f(0, 0)
            GL.glVertex2f(math.cos(a) * 0.8, math.sin(a) * 0.8)
        GL.glEnd()
        a = self.t % (2 * math.pi)
        GL.glBegin(GL.GL_LINES)
        GL.glColor3f(1.0, 0.4, 0.4)
        GL.glVertex2f(0, 0)
        GL.glVertex2f(math.cos(a) * 0.7, math.sin(a) * 0.7)
        GL.glEnd()

    def mouseMoveEvent(self, ev) -> None:  # Qt reports widget-local coords
        self.mouse = (ev.position().x() / max(self.width(), 1),
                      1 - ev.position().y() / max(self.height(), 1))


class InteractiveRenderer(Renderer):
    def __init__(self, monitor: dict, mode: str = "particle", audio=None) -> None:
        super().__init__(monitor)
        self.mode = mode
        self.audio = audio
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.limiter = FpsLimiter(60)

    def init(self, content_path: str) -> None:
        self.content_path = content_path
        self.window = self._create_window()
        self.scene = GLScene(self.mode, self.audio.get_spectrum if self.audio else None)
        self.scene.setParent(self.window)
        self.scene.setGeometry(0, 0, self.window.width(), self.window.height())
        self.scene.show()
        self.attach()

    def resize_to_monitor(self) -> None:
        super().resize_to_monitor()
        if hasattr(self, "scene") and self.scene:
            self.scene.setGeometry(0, 0, self.window.width(), self.window.height())

    def _tick(self) -> None:
        if not self.running:
            return
        if self.limiter.tick():
            self.scene.update()

    def start(self) -> None:
        self.running = True
        self.window.show()
        self.timer.start(16)  # ~60Hz poll; actual draw throttled by limiter

    def pause(self) -> None:
        self.running = False
        self.timer.stop()

    def resume(self) -> None:
        self.running = True
        self.timer.start(16)

    def stop(self) -> None:
        self.running = False
        self.timer.stop()
        if self.window:
            self.window.close()
            self.window = None
