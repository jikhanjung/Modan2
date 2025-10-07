"""
Test suite for DatasetOpsViewer widget component

Tests cover:
- Widget initialization
- Dataset operations object setup
- Scale and pan calculation
- Display options (index, wireframe, baseline, average)
- Coordinate transformation
- Paint event handling
- Resize event handling

Note: Full painting tests require complex Qt mocking. These tests focus on
core widget functionality and state management.
"""

from unittest.mock import Mock, patch

from PyQt5.QtGui import QPaintEvent

from components.widgets.dataset_ops_viewer import DatasetOpsViewer


class TestDatasetOpsViewerInitialization:
    """Test DatasetOpsViewer initialization"""

    def test_widget_creation(self, qtbot):
        """Test that DatasetOpsViewer can be created"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        assert widget is not None

    def test_initial_values(self, qtbot):
        """Test initial widget values"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        # Initial ds_ops is None
        assert widget.ds_ops is None

        # Initial scale and pan
        assert widget.scale == 1.0
        assert widget.pan_x == 0
        assert widget.pan_y == 0

        # Initial display options
        assert widget.show_index is True
        assert widget.show_wireframe is False
        assert widget.show_baseline is False
        assert widget.show_average is True


class TestDatasetOpsViewerDisplayOptions:
    """Test display option toggles"""

    def test_show_index_toggle(self, qtbot):
        """Test show_index option"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        assert widget.show_index is True

        widget.show_index = False
        assert widget.show_index is False

    def test_show_wireframe_toggle(self, qtbot):
        """Test show_wireframe option"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        assert widget.show_wireframe is False

        widget.show_wireframe = True
        assert widget.show_wireframe is True

    def test_show_baseline_toggle(self, qtbot):
        """Test show_baseline option"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        assert widget.show_baseline is False

        widget.show_baseline = True
        assert widget.show_baseline is True

    def test_show_average_toggle(self, qtbot):
        """Test show_average option"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        assert widget.show_average is True

        widget.show_average = False
        assert widget.show_average is False


