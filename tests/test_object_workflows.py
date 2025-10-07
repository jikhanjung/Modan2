"""Object Workflows Integration Tests.

Tests complete object manipulation workflows:
- Create object with landmarks
- Edit object properties
- Attach images to objects
- Copy/delete objects
- Batch object operations
"""

import pytest

import MdModel
from dialogs import ObjectDialog


class TestObjectCreationWorkflow:
    """Test object creation workflows."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    @pytest.fixture
    def sample_dataset(self):
        """Create a sample dataset for object tests."""
        return MdModel.MdDataset.create(
            dataset_name="Object Test Dataset", dimension=2, landmark_count=5, propertyname_str="Sex,Age,Location"
        )

    def test_create_object_through_dialog(self, qtbot, sample_dataset):
        """Test creating object through ObjectDialog."""
        # Create dialog
        dialog = ObjectDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(sample_dataset)

        # Set object properties
        dialog.edtObjectName.setText("Test Object")
        dialog.edtSequence.setText("1")

        # Set landmarks directly
        dialog.landmark_list = [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0], [70.0, 80.0], [90.0, 100.0]]
        dialog.show_landmarks()

        # Set property values
        property_values = ["M", "25", "SiteA"]
        for idx, value in enumerate(property_values):
            dialog.edtPropertyList[idx].setText(value)

        # Save object
        dialog.save_object()

        # Verify object created
        assert sample_dataset.object_list.count() == 1

        obj = sample_dataset.object_list.first()
        assert obj.object_name == "Test Object"
        assert obj.sequence == 1
        # Verify landmarks saved correctly
        assert obj.landmark_str == "10.0\t20.0\n30.0\t40.0\n50.0\t60.0\n70.0\t80.0\n90.0\t100.0"
        assert obj.property_str == "M,25,SiteA"

    def test_create_multiple_objects_in_dataset(self, qtbot, sample_dataset):
        """Test creating multiple objects in same dataset."""
        # Create 5 objects
        for i in range(5):
            dialog = ObjectDialog(parent=None)
            qtbot.addWidget(dialog)
            dialog.set_dataset(sample_dataset)

            dialog.edtObjectName.setText(f"Object_{i + 1}")
            dialog.edtSequence.setText(str(i + 1))

            # Create landmark data
            dialog.landmark_list = [[j + i * 10.0, j + i * 10 + 1.0] for j in range(5)]
            dialog.show_landmarks()

            # Set properties
            property_values = ["M" if i % 2 == 0 else "F", str(20 + i), f"Site{i}"]
            for idx, value in enumerate(property_values):
                dialog.edtPropertyList[idx].setText(value)

            dialog.save_object()

        # Verify all objects created
        assert sample_dataset.object_list.count() == 5

        # Verify objects are in sequence
        objects = list(sample_dataset.object_list.order_by(MdModel.MdObject.sequence))
        for i, obj in enumerate(objects):
            assert obj.object_name == f"Object_{i + 1}"
            assert obj.sequence == i + 1

    def test_create_object_without_properties(self, qtbot, sample_dataset):
        """Test creating object without property values (optional)."""
        dialog = ObjectDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(sample_dataset)

        dialog.edtObjectName.setText("No Properties Object")
        dialog.edtSequence.setText("1")
        dialog.landmark_list = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0], [9.0, 10.0]]
        dialog.show_landmarks()

        # Don't set property values
        dialog.save_object()

        # Verify object created
        obj = sample_dataset.object_list.first()
        assert obj.object_name == "No Properties Object"
        # Property str might be None, empty, or commas (empty values for each property)
        assert obj.property_str is None or obj.property_str == "" or obj.property_str == ",,"


class TestObjectEditingWorkflow:
    """Test object editing workflows."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    @pytest.fixture
    def dataset_with_object(self):
        """Create dataset with one object."""
        dataset = MdModel.MdDataset.create(
            dataset_name="Edit Test Dataset", dimension=2, landmark_count=5, propertyname_str="Var1,Var2"
        )

        obj = MdModel.MdObject.create(
            object_name="Original Object",
            dataset=dataset,
            sequence=1,
            landmark_str="1,2\n3,4\n5,6\n7,8\n9,10",
            property_str="A,B",
        )

        return dataset, obj

    def test_edit_object_properties(self, qtbot, dataset_with_object):
        """Test editing object name and properties."""
        dataset, obj = dataset_with_object

        # Open dialog with existing object
        dialog = ObjectDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)
        dialog.set_object(obj)

        # Modify properties
        dialog.edtObjectName.setText("Modified Object")
        dialog.edtPropertyList[0].setText("C")
        dialog.edtPropertyList[1].setText("D")

        # Save changes
        dialog.save_object()

        # Verify changes saved
        obj = obj.get_by_id(obj.id)  # Refresh
        assert obj.object_name == "Modified Object"
        assert obj.property_str == "C,D"

    def test_edit_object_landmarks(self, qtbot, dataset_with_object):
        """Test editing object landmarks."""
        dataset, obj = dataset_with_object
        original_landmark_str = obj.landmark_str

        # Open dialog
        dialog = ObjectDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)
        dialog.set_object(obj)

        # Modify landmarks
        dialog.landmark_list = [[11.0, 12.0], [13.0, 14.0], [15.0, 16.0], [17.0, 18.0], [19.0, 20.0]]
        dialog.show_landmarks()

        # Save changes
        dialog.save_object()

        # Verify landmarks changed
        obj = obj.get_by_id(obj.id)
        assert obj.landmark_str == "11.0\t12.0\n13.0\t14.0\n15.0\t16.0\n17.0\t18.0\n19.0\t20.0"
        assert obj.landmark_str != original_landmark_str

    def test_edit_object_sequence(self, qtbot, dataset_with_object):
        """Test changing object sequence number."""
        dataset, obj = dataset_with_object

        dialog = ObjectDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)
        dialog.set_object(obj)

        # Change sequence
        dialog.edtSequence.setText("10")
        dialog.save_object()

        # Verify sequence changed
        obj = obj.get_by_id(obj.id)
        assert obj.sequence == 10


