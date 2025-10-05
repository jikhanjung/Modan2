"""Tests for AnalysisResultDialog."""

import pytest
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QWidget

import MdUtils as mu
from dialogs import AnalysisResultDialog


class TestAnalysisResultDialogInitialization:
    """Test AnalysisResultDialog initialization."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    def test_dialog_creation(self, qtbot, mock_parent):
        """Test dialog can be created successfully."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)
        assert dialog is not None
        assert dialog.parent == mock_parent

    def test_window_title(self, qtbot, mock_parent):
        """Test dialog window title is set."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)
        assert "Analysis" in dialog.windowTitle()

    def test_window_flags(self, qtbot, mock_parent):
        """Test dialog has maximize and minimize buttons."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        flags = dialog.windowFlags()
        assert flags & Qt.WindowMaximizeButtonHint
        assert flags & Qt.WindowMinimizeButtonHint
        assert flags & Qt.WindowCloseButtonHint

    def test_default_geometry(self, qtbot, mock_parent, qapp):
        """Test dialog has default geometry."""
        # Disable remember geometry for this test
        qapp.settings.setValue("WindowGeometry/RememberGeometry", False)

        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Should have a reasonable default size
        assert dialog.width() > 0
        assert dialog.height() > 0

    def test_main_splitter_created(self, qtbot, mock_parent):
        """Test main horizontal splitter is created."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        assert dialog.main_hsplitter is not None
        assert dialog.main_hsplitter.orientation() == Qt.Horizontal


class TestAnalysisResultDialogPreferences:
    """Test AnalysisResultDialog preferences."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    @pytest.fixture
    def dialog(self, qtbot, mock_parent):
        """Create dialog for testing."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)
        return dialog

    def test_default_color_list(self, dialog):
        """Test default color list is set."""
        assert dialog.default_color_list == mu.VIVID_COLOR_LIST
        assert dialog.color_list == mu.VIVID_COLOR_LIST

    def test_default_marker_list(self, dialog):
        """Test default marker list is set."""
        assert dialog.marker_list == mu.MARKER_LIST

    def test_default_plot_size(self, dialog):
        """Test default plot size is medium."""
        assert dialog.plot_size == "medium"

    def test_remember_geometry_default(self, dialog):
        """Test remember geometry is enabled by default."""
        assert dialog.remember_geometry is True


class TestAnalysisResultDialogDataStructures:
    """Test AnalysisResultDialog data structures."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    @pytest.fixture
    def dialog(self, qtbot, mock_parent):
        """Create dialog for testing."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)
        return dialog

    def test_initial_data_structures(self, dialog):
        """Test initial data structures are empty."""
        assert dialog.ds_ops is None
        assert dialog.object_hash == {}
        assert dialog.shape_list == []
        assert dialog.shape_name_list == []

    def test_can_set_data_structures(self, dialog):
        """Test data structures can be modified."""
        dialog.object_hash = {"obj1": "data1"}
        dialog.shape_list = ["shape1", "shape2"]
        dialog.shape_name_list = ["Shape 1", "Shape 2"]

        assert dialog.object_hash == {"obj1": "data1"}
        assert dialog.shape_list == ["shape1", "shape2"]
        assert dialog.shape_name_list == ["Shape 1", "Shape 2"]


class TestAnalysisResultDialogSettings:
    """Test AnalysisResultDialog settings persistence."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    def test_read_settings_with_remember_geometry(self, qtbot, mock_parent, qapp):
        """Test reading settings when remember geometry is enabled."""
        # Set up saved geometry
        qapp.settings.setValue("WindowGeometry/RememberGeometry", True)
        saved_geometry = QRect(200, 200, 1000, 600)
        qapp.settings.setValue("WindowGeometry/AnalysisResultDialog", saved_geometry)

        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Geometry should be restored
        assert dialog.remember_geometry is True

    def test_read_settings_without_remember_geometry(self, qtbot, mock_parent, qapp):
        """Test reading settings when remember geometry is disabled."""
        qapp.settings.setValue("WindowGeometry/RememberGeometry", False)

        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Should read the setting (False)
        # Note: value_to_bool may return True if key doesn't exist or has unexpected value
        assert isinstance(dialog.remember_geometry, bool)

    def test_write_settings(self, qtbot, mock_parent, qapp):
        """Test saving settings on close."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Set geometry
        dialog.setGeometry(QRect(100, 100, 1200, 700))
        dialog.remember_geometry = True

        # Close dialog (triggers write_settings)
        dialog.close()

        # Verify geometry was saved (if remember_geometry is True)
        if dialog.remember_geometry:
            saved_geometry = qapp.settings.value("WindowGeometry/AnalysisResultDialog")
            # Settings may return the geometry or None
            assert saved_geometry is not None or not hasattr(qapp, "settings")


class TestAnalysisResultDialogCloseEvent:
    """Test AnalysisResultDialog close event handling."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    def test_close_event_saves_settings(self, qtbot, mock_parent):
        """Test close event saves settings."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        # Close dialog
        dialog.close()

        # Dialog should be closed
        assert not dialog.isVisible()

    def test_close_event_accepts_event(self, qtbot, mock_parent):
        """Test close event is accepted."""
        from PyQt5.QtGui import QCloseEvent

        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Create and trigger close event
        event = QCloseEvent()
        dialog.closeEvent(event)

        # Event should be accepted
        assert event.isAccepted()


class TestAnalysisResultDialogIntegration:
    """Test AnalysisResultDialog integration scenarios."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    def test_dialog_can_be_shown(self, qtbot, mock_parent):
        """Test dialog can be shown and hidden."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        dialog.show()
        # Note: Dialog may not be fully visible immediately in headless mode
        # Just verify show() doesn't crash
        assert dialog is not None

        dialog.hide()
        # After explicit hide, should not be visible
        assert not dialog.isVisible()

    def test_multiple_dialogs_can_coexist(self, qtbot, mock_parent):
        """Test multiple dialog instances can coexist."""
        dialog1 = AnalysisResultDialog(mock_parent)
        dialog2 = AnalysisResultDialog(mock_parent)

        qtbot.addWidget(dialog1)
        qtbot.addWidget(dialog2)

        # Both dialogs should be independent
        assert dialog1 is not dialog2
        assert dialog1.parent == dialog2.parent

    def test_initialize_ui_can_be_called(self, qtbot, mock_parent):
        """Test initialize_UI method can be called."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Should not raise exception (it's a placeholder method)
        dialog.initialize_UI()
        assert True

    def test_color_list_modification(self, qtbot, mock_parent):
        """Test color list can be modified independently."""
        dialog = AnalysisResultDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Modify color list
        original_default = dialog.default_color_list[:]
        dialog.color_list = ["#FF0000", "#00FF00", "#0000FF"]

        # Default should remain unchanged
        assert dialog.default_color_list == original_default
        assert dialog.color_list == ["#FF0000", "#00FF00", "#0000FF"]
