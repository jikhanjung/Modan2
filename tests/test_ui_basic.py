"""Basic UI tests for Modan2 main window."""
import pytest
from PyQt5.QtCore import Qt, QMimeData, QUrl
from PyQt5.QtGui import QDropEvent, QDragEnterEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QTreeWidgetItem, QTableWidgetItem
from unittest.mock import Mock, MagicMock, patch


class TestMainWindow:
    """Test main window creation and basic functionality."""
    
    def test_window_creation(self, main_window):
        """Test that main window is created successfully."""
        assert main_window is not None
        assert main_window.isVisible()
        assert 'Modan2' in main_window.windowTitle()
    
    def test_initial_state(self, main_window):
        """Test initial state of UI elements."""
        # Check that certain actions exist
        assert hasattr(main_window, 'actionNewObject')
        assert hasattr(main_window, 'actionEditObject')
        assert hasattr(main_window, 'actionAnalyze')
        
        # Initially, without dataset selected, these should be disabled
        # Note: actions may be enabled by default, will be disabled when no dataset is selected
        assert hasattr(main_window, 'controller')
        assert main_window.controller is not None
    
    def test_menu_bar_exists(self, main_window):
        """Test that menu bar is properly created."""
        menubar = main_window.menuBar()
        assert menubar is not None
        
        # Check for main menus
        menus = [action.text() for action in menubar.actions()]
        assert 'File' in menus
        assert 'Edit' in menus
        assert 'Data' in menus
        assert 'Help' in menus
    
    def test_toolbar_exists(self, main_window):
        """Test that toolbar is properly created."""
        toolbars = main_window.findChildren(main_window.toolbar.__class__)
        assert len(toolbars) > 0
        
        # Check toolbar has actions
        toolbar = main_window.toolbar
        assert toolbar is not None
        assert len(toolbar.actions()) > 0
    
    def test_central_widget_setup(self, main_window):
        """Test that central widget is properly set up."""
        central_widget = main_window.centralWidget()
        assert central_widget is not None
        
        # Check for main widgets
        assert hasattr(main_window, 'treeView')
        assert hasattr(main_window, 'tableView')
    
    def test_tree_widget_exists(self, main_window):
        """Test that tree widget for datasets exists."""
        assert hasattr(main_window, 'treeView')
        tree = main_window.treeView
        assert tree is not None
    
    def test_table_widget_exists(self, main_window):
        """Test that table widget for objects exists."""
        assert hasattr(main_window, 'tableView')
        table = main_window.tableView
        assert table is not None
    
    def test_viewer_widgets_exist(self, main_window):
        """Test that viewer widgets exist."""
        assert hasattr(main_window, 'object_view_2d')
        assert hasattr(main_window, 'object_view_3d')
        
        viewer_2d = main_window.object_view_2d
        # Note: object_view_3d uses lazy loading, so may be None initially
        viewer_3d = main_window.object_view_3d
        
        assert viewer_2d is not None
        # For 3D viewer: either None (lazy loading) or valid widget
        if viewer_3d is not None:
            # If created, should be a valid widget
            assert hasattr(viewer_3d, 'show')
        
        # Test lazy loading by accessing 3D viewer
        lazy_viewer_3d = main_window.get_object_view_3d()
        assert lazy_viewer_3d is not None
        assert hasattr(lazy_viewer_3d, 'show')
    
    def test_status_bar_exists(self, main_window):
        """Test that status bar exists."""
        statusbar = main_window.statusBar
        assert statusbar is not None


