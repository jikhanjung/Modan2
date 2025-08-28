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
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app here as it might be reused