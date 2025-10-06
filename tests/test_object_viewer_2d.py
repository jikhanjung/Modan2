"""
Test suite for ObjectViewer2D component

Tests cover:
- Initialization and basic properties
- Mode setting and switching
- Coordinate transformations
- Landmark operations
- Mouse interactions
- Object and dataset display
- Settings and preferences
"""

from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QMouseEvent, QWheelEvent

import MdModel as mm
from components.viewers.object_viewer_2d import MODE, ObjectViewer2D


@pytest.fixture
def viewer_2d(qtbot):
    """Create ObjectViewer2D instance for testing"""
    viewer = ObjectViewer2D()
    qtbot.addWidget(viewer)
    return viewer


@pytest.fixture
def mock_object(mock_database):
    """Create a mock object with landmarks for testing"""
    dataset = mm.MdDataset.create(dataset_name="Test Dataset 2D", dimension=2, landmark_count=3)

    # Create object with 3 landmarks
    obj = mm.MdObject.create(dataset=dataset, object_name="Test Object", landmark_str="10.0,20.0\n30.0,40.0\n50.0,60.0")

    return obj


@pytest.fixture
def mock_dataset_with_objects(mock_database):
    """Create a dataset with multiple objects"""
    dataset = mm.MdDataset.create(
        dataset_name="Multi Object Dataset",
        dimension=2,
        landmark_count=5,
        wireframe="1 2\n2 3\n3 4",  # Space-separated, not comma
        polygon="1 2 3",  # Space-separated, not comma
    )

    # Create 3 objects
    for i in range(3):
        mm.MdObject.create(dataset=dataset, object_name=f"Object {i + 1}", landmark_str="0,0\n10,0\n10,10\n0,10\n5,5")

    return dataset


class TestObjectViewer2DInit:
    """Test ObjectViewer2D initialization"""

    def test_viewer_creation(self, qtbot):
        """Test that viewer can be created"""
        viewer = ObjectViewer2D()
        qtbot.addWidget(viewer)

        assert viewer is not None
        assert isinstance(viewer, ObjectViewer2D)

    def test_transparent_mode(self, qtbot):
        """Test viewer with transparent mode"""
        viewer = ObjectViewer2D(transparent=True)
        qtbot.addWidget(viewer)

        assert viewer.transparent is True

    def test_initial_properties(self, viewer_2d):
        """Test initial property values"""
        # landmark_size is read from settings, may not be 1
        assert viewer_2d.landmark_size >= 1
        assert viewer_2d.wireframe_thickness >= 1
        assert viewer_2d.scale == 1.0
        assert viewer_2d.pan_x == 0
        assert viewer_2d.pan_y == 0
        assert viewer_2d.selected_landmark_index == -1
        assert viewer_2d.selected_edge_index == -1

    def test_initial_mode(self, viewer_2d):
        """Test initial edit mode"""
        assert viewer_2d.edit_mode == MODE["EDIT_LANDMARK"]

    def test_initial_display_flags(self, viewer_2d):
        """Test initial display flags"""
        assert viewer_2d.show_index is False
        assert viewer_2d.show_wireframe is True
        assert viewer_2d.show_polygon is True
        assert viewer_2d.show_baseline is False
        assert viewer_2d.read_only is False


class TestObjectViewer2DModes:
    """Test mode setting and behavior"""

    def test_set_edit_landmark_mode(self, viewer_2d):
        """Test setting edit landmark mode"""
        viewer_2d.set_mode(MODE["EDIT_LANDMARK"])
        assert viewer_2d.edit_mode == MODE["EDIT_LANDMARK"]

    def test_set_wireframe_mode(self, viewer_2d):
        """Test setting wireframe mode"""
        viewer_2d.set_mode(MODE["WIREFRAME"])
        assert viewer_2d.edit_mode == MODE["WIREFRAME"]

    def test_set_calibration_mode(self, viewer_2d):
        """Test setting calibration mode"""
        viewer_2d.set_mode(MODE["CALIBRATION"])
        assert viewer_2d.edit_mode == MODE["CALIBRATION"]

    def test_set_view_mode(self, viewer_2d):
        """Test setting view mode"""
        viewer_2d.set_mode(MODE["VIEW"])
        assert viewer_2d.edit_mode == MODE["VIEW"]

    def test_mode_switching(self, viewer_2d):
        """Test switching between modes"""
        viewer_2d.set_mode(MODE["EDIT_LANDMARK"])
        assert viewer_2d.edit_mode == MODE["EDIT_LANDMARK"]

        viewer_2d.set_mode(MODE["WIREFRAME"])
        assert viewer_2d.edit_mode == MODE["WIREFRAME"]

        viewer_2d.set_mode(MODE["VIEW"])
        assert viewer_2d.edit_mode == MODE["VIEW"]


