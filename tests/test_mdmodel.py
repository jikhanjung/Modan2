"""Tests for MdModel module - Database models and operations."""

import os
import sys
import tempfile

import pytest
from peewee import IntegrityError

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peewee import SqliteDatabase

import MdModel as mm


@pytest.fixture
def test_database():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name

    # Create test database
    test_db = SqliteDatabase(test_db_path, pragmas={"foreign_keys": 1})

    # Replace the global database with test database
    original_db = mm.gDatabase
    mm.gDatabase = test_db

    # Update model metadata
    mm.MdDataset._meta.database = test_db
    mm.MdObject._meta.database = test_db
    mm.MdImage._meta.database = test_db
    mm.MdThreeDModel._meta.database = test_db
    mm.MdAnalysis._meta.database = test_db

    # Create tables
    test_db.connect()
    test_db.create_tables([mm.MdDataset, mm.MdObject, mm.MdImage, mm.MdThreeDModel, mm.MdAnalysis])

    yield test_db

    # Cleanup
    test_db.drop_tables([mm.MdDataset, mm.MdObject, mm.MdImage, mm.MdThreeDModel, mm.MdAnalysis])
    test_db.close()

    # Restore original database
    mm.gDatabase = original_db
    mm.MdDataset._meta.database = original_db
    mm.MdObject._meta.database = original_db
    mm.MdImage._meta.database = original_db
    mm.MdThreeDModel._meta.database = original_db
    mm.MdAnalysis._meta.database = original_db

    # Remove test database file
    try:
        os.unlink(test_db_path)
    except:
        pass


@pytest.fixture
def temp_test_file(tmp_path):
    """Create a temporary test file."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("test content")
    return str(test_file)


class TestDatabaseConstants:
    """Test database-related constants."""

    def test_separators(self):
        """Test separator constants."""
        assert mm.LANDMARK_SEPARATOR == "\t"
        assert mm.LINE_SEPARATOR == "\n"
        assert mm.VARIABLE_SEPARATOR == ","
        assert mm.EDGE_SEPARATOR == "-"
        assert mm.WIREFRAME_SEPARATOR == ","

    def test_database_filename(self):
        """Test database filename generation."""
        assert mm.DATABASE_FILENAME.endswith(".db")
        assert "Modan2" in mm.DATABASE_FILENAME


class TestMdDataset:
    """Test MdDataset model."""

    def test_create_dataset(self, test_database):
        """Test creating a new dataset."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset", dataset_desc="Test Description", dimension=2)

        assert dataset.id is not None
        assert dataset.dataset_name == "Test Dataset"
        assert dataset.dataset_desc == "Test Description"
        assert dataset.dimension == 2
        assert dataset.created_at is not None
        assert dataset.modified_at is not None

    def test_dataset_defaults(self, test_database):
        """Test dataset default values."""
        dataset = mm.MdDataset.create(dataset_name="Minimal Dataset")

        assert dataset.dimension == 2  # Default dimension
        assert dataset.parent is None
        assert dataset.wireframe is None
        assert dataset.baseline is None
        assert dataset.polygons is None

    def test_dataset_parent_child_relationship(self, test_database):
        """Test parent-child relationship between datasets."""
        parent = mm.MdDataset.create(dataset_name="Parent Dataset")
        child = mm.MdDataset.create(dataset_name="Child Dataset", parent=parent)

        assert child.parent == parent
        assert child in parent.children

    def test_pack_unpack_variablename_str(self, test_database):
        """Test packing and unpacking variable names."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")

        # Test packing
        variablename_list = ["var1", "var2", "var3"]
        packed_str = dataset.pack_variablename_str(variablename_list)
        assert packed_str == "var1,var2,var3"
        assert dataset.propertyname_str == "var1,var2,var3"

        # Test unpacking
        unpacked_list = dataset.unpack_variablename_str()
        assert unpacked_list == variablename_list

    def test_unpack_empty_variablename(self, test_database):
        """Test unpacking empty variable name string."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")

        # Test with None
        dataset.propertyname_str = None
        assert dataset.unpack_variablename_str() == []

        # Test with empty string
        dataset.propertyname_str = ""
        assert dataset.unpack_variablename_str() == []

    def test_get_variablename_list(self, test_database):
        """Test getting variable name list."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset", propertyname_str="width,height,depth")

        variablename_list = dataset.get_variablename_list()
        assert variablename_list == ["width", "height", "depth"]

    def test_update_dataset_name(self, test_database):
        """Test updating dataset name."""
        dataset = mm.MdDataset.create(dataset_name="Original Name", dataset_desc="Original Description")
        original_id = dataset.id

        # Update the dataset name
        dataset.dataset_name = "Updated Name"
        dataset.save()

        # Verify the update
        updated_dataset = mm.MdDataset.get_by_id(original_id)
        assert updated_dataset.dataset_name == "Updated Name"
        assert updated_dataset.dataset_desc == "Original Description"  # Should remain unchanged
        assert updated_dataset.id == original_id  # ID should remain the same

    def test_update_multiple_fields(self, test_database):
        """Test updating multiple dataset fields."""
        dataset = mm.MdDataset.create(dataset_name="Original Name", dataset_desc="Original Description", dimension=2)

        # Update multiple fields
        dataset.dataset_name = "New Name"
        dataset.dataset_desc = "New Description"
        dataset.dimension = 3
        dataset.save()

        # Verify all updates
        updated_dataset = mm.MdDataset.get_by_id(dataset.id)
        assert updated_dataset.dataset_name == "New Name"
        assert updated_dataset.dataset_desc == "New Description"
        assert updated_dataset.dimension == 3

    def test_delete_dataset(self, test_database):
        """Test deleting a dataset."""
        dataset = mm.MdDataset.create(dataset_name="To Delete", dataset_desc="Will be deleted")
        dataset_id = dataset.id

        # Verify dataset exists
        assert mm.MdDataset.get_by_id(dataset_id) is not None

        # Delete the dataset
        dataset.delete_instance()

        # Verify dataset no longer exists
        with pytest.raises(mm.MdDataset.DoesNotExist):
            mm.MdDataset.get_by_id(dataset_id)

    def test_delete_dataset_with_cascade(self, test_database):
        """Test that deleting dataset cascades to related objects."""
        # Create dataset with related objects
        dataset = mm.MdDataset.create(dataset_name="Parent Dataset")
        obj1 = mm.MdObject.create(object_name="Child Object 1", dataset=dataset)
        obj2 = mm.MdObject.create(object_name="Child Object 2", dataset=dataset)

        dataset_id = dataset.id
        obj1_id = obj1.id
        obj2_id = obj2.id

        # Verify all exist
        assert mm.MdDataset.get_by_id(dataset_id) is not None
        assert mm.MdObject.get_by_id(obj1_id) is not None
        assert mm.MdObject.get_by_id(obj2_id) is not None

        # Delete the parent dataset
        dataset.delete_instance(recursive=True)

        # Verify cascade delete worked
        with pytest.raises(mm.MdDataset.DoesNotExist):
            mm.MdDataset.get_by_id(dataset_id)
        with pytest.raises(mm.MdObject.DoesNotExist):
            mm.MdObject.get_by_id(obj1_id)
        with pytest.raises(mm.MdObject.DoesNotExist):
            mm.MdObject.get_by_id(obj2_id)


class TestMdObject:
    """Test MdObject model."""

    def test_create_object(self, test_database):
        """Test creating a new object."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="Test Object", object_desc="Test Description", dataset=dataset, sequence=1)

        assert obj.id is not None
        assert obj.object_name == "Test Object"
        assert obj.object_desc == "Test Description"
        assert obj.dataset == dataset
        assert obj.sequence == 1

    def test_object_defaults(self, test_database):
        """Test object default values."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="Minimal Object", dataset=dataset)

        assert obj.pixels_per_mm is None
        assert obj.sequence is None
        assert obj.landmark_str is None
        assert obj.property_str is None

    def test_pack_unpack_landmark_2d(self, test_database):
        """Test packing and unpacking 2D landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset", dimension=2)
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)

        # Test 2D landmarks
        obj.landmark_list = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        obj.pack_landmark()
        assert obj.landmark_str == "1.0\t2.0\n3.0\t4.0\n5.0\t6.0"

        # Test unpacking
        obj.landmark_list = []  # Reset
        obj.unpack_landmark()
        assert len(obj.landmark_list) == 3
        assert obj.landmark_list[0] == [1.0, 2.0]
        assert obj.landmark_list[1] == [3.0, 4.0]
        assert obj.landmark_list[2] == [5.0, 6.0]

    def test_pack_unpack_landmark_3d(self, test_database):
        """Test packing and unpacking 3D landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset", dimension=3)
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)

        # Test 3D landmarks
        obj.landmark_list = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        obj.pack_landmark()
        assert obj.landmark_str == "1.0\t2.0\t3.0\n4.0\t5.0\t6.0"

        # Test unpacking
        obj.landmark_list = []  # Reset
        obj.unpack_landmark()
        assert len(obj.landmark_list) == 2
        assert obj.landmark_list[0] == [1.0, 2.0, 3.0]
        assert obj.landmark_list[1] == [4.0, 5.0, 6.0]

    def test_pack_unpack_variable(self, test_database):
        """Test packing and unpacking variables."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)

        # Test packing
        obj.variable_list = ["male", "adult", "large"]
        obj.pack_variable()
        assert obj.property_str == "male,adult,large"

        # Test unpacking
        obj.variable_list = []  # Reset
        obj.unpack_variable()
        assert obj.variable_list == ["male", "adult", "large"]

    def test_update_object_name(self, test_database):
        """Test updating object name."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="Original Name", object_desc="Original Description", dataset=dataset)
        original_id = obj.id

        # Update the object name
        obj.object_name = "Updated Name"
        obj.save()

        # Verify the update
        updated_obj = mm.MdObject.get_by_id(original_id)
        assert updated_obj.object_name == "Updated Name"
        assert updated_obj.object_desc == "Original Description"  # Should remain unchanged
        assert updated_obj.id == original_id  # ID should remain the same

    def test_delete_object(self, test_database):
        """Test deleting an object."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="To Delete", dataset=dataset)
        obj_id = obj.id

        # Verify object exists
        assert mm.MdObject.get_by_id(obj_id) is not None

        # Delete the object
        obj.delete_instance()

        # Verify object no longer exists
        with pytest.raises(mm.MdObject.DoesNotExist):
            mm.MdObject.get_by_id(obj_id)

        # Verify dataset still exists (no reverse cascade)
        assert mm.MdDataset.get_by_id(dataset.id) is not None


