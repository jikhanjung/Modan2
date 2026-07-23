"""Integration tests for live-wire snapping in the 2D object viewer.

The pure algorithm lives in tests/test_livewire.py; here we check that the
ObjectViewer2D wiring -- grayscale extraction, lazy cost-map build, edge snapping
and the enable/disable toggle -- behaves on a real widget with an in-memory
image, plus the ObjectDialog "Snap" button forwarding.
"""

import os
import sys
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QImage, QKeyEvent, QPixmap, qRgb

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


class TestAcceptCancel:
    def _curve_viewer(self, qtbot):
        v = ObjectViewer2D()
        qtbot.addWidget(v)
        v.set_mode(MODE["EDIT_CURVE"])
        v.object_dialog = Mock()
        v.current_curve_points = [[0, 0], [5, 5], [10, 10]]
        return v

    def test_enter_accepts_and_finishes(self, qtbot):
        v = self._curve_viewer(qtbot)
        v.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier))
        # No snap anchors were recorded, so anchors is None (hand-traced).
        v.object_dialog.finish_curve.assert_called_once_with([[0, 0], [5, 5], [10, 10]], None)
        assert v.current_curve_points == []

    def test_escape_cancels_without_finishing(self, qtbot):
        v = self._curve_viewer(qtbot)
        v.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier))
        v.object_dialog.finish_curve.assert_not_called()
        assert v.current_curve_points == []
        assert v.livewire_preview == []

    def test_accept_needs_two_points(self, qtbot):
        v = self._curve_viewer(qtbot)
        v.current_curve_points = [[0, 0]]  # a single point is not a curve
        accepted = v._accept_current_curve()
        assert accepted is True  # the trace is consumed
        v.object_dialog.finish_curve.assert_not_called()  # but nothing committed

    def test_keys_ignored_outside_curve_mode(self, qtbot):
        v = self._curve_viewer(qtbot)
        v.set_mode(MODE["EDIT_LANDMARK"])
        v.object_dialog = Mock()
        v.current_curve_points = [[0, 0], [5, 5]]
        # Not in curve mode -> the helper reports nothing to accept.
        assert v._accept_current_curve() is False


