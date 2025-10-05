# Modan2 Project Information for Claude

## Project Overview
Modan2 is a desktop GUI application for morphometric analysis, supporting 2D/3D landmark-based shape analysis with statistical tools.

## Key Information

### Main Entry Point
- **Run application**: `python Modan2.py`
- **Linux/WSL users**: Use `python fix_qt_import.py` if Qt plugin conflicts occur

### Development Environment Setup

#### Required System Dependencies (Linux/WSL)
```bash
sudo apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
  libxcb-randr0 libxcb-render-util0 libxcb-xfixes0 libxcb-shape0 libxcb-cursor0 \
  qt5-qmake qtbase5-dev libqt5gui5 libqt5core5a libqt5widgets5 python3-pyqt5 \
  libglut-dev libglut3.12 python3-opengl
```

#### Python Dependencies
- Install: `pip install -r requirements.txt`
- Key packages: PyQt5, numpy>2.0.0, pandas, scipy, opencv-python, peewee, trimesh

### Project Structure
```
Modan2/
├── Modan2.py             # Main application entry point
├── MdModel.py            # Database models (Peewee ORM)
├── MdUtils.py            # Utility functions and constants
├── ModanDialogs.py       # PyQt5 dialog classes (uses cv2)
├── ModanComponents.py    # Custom PyQt5 widgets (uses cv2)
├── MdStatistics.py       # Statistical analysis (PCA, CVA, MANOVA)
├── build.py              # PyInstaller build script
├── migrate.py            # Database migration tool
├── logs/                 # Application log files
├── config/               # Configuration files
│   ├── pytest.ini       # Pytest configuration
│   └── requirements-dev.txt # Development dependencies
├── tests/                # Automated test suite (pytest)
├── devlog/              # Development documentation and logs
├── scripts/             # Utility scripts and tools
└── test_script/         # Legacy test scripts (for reference)
```

### Build and Deployment
- **Build executable**: `python build.py`
- **Database migrations**: `python migrate.py`
- **Windows installer**: InnoSetup configuration in `InnoSetup/Modan2.iss`

### Testing

#### Current Testing Status
Automated testing with pytest is fully operational.

**Coverage Status** (as of 2025-10-05):
- **Overall**: 500+ tests, 503 passed, 35 skipped
- **MdStatistics.py**: 95% coverage ✅
- **MdUtils.py**: 78% coverage
- **MdModel.py**: 56% coverage
- **Target**: Maintain >70% for new code, >50% overall

#### Automated Testing Setup
- **Framework**: pytest with pytest-qt, pytest-cov, pytest-mock
- **Test directory**: `tests/`
- **Configuration**: `pytest.ini`
- **Install test dependencies**: `pip install -r config/requirements-dev.txt`

**Common Commands**:
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_mdmodel.py

# Run specific test class
pytest tests/test_mdmodel.py::TestMdDataset

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s

# Run only failed tests from last run
pytest --lf
```

#### Test Development Guidelines
1. Write tests for new features before or during implementation
2. Test file naming: `test_*.py` in `tests/` directory
3. Use fixtures for common test data (in `tests/conftest.py`)
4. Mock external dependencies when appropriate
5. Aim for minimum 70% code coverage on new code

#### Test Organization
**Core Module Tests**:
- `test_mdmodel.py` - Database models and operations (82 tests)
- `test_mdutils.py` - Utility functions and helpers
- `test_mdstatistics.py` - Statistical analysis functions
- `test_mdhelpers.py` - Helper functions

**Integration Tests**:
- `test_controller.py` - Controller logic and workflows
- `test_analysis_workflow.py` - Complete analysis workflows
- `test_import.py` - File import operations

**UI Tests** (pytest-qt):
- `test_ui_basic.py` - Basic UI components
- `test_ui_dialogs.py` - Dialog interactions
- `test_dataset_dialog_direct.py` - Dataset creation workflows

**Performance Tests**:
- `test_performance.py` - Performance benchmarks (skipped by default)

#### Before Committing
1. Run automated tests: `pytest`
2. Check test coverage: `pytest --cov=. --cov-report=term`
3. Ensure no regressions: `pytest --lf` (re-run last failures)
4. Run the application: `python Modan2.py`
5. Verify core features work (dataset loading, object viewing, analysis)

### Database
- SQLite database with Peewee ORM
- Models: MdDataset, MdObject, MdImage, MdThreeDModel, MdAnalysis
- Migrations tracked in `migrations/` folder

### Known Issues and Solutions

#### Qt Platform Plugin Error (Linux/WSL)
If you encounter "could not load the Qt platform plugin" error:
1. Run with: `python fix_qt_import.py` instead of `python Modan2.py`
2. Or set environment: `export QT_QPA_PLATFORM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt5/plugins/platforms`

#### OpenGL/GLUT Error
Install GLUT libraries: `sudo apt-get install -y libglut-dev libglut3.12 python3-opengl`

### Code Style Guidelines
- Follow existing PyQt5 patterns in the codebase
- Use Peewee ORM for all database operations
- Numpy > 2.0.0 is now supported (OpenGL issues resolved with pip installation)
- OpenCV (cv2) is used in ModanDialogs.py and ModanComponents.py

### Important Notes
- Cross-platform application (Windows, macOS, Linux)
- Supports various file formats: TPS, NTS, OBJ, PLY, STL, image formats
- Core functionality: 2D/3D landmark analysis, statistical shape analysis
- Version: 0.1.4
- License: MIT

### Development Workflow

#### Quick Start
1. Make changes to relevant Python files
2. Run linter and formatter: `ruff check . && ruff format .`
3. Run tests: `pytest`
4. Test application launch: `python Modan2.py` (or `python fix_qt_import.py` on Linux)
5. Verify core features work (dataset loading, object viewing, analysis)
6. Commit changes with descriptive messages

#### Code Quality Checks
Before committing code, ensure:
- All tests pass: `pytest`
- Code is formatted: `ruff format .`
- No linting errors: `ruff check .`
- Coverage maintained: `pytest --cov=. --cov-report=term`

### Code Quality Tools

#### Ruff - Linter and Formatter
Ruff is configured for fast Python linting and formatting.

**Configuration**: `pyproject.toml`
- Line length: 120
- Target Python: 3.12
- Enabled rules: pycodestyle (E), pyflakes (F), isort (I), pep8-naming (N), pyupgrade (UP), flake8-bugbear (B), flake8-comprehensions (C4)

**Usage**:
```bash
# Format all code
ruff format .

