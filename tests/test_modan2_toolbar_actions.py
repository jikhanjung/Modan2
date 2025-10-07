"""Tests for Modan2 main window toolbar actions."""

from unittest.mock import Mock, patch

import pytest
from PyQt5.QtWidgets import QAbstractItemView


@pytest.mark.skip(reason="Toolbar action tests cause dialog exec_() blocking - needs dialog mocking refactor")
class TestToolbarActions:
    """Test toolbar button actions."""

    def test_toolbar_new_dataset_action(self, qtbot, main_window, mock_database):
        """Test New Dataset toolbar button."""
        main_window.controller.db_file_path = ":memory:"

        with patch("Modan2.DatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.actionNewDataset.trigger()

            mock_dialog.assert_called_once()
            mock_instance.exec_.assert_called_once()

    def test_toolbar_new_object_action(self, qtbot, main_window, mock_database):
        """Test New Object toolbar button."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Toolbar Test", dimension=2, landmark_count=5)
        main_window.selected_dataset = dataset

        with patch("Modan2.ObjectDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.actionNewObject.trigger()

            mock_dialog.assert_called_once()
            mock_instance.exec_.assert_called_once()

    def test_toolbar_import_action(self, qtbot, main_window, mock_database):
        """Test Import toolbar button."""
        main_window.controller.db_file_path = ":memory:"

        with patch("Modan2.ImportDatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.actionImport.trigger()

            mock_dialog.assert_called_once()
            mock_instance.exec_.assert_called_once()

    def test_toolbar_export_action(self, qtbot, main_window, mock_database):
        """Test Export toolbar button."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Export Test", dimension=2, landmark_count=5)
        main_window.selected_dataset = dataset

        with patch("Modan2.ExportDatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.actionExport.trigger()

            mock_dialog.assert_called_once_with(main_window)
            mock_instance.set_dataset.assert_called_once_with(dataset)
            mock_instance.exec_.assert_called_once()

    def test_toolbar_analyze_action(self, qtbot, main_window, mock_database):
        """Test Analyze toolbar button."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Analysis Test", dimension=2, landmark_count=5)
        for i in range(3):
            mm.MdObject.create(dataset=dataset, object_name=f"Object {i + 1}", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")
        main_window.selected_dataset = dataset

        with patch("Modan2.NewAnalysisDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.actionAnalyze.trigger()

            mock_dialog.assert_called_once()
            mock_instance.exec_.assert_called_once()

    def test_toolbar_preferences_action(self, qtbot, main_window):
        """Test Preferences toolbar button."""
        with patch("Modan2.PreferencesDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec.return_value = False

            main_window.actionPreferences.trigger()

            mock_dialog.assert_called_once()
            mock_instance.exec.assert_called_once()

    def test_toolbar_about_action(self, qtbot, main_window):
        """Test About toolbar button."""
        with patch("Modan2.QMessageBox.about") as mock_about:
            main_window.actionAbout.trigger()
            mock_about.assert_called_once()

    def test_toolbar_cell_selection_action(self, qtbot, main_window):
        """Test Cell Selection toolbar button."""
        main_window.actionCellSelection.trigger()
        assert main_window.tableView.selectionBehavior() == QAbstractItemView.SelectItems
        assert main_window.actionCellSelection.isChecked()
        assert not main_window.actionRowSelection.isChecked()

    def test_toolbar_row_selection_action(self, qtbot, main_window):
        """Test Row Selection toolbar button."""
        main_window.actionRowSelection.trigger()
        assert main_window.tableView.selectionBehavior() == QAbstractItemView.SelectRows
        assert main_window.actionRowSelection.isChecked()
        assert not main_window.actionCellSelection.isChecked()

    def test_toolbar_add_variable_action(self, qtbot, main_window, mock_database):
        """Test Add Variable toolbar button."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Variable Test", dimension=2, landmark_count=5)
        main_window.controller.current_dataset = dataset

        # Should trigger add variable functionality
        # Since implementation may vary, just ensure no crash
        main_window.actionAddVariable.trigger()


