"""Editor canvas: live OpenGL preview of the current EditorProject.

Subclasses QOpenGLWidget and draws the project evaluated at the playhead time.
"""
from __future__ import annotations

from PySide6.QtOpenGLWidgets import QOpenGLWidget

from ..core.logger import setup_logger

log = setup_logger("wallforge.editor.canvas")


class EditorCanvas(QOpenGLWidget):
    def __init__(self, project) -> None:
        super().__init__()
        self.project = project
        self.t = 0.0
        import OpenGL.GL as GL  # noqa: F401  (imported for side effects)

    def initializeGL(self) -> None:
        import OpenGL.GL as GL
        GL.glClearColor(0.04, 0.04, 0.08, 1.0)

    def resizeGL(self, w, h) -> None:
        import OpenGL.GL as GL
        GL.glViewport(0, 0, w, h)

    def paintGL(self) -> None:
        try:
            from ..editor.runtime import render_project
            import OpenGL.GL as GL
            render_project(GL, self.project.to_dict(), self.t)
        except Exception as exc:
            log.debug("editor canvas draw err: %s", exc)

    def set_time(self, t: float) -> None:
        self.t = t
        self.update()
