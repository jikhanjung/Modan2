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
- Key packages: PyQt5, numpy<2.0.0, pandas, scipy, opencv-python, peewee, trimesh

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
- Transitioning from manual testing to automated testing with pytest
- Legacy test scripts in `test_script/` directory (for reference)

#### Automated Testing Setup (In Progress)
- **Framework**: pytest
- **Test directory**: `tests/`
- **Install test dependencies**: `pip install -r config/requirements-dev.txt`
- **Run all tests**: `pytest`
- **Run with coverage**: `pytest --cov=. --cov-report=html`
- **Run specific test file**: `pytest tests/test_mdutils.py`
- **Run with verbose output**: `pytest -v`

#### Test Development Guidelines
1. Write tests for new features before or during implementation
2. Test file naming: `test_*.py` in `tests/` directory
3. Use fixtures for common test data (in `tests/conftest.py`)
4. Mock external dependencies when appropriate
5. Aim for minimum 50% code coverage on core modules

#### Testing Priority (Planned)
1. **Priority 1**: Utility functions (`MdUtils.py`) - Pure functions, easiest to test
2. **Priority 2**: Data models (`MdModel.py`) - Database CRUD operations
3. **Priority 3**: Statistical analysis (`MdStatistics.py`) - Core calculation logic
4. **Priority 4**: Business logic (non-UI parts of `Modan2.py`)
5. **Future**: UI components with `pytest-qt`

#### Before Committing
1. Run the application: `python Modan2.py`
2. Verify core features work (dataset loading, object viewing, analysis)
3. Run automated tests: `pytest`
4. Check test coverage: `pytest --cov=. --cov-report=term`

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
- Maintain compatibility with numpy < 2.0.0
- OpenCV (cv2) is used in ModanDialogs.py and ModanComponents.py

### Important Notes
- Cross-platform application (Windows, macOS, Linux)
- Supports various file formats: TPS, NTS, OBJ, PLY, STL, image formats
- Core functionality: 2D/3D landmark analysis, statistical shape analysis
- Version: 0.1.4
- License: MIT

### Development Workflow
1. Make changes to relevant Python files
2. Test application launch: `python Modan2.py` (or `python fix_qt_import.py` on Linux)
3. Verify core features work (dataset loading, object viewing, analysis)
4. Run any relevant test scripts from `test_script/`
5. Commit changes with descriptive messages

### Linting and Type Checking
Currently no automated linting or type checking configured. Consider adding:
- `ruff` for Python linting
- `mypy` for type checking (would require adding type hints)