"""Tests for Modan2 main window menu actions."""

from unittest.mock import Mock, patch

from PyQt5.QtWidgets import QMessageBox


class TestFileMenuActions:
    """Test File menu actions."""

    def test_action_exit_triggered(self, qtbot, main_window):
        """Test Exit action triggers close event."""
        with patch.object(main_window, "close") as mock_close:
            main_window.on_action_exit_triggered()
            mock_close.assert_called_once()

    def test_action_preferences_triggered(self, qtbot, main_window):
        """Test Preferences action opens preferences dialog."""
        with patch("Modan2.PreferencesDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec.return_value = False

            main_window.on_action_edit_preferences_triggered()

            mock_dialog.assert_called_once()
            mock_instance.exec.assert_called_once()


class TestDatasetMenuActions:
    """Test Dataset menu actions."""

    def test_action_new_dataset_with_database(self, qtbot, main_window, mock_database):
        """Test new dataset action when database is open."""
        with patch("Modan2.DatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = True
            mock_instance.dataset = Mock()
            mock_instance.dataset.id = 1
            mock_instance.dataset.dataset_name = "Test Dataset"

            main_window.on_action_new_dataset_triggered()

            mock_dialog.assert_called_once()
            mock_instance.exec_.assert_called_once()

    def test_action_import_with_database(self, qtbot, main_window, mock_database):
        """Test import action when database is open."""
        with patch("Modan2.ImportDatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.on_action_import_dataset_triggered()

            mock_dialog.assert_called_once()
            mock_instance.exec_.assert_called_once()

    def test_action_export_no_dataset_selected(self, qtbot, main_window):
        """Export does nothing without a selection (the action is disabled then)."""
        main_window.selected_dataset = None

        with patch("Modan2.ExportDatasetDialog") as mock_dialog:
            main_window.on_action_export_dataset_triggered()
            mock_dialog.assert_not_called()

    def test_action_export_with_dataset_selected(self, qtbot, main_window, mock_database):
        """Test export action when dataset is selected."""
        import MdModel as mm

        # Create test dataset
        dataset = mm.MdDataset.create(dataset_name="Export Test", dimension=2, landmark_count=5)
        main_window.selected_dataset = dataset

        with patch("Modan2.ExportDatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.on_action_export_dataset_triggered()

            mock_dialog.assert_called_once_with(main_window)
            mock_instance.set_dataset.assert_called_once_with(dataset)
            mock_instance.exec_.assert_called_once()


class TestObjectMenuActions:
    """Test Object menu actions."""

    def test_action_new_object_no_dataset(self, qtbot, main_window):
        """New object does nothing without a selection (the action is disabled then)."""
        main_window.selected_dataset = None

        with patch("Modan2.ObjectDialog") as mock_dialog:
            main_window.on_action_new_object_triggered()
            mock_dialog.assert_not_called()

    def test_action_new_object_with_dataset(self, qtbot, main_window, mock_database):
        """Test new object action when dataset is selected."""
        import MdModel as mm

        # Create test dataset
        dataset = mm.MdDataset.create(dataset_name="Object Test", dimension=2, landmark_count=5)
        main_window.selected_dataset = dataset

        with patch("Modan2.ObjectDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.on_action_new_object_triggered()

            mock_dialog.assert_called_once()
            mock_instance.exec_.assert_called_once()

    def test_action_delete_object_no_selection(self, qtbot, main_window):
        """Test delete object action when no object is selected."""
        main_window.controller.current_object = None

        with patch("Modan2.QMessageBox.warning") as mock_warning:
            main_window.on_action_delete_object_triggered()
            mock_warning.assert_called_once()

    def test_action_delete_object_with_confirmation_cancel(self, qtbot, main_window, mock_database):
        """Test delete object action when user cancels confirmation."""
        import MdModel as mm

        # Create test dataset and object
        dataset = mm.MdDataset.create(dataset_name="Delete Test", dimension=2, landmark_count=5)
        obj = mm.MdObject.create(dataset=dataset, object_name="Test Object", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")
        main_window.controller.current_object = obj

        with patch("Modan2.QMessageBox.question", return_value=QMessageBox.No):
            main_window.on_action_delete_object_triggered()

            # Object should still exist
            assert mm.MdObject.select().where(mm.MdObject.id == obj.id).exists()

    def test_action_delete_object_with_confirmation_accept(self, qtbot, main_window, mock_database):
        """Test delete object action when user confirms deletion."""
        import MdModel as mm

        # Create test dataset and object
        dataset = mm.MdDataset.create(dataset_name="Delete Test", dimension=2, landmark_count=5)
        obj = mm.MdObject.create(dataset=dataset, object_name="Test Object", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")
        obj_id = obj.id

        with (
            patch("Modan2.QMessageBox.warning", return_value=QMessageBox.Yes),
            patch.object(main_window, "get_selected_object_list", return_value=[obj]),
        ):
            main_window.on_action_delete_object_triggered()

            assert not mm.MdObject.select().where(mm.MdObject.id == obj_id).exists()


class TestAnalysisMenuActions:
    """Test Analysis menu actions."""

    def test_action_analyze_no_dataset(self, qtbot, main_window):
        """Test analyze action when no dataset is selected."""
        main_window.controller.current_dataset = None

        with patch("Modan2.QMessageBox.warning") as mock_warning:
            main_window.on_action_analyze_dataset_triggered()
            mock_warning.assert_called_once()

    def test_action_analyze_dataset_insufficient_objects(self, qtbot, main_window, mock_database):
        """A thin dataset still opens the dialog — it does the validating."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Analysis Test", dimension=2, landmark_count=5)
        mm.MdObject.create(dataset=dataset, object_name="Object 1", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")
        main_window.selected_dataset = dataset

        with patch("Modan2.NewAnalysisDialog") as mock_dialog:
            main_window.on_action_analyze_dataset_triggered()
            mock_dialog.assert_called_once()

    def test_action_analyze_dataset_with_valid_dataset(self, qtbot, main_window, mock_database):
        """Test analyze action when dataset has sufficient objects."""
        import MdModel as mm

        # Create dataset with 3 objects (minimum for analysis)
        dataset = mm.MdDataset.create(dataset_name="Analysis Test", dimension=2, landmark_count=5)
        for i in range(3):
            mm.MdObject.create(dataset=dataset, object_name=f"Object {i + 1}", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")
        main_window.selected_dataset = dataset

        with patch("Modan2.NewAnalysisDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = False

            main_window.on_action_analyze_dataset_triggered()

            mock_dialog.assert_called_once()
            mock_instance.exec_.assert_called_once()


class TestHelpMenuActions:
    """Test Help menu actions."""

    def test_action_about_triggered(self, qtbot, main_window):
        """Test About action shows about dialog."""
        message = main_window.build_about_message()
        message.deleteLater()
        assert "Modan2" in message.text()
        main_window.on_action_about_triggered()


class TestVariableMenuActions:
    """Test variable/property management actions."""

    def test_action_add_variable_no_dataset(self, qtbot, main_window):
        """Test add variable action when no dataset is selected."""
        main_window.controller.current_dataset = None

        # May show warning or do nothing - just ensure no crash
        main_window.on_action_add_variable_triggered()

    def test_action_cell_selection_triggered(self, qtbot, main_window):
        """Test cell selection mode action."""
        # Should change selection mode
        main_window.on_action_cell_selection_triggered()

        # Verify selection behavior changed
        from PyQt5.QtWidgets import QAbstractItemView

        assert main_window.tableView.selectionBehavior() == QAbstractItemView.SelectItems

    def test_action_row_selection_triggered(self, qtbot, main_window):
        """Test row selection mode action."""
        # The handler only acts while the action is checked.
        main_window.actionRowSelection.setChecked(True)
        main_window.on_action_row_selection_triggered()

        # Verify selection behavior changed
        from PyQt5.QtWidgets import QAbstractItemView

        assert main_window.tableView.selectionBehavior() == QAbstractItemView.SelectRows


class TestDataExplorationActions:
    """Test data exploration actions."""

    def test_action_explore_data_no_dataset(self, qtbot, main_window):
        """Test explore data action when no dataset is selected."""
        main_window.controller.current_dataset = None

        # Should show warning or do nothing - just ensure no crash
        main_window.on_action_explore_data_triggered()

    def test_action_explore_data_with_analysis(self, qtbot, main_window, mock_database):
        """Explore data opens the exploration window for the selected analysis.

        It is shown non-modally (and owns itself, so it is freed on close), not
        exec_'d, and it reads the selected *analysis* rather than the dataset.
        """
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Explore Test", dimension=2, landmark_count=5)
        analysis = mm.MdAnalysis.create(analysis_name="A", dataset=dataset, superimposition_method="Procrustes")
        main_window.selected_analysis = analysis

        with patch("Modan2.DataExplorationDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance

            main_window.on_action_explore_data_triggered()

            mock_dialog.assert_called_once_with(main_window)
            mock_instance.set_analysis.assert_called_once_with(analysis)
            mock_instance.show.assert_called_once()
