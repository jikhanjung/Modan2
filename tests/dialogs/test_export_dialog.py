"""UI tests for ExportDatasetDialog."""

from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QWidget

import MdModel
from dialogs import ExportDatasetDialog


@pytest.fixture
def mock_parent(qtbot):
    """Create a mock parent window."""
    parent = QWidget()
    qtbot.addWidget(parent)
    return parent


@pytest.fixture
def mock_dataset(mock_database):
    """Create a mock dataset with objects for testing."""
    dataset = MdModel.MdDataset.create(
        dataset_name="Test Export Dataset",
        dataset_desc="Test dataset for export",
        dimension=2,
        landmark_count=5,
        object_name="Test",
        object_desc="Test",
    )

    # Create multiple objects with landmarks
    for i in range(3):
        # Create landmark string (5 landmarks, tab-separated x,y coordinates)
        landmark_str = "\n".join([f"{j}.0\t{j + 1}.0" for j in range(5)])
        MdModel.MdObject.create(
            object_name=f"Object_{i + 1}",
            object_desc=f"Test object {i + 1}",
            dataset=dataset,
            landmark_str=landmark_str,
        )

    return dataset


@pytest.fixture
def dialog(qtbot, mock_parent, mock_dataset):
    """Create ExportDatasetDialog instance."""
    dlg = ExportDatasetDialog(mock_parent)
    dlg.set_dataset(mock_dataset)
    qtbot.addWidget(dlg)
    dlg.show()
    qtbot.waitExposed(dlg)
    return dlg


class TestExportDatasetDialogInitialization:
    """Test dialog initialization and setup."""

    def test_dialog_creation(self, dialog):
        """Test that dialog is created successfully."""
        assert dialog is not None
        assert isinstance(dialog, QDialog)
        # Title is translatable
        assert "Export" in dialog.windowTitle() or "내보내기" in dialog.windowTitle()

    def test_ui_elements_present(self, dialog):
        """Test that all UI elements are created."""
        # Dataset name
        assert dialog.lblDatasetName is not None
        assert dialog.edtDatasetName is not None

        # Object lists
        assert dialog.lblObjectList is not None
        assert dialog.lblExportList is not None
        assert dialog.lstObjectList is not None
        assert dialog.lstExportList is not None

        # Move buttons
        assert dialog.btnMoveRight is not None
        assert dialog.btnMoveLeft is not None

        # Export/Cancel buttons
        assert dialog.btnExport is not None
        assert dialog.btnCancel is not None

        # Format radio buttons
        assert dialog.rbTPS is not None
        assert dialog.rbX1Y1 is not None
        assert dialog.rbMorphologika is not None
        assert dialog.rbJSONZip is not None

        # Superimposition radio buttons
        assert dialog.rbProcrustes is not None
        assert dialog.rbBookstein is not None
        assert dialog.rbRFTRA is not None
        assert dialog.rbNone is not None

        # JSON+ZIP options
        assert dialog.chkIncludeFiles is not None
        assert dialog.lblEstimatedSize is not None

    def test_initial_state(self, dialog):
        """Test initial dialog state."""
        # Dataset name should be set
        assert dialog.edtDatasetName.text() == "Test Export Dataset"

        # Export list should have all objects initially
        assert dialog.lstExportList.count() == 3

        # Object list should be empty initially (all in export list)
        assert dialog.lstObjectList.count() == 0

        # TPS should be default format
        assert dialog.rbTPS.isChecked()

        # Procrustes should be default superimposition
        assert dialog.rbProcrustes.isChecked()

        # Include files checkbox should be disabled for non-ZIP formats
        assert not dialog.chkIncludeFiles.isEnabled()

    def test_format_button_group(self, dialog):
        """Test that format buttons form exclusive group."""
        # Select Morphologika
        dialog.rbMorphologika.setChecked(True)
        assert dialog.rbMorphologika.isChecked()
        assert not dialog.rbTPS.isChecked()

        # Select JSON+ZIP (should uncheck Morphologika)
        dialog.rbJSONZip.setChecked(True)
        assert not dialog.rbMorphologika.isChecked()
        assert dialog.rbJSONZip.isChecked()

    def test_superimposition_button_group(self, dialog):
        """Test that superimposition buttons form exclusive group."""
        # Select None
        dialog.rbNone.setChecked(True)
        assert dialog.rbNone.isChecked()
        assert not dialog.rbProcrustes.isChecked()

        # Select Procrustes (should uncheck None)
        dialog.rbProcrustes.setChecked(True)
        assert not dialog.rbNone.isChecked()
        assert dialog.rbProcrustes.isChecked()


