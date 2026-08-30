"""Tests for editor undo/redo and image-layer export."""
from __future__ import annotations

from pathlib import Path

from src.wallforge.editor.model import EditorProject


def test_undo_redo_layer_add():
    p = EditorProject()
    # Simulate the page's snapshot-based undo by pickling to_dict.
    import pickle
    undo = [pickle.dumps(p.to_dict())]
    p.add_layer("particle")
    assert len(p.layers) == 1
    # undo
    p = EditorProject.from_dict(pickle.loads(undo.pop()))
    assert len(p.layers) == 0


def test_image_layer_export_carries_source(tmp_path):
    p = EditorProject(name="Img WP")
    img = tmp_path / "pic.png"
    img.write_bytes(b"fake")
    layer = p.add_layer("image", "pic")
    layer.props["source"] = str(img)
    p.export_wallpaper(str(tmp_path / "out"))
    import json
    data = json.loads((tmp_path / "out" / "content" / "project.json").read_text())
    img_layer = [l for l in data["layers"] if l["type"] == "image"][0]
    assert img_layer["props"]["source"] == str(img)
