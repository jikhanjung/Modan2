"""Tests for the oversized-image downscaling in ObjectViewer2D.set_image.

Big images are decoded to a downscaled *render source* for speed, but the TRUE
pixel dimensions must be preserved so landmark coordinate math (landmarks are
stored in original-image pixels) is unaffected.
"""

from PyQt5.QtGui import QImage

import components.viewers.object_viewer_2d as ov2d
from components.viewers.object_viewer_2d import ObjectViewer2D


def _write_png(path, w, h):
    """Write a solid w x h PNG and return its path string."""
    img = QImage(w, h, QImage.Format_RGB32)
    img.fill(0xFF808080)
    assert img.save(str(path), "PNG")
    return str(path)


def test_small_image_not_downscaled(qtbot, tmp_path):
    """An image under the cap loads full-resolution (no behavior change)."""
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    viewer.set_image(_write_png(tmp_path / "small.png", 200, 120))

    assert (viewer.orig_width, viewer.orig_height) == (200, 120)
    # render source == true size (not downscaled)
    assert (viewer.orig_pixmap.width(), viewer.orig_pixmap.height()) == (200, 120)


def test_large_image_downscaled_but_true_dims_preserved(qtbot, tmp_path, monkeypatch):
    """An oversized image gets a downscaled render source, yet orig_width/height
    stay at the TRUE pixel dimensions used by all coordinate math."""
    monkeypatch.setattr(ov2d, "MAX_RENDER_DIM", 100)
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    viewer.set_image(_write_png(tmp_path / "big.png", 400, 200))

    # true dimensions preserved
    assert (viewer.orig_width, viewer.orig_height) == (400, 200)
    # render source capped at MAX_RENDER_DIM on the longer side, aspect kept
    assert max(viewer.orig_pixmap.width(), viewer.orig_pixmap.height()) <= 100
    assert viewer.orig_pixmap.width() == 100
    assert viewer.orig_pixmap.height() == 50


def test_downscaled_image_coordinate_mapping_uses_true_dims(qtbot, tmp_path, monkeypatch):
    """calculate_resize / _2imgx must key off the true dims, so a downscaled
    render source yields exactly the same image<->canvas mapping as a full load."""
    monkeypatch.setattr(ov2d, "MAX_RENDER_DIM", 100)
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    viewer.resize(400, 400)
    viewer.set_image(_write_png(tmp_path / "big.png", 800, 400))
    viewer.calculate_resize()

    # ratio is computed from the TRUE width (800), not the ~100px render source.
    assert viewer.orig_width == 800
    assert viewer.image_canvas_ratio == 800 / viewer.width()

    # image<->canvas round-trip at scale 1, no pan: a click at the canvas position
    # of true-image x=400 maps back to ~400 (within rounding).
    viewer.scale = 1.0
    viewer.pan_x = viewer.pan_y = 0
    viewer.temp_pan_x = viewer.temp_pan_y = 0
    canvas_x = viewer._2canx(400)
    assert abs(viewer._2imgx(canvas_x) - 400) <= 1


def test_zoom_in_loads_full_resolution(qtbot, tmp_path, monkeypatch):
    """Zooming in far enough to upscale the downscaled source swaps in the
    full-resolution image; coordinate math (true dims) is unchanged."""
    monkeypatch.setattr(ov2d, "MAX_RENDER_DIM", 100)
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    viewer.resize(200, 200)
    viewer.set_image(_write_png(tmp_path / "big.png", 800, 400))
    viewer.calculate_resize()

    assert viewer._render_downscaled is True
    assert viewer.orig_pixmap.width() == 100  # downscaled render source
    true_w, true_h = viewer.orig_width, viewer.orig_height

    # Zoom in a lot so the display width exceeds the 100px render source.
    for _ in range(60):
        viewer.adjust_scale(0.2, recurse=False)

    assert viewer._render_downscaled is False
    assert viewer.orig_pixmap.width() == 800  # full-resolution now loaded
    # true dims (coordinate reference) untouched by the swap
    assert (viewer.orig_width, viewer.orig_height) == (true_w, true_h)


def test_zoom_stays_downscaled_when_not_upscaling(qtbot, tmp_path, monkeypatch):
    """At low zoom the downscaled source is enough; no full-res load happens."""
    monkeypatch.setattr(ov2d, "MAX_RENDER_DIM", 100)
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    viewer.resize(200, 200)
    viewer.set_image(_write_png(tmp_path / "big.png", 800, 400))
    viewer.calculate_resize()

    viewer._ensure_render_resolution()  # at fit, no upscale needed
    assert viewer._render_downscaled is True
    assert viewer.orig_pixmap.width() == 100


def test_null_image_sets_sentinel_dims(qtbot, tmp_path):
    """A missing/corrupt image doesn't crash and marks dims invalid."""
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    viewer.set_image(str(tmp_path / "does_not_exist.png"))
    assert viewer.orig_pixmap.isNull()
    assert (viewer.orig_width, viewer.orig_height) == (-1, -1)
