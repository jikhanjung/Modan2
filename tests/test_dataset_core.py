"""
Core Dataset and Object functionality tests.

This module contains tests for basic dataset and object creation, management,
and their relationships. These are the foundational tests that other test
modules depend on.
"""

from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QPoint

import MdModel
from ModanDialogs import DatasetDialog, ObjectDialog


class TestDatasetCore:
    """Test core dataset creation and management functionality."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Automatically setup database for all tests in this class."""
        pass

    def test_dataset_dialog_creation(self, qtbot):
        """Test that DatasetDialog can be created and displays correctly."""
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        dialog = DatasetDialog(parent=mock_parent)
        qtbot.addWidget(dialog)

        assert dialog is not None
        assert dialog.windowTitle() == "Modan2 - Dataset Information"
        assert hasattr(dialog, "edtDatasetName")
        assert hasattr(dialog, "rbtn2D")
        assert hasattr(dialog, "rbtn3D")

    def test_dataset_creation_2d(self, qtbot):
        """Test creating a 2D dataset through the dialog."""
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        dialog = DatasetDialog(parent=mock_parent)
        qtbot.addWidget(dialog)

        # Set up the dialog for 2D dataset
        dialog.edtDatasetName.setText("Test2D")
        dialog.rbtn2D.setChecked(True)

        # Get initial count
        initial_count = MdModel.MdDataset.select().count()

        # Simulate clicking Save - this should create the dataset
        dialog.btnOkay.click()

        # Verify dataset was created
        final_count = MdModel.MdDataset.select().count()
        assert final_count == initial_count + 1

        # Get the created dataset
        created_dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()
        assert created_dataset.dataset_name == "Test2D"
        assert created_dataset.dimension == 2

    def test_dataset_creation_3d(self, qtbot):
        """Test creating a 3D dataset through the dialog."""
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        dialog = DatasetDialog(parent=mock_parent)
        qtbot.addWidget(dialog)

        # Set up the dialog for 3D dataset
        dialog.edtDatasetName.setText("Test3D")
        dialog.rbtn3D.setChecked(True)

        # Get initial count
        initial_count = MdModel.MdDataset.select().count()

        # Click Save to create dataset
        dialog.btnOkay.click()

        # Verify dataset was created
        final_count = MdModel.MdDataset.select().count()
        assert final_count == initial_count + 1

        # Get the created dataset
        created_dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()
        assert created_dataset.dataset_name == "Test3D"
        assert created_dataset.dimension == 3

    def test_dataset_validation(self, qtbot):
        """Test dataset name validation."""
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        dialog = DatasetDialog(parent=mock_parent)
        qtbot.addWidget(dialog)

        # Test empty name validation
        dialog.edtDatasetName.setText("")
        dialog.rbtn2D.setChecked(True)

        initial_count = MdModel.MdDataset.select().count()

        # Try to save - DatasetDialog allows empty names and creates dataset
        dialog.btnOkay.click()

        # DatasetDialog creates dataset even with empty name (current behavior)
        final_count = MdModel.MdDataset.select().count()
        assert final_count == initial_count + 1