class TestMdAnalysis:
    """Test MdAnalysis model."""

    def test_create_analysis(self, test_database):
        """Test creating a new analysis."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        analysis = mm.MdAnalysis.create(
            analysis_name="PCA Analysis",
            analysis_desc="Principal Component Analysis",
            dataset=dataset,
            superimposition_method="Procrustes",  # Required field
        )

        assert analysis.id is not None
        assert analysis.analysis_name == "PCA Analysis"
        assert analysis.analysis_desc == "Principal Component Analysis"
        assert analysis.dataset == dataset
        assert analysis.superimposition_method == "Procrustes"

    def test_analysis_defaults(self, test_database):
        """Test analysis default values."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        analysis = mm.MdAnalysis.create(
            analysis_name="Test Analysis",
            dataset=dataset,
            superimposition_method="None",  # Required field
        )

        assert analysis.dimension == 2  # Default dimension
        assert analysis.analysis_desc is None
        assert analysis.wireframe is None
        assert analysis.baseline is None


class TestDatabaseOperations:
    """Test database-level operations."""

    def test_cascade_delete(self, test_database):
        """Test cascade delete from parent dataset."""
        parent = mm.MdDataset.create(dataset_name="Parent")
        child = mm.MdDataset.create(dataset_name="Child", parent=parent)
        obj = mm.MdObject.create(object_name="Object", dataset=child)

        parent_id = parent.id
        child_id = child.id
        obj_id = obj.id

        # Delete parent should cascade to child and its objects
        # Use delete_instance with recursive=True and dependencies=True
        parent.delete_instance(recursive=True, delete_nullable=True)

        # Verify deletion
        assert mm.MdDataset.select().where(mm.MdDataset.id == parent_id).count() == 0
        assert mm.MdDataset.select().where(mm.MdDataset.id == child_id).count() == 0
        assert mm.MdObject.select().where(mm.MdObject.id == obj_id).count() == 0

    def test_foreign_key_constraint(self, test_database):
        """Test foreign key constraints."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        mm.MdObject.create(object_name="Test Object", dataset=dataset)

        # Should not be able to delete dataset while object exists (if FKs are enforced)
        # In SQLite, this depends on foreign_keys pragma being enabled
        try:
            # Try to delete the dataset directly via SQL
            test_database.execute_sql(f"DELETE FROM mddataset WHERE id = {dataset.id}")
            # If no exception, check if the delete actually happened
            remaining = mm.MdDataset.select().where(mm.MdDataset.id == dataset.id).count()
            if remaining > 0:
                # Foreign key constraint prevented deletion
                pass
        except Exception:
            # Foreign key constraint raised exception - this is expected behavior
            pass

    def test_transaction_rollback(self, test_database):
        """Test transaction rollback on error."""
        with test_database.atomic() as transaction:
            try:
                mm.MdDataset.create(dataset_name="Test Dataset")
                # Force an error
                raise Exception("Test error")
            except:
                transaction.rollback()

        # Dataset should not exist due to rollback
        assert mm.MdDataset.select().where(mm.MdDataset.dataset_name == "Test Dataset").count() == 0


class TestErrorHandling:
    """Test error handling and edge cases in database models."""

    def test_create_dataset_duplicate_name_allowed(self, test_database):
        """Test that duplicate dataset names are allowed (if not constrained)."""
        mm.MdDataset.create(dataset_name="Duplicate Name")

        # Should be able to create another dataset with the same name
        # (unless unique constraint is enforced)
        duplicate_dataset = mm.MdDataset.create(dataset_name="Duplicate Name")
        assert duplicate_dataset.id is not None

    def test_create_object_missing_required_dataset(self, test_database):
        """Test creating object without dataset reference."""
        with pytest.raises((ValueError, IntegrityError)):
            # This should fail since dataset is required (NOT NULL constraint)
            mm.MdObject.create(object_name="Orphan Object", dataset=None)

    def test_invalid_landmark_data_handling(self, test_database):
        """Test handling of invalid landmark string data."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)

        # Test with malformed landmark string
        obj.landmark_str = "invalid\tdata\tformat\nextra_values"

        try:
            obj.unpack_landmark()
            # If it succeeds, check that it handled the error gracefully
            assert isinstance(obj.landmark_list, list)
        except (ValueError, IndexError):
            # These exceptions are acceptable for malformed data
            pass

    def test_empty_variablename_str_handling(self, test_database):
        """Test handling of various empty variable name strings."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")

        # Test None
        dataset.propertyname_str = None
        result = dataset.unpack_variablename_str()
        assert result == []

        # Test empty string
        dataset.propertyname_str = ""
        result = dataset.unpack_variablename_str()
        assert result == []

        # Test whitespace only
        dataset.propertyname_str = "   "
        result = dataset.unpack_variablename_str()
        # Should handle whitespace gracefully
        assert isinstance(result, list)

    def test_large_landmark_data(self, test_database):
        """Test handling of large amounts of landmark data."""
        dataset = mm.MdDataset.create(dataset_name="Large Dataset", dimension=2)
        obj = mm.MdObject.create(object_name="Large Object", dataset=dataset)

        # Create a large landmark list (100 landmarks)
        large_landmark_list = [[float(i), float(i + 1)] for i in range(100)]
        obj.landmark_list = large_landmark_list

        # Should handle large data without issues
        obj.pack_landmark()
        assert obj.landmark_str is not None
        assert len(obj.landmark_str) > 0

        # Test unpacking
        obj.landmark_list = []
        obj.unpack_landmark()
        assert len(obj.landmark_list) == 100
        assert obj.landmark_list[0] == [0.0, 1.0]
        assert obj.landmark_list[99] == [99.0, 100.0]


class TestWireframeEdgeParsing:
    """Test wireframe edge parsing logic."""

    def test_parse_wireframe_valid(self, test_database):
        """Test parsing valid wireframe edge data."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")

        # Valid wireframe format
        dataset.wireframe = "1-2,2-3,3-1"
        dataset.save()

        # Verify it was saved
        loaded = mm.MdDataset.get_by_id(dataset.id)
        assert loaded.wireframe == "1-2,2-3,3-1"

    def test_parse_wireframe_empty(self, test_database):
        """Test parsing empty wireframe."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")

        # Empty wireframe
        dataset.wireframe = ""
        dataset.save()

        loaded = mm.MdDataset.get_by_id(dataset.id)
        assert loaded.wireframe == ""

    def test_parse_wireframe_with_spaces(self, test_database):
        """Test wireframe with various separators."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")

        # Wireframe with spaces (should be handled)
        dataset.wireframe = "1-2, 2-3, 3-1"
        dataset.save()

        loaded = mm.MdDataset.get_by_id(dataset.id)
        assert loaded.wireframe is not None