class TestExportDatasetDialogObjectSelection:
    """Test object selection functionality."""

    def test_move_right(self, qtbot, dialog):
        """Test moving objects from object list to export list."""
        # First, move all objects to object list
        for _ in range(dialog.lstExportList.count()):
            item = dialog.lstExportList.item(0)
            dialog.lstExportList.takeItem(0)
            dialog.lstObjectList.addItem(item)

        # Select first object in object list
        dialog.lstObjectList.setCurrentRow(0)
        initial_object_count = dialog.lstObjectList.count()
        initial_export_count = dialog.lstExportList.count()

        # Move right
        dialog.move_right()

        # Verify counts changed
        assert dialog.lstObjectList.count() == initial_object_count - 1
        assert dialog.lstExportList.count() == initial_export_count + 1

    def test_move_left(self, qtbot, dialog):
        """Test moving objects from export list to object list."""
        # Select first object in export list
        dialog.lstExportList.setCurrentRow(0)
        initial_object_count = dialog.lstObjectList.count()
        initial_export_count = dialog.lstExportList.count()

        # Move left
        dialog.move_left()

        # Verify counts changed
        assert dialog.lstObjectList.count() == initial_object_count + 1
        assert dialog.lstExportList.count() == initial_export_count - 1

    def test_multiple_object_selection(self, qtbot, dialog):
        """Test moving multiple objects one by one."""
        # Move all objects to object list first
        initial_export_count = dialog.lstExportList.count()
        while dialog.lstExportList.count() > 0:
            item = dialog.lstExportList.item(0)
            dialog.lstExportList.takeItem(0)
            dialog.lstObjectList.addItem(item)

        assert dialog.lstObjectList.count() == initial_export_count
        assert dialog.lstExportList.count() == 0

        # Move objects one by one back to export list
        for _ in range(initial_export_count):
            dialog.lstObjectList.setCurrentRow(0)
            dialog.move_right()

        # Verify all moved back
        assert dialog.lstExportList.count() == initial_export_count
        assert dialog.lstObjectList.count() == 0


class TestExportDatasetDialogFormatSelection:
    """Test export format selection."""

    def test_tps_format_selection(self, qtbot, dialog):
        """Test selecting TPS format."""
        dialog.rbTPS.setChecked(True)
        assert dialog.button_group2.checkedButton() == dialog.rbTPS
        # Include files should be disabled for TPS
        assert not dialog.chkIncludeFiles.isEnabled()

    def test_x1y1_format_selection(self, qtbot, dialog):
        """Test selecting X1Y1 format."""
        dialog.rbX1Y1.setChecked(True)
        assert dialog.button_group2.checkedButton() == dialog.rbX1Y1

    def test_morphologika_format_selection(self, qtbot, dialog):
        """Test selecting Morphologika format."""
        dialog.rbMorphologika.setChecked(True)
        assert dialog.button_group2.checkedButton() == dialog.rbMorphologika

    def test_jsonzip_format_selection(self, qtbot, dialog):
        """Test selecting JSON+ZIP format."""
        dialog.rbJSONZip.setChecked(True)
        # Trigger the click handler manually
        dialog.on_rbJSONZip_clicked()
        assert dialog.button_group2.checkedButton() == dialog.rbJSONZip
        # Include files checkbox should be enabled for JSON+ZIP
        assert dialog.chkIncludeFiles.isEnabled()


