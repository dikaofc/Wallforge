"""Tests for the editor model: layers, keyframe interpolation, export."""
from __future__ import annotations

from pathlib import Path

from src.wallforge.editor.model import EditorProject, Layer, Keyframe


def test_add_and_remove_layer():
    p = EditorProject()
    l = p.add_layer("particle", "Stars")
    assert l.id == 1 and l.name == "Stars"
    p.remove_layer(l.id)
    assert p.layers == []


def test_keyframe_interpolation():
    p = EditorProject()
    l = p.add_layer("image")
    l.keyframes["x"] = [Keyframe(0.0, 0.0), Keyframe(10.0, 100.0)]
    assert l.prop_at("x", 0.0) == 0.0
    assert l.prop_at("x", 10.0) == 100.0
    assert l.prop_at("x", 5.0) == 50.0
    assert l.prop_at("x", 20.0) == 100.0


def test_export_writes_wallpaper(tmp_path):
    p = EditorProject(name="My WP")
    p.add_layer("background")
    p.add_layer("particle")
    p.export_wallpaper(str(tmp_path / "out"))
    assert (tmp_path / "out" / "manifest.json").exists()
    assert (tmp_path / "out" / "content" / "scene.py").exists()
    assert (tmp_path / "out" / "content" / "project.json").exists()


def test_runtime_render_runs():
    from src.wallforge.editor.runtime import render_project
    p = EditorProject()
    p.add_layer("particle")
    from src.wallforge.editor.runtime import render_project as rp
    # Provide a stand-in GL whose attributes are no-op callables.
    class FakeGL:
        def __getattr__(self, k):
            return lambda *a, **k: None
    rp(FakeGL(), p.to_dict(), 1.0)