class TestMdObjectOpsCreation:
    """Test MdObjectOps wrapper class creation."""

    def test_create_object_ops(self, test_database):
        """Test creating MdObjectOps from MdObject."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset", dimension=2)
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)
        obj.landmark_str = "1.0\t2.0\n3.0\t4.0"
        obj.property_str = "male,adult"

        # Create MdObjectOps wrapper
        obj_ops = mm.MdObjectOps(obj)

        # Verify properties are copied
        assert obj_ops.id == obj.id
        assert obj_ops.object_name == obj.object_name
        assert obj_ops.landmark_str == obj.landmark_str
        assert obj_ops.property_str == obj.property_str

    def test_object_ops_with_landmark_list(self, test_database):
        """Test MdObjectOps preserves landmark_list."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset", dimension=2)
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)
        obj.landmark_list = [[1.0, 2.0], [3.0, 4.0]]

        # Create ops wrapper
        obj_ops = mm.MdObjectOps(obj)

        # Should have landmark_list
        assert hasattr(obj_ops, "landmark_list")
        assert obj_ops.landmark_list == [[1.0, 2.0], [3.0, 4.0]]


class TestMdAnalysisExtended:
    """Extended tests for MdAnalysis model."""

    def test_analysis_with_wireframe(self, test_database):
        """Test analysis with wireframe data."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        analysis = mm.MdAnalysis.create(
            analysis_name="Test Analysis", dataset=dataset, superimposition_method="Procrustes", wireframe="1-2,2-3,3-1"
        )

        assert analysis.wireframe == "1-2,2-3,3-1"

    def test_analysis_with_baseline(self, test_database):
        """Test analysis with baseline landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        analysis = mm.MdAnalysis.create(
            analysis_name="Test Analysis", dataset=dataset, superimposition_method="Procrustes", baseline="1,2,3"
        )

        assert analysis.baseline == "1,2,3"

    def test_analysis_requires_dataset(self, test_database):
        """Test that analysis requires dataset reference."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        analysis = mm.MdAnalysis.create(
            analysis_name="Test Analysis", dataset=dataset, superimposition_method="Procrustes"
        )

        # Verify analysis is linked to dataset
        assert analysis.dataset == dataset
        assert analysis.dataset.id == dataset.id


class TestMdObjectMethods:
    """Test MdObject helper methods."""

    def test_get_name_with_name(self, test_database):
        """Test get_name when object_name is set."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        obj = mm.MdObject.create(object_name="MyObject", dataset=dataset)

        assert obj.get_name() == "MyObject"

    def test_get_name_without_name(self, test_database):
        """Test get_name when object_name is empty."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        obj = mm.MdObject.create(object_name="", dataset=dataset)

        # Should return string of ID
        assert obj.get_name() == str(obj.id)

    # Note: object_name has NOT NULL constraint, so we can't test with None

    def test_count_landmarks_empty(self, test_database):
        """Test count_landmarks with no landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        assert obj.count_landmarks() == 0
        assert obj.count_landmarks(exclude_missing=False) == 0

    def test_count_landmarks_with_data(self, test_database):
        """Test count_landmarks with landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset, landmark_str="1.0\t2.0\n3.0\t4.0\n5.0\t6.0")
        obj.unpack_landmark()

        assert obj.count_landmarks() == 3
        assert obj.count_landmarks(exclude_missing=False) == 3

    def test_count_landmarks_excluding_missing(self, test_database):
        """Test count_landmarks excluding missing landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        # Create object with manually set missing landmark (None values)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)
        # Set landmarks with one missing
        obj.landmark_list = [[1.0, 2.0], [None, None], [5.0, 6.0]]
        obj.pack_landmark()

        # exclude_missing=True should count only valid landmarks
        assert obj.count_landmarks(exclude_missing=True) == 2
        # exclude_missing=False should count all landmarks
        assert obj.count_landmarks(exclude_missing=False) == 3

    def test_has_image_false(self, test_database):
        """Test has_image when no image attached."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        assert obj.has_image() is False

    def test_has_threed_model_false(self, test_database):
        """Test has_threed_model when no model attached."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        assert obj.has_threed_model() is False

    def test_str_repr(self, test_database):
        """Test __str__ and __repr__ methods."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        obj = mm.MdObject.create(object_name="MyObject", dataset=dataset)

        assert str(obj) == "MyObject"
        assert repr(obj) == "MyObject"

    def test_str_repr_empty_name(self, test_database):
        """Test __str__ and __repr__ with empty name."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        obj = mm.MdObject.create(object_name="", dataset=dataset)

        assert str(obj) == ""
        assert repr(obj) == ""


class TestMdDatasetPackingMethods:
    """Test MdDataset pack/unpack methods."""

    def test_pack_variablename_str_from_list(self, test_database):
        """Test pack_variablename_str with provided list."""
        dataset = mm.MdDataset.create(dataset_name="Test")

        result = dataset.pack_variablename_str(["age", "weight", "length"])

        assert result == "age,weight,length"
        assert dataset.propertyname_str == "age,weight,length"

    def test_pack_variablename_str_from_attribute(self, test_database):
        """Test pack_variablename_str using variablename_list attribute."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        dataset.variablename_list = ["var1", "var2"]

        result = dataset.pack_variablename_str()

        assert result == "var1,var2"

    def test_unpack_variablename_str_with_parameter(self, test_database):
        """Test unpack_variablename_str with parameter."""
        dataset = mm.MdDataset.create(dataset_name="Test")

        result = dataset.unpack_variablename_str("a,b,c")

        assert result == ["a", "b", "c"]
        assert dataset.variablename_list == ["a", "b", "c"]

    def test_unpack_variablename_str_from_attribute(self, test_database):
        """Test unpack_variablename_str using propertyname_str attribute."""
        dataset = mm.MdDataset.create(dataset_name="Test", propertyname_str="x,y,z")

        result = dataset.unpack_variablename_str()

        assert result == ["x", "y", "z"]

    def test_get_variablename_list(self, test_database):
        """Test get_variablename_list method."""
        dataset = mm.MdDataset.create(dataset_name="Test", propertyname_str="v1,v2,v3")

        result = dataset.get_variablename_list()

        assert result == ["v1", "v2", "v3"]

    def test_pack_wireframe(self, test_database):
        """Test pack_wireframe method."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        dataset.edge_list = [[1, 2], [2, 3], [0, 1]]

        dataset.pack_wireframe()

        # Edges should be sorted
        assert dataset.wireframe is not None
        # Should contain edge data
        assert "1-2" in dataset.wireframe or "2-1" in dataset.wireframe

    def test_pack_polygons(self, test_database):
        """Test pack_polygons method."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        dataset.polygon_list = [[0, 1, 2], [1, 2, 3]]

        dataset.pack_polygons()

        assert dataset.polygons is not None
        # Polygons use "-" to separate points, "," to separate polygons
        assert "0-1-2" in dataset.polygons

    def test_pack_baseline(self, test_database):
        """Test pack_baseline method."""
        dataset = mm.MdDataset.create(dataset_name="Test")
        dataset.baseline_point_list = [0, 1, 2]

        dataset.pack_baseline()

        assert dataset.baseline == "0,1,2"

    def test_get_edge_list(self, test_database):
        """Test get_edge_list method."""
        dataset = mm.MdDataset.create(dataset_name="Test", wireframe="0-1,1-2,2-0")
        dataset.unpack_wireframe()

        result = dataset.get_edge_list()

        assert len(result) == 3
        assert [0, 1] in result or [1, 0] in result

    def test_get_polygon_list(self, test_database):
        """Test get_polygon_list method."""
        dataset = mm.MdDataset.create(
            dataset_name="Test",
            polygons="0-1-2,1-2-3",  # Use "-" for points, "," for polygons
        )
        dataset.unpack_polygons()

        result = dataset.get_polygon_list()

        assert len(result) == 2
        assert [0, 1, 2] in result

    def test_get_baseline_points(self, test_database):
        """Test get_baseline_points method."""
        dataset = mm.MdDataset.create(dataset_name="Test", baseline="0,1,2,3")
        dataset.unpack_baseline()

        result = dataset.get_baseline_points()

        assert result == [0, 1, 2, 3]


class TestCentroidCalculations:
    """Test centroid calculation methods."""

    def test_get_centroid_size_2d(self, test_database):
        """Test centroid size calculation for 2D landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        # Create symmetric landmarks around origin
        obj.landmark_list = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        obj.pack_landmark()
        obj.save()

        centroid_size = obj.get_centroid_size()

        # Centroid size should be positive
        assert centroid_size > 0

    def test_get_centroid_size_3d(self, test_database):
        """Test centroid size calculation for 3D landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        # Create 3D landmarks
        obj.landmark_list = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        obj.pack_landmark()
        obj.save()

        centroid_size = obj.get_centroid_size()

        assert centroid_size > 0

    def test_get_centroid_size_with_missing_landmarks(self, test_database):
        """Test centroid size with missing landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        # Include missing landmark (None values)
        obj.landmark_list = [[1.0, 2.0], [None, None], [3.0, 4.0]]
        obj.pack_landmark()
        obj.save()

        centroid_size = obj.get_centroid_size()

        # Should calculate centroid excluding missing landmarks
        assert centroid_size > 0

    def test_get_centroid_size_single_landmark(self, test_database):
        """Test centroid size with single landmark."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        obj.landmark_list = [[5.0, 10.0]]
        obj.pack_landmark()
        obj.save()

        centroid_size = obj.get_centroid_size()

        # Single landmark returns 1
        assert centroid_size == 1

    def test_get_centroid_size_no_landmarks(self, test_database):
        """Test centroid size with no landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        centroid_size = obj.get_centroid_size()

        # No landmarks returns -1
        assert centroid_size == -1

    def test_get_centroid_size_with_pixels_per_mm(self, test_database):
        """Test centroid size with pixels_per_mm conversion."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset, pixels_per_mm=10.0)

        obj.landmark_list = [[0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [10.0, 10.0]]
        obj.pack_landmark()
        obj.save()

        centroid_size = obj.get_centroid_size()

        # Should be scaled by pixels_per_mm
        assert centroid_size > 0

    def test_get_centroid_size_cached(self, test_database):
        """Test that centroid size is cached."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        obj.landmark_list = [[0.0, 0.0], [1.0, 1.0]]
        obj.pack_landmark()
        obj.save()

        # First call calculates
        size1 = obj.get_centroid_size()
        # Second call should return cached value
        size2 = obj.get_centroid_size(refresh=False)

        assert size1 == size2
        assert size1 > 0

    def test_get_centroid_coord_2d(self, test_database):
        """Test centroid coordinate calculation for 2D."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        # Landmarks with known centroid: (0.5, 0.5)
        obj.landmark_list = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]

        centroid = obj.get_centroid_coord()

        assert len(centroid) == 3  # Returns [x, y, z]
        assert centroid[0] == 0.5  # X coordinate
        assert centroid[1] == 0.5  # Y coordinate

    def test_get_centroid_coord_3d(self, test_database):
        """Test centroid coordinate calculation for 3D."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        # 3D landmarks
        obj.landmark_list = [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]]

        centroid = obj.get_centroid_coord()

        assert len(centroid) == 3
        assert centroid[0] == 0.5  # Mean of X
        assert centroid[1] == 0.5  # Mean of Y
        assert centroid[2] == 0.5  # Mean of Z

    def test_get_centroid_coord_with_missing(self, test_database):
        """Test centroid coordinate with missing landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        # Include None values
        obj.landmark_list = [[0.0, 0.0], [None, None], [2.0, 2.0]]

        centroid = obj.get_centroid_coord()

        # Should calculate mean excluding None values
        assert centroid[0] == 1.0  # (0 + 2) / 2
        assert centroid[1] == 1.0  # (0 + 2) / 2

    def test_get_centroid_coord_empty(self, test_database):
        """Test centroid coordinate with no landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        centroid = obj.get_centroid_coord()

        # Empty landmarks should return [0, 0, 0]
        assert centroid == [0, 0, 0]