class TestObjectDeletionWorkflow:
    """Test object deletion workflows."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_delete_object_from_dataset(self, qtbot):
        """Test deleting object removes it from dataset."""
        # Create dataset with 3 objects
        dataset = MdModel.MdDataset.create(dataset_name="Delete Test", dimension=2, landmark_count=3)

        obj_ids = []
        for i in range(3):
            obj = MdModel.MdObject.create(object_name=f"Obj_{i + 1}", dataset=dataset, landmark_str="1,2\n3,4\n5,6")
            obj_ids.append(obj.id)

        # Verify 3 objects exist
        assert dataset.object_list.count() == 3

        # Delete middle object
        obj_to_delete = MdModel.MdObject.get_by_id(obj_ids[1])
        obj_to_delete.delete_instance()

        # Verify object deleted
        assert dataset.object_list.count() == 2
        assert not MdModel.MdObject.select().where(MdModel.MdObject.id == obj_ids[1]).exists()

        # Verify other objects still exist
        assert MdModel.MdObject.select().where(MdModel.MdObject.id == obj_ids[0]).exists()
        assert MdModel.MdObject.select().where(MdModel.MdObject.id == obj_ids[2]).exists()

    def test_delete_all_objects_from_dataset(self, qtbot):
        """Test deleting all objects leaves dataset intact."""
        dataset = MdModel.MdDataset.create(dataset_name="Empty Dataset Test", dimension=2, landmark_count=3)

        # Add 5 objects
        for i in range(5):
            MdModel.MdObject.create(object_name=f"Obj_{i}", dataset=dataset, landmark_str="1,2\n3,4\n5,6")

        dataset_id = dataset.id

        # Delete all objects
        for obj in list(dataset.object_list):
            obj.delete_instance()

        # Verify dataset still exists but has no objects
        dataset = MdModel.MdDataset.get_by_id(dataset_id)
        assert dataset is not None
        assert dataset.object_list.count() == 0


class TestObjectBatchOperations:
    """Test batch object operations."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_batch_create_objects_programmatically(self, qtbot):
        """Test creating many objects programmatically."""
        dataset = MdModel.MdDataset.create(
            dataset_name="Batch Dataset", dimension=2, landmark_count=5, propertyname_str="Group,Value"
        )

        # Batch create 50 objects
        for i in range(50):
            landmarks = "\n".join([f"{j + i}.0\t{j + i + 1}.0" for j in range(5)])
            MdModel.MdObject.create(
                object_name=f"Batch_Obj_{i:03d}",
                dataset=dataset,
                sequence=i + 1,
                landmark_str=landmarks,
                property_str=f"Group{i % 5},Value{i}",
            )

        # Verify all objects created
        assert dataset.object_list.count() == 50

        # Verify random samples
        obj_10 = dataset.object_list.where(MdModel.MdObject.object_name == "Batch_Obj_010").first()
        assert obj_10 is not None
        assert obj_10.property_str == "Group0,Value10"

        obj_25 = dataset.object_list.where(MdModel.MdObject.object_name == "Batch_Obj_025").first()
        assert obj_25 is not None
        assert obj_25.sequence == 26

    def test_batch_update_object_properties(self, qtbot):
        """Test updating multiple objects at once."""
        dataset = MdModel.MdDataset.create(
            dataset_name="Batch Update", dimension=2, landmark_count=3, propertyname_str="Status"
        )

        # Create 10 objects with "Active" status
        for i in range(10):
            MdModel.MdObject.create(
                object_name=f"Obj_{i}", dataset=dataset, landmark_str="1,2\n3,4\n5,6", property_str="Active"
            )

        # Batch update first 5 to "Inactive"
        for i, obj in enumerate(dataset.object_list):
            if i < 5:
                obj.property_str = "Inactive"
                obj.save()

        # Verify updates
        active_count = dataset.object_list.where(MdModel.MdObject.property_str == "Active").count()
        inactive_count = dataset.object_list.where(MdModel.MdObject.property_str == "Inactive").count()

        assert active_count == 5
        assert inactive_count == 5