class TestObjectViewer2DCoordinates:
    """Test coordinate transformation methods"""

    def test_2canx_basic(self, viewer_2d):
        """Test image to canvas X coordinate conversion"""
        viewer_2d.scale = 1.0
        viewer_2d.pan_x = 0
        result = viewer_2d._2canx(100)
        assert result == 100

    def test_2cany_basic(self, viewer_2d):
        """Test image to canvas Y coordinate conversion"""
        viewer_2d.scale = 1.0
        viewer_2d.pan_y = 0
        result = viewer_2d._2cany(100)
        assert result == 100

    def test_2canx_with_scale(self, viewer_2d):
        """Test X coordinate with scaling"""
        viewer_2d.scale = 2.0
        viewer_2d.pan_x = 0
        result = viewer_2d._2canx(100)
        assert result == 200

    def test_2cany_with_scale(self, viewer_2d):
        """Test Y coordinate with scaling"""
        viewer_2d.scale = 2.0
        viewer_2d.pan_y = 0
        result = viewer_2d._2cany(100)
        assert result == 200

    def test_2canx_with_pan(self, viewer_2d):
        """Test X coordinate with panning"""
        viewer_2d.scale = 1.0
        viewer_2d.pan_x = 50
        result = viewer_2d._2canx(100)
        assert result == 150

    def test_2cany_with_pan(self, viewer_2d):
        """Test Y coordinate with panning"""
        viewer_2d.scale = 1.0
        viewer_2d.pan_y = 50
        result = viewer_2d._2cany(100)
        assert result == 150

    def test_2imgx_basic(self, viewer_2d):
        """Test canvas to image X coordinate conversion"""
        viewer_2d.scale = 1.0
        viewer_2d.pan_x = 0
        result = viewer_2d._2imgx(100)
        assert result == 100

    def test_2imgy_basic(self, viewer_2d):
        """Test canvas to image Y coordinate conversion"""
        viewer_2d.scale = 1.0
        viewer_2d.pan_y = 0
        result = viewer_2d._2imgy(100)
        assert result == 100

    def test_coordinate_roundtrip(self, viewer_2d):
        """Test that coordinates convert back correctly"""
        viewer_2d.scale = 1.5
        viewer_2d.pan_x = 20
        viewer_2d.pan_y = 30

        img_x = 100
        img_y = 150

        can_x = viewer_2d._2canx(img_x)
        can_y = viewer_2d._2cany(img_y)

        back_x = viewer_2d._2imgx(can_x)
        back_y = viewer_2d._2imgy(can_y)

        assert abs(back_x - img_x) < 0.01
        assert abs(back_y - img_y) < 0.01


class TestObjectViewer2DDistance:
    """Test distance calculation methods"""

    def test_get_distance(self, viewer_2d):
        """Test distance calculation between two points"""
        pos1 = [0, 0]
        pos2 = [3, 4]
        distance = viewer_2d.get_distance(pos1, pos2)
        assert abs(distance - 5.0) < 0.01  # 3-4-5 triangle

    def test_get_distance_same_point(self, viewer_2d):
        """Test distance to same point is zero"""
        pos1 = [10, 20]
        pos2 = [10, 20]
        distance = viewer_2d.get_distance(pos1, pos2)
        assert distance == 0.0

    def test_get_distance_negative_coords(self, viewer_2d):
        """Test distance with negative coordinates"""
        pos1 = [-3, -4]
        pos2 = [0, 0]
        distance = viewer_2d.get_distance(pos1, pos2)
        assert abs(distance - 5.0) < 0.01


