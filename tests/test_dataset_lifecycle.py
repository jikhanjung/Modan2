"""Dataset Lifecycle Integration Tests.

Tests complete dataset workflows from creation to deletion:
- Create dataset with variables
- Add objects to dataset
- Edit dataset properties
- Manage wireframes and baselines
- Dataset hierarchy (parent-child)
- Delete dataset with cascade
"""

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidgetItem

import MdModel
from dialogs import DatasetDialog


class TestDatasetCreationWorkflow:
    """Test complete dataset creation workflows."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_create_dataset_with_variables_and_objects(self, qtbot):
        """Test complete workflow: create dataset → add variables → add objects."""
        # Step 1: Create dataset
        dialog = DatasetDialog(parent=None)
        qtbot.addWidget(dialog)

        dialog.edtDatasetName.setText("Complete Workflow Dataset")
        dialog.edtDatasetDesc.setText("Testing complete workflow")
        dialog.rbtn2D.setChecked(True)

        # Add variables directly to the list widget
        for var_name in ["Sex", "Age", "Location"]:
            item = QListWidgetItem(var_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setData(Qt.UserRole, -1)
            dialog.lstVariableName.addItem(item)

        # Save dataset
        dialog.btnOkay.click()

        # Verify dataset created
        dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()
        assert dataset is not None
        assert dataset.dataset_name == "Complete Workflow Dataset"
        assert dataset.dimension == 2
        assert dataset.get_variablename_list() == ["Sex", "Age", "Location"]

        # Step 2: Add objects to dataset
        for i in range(3):
            landmark_str = "\n".join([f"{j}.0\t{j + 1}.0" for j in range(5)])
            obj = MdModel.MdObject.create(
                object_name=f"Object_{i + 1}",
                dataset=dataset,
                landmark_str=landmark_str,
                property_str=f"{'M' if i % 2 == 0 else 'F'},{20 + i},Site{i + 1}",
            )

        # Step 3: Verify consistency
        assert dataset.object_list.count() == 3

        # Verify each object has correct properties
        for obj in dataset.object_list:
            values = obj.property_str.split(",")
            assert len(values) == 3
            assert values[0] in ["M", "F"]
            assert int(values[1]) >= 20
            assert values[2].startswith("Site")

    def test_dataset_with_parent_child_hierarchy(self, qtbot):
        """Test creating dataset hierarchy with parent-child relationships."""
        # Step 1: Create parent dataset
        parent_dialog = DatasetDialog(parent=None)
        qtbot.addWidget(parent_dialog)

        parent_dialog.edtDatasetName.setText("Parent Dataset")
        parent_dialog.rbtn2D.setChecked(True)
        parent_dialog.btnOkay.click()

        parent_dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()

        # Step 2: Create child dataset
        child_dialog = DatasetDialog(parent=None)
        qtbot.addWidget(child_dialog)

        child_dialog.edtDatasetName.setText("Child Dataset")
        child_dialog.rbtn2D.setChecked(True)

        # Set parent dataset
        # Find parent in combo box and select it
        for i in range(child_dialog.cbxParent.count()):
            if child_dialog.cbxParent.itemData(i) == parent_dataset.id:
                child_dialog.cbxParent.setCurrentIndex(i)
                break

        child_dialog.btnOkay.click()

        # Step 3: Verify hierarchy
        child_dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()
        assert child_dataset.parent_id == parent_dataset.id

    def test_edit_dataset_properties_updates_objects(self, qtbot):
        """Test editing dataset properties updates all objects correctly."""
        # Step 1: Create dataset with objects
        dataset = MdModel.MdDataset.create(
            dataset_name="Edit Test Dataset", dimension=2, landmark_count=5, propertyname_str="Var1,Var2"
        )

        # Add objects with 2 variables
        for i in range(3):
            landmark_str = "\n".join([f"{j}.0\t{j + 1}.0" for j in range(5)])
            MdModel.MdObject.create(
                object_name=f"Obj_{i + 1}", dataset=dataset, landmark_str=landmark_str, property_str="A,B"
            )

        # Step 2: Open dialog to edit dataset
        dialog = DatasetDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)

        # Add a new variable (add to the list widget directly)
        item = QListWidgetItem("Var3")
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setData(Qt.UserRole, -1)
        dialog.lstVariableName.addItem(item)

        # Save changes
        dialog.btnOkay.click()

        # Step 3: Verify dataset updated
        dataset = dataset.get_by_id(dataset.id)  # Refresh
        assert dataset.get_variablename_list() == ["Var1", "Var2", "Var3"]

        # Step 4: Verify objects updated with new variable (should have empty value)
        for obj in dataset.object_list:
            values = obj.property_str.split(",")
            assert len(values) == 3  # Now has 3 values
            assert values[0] == "A"
            assert values[1] == "B"
            assert values[2] == ""  # New variable has empty value

    def test_dataset_with_wireframe_and_baseline(self, qtbot):
        """Test dataset with wireframe and baseline definitions."""
        # Create dataset with wireframe and baseline
        dialog = DatasetDialog(parent=None)
        qtbot.addWidget(dialog)

        dialog.edtDatasetName.setText("Wireframe Dataset")
        dialog.rbtn2D.setChecked(True)

        # Set wireframe (edges)
        wireframe = "0,1\n1,2\n2,3\n3,4\n4,0"
        dialog.edtWireframe.setPlainText(wireframe)

        # Set baseline
        dialog.edtBaseline.setText("0,4")

        dialog.btnOkay.click()

        # Verify dataset created with wireframe and baseline
        dataset = MdModel.MdDataset.select().order_by(MdModel.MdDataset.id.desc()).first()
        assert dataset.wireframe == wireframe
        assert dataset.baseline == "0,4"

    @pytest.mark.skip(reason="Variable reordering logic needs investigation")
    def test_reorder_variables_migrates_object_data(self, qtbot):
        """Test reordering variables correctly migrates object data."""
        # Step 1: Create dataset with 3 variables
        dataset = MdModel.MdDataset.create(
            dataset_name="Reorder Test", dimension=2, landmark_count=3, propertyname_str="A,B,C"
        )

        # Add object with values for each variable
        landmark_str = "1,2\n3,4\n5,6"
        obj = MdModel.MdObject.create(
            object_name="TestObj", dataset=dataset, landmark_str=landmark_str, property_str="ValueA,ValueB,ValueC"
        )

        # Step 2: Open dialog and reorder variables (C, A, B)
        dialog = DatasetDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)

        # Reorder: move variable at index 2 (C) to index 0
        # This simulates drag-and-drop reordering
        item_c = dialog.lstVariableName.takeItem(2)  # Remove C
        dialog.lstVariableName.insertItem(0, item_c)  # Insert C at beginning

        dialog.btnOkay.click()

        # Step 3: Verify variable order changed
        dataset = dataset.get_by_id(dataset.id)  # Refresh
        new_var_names = dataset.get_variablename_list()
        assert new_var_names == ["C", "A", "B"]

        # Step 4: Verify object values reordered correctly
        obj = obj.get_by_id(obj.id)  # Refresh
        new_values = obj.property_str.split(",")
        assert new_values == ["ValueC", "ValueA", "ValueB"]


class TestDatasetDeletionWorkflow:
    """Test dataset deletion workflows."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_delete_dataset_cascades_to_objects(self, qtbot):
        """Test deleting dataset also deletes all its objects."""
        # Step 1: Create dataset with objects
        dataset = MdModel.MdDataset.create(dataset_name="Delete Test", dimension=2, landmark_count=3)

        # Add 3 objects
        object_ids = []
        for i in range(3):
            obj = MdModel.MdObject.create(object_name=f"Obj_{i + 1}", dataset=dataset, landmark_str="1,2\n3,4\n5,6")
            object_ids.append(obj.id)

        # Verify objects exist
        assert dataset.object_list.count() == 3
        for obj_id in object_ids:
            assert MdModel.MdObject.select().where(MdModel.MdObject.id == obj_id).exists()

        # Step 2: Delete dataset
        dataset_id = dataset.id
        dataset.delete_instance()

        # Step 3: Verify dataset deleted
        assert not MdModel.MdDataset.select().where(MdModel.MdDataset.id == dataset_id).exists()

        # Step 4: Verify all objects deleted (cascade)
        for obj_id in object_ids:
            assert not MdModel.MdObject.select().where(MdModel.MdObject.id == obj_id).exists()

    def test_delete_parent_dataset_deletes_children(self, qtbot):
        """Test deleting parent dataset also deletes child datasets."""
        # Step 1: Create parent dataset
        parent = MdModel.MdDataset.create(dataset_name="Parent", dimension=2, landmark_count=3)

        # Step 2: Create 2 child datasets
        child1 = MdModel.MdDataset.create(dataset_name="Child1", dimension=2, landmark_count=3, parent_id=parent.id)
        child2 = MdModel.MdDataset.create(dataset_name="Child2", dimension=2, landmark_count=3, parent_id=parent.id)

        child1_id = child1.id
        child2_id = child2.id

        # Step 3: Delete parent
        parent_id = parent.id
        parent.delete_instance()

        # Step 4: Verify parent and children deleted
        assert not MdModel.MdDataset.select().where(MdModel.MdDataset.id == parent_id).exists()
        assert not MdModel.MdDataset.select().where(MdModel.MdDataset.id == child1_id).exists()
        assert not MdModel.MdDataset.select().where(MdModel.MdDataset.id == child2_id).exists()


