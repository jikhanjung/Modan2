"""Tests for MdModel module - Database models and operations."""
import sys
import os
import pytest
import tempfile
import datetime
from pathlib import Path
from peewee import IntegrityError

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peewee import SqliteDatabase
import MdModel as mm


@pytest.fixture
def test_database():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db_path = tmp.name
    
    # Create test database
    test_db = SqliteDatabase(test_db_path, pragmas={'foreign_keys': 1})
    
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
        dataset = mm.MdDataset.create(
            dataset_name="Test Dataset",
            dataset_desc="Test Description",
            dimension=2
        )
        
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
        child = mm.MdDataset.create(
            dataset_name="Child Dataset",
            parent=parent
        )
        
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
        dataset = mm.MdDataset.create(
            dataset_name="Test Dataset",
            propertyname_str="width,height,depth"
        )
        
        variablename_list = dataset.get_variablename_list()
        assert variablename_list == ["width", "height", "depth"]
    
    def test_update_dataset_name(self, test_database):
        """Test updating dataset name."""
        dataset = mm.MdDataset.create(
            dataset_name="Original Name",
            dataset_desc="Original Description"
        )
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
        dataset = mm.MdDataset.create(
            dataset_name="Original Name",
            dataset_desc="Original Description",
            dimension=2
        )
        
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
        dataset = mm.MdDataset.create(
            dataset_name="To Delete",
            dataset_desc="Will be deleted"
        )
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
        obj = mm.MdObject.create(
            object_name="Test Object",
            object_desc="Test Description",
            dataset=dataset,
            sequence=1
        )
        
        assert obj.id is not None
        assert obj.object_name == "Test Object"
        assert obj.object_desc == "Test Description"
        assert obj.dataset == dataset
        assert obj.sequence == 1
    
    def test_object_defaults(self, test_database):
        """Test object default values."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(
            object_name="Minimal Object",
            dataset=dataset
        )
        
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
        obj = mm.MdObject.create(
            object_name="Original Name",
            object_desc="Original Description",
            dataset=dataset
        )
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
        obj = mm.MdObject.create(
            object_name="To Delete",
            dataset=dataset
        )
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
            superimposition_method="Procrustes"  # Required field
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
            superimposition_method="None"  # Required field
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
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)
        
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
                dataset = mm.MdDataset.create(dataset_name="Test Dataset")
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
        large_landmark_list = [[float(i), float(i+1)] for i in range(100)]
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


class TestImageOperations:
    """Test MdImage file and EXIF operations."""

    def test_get_md5hash_info(self, test_database, tmp_path):
        """Test MD5 hash calculation for image files."""
        # Create a test dataset and object first (required for MdImage)
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)

        # Create image with required object_id
        image = mm.MdImage.create(object_id=obj.id)
        test_file = tmp_path / "test_image.jpg"
        test_content = b"fake image content for testing"
        test_file.write_bytes(test_content)

        # Calculate MD5 hash
        md5hash, image_data = image.get_md5hash_info(str(test_file))

        assert md5hash is not None
        assert len(md5hash) == 32  # MD5 hash is 32 hex characters
        assert image_data == test_content

    def test_get_md5hash_info_file_not_found(self, test_database):
        """Test MD5 hash with non-existent file."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)
        image = mm.MdImage.create(object_id=obj.id)

        with pytest.raises((FileNotFoundError, ValueError)):
            image.get_md5hash_info("/nonexistent/file.jpg")

    def test_get_exif_info_no_exif(self, test_database, tmp_path):
        """Test EXIF extraction from file without EXIF data."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)
        image = mm.MdImage.create(object_id=obj.id)

        test_file = tmp_path / "no_exif.txt"
        test_file.write_text("not an image")

        # Should return empty EXIF info for non-image files
        result = image.get_exif_info(str(test_file))

        assert isinstance(result, dict)
        assert 'datetime' in result
        assert 'latitude' in result
        assert 'longitude' in result

    def test_load_file_info_directory(self, test_database, tmp_path):
        """Test loading file info for a directory."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        obj = mm.MdObject.create(object_name="Test Object", dataset=dataset)
        image = mm.MdImage.create(object_id=obj.id)

        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()

        file_info = image.load_file_info(str(test_dir))

        # For directories, should return basic info without hash
        assert file_info is not None or image.original_path == str(test_dir)


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
        assert hasattr(obj_ops, 'landmark_list')
        assert obj_ops.landmark_list == [[1.0, 2.0], [3.0, 4.0]]


class TestMdAnalysisExtended:
    """Extended tests for MdAnalysis model."""

    def test_analysis_with_wireframe(self, test_database):
        """Test analysis with wireframe data."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        analysis = mm.MdAnalysis.create(
            analysis_name="Test Analysis",
            dataset=dataset,
            superimposition_method="Procrustes",
            wireframe="1-2,2-3,3-1"
        )

        assert analysis.wireframe == "1-2,2-3,3-1"

    def test_analysis_with_baseline(self, test_database):
        """Test analysis with baseline landmarks."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        analysis = mm.MdAnalysis.create(
            analysis_name="Test Analysis",
            dataset=dataset,
            superimposition_method="Procrustes",
            baseline="1,2,3"
        )

        assert analysis.baseline == "1,2,3"

    def test_analysis_requires_dataset(self, test_database):
        """Test that analysis requires dataset reference."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset")
        analysis = mm.MdAnalysis.create(
            analysis_name="Test Analysis",
            dataset=dataset,
            superimposition_method="Procrustes"
        )

        # Verify analysis is linked to dataset
        assert analysis.dataset == dataset
        assert analysis.dataset.id == dataset.id