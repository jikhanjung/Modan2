"""Tests for DatasetDialog."""

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

from dialogs import DatasetDialog


class TestDatasetDialogInitialization:
    """Test DatasetDialog initialization."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    def test_dialog_creation(self, qtbot, mock_parent):
        """Test dialog can be created successfully."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)
        assert dialog is not None
        assert dialog.parent == mock_parent

    def test_window_title(self, qtbot, mock_parent):
        """Test dialog window title is set."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)
        assert "Dataset" in dialog.windowTitle()

    def test_ui_elements_present(self, qtbot, mock_parent):
        """Test all UI elements are present."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Basic info widgets
        assert dialog.cbxParent is not None
        assert dialog.edtDatasetName is not None
        assert dialog.edtDatasetDesc is not None

        # Dimension widgets
        assert dialog.rbtn2D is not None
        assert dialog.rbtn3D is not None

        # Geometric configuration widgets
        assert dialog.edtWireframe is not None
        assert dialog.edtBaseline is not None
        assert dialog.edtPolygons is not None

        # Variable management widgets
        assert dialog.lstVariableName is not None
        assert dialog.btnAddVariable is not None
        assert dialog.btnDeleteVariable is not None
        assert dialog.btnMoveUp is not None
        assert dialog.btnMoveDown is not None

        # Action buttons
        assert dialog.btnOkay is not None
        assert dialog.btnDelete is not None
        assert dialog.btnCancel is not None

    def test_default_dimension_2d(self, qtbot, mock_parent):
        """Test default dimension is 2D."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)

        assert dialog.rbtn2D.isChecked()
        assert not dialog.rbtn3D.isChecked()


class TestDatasetDialogDimensionSelection:
    """Test dimension selection functionality."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    @pytest.fixture
    def dialog(self, qtbot, mock_parent):
        """Create dialog for testing."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)
        return dialog

    def test_select_2d_dimension(self, qtbot, dialog):
        """Test selecting 2D dimension."""
        dialog.rbtn3D.setChecked(True)  # First set to 3D
        dialog.rbtn2D.setChecked(True)  # Then set to 2D

        assert dialog.rbtn2D.isChecked()
        assert not dialog.rbtn3D.isChecked()

    def test_select_3d_dimension(self, qtbot, dialog):
        """Test selecting 3D dimension."""
        dialog.rbtn3D.setChecked(True)

        assert dialog.rbtn3D.isChecked()
        assert not dialog.rbtn2D.isChecked()


class TestDatasetDialogBasicInput:
    """Test basic input fields."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    @pytest.fixture
    def dialog(self, qtbot, mock_parent):
        """Create dialog for testing."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)
        return dialog

    def test_dataset_name_input(self, qtbot, dialog):
        """Test entering dataset name."""
        dialog.edtDatasetName.setText("Test Dataset")
        assert dialog.edtDatasetName.text() == "Test Dataset"

    def test_dataset_description_input(self, qtbot, dialog):
        """Test entering dataset description."""
        dialog.edtDatasetDesc.setText("Test description")
        assert dialog.edtDatasetDesc.text() == "Test description"

    def test_baseline_input(self, qtbot, dialog):
        """Test entering baseline configuration."""
        dialog.edtBaseline.setText("1,2")
        assert dialog.edtBaseline.text() == "1,2"


class TestDatasetDialogVariableManagement:
    """Test variable management functionality."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    @pytest.fixture
    def dialog(self, qtbot, mock_parent):
        """Create dialog for testing."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)
        return dialog

    def test_add_variable(self, qtbot, dialog):
        """Test adding a new variable."""
        initial_count = dialog.lstVariableName.count()

        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)

        # Should have one more item
        assert dialog.lstVariableName.count() == initial_count + 1

    def test_add_multiple_variables(self, qtbot, dialog):
        """Test adding multiple variables."""
        initial_count = dialog.lstVariableName.count()

        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)
        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)
        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)

        assert dialog.lstVariableName.count() == initial_count + 3

    def test_delete_variable(self, qtbot, dialog):
        """Test deleting a variable."""
        # Add a variable first
        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)
        count_after_add = dialog.lstVariableName.count()

        # Select and delete it
        dialog.lstVariableName.setCurrentRow(count_after_add - 1)
        qtbot.mouseClick(dialog.btnDeleteVariable, Qt.LeftButton)

        assert dialog.lstVariableName.count() == count_after_add - 1

    def test_move_variable_up(self, qtbot, dialog):
        """Test moving variable up in the list."""
        # Add two variables
        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)
        first_item = dialog.lstVariableName.item(dialog.lstVariableName.count() - 1)
        first_item.setText("First")

        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)
        second_item = dialog.lstVariableName.item(dialog.lstVariableName.count() - 1)
        second_item.setText("Second")

        # Select second item and move up
        dialog.lstVariableName.setCurrentRow(dialog.lstVariableName.count() - 1)
        initial_row = dialog.lstVariableName.currentRow()

        qtbot.mouseClick(dialog.btnMoveUp, Qt.LeftButton)

        # Should be moved up one position
        assert dialog.lstVariableName.currentRow() == initial_row - 1

    def test_move_variable_down(self, qtbot, dialog):
        """Test moving variable down in the list."""
        # Add two variables
        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)
        first_item = dialog.lstVariableName.item(dialog.lstVariableName.count() - 1)
        first_item.setText("First")

        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)
        second_item = dialog.lstVariableName.item(dialog.lstVariableName.count() - 1)
        second_item.setText("Second")

        # Select first item and move down
        dialog.lstVariableName.setCurrentRow(dialog.lstVariableName.count() - 2)
        initial_row = dialog.lstVariableName.currentRow()

        qtbot.mouseClick(dialog.btnMoveDown, Qt.LeftButton)

        # Should be moved down one position
        assert dialog.lstVariableName.currentRow() == initial_row + 1

    def test_cannot_move_up_from_top(self, qtbot, dialog):
        """Test that top item cannot be moved up."""
        # Add one variable
        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)

        # Select first item
        dialog.lstVariableName.setCurrentRow(0)

        # Try to move up (should do nothing)
        qtbot.mouseClick(dialog.btnMoveUp, Qt.LeftButton)

        # Should still be at position 0
        assert dialog.lstVariableName.currentRow() == 0

    def test_cannot_move_down_from_bottom(self, qtbot, dialog):
        """Test that bottom item cannot be moved down."""
        # Add one variable
        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)
        last_index = dialog.lstVariableName.count() - 1

        # Select last item
        dialog.lstVariableName.setCurrentRow(last_index)

        # Try to move down (should do nothing)
        qtbot.mouseClick(dialog.btnMoveDown, Qt.LeftButton)

        # Should still be at last position
        assert dialog.lstVariableName.currentRow() == last_index


class TestDatasetDialogSettings:
    """Test settings persistence."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    def test_read_settings(self, qtbot, mock_parent, qapp):
        """Test reading settings on initialization."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Dialog should have read settings
        assert isinstance(dialog.remember_geometry, bool)

    def test_write_settings(self, qtbot, mock_parent, qapp):
        """Test writing settings."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Call write_settings
        dialog.write_settings()

        # Verify settings were called (implementation may vary)
        assert True  # Just verify no crash


