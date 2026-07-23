"""Integration tests for live-wire snapping in the 2D object viewer.

The pure algorithm lives in tests/test_livewire.py; here we check that the
ObjectViewer2D wiring -- grayscale extraction, lazy cost-map build, edge snapping
and the enable/disable toggle -- behaves on a real widget with an in-memory
image, plus the ObjectDialog "Snap" button forwarding.
"""

import os
import sys

import pytest
from PyQt5.QtGui import QImage, QPixmap, qRgb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.viewers.object_viewer_2d import MODE, ObjectViewer2D


def _bar_pixmap(w=40, h=40, bar_x=20, bar_w=3):
    """A dark image with a bright vertical bar (a strong edge) at ``bar_x``."""
    img = QImage(w, h, QImage.Format_RGB32)
    img.fill(qRgb(0, 0, 0))
    for y in range(h):
        for x in range(bar_x, min(bar_x + bar_w, w)):
            img.setPixel(x, y, qRgb(255, 255, 255))
    return QPixmap.fromImage(img)


@pytest.fixture
def viewer(qtbot):
    v = ObjectViewer2D()
    qtbot.addWidget(v)
    return v


class TestPixmapToGray:
    def test_shape_and_bar_are_bright(self, viewer):
        pixmap = _bar_pixmap(w=40, h=30, bar_x=20)
        gray = viewer._pixmap_to_gray(pixmap)
        assert gray.shape == (30, 40)  # (rows=y, cols=x)
        assert gray[:, 21].mean() > 200  # the bar is bright
        assert gray[:, 0].mean() < 20  # the background is dark


class TestLivewireToggle:
    def test_enable_and_disable(self, viewer):
        assert viewer.livewire_enabled is False
        viewer.set_livewire_enabled(True)
        assert viewer.livewire_enabled is True
        viewer.livewire_preview = [[1, 1], [2, 2]]
        viewer.set_livewire_enabled(False)
        assert viewer.livewire_enabled is False
        assert viewer.livewire_preview == []

    def test_setting_image_resets_cost_map(self, viewer, tmp_path):
        viewer.orig_pixmap = _bar_pixmap()
        viewer._ensure_livewire()
        assert viewer._livewire is not None
        # Loading a new image drops the cached cost map.
        path = str(tmp_path / "x.png")
        _bar_pixmap().save(path)
        viewer.set_image(path)
        assert viewer._livewire is None

    def test_leaving_curve_mode_clears_preview(self, viewer):
        viewer.livewire_preview = [[1, 1], [2, 2]]
        viewer.set_mode(MODE["EDIT_LANDMARK"])
        assert viewer.livewire_preview == []


class TestLivewireSegment:
    def test_ensure_livewire_builds_from_orig_pixmap(self, viewer):
        assert viewer._ensure_livewire() is None  # no image yet
        viewer.orig_pixmap = _bar_pixmap()
        wire = viewer._ensure_livewire()
        assert wire is not None
        assert viewer._ensure_livewire() is wire  # cached, not rebuilt

    def test_segment_snaps_to_the_bar(self, viewer):
        viewer.orig_pixmap = _bar_pixmap(w=40, h=40, bar_x=20)
        # Seed and target on the bar's edge; snapped path hugs it.
        path = viewer._livewire_segment([21, 2], [21, 37])
        xs = [p[0] for p in path]
        assert path[0] == [21, 2]
        assert path[-1] == [21, 37]
        assert all(abs(x - 21) <= 2 for x in xs)

    def test_segment_without_image_is_straight(self, viewer):
        viewer.orig_pixmap = None
        seg = viewer._livewire_segment([1, 2], [3, 4])
        assert seg == [[1, 2], [3, 4]]


class TestDialogSnapButton:
    def test_button_forwards_to_viewer(self, qtbot):
        # Build a minimal dialog stub: the real Snap slot toggling a real viewer.
        from PyQt5.QtWidgets import QPushButton

        from dialogs.object_dialog import ObjectDialog

        dlg = ObjectDialog.__new__(ObjectDialog)
        dlg.object_view = ObjectViewer2D()
        qtbot.addWidget(dlg.object_view)
        dlg.object_view.set_mode(MODE["EDIT_CURVE"])  # already in curve mode
        dlg.btnCurveSnap = QPushButton()
        dlg.btnCurveSnap.setCheckable(True)
        dlg.btnCurveSnap.setChecked(True)

        dlg.btnCurveSnap_clicked()
        assert dlg.object_view.livewire_enabled is True

        dlg.btnCurveSnap.setChecked(False)
        dlg.btnCurveSnap_clicked()
        assert dlg.object_view.livewire_enabled is False