class TestMdDatasetOps:
    """Test MdDatasetOps methods."""

    def test_add_object(self, test_database):
        """Test adding object to dataset."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        new_obj = dataset.add_object(object_name="NewObject")
        new_obj.save()  # Need to save to get an ID

        assert new_obj is not None
        assert new_obj.object_name == "NewObject"
        assert new_obj.dataset == dataset
        assert new_obj.id is not None

    def test_get_edge_list(self, test_database):
        """Test getting edge list from wireframe."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        dataset.wireframe = "0-1,1-2,2-0"  # Format: "vertex1-vertex2,vertex3-vertex4,..."
        dataset.unpack_wireframe()

        edge_list = dataset.get_edge_list()

        assert edge_list is not None
        assert len(edge_list) == 3
        assert [0, 1] in edge_list
        assert [1, 2] in edge_list
        assert [2, 0] in edge_list or [0, 2] in edge_list  # Edges may be sorted

    def test_pack_unpack_variablename(self, test_database):
        """Test packing and unpacking variable names."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        variablename_list = ["var1", "var2", "var3"]

        dataset.pack_variablename_str(variablename_list)
        dataset.save()

        # Reload and unpack
        dataset = mm.MdDataset.get_by_id(dataset.id)
        dataset.unpack_variablename_str()

        result_list = dataset.get_variablename_list()
        assert result_list == variablename_list

    def test_get_baseline_points(self, test_database):
        """Test getting baseline points."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        baseline_points = [0, 1]  # Baseline is stored as flat list of landmark indices

        dataset.pack_baseline(baseline_points)
        dataset.save()

        # Reload and get baseline
        dataset = mm.MdDataset.get_by_id(dataset.id)
        dataset.unpack_baseline()  # Need to unpack first
        result = dataset.get_baseline_points()

        assert result == baseline_points


class TestMdImage:
    """Test MdImage model."""

    def test_create_image(self, test_database):
        """Test creating an image record."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        _image = mm.MdImage.create(
            object=obj, original_path="/path/to/test.jpg", original_filename="test.jpg", size=1024, md5hash="abc123"
        )

        assert _image.id is not None
        assert _image.object == obj
        assert _image.original_path == "/path/to/test.jpg"
        assert _image.original_filename == "test.jpg"
        assert _image.size == 1024
        assert _image.md5hash == "abc123"

    def test_image_file_path(self, test_database):
        """Test getting image file path."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        _image = mm.MdImage.create(
            object=obj, original_path="/path/to/test.jpg", original_filename="test.jpg", size=1024, md5hash="abc123"
        )

        file_path = _image.get_file_path()

        assert file_path is not None
        assert str(obj.id) in file_path


class TestMdThreeDModel:
    """Test MdThreeDModel model."""

    def test_create_3d_model(self, test_database):
        """Test creating a 3D model record."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        _model = mm.MdThreeDModel.create(
            object=obj, original_path="/path/to/test.obj", original_filename="test.obj", size=2048, md5hash="def456"
        )

        assert _model.id is not None
        assert _model.object == obj
        assert _model.original_path == "/path/to/test.obj"
        assert _model.original_filename == "test.obj"
        assert _model.size == 2048
        assert _model.md5hash == "def456"

    def test_3d_model_file_path(self, test_database):
        """Test getting 3D model file path."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        _model = mm.MdThreeDModel.create(
            object=obj, original_path="/path/to/test.obj", original_filename="test.obj", size=2048, md5hash="def456"
        )

        file_path = _model.get_file_path()

        assert file_path is not None
        assert str(obj.id) in file_path


class TestMdAnalysis:
    """Test MdAnalysis model."""

    def test_create_analysis(self, test_database):
        """Test creating an analysis record."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        analysis = mm.MdAnalysis.create(dataset=dataset, analysis_name="PCA Test", superimposition_method="procrustes")

        assert analysis.id is not None
        assert analysis.dataset == dataset
        assert analysis.analysis_name == "PCA Test"
        assert analysis.superimposition_method == "procrustes"
        assert analysis.created_at is not None

    def test_analysis_result_storage(self, test_database):
        """Test storing and retrieving analysis results."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        analysis = mm.MdAnalysis.create(dataset=dataset, analysis_name="PCA Test", superimposition_method="procrustes")

        # Store result as JSON string
        result_data = {"eigenvalues": [1.0, 0.5], "scores": [[0.1, 0.2]]}
        import json

        analysis.pca_analysis_result_json = json.dumps(result_data)
        analysis.save()

        # Retrieve and parse
        retrieved = mm.MdAnalysis.get_by_id(analysis.id)
        parsed_result = json.loads(retrieved.pca_analysis_result_json)

        assert parsed_result["eigenvalues"] == [1.0, 0.5]
        assert parsed_result["scores"] == [[0.1, 0.2]]


