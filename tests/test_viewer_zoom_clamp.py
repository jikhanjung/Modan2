"""Zoom clamp in ObjectViewer2D.adjust_scale.

The zoom scale grows near-exponentially under repeated zoom-in and the render
pixmap is allocated proportionally to it; without a clamp a burst of wheel
events requested a multi-GB allocation and took the process down with a kernel
OOM (devlog 220). The clamp caps the scaled pixmap's longer side.
"""

import os
import sys

from PyQt5.QtGui import QImage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import components.viewers.object_viewer_2d as ov2d
from components.viewers.object_viewer_2d import ObjectViewer2D


def _write_png(path, w, h):
    img = QImage(w, h, QImage.Format_RGB32)
    img.fill(0xFF808080)
    assert img.save(str(path), "PNG")
    return str(path)


def _zoomed_viewer(qtbot, tmp_path, zoom_steps):
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    viewer.resize(400, 400)
    viewer.set_image(_write_png(tmp_path / "img.png", 400, 200))
    viewer.calculate_resize()
    for _ in range(zoom_steps):
        viewer.adjust_scale(0.2, recurse=False)
    return viewer


def test_repeated_zoom_in_is_clamped(qtbot, tmp_path, monkeypatch):
    """60 zoom-in steps (the OOM scenario) stay bounded by the pixmap cap."""
    monkeypatch.setattr(ov2d, "MAX_SCALED_PIXMAP_DIM", 512)
    viewer = _zoomed_viewer(qtbot, tmp_path, 60)

    assert max(viewer.curr_pixmap.width(), viewer.curr_pixmap.height()) <= 512
    # the scale itself is pinned, not just the pixmap
    expected_max_scale = 512 * viewer.image_canvas_ratio / 400
    assert viewer.scale <= expected_max_scale


def test_zoom_below_cap_is_untouched(qtbot, tmp_path):
    """Normal zooming far below the cap behaves exactly as before."""
    viewer = _zoomed_viewer(qtbot, tmp_path, 2)  # 1.0 -> 1.2 -> 1.4
    assert viewer.scale == 1.4


def test_clamp_never_goes_below_fit_scale(qtbot, tmp_path, monkeypatch):
    """A cap smaller than the fit size must not shrink the view below fit."""
    monkeypatch.setattr(ov2d, "MAX_SCALED_PIXMAP_DIM", 10)
    viewer = _zoomed_viewer(qtbot, tmp_path, 5)
    assert viewer.scale >= 1.0