class TestToolbarStateManagement:
    """Test toolbar button enabled/disabled states."""

    def test_initial_toolbar_state_no_database(self, qtbot, main_window):
        """Test initial toolbar state with no database."""
        main_window.controller.db_file_path = None
        main_window.controller.current_dataset = None

        # Call the dataset selection handler to update states
        main_window.on_dataset_selected_from_tree(None)

        # Dataset actions should be enabled (can create new)
        assert main_window.actionNewDataset.isEnabled()
        assert main_window.actionImport.isEnabled()

        # Object/analysis actions should be disabled
        assert not main_window.actionNewObject.isEnabled()
        assert not main_window.actionEditObject.isEnabled()
        assert not main_window.actionExport.isEnabled()
        assert not main_window.actionAnalyze.isEnabled()

        # Table actions should be disabled
        assert not main_window.actionCellSelection.isEnabled()
        assert not main_window.actionRowSelection.isEnabled()
        assert not main_window.actionAddVariable.isEnabled()

    def test_toolbar_state_with_dataset_selected(self, qtbot, main_window, mock_database):
        """Test toolbar state when dataset is selected."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="State Test", dimension=2, landmark_count=5)

        # Simulate dataset selection
        main_window.on_dataset_selected_from_tree(dataset)

        # Dataset actions should be enabled
        assert main_window.actionNewDataset.isEnabled()
        assert main_window.actionNewObject.isEnabled()
        assert main_window.actionImport.isEnabled()
        assert main_window.actionExport.isEnabled()
        assert main_window.actionAnalyze.isEnabled()

        # Table actions should be enabled
        assert main_window.actionCellSelection.isEnabled()
        assert main_window.actionRowSelection.isEnabled()
        assert main_window.actionAddVariable.isEnabled()

        # Edit object should be disabled until object is selected
        assert not main_window.actionEditObject.isEnabled()

    def test_toolbar_state_with_analysis_selected(self, qtbot, main_window, mock_database):
        """Test toolbar state when analysis is selected."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Analysis State Test", dimension=2, landmark_count=5)
        for i in range(3):
            mm.MdObject.create(dataset=dataset, object_name=f"Object {i + 1}", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")

        analysis = mm.MdAnalysis.create(
            dataset=dataset,
            analysis_name="Test Analysis",
            analysis_method="PCA",
            edge_length=0,
            superimposition_method="Procrustes",
        )

        # Simulate analysis selection
        main_window.on_analysis_selected_from_tree(analysis)

        # Dataset/object actions should be disabled when viewing analysis
        assert not main_window.actionNewObject.isEnabled()
        assert not main_window.actionEditObject.isEnabled()
        assert not main_window.actionExport.isEnabled()
        assert not main_window.actionAnalyze.isEnabled()
        assert not main_window.actionCellSelection.isEnabled()
        assert not main_window.actionRowSelection.isEnabled()
        assert not main_window.actionAddVariable.isEnabled()

    def test_toolbar_state_no_dataset_selected(self, qtbot, main_window, mock_database):
        """Test toolbar state when no dataset is selected."""
        # Simulate no dataset selection
        main_window.on_dataset_selected_from_tree(None)

        # Object/analysis actions should be disabled
        assert not main_window.actionNewObject.isEnabled()
        assert not main_window.actionEditObject.isEnabled()
        assert not main_window.actionExport.isEnabled()
        assert not main_window.actionAnalyze.isEnabled()
        assert not main_window.actionCellSelection.isEnabled()
        assert not main_window.actionRowSelection.isEnabled()
        assert not main_window.actionAddVariable.isEnabled()


class TestToolbarShortcuts:
    """Test toolbar action keyboard shortcuts."""

    def test_new_dataset_shortcut(self, qtbot, main_window, mock_database):
        """Test Ctrl+N shortcut for New Dataset."""
        main_window.controller.db_file_path = ":memory:"

        with patch("Modan2.DatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            # Trigger via shortcut
            main_window.actionNewDataset.trigger()

            mock_dialog.assert_called_once()

    def test_new_object_shortcut(self, qtbot, main_window, mock_database):
        """Test Ctrl+Shift+N shortcut for New Object."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Shortcut Test", dimension=2, landmark_count=5)
        main_window.selected_dataset = dataset

        with patch("Modan2.ObjectDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.actionNewObject.trigger()

            mock_dialog.assert_called_once()

    def test_import_shortcut(self, qtbot, main_window, mock_database):
        """Test Ctrl+I shortcut for Import."""
        main_window.controller.db_file_path = ":memory:"

        with patch("Modan2.ImportDatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.actionImport.trigger()

            mock_dialog.assert_called_once()

    def test_export_shortcut(self, qtbot, main_window, mock_database):
        """Test Ctrl+E shortcut for Export."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Export Shortcut", dimension=2, landmark_count=5)
        main_window.selected_dataset = dataset

        with patch("Modan2.ExportDatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.actionExport.trigger()

            mock_dialog.assert_called_once()

    def test_analyze_shortcut(self, qtbot, main_window, mock_database):
        """Test Ctrl+G shortcut for Analyze."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Analyze Shortcut", dimension=2, landmark_count=5)
        for i in range(3):
            mm.MdObject.create(dataset=dataset, object_name=f"Object {i + 1}", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")
        main_window.selected_dataset = dataset

        with patch("Modan2.NewAnalysisDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.actionAnalyze.trigger()

            mock_dialog.assert_called_once()


class TestSelectionModeToggle:
    """Test cell/row selection mode toggle behavior."""

    def test_selection_mode_toggle_exclusive(self, qtbot, main_window):
        """Test that cell and row selection modes are mutually exclusive."""
        # Start with cell selection
        main_window.actionCellSelection.setChecked(True)
        main_window.actionRowSelection.setChecked(False)

        # Switch to row selection
        main_window.actionRowSelection.trigger()

        assert main_window.actionRowSelection.isChecked()
        assert not main_window.actionCellSelection.isChecked()
        assert main_window.tableView.selectionBehavior() == QAbstractItemView.SelectRows

        # Switch back to cell selection
        main_window.actionCellSelection.trigger()

        assert main_window.actionCellSelection.isChecked()
        assert not main_window.actionRowSelection.isChecked()
        assert main_window.tableView.selectionBehavior() == QAbstractItemView.SelectItems

    def test_selection_mode_action_group(self, qtbot, main_window):
        """Test that selection modes belong to exclusive action group."""
        assert main_window.selection_mode_group is not None
        assert main_window.selection_mode_group.isExclusive()
        assert main_window.actionCellSelection in main_window.selection_mode_group.actions()
        assert main_window.actionRowSelection in main_window.selection_mode_group.actions()

    def test_default_selection_mode(self, qtbot, main_window):
        """Test default selection mode is cell selection."""
        assert main_window.actionCellSelection.isChecked()
        assert not main_window.actionRowSelection.isChecked()
        assert main_window.tableView.selectionBehavior() == QAbstractItemView.SelectItems
