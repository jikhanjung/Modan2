"""Characterization tests for the viewer rendering / interaction hot spots.

``ObjectViewer2D.paintEvent`` (cyclomatic complexity 56),
``ObjectViewer2D.mousePressEvent`` (33) and ``ObjectViewer3D.draw_object`` (39)
are the remaining complexity hot spots, and had little or no direct coverage.
These tests pin their *current* behavior so a later refactor can be shown to be
behavior-preserving.

Rendering is asserted as "every display-flag / edit-mode combination renders and
produces a valid pixmap", not as a pixel hash: exact pixels differ across the
Linux/Windows/macOS CI matrix (fonts, antialiasing), so an image golden would be
flaky. Interaction is asserted precisely, as the observable state transition of
each mousePressEvent branch.
"""

import sys

import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QMouseEvent

import MdModel as mm
from components.viewers.object_viewer_2d import ObjectViewer2D
from components.viewers.object_viewer_3d import ObjectViewer3D
from MdConstants import MODE

DISPLAY_FLAGS = [
    "show_index",
    "show_wireframe",
    "show_baseline",
    "show_polygon",
    "show_average",
    "show_curve",
    "show_semi_landmark",
    "show_landmark_name",
    "show_arrow",
]

EDIT_MODES = ["EDIT_LANDMARK", "READY_MOVE_LANDMARK", "MOVE_LANDMARK", "WIREFRAME", "CALIBRATION", "VIEW", "EDIT_CURVE"]


def _dataset_2d():
    return mm.MdDataset.create(
        dataset_name="CharDS2D",
        dimension=2,
        landmark_count=3,
        wireframe="1 2\n2 3",
        polygon="1 2 3",
    )


@pytest.fixture
def object_2d(mock_database):
    dataset = _dataset_2d()
    return mm.MdObject.create(
        dataset=dataset,
        object_name="O1",
        landmark_str="10.0,20.0\n30.0,40.0\n50.0,60.0",
    )


@pytest.fixture
def viewer_2d_obj(qtbot, object_2d):
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    viewer.resize(300, 300)
    viewer.set_object(object_2d)
    return viewer


def _press(viewer, button=Qt.LeftButton, pos=(50, 50)):
    """Deliver a mouse-press to the viewer the way Qt would."""
    event = QMouseEvent(QMouseEvent.MouseButtonPress, QPoint(*pos), button, button, Qt.NoModifier)
    viewer.mousePressEvent(event)


class TestPaintEventCharacterization:
    """ObjectViewer2D.paintEvent renders across its state combinations."""

    def test_empty_viewer_renders(self, qtbot):
        viewer = ObjectViewer2D()
        qtbot.addWidget(viewer)
        viewer.resize(200, 200)
        assert not viewer.grab().isNull()

    def test_viewer_with_object_renders(self, viewer_2d_obj):
        assert not viewer_2d_obj.grab().isNull()

    @pytest.mark.parametrize("flag", DISPLAY_FLAGS)
    @pytest.mark.parametrize("enabled", [True, False])
    def test_each_display_flag_renders(self, viewer_2d_obj, flag, enabled):
        setattr(viewer_2d_obj, flag, enabled)
        assert not viewer_2d_obj.grab().isNull()

    def test_all_display_flags_on_renders(self, viewer_2d_obj):
        for flag in DISPLAY_FLAGS:
            setattr(viewer_2d_obj, flag, True)
        assert not viewer_2d_obj.grab().isNull()

    @pytest.mark.parametrize("mode_name", EDIT_MODES)
    def test_each_edit_mode_renders(self, viewer_2d_obj, mode_name):
        if mode_name not in MODE:
            pytest.skip(f"MODE has no {mode_name}")
        viewer_2d_obj.edit_mode = MODE[mode_name]
        assert not viewer_2d_obj.grab().isNull()

    def test_dataset_path_renders(self, qtbot, mock_database):
        """With no object but a ds_ops set, paintEvent takes the dataset branch."""
        dataset = _dataset_2d()
        mm.MdObject.create(dataset=dataset, object_name="A", landmark_str="1.0,2.0\n3.0,4.0\n5.0,6.0")
        viewer = ObjectViewer2D()
        qtbot.addWidget(viewer)
        viewer.resize(300, 300)
        viewer.set_ds_ops(mm.MdDatasetOps(dataset))
        assert not viewer.grab().isNull()