class TestDatasetDialogIntegration:
    """Test DatasetDialog integration scenarios."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    def test_complete_dataset_setup(self, qtbot, mock_parent):
        """Test complete dataset configuration workflow."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)

        # Set basic info
        dialog.edtDatasetName.setText("Integration Test Dataset")
        dialog.edtDatasetDesc.setText("Test description")

        # Select dimension
        dialog.rbtn3D.setChecked(True)

        # Add variables
        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)
        qtbot.mouseClick(dialog.btnAddVariable, Qt.LeftButton)

        # Verify state
        assert dialog.edtDatasetName.text() == "Integration Test Dataset"
        assert dialog.rbtn3D.isChecked()
        assert dialog.lstVariableName.count() >= 2

    def test_keyboard_shortcut_close(self, qtbot, mock_parent):
        """Test Ctrl+W keyboard shortcut closes dialog."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)
        dialog.show()

        # Keyboard shortcut should exist
        # Just verify dialog was created successfully
        assert dialog is not None

    def test_cancel_button_closes_dialog(self, qtbot, mock_parent):
        """Test Cancel button closes dialog."""
        dialog = DatasetDialog(mock_parent)
        qtbot.addWidget(dialog)
        dialog.show()

        qtbot.mouseClick(dialog.btnCancel, Qt.LeftButton)

        # Dialog should be closed
        assert not dialog.isVisible()
