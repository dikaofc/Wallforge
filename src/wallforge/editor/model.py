"""Editor: in-memory project model.

A project is a set of layers, each with keyframed properties across a timeline.
The editor renders a live preview by evaluating the layer stack at the current
playhead time and drawing it on a QOpenGLWidget. Export writes a self-contained
interactive wallpaper (scene.py + manifest.json) that the runtime can load.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Keyframe:
    t: float                 # seconds
    value: Any


@dataclass
class Layer:
    id: int
    name: str
    type: str                # background | image | text | particle
    enabled: bool = True
    props: dict = field(default_factory=dict)
    keyframes: dict = field(default_factory=dict)  # prop_name -> list[Keyframe]

    def prop_at(self, name: str, t: float):
        if name in self.keyframes and self.keyframes[name]:
            kfs = sorted(self.keyframes[name], key=lambda k: k.t)
            if t <= kfs[0].t:
                return kfs[0].value
            if t >= kfs[-1].t:
                return kfs[-1].value
            for a, b in zip(kfs, kfs[1:]):
                if a.t <= t <= b.t:
                    span = (b.t - a.t) or 1
                    f = (t - a.t) / span
                    try:
                        return a.value + (b.value - a.value) * f
                    except TypeError:
                        return b.value
        return self.props.get(name)


@dataclass
class EditorProject:
    name: str = "Untitled"
    duration: float = 30.0
    fps: int = 60
    width: int = 1920
    height: int = 1080
    background: tuple = (10, 10, 20)
    layers: list[Layer] = field(default_factory=list)
    _next_id: int = 1

    def add_layer(self, type_: str, name: str = "") -> Layer:
        layer = Layer(id=self._next_id, name=name or type_.capitalize(),
                      type=type_)
        self._next_id += 1
        self.layers.append(layer)
        return layer

    def remove_layer(self, layer_id: int) -> None:
        self.layers = [l for l in self.layers if l.id != layer_id]

    def move_layer(self, layer_id: int, up: bool) -> None:
        idx = next((i for i, l in enumerate(self.layers) if l.id == layer_id), None)
        if idx is None:
            return
        j = idx - 1 if up else idx + 1
        if 0 <= j < len(self.layers):
            self.layers[idx], self.layers[j] = self.layers[j], self.layers[idx]

    def to_dict(self) -> dict:
        return {
            "name": self.name, "duration": self.duration, "fps": self.fps,
            "width": self.width, "height": self.height,
            "background": list(self.background),
            "layers": [
                {
                    "id": l.id, "name": l.name, "type": l.type,
                    "enabled": l.enabled, "props": l.props,
                    "keyframes": {k: [{"t": kf.t, "value": kf.value}
                                     for kf in v]
                                  for k, v in l.keyframes.items()},
                } for l in self.layers
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EditorProject":
        p = cls(name=d.get("name", "Untitled"),
                duration=d.get("duration", 30.0),
                fps=d.get("fps", 60),
                width=d.get("width", 1920),
                height=d.get("height", 1080),
                background=tuple(d.get("background", (10, 10, 20))))
        for l in d.get("layers", []):
            layer = Layer(id=l["id"], name=l["name"], type=l["type"],
                          enabled=l.get("enabled", True),
                          props=l.get("props", {}),
                          keyframes={k: [Keyframe(kf["t"], kf["value"])
                                         for kf in v]
                                    for k, v in l.get("keyframes", {}).items()})
            p.layers.append(layer)
            p._next_id = max(p._next_id, l["id"] + 1)
        return p

    # ---- export to a runtime wallpaper ---------------------------------
    def export_wallpaper(self, folder: str) -> None:
        from pathlib import Path
        f = Path(folder)
        f.mkdir(parents=True, exist_ok=True)
        (f / "content").mkdir(exist_ok=True)
        # Serialise the project so the runtime scene can replay it.
        (f / "content" / "project.json").write_text(
            json.dumps(self.to_dict()), encoding="utf-8")
        scene = f / "content" / "scene.py"
        scene.write_text(_SCENE_TEMPLATE, encoding="utf-8")
        manifest = {
            "name": self.name, "author": "Wallforge Editor",
            "type": "interactive", "version": "1.0",
            "resolution": f"{self.width}x{self.height}",
            "fps": self.fps, "audio": False,
            "entry": "content/scene.py", "tags": ["editor"],
        }
        (f / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                         encoding="utf-8")


_SCENE_TEMPLATE = '''\
"""Auto-generated by Wallforge Editor. Replays an EditorProject timeline."""
import json
from pathlib import Path
from wallforge.editor.runtime import render_project


def load_project():
    here = Path(__file__).parent
    data = json.loads((here / "project.json").read_text(encoding="utf-8"))
    return data


PROJECT = load_project()


def render(gl, t, spectrum):
    render_project(gl, PROJECT, t)
'''
