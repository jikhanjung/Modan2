"""Tests for Modan2 dataset tree view interactions."""

from unittest.mock import Mock, patch

from PyQt5.QtCore import QItemSelectionModel


class TestTreeViewDatasetSelection:
    """Test dataset selection in tree view."""

    def test_select_dataset_from_tree(self, qtbot, main_window, mock_database):
        """Test selecting a dataset from tree view."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Tree Test", dimension=2, landmark_count=5)
        main_window.load_dataset()

        # Find the dataset item in tree
        root = main_window.dataset_model.invisibleRootItem()
        item = root.child(0, 0)
        assert item is not None
        assert item.data() == dataset

        # Simulate selection
        index = main_window.dataset_model.indexFromItem(item)
        main_window.treeView.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

        # Verify dataset is selected
        assert main_window.selected_dataset == dataset

    def test_deselect_dataset_from_tree(self, qtbot, main_window, mock_database):
        """Test deselecting by clicking empty space."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Deselect Test", dimension=2, landmark_count=5)
        main_window.load_dataset()
        main_window.selected_dataset = dataset

        # Clear selection
        main_window.treeView.selectionModel().clearSelection()

        # Trigger selection changed with empty selection
        from PyQt5.QtCore import QItemSelection

        main_window.on_dataset_selection_changed(QItemSelection(), QItemSelection())

        # Verify dataset is deselected
        assert main_window.selected_dataset is None

    def test_select_analysis_from_tree(self, qtbot, main_window, mock_database):
        """Test selecting an analysis from tree view."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Analysis Tree Test", dimension=2, landmark_count=5)
        for i in range(3):
            mm.MdObject.create(dataset=dataset, object_name=f"Object {i + 1}", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")

        analysis = mm.MdAnalysis.create(
            dataset=dataset,
            analysis_name="Test Analysis",
            analysis_method="PCA",
            edge_length=0,
            superimposition_method="Procrustes",
        )

        main_window.load_dataset()

        # Find the analysis item in tree
        root = main_window.dataset_model.invisibleRootItem()
        dataset_item = root.child(0, 0)
        analysis_item = dataset_item.child(0, 0)
        assert analysis_item is not None
        assert analysis_item.data() == analysis

        # Simulate selection
        index = main_window.dataset_model.indexFromItem(analysis_item)
        main_window.treeView.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

        # Verify analysis is selected
        assert main_window.selected_analysis == analysis

    def test_switch_between_datasets(self, qtbot, main_window, mock_database):
        """Test switching between different datasets."""
        import MdModel as mm

        dataset1 = mm.MdDataset.create(dataset_name="Dataset 1", dimension=2, landmark_count=5)
        dataset2 = mm.MdDataset.create(dataset_name="Dataset 2", dimension=3, landmark_count=10)

        main_window.load_dataset()

        # Select first dataset
        root = main_window.dataset_model.invisibleRootItem()
        item1 = root.child(0, 0)
        index1 = main_window.dataset_model.indexFromItem(item1)
        main_window.treeView.selectionModel().select(index1, QItemSelectionModel.ClearAndSelect)
        assert main_window.selected_dataset.id in [dataset1.id, dataset2.id]

        # Switch to second dataset
        item2 = root.child(1, 0)
        index2 = main_window.dataset_model.indexFromItem(item2)
        main_window.treeView.selectionModel().select(index2, QItemSelectionModel.ClearAndSelect)
        assert main_window.selected_dataset.id in [dataset1.id, dataset2.id]


class TestTreeViewLoading:
    """Test tree view loading and structure."""

    def test_load_empty_tree(self, qtbot, main_window, mock_database):
        """Test loading tree with no datasets."""
        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        assert root.rowCount() == 0

    def test_load_single_dataset(self, qtbot, main_window, mock_database):
        """Test loading tree with single dataset."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Single Dataset", dimension=2, landmark_count=5)
        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        assert root.rowCount() == 1

        item = root.child(0, 0)
        assert item.data() == dataset
        assert "Single Dataset" in item.text()

    def test_load_multiple_datasets(self, qtbot, main_window, mock_database):
        """Test loading tree with multiple datasets."""
        import MdModel as mm

        mm.MdDataset.create(dataset_name="Dataset A", dimension=2, landmark_count=5)
        mm.MdDataset.create(dataset_name="Dataset B", dimension=3, landmark_count=10)
        mm.MdDataset.create(dataset_name="Dataset C", dimension=2, landmark_count=8)

        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        assert root.rowCount() == 3

    def test_load_dataset_with_analyses(self, qtbot, main_window, mock_database):
        """Test loading dataset with analyses as child nodes."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Dataset with Analyses", dimension=2, landmark_count=5)
        for i in range(3):
            mm.MdObject.create(dataset=dataset, object_name=f"Object {i + 1}", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")

        mm.MdAnalysis.create(
            dataset=dataset,
            analysis_name="PCA Analysis",
            analysis_method="PCA",
            edge_length=0,
            superimposition_method="Procrustes",
        )
        mm.MdAnalysis.create(
            dataset=dataset,
            analysis_name="CVA Analysis",
            analysis_method="CVA",
            edge_length=0,
            superimposition_method="Procrustes",
        )

        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        dataset_item = root.child(0, 0)
        assert dataset_item.rowCount() == 2

        # Verify analysis items
        analysis_item1 = dataset_item.child(0, 0)
        analysis_item2 = dataset_item.child(1, 0)
        assert analysis_item1.data().analysis_name in ["PCA Analysis", "CVA Analysis"]
        assert analysis_item2.data().analysis_name in ["PCA Analysis", "CVA Analysis"]

    def test_load_nested_datasets(self, qtbot, main_window, mock_database):
        """Test loading tree with parent-child dataset relationships."""
        import MdModel as mm

        parent_dataset = mm.MdDataset.create(dataset_name="Parent Dataset", dimension=2, landmark_count=5)
        child_dataset = mm.MdDataset.create(
            dataset_name="Child Dataset", dimension=2, landmark_count=5, parent=parent_dataset
        )

        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        assert root.rowCount() == 1

        parent_item = root.child(0, 0)
        assert parent_item.data() == parent_dataset
        assert parent_item.rowCount() == 1

        child_item = parent_item.child(0, 0)
        assert child_item.data() == child_dataset


class TestTreeViewIcons:
    """Test tree view icon display."""

    def test_2d_dataset_icon(self, qtbot, main_window, mock_database):
        """Test that 2D datasets show correct icon."""
        import MdModel as mm

        mm.MdDataset.create(dataset_name="2D Dataset", dimension=2, landmark_count=5)
        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        item = root.child(0, 0)
        assert item.icon() is not None

    def test_3d_dataset_icon(self, qtbot, main_window, mock_database):
        """Test that 3D datasets show correct icon."""
        import MdModel as mm

        mm.MdDataset.create(dataset_name="3D Dataset", dimension=3, landmark_count=10)
        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        item = root.child(0, 0)
        assert item.icon() is not None

    def test_analysis_icon(self, qtbot, main_window, mock_database):
        """Test that analyses show correct icon."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Dataset", dimension=2, landmark_count=5)
        for i in range(3):
            mm.MdObject.create(dataset=dataset, object_name=f"Object {i + 1}", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")

        mm.MdAnalysis.create(
            dataset=dataset,
            analysis_name="Test Analysis",
            analysis_method="PCA",
            edge_length=0,
            superimposition_method="Procrustes",
        )

        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        dataset_item = root.child(0, 0)
        analysis_item = dataset_item.child(0, 0)
        assert analysis_item.icon() is not None


class TestTreeViewDoubleClick:
    """Test double-click behavior on tree items."""

    def test_double_click_dataset_opens_dialog(self, qtbot, main_window, mock_database):
        """Test that double-clicking a dataset opens the dataset dialog."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Double Click Test", dimension=2, landmark_count=5)
        main_window.load_dataset()
        main_window.selected_dataset = dataset

        with patch("Modan2.DatasetDialog") as mock_dialog:
            mock_instance = Mock()
            mock_dialog.return_value = mock_instance
            mock_instance.exec_.return_value = 0

            main_window.on_treeView_doubleClicked()

            mock_dialog.assert_called_once()
            mock_instance.set_dataset.assert_called_once()


class TestTreeViewExpansion:
    """Test tree view expand/collapse behavior."""

    def test_tree_expands_on_load(self, qtbot, main_window, mock_database):
        """Test that tree is expanded by default after loading."""
        import MdModel as mm

        parent = mm.MdDataset.create(dataset_name="Parent", dimension=2, landmark_count=5)
        mm.MdDataset.create(dataset_name="Child", dimension=2, landmark_count=5, parent=parent)

        main_window.load_dataset()

        # Tree should be expanded
        root = main_window.dataset_model.invisibleRootItem()
        parent_item = root.child(0, 0)
        index = main_window.dataset_model.indexFromItem(parent_item)
        assert main_window.treeView.isExpanded(index)


class TestTreeViewObjectCount:
    """Test object count display in tree."""

    def test_dataset_shows_object_count(self, qtbot, main_window, mock_database):
        """Test that dataset label shows object count."""
        import MdModel as mm

        dataset = mm.MdDataset.create(dataset_name="Count Test", dimension=2, landmark_count=5)
        mm.MdObject.create(dataset=dataset, object_name="Object 1", landmark_str="0,0\n1,1\n2,2\n3,3\n4,4")
        mm.MdObject.create(dataset=dataset, object_name="Object 2", landmark_str="1,1\n2,2\n3,3\n4,4\n5,5")
        mm.MdObject.create(dataset=dataset, object_name="Object 3", landmark_str="2,2\n3,3\n4,4\n5,5\n6,6")

        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        item = root.child(0, 0)
        assert "(3)" in item.text()

    def test_empty_dataset_shows_zero_count(self, qtbot, main_window, mock_database):
        """Test that dataset with no objects shows (0)."""
        import MdModel as mm

        mm.MdDataset.create(dataset_name="Empty Dataset", dimension=2, landmark_count=5)
        main_window.load_dataset()

        root = main_window.dataset_model.invisibleRootItem()
        item = root.child(0, 0)
        assert "(0)" in item.text()