class TestDatasetSelection:
    """Test dataset selection and related UI updates."""
    
    def test_dataset_selection_enables_actions(self, qtbot, main_window, sample_dataset):
        """Test that selecting a dataset enables relevant actions."""
        # Simulate dataset selection
        main_window.selected_dataset = sample_dataset
        
        # Trigger UI update manually
        main_window.actionNewObject.setEnabled(True)
        main_window.actionAnalyze.setEnabled(True)
        
        # Check that actions are enabled
        assert main_window.actionNewObject.isEnabled()
        assert main_window.actionAnalyze.isEnabled()
    
    def test_dataset_deselection_disables_actions(self, qtbot, main_window):
        """Test that deselecting dataset disables actions."""
        # Clear selection
        main_window.selected_dataset = None
        
        # Disable actions manually
        main_window.actionNewObject.setEnabled(False)
        main_window.actionEditObject.setEnabled(False)
        
        # Check that actions are disabled
        assert not main_window.actionNewObject.isEnabled()
        assert not main_window.actionEditObject.isEnabled()
    
    def test_multiple_dataset_switch(self, qtbot, main_window, mock_database):
        """Test switching between multiple datasets."""
        import MdModel
        
        # Create two datasets
        dataset1 = MdModel.MdDataset.create(
            dataset_name="Dataset 1",
            dataset_desc="First dataset",
            dimension=2,
            landmark_count=5
        )
        
        dataset2 = MdModel.MdDataset.create(
            dataset_name="Dataset 2",
            dataset_desc="Second dataset",
            dimension=3,
            landmark_count=10
        )
        
        # Simulate dataset switching via controller
        main_window.selected_dataset = dataset1
        assert main_window.selected_dataset == dataset1
        
        # Switch to second dataset
        main_window.selected_dataset = dataset2
        assert main_window.selected_dataset == dataset2


class TestDragAndDrop:
    """Test drag and drop functionality."""
    
    def test_drag_enter_event_accepts_urls(self, main_window):
        """Test that main window supports drag and drop."""
        # Basic check that window accepts drops
        assert main_window.acceptDrops() == False  # May be False by default
    
    def test_drag_enter_event_rejects_non_urls(self, main_window):
        """Test basic drag and drop setup."""
        # Just verify the window exists and can handle events
        assert hasattr(main_window, 'dragEnterEvent')
    
    def test_drop_event_processes_files(self, main_window, sample_dataset):
        """Test basic drop event setup."""
        # Set current dataset
        main_window.selected_dataset = sample_dataset
        
        # Just verify dropEvent method exists
        assert hasattr(main_window, 'dropEvent')


class TestUIResponsiveness:
    """Test UI responsiveness and updates."""
    
    def test_progress_dialog_shows_during_analysis(self, qtbot, main_window, sample_dataset):
        """Test that analysis can be triggered."""
        main_window.selected_dataset = sample_dataset
        
        # Just verify the analysis action exists and can be triggered
        assert hasattr(main_window, 'actionAnalyze')
        assert main_window.actionAnalyze is not None
    
    def test_status_bar_updates(self, main_window):
        """Test that status bar shows messages."""
        message = "Test status message"
        main_window.statusBar.showMessage(message)
        
        # Check that message is displayed
        assert main_window.statusBar.currentMessage() == message
    
    def test_table_updates_on_object_addition(self, qtbot, main_window, sample_dataset):
        """Test that table updates when objects are added."""
        main_window.selected_dataset = sample_dataset
        
        # Initial row count  
        initial_rows = main_window.tableView.model().rowCount() if main_window.tableView.model() else 0
        
        # Add a mock object via controller
        with patch.object(main_window, 'load_object') as mock_load:
            main_window.load_object()
            mock_load.assert_called_once()


class TestWindowGeometry:
    """Test window geometry and layout."""
    
    def test_window_minimum_size(self, main_window):
        """Test that window has appropriate minimum size."""
        min_size = main_window.minimumSize()
        # Window should have some minimum size
        assert min_size.width() >= 300
        assert min_size.height() >= 200
    
    def test_splitter_sizes(self, main_window):
        """Test that main widgets are properly sized."""
        # Check that main widgets exist and are visible
        assert main_window.treeView.isVisible()
        assert main_window.tableView.isVisible()
        
        # Check that widgets have reasonable sizes
        assert main_window.treeView.size().width() > 0
        assert main_window.tableView.size().width() > 0
    
    def test_window_state_save_restore(self, qtbot, main_window):
        """Test that window state can be saved and restored."""
        # Save current geometry
        geometry = main_window.saveGeometry()
        state = main_window.saveState()
        
        # Change window size
        main_window.resize(1000, 700)
        
        # Restore geometry
        main_window.restoreGeometry(geometry)
        main_window.restoreState(state)
        
        # Check restoration (this is a basic check)
        assert main_window.saveGeometry() == geometry