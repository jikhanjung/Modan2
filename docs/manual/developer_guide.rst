Developer Guide
===============

This guide provides information for developers who want to contribute to Modan2 or understand its architecture.

Project Overview
----------------

Modan2 is a Python desktop application for geometric morphometrics built with:

- **GUI Framework**: PyQt5
- **Database**: SQLite with Peewee ORM
- **Scientific Computing**: NumPy, SciPy, Pandas, Statsmodels
- **3D Graphics**: PyOpenGL, Trimesh
- **Image Processing**: Pillow, OpenCV

**Project Structure**:

.. code-block:: text

   Modan2/
   ├── Modan2.py                    # Main application entry point
   ├── MdModel.py                   # Database models (Peewee ORM)
   ├── MdUtils.py                   # Utility functions and constants
   ├── MdStatistics.py              # Statistical analysis functions
   ├── MdHelpers.py                 # Helper functions
   ├── MdConstants.py               # Application constants
   ├── MdLogger.py                  # Logging utilities
   ├── MdAppSetup.py                # Application initialization
   ├── MdSplashScreen.py            # Splash screen widget
   ├── ModanController.py           # MVC controller
   ├── ModanDialogs.py              # Legacy dialogs (being phased out)
   ├── ModanComponents.py           # Legacy components (being phased out)
   ├── ModanWidgets.py              # Reusable widget utilities
   ├── build.py                     # PyInstaller build script
   ├── migrate.py                   # Database migration tool
   ├── requirements.txt             # Python dependencies
   │
   ├── dialogs/                     # Dialog modules (Phase 2+ refactoring)
   │   ├── __init__.py
   │   ├── base_dialog.py           # Base dialog class
   │   ├── analysis_dialog.py       # New analysis dialog
   │   ├── analysis_result_dialog.py # Analysis results
   │   ├── calibration_dialog.py    # Image calibration
   │   ├── data_exploration_dialog.py # Data visualization & exploration
   │   ├── dataset_analysis_dialog.py # Dataset analysis configuration
   │   ├── dataset_dialog.py        # Dataset create/edit
   │   ├── export_dialog.py         # Data export (TPS, Morphologika, JSON+ZIP)
   │   ├── import_dialog.py         # Data import (TPS, NTS, X1Y1, etc.)
   │   ├── object_dialog.py         # Object/specimen editor with landmarks
   │   ├── preferences_dialog.py    # Application preferences
   │   └── progress_dialog.py       # Progress tracking
   │
   ├── components/                  # Reusable components (Phase 3+ refactoring)
   │   ├── __init__.py
   │   ├── formats/                 # File format parsers
   │   │   ├── tps.py              # TPS format support
   │   │   ├── nts.py              # NTS format support
   │   │   ├── x1y1.py             # X1Y1 format support
   │   │   └── morphologika.py     # Morphologika format support
   │   ├── viewers/                 # 2D/3D visualization widgets
   │   │   ├── object_viewer_2d.py # 2D image viewer with landmarks
   │   │   └── object_viewer_3d.py # 3D model viewer (OpenGL)
   │   └── widgets/                 # UI widgets
   │       ├── analysis_info.py     # Analysis info widget
   │       ├── dataset_ops_viewer.py # Dataset operations viewer
   │       ├── delegates.py         # Table/tree delegates
   │       ├── drag_widgets.py      # Drag-and-drop widgets
   │       ├── overlay_widget.py    # Overlay rendering widget
   │       ├── pic_button.py        # Picture button widget
   │       ├── shape_preference.py  # Shape visualization preferences
   │       └── table_view.py        # Custom table view
   │
   ├── OBJFileLoader/               # 3D OBJ file loading
   │   ├── objloader.py
   │   └── objviewer.py
   │
   ├── tests/                       # Automated tests (pytest)
   │   ├── conftest.py              # Test fixtures
   │   ├── test_mdmodel.py          # Database model tests
   │   ├── test_mdstatistics.py     # Statistical analysis tests
   │   ├── test_mdutils.py          # Utility function tests
   │   └── ...                      # Additional test modules
   │
   ├── devlog/                      # Development log (142+ sessions)
   ├── docs/                        # Sphinx documentation
   ├── icons/                       # Application icons
   ├── migrations/                  # Database schema migrations
   ├── benchmarks/                  # Performance benchmarks
   ├── tools/                       # Development tools & scripts
   ├── config/                      # Configuration files
   │   ├── pytest.ini
   │   └── requirements-dev.txt
   └── translations/                # i18n translation files

