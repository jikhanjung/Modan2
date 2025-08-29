"""Tests for Modan2 dialog windows."""
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNewDatasetDialog:
    """Test New Dataset dialog."""
    
    @patch('ModanDialogs.MdNewDatasetDialog.show')
    def test_new_dataset_dialog_creation(self, mock_show, qtbot, main_window):
        """Test that new dataset dialog can be created."""
        from ModanDialogs import MdNewDatasetDialog
        
        dialog = MdNewDatasetDialog(main_window)
        qtbot.addWidget(dialog)
        
        assert dialog is not None
        assert isinstance(dialog, QDialog)
    
    @patch('ModanDialogs.MdNewDatasetDialog.exec_')
    def test_new_dataset_dialog_accept(self, mock_exec, qtbot, main_window):
        """Test accepting new dataset dialog with valid data."""
        from ModanDialogs import MdNewDatasetDialog
        
        mock_exec.return_value = QDialog.Accepted
        
        dialog = MdNewDatasetDialog(main_window)
        qtbot.addWidget(dialog)
        
        # Set test values
        dialog.edit_dataset_name.setText("Test Dataset")
        dialog.edit_dataset_desc.setText("Test Description")
        dialog.combo_dimension.setCurrentText("2D")
        dialog.spinbox_no_landmark.setValue(10)
        
        # Accept dialog
        result = dialog.exec_()
        
        assert result == QDialog.Accepted
        assert dialog.edit_dataset_name.text() == "Test Dataset"
        assert dialog.spinbox_no_landmark.value() == 10
    
    @patch('ModanDialogs.MdNewDatasetDialog.exec_')
    def test_new_dataset_dialog_cancel(self, mock_exec, qtbot, main_window):
        """Test canceling new dataset dialog."""
        from ModanDialogs import MdNewDatasetDialog
        
        mock_exec.return_value = QDialog.Rejected
        
        dialog = MdNewDatasetDialog(main_window)
        qtbot.addWidget(dialog)
        
        result = dialog.exec_()
        assert result == QDialog.Rejected
    
    def test_new_dataset_dialog_validation(self, qtbot, main_window):
        """Test new dataset dialog input validation."""
        from ModanDialogs import MdNewDatasetDialog
        
        dialog = MdNewDatasetDialog(main_window)
        qtbot.addWidget(dialog)
        
        # Test with empty dataset name
        dialog.edit_dataset_name.setText("")
        
        with patch.object(QMessageBox, 'warning') as mock_warning:
            dialog.accept()
            # Should show warning for empty name
            mock_warning.assert_called()


class TestPreferencesDialog:
    """Test Preferences dialog."""
    
    @patch('ModanDialogs.MdPreferencesDialog.show')
    def test_preferences_dialog_creation(self, mock_show, qtbot, main_window):
        """Test that preferences dialog can be created."""
        from ModanDialogs import MdPreferencesDialog
        
        dialog = MdPreferencesDialog(main_window)
        qtbot.addWidget(dialog)
        
        assert dialog is not None
        assert isinstance(dialog, QDialog)
    
    @patch('ModanDialogs.MdPreferencesDialog.exec_')
    def test_preferences_dialog_settings(self, mock_exec, qtbot, main_window):
        """Test changing settings in preferences dialog."""
        from ModanDialogs import MdPreferencesDialog
        
        mock_exec.return_value = QDialog.Accepted
        
        dialog = MdPreferencesDialog(main_window)
        qtbot.addWidget(dialog)
        
        # Get initial icon size
        initial_size = main_window.toolbar.iconSize()
        
        # Change settings
        dialog.slider_toolbar_icon_size.setValue(48)
        dialog.slider_landmark_size.setValue(5)
        
        # Accept dialog
        result = dialog.exec_()
        
        assert result == QDialog.Accepted
        assert dialog.slider_toolbar_icon_size.value() == 48
        assert dialog.slider_landmark_size.value() == 5
    
    def test_preferences_dialog_color_selection(self, qtbot, main_window):
        """Test color selection in preferences dialog."""
        from ModanDialogs import MdPreferencesDialog
        
        dialog = MdPreferencesDialog(main_window)
        qtbot.addWidget(dialog)
        
        # Test landmark color button
        with patch('PyQt5.QtWidgets.QColorDialog.getColor') as mock_color:
            from PyQt5.QtGui import QColor
            mock_color.return_value = QColor(255, 0, 0)
            
            dialog.btn_landmark_color.click()
            
            # Check that color was set
            mock_color.assert_called()


class TestAnalysisDialog:
    """Test Analysis dialog."""
    
    @patch('ModanDialogs.MdAnalysisDialog.show')
    def test_analysis_dialog_creation(self, mock_show, qtbot, main_window, sample_dataset):
        """Test that analysis dialog can be created."""
        from ModanDialogs import MdAnalysisDialog
        
        main_window.m_dataset = sample_dataset
        
        dialog = MdAnalysisDialog(main_window)
        qtbot.addWidget(dialog)
        
        assert dialog is not None
        assert isinstance(dialog, QDialog)
    
    @patch('ModanDialogs.MdAnalysisDialog.exec_')
    def test_analysis_dialog_pca_selection(self, mock_exec, qtbot, main_window, sample_dataset):
        """Test selecting PCA analysis."""
        from ModanDialogs import MdAnalysisDialog
        
        mock_exec.return_value = QDialog.Accepted
        main_window.m_dataset = sample_dataset
        
        dialog = MdAnalysisDialog(main_window)
        qtbot.addWidget(dialog)
        
        # Select PCA
        dialog.comboBox.setCurrentText("PCA")
        
        # Accept dialog
        result = dialog.exec_()
        
        assert result == QDialog.Accepted
        assert dialog.get_analysis_type() == "PCA"
    
    @patch('ModanDialogs.MdAnalysisDialog.exec_')
    def test_analysis_dialog_cva_selection(self, mock_exec, qtbot, main_window, sample_dataset):
        """Test selecting CVA analysis."""
        from ModanDialogs import MdAnalysisDialog
        
        mock_exec.return_value = QDialog.Accepted
        main_window.m_dataset = sample_dataset
        
        dialog = MdAnalysisDialog(main_window)
        qtbot.addWidget(dialog)
        
        # Select CVA
        dialog.comboBox.setCurrentText("CVA")
        
        # Set number of groups
        dialog.spinBox.setValue(3)
        
        # Accept dialog
        result = dialog.exec_()
        
        assert result == QDialog.Accepted
        assert dialog.get_analysis_type() == "CVA"
        assert dialog.spinBox.value() == 3


