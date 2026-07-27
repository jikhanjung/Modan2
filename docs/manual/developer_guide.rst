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
   ├── main.py               Entry point (--debug, --db, --config, --lang, --no-splash)
   ├── Modan2.py             ModanMainWindow, imported by main.py
   ├── ModanController.py    Controller layer: DB/file I/O, analysis runs
   ├── MdModel.py            Peewee models + Procrustes/superimposition operations
   ├── MdStatistics.py       PCA, CVA, MANOVA
   ├── MdUtils.py            Utilities, paths, constants
   ├── MdHelpers.py          Shared helpers (guard_slot, geometry, …)
   ├── MdConstants.py        Shared constants
   ├── MdAppSetup.py         Application initialization
   ├── MdSplashScreen.py     Splash screen
   ├── MdLiveWire.py         Edge-following curve tracing
   ├── build.py              PyInstaller build script
   ├── migrate.py            Database migration tool
   ├── version.py            Single source of truth for the version
   │
   ├── dialogs/              One module per dialog, all inheriting BaseDialog
   ├── components/
   │   ├── formats/          TPS / NTS / X1Y1 / Morphologika readers
   │   ├── viewers/          ObjectViewer2D, ObjectViewer3D
   │   └── widgets/          Custom PyQt5 widgets
   ├── OBJFileLoader/        3D OBJ loading
   │
   ├── tests/                pytest suite
   ├── migrations/           Database schema migrations
   ├── tools/                Code index builder and search (dev only)
   ├── scripts/              Benchmarks and profilers (dev only)
   ├── benchmarks/           Benchmark output
   ├── devlog/               Development log
   ├── docs/                 Repository-only Markdown notes
   │   └── manual/           This manual (Sphinx, .rst)
   ├── config/               requirements-dev.txt
   ├── icons/                Application icons
   └── translations/         Qt i18n files (.ts / .qm)

``ModanComponents.py`` is a backward-compatibility shim re-exporting
``components/``; new code should import from ``components.<subpackage>`` and
``dialogs.<module>`` directly. ``ModanDialogs.py`` no longer exists — every
dialog has been migrated into ``dialogs/``.

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
   │  ModanController           │  │  dialogs/         │
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
   │  Database: Modan2.db (SQLite)              │
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

- **Python**: 3.12 or newer
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

   python main.py

``main.py`` is the entry point; ``Modan2.py`` is a module it imports, not a
script. Useful flags: ``--debug``, ``--db <path>``, ``--config <path>``,
``--lang <en|ko>``, ``--no-splash``.

**Linux/WSL**: if Qt cannot load its ``xcb`` platform plugin:

.. code-block:: bash

   python fix_qt_import.py

Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

Installed via ``config/requirements-dev.txt``:

- ``pytest``, ``pytest-cov``, ``pytest-qt``, ``pytest-mock``: the test suite
- ``ruff``: linting and formatting (enforced in CI)
- ``mypy``: type checking
- ``pre-commit``: the commit hooks

Code Quality Tools
~~~~~~~~~~~~~~~~~~

Ruff handles both linting and formatting; configuration lives in
``pyproject.toml`` (line length 120, target Python 3.12).

.. code-block:: bash

   ruff format .          # format
   ruff check .           # lint
   ruff check --fix .     # lint and auto-fix

Type checking is optional locally but runs in CI:

.. code-block:: bash

   mypy MdStatistics.py MdUtils.py

Pre-commit runs the same checks before each commit:

.. code-block:: bash

   pre-commit install         # one-time setup
   pre-commit run --all-files # run manually

Before pushing, the short version is: ``ruff check . && ruff format . && pytest``.

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