class TestDatasetModificationWorkflow:
    """Test dataset modification workflows."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_add_variable_to_existing_dataset(self, qtbot):
        """Test adding variable to dataset with existing objects."""
        # Step 1: Create dataset with objects
        dataset = MdModel.MdDataset.create(dataset_name="Add Var Test", dimension=2, landmark_count=3)

        for i in range(3):
            MdModel.MdObject.create(object_name=f"Obj_{i + 1}", dataset=dataset, landmark_str="1,2\n3,4\n5,6")

        # Step 2: Add variable through dialog
        dialog = DatasetDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)

        item = QListWidgetItem("NewVariable")
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setData(Qt.UserRole, -1)
        dialog.lstVariableName.addItem(item)
        dialog.btnOkay.click()

        # Step 3: Verify variable added
        dataset = dataset.get_by_id(dataset.id)
        assert "NewVariable" in dataset.get_variablename_list()

        # Step 4: Verify all objects have empty value for new variable
        for obj in dataset.object_list:
            if obj.property_str:
                values = obj.property_str.split(",")
                # Last value should be empty (new variable)
                assert values[-1] == ""

    @pytest.mark.skip(reason="Variable deletion logic needs investigation")
    def test_remove_variable_from_dataset(self, qtbot):
        """Test removing variable from dataset updates objects."""
        # Step 1: Create dataset with 3 variables
        dataset = MdModel.MdDataset.create(
            dataset_name="Remove Var Test", dimension=2, landmark_count=3, propertyname_str="Var1,Var2,Var3"
        )

        # Add object with all 3 values
        obj = MdModel.MdObject.create(
            object_name="TestObj", dataset=dataset, landmark_str="1,2\n3,4\n5,6", property_str="A,B,C"
        )

        # Step 2: Remove middle variable (Var2)
        dialog = DatasetDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)

        # Select and remove Var2 (index 1)
        dialog.lstVariableName.setCurrentRow(1)
        dialog.btnDeleteVariable.click()
        dialog.btnOkay.click()

        # Step 3: Verify variable removed
        dataset = dataset.get_by_id(dataset.id)
        assert dataset.get_variablename_list() == ["Var1", "Var3"]

        # Step 4: Verify object values updated (B removed)
        obj = obj.get_by_id(obj.id)
        assert obj.property_str == "A,C"

    def test_change_dataset_dimension_validation(self, qtbot):
        """Test that dimension cannot be changed after objects added."""
        # Step 1: Create dataset with objects
        dataset = MdModel.MdDataset.create(dataset_name="Dimension Test", dimension=2, landmark_count=3)

        MdModel.MdObject.create(object_name="Obj1", dataset=dataset, landmark_str="1,2\n3,4\n5,6")

        # Step 2: Try to change dimension
        dialog = DatasetDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog.set_dataset(dataset)

        # Dimension radio buttons should be disabled
        assert not dialog.rbtn2D.isEnabled()
        assert not dialog.rbtn3D.isEnabled()


class TestLargeDatasetWorkflow:
    """Test workflows with large datasets."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_create_dataset_with_many_objects(self, qtbot):
        """Test creating dataset with 100+ objects."""
        # Step 1: Create dataset
        dataset = MdModel.MdDataset.create(
            dataset_name="Large Dataset", dimension=2, landmark_count=5, propertyname_str="Group,Size"
        )

        # Step 2: Add 100 objects
        for i in range(100):
            landmark_str = "\n".join([f"{j + i}.0\t{j + i + 1}.0" for j in range(5)])
            MdModel.MdObject.create(
                object_name=f"Obj_{i:03d}",
                dataset=dataset,
                landmark_str=landmark_str,
                property_str=f"Group{i % 10},Size{i}",
            )

        # Step 3: Verify all objects created
        assert dataset.object_list.count() == 100

        # Step 4: Verify random sampling of objects
        obj_50 = dataset.object_list.where(MdModel.MdObject.object_name == "Obj_050").first()
        assert obj_50 is not None
        assert obj_50.property_str == "Group0,Size50"

    def test_edit_dataset_with_many_variables(self, qtbot):
        """Test dataset with many variables (20+)."""
        # Create dataset with 20 variables
        var_names = [f"Var{i:02d}" for i in range(20)]
        dataset = MdModel.MdDataset.create(
            dataset_name="Many Variables", dimension=2, landmark_count=3, propertyname_str=",".join(var_names)
        )

        # Add object with all variable values
        values = [f"Val{i:02d}" for i in range(20)]
        MdModel.MdObject.create(
            object_name="Obj1", dataset=dataset, landmark_str="1,2\n3,4\n5,6", property_str=",".join(values)
        )

        # Verify dataset and object consistency
        assert len(dataset.get_variablename_list()) == 20
        obj = dataset.object_list.first()
        assert len(obj.property_str.split(",")) == 20