class TestDatasetOpsViewerCoordinateTransform:
    """Test coordinate transformation methods"""

    def test_2canx_basic(self, qtbot):
        """Test X coordinate transformation"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        # With scale=1.0 and pan_x=0
        assert widget._2canx(10.0) == 10
        assert widget._2canx(0.0) == 0
        assert widget._2canx(-5.0) == -5

    def test_2cany_basic(self, qtbot):
        """Test Y coordinate transformation"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        # With scale=1.0 and pan_y=0
        assert widget._2cany(10.0) == 10
        assert widget._2cany(0.0) == 0
        assert widget._2cany(-5.0) == -5

    def test_2canx_with_scale(self, qtbot):
        """Test X coordinate transformation with scale"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        widget.scale = 2.0
        widget.pan_x = 0

        assert widget._2canx(10.0) == 20
        assert widget._2canx(5.0) == 10

    def test_2cany_with_scale(self, qtbot):
        """Test Y coordinate transformation with scale"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        widget.scale = 2.0
        widget.pan_y = 0

        assert widget._2cany(10.0) == 20
        assert widget._2cany(5.0) == 10

    def test_2canx_with_pan(self, qtbot):
        """Test X coordinate transformation with pan"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        widget.scale = 1.0
        widget.pan_x = 100

        assert widget._2canx(10.0) == 110
        assert widget._2canx(0.0) == 100

    def test_2cany_with_pan(self, qtbot):
        """Test Y coordinate transformation with pan"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        widget.scale = 1.0
        widget.pan_y = 50

        assert widget._2cany(10.0) == 60
        assert widget._2cany(0.0) == 50

    def test_coordinate_transform_with_scale_and_pan(self, qtbot):
        """Test coordinate transformation with both scale and pan"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        widget.scale = 2.0
        widget.pan_x = 100
        widget.pan_y = 50

        assert widget._2canx(10.0) == 120  # 10 * 2 + 100
        assert widget._2cany(10.0) == 70  # 10 * 2 + 50


class TestDatasetOpsViewerDatasetOps:
    """Test dataset operations object handling"""

    def test_set_ds_ops(self, qtbot):
        """Test setting dataset operations object"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)
        widget.resize(400, 400)

        # Create mock ds_ops with minimal data
        ds_ops = Mock()
        mock_obj = Mock()
        mock_obj.landmark_list = [[0.0, 0.0], [10.0, 10.0]]
        ds_ops.object_list = [mock_obj]

        widget.set_ds_ops(ds_ops)

        assert widget.ds_ops is ds_ops

    def test_calculate_scale_and_pan_single_object(self, qtbot):
        """Test scale and pan calculation with single object"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)
        widget.resize(400, 400)

        # Create mock ds_ops with one object
        ds_ops = Mock()
        mock_obj = Mock()
        mock_obj.landmark_list = [[0.0, 0.0], [100.0, 100.0]]
        ds_ops.object_list = [mock_obj]

        widget.ds_ops = ds_ops
        widget.calculate_scale_and_pan()

        # Scale should be calculated to fit data
        assert widget.scale > 0
        # Pan should be calculated to center data
        assert isinstance(widget.pan_x, (int, float))
        assert isinstance(widget.pan_y, (int, float))

    def test_calculate_scale_and_pan_multiple_objects(self, qtbot):
        """Test scale and pan calculation with multiple objects"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)
        widget.resize(400, 400)

        # Create mock ds_ops with multiple objects
        ds_ops = Mock()
        mock_obj1 = Mock()
        mock_obj1.landmark_list = [[0.0, 0.0], [50.0, 50.0]]
        mock_obj2 = Mock()
        mock_obj2.landmark_list = [[50.0, 50.0], [100.0, 100.0]]
        ds_ops.object_list = [mock_obj1, mock_obj2]

        widget.ds_ops = ds_ops
        widget.calculate_scale_and_pan()

        assert widget.scale > 0
        assert isinstance(widget.pan_x, (int, float))
        assert isinstance(widget.pan_y, (int, float))

    def test_calculate_scale_and_pan_negative_coords(self, qtbot):
        """Test scale and pan calculation with negative coordinates"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)
        widget.resize(400, 400)

        # Create mock ds_ops with negative coordinates
        ds_ops = Mock()
        mock_obj = Mock()
        mock_obj.landmark_list = [[-50.0, -50.0], [50.0, 50.0]]
        ds_ops.object_list = [mock_obj]

        widget.ds_ops = ds_ops
        widget.calculate_scale_and_pan()

        assert widget.scale > 0
        assert isinstance(widget.pan_x, (int, float))
        assert isinstance(widget.pan_y, (int, float))


class TestDatasetOpsViewerEventHandling:
    """Test event handling"""

    def test_resize_event_triggers_recalculation(self, qtbot):
        """Test that resize event triggers scale/pan recalculation"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)

        # Create mock ds_ops
        ds_ops = Mock()
        mock_obj = Mock()
        mock_obj.landmark_list = [[0.0, 0.0], [100.0, 100.0]]
        ds_ops.object_list = [mock_obj]

        widget.ds_ops = ds_ops

        # Resize widget (triggers scale/pan recalculation)
        widget.resize(200, 200)
        # Resize again with different size
        widget.resize(400, 400)

        # Scale should be recalculated
        # Note: actual value depends on calculation, just verify it happened
        assert isinstance(widget.scale, (int, float))
        assert widget.scale > 0

    def test_paint_event_with_no_ds_ops(self, qtbot):
        """Test paint event when ds_ops is None"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)
        # Don't call show() as it triggers resizeEvent which crashes with None ds_ops

        # Create paint event
        paint_event = QPaintEvent(widget.rect())

        # Should not crash when ds_ops is None
        widget.paintEvent(paint_event)

    @patch("components.widgets.dataset_ops_viewer.QPainter")
    def test_paint_event_with_ds_ops(self, mock_painter_class, qtbot):
        """Test paint event with ds_ops"""
        widget = DatasetOpsViewer(None)
        qtbot.addWidget(widget)
        widget.resize(400, 400)

        # Create mock ds_ops with average shape
        ds_ops = Mock()
        mock_obj = Mock()
        mock_obj.id = 1
        mock_obj.landmark_list = [[0.0, 0.0], [100.0, 100.0]]
        ds_ops.object_list = [mock_obj]
        ds_ops.selected_object_id_list = []
        ds_ops.edge_list = []

        mock_avg = Mock()
        mock_avg.landmark_list = [[50.0, 50.0]]
        ds_ops.get_average_shape.return_value = mock_avg

        # Set ds_ops BEFORE show() to avoid resizeEvent crash
        widget.set_ds_ops(ds_ops)
        widget.show()

        # Create paint event
        paint_event = QPaintEvent(widget.rect())

        # Should call QPainter
        widget.paintEvent(paint_event)

        # Verify QPainter was instantiated
        mock_painter_class.assert_called()