class TestObjectCore:
    """Test core object creation and management functionality."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Automatically setup database for all tests in this class."""
        pass

    @pytest.fixture
    def sample_dataset(self, qtbot):
        """Create a sample dataset for object tests."""
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        dialog = DatasetDialog(parent=mock_parent)
        qtbot.addWidget(dialog)

        dialog.edtDatasetName.setText("SampleDataset")
        dialog.rbtn2D.setChecked(True)
        dialog.Okay()

        return MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()

    def test_object_dialog_creation(self, qtbot, sample_dataset):
        """Test that ObjectDialog can be created and displays correctly."""
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        dialog = ObjectDialog(parent=mock_parent)
        qtbot.addWidget(dialog)
        dialog.set_dataset(sample_dataset)

        assert dialog is not None
        assert dialog.windowTitle() == "Modan2 - Object Information"
        assert hasattr(dialog, "edtObjectName")
        assert dialog.dataset == sample_dataset

    def test_object_creation(self, qtbot, sample_dataset):
        """Test creating an object through the dialog."""
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        dialog = ObjectDialog(parent=mock_parent)
        qtbot.addWidget(dialog)
        dialog.set_dataset(sample_dataset)

        # Set up the dialog
        dialog.edtObjectName.setText("TestObject")
        dialog.edtSequence.setText("1")

        # Get initial count
        initial_count = sample_dataset.object_list.count()

        # Manually call save_object to test the logic
        dialog.save_object()

        # Verify object was created
        final_count = sample_dataset.object_list.count()
        assert final_count == initial_count + 1

        # Get the created object
        created_object = sample_dataset.object_list.order_by(MdModel.MdObject.id.desc()).first()
        assert created_object.object_name == "TestObject"
        assert created_object.dataset == sample_dataset

    def test_object_validation(self, qtbot, sample_dataset):
        """Test object name validation."""
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        dialog = ObjectDialog(parent=mock_parent)
        qtbot.addWidget(dialog)
        dialog.set_dataset(sample_dataset)

        # Test empty name validation
        dialog.edtObjectName.setText("")
        dialog.edtSequence.setText("1")

        initial_count = sample_dataset.object_list.count()
        dialog.save_object()

        # ObjectDialog creates object even with empty name (current behavior)
        final_count = sample_dataset.object_list.count()
        assert final_count == initial_count + 1


class TestDatasetObjectIntegration:
    """Test integration between datasets and objects."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Automatically setup database for all tests in this class."""
        pass

    def test_dataset_object_relationship(self, qtbot):
        """Test the relationship between datasets and objects."""
        # Create dataset
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        dataset_dialog = DatasetDialog(parent=mock_parent)
        qtbot.addWidget(dataset_dialog)

        dataset_dialog.edtDatasetName.setText("IntegrationTest")
        dataset_dialog.rbtn2D.setChecked(True)
        dataset_dialog.Okay()

        dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()

        # Create multiple objects in the dataset
        for i in range(3):
            object_dialog = ObjectDialog(parent=mock_parent)
            qtbot.addWidget(object_dialog)
            object_dialog.set_dataset(dataset)

            object_dialog.edtObjectName.setText(f"Object{i + 1}")
            object_dialog.edtSequence.setText(str(i + 1))
            object_dialog.save_object()

        # Verify relationships
        assert dataset.object_list.count() == 3

        objects = list(dataset.object_list)
        for i, obj in enumerate(objects):
            assert obj.object_name == f"Object{i + 1}"
            assert obj.dataset == dataset

    def test_multiple_datasets_with_objects(self, qtbot):
        """Test creating multiple datasets each with their own objects."""
        mock_parent = Mock()
        mock_parent.pos.return_value = QPoint(100, 100)

        datasets = []

        # Create 2 datasets
        for i in range(2):
            dataset_dialog = DatasetDialog(parent=mock_parent)
            qtbot.addWidget(dataset_dialog)

            dataset_dialog.edtDatasetName.setText(f"Dataset{i + 1}")
            dataset_dialog.rbtn2D.setChecked(True)
            dataset_dialog.Okay()

            dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()
            datasets.append(dataset)

            # Add objects to each dataset
            for j in range(2):
                object_dialog = ObjectDialog(parent=mock_parent)
                qtbot.addWidget(object_dialog)
                object_dialog.set_dataset(dataset)

                object_dialog.edtObjectName.setText(f"Obj{j + 1}")
                object_dialog.edtSequence.setText(str(j + 1))
                object_dialog.save_object()

        # Verify each dataset has its own objects
        for i, dataset in enumerate(datasets):
            assert dataset.object_list.count() == 2
            assert dataset.dataset_name == f"Dataset{i + 1}"

            objects = list(dataset.object_list)
            for j, obj in enumerate(objects):
                assert obj.object_name == f"Obj{j + 1}"
                assert obj.dataset == dataset