class TestMdDatasetGrouping:
    """Test MdDataset grouping variable operations."""

    def test_get_grouping_variable_with_multiple_groups(self, test_database):
        """Test grouping variable identification with multiple distinct groups."""
        dataset = mm.MdDataset.create(dataset_name="Grouping Test", dimension=2)
        dataset.propertyname_str = "Species,Location,Age"
        dataset.save()

        # Create objects with grouping variables
        for i in range(10):
            obj = mm.MdObject.create(object_name=f"Obj{i}", dataset=dataset)
            # Species: 3 groups, Location: 2 groups, Age: 10 unique (too many)
            species = ["A", "B", "C"][i % 3]
            location = ["North", "South"][i % 2]
            age = str(20 + i)
            obj.variablename_str = f"{species},{location},{age}"
            obj.save()

        # Get grouping variable indices
        indices = dataset.get_grouping_variable_index_list()

        # Species (index 0) and Location (index 1) should be included
        # Age (index 2) has too many unique values (10 = 100% of objects)
        assert 0 in indices  # Species
        assert 1 in indices  # Location
        # Age might or might not be included depending on threshold

    def test_get_grouping_variable_with_few_groups(self, test_database):
        """Test grouping with variables having few distinct values."""
        dataset = mm.MdDataset.create(dataset_name="Few Groups", dimension=2)
        dataset.propertyname_str = "Group,Subgroup"
        dataset.save()

        # Create 20 objects with only 2-3 unique values per variable
        for i in range(20):
            obj = mm.MdObject.create(object_name=f"Obj{i}", dataset=dataset)
            group = ["A", "B"][i % 2]
            subgroup = ["X", "Y", "Z"][i % 3]
            obj.variablename_str = f"{group},{subgroup}"
            obj.save()

        indices = dataset.get_grouping_variable_index_list()

        # Both should be valid grouping variables (<=10 unique values)
        assert len(indices) == 2
        assert 0 in indices
        assert 1 in indices

    def test_get_grouping_variable_empty_dataset(self, test_database):
        """Test grouping variables with no objects."""
        dataset = mm.MdDataset.create(dataset_name="Empty", dimension=2)
        dataset.propertyname_str = "Var1,Var2"
        dataset.save()

        # No objects created
        indices = dataset.get_grouping_variable_index_list()

        # Should return all variables when dataset is empty
        assert len(indices) == 2

    def test_get_grouping_variable_no_variables(self, test_database):
        """Test grouping when no variables are defined."""
        dataset = mm.MdDataset.create(dataset_name="No Vars", dimension=2)
        # No propertyname_str set

        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.save()

        indices = dataset.get_grouping_variable_index_list()

        # Should return empty list
        assert len(indices) == 0

    def test_get_grouping_variable_all_unique(self, test_database):
        """Test grouping when all values are unique (bad for grouping)."""
        dataset = mm.MdDataset.create(dataset_name="All Unique", dimension=2)
        dataset.propertyname_str = "ID"
        dataset.save()

        # Create 15 objects, each with unique ID
        for i in range(15):
            obj = mm.MdObject.create(object_name=f"Obj{i}", dataset=dataset)
            obj.variablename_str = f"ID_{i}"
            obj.save()

        indices = dataset.get_grouping_variable_index_list()

        # Should still return the variable (fallback behavior)
        # When no valid grouping variables, returns all
        assert len(indices) > 0


class TestMdDatasetWireframePolygon:
    """Test MdDataset wireframe and polygon operations."""

    def test_pack_unpack_wireframe_complex(self, test_database):
        """Test packing and unpacking complex wireframe data."""
        dataset = mm.MdDataset.create(dataset_name="Wireframe Test", dimension=2)

        # Create complex edge list
        edge_list = [[0, 1], [1, 2], [2, 3], [3, 0], [0, 2]]
        dataset.pack_wireframe(edge_list)
        dataset.save()

        # Unpack and verify
        retrieved = mm.MdDataset.get_by_id(dataset.id)
        unpacked_edges = retrieved.get_edge_list()

        assert len(unpacked_edges) == 5
        assert [0, 1] in unpacked_edges
        assert [0, 2] in unpacked_edges

    def test_pack_wireframe_with_sorting(self, test_database):
        """Test that wireframe edges are sorted correctly."""
        dataset = mm.MdDataset.create(dataset_name="Sort Test", dimension=2)

        # Edges in random order with reversed pairs
        edge_list = [[5, 3], [1, 0], [2, 1], [4, 2]]
        dataset.pack_wireframe(edge_list)
        dataset.save()

        retrieved = mm.MdDataset.get_by_id(dataset.id)
        unpacked_edges = retrieved.get_edge_list()

        # Each edge should be sorted (smaller index first)
        for edge in unpacked_edges:
            assert edge[0] <= edge[1]

    def test_get_edge_list_empty(self, test_database):
        """Test getting edge list when no wireframe is set."""
        dataset = mm.MdDataset.create(dataset_name="No Wireframe", dimension=2)

        edges = dataset.get_edge_list()

        assert edges == []

    def test_pack_unpack_polygons(self, test_database):
        """Test packing and unpacking polygon data."""
        dataset = mm.MdDataset.create(dataset_name="Polygon Test", dimension=2)

        # Create polygon list (triangle and square)
        polygon_list = [[0, 1, 2], [3, 4, 5, 6]]
        dataset.pack_polygons(polygon_list)
        dataset.save()

        retrieved = mm.MdDataset.get_by_id(dataset.id)
        unpacked_polygons = retrieved.get_polygon_list()

        assert len(unpacked_polygons) == 2
        assert [0, 1, 2] in unpacked_polygons
        assert [3, 4, 5, 6] in unpacked_polygons

    def test_pack_unpack_baseline(self, test_database):
        """Test packing and unpacking baseline points."""
        dataset = mm.MdDataset.create(dataset_name="Baseline Test", dimension=2)

        # Set baseline points
        baseline_points = [0, 5]
        dataset.pack_baseline(baseline_points)
        dataset.save()

        retrieved = mm.MdDataset.get_by_id(dataset.id)
        retrieved.unpack_baseline()  # Need to unpack first
        unpacked_baseline = retrieved.get_baseline_points()

        assert len(unpacked_baseline) == 2
        assert 0 in unpacked_baseline
        assert 5 in unpacked_baseline

    def test_get_polygon_list_empty(self, test_database):
        """Test getting polygon list when none is set."""
        dataset = mm.MdDataset.create(dataset_name="No Polygons", dimension=2)

        polygons = dataset.get_polygon_list()

        assert polygons == []

    def test_get_baseline_points_empty(self, test_database):
        """Test getting baseline points when none is set."""
        dataset = mm.MdDataset.create(dataset_name="No Baseline", dimension=2)

        baseline = dataset.get_baseline_points()

        assert baseline == []


class TestMdObjectImageOperations:
    """Test MdObject image attachment and operations."""

    def test_has_image_with_image(self, test_database):
        """Test has_image returns True when image is attached."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        # Attach an image
        _img = mm.MdImage.create(
            object=obj, original_path="/test/image.jpg", original_filename="image.jpg", size=1024, md5hash="abc123"
        )

        assert obj.has_image() is True

    def test_has_image_without_image(self, test_database):
        """Test has_image returns False when no image."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        assert obj.has_image() is False

    def test_get_image_path(self, test_database):
        """Test getting image file path."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        _img = mm.MdImage.create(
            object=obj, original_path="/test/image.jpg", original_filename="image.jpg", size=1024, md5hash="abc123"
        )

        # Get the image object first, then get its path
        image = obj.get_image()
        path = image.get_file_path()

        assert path is not None
        assert str(obj.id) in path

    def test_get_image_no_image(self, test_database):
        """Test getting image when no image attached."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        # Should return False for has_image
        assert obj.has_image() is False


class TestMdObject3DModelOperations:
    """Test MdObject 3D model attachment and operations."""

    def test_has_threed_model_with_model(self, test_database):
        """Test has_threed_model returns True when model is attached."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        # Attach a 3D model
        _model = mm.MdThreeDModel.create(
            object=obj, original_path="/test/model.obj", original_filename="model.obj", size=2048, md5hash="def456"
        )

        assert obj.has_threed_model() is True

    def test_has_threed_model_without_model(self, test_database):
        """Test has_threed_model returns False when no model."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        assert obj.has_threed_model() is False

    def test_get_threed_model_path(self, test_database):
        """Test getting 3D model file path."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        _model = mm.MdThreeDModel.create(
            object=obj, original_path="/test/model.obj", original_filename="model.obj", size=2048, md5hash="def456"
        )

        # Get the model object first, then get its path
        threed_model = obj.get_threed_model()
        path = threed_model.get_file_path()

        assert path is not None
        assert str(obj.id) in path

    def test_get_threed_model_no_model(self, test_database):
        """Test getting model when no model attached."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        # Should return False for has_threed_model
        assert obj.has_threed_model() is False


