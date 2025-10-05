"""End-to-end workflow tests for Modan2."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import QMimeData, QPoint, Qt, QUrl
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWidgets import QDialog, QMessageBox, QTreeWidgetItem

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.skip(reason="Workflow tests causing CI timeout - needs refactoring")
class TestCoreWorkflows:
    """Test complete user workflows."""
    
    @pytest.fixture
    def sample_tps_content(self):
        """Sample TPS file content."""
        return """LM=5
10.0 20.0
30.0 40.0
50.0 60.0
70.0 80.0
90.0 100.0
ID=specimen_001

LM=5
15.0 25.0
35.0 45.0
55.0 65.0
75.0 85.0
95.0 105.0
ID=specimen_002
"""
    
    @pytest.fixture
    def sample_tps_file(self, tmp_path, sample_tps_content):
        """Create a temporary TPS file."""
        tps_path = tmp_path / "test_workflow.tps"
        tps_path.write_text(sample_tps_content)
        return str(tps_path)
    
    def test_import_2d_landmark_workflow(self, qtbot, main_window, sample_tps_file, mock_database):
        """Test complete workflow for importing 2D landmarks."""
        import MdModel
        
        # Step 1: Create a new dataset
        with patch('ModanDialogs.MdNewDatasetDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog.exec_.return_value = QDialog.Accepted
            mock_dialog.edit_dataset_name.text.return_value = "2D Workflow Test"
            mock_dialog.edit_dataset_desc.text.return_value = "Testing 2D import"
            mock_dialog.combo_dimension.currentText.return_value = "2D"
            mock_dialog.spinbox_no_landmark.value.return_value = 5
            mock_dialog_class.return_value = mock_dialog
            
            # Trigger new dataset action
            main_window.on_action_new_dataset()
            
            # Verify dataset was created
            datasets = list(MdModel.MdDataset.select())
            assert len(datasets) > 0
            dataset = datasets[-1]
            assert dataset.dataset_name == "2D Workflow Test"
        
        # Step 2: Select the dataset in treeView
        item = QTreeWidgetItem()
        item.setText(0, dataset.dataset_name)
        item.setData(0, Qt.UserRole, dataset)
        main_window.treeView.addTopLevelItem(item)
        main_window.treeView.setCurrentItem(item)
        main_window.on_selection_changed()
        
        assert main_window.m_dataset == dataset
        
        # Step 3: Import TPS file via drag and drop
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(sample_tps_file)])
        
        # Create drop event
        drop_event = QDropEvent(
            QPoint(100, 100),
            Qt.CopyAction,
            mime_data,
            Qt.LeftButton,
            Qt.NoModifier
        )
        
        with patch.object(main_window, 'process_dropped_file') as mock_process:
            mock_process.return_value = True
            
            # Simulate drop
            main_window.dropEvent(drop_event)
            
            # Verify file was processed
            mock_process.assert_called_with(sample_tps_file)
        
        # Step 4: Verify objects were added to table
        with patch.object(main_window, 'populate_tableWidget'):
            main_window.refresh_table()
            
            # Check that table update was triggered
            main_window.populate_tableWidget.assert_called()
    
    @pytest.mark.slow
    def test_pca_analysis_workflow(self, qtbot, main_window, mock_database):
        """Test complete PCA analysis workflow."""
        import MdModel
        
        # Create dataset with multiple objects
        dataset = MdModel.MdDataset.create(
            dataset_name="PCA Test Dataset",
            dataset_desc="Dataset for PCA testing",
            dimension=2,
            landmark_count=10
        )
        
        # Add multiple objects
        for i in range(5):
            obj = MdModel.MdObject.create(
                dataset=dataset,
                object_name=f"Object_{i+1}",
                object_desc=f"Test object {i+1}"
            )
            # Add dummy landmarks
            obj.landmarks = [[j*10 + i, j*10 + i + 5] for j in range(10)]
            obj.save()
        
        # Select dataset
        main_window.m_dataset = dataset
        
        # Run PCA analysis
        with patch('ModanDialogs.MdAnalysisDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog.exec_.return_value = QDialog.Accepted
            mock_dialog.get_analysis_type.return_value = "PCA"
            mock_dialog.comboBox.currentText.return_value = "PCA"
            mock_dialog_class.return_value = mock_dialog
            
            with patch('MdStatistics.do_pca_analysis') as mock_pca:
                mock_pca.return_value = {
                    'eigenvalues': [0.5, 0.3, 0.2],
                    'eigenvectors': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                    'scores': [[1, 2, 3], [4, 5, 6]]
                }
                
                # Trigger analysis
                main_window.on_action_analysis()
                
                # Verify PCA was called
                mock_pca.assert_called()
        
        # Verify analysis result was saved
        analyses = list(MdModel.MdAnalysis.select().where(
            MdModel.MdAnalysis.dataset == dataset
        ))
        assert len(analyses) > 0
    
    def test_3d_model_import_workflow(self, qtbot, main_window, mock_database):
        """Test importing 3D model files."""
        import MdModel
        
        # Create 3D dataset
        dataset = MdModel.MdDataset.create(
            dataset_name="3D Model Test",
            dataset_desc="Testing 3D model import",
            dimension=3,
            landmark_count=0
        )
        
        main_window.m_dataset = dataset
        
        # Create temporary OBJ file
        with tempfile.NamedTemporaryFile(suffix='.obj', delete=False) as tmp_obj:
            obj_content = """# Simple cube
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
v 0.0 0.0 1.0
v 1.0 0.0 1.0
v 1.0 1.0 1.0
v 0.0 1.0 1.0
f 1 2 3 4
f 5 6 7 8
"""
            tmp_obj.write(obj_content.encode())
            obj_path = tmp_obj.name
        
        try:
            # Import OBJ file
            with patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
                mock_dialog.return_value = (obj_path, '3D Files (*.obj)')
                
                with patch.object(main_window, 'on_action_import_dataset_triggered') as mock_import:
                    mock_import.return_value = True
                    
                    main_window.on_action_import_3d()
                    
                    # Verify import was called
                    mock_import.assert_called_with(obj_path)
        finally:
            # Clean up
            Path(obj_path).unlink(missing_ok=True)
    
    def test_dataset_export_workflow(self, qtbot, main_window, mock_database):
        """Test exporting dataset to file."""
        import MdModel
        
        # Create dataset with objects
        dataset = MdModel.MdDataset.create(
            dataset_name="Export Test",
            dataset_desc="Dataset for export testing",
            dimension=2,
            landmark_count=3
        )
        
        # Add objects
        for i in range(3):
            MdModel.MdObject.create(
                dataset=dataset,
                object_name=f"Export_Object_{i+1}",
                landmarks=[[i, i+1], [i+2, i+3], [i+4, i+5]]
            )
        
        main_window.m_dataset = dataset
        
        # Export to CSV
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_csv:
            csv_path = tmp_csv.name
        
        try:
            with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
                mock_dialog.return_value = (csv_path, 'CSV Files (*.csv)')
                
                with patch.object(main_window, 'on_action_export_dataset_triggered') as mock_export:
                    mock_export.return_value = True
                    
                    main_window.on_action_export()
                    
                    # Verify export was called
                    mock_export.assert_called_with(csv_path)
        finally:
            # Clean up
            Path(csv_path).unlink(missing_ok=True)
    
    def test_object_editing_workflow(self, qtbot, main_window, mock_database):
        """Test editing object properties."""
        import MdModel
        
        # Create dataset and object
        dataset = MdModel.MdDataset.create(
            dataset_name="Edit Test",
            dataset_desc="Dataset for edit testing",
            dimension=2,
            landmark_count=5
        )
        
        obj = MdModel.MdObject.create(
            dataset=dataset,
            object_name="Original Name",
            object_desc="Original Description"
        )
        
        main_window.m_dataset = dataset
        main_window.m_object = obj
        
        # Edit object
        with patch('ModanDialogs.MdEditObjectDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog.exec_.return_value = QDialog.Accepted
            mock_dialog.edit_object_name.text.return_value = "Updated Name"
            mock_dialog.edit_object_desc.text.return_value = "Updated Description"
            mock_dialog_class.return_value = mock_dialog
            
            # Trigger edit action
            main_window.on_action_edit_object()
            
            # Verify object was updated
            obj.refresh()
            assert obj.object_name == "Updated Name"
            assert obj.object_desc == "Updated Description"
    
    def test_preferences_change_workflow(self, qtbot, main_window):
        """Test changing and applying preferences."""
        initial_icon_size = main_window.toolbar.iconSize().width()
        
        with patch('ModanDialogs.MdPreferencesDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog.exec_.return_value = QDialog.Accepted
            mock_dialog.slider_toolbar_icon_size.value.return_value = 48
            mock_dialog.slider_landmark_size.value.return_value = 5
            mock_dialog.landmark_color = "#ff0000"
            mock_dialog.wireframe_color = "#0000ff"
            mock_dialog_class.return_value = mock_dialog
            
            # Open preferences
            main_window.on_action_preferences()
            
            # Apply new settings
            with patch.object(main_window, 'apply_preferences') as mock_apply:
                mock_dialog.accepted.emit()
                mock_apply.assert_called()
    
    def test_multi_dataset_management_workflow(self, qtbot, main_window, mock_database):
        """Test managing multiple datasets."""
        import MdModel
        
        # Create multiple datasets
        datasets = []
        for i in range(3):
            ds = MdModel.MdDataset.create(
                dataset_name=f"Dataset_{i+1}",
                dataset_desc=f"Test dataset {i+1}",
                dimension=2 if i < 2 else 3,
                landmark_count=10 + i*5
            )
            datasets.append(ds)
            
            # Add to treeView
            item = QTreeWidgetItem()
            item.setText(0, ds.dataset_name)
            item.setData(0, Qt.UserRole, ds)
            main_window.treeView.addTopLevelItem(item)
        
        # Switch between datasets
        for i, ds in enumerate(datasets):
            item = main_window.treeView.topLevelItem(i)
            main_window.treeView.setCurrentItem(item)
            main_window.on_selection_changed()
            
            assert main_window.m_dataset == ds
            
            # Verify UI updates for dataset dimension
            if ds.dimension == 2:
                assert main_window.object_view_2d.isEnabled()
            else:
                assert main_window.viewer_3d.isEnabled()
    
    def test_error_recovery_workflow(self, qtbot, main_window):
        """Test error handling and recovery."""
        # Test handling missing dataset
        main_window.m_dataset = None
        
        with patch.object(QMessageBox, 'warning') as mock_warning:
            main_window.on_action_analysis()
            
            # Should show warning about no dataset
            mock_warning.assert_called()
            args = mock_warning.call_args[0]
            assert "dataset" in args[2].lower()
        
        # Test handling corrupted file
        with patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = ('/invalid/file.tps', 'TPS Files (*.tps)')
            
            with patch.object(main_window, 'show_error_message') as mock_error:
                main_window.on_action_import()
                
                # Should show error message
                mock_error.assert_called()


@pytest.mark.skip(reason="Integration tests causing CI timeout - needs refactoring")
class TestIntegrationScenarios:
    """Test integration scenarios between components."""
    
    def test_dataset_treeView_table_sync(self, qtbot, main_window, mock_database):
        """Test synchronization between treeView and table views."""
        import MdModel
        
        # Create dataset with objects
        dataset = MdModel.MdDataset.create(
            dataset_name="Sync Test",
            dataset_desc="Testing treeView-table sync",
            dimension=2,
            landmark_count=5
        )
        
        # Add objects
        objects = []
        for i in range(3):
            obj = MdModel.MdObject.create(
                dataset=dataset,
                object_name=f"Sync_Object_{i+1}"
            )
            objects.append(obj)
        
        # Add dataset to treeView
        dataset_item = QTreeWidgetItem()
        dataset_item.setText(0, dataset.dataset_name)
        dataset_item.setData(0, Qt.UserRole, dataset)
        main_window.treeView.addTopLevelItem(dataset_item)
        
        # Select dataset
        main_window.treeView.setCurrentItem(dataset_item)
        main_window.on_selection_changed()
        
        # Verify table is populated
        with patch.object(main_window, 'populate_tableWidget') as mock_populate:
            main_window.refresh_table()
            mock_populate.assert_called()
    
    def test_viewer_updates_on_object_selection(self, qtbot, main_window, mock_database):
        """Test that viewers update when object is selected."""
        import MdModel
        
        # Create dataset and object with landmarks
        dataset = MdModel.MdDataset.create(
            dataset_name="Viewer Test",
            dataset_desc="Testing viewer updates",
            dimension=2,
            landmark_count=4
        )
        
        obj = MdModel.MdObject.create(
            dataset=dataset,
            object_name="Viewer_Object",
            landmarks=[[10, 20], [30, 40], [50, 60], [70, 80]]
        )
        
        main_window.m_dataset = dataset
        main_window.m_object = obj
        
        # Trigger viewer update
        with patch.object(main_window.object_view_2d, 'show_object') as mock_show:
            main_window.on_object_selected()
            
            # Verify viewer was updated
            mock_show.assert_called_with(obj)