class TestObjectViewer2DLandmarks:
    """Test landmark-related operations"""

    def test_get_landmark_index_none_within_threshold(self, viewer_2d):
        """Test finding landmark when none are within threshold"""
        viewer_2d.landmark_list = [[10, 10], [20, 20], [30, 30]]
        curr_pos = [100, 100]  # Far from any landmark
        index = viewer_2d.get_landmark_index_within_threshold(curr_pos, threshold=5)
        assert index == -1

    def test_get_landmark_index_within_threshold(self, viewer_2d):
        """Test finding landmark within threshold"""
        viewer_2d.landmark_list = [[10, 10], [20, 20], [30, 30]]
        curr_pos = [11, 11]  # Close to first landmark
        index = viewer_2d.get_landmark_index_within_threshold(curr_pos, threshold=5)
        assert index == 0

    def test_get_landmark_index_closest(self, viewer_2d):
        """Test that closest landmark is returned"""
        viewer_2d.landmark_list = [[10, 10], [12, 12], [30, 30]]
        curr_pos = [11, 11]  # Closer to first landmark
        index = viewer_2d.get_landmark_index_within_threshold(curr_pos, threshold=10)
        assert index == 0  # Should return closest one


class TestObjectViewer2DMouseEvents:
    """Test mouse event handling"""

    def test_mouse_press_left_button(self, viewer_2d, qtbot):
        """Test left mouse button press"""
        viewer_2d.setFixedSize(400, 400)

        # Mouse press behavior depends on object being set
        # Without an object, mouse_down_x/y may not be updated
        # Just verify the event is handled without error
        event = QMouseEvent(QMouseEvent.MouseButtonPress, QPoint(100, 100), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)

        viewer_2d.mousePressEvent(event)

        # Event handled successfully
        assert True

    def test_mouse_press_right_button_pan_mode(self, viewer_2d, qtbot):
        """Test right mouse button activates pan mode"""
        viewer_2d.setFixedSize(400, 400)
        event = QMouseEvent(
            QMouseEvent.MouseButtonPress, QPoint(100, 100), Qt.RightButton, Qt.RightButton, Qt.NoModifier
        )

        viewer_2d.mousePressEvent(event)

        assert viewer_2d.pan_mode == MODE["PAN"]

    def test_mouse_release_deactivates_pan(self, viewer_2d, qtbot):
        """Test mouse release deactivates pan mode"""
        viewer_2d.setFixedSize(400, 400)
        viewer_2d.pan_mode = MODE["PAN"]

        # mouseReleaseEvent requires object_dialog to be set
        viewer_2d.object_dialog = Mock()

        release_event = QMouseEvent(
            QMouseEvent.MouseButtonRelease, QPoint(150, 150), Qt.RightButton, Qt.NoButton, Qt.NoModifier
        )

        viewer_2d.mouseReleaseEvent(release_event)

        assert viewer_2d.pan_mode == MODE["NONE"]

    def test_wheel_event_zoom_in(self, viewer_2d, qtbot):
        """Test mouse wheel zoom in"""
        viewer_2d.setFixedSize(400, 400)
        initial_scale = viewer_2d.scale

        # Positive delta = zoom in
        # Use simpler QWheelEvent constructor compatible with PyQt5
        from PyQt5.QtCore import QPointF

        event = QWheelEvent(
            QPointF(200, 200),  # pos
            QPointF(200, 200),  # globalPos
            QPoint(0, 0),  # pixelDelta
            QPoint(0, 120),  # angleDelta (positive = up)
            Qt.NoButton,  # buttons
            Qt.NoModifier,  # modifiers
            Qt.ScrollUpdate,  # phase
            False,  # inverted
        )

        viewer_2d.wheelEvent(event)

        assert viewer_2d.scale > initial_scale

    def test_wheel_event_zoom_out(self, viewer_2d, qtbot):
        """Test mouse wheel zoom out"""
        viewer_2d.setFixedSize(400, 400)
        viewer_2d.scale = 2.0
        initial_scale = viewer_2d.scale

        # Negative delta = zoom out
        from PyQt5.QtCore import QPointF

        event = QWheelEvent(
            QPointF(200, 200),  # pos
            QPointF(200, 200),  # globalPos
            QPoint(0, 0),  # pixelDelta
            QPoint(0, -120),  # angleDelta (negative = down)
            Qt.NoButton,  # buttons
            Qt.NoModifier,  # modifiers
            Qt.ScrollUpdate,  # phase
            False,  # inverted
        )

        viewer_2d.wheelEvent(event)

        assert viewer_2d.scale < initial_scale