# Check for linting issues
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Check specific file
ruff check MdModel.py
```

**Key Exceptions**:
- E501: Line too long (handled by formatter)
- E402: Module level import not at top (needed for sys.path manipulation)
- N802/N803/N806: Qt methods use camelCase (PyQt5 convention)

#### Pre-commit Hooks
Pre-commit hooks are configured to run automatically before each commit.

**Setup**:
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

**Configured Hooks**:
- Ruff linting and formatting
- Trailing whitespace removal
- End-of-file fixer
- YAML validation
- Large file check
- Merge conflict detection

#### Type Hints
Core modules have type hints using Python 3.12+ syntax:
- `MdStatistics.py` - Full type coverage
- `MdUtils.py` - Core functions typed
- Using modern syntax: `str | None` instead of `Optional[str]`

**Type Checking** (optional):
```bash
# Install mypy
pip install mypy

# Check types in specific module
mypy MdStatistics.py MdUtils.py
```

#### Import Organization
- Wildcard imports removed from all modules
- Import order: stdlib → third-party → local
- Organized using isort (via Ruff)

## Code Navigation and Search Tools

### Quick Reference
The codebase has been indexed for fast navigation. Use these tools to quickly find code:

#### Index Location
- **Index files**: `.index/` directory contains all search indexes
- **Index report**: `.index/INDEX_REPORT.md` - Overview of entire codebase
- **Symbol cards**: `.index/cards/` - Detailed information about key components

### Search Commands

#### 1. Find Classes, Functions, Methods
```bash
# Search for any symbol (class, function, method)
python tools/search_index.py --symbol "DataExploration"
python tools/search_index.py -s "analyze"

# Search only specific types
python tools/search_index.py --symbol "Dialog" --type class
python tools/search_index.py -s "calculate" -t function
```

#### 2. Find Qt Signal/Slot Connections
```bash
# Find all connections for a signal or slot
python tools/search_index.py --qt "clicked"
python tools/search_index.py --qt "triggered"
python tools/search_index.py --qt "on_action"
```

#### 3. Find Wait Cursor Usage
```bash
# List all methods using wait cursor (for UX optimization)
python tools/search_index.py --wait-cursor
```

#### 4. Find Database Model Usage
```bash
# Find where database models are used
python tools/search_index.py --model "MdDataset"
python tools/search_index.py -m "MdAnalysis"
```

#### 5. Get File Information
```bash
# Get statistics about a specific file
python tools/search_index.py --file "ModanDialogs.py"
python tools/search_index.py -f "Modan2.py"
```

#### 6. Find Dialog Widgets
```bash
# Find widgets and layouts in a dialog
python tools/search_index.py --dialog "NewAnalysisDialog"
python tools/search_index.py -d "DataExploration"
```

#### 7. Project Statistics
```bash
# Show overall project statistics
python tools/search_index.py --stats
```

### Common Search Patterns

#### Finding Implementation of a Feature
```bash
# Example: Find analysis-related code
python tools/search_index.py -s "analysis"
python tools/search_index.py -s "run_analysis"
python tools/search_index.py --qt "analyze"
```

#### Finding UI Components
```bash
# Example: Find progress-related UI
python tools/search_index.py -s "progress"
python tools/search_index.py -s "ProgressDialog"
python tools/search_index.py --dialog "Progress"
```

#### Finding Event Handlers
```bash
# Example: Find button click handlers
python tools/search_index.py --qt "clicked"
python tools/search_index.py -s "btnOK_clicked"
python tools/search_index.py -s "_clicked"
```

### Rebuilding the Index
If the code has changed significantly:
```bash
# Rebuild complete index
python tools/build_index.py

# Regenerate symbol cards
python tools/generate_cards.py
```

### Key Files Quick Reference

| Component | File | Key Classes/Functions |
|-----------|------|----------------------|
| Main Window | `Modan2.py` | ModanMainWindow (80+ methods) |
| Dialogs | `ModanDialogs.py` (6,511 lines) | NewAnalysisDialog, DataExplorationDialog, etc. |
| Custom Widgets | `ModanComponents.py` (4,359 lines) | ObjectViewer2D, ObjectViewer3D |
| Database | `MdModel.py` | MdDataset, MdObject, MdAnalysis |
| Statistics | `MdStatistics.py` | PCA, CVA, MANOVA functions |
| Controller | `ModanController.py` | ModanController (35+ methods) |
| Utilities | `MdUtils.py` | Helper functions, constants |

### Performance Hotspots
Methods with wait cursor (long operations):
- `ModanDialogs.py:2402` - cbxShapeGrid_state_changed
- `ModanDialogs.py:4072` - pick_shape
- `ModanDialogs.py:1710` - NewAnalysisDialog.btnOK_clicked
- `Modan2.py:659` - on_action_analyze_dataset_triggered

### Quick Stats (as of last index)
- **Total Files**: 27
- **Total Lines**: 24,145
- **Classes**: 63
- **Functions**: 960
- **Dialogs**: 11
- **Database Models**: 5
- **Qt Connections**: 257
