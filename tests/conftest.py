"""Pytest configuration and shared fixtures."""
import sys
import os
import pytest
import tempfile
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_tps_data():
    """Provide sample TPS format data."""
    return """LM=3
1.0 2.0
3.0 4.0
5.0 6.0
ID=specimen_001
"""


@pytest.fixture
def sample_nts_data():
    """Provide sample NTS format data."""
    return """1  3  2  0  DIM=2
specimen_001
1.0 2.0
3.0 4.0
5.0 6.0
"""


@pytest.fixture(scope="session")
def qt_app():
    """Create a QApplication for Qt tests."""
    from PyQt5.QtWidgets import QApplication
    from unittest.mock import Mock
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Setup mock settings for all tests
    if not hasattr(app, 'settings'):
        from PyQt5.QtCore import QRect
        
        def mock_settings_value(key, default=None):
            if "Geometry" in key:
                return QRect(100, 100, 600, 400)
            if "RememberGeometry" in key:
                return True
            if "LandmarkSize" in key:
                return 10
            if "width_scale" in key:
                return 1.0
            if "dataset_mode" in key:
                return 0
            return default if default is not None else True
        
        app.settings = Mock()
        app.settings.value = Mock(side_effect=mock_settings_value)
        app.settings.setValue = Mock()
        app.settings.sync = Mock()
    
    yield app
    # Don't quit the app here as it might be reused


@pytest.fixture(scope='session')
def qapp():
    """Global Qt Application fixture for pytest-qt."""
    from PyQt5.QtWidgets import QApplication
    from unittest.mock import Mock
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Setup mock settings for all tests
    if not hasattr(app, 'settings'):
        from PyQt5.QtCore import QRect
        
        def mock_settings_value(key, default=None):
            if "Geometry" in key:
                return QRect(100, 100, 600, 400)
            if "RememberGeometry" in key:
                return True
            if "LandmarkSize" in key:
                return 10
            if "width_scale" in key:
                return 1.0
            if "dataset_mode" in key:
                return 0
            return default if default is not None else True
        
        app.settings = Mock()
        app.settings.value = Mock(side_effect=mock_settings_value)
        app.settings.setValue = Mock()
        app.settings.sync = Mock()
    
    yield app


@pytest.fixture
def temp_db(tmp_path):
    """Temporary database for testing."""
    db_path = tmp_path / "test_modan.db"
    return str(db_path)


@pytest.fixture
def mock_database(monkeypatch, temp_db):
    """Mock database operations."""
    import MdModel
    from peewee import SqliteDatabase
    
    # Create test database
    test_db = SqliteDatabase(temp_db, pragmas={'foreign_keys': 1})
    
    # Store original database
    original_db = MdModel.gDatabase
    
    # Set test database
    monkeypatch.setattr(MdModel, 'gDatabase', test_db)
    
    # Update all model classes to use test database
    models = [MdModel.MdDataset, MdModel.MdObject, MdModel.MdImage, 
              MdModel.MdThreeDModel, MdModel.MdAnalysis]
    for model in models:
        model._meta.database = test_db
    
    # Create tables
    test_db.connect()
    test_db.create_tables(models, safe=True)
    
    yield temp_db
    
    # Cleanup
    test_db.close()
    
    # Restore original database
    monkeypatch.setattr(MdModel, 'gDatabase', original_db)
    for model in models:
        model._meta.database = original_db


@pytest.fixture
def main_window(qtbot, mock_database):
    """Main window fixture with mocked database."""
    from Modan2 import ModanMainWindow
    
    # Create test config
    test_config = {
        "language": "en",
        "ui": {
            "toolbar_icon_size": "Medium",
            "remember_geometry": False,
            "window_geometry": [100, 100, 1400, 800],
            "is_maximized": False
        }
    }
    
    # Create window with config
    window = ModanMainWindow(test_config)
    qtbot.addWidget(window)
    
    # Show window
    window.show()
    qtbot.waitForWindowShown(window)
    
    yield window
    
    # Cleanup
    window.close()


@pytest.fixture
def sample_dataset(mock_database):
    """Create a sample dataset for testing."""
    import MdModel
    
    dataset = MdModel.MdDataset.create(
        dataset_name="Test Dataset",
        dataset_desc="Dataset for testing",
        dimension=2,
        landmark_count=10,
        object_name="Test Object",
        object_desc="Test Description"
    )
    
    return dataset


@pytest.fixture
def sample_tps_file(tmp_path, sample_tps_data):
    """Create a temporary TPS file."""
    tps_path = tmp_path / "test.tps"
    tps_path.write_text(sample_tps_data)
    return str(tps_path)


@pytest.fixture
def sample_nts_file(tmp_path, sample_nts_data):
    """Create a temporary NTS file."""
    nts_path = tmp_path / "test.nts"
    nts_path.write_text(sample_nts_data)
    return str(nts_path)


@pytest.fixture
def controller(mock_database):
    """Create a ModanController instance for testing."""
    from ModanController import ModanController
    return ModanController()


@pytest.fixture  
def controller_with_data(controller, sample_dataset):
    """Controller with sample dataset loaded."""
    import MdModel
    
    # Add objects with landmarks to the dataset
    for i in range(5):  # Create 5 objects for analysis
        obj = MdModel.MdObject.create(
            dataset=sample_dataset,
            object_name=f"Object_{i+1}",
            sequence=i+1
        )
        # Add sample landmark data (5 landmarks with x,y coordinates)
        landmark_str = "\n".join([f"{i+j}.0\t{i+j+1}.0" for j in range(5)])
        obj.landmark_str = landmark_str
        obj.save()
    
    controller.set_current_dataset(sample_dataset)
    return controller