class TestMousePressEventCharacterization:
    """Each mousePressEvent branch's observable state transition."""

    def test_right_button_enters_pan_mode(self, viewer_2d_obj):
        _press(viewer_2d_obj, Qt.RightButton)
        assert viewer_2d_obj.pan_mode == MODE["PAN"]

    def test_ready_move_landmark_becomes_move_landmark(self, viewer_2d_obj):
        viewer_2d_obj.edit_mode = MODE["READY_MOVE_LANDMARK"]
        _press(viewer_2d_obj, Qt.LeftButton)
        assert viewer_2d_obj.edit_mode == MODE["MOVE_LANDMARK"]

    def test_wireframe_click_latches_hovered_vertex_as_start(self, viewer_2d_obj):
        viewer_2d_obj.edit_mode = MODE["WIREFRAME"]
        viewer_2d_obj.wire_start_index = -1
        viewer_2d_obj.wire_hover_index = 2
        _press(viewer_2d_obj, Qt.LeftButton)
        assert viewer_2d_obj.wire_start_index == 2
        assert viewer_2d_obj.wire_hover_index == -1

    def test_wireframe_click_without_hover_changes_nothing(self, viewer_2d_obj):
        viewer_2d_obj.edit_mode = MODE["WIREFRAME"]
        viewer_2d_obj.wire_start_index = -1
        viewer_2d_obj.wire_hover_index = -1
        _press(viewer_2d_obj, Qt.LeftButton)
        assert viewer_2d_obj.wire_start_index == -1

    def test_calibration_click_records_image_coordinates(self, viewer_2d_obj):
        viewer_2d_obj.edit_mode = MODE["CALIBRATION"]
        viewer_2d_obj.mouse_curr_x = 40
        viewer_2d_obj.mouse_curr_y = 60
        _press(viewer_2d_obj, Qt.LeftButton)
        assert viewer_2d_obj.calibration_from_img_x == viewer_2d_obj._2imgx(40)
        assert viewer_2d_obj.calibration_from_img_y == viewer_2d_obj._2imgy(60)

    def test_edit_landmark_without_image_is_a_noop(self, viewer_2d_obj):
        """No image loaded: the handler returns before touching the dialog."""
        viewer_2d_obj.edit_mode = MODE["EDIT_LANDMARK"]
        viewer_2d_obj.orig_pixmap = None
        before = list(viewer_2d_obj.landmark_list)
        _press(viewer_2d_obj, Qt.LeftButton)
        assert list(viewer_2d_obj.landmark_list) == before


@pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason=(
        "needs a usable offscreen GL context: on headless Windows CI "
        "glGetIntegerv(GL_FRAMEBUFFER_BINDING) raises GLError 1282, and macOS CI "
        "segfaults (uncatchable, so it cannot be guarded with try/except)"
    ),
)
class TestDrawObject3DCharacterization:
    """ObjectViewer3D.draw_object runs inside a GL context for its flag combos."""

    @pytest.fixture
    def viewer_3d_obj(self, qtbot, mock_database):
        dataset = mm.MdDataset.create(
            dataset_name="CharDS3D",
            dimension=3,
            landmark_count=3,
            wireframe="1 2\n2 3",
            polygon="1 2 3",
        )
        obj = mm.MdObject.create(
            dataset=dataset,
            object_name="O3D",
            landmark_str="1.0,2.0,3.0\n4.0,5.0,6.0\n7.0,8.0,9.0",
        )
        viewer = ObjectViewer3D(None)
        qtbot.addWidget(viewer)
        viewer.resize(200, 200)
        viewer.show()
        qtbot.wait(50)
        viewer.set_object(obj)
        return viewer

    def test_draw_object_runs(self, viewer_3d_obj):
        viewer_3d_obj.makeCurrent()
        viewer_3d_obj.draw_object(viewer_3d_obj.obj_ops)

    @pytest.mark.parametrize("landmark_as_sphere", [True, False])
    def test_draw_object_landmark_styles(self, viewer_3d_obj, landmark_as_sphere):
        viewer_3d_obj.makeCurrent()
        viewer_3d_obj.draw_object(viewer_3d_obj.obj_ops, landmark_as_sphere=landmark_as_sphere)

    def test_draw_object_with_none_is_safe(self, viewer_3d_obj):
        viewer_3d_obj.makeCurrent()
        viewer_3d_obj.draw_object(None)

    def test_viewer_3d_renders(self, viewer_3d_obj):
        assert not viewer_3d_obj.grab().isNull()
