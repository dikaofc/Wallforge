"""Default interactive scene for Neon Particles.

Exposes a `render(gl, t, spectrum)` hook. The renderer drives a fallback
built-in scene if this file is absent, so this is optional polish.
"""
import math


def render(gl, t, spectrum):
    gl.glClearColor(0.02, 0.02, 0.06, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    gl.glBegin(gl.GL_POINTS)
    for i in range(200):
        x = (i / 200.0) * 2 - 1
        y = math.sin(t + i * 0.2) * 0.4
        gl.glColor3f(0.3 + i / 200.0, 0.5, 1.0)
        gl.glVertex2f(x, y)
    gl.glEnd()