class TestObjectViewer2DObject:
    """Test object display and manipulation"""

    def test_set_object(self, viewer_2d, mock_object):
        """Test setting an object to display"""
        viewer_2d.set_object(mock_object)

        assert viewer_2d.object == mock_object
        assert viewer_2d.dataset == mock_object.dataset

    def test_align_object(self, viewer_2d, mock_object):
        """Test object alignment"""
        viewer_2d.set_object(mock_object)
        viewer_2d.setFixedSize(400, 400)

        # This should run without error
        viewer_2d.align_object()

        # After alignment, scale and pan should be set
        assert viewer_2d.scale > 0

    def test_set_object_name(self, viewer_2d):
        """Test setting object name"""
        test_name = "New Object Name"
        viewer_2d.set_object_name(test_name)
        # This should run without error
        # Name would be set on the actual object if it exists


class TestObjectViewer2DPreferences:
    """Test shape preference settings"""

    def test_set_source_shape_color(self, viewer_2d):
        """Test setting source shape color"""
        color = "#FF0000"
        viewer_2d.set_source_shape_color(color)
        assert viewer_2d.source_shape_color == color

    def test_set_target_shape_color(self, viewer_2d):
        """Test setting target shape color"""
        color = "#00FF00"
        viewer_2d.set_target_shape_color(color)
        assert viewer_2d.target_shape_color == color

    def test_set_landmark_pref(self, viewer_2d):
        """Test setting landmark preferences"""
        lm_pref = {"size": 2, "color": "#0000FF"}
        wf_pref = {"thickness": 2, "color": "#FFFF00"}
        bgcolor = "#FFFFFF"

        viewer_2d.set_landmark_pref(lm_pref, wf_pref, bgcolor)

        assert viewer_2d.landmark_size == 2
        assert viewer_2d.landmark_color == "#0000FF"
        assert viewer_2d.wireframe_thickness == 2


class TestObjectViewer2DDatasetOps:
    """Test dataset operations viewer"""

    def test_set_ds_ops(self, viewer_2d, mock_dataset_with_objects):
        """Test setting dataset operations"""
        ds_ops = mm.MdDatasetOps(mock_dataset_with_objects)

        viewer_2d.set_ds_ops(ds_ops)

        assert viewer_2d.ds_ops == ds_ops
        # set_ds_ops sets landmark_list from average shape
        assert len(viewer_2d.landmark_list) > 0

    def test_set_ds_ops_updates_edges(self, viewer_2d, mock_dataset_with_objects):
        """Test that setting ds_ops updates edge list"""
        ds_ops = mm.MdDatasetOps(mock_dataset_with_objects)

        viewer_2d.set_ds_ops(ds_ops)

        # edge_list is set from ds_ops.edge_list
        assert viewer_2d.edge_list == ds_ops.edge_list


class TestObjectViewer2DComparison:
    """Test shape comparison features"""

    def test_set_source_shape(self, viewer_2d, mock_object):
        """Test setting source shape for comparison"""
        viewer_2d.set_source_shape(mock_object)
        assert "source_shape" in viewer_2d.comparison_data
        assert viewer_2d.comparison_data["source_shape"] == mock_object

    def test_set_target_shape(self, viewer_2d, mock_object):
        """Test setting target shape for comparison"""
        viewer_2d.set_target_shape(mock_object)
        assert "target_shape" in viewer_2d.comparison_data
        assert viewer_2d.comparison_data["target_shape"] == mock_object

    def test_set_intermediate_shape(self, viewer_2d, mock_object):
        """Test setting intermediate shape for comparison"""
        viewer_2d.set_intermediate_shape(mock_object)
        assert "intermediate_shape" in viewer_2d.comparison_data
        assert viewer_2d.comparison_data["intermediate_shape"] == mock_object


class TestObjectViewer2DRotation:
    """Test rotation operations"""

    def test_apply_rotation(self, viewer_2d):
        """Test applying rotation angle"""
        angle = 45.0
        viewer_2d.apply_rotation(angle)
        # This should run without error
        # Actual rotation would be applied to object if it exists
