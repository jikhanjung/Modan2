"""Full-resolution render source in ObjectViewer2D ("Show Original").

The stored working copy defines the landmark coordinate space; the archived
original may be swapped in as the RENDER SOURCE only, so zooming shows the
original's detail while every coordinate stays in working-copy pixels.
"""

import os
import sys

from PyQt5.QtGui import QImage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.viewers.object_viewer_2d import ObjectViewer2D


def _write_png(path, w, h):
    img = QImage(w, h, QImage.Format_RGB32)
    img.fill(0xFF808080)
    assert img.save(str(path), "PNG")
    return str(path)


def _viewer_with_working_copy(qtbot, tmp_path):
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    viewer.resize(400, 400)
    viewer.set_image(_write_png(tmp_path / "working.png", 100, 50))
    viewer.calculate_resize()
    return viewer


def test_fullres_source_does_not_change_coordinate_space(qtbot, tmp_path):
    viewer = _viewer_with_working_copy(qtbot, tmp_path)
    ratio_before = viewer.image_canvas_ratio
    size_before = (viewer.curr_pixmap.width(), viewer.curr_pixmap.height())

    viewer.set_fullres_source(_write_png(tmp_path / "original.png", 400, 200))

    # coordinate space still keyed to the 100x50 working copy
    assert (viewer.orig_pixmap.width(), viewer.orig_pixmap.height()) == (100, 50)
    assert viewer.image_canvas_ratio == ratio_before
    # render pixmap same displayed size, just resampled from the original
    assert (viewer.curr_pixmap.width(), viewer.curr_pixmap.height()) == size_before
    assert viewer.fullres_pixmap.width() == 400


def test_fullres_source_off_returns_to_working_copy(qtbot, tmp_path):
    viewer = _viewer_with_working_copy(qtbot, tmp_path)
    viewer.set_fullres_source(_write_png(tmp_path / "original.png", 400, 200))
    viewer.set_fullres_source(None)
    assert viewer.fullres_pixmap is None
    assert viewer._render_source() is viewer.orig_pixmap


def test_loading_new_image_drops_fullres_source(qtbot, tmp_path):
    viewer = _viewer_with_working_copy(qtbot, tmp_path)
    viewer.set_fullres_source(_write_png(tmp_path / "original.png", 400, 200))
    viewer.set_image(_write_png(tmp_path / "other.png", 80, 40))
    assert viewer.fullres_pixmap is None


def test_unreadable_fullres_source_falls_back_to_working_copy(qtbot, tmp_path):
    viewer = _viewer_with_working_copy(qtbot, tmp_path)
    viewer.set_fullres_source(str(tmp_path / "missing.png"))
    assert viewer.fullres_pixmap is None
    assert viewer._render_source() is viewer.orig_pixmap