.. important::
   On Linux (including WSL) the GUI tests need an X server **and** the xcb
   libraries PyQt5's platform plugin links against. If either is missing the
   suite does not fail cleanly — the interpreter aborts with ``Fatal Python
   error: Aborted`` partway through, which looks like a code problem but is not.

   .. code-block:: bash

      sudo apt-get install -y xvfb fonts-nanum \
        libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
        libxcb-randr0 libxcb-render-util0 libxcb-xfixes0 libxcb-shape0 \
        libxcb-cursor0 libxkbcommon-x11-0

      Xvfb :99 -screen 0 1024x768x24 >/tmp/xvfb.log 2>&1 &
      export DISPLAY=:99
      pytest -p no:xvfb

   ``-p no:xvfb`` disables the ``pytest-xvfb`` plugin so it does not start and
   tear down a second server on top of this one. **Leaving it out makes pytest
   hang** rather than fail — the plugin tries to start its own Xvfb and never
   returns, so the run stalls before collection finishes.

   If it still aborts, ask Qt which library it could not open:

   .. code-block:: bash

      QT_DEBUG_PLUGINS=1 python -c "from PyQt5.QtWidgets import QApplication; QApplication([])"

   The answer is usually one missing ``libxcb-*`` package named in the error.

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

Common Tasks
------------

Adding a New Dialog
~~~~~~~~~~~~~~~~~~~

Dialogs live one per module under ``dialogs/`` and inherit ``BaseDialog``, which
supplies the title, geometry save/restore, ``show_error`` / ``show_warning`` /
``show_info``, ``with_wait_cursor``, and ``create_button_box``.

.. code-block:: python

   # dialogs/my_new_dialog.py
   from PyQt5.QtWidgets import QLabel, QVBoxLayout

   from dialogs.base_dialog import BaseDialog


   class MyNewDialog(BaseDialog):
       """Dialog for the new feature."""

       def __init__(self, parent=None):
           super().__init__(parent, title="My New Dialog")
           self._create_widgets()
           self._create_layout()
           self._connect_signals()

       def _create_widgets(self):
           self.lblInfo = QLabel("Information goes here")

       def _create_layout(self):
           layout = QVBoxLayout()
           layout.addWidget(self.lblInfo)
           layout.addWidget(self.create_button_box())
           self.setLayout(layout)

       def _connect_signals(self):
           pass

Export it from ``dialogs/__init__.py`` (import it and add the name to
``__all__``), then open it from the main window:

.. code-block:: python

   from dialogs import MyNewDialog

   @guard_slot("Failed to open the new feature")
   def on_action_new_feature_triggered(self):
       dialog = MyNewDialog(self)
       if dialog.exec_() == QDialog.Accepted:
           ...
       dialog.deleteLater()

.. note::
   Wrap slots in ``@guard_slot`` so an exception surfaces as an error dialog
   instead of silently closing the window, and call ``deleteLater()`` after
   ``exec_()`` — parented dialogs are otherwise never freed.

Add a test under ``tests/dialogs/``:

.. code-block:: python

   def test_dialog_creation(qtbot):
       dialog = MyNewDialog()
       qtbot.addWidget(dialog)
       assert dialog.windowTitle() == "My New Dialog"

Adding a New Analysis Method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A single analysis run performs the superimposition and then computes PCA, CVA,
and MANOVA together — there is no per-analysis-type switch to extend. Statistical
routines live in ``MdStatistics.py`` and follow the ``do_*_analysis`` convention
(``do_pca_analysis``, ``do_cva_analysis``, ``do_manova_analysis``), taking
landmark data plus grouping and returning a result dictionary.

.. code-block:: python

   # MdStatistics.py
   def do_new_analysis(landmarks_data, groups=None):
       """Perform the new analysis.

       Args:
           landmarks_data: sequence of (n_landmarks, n_dims) arrays
           groups: per-object group labels, when the method needs them

       Returns:
           dict with the results and any summary statistics
       """
       if not landmarks_data:
           raise ValueError("landmarks_data cannot be empty")
       ...

Call it from ``ModanController.run_analysis``, which already receives
``superimposition_method``, ``cva_group_by``, and ``manova_group_by``, and
persist the output alongside the other results in ``_persist_analysis_results``.
Anything you want to keep needs a field on ``MdAnalysis`` and a migration (see
`Database Migrations`_).

Cover the new routine in ``tests/test_mdstatistics.py``; that module has the
highest coverage in the project and is the right place to keep it.