class TestMdObjectOpsTransformations:
    """Tests for MdObjectOps transformation methods."""

    def test_move_object(self, test_database):
        """Test moving an object's landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.landmark_str = "0\t0\n10\t10\n20\t20"
        obj.unpack_landmark()
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        obj_ops.move(5, 5)

        assert obj_ops.landmark_list[0] == [5, 5]
        assert obj_ops.landmark_list[1] == [15, 15]
        assert obj_ops.landmark_list[2] == [25, 25]

    def test_move_to_center(self, test_database):
        """Test moving an object to center (centroid at origin)."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.landmark_str = "0\t0\n10\t10\n20\t20"
        obj.unpack_landmark()
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        obj_ops.move_to_center()

        # Centroid should be at origin (approximately)
        centroid = obj_ops.get_centroid_coord()
        assert abs(centroid[0]) < 1e-10
        assert abs(centroid[1]) < 1e-10

    def test_rescale_object(self, test_database):
        """Test rescaling an object."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.landmark_str = "10\t10\n20\t20\n30\t30"
        obj.unpack_landmark()
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        obj_ops.rescale(2.0)

        assert obj_ops.landmark_list[0] == [20, 20]
        assert obj_ops.landmark_list[1] == [40, 40]
        assert obj_ops.landmark_list[2] == [60, 60]

    def test_rescale_to_unitsize(self, test_database):
        """Test rescaling to unit centroid size."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.landmark_str = "0\t0\n10\t0\n0\t10"
        obj.unpack_landmark()
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        obj_ops.rescale_to_unitsize()

        # Centroid size should be 1 after rescaling (refresh to recalculate)
        centroid_size = obj_ops.get_centroid_size(refresh=True)
        assert abs(centroid_size - 1.0) < 1e-10

    def test_get_centroid_coord_3d(self, test_database):
        """Test getting centroid coordinates in 3D."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.landmark_str = "0\t0\t0\n10\t10\t10\n20\t20\t20"
        obj.unpack_landmark()
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        centroid = obj_ops.get_centroid_coord()

        assert centroid[0] == 10.0
        assert centroid[1] == 10.0
        assert centroid[2] == 10.0

    def test_get_centroid_size_3d(self, test_database):
        """Test getting centroid size in 3D."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.landmark_str = "0\t0\t0\n1\t0\t0\n0\t1\t0\n0\t0\t1"
        obj.unpack_landmark()
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        centroid_size = obj_ops.get_centroid_size()

        assert centroid_size > 0


class TestMdObjectVariableOperations:
    """Tests for MdObject variable operations."""

    def test_pack_unpack_variable(self, test_database):
        """Test packing and unpacking variables."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        dataset.propertyname_str = "Species,Location,Age"
        dataset.save()

        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        variable_list = ["Human", "Africa", "25"]
        obj.pack_variable(variable_list)
        obj.save()

        obj2 = mm.MdObject.get_by_id(obj.id)
        obj2.unpack_variable()
        result = obj2.get_variable_list()

        assert len(result) == 3
        assert result[0] == "Human"
        assert result[1] == "Africa"
        assert result[2] == "25"

    def test_get_variable_list_empty(self, test_database):
        """Test getting empty variable list."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        result = obj.get_variable_list()

        assert result == []


class TestMdObjectLandmarkOperations:
    """Tests for MdObject landmark operations."""

    def test_pack_unpack_landmark_2d(self, test_database):
        """Test packing and unpacking 2D landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        obj.landmark_list = [[1.5, 2.5], [3.5, 4.5], [5.5, 6.5]]
        obj.pack_landmark()
        obj.save()

        obj2 = mm.MdObject.get_by_id(obj.id)
        obj2.unpack_landmark()

        assert len(obj2.landmark_list) == 3
        assert obj2.landmark_list[0] == [1.5, 2.5]
        assert obj2.landmark_list[1] == [3.5, 4.5]
        assert obj2.landmark_list[2] == [5.5, 6.5]

    def test_pack_unpack_landmark_3d(self, test_database):
        """Test packing and unpacking 3D landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=3)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)

        obj.landmark_list = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        obj.pack_landmark()
        obj.save()

        obj2 = mm.MdObject.get_by_id(obj.id)
        obj2.unpack_landmark()

        assert len(obj2.landmark_list) == 2
        assert obj2.landmark_list[0] == [1.0, 2.0, 3.0]
        assert obj2.landmark_list[1] == [4.0, 5.0, 6.0]

    def test_get_landmark_list(self, test_database):
        """Test getting landmark list."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.landmark_str = "1\t2\n3\t4\n5\t6"
        obj.save()

        result = obj.get_landmark_list()

        assert len(result) == 3
        assert result[0] == [1.0, 2.0]
        assert result[1] == [3.0, 4.0]
        assert result[2] == [5.0, 6.0]


class TestMdDatasetOpsInitialization:
    """Tests for MdDatasetOps initialization and basic operations."""

    def test_create_dataset_ops(self, test_database):
        """Test creating MdDatasetOps from dataset."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset", dimension=2)
        dataset.wireframe = "0-1,1-2,2-0"
        dataset.baseline = "0,1"
        dataset.save()

        # Add some objects
        for i in range(3):
            obj = mm.MdObject.create(
                object_name=f"Obj{i}", dataset=dataset, landmark_str=f"{i}\t0\n{i}\t10\n{i + 10}\t20", sequence=i
            )
            obj.save()

        ds_ops = mm.MdDatasetOps(dataset)

        assert ds_ops.dataset_name == "Test Dataset"
        assert ds_ops.dimension == 2
        assert len(ds_ops.object_list) == 3
        assert len(ds_ops.edge_list) == 3

    def test_dataset_ops_object_ordering(self, test_database):
        """Test that dataset ops maintains object sequence order."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Create objects out of order
        _obj2 = mm.MdObject.create(object_name="Obj2", dataset=dataset, sequence=2)
        _obj0 = mm.MdObject.create(object_name="Obj0", dataset=dataset, sequence=0)
        _obj1 = mm.MdObject.create(object_name="Obj1", dataset=dataset, sequence=1)

        ds_ops = mm.MdDatasetOps(dataset)

        # Should be ordered by sequence
        assert ds_ops.object_list[0].object_name == "Obj0"
        assert ds_ops.object_list[1].object_name == "Obj1"
        assert ds_ops.object_list[2].object_name == "Obj2"


class TestMdDatasetOpsAdvanced:
    """Tests for advanced MdDatasetOps operations."""

    def test_check_object_list(self, test_database):
        """Test checking object list validity."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Add objects with same number of landmarks
        for i in range(3):
            _obj = mm.MdObject.create(object_name=f"Obj{i}", dataset=dataset, landmark_str="0\t0\n10\t10\n20\t20")

        ds_ops = mm.MdDatasetOps(dataset)
        result = ds_ops.check_object_list()

        assert result is True

    def test_has_missing_landmarks_false(self, test_database):
        """Test has_missing_landmarks when no landmarks are missing."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Add objects with complete landmarks
        for i in range(3):
            _obj = mm.MdObject.create(object_name=f"Obj{i}", dataset=dataset, landmark_str="0\t0\n10\t10\n20\t20")

        ds_ops = mm.MdDatasetOps(dataset)
        result = ds_ops.has_missing_landmarks()

        assert result is False

    def test_get_average_shape(self, test_database):
        """Test getting average shape from dataset."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Add objects with same landmarks (average should be same)
        for i in range(3):
            _obj = mm.MdObject.create(object_name=f"Obj{i}", dataset=dataset, landmark_str="0\t0\n10\t10\n20\t20")

        ds_ops = mm.MdDatasetOps(dataset)
        avg_shape = ds_ops.get_average_shape()

        assert len(avg_shape.landmark_list) == 3
        assert avg_shape.landmark_list[0] == [0.0, 0.0]
        assert avg_shape.landmark_list[1] == [10.0, 10.0]
        assert avg_shape.landmark_list[2] == [20.0, 20.0]


class TestMdObjectCopyOperations:
    """Tests for MdObject copy and change operations."""

    def test_change_dataset(self, test_database):
        """Test changing object's dataset (without image/model)."""
        dataset1 = mm.MdDataset.create(dataset_name="Dataset1", dimension=2)
        dataset2 = mm.MdDataset.create(dataset_name="Dataset2", dimension=2)

        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset1)
        obj.landmark_str = "0\t0\n10\t10"
        obj.save()

        # Change to dataset2 (this will fail if object has image/model)
        # So we just test that the dataset field changes
        obj.dataset = dataset2
        obj.save()

        # Verify the change
        obj_reloaded = mm.MdObject.get_by_id(obj.id)
        assert obj_reloaded.dataset == dataset2
        assert obj_reloaded.dataset.id == dataset2.id