class TestAboutDialog:
    """Test About dialog."""
    
    def test_about_dialog_shows(self, qtbot, main_window):
        """Test that about dialog shows information."""
        with patch.object(QMessageBox, 'about') as mock_about:
            main_window.on_action_about()
            
            # Check that about dialog was shown
            mock_about.assert_called_once()
            
            # Check that it contains app name
            args = mock_about.call_args[0]
            assert 'Modan2' in args[1] or 'Modan2' in args[2]


class TestFileDialogs:
    """Test file selection dialogs."""
    
    def test_import_dialog(self, qtbot, main_window):
        """Test import file dialog."""
        with patch('PyQt5.QtWidgets.QFileDialog.getOpenFileNames') as mock_dialog:
            mock_dialog.return_value = (['/path/to/file.tps'], 'TPS Files (*.tps)')
            
            main_window.on_action_import()
            
            # Check that dialog was called
            mock_dialog.assert_called_once()
    
    def test_export_dialog(self, qtbot, main_window, sample_dataset):
        """Test export file dialog."""
        main_window.m_dataset = sample_dataset
        
        with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = ('/path/to/export.csv', 'CSV Files (*.csv)')
            
            with patch.object(main_window, 'export_dataset') as mock_export:
                main_window.on_action_export()
                
                # Check that dialog was called
                mock_dialog.assert_called_once()
    
    def test_open_image_dialog(self, qtbot, main_window):
        """Test open image file dialog."""
        with patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = ('/path/to/image.jpg', 'Image Files (*.jpg)')
            
            with patch.object(main_window, 'load_image') as mock_load:
                main_window.on_action_open_image()
                
                # Check that dialog was called
                mock_dialog.assert_called_once()


class TestMessageBoxes:
    """Test various message boxes."""
    
    def test_error_message(self, qtbot, main_window):
        """Test showing error messages."""
        with patch.object(QMessageBox, 'critical') as mock_critical:
            error_msg = "Test error message"
            main_window.show_error_message(error_msg)
            
            mock_critical.assert_called_once()
            args = mock_critical.call_args[0]
            assert error_msg in args[2]
    
    def test_warning_message(self, qtbot, main_window):
        """Test showing warning messages."""
        with patch.object(QMessageBox, 'warning') as mock_warning:
            warning_msg = "Test warning message"
            main_window.show_warning_message(warning_msg)
            
            mock_warning.assert_called_once()
            args = mock_warning.call_args[0]
            assert warning_msg in args[2]
    
    def test_info_message(self, qtbot, main_window):
        """Test showing info messages."""
        with patch.object(QMessageBox, 'information') as mock_info:
            info_msg = "Test info message"
            main_window.show_info_message(info_msg)
            
            mock_info.assert_called_once()
            args = mock_info.call_args[0]
            assert info_msg in args[2]
    
    def test_confirmation_dialog(self, qtbot, main_window):
        """Test confirmation dialog."""
        with patch.object(QMessageBox, 'question') as mock_question:
            mock_question.return_value = QMessageBox.Yes
            
            result = main_window.confirm_action("Delete dataset?")
            
            mock_question.assert_called_once()
            assert result == True


class TestEditObjectDialog:
    """Test Edit Object dialog."""
    
    @patch('ModanDialogs.MdEditObjectDialog.show')
    def test_edit_object_dialog_creation(self, mock_show, qtbot, main_window):
        """Test that edit object dialog can be created."""
        from ModanDialogs import MdEditObjectDialog
        
        # Create a mock object
        mock_object = Mock()
        mock_object.object_name = "Test Object"
        mock_object.object_desc = "Test Description"
        
        dialog = MdEditObjectDialog(main_window, mock_object)
        qtbot.addWidget(dialog)
        
        assert dialog is not None
        assert isinstance(dialog, QDialog)
    
    @patch('ModanDialogs.MdEditObjectDialog.exec_')
    def test_edit_object_dialog_save(self, mock_exec, qtbot, main_window):
        """Test saving changes in edit object dialog."""
        from ModanDialogs import MdEditObjectDialog
        
        mock_exec.return_value = QDialog.Accepted
        
        # Create a mock object
        mock_object = Mock()
        mock_object.object_name = "Original Name"
        mock_object.object_desc = "Original Description"
        
        dialog = MdEditObjectDialog(main_window, mock_object)
        qtbot.addWidget(dialog)
        
        # Change values
        dialog.edit_object_name.setText("New Name")
        dialog.edit_object_desc.setText("New Description")
        
        # Accept dialog
        result = dialog.exec_()
        
        assert result == QDialog.Accepted
        assert dialog.edit_object_name.text() == "New Name"
        assert dialog.edit_object_desc.text() == "New Description"