Adding a New File Format
~~~~~~~~~~~~~~~~~~~~~~~~

Readers live in ``components/formats/`` — one module per format, each exposing a
class (``TPS``, ``NTS``, ``X1Y1``, ``Morphologika``).

.. code-block:: python

   # components/formats/newformat.py
   from components.formats._encoding import open_text


   class NewFormat:
       def __init__(self, filename, datasetname, invertY=False):
           self.filename = filename
           self.dataset_name = datasetname
           self.invertY = invertY
           self.nlandmarks = 0
           self.object_name_list = []
           self.landmark_data = {}

       def read(self):
           with open_text(self.filename) as f:
               ...

.. important::
   Open files through ``components/formats/_encoding.py``'s ``open_text``, not
   plain ``open()``. It tries UTF-8, then the platform encoding, then latin-1, so
   a file with non-ASCII specimen names imports on any locale.

   Set ``nlandmarks`` from the data rather than leaving it at zero — that was a
   real bug in the X1Y1 reader.

Export the class from ``components/formats/__init__.py``, add a radio button and
a branch in ``dialogs/import_dialog.py``, and add parser tests under ``tests/``
covering a well-formed file, a malformed one (it must raise a clear error, not
crash), and a non-ASCII specimen name.

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
2. Run ``python build.py`` — it builds the executable, fills
   ``InnoSetup/Modan2.iss.template`` in with the current version and build
   number, and compiles the installer
3. Output: ``InnoSetup/Output/Modan2_v<version>_build<build>_Installer.exe``

Creating Releases
~~~~~~~~~~~~~~~~~

1. **Bump the version.** ``version.py`` is the single source of truth — every
   other place (the app, ``conf.py``, the installer name) derives from it, and
   ``tests/test_version_consistency.py`` fails if something hardcodes it
   instead. Use the helper rather than editing by hand:

   .. code-block:: bash

      python manage_version.py patch        # or minor / major
      python manage_version.py prerelease   # 0.2.0-alpha.2 -> alpha.3

2. **Update CHANGELOG.md** with release notes

3. **Commit and tag**:

   .. code-block:: bash

      git commit -am "Release v<version>"
      git tag v<version>
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

   python -m cProfile -o profile.stats main.py
   # Analyze with snakeviz
   pip install snakeviz
   snakeviz profile.stats

**Memory profiling**:

.. code-block:: bash

   pip install memory_profiler
   python -m memory_profiler main.py

Debugging
~~~~~~~~~

**Logging**. Modules take a standard module-level logger; ``main.py`` configures
the handlers in ``setup_logging()``, and ``--debug`` raises the level.

.. code-block:: python

   import logging

   logger = logging.getLogger(__name__)

   logger.debug("Detailed debugging info")
   logger.error("Something failed", exc_info=True)

Log files are written to ``~/PaleoBytes/Modan2/logs/``.

**Qt debugging**:

.. code-block:: bash

   export QT_DEBUG_PLUGINS=1
   python main.py --debug

**Database debugging**. Peewee logs the SQL it emits:

.. code-block:: python

   import logging

   logging.getLogger("peewee").addHandler(logging.StreamHandler())
   logging.getLogger("peewee").setLevel(logging.DEBUG)

To inspect the database directly:

.. code-block:: bash

   sqlite3 ~/PaleoBytes/Modan2/Modan2.db "PRAGMA integrity_check"

Useful Commands
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Development
   pytest                              # run the suite
   pytest --cov=. --cov-report=html    # coverage report
   pytest --lf                         # re-run last failures
   ruff check . && ruff format .       # lint and format
   pre-commit run --all-files          # all hooks

   # Performance
   python scripts/benchmark_analysis.py     # analysis benchmarks
   python scripts/benchmark_large_scale.py  # large-dataset benchmarks
   python scripts/profile_detailed.py       # profiling
   snakeviz benchmarks/*.prof               # view a profile

   # Database
   python migrate.py                        # run migrations

   # Build
   python build.py                          # build the executable

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