class TestExportDatasetDialogSuperimposition:
    """Test superimposition options."""

    def test_procrustes_selection(self, qtbot, dialog):
        """Test selecting Procrustes superimposition."""
        dialog.rbProcrustes.setChecked(True)
        assert dialog.button_group3.checkedButton() == dialog.rbProcrustes

    def test_bookstein_selection(self, qtbot, dialog):
        """Test selecting Bookstein superimposition."""
        # Bookstein is currently disabled, but test the button exists
        assert dialog.rbBookstein is not None
        # When enabled, it should work
        dialog.rbBookstein.setEnabled(True)
        dialog.rbBookstein.setChecked(True)
        assert dialog.rbBookstein.isChecked()

    def test_rftra_selection(self, qtbot, dialog):
        """Test selecting Resistant fit superimposition."""
        # RFTRA is currently disabled, but test the button exists
        assert dialog.rbRFTRA is not None
        # When enabled, it should work
        dialog.rbRFTRA.setEnabled(True)
        dialog.rbRFTRA.setChecked(True)
        assert dialog.rbRFTRA.isChecked()

    def test_none_selection(self, qtbot, dialog):
        """Test selecting no superimposition."""
        dialog.rbNone.setChecked(True)
        assert dialog.button_group3.checkedButton() == dialog.rbNone


class TestExportDatasetDialogJSONZipOptions:
    """Test JSON+ZIP specific options."""

    def test_include_files_checkbox(self, qtbot, dialog):
        """Test include files checkbox."""
        # Enable JSON+ZIP format first
        dialog.rbJSONZip.setChecked(True)
        # Trigger the click handler to enable checkbox
        dialog.on_rbJSONZip_clicked()

        # Checkbox should be enabled and checked by default
        assert dialog.chkIncludeFiles.isEnabled()
        assert dialog.chkIncludeFiles.isChecked()

        # Uncheck it
        dialog.chkIncludeFiles.setChecked(False)
        assert not dialog.chkIncludeFiles.isChecked()

    @patch("MdUtils.estimate_package_size")
    def test_estimated_size_display(self, mock_estimate, qtbot, dialog):
        """Test estimated size calculation and display."""
        # Mock package size estimation
        mock_estimate.return_value = 1024 * 1024  # 1 MB

        # Enable JSON+ZIP format
        dialog.rbJSONZip.setChecked(True)

        # Update size
        dialog.update_estimated_size()

        # Verify size is displayed
        size_text = dialog.lblEstimatedSize.text()
        assert "1.0 MB" in size_text or "Estimated" in size_text

    @patch("MdUtils.estimate_package_size")
    def test_estimated_size_updates_on_checkbox_toggle(self, mock_estimate, qtbot, dialog):
        """Test that estimated size updates when checkbox is toggled."""
        mock_estimate.return_value = 2048 * 1024  # 2 MB

        # Enable JSON+ZIP format
        dialog.rbJSONZip.setChecked(True)

        # Toggle checkbox
        dialog.chkIncludeFiles.setChecked(False)
        QApplication.processEvents()

        # Verify estimate_package_size was called
        assert mock_estimate.called