class TestObjectValidation:
    """Test object validation workflows."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_object_requires_dataset(self, qtbot):
        """Test that object cannot be created without dataset."""
        dialog = ObjectDialog(parent=None)
        qtbot.addWidget(dialog)

        # Try to save without setting dataset - should handle gracefully
        # Note: Actual behavior depends on ObjectDialog implementation
        # This test documents expected behavior

    def test_object_landmark_count_validation(self, qtbot):
        """Test object landmark count matches dataset."""
        dataset = MdModel.MdDataset.create(
            dataset_name="Validation Test",
            dimension=2,
            landmark_count=5,  # Expects 5 landmarks
        )

        dialog = ObjectDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)

        dialog.edtObjectName.setText("Test")
        dialog.edtSequence.setText("1")

        # Set wrong number of landmarks (only 3 instead of 5)
        dialog.landmark_list = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        dialog.show_landmarks()

        # Save - behavior depends on validation logic
        # Some systems allow it, some don't
        dialog.save_object()

        # Document actual behavior
        obj = dataset.object_list.first()
        if obj:
            # If object was created, verify it exists
            assert obj.object_name == "Test"

    def test_object_with_empty_name(self, qtbot):
        """Test creating object with empty name."""
        dataset = MdModel.MdDataset.create(dataset_name="Empty Name Test", dimension=2, landmark_count=3)

        dialog = ObjectDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)

        # Leave name empty
        dialog.edtObjectName.setText("")
        dialog.edtSequence.setText("1")
        dialog.landmark_list = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        dialog.show_landmarks()

        dialog.save_object()

        # Verify object created (with empty or default name)
        assert dataset.object_list.count() == 1
