# Modan2 Developer Guide

**Version**: 0.1.5-alpha.1
**Last Updated**: 2025-10-06
**Target Audience**: Contributors and developers

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Structure](#project-structure)
4. [Coding Standards](#coding-standards)
5. [Testing](#testing)
6. [Common Tasks](#common-tasks)
7. [Performance Guidelines](#performance-guidelines)
8. [Debugging](#debugging)
9. [Contributing](#contributing)
10. [Appendix](#appendix)

## Getting Started

### Prerequisites

- **Python**: 3.12 or higher
- **OS**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **RAM**: Minimum 4GB, recommended 8GB
- **Disk**: 500MB for application + dependencies

### Quick Setup

```bash
# Clone repository
git clone <repository-url>
cd Modan2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r config/requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest

# Run application
python Modan2.py
```

### Linux/WSL Specific Setup

```bash
# Install Qt dependencies
sudo apt-get update
sudo apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xfixes0 \
  libxcb-shape0 libxcb-cursor0 qt5-qmake qtbase5-dev libqt5gui5 \
  libqt5core5a libqt5widgets5 python3-pyqt5

# Install OpenGL dependencies
sudo apt-get install -y libglut-dev libglut3.12 python3-opengl

# If Qt plugin errors occur, use fix script
python fix_qt_import.py
```

## Development Environment

### Recommended IDE

**Visual Studio Code** (with extensions):
- Python (Microsoft)
- Pylance
- Python Test Explorer
- Ruff (charliermarsh.ruff)
- Git Graph
- Better Comments

**PyCharm Professional**:
- Excellent PyQt5 integration
- Built-in database tools
- Integrated debugger

### Editor Configuration

**VS Code** (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "editor.formatOnSave": true,
  "editor.rulers": [120],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  }
}
```

### Git Configuration

```bash
# Set user info
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Enable pre-commit hooks
pre-commit install

# Useful aliases
git config alias.st status
git config alias.co checkout
git config alias.br branch
git config alias.ci commit
```

## Project Structure

### Directory Layout

```
Modan2/
├── Modan2.py              # Main application entry point
├── MdModel.py             # Database models (3,789 lines)
├── MdStatistics.py        # Statistical analysis (634 lines)
├── MdUtils.py             # Utilities (436 lines)
├── ModanController.py     # Controller (1,139 lines)
├── ModanComponents.py     # Custom widgets (4,354 lines)
├── ModanDialogs.py        # Legacy dialogs (2,900 lines)
│
├── dialogs/               # Extracted dialog modules
│   ├── __init__.py
│   ├── base_dialog.py            # Base class for all dialogs
│   ├── analysis_dialog.py        # New analysis dialog
│   ├── dataset_dialog.py         # Dataset creation/editing
│   ├── object_dialog.py          # Object creation/editing
│   ├── import_dialog.py          # Multi-format import
│   ├── export_dialog.py          # Multi-format export
│   ├── data_exploration_dialog.py    # Data visualization (2,637 lines)
│   ├── dataset_analysis_dialog.py    # Analysis management (1,354 lines)
│   └── [other dialogs...]
│
├── components/            # Reusable UI components (future)
│   └── __init__.py
│
├── tests/                 # Test suite (962 tests)
│   ├── conftest.py              # Pytest fixtures
│   ├── test_mdmodel.py          # Database tests (262 tests)
│   ├── test_mdstatistics.py     # Statistics tests
│   ├── test_controller.py       # Controller tests (92 tests)
│   └── dialogs/                 # Dialog tests (200+ tests)
│
├── scripts/               # Utility scripts
│   ├── benchmark_analysis.py    # Performance benchmarks
│   ├── profile_detailed.py      # Profiling tools
│   └── [other scripts...]
│
├── docs/                  # Documentation
│   ├── architecture.md          # Architecture overview
│   ├── performance.md           # Performance guide
│   ├── developer_guide.md       # This file
│   └── README.md
│
├── devlog/                # Development logs
│   ├── 20251006_110_phase4_week3_kickoff.md
│   ├── 20251006_113_optimization_results.md
│   └── [other logs...]
│
├── benchmarks/            # Performance benchmark results
│   ├── analysis_benchmarks.json
│   └── *.prof files
│
├── config/                # Configuration files
│   ├── pytest.ini
│   └── requirements-dev.txt
│
└── logs/                  # Application logs
    └── modan2.log
```

### Module Responsibilities

| Module | Purpose | Size | Coverage |
|--------|---------|------|----------|
| `MdModel.py` | Database ORM, operations | 3,789 | 70% ✅ |
| `MdStatistics.py` | Statistical analysis | 634 | 95% ✅ |
| `MdUtils.py` | File I/O, helpers | 436 | 78% ✅ |
| `ModanController.py` | Business logic | 1,139 | 70% ✅ |
| `Modan2.py` | Main window, UI | 1,765 | 40% |
| `ModanComponents.py` | Custom widgets | 4,354 | 26% |
| `dialogs/` | Dialog modules | 8,179 | 79% ✅ |

## Coding Standards

### Style Guide

**Base**: PEP 8 with project-specific adaptations

**Line Length**: 120 characters (configured in `pyproject.toml`)

**Enforced by**: Ruff (linter and formatter)

### Naming Conventions

```python
# Classes: PascalCase
class MdDataset:
    pass

class ObjectViewer2D:
    pass

# Functions and methods: snake_case
def do_pca_analysis():
    pass

def create_dataset():
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_DIMENSION = 2
MAX_LANDMARKS = 1000

# Private methods: _leading_underscore
def _create_widgets(self):
    pass

# Qt slots: camelCase (Qt convention)
def onActionTriggered(self):
    pass

# Qt widgets: Hungarian notation (optional)
self.btnOK = QPushButton("OK")
self.edtName = QLineEdit()
self.cbxMethod = QComboBox()
```

### Import Organization

```python
# 1. Standard library
import sys
import json
from pathlib import Path

# 2. Third-party packages
from PyQt5.QtWidgets import QDialog, QVBoxLayout
import numpy as np
import pandas as pd

# 3. Local imports
import MdModel as mm
from dialogs.base_dialog import BaseDialog
from MdUtils import read_tps_file
```

**Enforced by**: Ruff (isort integration)

### Docstring Style

**Format**: Google style

```python
def do_pca_analysis(landmarks_data, n_components=None):
    """Perform Principal Component Analysis on landmark data.

    This function performs PCA using numpy's SVD implementation,
    which is highly optimized and suitable for morphometric data.

    Args:
        landmarks_data: List of landmark arrays, shape (n_objects, n_landmarks, n_dims)
        n_components: Number of components to extract. If None, extracts all.

    Returns:
        dict: PCA results containing:
            - 'scores': PC scores, shape (n_objects, n_components)
            - 'loadings': PC loadings, shape (n_landmarks * n_dims, n_components)
            - 'variance': Variance explained by each component
            - 'variance_ratio': Proportion of variance explained

    Raises:
        ValueError: If landmarks_data is empty or has inconsistent shapes

    Example:
        >>> landmarks = [np.random.randn(10, 2) for _ in range(50)]
        >>> result = do_pca_analysis(landmarks, n_components=2)
        >>> print(result['variance_ratio'][:2])
        [0.45, 0.25]  # First two PCs explain 70% of variance
    """
    if not landmarks_data:
        raise ValueError("landmarks_data cannot be empty")

    # Implementation...
    return result
```

### Type Hints

**Encouraged** for new code (Python 3.12+ syntax):

```python
from collections.abc import Sequence

def calculate_centroid(landmarks: np.ndarray) -> np.ndarray:
    """Calculate centroid of landmarks."""
    return np.mean(landmarks, axis=0)

def get_dataset(dataset_id: int) -> MdDataset | None:
    """Get dataset by ID, or None if not found."""
    try:
        return MdDataset.get_by_id(dataset_id)
    except DoesNotExist:
        return None

def process_objects(objects: Sequence[MdObject]) -> list[dict]:
    """Process multiple objects and return results."""
    return [process_one(obj) for obj in objects]
```

### Code Quality Tools

#### Ruff (Linter + Formatter)

**Run manually**:
```bash
# Format code
ruff format .

# Check linting
ruff check .

# Auto-fix issues
ruff check --fix .
```

**Automatic**: Pre-commit hooks run on every commit

**Configuration**: `pyproject.toml`

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4"]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports OK
"tests/*" = ["S101"]      # Assert OK in tests
```

#### Pre-commit Hooks

**Configuration**: `.pre-commit-config.yaml`

**Hooks**:
- Ruff linting and formatting
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON validation
- Large file check (10MB limit)
- Merge conflict detection

**Run manually**:
```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

## Testing

### Test Framework

**Framework**: pytest with plugins:
- pytest-qt: Qt application testing
- pytest-cov: Coverage reporting
- pytest-mock: Mocking support
- pytest-benchmark: Performance testing

### Test Organization

```python
# tests/test_mdmodel.py

import pytest
import MdModel as mm

class TestMdDataset:
    """Tests for MdDataset model."""

    @pytest.fixture
    def dataset(self, mock_database):
        """Create a test dataset."""
        return mm.MdDataset.create(
            dataset_name="Test",
            dimension=2,
            landmark_count=10
        )

    def test_dataset_creation(self, dataset):
        """Test dataset can be created."""
        assert dataset.dataset_name == "Test"
        assert dataset.dimension == 2

    def test_dataset_validation(self):
        """Test dataset validation."""
        with pytest.raises(Exception):
            mm.MdDataset.create(
                dataset_name="",  # Empty name should fail
                dimension=2
            )
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Run specific file
pytest tests/test_mdmodel.py

# Run specific class
pytest tests/test_mdmodel.py::TestMdDataset

# Run specific test
pytest tests/test_mdmodel.py::TestMdDataset::test_dataset_creation

# Run verbose
pytest -v

# Show print statements
pytest -s

# Run only failed tests from last run
pytest --lf

# Run tests matching pattern
pytest -k "procrustes"
```

### Writing Tests

#### Unit Tests

```python
def test_calculate_centroid():
    """Test centroid calculation."""
    landmarks = np.array([[0, 0], [2, 2], [4, 4]])
    centroid = calculate_centroid(landmarks)
    expected = np.array([2, 2])
    np.testing.assert_array_almost_equal(centroid, expected)
```

#### Integration Tests

```python
def test_import_workflow(qtbot, mock_database):
    """Test complete import workflow."""
    # Create dialog
    dialog = ImportDialog()
    qtbot.addWidget(dialog)

    # Simulate user actions
    dialog.edtFilePath.setText("test.tps")
    dialog.edtDatasetName.setText("Imported")

    # Trigger import
    with qtbot.waitSignal(dialog.accepted, timeout=1000):
        dialog.btnOK.click()

    # Verify results
    dataset = mm.MdDataset.get(dataset_name="Imported")
    assert dataset is not None
    assert len(list(dataset.objects)) > 0
```

#### Performance Tests

```python
def test_procrustes_performance(benchmark):
    """Ensure Procrustes doesn't regress."""
    dataset = create_test_dataset(50, 20, 2)
    ds_ops = mm.MdDatasetOps(dataset)

    result = benchmark(ds_ops.procrustes_superimposition)

    assert result is True
    assert benchmark.stats.mean < 0.5  # Should be < 500ms
```

### Coverage Goals

| Module | Target | Current | Status |
|--------|--------|---------|--------|
| New features | 70%+ | - | 🎯 Target |
| MdModel.py | 70%+ | 70% | ✅ Met |
| MdStatistics.py | 90%+ | 95% | ✅ Exceeded |
| ModanController.py | 70%+ | 70% | ✅ Met |
| dialogs/ | 70%+ | 79% | ✅ Exceeded |
| Overall | 60%+ | 70%+ | ✅ Exceeded |

## Common Tasks

### Adding a New Dialog

**1. Create dialog file**:

```bash
# Create file
touch dialogs/my_new_dialog.py
```

```python
# dialogs/my_new_dialog.py

from PyQt5.QtWidgets import QVBoxLayout, QLabel
from dialogs.base_dialog import BaseDialog

class MyNewDialog(BaseDialog):
    """Dialog for new feature."""

    def __init__(self, parent=None):
        super().__init__(parent, title="My New Dialog")
        self._create_widgets()
        self._create_layout()
        self._connect_signals()

    def _create_widgets(self):
        """Create UI widgets."""
        self.lblInfo = QLabel("Information goes here")

    def _create_layout(self):
        """Create layout."""
        layout = QVBoxLayout()
        layout.addWidget(self.lblInfo)
        layout.addWidget(self.create_button_box())
        self.setLayout(layout)

    def _connect_signals(self):
        """Connect signals and slots."""
        pass
```

**2. Register dialog**:

```python
# dialogs/__init__.py

from .my_new_dialog import MyNewDialog

__all__ = [
    # ... existing ...
    'MyNewDialog',
]
```

**3. Add tests**:

```python
# tests/dialogs/test_my_new_dialog.py

import pytest
from dialogs.my_new_dialog import MyNewDialog

class TestMyNewDialog:
    """Tests for MyNewDialog."""

    def test_dialog_creation(self, qtbot):
        """Test dialog can be created."""
        dialog = MyNewDialog()
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "My New Dialog"
```

**4. Use in main window**:

```python
# Modan2.py

from dialogs import MyNewDialog

def on_action_new_feature_triggered(self):
    """Handle new feature action."""
    dialog = MyNewDialog(self)
    if dialog.exec_() == QDialog.Accepted:
        # Handle result
        pass
```

### Adding a New Analysis Method

**1. Implement in MdStatistics.py**:

```python
# MdStatistics.py

def do_new_analysis(landmarks_data, parameter1=None, parameter2=None):
    """Perform new analysis method.

    Args:
        landmarks_data: List of landmark arrays
        parameter1: First parameter
        parameter2: Second parameter

    Returns:
        dict: Analysis results with keys:
            - 'result_data': Main results
            - 'statistics': Summary statistics
            - 'metadata': Analysis metadata
    """
    # Validate input
    if not landmarks_data:
        raise ValueError("landmarks_data cannot be empty")

    # Perform analysis
    # ... implementation ...

    return {
        'result_data': result,
        'statistics': stats,
        'metadata': {
            'method': 'new_analysis',
            'n_objects': len(landmarks_data),
            'parameters': {
                'parameter1': parameter1,
                'parameter2': parameter2,
            }
        }
    }
```

**2. Add to controller**:

```python
# ModanController.py

def run_analysis(self, dataset, analysis_method, **params):
    """Run analysis on dataset."""
    # ... existing code ...

    if analysis_method == "new_analysis":
        result = MdStatistics.do_new_analysis(
            landmarks_data,
            parameter1=params.get('parameter1'),
            parameter2=params.get('parameter2')
        )

    # ... save results ...
```

**3. Add UI in analysis dialog**:

```python
# dialogs/analysis_dialog.py

def _create_widgets(self):
    # ... existing ...
    self.cbxAnalysisMethod.addItem("New Analysis")
```

**4. Write tests**:

```python
# tests/test_mdstatistics.py

def test_new_analysis():
    """Test new analysis method."""
    landmarks = [np.random.randn(10, 2) for _ in range(50)]

    result = MdStatistics.do_new_analysis(
        landmarks,
        parameter1="value1",
        parameter2=42
    )

    assert 'result_data' in result
    assert 'statistics' in result
    assert result['metadata']['method'] == 'new_analysis'
```

### Adding a New File Format

**1. Implement reader in MdUtils.py**:

```python
# MdUtils.py

def read_new_format(file_path):
    """Read landmarks from new file format.

    Args:
        file_path: Path to file

    Returns:
        dict: Parsed data with keys:
            - 'landmarks': List of landmark arrays
            - 'object_names': List of object names
            - 'metadata': Format-specific metadata

    Raises:
        ValueError: If file format is invalid
    """
    with open(file_path, 'r') as f:
        content = f.read()

    # Parse file
    # ... implementation ...

    return {
        'landmarks': landmarks,
        'object_names': names,
        'metadata': metadata
    }
```

**2. Update import dialog**:

```python
# dialogs/import_dialog.py

def _get_import_data(self, file_path):
    """Get import data from file."""
    # ... existing formats ...

    if file_path.endswith('.new'):
        data = MdUtils.read_new_format(file_path)
        return data

    # ... rest of code ...
```

**3. Add tests**:

```python
# tests/test_mdutils.py

def test_read_new_format(tmp_path):
    """Test reading new file format."""
    # Create test file
    test_file = tmp_path / "test.new"
    test_file.write_text("test data")

    # Read file
    result = MdUtils.read_new_format(str(test_file))

    # Verify
    assert 'landmarks' in result
    assert len(result['landmarks']) > 0
```

### Database Migrations

**When schema changes**:

```python
# migrate.py

from peewee import *
from playhouse.migrate import *

migrator = SqliteMigrator(database)

# Add column
migrate(
    migrator.add_column('mddataset', 'new_column', CharField(null=True))
)

# Rename column
migrate(
    migrator.rename_column('mddataset', 'old_name', 'new_name')
)

# Drop column
migrate(
    migrator.drop_column('mddataset', 'unused_column')
)
```

**Run migration**:

```bash
python migrate.py
```

## Performance Guidelines

### Profiling

**Always profile before optimizing**:

```bash
# Run benchmarks
python scripts/benchmark_analysis.py

# Detailed profiling
python scripts/profile_detailed.py

# View results
snakeviz benchmarks/procrustes_profile.prof
```

### Optimization Tips

**1. Use Numpy vectorization**:

```python
# Bad - Python loop
for i in range(len(array)):
    result[i] = array[i] ** 2

# Good - Numpy
result = np.square(array)
```

**2. Batch database operations**:

```python
# Bad - Multiple queries
for obj_data in objects:
    MdObject.create(**obj_data)

# Good - Single batch insert
with mm.gDatabase.atomic():
    MdObject.insert_many(objects).execute()
```

**3. Cache expensive computations**:

```python
from functools import cached_property

class MdObject:
    @cached_property
    def centroid_size(self):
        """Cached centroid size calculation."""
        return np.sqrt(np.sum(np.square(self.landmarks)))
```

**4. Use generators for large datasets**:

```python
# Bad - Load all in memory
objects = list(MdObject.select())
for obj in objects:
    process(obj)

# Good - Stream
for obj in MdObject.select().iterator():
    process(obj)
```

### Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| Procrustes (50 obj) | <500ms | ✅ 315ms |
| PCA (50 obj) | <10ms | ✅ 2ms |
| Database query | <50ms | ✅ <20ms |
| Import TPS (50 obj) | <1s | ✅ 300ms |

## Debugging

### Logging

```python
# Use built-in logger
from MdLogger import setup_logger

logger = setup_logger(__name__)

# Log messages
logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

**Log file**: `logs/modan2.log`

### Qt Debugging

```python
# Enable Qt debug output
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'

# Print widget hierarchy
def print_widget_tree(widget, indent=0):
    """Print widget hierarchy for debugging."""
    print("  " * indent + f"{widget.__class__.__name__}: {widget.objectName()}")
    for child in widget.children():
        if isinstance(child, QWidget):
            print_widget_tree(child, indent + 1)
```

### Database Debugging

```python
# Enable SQL logging
import logging
logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Check database integrity
import sqlite3
conn = sqlite3.connect('modan.db')
cursor = conn.execute('PRAGMA integrity_check')
print(cursor.fetchall())
```

### Common Issues

**Qt Platform Plugin Error (Linux/WSL)**:
```bash
# Solution 1: Use fix script
python fix_qt_import.py

# Solution 2: Set environment variable
export QT_QPA_PLATFORM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt5/plugins/platforms
```

**OpenGL Errors**:
```bash
# Install GLUT libraries
sudo apt-get install -y libglut-dev libglut3.12 python3-opengl
```

**Database Locked**:
```python
# Ensure database is closed properly
mm.gDatabase.close()

# Or use atomic transactions
with mm.gDatabase.atomic():
    # ... operations ...
```

## Contributing

### Workflow

1. **Create feature branch**:
```bash
git checkout -b feature/my-new-feature
```

2. **Make changes**:
- Write code
- Add tests
- Update documentation

3. **Run quality checks**:
```bash
pytest
ruff check .
ruff format .
```

4. **Commit changes**:
```bash
git add .
git commit -m "feat: Add new feature description"
```

5. **Push and create PR**:
```bash
git push origin feature/my-new-feature
# Create pull request on GitHub
```

### Commit Message Format

**Format**: `<type>: <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat: Add CVA analysis method
fix: Resolve Procrustes convergence issue
docs: Update developer guide with testing section
perf: Optimize Procrustes convergence (77% faster)
test: Add integration tests for import workflow
refactor: Extract DatasetDialog from ModanDialogs
```

### Code Review Checklist

- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Code follows style guide (Ruff passing)
- [ ] No new warnings or errors
- [ ] Performance impact considered
- [ ] Breaking changes documented
- [ ] Commit messages are clear

## Appendix

### Useful Commands

```bash
# Development
pytest                              # Run tests
pytest --cov=. --cov-report=html   # Coverage report
ruff check .                        # Lint code
ruff format .                       # Format code
pre-commit run --all-files         # Run all hooks

# Performance
python scripts/benchmark_analysis.py    # Benchmarks
python scripts/profile_detailed.py      # Profiling
snakeviz benchmarks/*.prof             # View profiles

# Database
sqlite3 modan.db "PRAGMA integrity_check"  # Check integrity
sqlite3 modan.db "VACUUM"                   # Compact database
python migrate.py                           # Run migrations

# Build
python build.py                     # Build executable
```

### Resources

**Internal**:
- `docs/architecture.md` - Architecture overview
- `docs/performance.md` - Performance guide
- `devlog/` - Development logs
- `CLAUDE.md` - Project info for AI assistants

**External**:
- PyQt5: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- Peewee: http://docs.peewee-orm.com/
- pytest: https://docs.pytest.org/
- Numpy: https://numpy.org/doc/

### Glossary

- **Landmark**: A point of biological significance on a specimen
- **Procrustes**: Superimposition method to align shapes
- **PCA**: Principal Component Analysis
- **CVA**: Canonical Variate Analysis
- **MANOVA**: Multivariate Analysis of Variance
- **Centroid Size**: Scale measure (sqrt of sum of squared distances from centroid)
- **GPA**: Generalized Procrustes Analysis
- **TPS**: Thin-Plate Spline (also a file format)
- **ORM**: Object-Relational Mapping (Peewee)

---

**Maintained by**: Modan2 Development Team
**Last Updated**: 2025-10-06 (Post Phase 4)
**Next Review**: After major feature additions or structural changes