class TestSnapAnchorsEditable:
    def _snap_viewer(self, qtbot):
        v = ObjectViewer2D()
        qtbot.addWidget(v)
        v.orig_pixmap = _bar_pixmap(w=40, h=40, bar_x=20)
        v.set_mode(MODE["EDIT_CURVE"])
        v.livewire_enabled = True
        v.object_dialog = Mock()
        v.object_dialog.curve_raw_map = {}
        v.object_dialog.curve_anchor_map = {}
        return v

    def test_snap_trace_records_sparse_anchors(self, qtbot):
        v = self._snap_viewer(qtbot)
        # Simulate the snap-click bookkeeping directly: seed, then a snapped step.
        v.current_curve_points = [[21, 5]]
        v.current_curve_anchors = [[21, 5]]
        seg = v._livewire_segment([21, 5], [21, 35])
        v.current_curve_points.extend(seg[1:])
        v.current_curve_anchors.append([21, 35])
        # Dense path has many points; anchors keep just the two clicks.
        assert len(v.current_curve_points) > len(v.current_curve_anchors)
        assert v.current_curve_anchors == [[21, 5], [21, 35]]

    def test_editpoints_are_anchors_when_present(self, qtbot):
        v = self._snap_viewer(qtbot)
        v.object_dialog.curve_raw_map = {"curve1": [[0, 0], [1, 0], [2, 0], [3, 0]]}
        v.object_dialog.curve_anchor_map = {"curve1": [[0, 0], [3, 0]]}
        assert v._curve_editpoints("curve1") == [[0, 0], [3, 0]]  # anchors, not dense
        v.selected_curve_id = "curve1"
        assert v._selected_curve_raw() == [[0, 0], [3, 0]]

    def test_editpoints_fall_back_to_raw_for_hand_traced(self, qtbot):
        v = self._snap_viewer(qtbot)
        v.object_dialog.curve_raw_map = {"curve1": [[0, 0], [5, 5], [9, 9]]}
        v.object_dialog.curve_anchor_map = {}  # no anchors -> raw is editable
        assert v._curve_editpoints("curve1") == [[0, 0], [5, 5], [9, 9]]

    def test_editing_an_anchor_resnaps_the_dense_trace(self, qtbot):
        v = self._snap_viewer(qtbot)
        v.object_dialog.curve_raw_map = {"curve1": [[21, 5], [21, 35]]}
        v.object_dialog.curve_anchor_map = {"curve1": [[21, 5], [21, 35]]}
        v.selected_curve_id = "curve1"
        # Move the lower anchor, then re-snap: the rebuilt trace runs between the
        # anchors along the bar and has more points than the two anchors.
        v.object_dialog.curve_anchor_map["curve1"][1] = [21, 30]
        v._resnap_selected_curve()
        dense = v.object_dialog.curve_raw_map["curve1"]
        assert len(dense) > 2
        assert dense[0] == [21, 5]
        assert dense[-1] == [21, 30]

    def test_resnap_noop_for_hand_traced_curve(self, qtbot):
        v = self._snap_viewer(qtbot)
        raw = [[0, 0], [5, 5], [9, 9]]
        v.object_dialog.curve_raw_map = {"curve1": raw}
        v.object_dialog.curve_anchor_map = {}
        v.selected_curve_id = "curve1"
        v._resnap_selected_curve()
        assert v.object_dialog.curve_raw_map["curve1"] == raw  # untouched

    def test_insert_anchor_orders_by_position_along_dense_trace(self, qtbot):
        v = self._snap_viewer(qtbot)
        # A curved dense trace bulging right, with anchors at its two ends.
        dense = [[10, 0], [16, 5], [18, 10], [16, 15], [10, 20]]
        v.object_dialog.curve_raw_map = {"curve1": dense}
        v.object_dialog.curve_anchor_map = {"curve1": [[10, 0], [10, 20]]}
        v.selected_curve_id = "curve1"
        # Click on the bulge (mid-curve). The new anchor must land *between* the
        # two existing anchors, not appended at the end.
        img_mid = [18, 10]
        idx = v._anchor_insert_index(dense, v.object_dialog.curve_anchor_map["curve1"], img_mid)
        assert idx == 1

    def test_dragging_anchor_resnaps_live(self, qtbot):
        v = self._snap_viewer(qtbot)
        v.object_dialog.curve_raw_map = {"curve1": [[21, 2], [21, 20], [21, 38]]}
        v.object_dialog.curve_anchor_map = {"curve1": [[21, 2], [21, 20], [21, 38]]}
        v.selected_curve_id = "curve1"
        before = [list(p) for p in v.object_dialog.curve_raw_map["curve1"]]
        # Simulate a drag step of the middle anchor with a live re-snap.
        v.moving_curve_point_index = 1
        v.object_dialog.curve_anchor_map["curve1"][1] = [21, 25]
        v._resnap_selected_curve(moving_index=1)
        after = v.object_dialog.curve_raw_map["curve1"]
        # The dense trace updated immediately (not only on release).
        assert after != before
        assert after[0] == [21, 2] and after[-1] == [21, 38]


class TestCurveHint:
    def test_hint_mentions_enter_and_esc(self, qtbot):
        v = ObjectViewer2D()
        qtbot.addWidget(v)
        assert "Enter" in v._curve_hint()
        assert "Esc" in v._curve_hint()

    def test_hint_changes_with_snap(self, qtbot):
        v = ObjectViewer2D()
        qtbot.addWidget(v)
        plain = v._curve_hint()
        v.livewire_enabled = True
        snap = v._curve_hint()
        assert snap != plain
        assert "Snap" in snap


class TestDialogSnapCheckbox:
    def _dlg(self, qtbot):
        from PyQt5.QtWidgets import QCheckBox

        from dialogs.object_dialog import ObjectDialog

        dlg = ObjectDialog.__new__(ObjectDialog)
        dlg.object_view = ObjectViewer2D()
        qtbot.addWidget(dlg.object_view)
        dlg.cbxSnapToCurve = QCheckBox()
        qtbot.addWidget(dlg.cbxSnapToCurve)
        return dlg

    def test_checkbox_forwards_to_viewer(self, qtbot):
        dlg = self._dlg(qtbot)
        dlg.cbxSnapToCurve.setChecked(True)
        dlg._apply_snap()
        assert dlg.object_view.livewire_enabled is True
        dlg.cbxSnapToCurve.setChecked(False)
        dlg._apply_snap()
        assert dlg.object_view.livewire_enabled is False

    def test_snap_enabled_only_in_curve_mode(self, qtbot):
        dlg = self._dlg(qtbot)
        dlg._set_snap_available(True)
        assert dlg.cbxSnapToCurve.isEnabled() is True
        dlg._set_snap_available(False)
        assert dlg.cbxSnapToCurve.isEnabled() is False

    def test_entering_curve_mode_applies_checkbox_state(self, qtbot):
        dlg = self._dlg(qtbot)
        dlg.cbxSnapToCurve.setChecked(True)
        dlg.object_view.livewire_enabled = False
        dlg._set_snap_available(True)  # entering curve mode
        assert dlg.object_view.livewire_enabled is True
