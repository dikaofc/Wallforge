"""Editor runtime: render an exported EditorProject dict on an OpenGL context.

Used by the exported scene.py (and optionally by the editor preview itself).
Kept free of PySide/Qt imports so it works inside the frozen wallpaper runtime.
"""
from __future__ import annotations

import math


def _gl_color(c):
    return (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)


def render_project(gl, project: dict, t: float) -> None:
    w, h = project.get("width", 1920), project.get("height", 1080)
    bg = project.get("background", (10, 10, 20))
    gl.glClearColor(*_gl_color(bg), 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    aspect = w / h

    for layer in project.get("layers", []):
        if not layer.get("enabled", True):
            continue
        ltype = layer["type"]
        props = layer.get("props", {})
        kfs = layer.get("keyframes", {})
        # helper to read a (possibly keyframed) prop
        def p(name, default=None):
            if name in kfs and kfs[name]:
                # simple linear interp between keyframes
                pts = sorted(kfs[name], key=lambda k: k["t"])
                if t <= pts[0]["t"]:
                    return pts[0]["value"]
                if t >= pts[-1]["t"]:
                    return pts[-1]["value"]
                for a, b in zip(pts, pts[1:]):
                    if a["t"] <= t <= b["t"]:
                        span = (b["t"] - a["t"]) or 1
                        f = (t - a["t"]) / span
                        try:
                            return a["value"] + (b["value"] - a["value"]) * f
                        except TypeError:
                            return b["value"]
            return props.get(name, default)

        if ltype == "background":
            continue
        elif ltype == "image":
            src = props.get("source")
            x, y, ww, hh = p("x", 0), p("y", 0), p("width", w), p("height", h)
            if src:
                _image(gl, src, x, y, ww, hh)
            else:
                col = p("color", (40, 80, 160))
                _rect(gl, x, y, ww, hh, col)
        elif ltype == "text":
            # Text is approximated with a centred quad tinted by colour.
            col = p("color", (255, 255, 255))
            _rect(gl, w * 0.2, h * 0.4, w * 0.6, h * 0.2, col)
        elif ltype == "particle":
            n = int(p("count", 200))
            speed = p("speed", 1.0)
            _particles(gl, n, t * speed, p("color", (120, 180, 255)))


def _image(gl, path: str, x, y, w, h):
    """Draw an image file as a textured quad (cached per path)."""
    tex = _image._cache.get(path)
    if tex is None:
        try:
            from PIL import Image
            import numpy as np
            img = Image.open(path).convert("RGBA").resize((512, 512))
            arr = np.asarray(img, dtype="uint8")
            tid = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, tid)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, arr.shape[1],
                            arr.shape[0], 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, arr)
            tex = (tid, arr.shape[1], arr.shape[0])
            _image._cache[path] = tex
        except Exception:
            return
    tid, tw, th = tex
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tid)
    gl.glColor3f(1, 1, 1)
    gl.glBegin(gl.GL_QUADS)
    gl.glTexCoord2f(0, 0); gl.glVertex2f(_ndc_x(x, 1920), _ndc_y(y, 1080))
    gl.glTexCoord2f(1, 0); gl.glVertex2f(_ndc_x(x + w, 1920), _ndc_y(y, 1080))
    gl.glTexCoord2f(1, 1); gl.glVertex2f(_ndc_x(x + w, 1920), _ndc_y(y + h, 1080))
    gl.glTexCoord2f(0, 1); gl.glVertex2f(_ndc_x(x, 1920), _ndc_y(y + h, 1080))
    gl.glEnd()
    gl.glDisable(gl.GL_TEXTURE_2D)


_image._cache = {}


def _rect(gl, x, y, w, h, color):
    gl.glColor3f(*_gl_color(color))
    gl.glBegin(gl.GL_QUADS)
    gl.glVertex2f(_ndc_x(x, 1920), _ndc_y(y, 1080))
    gl.glVertex2f(_ndc_x(x + w, 1920), _ndc_y(y, 1080))
    gl.glVertex2f(_ndc_x(x + w, 1920), _ndc_y(y + h, 1080))
    gl.glVertex2f(_ndc_x(x, 1920), _ndc_y(y + h, 1080))
    gl.glEnd()


def _ndc_x(x, w):
    return x / w * 2 - 1


def _ndc_y(y, h):
    return 1 - y / h * 2


def _particles(gl, n, t, color):
    gl.glColor3f(*_gl_color(color))
    gl.glBegin(gl.GL_POINTS)
    for i in range(n):
        px = ((i * 0.6180339 + t * 0.1) % 1.0) * 2 - 1
        py = ((i * 0.754877 + math.sin(t + i) * 0.05) % 1.0) * 2 - 1
        gl.glVertex2f(px, py)
    gl.glEnd()
