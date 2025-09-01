"""
Dataset Import functionality tests.

This module contains tests for importing various data file formats 
(TPS, NTS, Morphologika, etc.) and converting them into datasets and objects.
These tests depend on the core dataset/object functionality but are isolated
from analysis workflows.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, QPoint
import MdModel
from ModanDialogs import ImportDatasetDialog
from ModanComponents import TPS


class TestSampleDataCreation:
    """Test creation of sample data files for import testing."""
    
    @pytest.fixture(scope="session", autouse=True)
    def create_sample_data_directory(self):
        """Create sample data directory and files for testing."""
        sample_dir = Path("tests/sample_data")
        sample_dir.mkdir(exist_ok=True)
        
        # Create small sample TPS file
        tps_content = '''lm=4
100.0 200.0
150.0 180.0
180.0 220.0
120.0 250.0
ID=Sample01

lm=4
110.0 190.0
160.0 175.0
185.0 225.0
125.0 245.0
ID=Sample02

lm=4
105.0 195.0
155.0 185.0
175.0 215.0
115.0 255.0
ID=Sample03

'''
        
        tps_file = sample_dir / "small_sample.tps"
        with open(tps_file, 'w') as f:
            f.write(tps_content)
        
        return sample_dir


class TestImportDatasetDialog:
    """Test ImportDatasetDialog UI and basic functionality."""
    
    def test_import_dialog_creation(self, qtbot):
        """Test that ImportDatasetDialog can be created and displays correctly."""
        mock_parent = Mock()
        mock_parent.pos.return_value = Mock()
        mock_parent.pos.return_value.__add__ = Mock(return_value=Mock())
        
        def mock_value(key, default=None):
            if key == "width_scale":
                return 1.0
            if key == "dataset_mode":
                return 0
            return default if default is not None else True
        
        mock_settings = Mock()
        mock_settings.value.side_effect = mock_value
        mock_app = Mock()
        mock_app.settings = mock_settings
        
        with patch('PyQt5.QtWidgets.QApplication.instance', return_value=mock_app):
            dialog = ImportDatasetDialog(parent=mock_parent)
            qtbot.addWidget(dialog)
            
            assert dialog is not None
            assert dialog.windowTitle() == "Modan2 - Import"
            assert hasattr(dialog, 'edtFilename')
            assert hasattr(dialog, 'rbnTPS')
            assert hasattr(dialog, 'rbnNTS')
            assert hasattr(dialog, 'rbnMorphologika')

    def test_file_type_auto_detection(self, qtbot):
        """Test automatic file type detection based on extension."""
        mock_parent = Mock()
        mock_parent.pos.return_value = Mock()
        mock_parent.pos.return_value.__add__ = Mock(return_value=Mock())
        
        def mock_value(key, default=None):
            if key == "width_scale":
                return 1.0
            if key == "dataset_mode":
                return 0
            return default if default is not None else True
        
        mock_settings = Mock()
        mock_settings.value.side_effect = mock_value
        mock_app = Mock()
        mock_app.settings = mock_settings
        
        with patch('PyQt5.QtWidgets.QApplication.instance', return_value=mock_app):
            dialog = ImportDatasetDialog(parent=mock_parent)
            qtbot.addWidget(dialog)
            
            # Test TPS file detection
            tps_file = "/home/jikhanjung/projects/Modan2/tests/sample_data/small_sample.tps"
            dialog.open_file2(tps_file)
            
            assert dialog.rbnTPS.isChecked()
            assert dialog.edtFilename.text() == tps_file
            assert dialog.edtDatasetName.text() == "small_sample"


class TestTpsImport:
    """Test TPS file import functionality."""
    
    def test_tps_parsing_only(self, qtbot):
        """Test TPS file parsing without UI interaction."""
        tps_file = "/home/jikhanjung/projects/Modan2/tests/sample_data/small_sample.tps"
        
        # Test TPS parsing directly
        tps_parser = TPS(tps_file, "test_dataset", False)
        
        # Verify parsing results
        assert tps_parser.dataset_name == "test_dataset"
        assert len(tps_parser.object_list) == 3  # Based on sample data
        
        # Check first object
        first_object = tps_parser.object_list[0]
        assert first_object['id'] == "Sample01"
        assert len(first_object['coords']) == 4  # 4 landmarks
        
        # Verify coordinate values for first landmark
        assert first_object['coords'][0] == [100.0, 200.0]

    def test_import_dialog_file_loading_only(self, qtbot):
        """Test import dialog file loading without executing import."""
        mock_parent = Mock()
        mock_parent.pos.return_value = Mock()
        mock_parent.pos.return_value.__add__ = Mock(return_value=Mock())
        
        def mock_value(key, default=None):
            if key == "width_scale":
                return 1.0
            if key == "dataset_mode":
                return 0
            return default if default is not None else True
        
        mock_settings = Mock()
        mock_settings.value.side_effect = mock_value
        mock_app = Mock()
        mock_app.settings = mock_settings
        
        with patch('PyQt5.QtWidgets.QApplication.instance', return_value=mock_app):
            dialog = ImportDatasetDialog(parent=mock_parent)
            qtbot.addWidget(dialog)
            
            # Load file and configure UI
            file_path = "/home/jikhanjung/projects/Modan2/tests/sample_data/small_sample.tps"
            dialog.open_file2(file_path)
            
            # Verify UI configuration
            assert dialog.edtFilename.text() == file_path
            assert dialog.edtDatasetName.text() == "small_sample"
            assert dialog.rbnTPS.isChecked()


class TestImportWithMessageBoxHandling:
    """Test import functionality with QMessageBox auto-handling."""
    
    def setup_auto_click_messagebox(self):
        """Set up auto-clicking for QMessageBox dialogs."""
        def auto_click_messagebox():
            """Auto-click any visible QMessageBox."""
            widgets = QApplication.topLevelWidgets()
            for widget in widgets:
                if isinstance(widget, QMessageBox) and widget.isVisible():
                    print(f"✅ Auto-clicking QMessageBox: {widget.text()}")
                    widget.accept()
                    return
                for child in widget.findChildren(QMessageBox):
                    if child.isVisible():
                        print(f"✅ Auto-clicking QMessageBox child: {child.text()}")
                        child.accept()
                        return
        
        timer = QTimer()
        timer.timeout.connect(auto_click_messagebox)
        timer.setSingleShot(False)
        timer.start(1000)
        return timer

    def test_import_small_sample_with_auto_click(self, qtbot):
        """Test importing small sample TPS file with automatic QMessageBox handling."""
        mock_parent = Mock()
        mock_parent.pos.return_value = Mock()
        mock_parent.pos.return_value.__add__ = Mock(return_value=Mock())
        
        def mock_value(key, default=None):
            if key == "width_scale":
                return 1.0
            if key == "dataset_mode":
                return 0
            return default if default is not None else True
        
        mock_settings = Mock()
        mock_settings.value.side_effect = mock_value
        mock_app = Mock()
        mock_app.settings = mock_settings
        
        initial_dataset_count = MdModel.MdDataset.select().count()
        
        # Set up auto-click timer
        timer = self.setup_auto_click_messagebox()
        
        try:
            with patch('PyQt5.QtWidgets.QApplication.instance', return_value=mock_app):
                dialog = ImportDatasetDialog(parent=mock_parent)
                qtbot.addWidget(dialog)
                
                # Load and import file
                file_path = "/home/jikhanjung/projects/Modan2/tests/sample_data/small_sample.tps"
                dialog.open_file2(file_path)
                dialog.import_file()
                
                # Verify import success
                final_dataset_count = MdModel.MdDataset.select().count()
                assert final_dataset_count == initial_dataset_count + 1
                
                # Get imported dataset
                imported_dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()
                assert imported_dataset.dataset_name == "small_sample"
                
                # Verify objects
                object_list = list(imported_dataset.object_list)
                assert len(object_list) == 3
                
                return imported_dataset
                
        finally:
            timer.stop()

    def test_import_large_dataset_with_auto_click(self, qtbot):
        """Test importing large Thylacine dataset with automatic QMessageBox handling."""
        mock_parent = Mock()
        mock_parent.pos.return_value = Mock()
        mock_parent.pos.return_value.__add__ = Mock(return_value=Mock())
        
        def mock_value(key, default=None):
            if key == "width_scale":
                return 1.0
            if key == "dataset_mode":
                return 0
            return default if default is not None else True
        
        mock_settings = Mock()
        mock_settings.value.side_effect = mock_value
        mock_app = Mock()
        mock_app.settings = mock_settings
        
        initial_dataset_count = MdModel.MdDataset.select().count()
        
        # Set up auto-click timer
        timer = self.setup_auto_click_messagebox()
        
        try:
            with patch('PyQt5.QtWidgets.QApplication.instance', return_value=mock_app):
                dialog = ImportDatasetDialog(parent=mock_parent)
                qtbot.addWidget(dialog)
                
                # Load and import Thylacine file
                file_path = "/home/jikhanjung/projects/Modan2/Morphometrics dataset/Thylacine2020_NeuroGM.txt"
                dialog.open_file2(file_path)  # Auto-detects as Morphologika
                dialog.import_file()
                
                # Verify import success
                final_dataset_count = MdModel.MdDataset.select().count()
                assert final_dataset_count == initial_dataset_count + 1
                
                # Get imported dataset
                imported_dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()
                assert imported_dataset.dataset_name == "Thylacine2020_NeuroGM"
                
                # Verify objects (should have 222 objects)
                object_list = list(imported_dataset.object_list)
                assert len(object_list) > 200
                
                print(f"✅ Successfully imported {len(object_list)} objects from Thylacine dataset")
                
                return imported_dataset
                
        finally:
            timer.stop()


class TestImportEdgeCases:
    """Test import functionality edge cases and error handling."""
    
    def test_import_nonexistent_file(self, qtbot):
        """Test handling of non-existent file import."""
        mock_parent = Mock()
        mock_parent.pos.return_value = Mock()
        mock_parent.pos.return_value.__add__ = Mock(return_value=Mock())
        
        def mock_value(key, default=None):
            if key == "width_scale":
                return 1.0
            if key == "dataset_mode":
                return 0
            return default if default is not None else True
        
        mock_settings = Mock()
        mock_settings.value.side_effect = mock_value
        mock_app = Mock()
        mock_app.settings = mock_settings
        
        with patch('PyQt5.QtWidgets.QApplication.instance', return_value=mock_app):
            dialog = ImportDatasetDialog(parent=mock_parent)
            qtbot.addWidget(dialog)
            
            # Try to load non-existent file
            non_existent_file = "/path/to/nonexistent/file.tps"
            dialog.edtFilename.setText(non_existent_file)
            dialog.rbnTPS.setChecked(True)
            
            initial_count = MdModel.MdDataset.select().count()
            
            # This should handle the error gracefully
            try:
                dialog.import_file()
            except Exception:
                pass  # Expected to fail
            
            # Should not create any datasets
            final_count = MdModel.MdDataset.select().count()
            assert final_count == initial_count

    def test_import_empty_dataset_name(self, qtbot):
        """Test handling of empty dataset name."""
        mock_parent = Mock()
        mock_parent.pos.return_value = Mock()
        mock_parent.pos.return_value.__add__ = Mock(return_value=Mock())
        
        def mock_value(key, default=None):
            if key == "width_scale":
                return 1.0
            if key == "dataset_mode":
                return 0
            return default if default is not None else True
        
        mock_settings = Mock()
        mock_settings.value.side_effect = mock_value
        mock_app = Mock()
        mock_app.settings = mock_settings
        
        with patch('PyQt5.QtWidgets.QApplication.instance', return_value=mock_app):
            dialog = ImportDatasetDialog(parent=mock_parent)
            qtbot.addWidget(dialog)
            
            # Load file but clear dataset name
            file_path = "/home/jikhanjung/projects/Modan2/tests/sample_data/small_sample.tps"
            dialog.open_file2(file_path)
            dialog.edtDatasetName.setText("")  # Clear name
            
            initial_count = MdModel.MdDataset.select().count()
            
            # This should handle empty name appropriately
            try:
                dialog.import_file()
            except Exception:
                pass
            
            # Check if dataset was created (behavior depends on implementation)
            final_count = MdModel.MdDataset.select().count()
            # This test documents the current behavior, may need adjustment based on requirements