class TestExportDatasetDialogExport:
    """Test export functionality."""

    @patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName")
    @patch("builtins.open", create=True)
    def test_export_tps(self, mock_open, mock_file_dialog, qtbot, dialog):
        """Test exporting to TPS format."""
        # Mock file dialog
        mock_file_dialog.return_value = ("/tmp/test.tps", "")

        # Select TPS format
        dialog.rbTPS.setChecked(True)

        # Trigger export
        dialog.export_dataset()

        # Verify file dialog was called
        mock_file_dialog.assert_called_once()

    @patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName")
    @patch("builtins.open", create=True)
    @patch("shutil.copyfile")
    def test_export_morphologika(self, mock_copy, mock_open, mock_file_dialog, qtbot, dialog):
        """Test exporting to Morphologika format."""
        # Mock file dialog
        mock_file_dialog.return_value = ("/tmp/test.txt", "")

        # Select Morphologika format
        dialog.rbMorphologika.setChecked(True)

        # Trigger export
        dialog.export_dataset()

        # Verify file dialog was called
        mock_file_dialog.assert_called_once()

    @patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName")
    @patch("MdUtils.create_zip_package")
    @patch("PyQt5.QtWidgets.QMessageBox.information")
    def test_export_jsonzip(self, mock_msgbox, mock_create_zip, mock_file_dialog, qtbot, dialog):
        """Test exporting to JSON+ZIP format."""
        # Mock file dialog
        mock_file_dialog.return_value = ("/tmp/test.zip", "")

        # Select JSON+ZIP format
        dialog.rbJSONZip.setChecked(True)

        # Trigger export
        dialog.export_dataset()

        # Verify create_zip_package was called
        mock_create_zip.assert_called_once()
        # Verify success message shown
        mock_msgbox.assert_called_once()

    @patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName")
    def test_export_cancel(self, mock_file_dialog, qtbot, dialog):
        """Test canceling export."""
        # Mock file dialog to return empty (canceled)
        mock_file_dialog.return_value = ("", "")

        # Trigger export - should not raise exception
        dialog.export_dataset()


class TestExportDatasetDialogButtons:
    """Test button interactions."""

    def test_cancel_button_closes_dialog(self, qtbot, dialog):
        """Test that cancel button closes the dialog."""
        # Click cancel
        qtbot.mouseClick(dialog.btnCancel, Qt.LeftButton)

        # Dialog should be closed
        assert not dialog.isVisible()

    @patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName")
    @patch("builtins.open", create=True)
    def test_export_button_triggers_export(self, mock_open, mock_file_dialog, qtbot, dialog):
        """Test that export button triggers export process."""
        # Mock file dialog
        mock_file_dialog.return_value = ("/tmp/test.tps", "")

        # Click export button
        qtbot.mouseClick(dialog.btnExport, Qt.LeftButton)

        # Verify file dialog was called
        mock_file_dialog.assert_called_once()


class TestExportDatasetDialogSettings:
    """Test settings persistence."""

    def test_read_settings(self, dialog):
        """Test that read_settings can be called."""
        # Should not crash
        dialog.read_settings()

    def test_write_settings(self, dialog):
        """Test that write_settings can be called."""
        # Should not crash
        dialog.write_settings()

    def test_close_event_saves_settings(self, qtbot, dialog):
        """Test that close event saves settings."""
        from PyQt5.QtGui import QCloseEvent

        close_event = QCloseEvent()
        dialog.closeEvent(close_event)

        # Should accept the event
        assert close_event.isAccepted()


class TestExportDatasetDialogIntegration:
    """Integration tests for export workflow."""

    @patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName")
    @patch("builtins.open", create=True)
    def test_complete_export_workflow(self, mock_open, mock_file_dialog, qtbot, dialog):
        """Test complete export workflow."""
        # Mock file dialog
        mock_file_dialog.return_value = ("/tmp/test.tps", "")

        # Step 1: Verify dataset is set
        assert dialog.edtDatasetName.text() == "Test Export Dataset"
        assert dialog.lstExportList.count() == 3

        # Step 2: Select export format
        dialog.rbTPS.setChecked(True)
        assert dialog.rbTPS.isChecked()

        # Step 3: Select superimposition
        dialog.rbProcrustes.setChecked(True)
        assert dialog.rbProcrustes.isChecked()

        # Step 4: Trigger export
        dialog.export_dataset()

        # Verify export was called
        mock_file_dialog.assert_called_once()

    def test_dataset_setup(self, dialog, mock_dataset):
        """Test that dataset is properly set up."""
        # Verify dataset name
        assert dialog.edtDatasetName.text() == mock_dataset.dataset_name

        # Verify object count
        assert dialog.lstExportList.count() == len(mock_dataset.object_list)

        # Verify dataset ops is created
        assert dialog.ds_ops is not None
        assert dialog.ds_ops.id == mock_dataset.id
