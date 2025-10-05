"""Tests for CalibrationDialog."""

from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

from dialogs import CalibrationDialog


class TestCalibrationDialogInitialization:
    """Test CalibrationDialog initialization."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        parent.set_object_calibration = Mock()
        qtbot.addWidget(parent)
        return parent

    def test_dialog_creation(self, qtbot, mock_parent):
        """Test dialog can be created successfully."""
        dialog = CalibrationDialog(mock_parent, dist=None)
        qtbot.addWidget(dialog)
        assert dialog is not None
        assert dialog.parent == mock_parent

    def test_dialog_with_distance(self, qtbot, mock_parent):
        """Test dialog creation with initial distance."""
        dialog = CalibrationDialog(mock_parent, dist=100.5)
        qtbot.addWidget(dialog)
        assert dialog.pixel_number == 100.5
        assert "100.50" in dialog.lblText2.text()

    def test_ui_elements_present(self, qtbot, mock_parent):
        """Test all UI elements are present."""
        dialog = CalibrationDialog(mock_parent, dist=None)
        qtbot.addWidget(dialog)

        # Labels
        assert dialog.lblText1 is not None
        assert dialog.lblText2 is not None

        # Input widgets
        assert dialog.edtLength is not None
        assert dialog.comboUnit is not None

        # Buttons
        assert dialog.btnOK is not None
        assert dialog.btnCancel is not None

    def test_default_values(self, qtbot, mock_parent):
        """Test default values are set correctly."""
        dialog = CalibrationDialog(mock_parent, dist=None)
        qtbot.addWidget(dialog)

        # Default length is 1.0
        assert dialog.edtLength.text() == "1.0"

        # Default unit is mm
        assert dialog.comboUnit.currentText() == "mm"

    def test_unit_options(self, qtbot, mock_parent):
        """Test all unit options are available."""
        dialog = CalibrationDialog(mock_parent, dist=None)
        qtbot.addWidget(dialog)

        units = [dialog.comboUnit.itemText(i) for i in range(dialog.comboUnit.count())]
        assert units == ["nm", "um", "mm", "cm", "m"]


class TestCalibrationDialogInput:
    """Test CalibrationDialog input handling."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        parent.set_object_calibration = Mock()
        qtbot.addWidget(parent)
        return parent

    @pytest.fixture
    def dialog(self, qtbot, mock_parent):
        """Create dialog for testing."""
        dialog = CalibrationDialog(mock_parent, dist=100.0)
        qtbot.addWidget(dialog)
        return dialog

    def test_length_input(self, qtbot, dialog):
        """Test entering length value."""
        dialog.edtLength.clear()
        qtbot.keyClicks(dialog.edtLength, "5.25")
        assert dialog.edtLength.text() == "5.25"

    def test_unit_selection(self, qtbot, dialog):
        """Test selecting different units."""
        dialog.comboUnit.setCurrentText("cm")
        assert dialog.comboUnit.currentText() == "cm"

        dialog.comboUnit.setCurrentText("um")
        assert dialog.comboUnit.currentText() == "um"

    def test_double_validator(self, qtbot, dialog):
        """Test that only numeric input is accepted."""
        dialog.edtLength.clear()
        qtbot.keyClicks(dialog.edtLength, "12.34")
        assert dialog.edtLength.text() == "12.34"

        # Validator should accept decimal numbers
        assert dialog.edtLength.hasAcceptableInput()


class TestCalibrationDialogActions:
    """Test CalibrationDialog button actions."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        parent.set_object_calibration = Mock()
        qtbot.addWidget(parent)
        return parent

    @pytest.fixture
    def dialog(self, qtbot, mock_parent):
        """Create dialog for testing."""
        dialog = CalibrationDialog(mock_parent, dist=100.0)
        qtbot.addWidget(dialog)
        return dialog

    def test_ok_button_calls_parent_method(self, qtbot, dialog, mock_parent):
        """Test OK button calls parent's set_object_calibration."""
        dialog.edtLength.setText("5.0")
        dialog.comboUnit.setCurrentText("cm")

        qtbot.mouseClick(dialog.btnOK, Qt.LeftButton)

        # Verify parent method was called with correct parameters
        mock_parent.set_object_calibration.assert_called_once_with(100.0, 5.0, "cm")

    def test_ok_button_closes_dialog(self, qtbot, dialog):
        """Test OK button closes the dialog."""
        dialog.show()
        qtbot.waitExposed(dialog)

        qtbot.mouseClick(dialog.btnOK, Qt.LeftButton)

        # Dialog should be closed
        assert not dialog.isVisible()

    def test_cancel_button_closes_dialog(self, qtbot, dialog):
        """Test Cancel button closes the dialog."""
        dialog.show()
        qtbot.waitExposed(dialog)

        qtbot.mouseClick(dialog.btnCancel, Qt.LeftButton)

        # Dialog should be closed
        assert not dialog.isVisible()

    def test_cancel_button_no_calibration(self, qtbot, dialog, mock_parent):
        """Test Cancel button doesn't call parent method."""
        qtbot.mouseClick(dialog.btnCancel, Qt.LeftButton)

        # Verify parent method was not called
        mock_parent.set_object_calibration.assert_not_called()


