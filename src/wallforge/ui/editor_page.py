"""Editor page: assets panel, layer list, properties, timeline + export.

Supports undo/redo (snapshot-based) and adding real image assets as layers.
Emits export_requested with a target folder so the main app can write the
wallpaper and refresh the library.
"""
from __future__ import annotations

import pickle
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFileDialog, QHBoxLayout,
                               QInputDialog, QLabel, QListWidget, QListWidgetItem,
                               QPushButton, QSlider, QVBoxLayout, QWidget)

from ..core.logger import setup_logger
from ..editor.model import EditorProject, Layer
from .editor_canvas import EditorCanvas

log = setup_logger("wallforge.editor.page")


class EditorPage(QWidget):
    export_requested = Signal(str)

    def __init__(self, manager=None) -> None:
        super().__init__()
        self.manager = manager
        self.project = EditorProject()
        self._undo_stack: list[bytes] = []
        self._redo_stack: list[bytes] = []
        self._build_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self.playing = False

    # ---- undo / redo ---------------------------------------------------
    def _snapshot(self) -> bytes:
        return pickle.dumps(self.project.to_dict())

    def _push(self) -> None:
        self._undo_stack.append(self._snapshot())
        self._redo_stack.clear()

    def _restore(self, data: bytes) -> None:
        d = pickle.loads(data)
        self.project = EditorProject.from_dict(d)
        self.canvas.project = self.project
        self._refresh_layers()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(self._snapshot())
        self._restore(self._undo_stack.pop())

    def redo(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(self._snapshot())
        self._restore(self._redo_stack.pop())

    # ---- UI ------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QHBoxLayout(self)

        # Left: assets + layers
        left = QVBoxLayout()
        left.addWidget(QLabel("ASSETS"))
        add_bg = QPushButton("+ Background")
        add_img = QPushButton("+ Image")
        add_img_real = QPushButton("+ Image from file…")
        add_txt = QPushButton("+ Text")
        add_part = QPushButton("+ Particle")
        for b, fn in ((add_bg, lambda: self._add("background")),
                      (add_img, lambda: self._add("image")),
                      (add_img_real, self._add_image_file),
                      (add_txt, lambda: self._add("text")),
                      (add_part, lambda: self._add("particle"))):
            b.clicked.connect(fn)
            left.addWidget(b)
        left.addWidget(QLabel("LAYERS"))
        self.layer_list = QListWidget()
        self.layer_list.currentRowChanged.connect(self._on_layer_select)
        left.addWidget(self.layer_list)
        lrow = QHBoxLayout()
        up = QPushButton("Up"); down = QPushButton("Down")
        rm = QPushButton("Delete")
        undo = QPushButton("Undo"); red = QPushButton("Redo")
        up.clicked.connect(lambda: self._move(up=True))
        down.clicked.connect(lambda: self._move(up=False))
        rm.clicked.connect(self._remove)
        undo.clicked.connect(self.undo)
        red.clicked.connect(self.redo)
        lrow.addWidget(up); lrow.addWidget(down); lrow.addWidget(rm)
        left.addLayout(lrow)
        urow = QHBoxLayout()
        urow.addWidget(undo); urow.addWidget(red)
        left.addLayout(urow)
        left.addStretch()
        root.addLayout(left, 0)

        # Centre: canvas + timeline
        centre = QVBoxLayout()
        self.canvas = EditorCanvas(self.project)
        self.canvas.setMinimumSize(480, 270)
        centre.addWidget(self.canvas, 1)
        tl = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self._toggle_play)
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, int(self.project.duration * 100))
        self.time_slider.valueChanged.connect(self._on_time)
        tl.addWidget(self.play_btn)
        tl.addWidget(self.time_slider)
        centre.addLayout(tl)
        root.addLayout(centre, 1)

        # Right: properties + export
        right = QVBoxLayout()
        right.addWidget(QLabel("PROPERTIES"))
        self.props = QLabel("(select a layer)")
        self.props.setWordWrap(True)
        right.addWidget(self.props)
        self.export_btn = QPushButton("Export wallpaper")
        self.export_btn.setStyleSheet("background:#2d6cdf;color:#fff;padding:8px;")
        self.export_btn.clicked.connect(self._export)
        right.addWidget(self.export_btn)
        right.addStretch()
        root.addLayout(right, 0)

        # Keyboard shortcuts for undo/redo.
        from PySide6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self.redo)

    # ---- layer ops -----------------------------------------------------
    def _add(self, type_: str) -> None:
        self._push()
        layer = self.project.add_layer(type_)
        if type_ == "image":
            layer.props = {"x": 200, "y": 200, "width": 800, "height": 600,
                          "color": [40, 80, 160]}
        elif type_ == "text":
            layer.props = {"x": 200, "y": 400, "width": 800, "height": 200,
                          "color": [255, 255, 255]}
        elif type_ == "particle":
            layer.props = {"count": 200, "speed": 1.0, "color": [120, 180, 255]}
        self._refresh_layers()

    def _add_image_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select image", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if not path:
            return
        self._push()
        layer = self.project.add_layer("image", Path(path).stem)
        layer.props = {"x": 100, "y": 100, "width": 800, "height": 600,
                       "source": path, "color": [255, 255, 255]}
        self._refresh_layers()

    def _refresh_layers(self) -> None:
        self.layer_list.clear()
        for l in self.project.layers:
            item = QListWidgetItem(("☑ " if l.enabled else "☐ ") + l.name)
            item.setData(Qt.UserRole, l.id)
            self.layer_list.addItem(item)

    def _on_layer_select(self, row: int) -> None:
        if 0 <= row < len(self.project.layers):
            l = self.project.layers[row]
            self.props.setText(
                f"id={l.id}\ntype={l.type}\nprops={l.props}\n"
                f"keyframes={list(l.keyframes.keys())}")

    def _move(self, up: bool) -> None:
        item = self.layer_list.currentItem()
        if not item:
            return
        self._push()
        self.project.move_layer(item.data(Qt.UserRole), up)
        self._refresh_layers()

    def _remove(self) -> None:
        item = self.layer_list.currentItem()
        if not item:
            return
        self._push()
        self.project.remove_layer(item.data(Qt.UserRole))
        self._refresh_layers()

    # ---- timeline ------------------------------------------------------
    def _toggle_play(self) -> None:
        self.playing = not self.playing
        self.play_btn.setText("Pause" if self.playing else "Play")
        if self.playing:
            self._timer.start(16)
        else:
            self._timer.stop()

    def _tick(self) -> None:
        cur = self.time_slider.value() / 100.0
        cur += 1 / self.project.fps
        if cur > self.project.duration:
            cur = 0
        self.time_slider.setValue(int(cur * 100))

    def _on_time(self, v: int) -> None:
        self.canvas.set_time(v / 100.0)

    # ---- export --------------------------------------------------------
    def _export(self) -> None:
        name, ok = QInputDialog.getText(self, "Export", "Wallpaper name:")
        if not ok or not name:
            return
        from ..core.config import Config
        target = Path(Config.load().wallpapers_dir) / name.replace(" ", "_")
        self.project.name = name
        try:
            self.project.export_wallpaper(str(target))
            self.export_requested.emit(str(target))
            self.props.setText(f"Exported to:\n{target}")
        except Exception as exc:
            log.error("export failed: %s", exc)
            self.props.setText(f"Export failed: {exc}")