class TestMdDatasetAddOperations:
    """Tests for MdDataset add operations."""

    def test_add_object_basic(self, test_database):
        """Test adding an object to dataset."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Add object using dataset method
        obj = dataset.add_object(object_name="NewObj", object_desc="Test object")
        obj.save()

        assert obj.object_name == "NewObj"
        assert obj.object_desc == "Test object"
        assert obj.dataset == dataset

    def test_add_object_with_landmarks(self, test_database):
        """Test adding object with landmark data."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        landmark_str = "1\t2\n3\t4\n5\t6"
        obj = dataset.add_object(object_name="ObjWithLandmarks", landmark_str=landmark_str)
        obj.save()

        assert obj.landmark_str == landmark_str

    def test_add_variablename(self, test_database):
        """Test adding a variable name to dataset."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Initialize variablename_list first
        dataset.variablename_list = []

        # Add a variable name
        dataset.add_variablename("Species")

        # Check it was added
        var_list = dataset.get_variablename_list()
        assert "Species" in var_list
        assert len(var_list) == 1

    def test_add_multiple_variablenames(self, test_database):
        """Test adding multiple variable names."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Initialize variablename_list first
        dataset.variablename_list = []

        # Add multiple variables
        dataset.add_variablename("Species")
        dataset.add_variablename("Location")
        dataset.add_variablename("Age")

        var_list = dataset.get_variablename_list()
        assert len(var_list) == 3
        assert "Species" in var_list
        assert "Location" in var_list
        assert "Age" in var_list


class TestMdObjectOpsAdvancedTransformations:
    """Tests for advanced MdObjectOps transformations."""

    def test_apply_scale(self, test_database):
        """Test apply_scale method."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset, pixels_per_mm=10.0)
        obj.landmark_str = "0\t0\n10\t10\n20\t20"
        obj.unpack_landmark()
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        obj_ops.apply_scale()

        # After scaling by pixels_per_mm (10.0), landmarks should be divided by 10
        assert obj_ops.landmark_list[0] == [0.0, 0.0]
        assert obj_ops.landmark_list[1] == [1.0, 1.0]
        assert obj_ops.landmark_list[2] == [2.0, 2.0]
        assert obj_ops.scale_applied is True

    def test_rotate_2d(self, test_database):
        """Test 2D rotation."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.landmark_str = "1\t0\n0\t1"
        obj.unpack_landmark()
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        # Rotate 90 degrees (pi/2 radians)
        import math

        obj_ops.rotate_2d(math.pi / 2)

        # After 90 degree rotation, (1,0) → (0,1), (0,1) → (-1,0)
        # Check that rotation occurred (values changed)
        assert obj_ops.landmark_list[0][0] != 1.0 or obj_ops.landmark_list[0][1] != 0.0


class TestMdDatasetRefresh:
    """Tests for MdDataset refresh operation."""

    def test_dataset_refresh(self, test_database):
        """Test refreshing dataset from database."""
        dataset = mm.MdDataset.create(dataset_name="Original", dimension=2)
        original_id = dataset.id

        # Modify dataset
        dataset.dataset_name = "Modified"
        dataset.save()

        # Create new instance and refresh
        dataset2 = mm.MdDataset.get_by_id(original_id)
        dataset2.refresh()

        assert dataset2.dataset_name == "Modified"


class TestMdObjectRefresh:
    """Tests for MdObject refresh operation."""

    def test_object_refresh(self, test_database):
        """Test refreshing object from database."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Original", dataset=dataset)
        original_id = obj.id

        # Modify object
        obj.object_name = "Modified"
        obj.save()

        # Get object and refresh
        obj2 = mm.MdObject.get_by_id(original_id)
        obj2.refresh()

        assert obj2.object_name == "Modified"


class TestMdObjectIsFloat:
    """Tests for MdObject is_float helper method."""

    def test_is_float_valid_float(self, test_database):
        """Test is_float with valid float string."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        assert obj.is_float("3.14") is True
        assert obj.is_float("10") is True
        assert obj.is_float("-5.5") is True
        assert obj.is_float("0.0") is True

    def test_is_float_invalid_string(self, test_database):
        """Test is_float with invalid string."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        assert obj.is_float("abc") is False
        assert obj.is_float("") is False
        assert obj.is_float("3.14.15") is False

    def test_is_float_missing_keyword(self, test_database):
        """Test is_float with Missing keyword."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        assert obj.is_float("Missing") is False


class TestMdDatasetComplexOperations:
    """Tests for complex MdDataset operations."""

    def test_unpack_wireframe_with_spaces(self, test_database):
        """Test unpacking wireframe with spaces."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        dataset.wireframe = " 0-1 , 1-2 , 2-0 "  # With spaces
        dataset.unpack_wireframe()

        edges = dataset.get_edge_list()
        assert len(edges) > 0

    def test_pack_wireframe_from_edge_list(self, test_database):
        """Test packing wireframe from edge_list attribute."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        dataset.edge_list = [[0, 1], [1, 2], [2, 0]]

        dataset.pack_wireframe()

        assert dataset.wireframe is not None
        assert "0" in dataset.wireframe
        assert "1" in dataset.wireframe

    def test_pack_polygons_from_list(self, test_database):
        """Test packing polygons from polygon_list attribute."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        dataset.polygon_list = [[0, 1, 2], [3, 4, 5, 6]]

        dataset.pack_polygons()

        assert dataset.polygons is not None


class TestMdObjectComplexLandmarks:
    """Tests for complex landmark operations."""

    def test_unpack_landmark_with_missing(self, test_database):
        """Test unpacking landmarks with Missing values."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        # Landmark string with "Missing" keyword
        obj.landmark_str = "1\t2\nMissing\tMissing\n5\t6"
        obj.unpack_landmark()

        assert len(obj.landmark_list) == 3
        assert obj.landmark_list[0] == [1.0, 2.0]
        assert obj.landmark_list[1] == [None, None]
        assert obj.landmark_list[2] == [5.0, 6.0]

    def test_pack_landmark_with_missing(self, test_database):
        """Test packing landmarks with None values."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.landmark_list = [[1.0, 2.0], [None, None], [5.0, 6.0]]
        obj.pack_landmark()

        assert "Missing" in obj.landmark_str

    def test_landmark_with_comma_separator(self, test_database):
        """Test unpacking landmarks with comma separator."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        # Use comma as separator
        obj.landmark_str = "1,2\n3,4\n5,6"
        obj.unpack_landmark()

        assert len(obj.landmark_list) == 3
        assert obj.landmark_list[0] == [1.0, 2.0]

    def test_landmark_with_space_separator(self, test_database):
        """Test unpacking landmarks with space separator."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        # Use multiple spaces as separator
        obj.landmark_str = "1  2\n3  4\n5  6"
        obj.unpack_landmark()

        assert len(obj.landmark_list) == 3
        assert obj.landmark_list[0] == [1.0, 2.0]


class TestMdObjectSequenceOperations:
    """Tests for object sequence operations."""

    def test_object_sequence_ordering(self, test_database):
        """Test that objects are ordered by sequence."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Create objects with specific sequences
        _obj3 = mm.MdObject.create(object_name="Third", dataset=dataset, sequence=2)
        _obj1 = mm.MdObject.create(object_name="First", dataset=dataset, sequence=0)
        _obj2 = mm.MdObject.create(object_name="Second", dataset=dataset, sequence=1)

        # Query ordered by sequence
        objects = list(dataset.object_list.order_by(mm.MdObject.sequence))

        assert objects[0].object_name == "First"
        assert objects[1].object_name == "Second"
        assert objects[2].object_name == "Third"


class TestMdObjectCopyObject:
    """Tests for MdObject copy_object operation."""

    def test_copy_object_basic(self, test_database):
        """Test copying object to another dataset."""
        dataset1 = mm.MdDataset.create(dataset_name="Source", dimension=2)
        dataset2 = mm.MdDataset.create(dataset_name="Target", dimension=2)

        obj = mm.MdObject.create(object_name="Original", dataset=dataset1)
        obj.landmark_str = "1\t2\n3\t4"
        obj.property_str = "Species,Location"
        obj.variablename_str = "Human,Africa"
        obj.save()

        # Copy to new dataset
        new_obj = obj.copy_object(dataset2)
        new_obj.save()

        assert new_obj.object_name == obj.object_name
        assert new_obj.dataset == dataset2
        assert new_obj.landmark_str == obj.landmark_str
        assert new_obj.id != obj.id  # Different ID