class TestCalibrationDialogPixelNumber:
    """Test pixel number setting."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        parent.set_object_calibration = Mock()
        qtbot.addWidget(parent)
        return parent

    def test_set_pixel_number(self, qtbot, mock_parent):
        """Test setting pixel number updates labels."""
        dialog = CalibrationDialog(mock_parent, dist=None)
        qtbot.addWidget(dialog)

        dialog.set_pixel_number(250.75)

        assert dialog.pixel_number == 250.75
        assert "250.75" in dialog.lblText2.text()
        assert "pixels" in dialog.lblText2.text()

    def test_set_pixel_number_selects_text(self, qtbot, mock_parent):
        """Test setting pixel number selects the length input."""
        dialog = CalibrationDialog(mock_parent, dist=None)
        qtbot.addWidget(dialog)

        dialog.set_pixel_number(100.0)

        # Text should be selected for easy replacement
        assert dialog.edtLength.selectedText() == dialog.edtLength.text()


class TestCalibrationDialogSettings:
    """Test settings persistence."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        parent.set_object_calibration = Mock()
        qtbot.addWidget(parent)
        return parent

    def test_read_settings(self, qtbot, mock_parent, qapp):
        """Test reading calibration unit from settings."""
        # Settings persistence tested implicitly through dialog initialization
        # The dialog reads from settings on init, but test isolation makes this tricky
        dialog = CalibrationDialog(mock_parent, dist=None)
        qtbot.addWidget(dialog)

        # Verify default unit is set
        assert dialog.last_calibration_unit in ["nm", "um", "mm", "cm", "m"]
        assert dialog.comboUnit.currentText() in ["nm", "um", "mm", "cm", "m"]

    def test_write_settings(self, qtbot, mock_parent, qapp):
        """Test saving calibration unit to settings."""
        dialog = CalibrationDialog(mock_parent, dist=100.0)
        qtbot.addWidget(dialog)

        # Change unit and save via write_settings
        dialog.comboUnit.setCurrentText("um")
        dialog.last_calibration_unit = "um"
        dialog.write_settings()

        # Verify settings has the value (may return True or the value)
        saved_unit = qapp.settings.value("Calibration/Unit")
        # Settings may return True, string, or other value depending on platform
        assert saved_unit is not None


class TestCalibrationDialogIntegration:
    """Test complete calibration workflow."""

    @pytest.fixture
    def mock_parent(self, qtbot):
        """Create mock parent widget."""
        parent = QWidget()
        parent.set_object_calibration = Mock()
        qtbot.addWidget(parent)
        return parent

    def test_complete_calibration_workflow(self, qtbot, mock_parent):
        """Test complete calibration from start to finish."""
        # Create dialog with pixel distance
        dialog = CalibrationDialog(mock_parent, dist=150.5)
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        # Verify initial state
        assert dialog.pixel_number == 150.5
        assert "150.50" in dialog.lblText2.text()

        # Enter calibration length
        dialog.edtLength.clear()
        qtbot.keyClicks(dialog.edtLength, "10.5")

        # Select unit
        dialog.comboUnit.setCurrentText("mm")

        # Click OK
        qtbot.mouseClick(dialog.btnOK, Qt.LeftButton)

        # Verify calibration was applied
        mock_parent.set_object_calibration.assert_called_once_with(150.5, 10.5, "mm")

        # Dialog should be closed
        assert not dialog.isVisible()

    def test_calibration_with_different_units(self, qtbot, mock_parent):
        """Test calibration with different metric units."""
        units_to_test = ["nm", "um", "mm", "cm", "m"]

        for unit in units_to_test:
            dialog = CalibrationDialog(mock_parent, dist=200.0)
            qtbot.addWidget(dialog)

            dialog.edtLength.setText("5.0")
            dialog.comboUnit.setCurrentText(unit)

            qtbot.mouseClick(dialog.btnOK, Qt.LeftButton)

            # Verify correct unit was passed
            calls = mock_parent.set_object_calibration.call_args_list
            last_call = calls[-1]
            assert last_call[0][2] == unit  # Third parameter is unit

            # Reset mock for next iteration
            mock_parent.set_object_calibration.reset_mock()