Architecture
------------

High-Level Overview
~~~~~~~~~~~~~~~~~~~

Modan2 follows a modified **Model-View-Controller (MVC)** pattern:

.. code-block:: text

   ┌──────────────────────────────────────────┐
   │         ModanMainWindow (View)            │
   │  ┌────────────┐  ┌──────────────────┐   │
   │  │ TreeView   │  │  TableView       │   │
   │  │ (Datasets) │  │  (Objects)       │   │
   │  └────────────┘  └──────────────────┘   │
   └──────────────┬───────────────────────────┘
                  │
                  ├─── Signals/Slots ───┐
                  │                      │
   ┌──────────────▼─────────────┐  ┌────▼──────────────┐
   │  ModanController           │  │  ModanDialogs     │
   │  - Dataset operations      │  │  - ObjectDialog   │
   │  - Object CRUD             │  │  - AnalysisDialog │
   │  - Analysis coordination   │  │  - Preferences    │
   └───────────┬────────────────┘  └───────────────────┘
               │
               │ Uses
               │
   ┌───────────▼────────────────────────────────┐
   │         MdModel (Model - Peewee ORM)       │
   │  ┌──────────┐  ┌─────────────┐            │
   │  │MdDataset │  │ MdObject    │            │
   │  │MdImage   │  │ MdAnalysis  │            │
   │  └──────────┘  └─────────────┘            │
   │                                             │
   │  Database: modan.db (SQLite)               │
   └────────────────────────────────────────────┘
                    │
                    │ Queries
                    │
   ┌────────────────▼──────────────────┐
   │    MdStatistics                    │
   │  - Procrustes superimposition      │
   │  - PCA, CVA, MANOVA                │
   │  - Missing landmark imputation     │
   └────────────────────────────────────┘

Database Schema
~~~~~~~~~~~~~~~

**Core Models** (defined in ``MdModel.py``):

1. **MdDataset**:

   - Hierarchical structure (parent/child relationships)
   - Stores dimension (2D/3D), description
   - One-to-many relationship with MdObject

2. **MdObject**:

   - Represents a specimen (image or 3D model)
   - Stores landmark coordinates as JSON string (``landmark_str``)
   - Foreign key to MdDataset
   - Variable data stored as JSON (``propertyvalue_str``)

3. **MdImage**:

   - Links 2D images to objects
   - Stores file path, EXIF data, width/height

4. **MdThreeDModel**:

   - Links 3D models to objects
   - Stores file path, mesh metadata

5. **MdAnalysis**:

   - Stores analysis results (PCA, CVA, MANOVA)
   - Linked to MdDataset
   - Results stored as JSON

**Relationships**:

.. code-block:: python

   MdDataset (1) ──< (many) MdObject
   MdDataset (1) ──< (many) MdAnalysis
   MdObject (1) ──< (0 or 1) MdImage
   MdObject (1) ──< (0 or 1) MdThreeDModel

**Key Fields**:

- ``landmark_str``: Serialized landmark coordinates (format: "x,y\\nx,y\\n...")
- ``propertyvalue_str``: Serialized variable values (JSON)

**Temporary Operations**: ``MdObjectOps`` and ``MdDatasetOps`` classes wrap database models for in-memory operations (e.g., Procrustes alignment) without modifying the database.