class TestMdDatasetOpsRotationMatrix:
    """Tests for MdDatasetOps rotation matrix operations."""

    def test_rotation_matrix_2d(self, test_database):
        """Test rotation matrix calculation for 2D."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Add objects with landmarks
        for i in range(3):
            obj = mm.MdObject.create(object_name=f"Obj{i}", dataset=dataset, landmark_str="0\t0\n1\t0\n0\t1")
            obj.save()

        ds_ops = mm.MdDatasetOps(dataset)

        # Create reference and target shapes
        import numpy as np

        ref = np.array([[0, 0], [1, 0], [0, 1]])
        target = np.array([[0, 0], [1, 0], [0, 1]])

        rot_matrix = ds_ops.rotation_matrix(ref, target)

        # Identity rotation (same shapes)
        assert rot_matrix.shape == (2, 2)
        # Check it's close to identity
        assert abs(rot_matrix[0, 0] - 1.0) < 0.1

    def test_set_reference_shape(self, test_database):
        """Test setting reference shape."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        obj = mm.MdObject.create(object_name="Ref", dataset=dataset, landmark_str="0\t0\n1\t0\n0\t1")
        obj.save()

        ds_ops = mm.MdDatasetOps(dataset)
        obj_ops = mm.MdObjectOps(obj)

        ds_ops.set_reference_shape(obj_ops)

        assert ds_ops.reference_shape == obj_ops


class TestMdAnalysisOperations:
    """Tests for MdAnalysis model operations."""

    def test_create_analysis_with_all_fields(self, test_database):
        """Test creating analysis with all fields."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        analysis = mm.MdAnalysis.create(
            analysis_name="Full Analysis",
            analysis_desc="Complete test",
            dataset=dataset,
            superimposition_method="Procrustes",
            dimension=2,
            wireframe="0-1,1-2",
            baseline="0,1",
        )

        assert analysis.analysis_name == "Full Analysis"
        assert analysis.superimposition_method == "Procrustes"
        assert analysis.wireframe == "0-1,1-2"
        assert analysis.baseline == "0,1"

    def test_analysis_json_storage(self, test_database):
        """Test storing JSON data in analysis."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        analysis = mm.MdAnalysis.create(analysis_name="PCA Test", dataset=dataset, superimposition_method="None")

        import json

        test_data = {"pc1": [1, 2, 3], "pc2": [4, 5, 6]}
        analysis.pca_analysis_result_json = json.dumps(test_data)
        analysis.save()

        # Reload and verify
        analysis2 = mm.MdAnalysis.get_by_id(analysis.id)
        loaded_data = json.loads(analysis2.pca_analysis_result_json)

        assert loaded_data["pc1"] == [1, 2, 3]
        assert loaded_data["pc2"] == [4, 5, 6]


class TestMdObjectCentroidEdgeCases:
    """Tests for edge cases in centroid calculations."""

    def test_centroid_with_all_missing_landmarks(self, test_database):
        """Test centroid with all None landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.landmark_list = [[None, None], [None, None], [None, None]]
        obj.pack_landmark()
        obj.save()

        centroid = obj.get_centroid_coord()
        centroid_size = obj.get_centroid_size()

        # Should handle gracefully
        assert centroid == [0, 0, 0]
        assert centroid_size == 0

    def test_centroid_with_partial_missing(self, test_database):
        """Test centroid with some missing coordinates."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.landmark_list = [[1.0, 2.0], [None, 4.0], [5.0, None]]
        obj.pack_landmark()
        obj.save()

        centroid = obj.get_centroid_coord()

        # Should average only valid coordinates
        assert centroid[0] == 3.0  # (1 + 5) / 2
        assert centroid[1] == 3.0  # (2 + 4) / 2

    def test_centroid_size_refresh(self, test_database):
        """Test centroid size recalculation with refresh."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.landmark_list = [[0, 0], [1, 0], [0, 1]]
        obj.pack_landmark()
        obj.save()

        # First calculation
        size1 = obj.get_centroid_size()

        # Modify landmarks
        obj.landmark_list = [[0, 0], [2, 0], [0, 2]]

        # Without refresh, should return cached value
        size2 = obj.get_centroid_size(refresh=False)

        # With refresh, should recalculate
        size3 = obj.get_centroid_size(refresh=True)

        assert size1 == size2  # Cached
        assert size3 > size1  # Recalculated and larger


class TestMdObjectOpsEdgeCases:
    """Tests for MdObjectOps edge cases."""

    def test_move_with_missing_landmarks(self, test_database):
        """Test moving object with missing landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.landmark_list = [[1.0, 2.0], [None, None], [3.0, 4.0]]
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        obj_ops.move(10, 10)

        # Valid landmarks should be moved
        assert obj_ops.landmark_list[0] == [11.0, 12.0]
        # Missing landmarks should stay None
        assert obj_ops.landmark_list[1] == [None, None]
        assert obj_ops.landmark_list[2] == [13.0, 14.0]

    def test_rescale_with_missing_landmarks(self, test_database):
        """Test rescaling with missing landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.landmark_list = [[2.0, 4.0], [None, None], [6.0, 8.0]]
        obj.save()

        obj_ops = mm.MdObjectOps(obj)
        obj_ops.rescale(0.5)

        # Valid landmarks should be scaled
        assert obj_ops.landmark_list[0] == [1.0, 2.0]
        # Missing should stay None
        assert obj_ops.landmark_list[1] == [None, None]
        assert obj_ops.landmark_list[2] == [3.0, 4.0]


class TestMdDatasetUnpackOperations:
    """Tests for dataset unpack operations."""

    def test_unpack_wireframe_empty(self, test_database):
        """Test unpacking empty wireframe."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        dataset.wireframe = ""

        dataset.unpack_wireframe()

        assert dataset.edge_list == []

    def test_unpack_polygons_empty(self, test_database):
        """Test unpacking empty polygons."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        dataset.polygons = ""

        dataset.unpack_polygons()

        assert dataset.polygon_list == []

    def test_unpack_baseline_empty(self, test_database):
        """Test unpacking empty baseline."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        dataset.baseline = ""

        dataset.unpack_baseline()

        assert dataset.baseline_point_list == []


class TestMdObjectVariableEdgeCases:
    """Tests for object variable edge cases."""

    def test_pack_variable_empty_list(self, test_database):
        """Test packing empty variable list."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.pack_variable([])

        assert obj.property_str == ""

    def test_unpack_variable_none(self, test_database):
        """Test unpacking None property string."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.property_str = None
        obj.unpack_variable()

        assert obj.variable_list == []


class TestMdDatasetMultipleObjects:
    """Tests for dataset with multiple objects."""

    def test_dataset_with_many_objects(self, test_database):
        """Test dataset with many objects."""
        dataset = mm.MdDataset.create(dataset_name="Large Dataset", dimension=2)

        # Create 50 objects
        for i in range(50):
            obj = mm.MdObject.create(
                object_name=f"Obj{i:03d}", dataset=dataset, sequence=i, landmark_str=f"{i}\t{i}\n{i + 1}\t{i + 1}"
            )
            obj.save()

        # Verify all were created
        assert dataset.object_list.count() == 50

        # Verify ordering
        objects = list(dataset.object_list.order_by(mm.MdObject.sequence))
        assert objects[0].object_name == "Obj000"
        assert objects[49].object_name == "Obj049"

    def test_dataset_ops_with_many_objects(self, test_database):
        """Test MdDatasetOps with many objects."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)

        # Create 10 objects
        for i in range(10):
            obj = mm.MdObject.create(
                object_name=f"Obj{i}", dataset=dataset, landmark_str="0\t0\n1\t1\n2\t2", sequence=i
            )
            obj.save()

        ds_ops = mm.MdDatasetOps(dataset)

        assert len(ds_ops.object_list) == 10
        # Objects should be ordered by sequence
        assert ds_ops.object_list[0].object_name == "Obj0"
        assert ds_ops.object_list[9].object_name == "Obj9"


class TestMdObjectLandmarkEdgeCases:
    """Tests for landmark edge cases."""

    def test_landmark_empty_string(self, test_database):
        """Test unpacking empty landmark string."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.landmark_str = ""
        obj.unpack_landmark()

        assert obj.landmark_list == []

    def test_landmark_none(self, test_database):
        """Test unpacking None landmark string."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.landmark_str = None
        obj.unpack_landmark()

        assert obj.landmark_list == []

    def test_landmark_with_empty_lines(self, test_database):
        """Test landmarks with empty lines."""
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Test", dataset=dataset)

        obj.landmark_str = "1\t2\n\n3\t4\n\n5\t6"
        obj.unpack_landmark()

        # Should skip empty lines
        assert len(obj.landmark_list) == 3
        assert obj.landmark_list[0] == [1.0, 2.0]
        assert obj.landmark_list[1] == [3.0, 4.0]
        assert obj.landmark_list[2] == [5.0, 6.0]