MVC Pattern in Modan2
~~~~~~~~~~~~~~~~~~~~~

**Model** (``MdModel.py``):

- Peewee ORM models
- Database queries and CRUD operations
- Data validation

**View** (``Modan2.py``, ``dialogs/``, ``components/``):

- ``ModanMainWindow`` (``Modan2.py``): Main application window with tree/table views
- Dialog classes (``dialogs/*.py``): ``ObjectDialog``, ``NewAnalysisDialog``, ``DataExplorationDialog``, etc.
- Viewer widgets (``components/viewers/``): ``ObjectViewer2D``, ``ObjectViewer3D``
- Custom widgets (``components/widgets/``): UI components for analysis, data display, etc.
- Qt signals emitted on user actions

**Controller** (``ModanController.py``):

- Connects signals from views to model operations
- Coordinates between UI and business logic
- Handles analysis workflow

**Example Flow**:

.. code-block:: text

   User clicks "New Dataset" button
   → MainWindow emits signal
   → Controller receives signal
   → Controller opens DatasetDialog
   → User fills form, clicks OK
   → Controller creates MdDataset in database
   → Controller refreshes TreeView
   → TreeView displays new dataset

File Formats
~~~~~~~~~~~~

**TPS Format** (morphometric standard):

.. code-block:: text

   LM=5
   12.5 34.2
   45.6 78.9
   ...
   IMAGE=specimen_001.jpg
   ID=1
   SCALE=1.0

**NTS Format** (legacy):

.. code-block:: text

   5
   12.5 34.2
   45.6 78.9
   ...

**CSV Format** (custom):

.. code-block:: text

   object,lm1_x,lm1_y,lm2_x,lm2_y
   spec_001,12.5,34.2,45.6,78.9

**Internal Storage** (in database):

- Landmarks stored as newline-separated "x,y" or "x,y,z" strings
- Parsing done by ``MdObject.unpack_landmark()``
- Packing done by ``MdObject.pack_landmark()``

Development Setup
-----------------

Prerequisites
~~~~~~~~~~~~~

- **Python**: 3.11 or newer
- **Git**: For version control
- **IDE**: VSCode, PyCharm, or any Python IDE
- **Operating System**: Windows, macOS, or Linux

Cloning the Repository
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/jikhanjung/Modan2.git
   cd Modan2

Virtual Environment Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Linux/macOS**:

.. code-block:: bash

   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r config/requirements-dev.txt

**Windows**:

.. code-block:: bash

   python -m venv venv
   venv\\Scripts\\activate
   pip install -r requirements.txt
   pip install -r config/requirements-dev.txt

Running from Source
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python Modan2.py

**Linux/WSL**: If Qt errors occur:

.. code-block:: bash

   python fix_qt_import.py

Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

Installed via ``config/requirements-dev.txt``:

- ``pytest``: Testing framework
- ``pytest-cov``: Code coverage
- ``pytest-qt``: PyQt5 testing support (future)
- ``ruff``: Linting (future)

Testing
-------

Test Framework
~~~~~~~~~~~~~~

Modan2 uses **pytest** for automated testing.

**Test Structure**:

.. code-block:: text

   tests/
   ├── conftest.py            # Shared fixtures
   ├── test_mdutils.py        # Utility function tests
   ├── test_mdmodel.py        # Database model tests
   └── test_statistics.py     # Statistical function tests

Running Tests
~~~~~~~~~~~~~

**Run all tests**:

.. code-block:: bash

   pytest

**Run specific test file**:

.. code-block:: bash

   pytest tests/test_mdutils.py

**Run with coverage**:

.. code-block:: bash

   pytest --cov=. --cov-report=html
   # Open htmlcov/index.html

**Verbose output**:

.. code-block:: bash

   pytest -v

Writing Tests
~~~~~~~~~~~~~

**Example test** (``tests/test_mdutils.py``):

.. code-block:: python

   import pytest
   from MdUtils import normalize_path, is_valid_dimension

   def test_normalize_path():
       assert normalize_path("C:\\\\Users\\\\test") == "C:/Users/test"

   def test_is_valid_dimension():
       assert is_valid_dimension(2) == True
       assert is_valid_dimension(3) == True
       assert is_valid_dimension(4) == False

**Using fixtures** (``tests/conftest.py``):

.. code-block:: python

   import pytest
   from peewee import SqliteDatabase
   from MdModel import MdDataset, MdObject

   @pytest.fixture
   def test_db():
       test_database = SqliteDatabase(':memory:')
       with test_database.bind_ctx([MdDataset, MdObject]):
           test_database.create_tables([MdDataset, MdObject])
           yield test_database
           test_database.drop_tables([MdDataset, MdObject])

   def test_create_dataset(test_db):
       dataset = MdDataset.create(name="Test", dimension=2)
       assert dataset.name == "Test"

Code Style Guidelines
---------------------

General Principles
~~~~~~~~~~~~~~~~~~

- Follow **PEP 8** conventions
- Use descriptive variable names
- Add docstrings to classes and functions
- Keep functions focused (single responsibility)

Naming Conventions
~~~~~~~~~~~~~~~~~~

- **Classes**: ``PascalCase`` (e.g., ``ModanController``, ``ObjectDialog``)
- **Functions/Methods**: ``snake_case`` (e.g., ``create_dataset``, ``pack_landmark``)
- **Constants**: ``UPPER_SNAKE_CASE`` (e.g., ``PROGRAM_NAME``, ``DEFAULT_COLOR``)
- **Private methods**: ``_leading_underscore`` (e.g., ``_update_view``)
- **Qt slots**: ``on_<widget>_<action>`` (e.g., ``on_btnOK_clicked``)

Docstring Format
~~~~~~~~~~~~~~~~

Use **Google-style docstrings**:

.. code-block:: python

   def estimate_missing_landmarks(self, obj_index, reference_shape):
       """Estimate missing landmarks using aligned mean shape.

       The mean shape is computed from Procrustes-aligned complete specimens,
       then transformed to match the scale and position of the current object.

       Args:
           obj_index (int): Index of object in object_list
           reference_shape (MdObjectOps): Reference shape with complete landmarks

       Returns:
           list: Estimated landmark coordinates, or None if estimation fails

       Raises:
           ValueError: If obj_index is out of range
       """
       # Implementation...

PyQt5 Patterns
~~~~~~~~~~~~~~

**Signal/Slot Connections**:

.. code-block:: python

   # In __init__
   self.btnOK.clicked.connect(self.on_btnOK_clicked)

   # Slot method
   def on_btnOK_clicked(self):
       # Handle button click
       pass

**Wait Cursor for Long Operations**:

.. code-block:: python

   from PyQt5.QtCore import Qt
   from PyQt5.QtWidgets import QApplication

   def long_operation(self):
       QApplication.setOverrideCursor(Qt.WaitCursor)
       try:
           # Perform operation
           result = self.compute_something()
       finally:
           QApplication.restoreOverrideCursor()
       return result

Contributing
------------

Git Workflow
~~~~~~~~~~~~

1. **Fork the repository** on GitHub
2. **Clone your fork**:

   .. code-block:: bash

      git clone https://github.com/YOUR_USERNAME/Modan2.git
      cd Modan2

3. **Create a feature branch**:

   .. code-block:: bash

      git checkout -b feature/my-new-feature

4. **Make changes** and commit:

   .. code-block:: bash

      git add .
      git commit -m "Add new feature: description"

5. **Push to your fork**:

   .. code-block:: bash

      git push origin feature/my-new-feature

6. **Open a Pull Request** on GitHub

Commit Message Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~

Follow conventional commits:

.. code-block:: text

   <type>: <subject>

   <body (optional)>

   <footer (optional)>

**Types**:

- ``feat``: New feature
- ``fix``: Bug fix
- ``docs``: Documentation changes
- ``style``: Code style (formatting, no logic change)
- ``refactor``: Code restructuring
- ``test``: Adding/updating tests
- ``chore``: Maintenance tasks

**Examples**:

.. code-block:: text

   feat: Add hollow circle visualization for estimated landmarks

   fix: Resolve scale mismatch in missing landmark estimation

   docs: Update user guide with missing landmark section

   test: Add tests for Procrustes with missing data

Pull Request Process
~~~~~~~~~~~~~~~~~~~~~

1. **Describe your changes** clearly in the PR description
2. **Reference related issues** (e.g., "Fixes #42")
3. **Ensure tests pass**: Run ``pytest`` locally before submitting
4. **Update documentation** if adding new features
5. **Respond to review comments** promptly
6. **Squash commits** if requested (to keep history clean)

Code Review Checklist
~~~~~~~~~~~~~~~~~~~~~~

Reviewers will check:

- [ ] Code follows style guidelines
- [ ] New features have tests
- [ ] Documentation updated (if needed)
- [ ] No breaking changes (or clearly documented)
- [ ] Performance considerations addressed
- [ ] No security vulnerabilities introduced

Building Executables
---------------------

PyInstaller Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Modan2 uses PyInstaller to create standalone executables.

**Build script**: ``build.py``

**Running the build**:

.. code-block:: bash

   python build.py

**Output**:

- ``dist/Modan2/`` - Standalone application folder
- ``dist/Modan2.exe`` - Executable (Windows)
- ``dist/Modan2`` - Executable (Linux/macOS)

Platform-Specific Builds
~~~~~~~~~~~~~~~~~~~~~~~~

**Windows**:

.. code-block:: bash

   python build.py
   # Creates dist/Modan2.exe

**macOS**:

.. code-block:: bash

   python build.py
   # Creates dist/Modan2.app

**Linux**:

.. code-block:: bash

   python build.py
   # Creates dist/Modan2

**Note**: Cross-platform builds are not supported - build on the target platform.

InnoSetup Installer (Windows)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For Windows installers:

1. Install InnoSetup from https://jrsoftware.org/isinfo.php
2. Build executable: ``python build.py``
3. Compile installer:

   .. code-block:: bash

      iscc InnoSetup/Modan2.iss

4. Output: ``Output/Modan2-Setup.exe``

Creating Releases
~~~~~~~~~~~~~~~~~

1. **Update version** in ``MdUtils.py``:

   .. code-block:: python

      PROGRAM_VERSION = "0.1.5"

2. **Update CHANGELOG.md** with release notes

3. **Commit changes**:

   .. code-block:: bash

      git commit -am "Release v0.1.5"
      git tag v0.1.5
      git push origin main --tags

4. **Build executables** for Windows, macOS, Linux

5. **Create GitHub Release**:

   - Go to Releases → Draft a new release
   - Tag: ``v0.1.5``
   - Title: ``Modan2 v0.1.5``
   - Description: Copy from CHANGELOG.md
   - Attach built executables

6. **Publish release**

Database Migrations
-------------------

Modan2 uses ``peewee-migrate`` for schema changes.

Creating a Migration
~~~~~~~~~~~~~~~~~~~~

When you modify database models:

.. code-block:: bash

   python migrate.py create <migration_name>

**Example**:

.. code-block:: bash

   python migrate.py create add_missing_landmark_flag

This creates a new migration file in ``migrations/``.

**Edit the migration file** to define changes:

.. code-block:: python

   def migrate(migrator, database, fake=False, **kwargs):
       migrator.add_column('mdobject', 'has_missing', BooleanField(default=False))

   def rollback(migrator, database, fake=False, **kwargs):
       migrator.drop_column('mdobject', 'has_missing')

Running Migrations
~~~~~~~~~~~~~~~~~~

Apply pending migrations:

.. code-block:: bash

   python migrate.py

Rollback last migration:

.. code-block:: bash

   python migrate.py rollback

Advanced Topics
---------------

Custom Widgets
~~~~~~~~~~~~~~

Creating custom PyQt5 widgets (see ``components/widgets/`` for examples):

.. code-block:: python

   from PyQt5.QtWidgets import QWidget
   from PyQt5.QtCore import pyqtSignal

   class CustomWidget(QWidget):
       # Define custom signals
       valueChanged = pyqtSignal(int)

       def __init__(self, parent=None):
           super().__init__(parent)
           self.initUI()

       def initUI(self):
           # Setup UI components
           pass

       def setValue(self, value):
           # Custom logic
           self.valueChanged.emit(value)

**Examples from codebase**:

- ``components/widgets/pic_button.py``: Custom button with image support
- ``components/widgets/drag_widgets.py``: Drag-and-drop list widgets
- ``components/viewers/object_viewer_2d.py``: Complex 2D viewer with landmark editing
- ``components/viewers/object_viewer_3d.py``: OpenGL-based 3D viewer

Statistical Extensions
~~~~~~~~~~~~~~~~~~~~~~

Adding new statistical methods (in ``MdStatistics.py``):

.. code-block:: python

   def perform_new_analysis(dataset_ops, options):
       """Perform new statistical analysis.

       Args:
           dataset_ops (MdDatasetOps): Dataset with aligned shapes
           options (dict): Analysis parameters

       Returns:
           dict: Results including scores, statistics, etc.
       """
       # Extract shape data
       coords = extract_coordinates(dataset_ops)

       # Perform analysis
       result = compute_something(coords, **options)

       return {
           'scores': result.scores,
           'statistics': result.stats,
       }

Plugin System (Future)
~~~~~~~~~~~~~~~~~~~~~~

Modan2 may support plugins in future versions:

.. code-block:: python

   # plugins/my_plugin.py
   class MyPlugin:
       name = "My Analysis Plugin"
       version = "1.0"

       def run(self, dataset):
           # Plugin logic
           return result

Profiling and Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Profiling with cProfile**:

.. code-block:: bash

   python -m cProfile -o profile.stats Modan2.py
   # Analyze with snakeviz
   pip install snakeviz
   snakeviz profile.stats

**Memory profiling**:

.. code-block:: bash

   pip install memory_profiler
   python -m memory_profiler Modan2.py

Debugging
~~~~~~~~~

**Enable detailed logging**:

.. code-block:: python

   # In Modan2.py
   logging.basicConfig(level=logging.DEBUG)

**Qt debugging**:

.. code-block:: bash

   export QT_DEBUG_PLUGINS=1
   python Modan2.py

Resources
---------

Documentation
~~~~~~~~~~~~~

- `PyQt5 Documentation <https://www.riverbankcomputing.com/static/Docs/PyQt5/>`_
- `Peewee ORM Documentation <http://docs.peewee-orm.com/>`_
- `NumPy Documentation <https://numpy.org/doc/>`_
- `SciPy Documentation <https://docs.scipy.org/doc/scipy/>`_

Morphometric Analysis
~~~~~~~~~~~~~~~~~~~~~

- `Geometric Morphometrics for Biologists <https://www.elsevier.com/books/geometric-morphometrics-for-biologists/zelditch/978-0-12-386903-6>`_ by Zelditch et al.
- `Morphometrics with R <https://www.springer.com/gp/book/9780387777894>`_ by Claude

Community
~~~~~~~~~

- **GitHub Issues**: https://github.com/jikhanjung/Modan2/issues
- **Discussions**: https://github.com/jikhanjung/Modan2/discussions

License
-------

Modan2 is released under the **MIT License**.

You are free to:

- Use commercially
- Modify
- Distribute
- Sublicense

Under the condition that you include the original copyright and license notice.

See the `LICENSE <https://github.com/jikhanjung/Modan2/blob/main/LICENSE>`_ file for details.
