# Modan2 Architecture Documentation

**Version**: 0.1.5-alpha.1
**Last Updated**: 2025-10-06
**Status**: Post Phase 4 Refactoring

## Overview

Modan2 is a desktop application for morphometric analysis, built with PyQt5 and following a Model-View-Controller (MVC) architecture pattern. The application supports 2D/3D landmark-based geometric morphometrics with statistical analysis capabilities.

## Project Statistics

- **Total Python Files**: 98
- **Total Lines of Code**: ~28,000
- **Main Modules**: 24
- **Dialog Modules**: 13
- **Component Modules**: 1
- **Test Files**: 30+
- **Test Coverage**: 70%+ (core modules)

## Architecture Pattern

### MVC Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         VIEW LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Modan2.py  │  │   Dialogs/   │  │ Components/  │      │
│  │ (Main Window)│  │  (13 files)  │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │              │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
┌─────────┼─────────────────┼─────────────────┼──────────────┐
│         │    CONTROLLER LAYER              │              │
│  ┌──────▼────────────────────────────────┐  │              │
│  │      ModanController.py                │  │              │
│  │  - Dataset operations                  │  │              │
│  │  - Analysis orchestration             │  │              │
│  │  - Import/Export management           │◄─┘              │
│  └──────┬────────────────────────────────┘                 │
└─────────┼──────────────────────────────────────────────────┘
          │
┌─────────┼──────────────────────────────────────────────────┐
│         │         MODEL LAYER                              │
│  ┌──────▼────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   MdModel.py  │  │MdStatistics  │  │   MdUtils    │    │
│  │  - Database   │  │   .py        │  │    .py       │    │
│  │  - ORM Models │  │  - PCA       │  │  - Helpers   │    │
│  │  - Operations │  │  - CVA       │  │  - Constants │    │
│  │               │  │  - MANOVA    │  │              │    │
│  └───────────────┘  └──────────────┘  └──────────────┘    │
└───────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. Model Layer

#### MdModel.py (3,789 lines)
**Purpose**: Database models and operations using Peewee ORM

**Key Classes**:
- `MdDataset` - Dataset model (contains multiple objects)
- `MdObject` - Individual specimen/object model
- `MdAnalysis` - Analysis results storage
- `MdImage` - Image attachments
- `MdThreeDModel` - 3D model attachments
- `MdDatasetOps` - Dataset operations (Procrustes, transformations)

**Key Responsibilities**:
- SQLite database management
- Landmark data storage and manipulation
- Procrustes superimposition
- Shape transformations (scale, rotate, translate)
- Missing landmark imputation

**Recent Optimizations**:
- Procrustes convergence threshold: 10^-10 → 10^-6 (77% faster)
- Max iteration limit: 100 (safety mechanism)

#### MdStatistics.py (634 lines)
**Purpose**: Statistical analysis functions

**Key Functions**:
- `do_pca_analysis()` - Principal Component Analysis
- `do_cva_analysis()` - Canonical Variate Analysis
- `do_manova_analysis_on_procrustes()` - MANOVA
- `calculate_procrustes_distance()` - Shape distance metrics
- `bootstrap_analysis()` - Resampling methods

**Coverage**: 95% ✅

**Performance**:
- PCA: <10ms for typical datasets
- CVA: <100ms for typical datasets
- MANOVA: <50ms for typical datasets

#### MdUtils.py (436 lines)
**Purpose**: Utility functions and constants

**Key Components**:
- File I/O (TPS, NTS, Morphologika, JSON)
- Image processing utilities
- Math helpers
- Constants and configuration

**Coverage**: 78%

### 2. Controller Layer

#### ModanController.py (1,139 lines)
**Purpose**: Business logic and workflow orchestration

**Key Methods**:
- `create_dataset()` - Dataset creation
- `import_data()` - File import workflows
- `run_analysis()` - Analysis execution
- `export_data()` - Data export
- `delete_dataset()` - Dataset management

**Coverage**: 70% ✅

**Responsibilities**:
- Coordinate between View and Model
- Validate user input
- Manage application state
- Handle errors gracefully

### 3. View Layer

#### Modan2.py (1,765 lines)
**Purpose**: Main application window

**Key Components**:
- Menu bar and toolbar
- Dataset tree view
- Object list view
- Status bar
- Keyboard shortcuts

**Qt Connections**: 80+ signal/slot connections

**Coverage**: 40%

#### Dialogs/ (13 files, 8,179 lines total)

**Architecture**:
```
dialogs/
├── base_dialog.py (116 lines)          # Base class for all dialogs
├── progress_dialog.py (74 lines)       # Progress indicator
├── calibration_dialog.py (113 lines)   # Image calibration
├── analysis_dialog.py (389 lines)      # New analysis creation
├── analysis_result_dialog.py (95 lines) # Analysis results viewer
├── dataset_dialog.py (373 lines)       # Dataset creation/editing
├── object_dialog.py (1,237 lines)      # Object creation/editing
├── import_dialog.py (474 lines)        # Multi-format import
├── export_dialog.py (431 lines)        # Multi-format export
├── preferences_dialog.py (843 lines)   # Application settings
├── data_exploration_dialog.py (2,637 lines)    # Data visualization
├── dataset_analysis_dialog.py (1,354 lines)    # Analysis management
└── __init__.py (43 lines)
```

**Common Pattern** (BaseDialog):
```python
class BaseDialog(QDialog):
    """Base class providing common dialog functionality."""

    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.setWindowTitle(title)

    def show_error(self, message, title="Error"):
        """Show error message box."""

    def show_warning(self, message, title="Warning"):
        """Show warning message box."""

    def show_info(self, message, title="Information"):
        """Show info message box."""

    def set_progress(self, value, maximum=100):
        """Update progress bar if present."""

    def with_wait_cursor(self, func):
        """Execute function with wait cursor."""
```

**Dialog Coverage**: 79% ✅

#### ModanComponents.py (4,354 lines)
**Purpose**: Custom PyQt5 widgets

**Key Components**:
- `ObjectViewer2D` - 2D landmark visualization
- `ObjectViewer3D` - 3D mesh and landmark visualization
- Custom plot widgets
- Dual list widgets
- Image viewers

**Coverage**: 26% (complex UI, lower priority)

## Data Flow

### 1. Dataset Creation Flow

```
User Action (Modan2.py)
    │
    ▼
DatasetDialog (dialogs/dataset_dialog.py)
    │
    ├─ User fills form (name, dimension, landmarks)
    ├─ Validation
    │
    ▼
ModanController.create_dataset()
    │
    ▼
MdModel.MdDataset.create()
    │
    └─ SQLite Database
```

### 2. Import Flow

```
User Action (Modan2.py)
    │
    ▼
ImportDialog (dialogs/import_dialog.py)
    │
    ├─ File selection (TPS/NTS/Morphologika/JSON)
    ├─ Auto-detect format
    ├─ Parse file
    │
    ▼
ModanController.import_data()
    │
    ├─ MdUtils.read_tps_file()
    ├─ MdUtils.read_nts_file()
    ├─ MdUtils.read_morphologika()
    │
    ▼
MdModel.MdObject.create() (for each object)
    │
    └─ SQLite Database
```

### 3. Analysis Flow

```
User Action (Modan2.py)
    │
    ▼
NewAnalysisDialog (dialogs/analysis_dialog.py)
    │
    ├─ Select analysis type (PCA/CVA/MANOVA)
    ├─ Select superimposition (Procrustes/Bookstein/None)
    ├─ Configure parameters
    │
    ▼
ModanController.run_analysis()
    │
    ├─ Load dataset
    │   └─ MdDatasetOps(dataset)
    │
    ├─ Superimposition (if selected)
    │   └─ MdDatasetOps.procrustes_superimposition()
    │       └─ 77% faster after optimization! ✅
    │
    ├─ Run analysis
    │   ├─ MdStatistics.do_pca_analysis()
    │   ├─ MdStatistics.do_cva_analysis()
    │   └─ MdStatistics.do_manova_analysis_on_procrustes()
    │
    ├─ Save results
    │   └─ MdAnalysis.create()
    │
    └─ Show results
        └─ DatasetAnalysisDialog
```

## Database Schema

### Tables

```sql
-- Dataset table
CREATE TABLE mddataset (
    id INTEGER PRIMARY KEY,
    dataset_name TEXT UNIQUE,
    dimension INTEGER,           -- 2 or 3
    landmark_count INTEGER,
    wireframe TEXT,              -- JSON array of landmark pairs
    baseline TEXT,               -- JSON array for baseline landmarks
    polygon_list TEXT,           -- JSON array of polygons
    propertyname_str TEXT,       -- Comma-separated property names
    variablename_str TEXT,       -- Comma-separated variable names
    parent_dataset_id INTEGER,   -- FK to parent dataset
    created_at DATETIME,
    updated_at DATETIME
);

-- Object table
CREATE TABLE mdobject (
    id INTEGER PRIMARY KEY,
    dataset_id INTEGER,          -- FK to dataset
    object_name TEXT,
    sequence INTEGER,
    landmark_str TEXT,           -- Newline-separated coordinates
    property_str TEXT,           -- Comma-separated property values
    variable_str TEXT,           -- Comma-separated variable values
    edge_len REAL,               -- Calibration edge length
    unit TEXT,                   -- Calibration unit
    image_id INTEGER,            -- FK to image
    threedmodel_id INTEGER,      -- FK to 3D model
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE(dataset_id, object_name)
);

-- Analysis table
CREATE TABLE mdanalysis (
    id INTEGER PRIMARY KEY,
    dataset_id INTEGER,          -- FK to dataset
    analysis_name TEXT,
    superimposition_method TEXT, -- procrustes/bookstein/resistantfit/none
    analysis_method TEXT,        -- pca/cva/manova
    baseline_point1_index INTEGER,
    baseline_point2_index INTEGER,
    calibration_factor REAL,
    pca_result TEXT,             -- JSON
    cva_result TEXT,             -- JSON
    manova_result TEXT,          -- JSON
    group_column TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

-- Image table
CREATE TABLE mdimage (
    id INTEGER PRIMARY KEY,
    object_id INTEGER,           -- FK to object
    dataset_id INTEGER,          -- FK to dataset
    file_path TEXT,
    width INTEGER,
    height INTEGER,
    created_at DATETIME
);

-- 3D Model table
CREATE TABLE mdthreedmodel (
    id INTEGER PRIMARY KEY,
    object_id INTEGER,           -- FK to object
    dataset_id INTEGER,          -- FK to dataset
    file_path TEXT,
    file_type TEXT,              -- obj/ply/stl
    created_at DATETIME
);
```

### Relationships

```
MdDataset (1) ─────< (N) MdObject
    │                      │
    │                      ├─────< (1) MdImage
    │                      └─────< (1) MdThreeDModel
    │
    └────< (N) MdAnalysis
```

## File Format Support

### Input Formats

| Format | Extension | Description | Module |
|--------|-----------|-------------|--------|
| TPS | `.tps` | Thin-plate spline format | MdUtils |
| NTS | `.nts` | NTSys format | MdUtils |
| X1Y1 | `.txt` | Simple X/Y coordinates | MdUtils |
| Morphologika | `.txt` | Morphologika v2.5 format | MdUtils |
| JSON+ZIP | `.json` | Modan2 native format with images | MdUtils |
| OBJ | `.obj` | Wavefront 3D model | objloader |
| PLY | `.ply` | Polygon file format | trimesh |
| STL | `.stl` | Stereolithography | trimesh |

### Output Formats

| Format | Extension | Description | Module |
|--------|-----------|-------------|--------|
| TPS | `.tps` | Export landmarks only | MdUtils |
| Morphologika | `.txt` | Export with metadata | MdUtils |
| JSON+ZIP | `.zip` | Complete dataset with images | MdUtils |
| CSV | `.csv` | Analysis results | pandas |

## Testing Architecture

### Test Organization

```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── test_mdmodel.py                # Database model tests (262 tests)
├── test_mdstatistics.py           # Statistical analysis tests (95% coverage)
├── test_mdutils.py                # Utility function tests
├── test_controller.py             # Controller tests (92 tests)
├── test_analysis_workflow.py      # End-to-end workflows
├── test_import.py                 # Import functionality tests
├── test_performance.py            # Performance benchmarks (skipped)
├── dialogs/
│   ├── test_base_dialog.py        # Base dialog tests
│   ├── test_analysis_dialog.py    # Analysis dialog tests
│   ├── test_calibration_dialog.py # Calibration tests
│   ├── test_dataset_dialog.py     # Dataset dialog tests
│   ├── test_export_dialog.py      # Export dialog tests
│   ├── test_import_dialog.py      # Import dialog tests
│   ├── test_object_dialog.py      # Object dialog tests
│   └── test_progress_dialog.py    # Progress dialog tests
└── [other test files...]
```

### Test Coverage (Post Phase 4)

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| MdStatistics.py | 95% | 50+ | ✅ Excellent |
| MdUtils.py | 78% | 40+ | ✅ Good |
| MdModel.py | 70% | 262 | ✅ Target Met |
| ModanController.py | 70% | 92 | ✅ Target Met |
| dialogs/ | 79% | 200+ | ✅ Good |
| ModanComponents.py | 26% | 15 | ⚠️ Low (complex UI) |
| Modan2.py | 40% | 20 | ⚠️ Moderate |

**Total**: 962 tests, 913 passing (94.9%)

### Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific module
pytest tests/test_mdmodel.py

# Run with verbose output
pytest -v

# Run performance benchmarks
pytest tests/test_performance.py -v
```

## Performance Characteristics

### Benchmarks (Post Phase 4 Optimization)

| Operation | 10 objects | 50 objects | 100 objects |
|-----------|------------|------------|-------------|
| Procrustes | 0.05s | 0.31s | 0.63s |
| PCA | <0.001s | 0.002s | 0.007s |
| CVA | 0.13s | 0.004s | 0.08s |
| MANOVA | 0.009s | 0.035s | 0.027s |

**Procrustes Optimization** (Phase 4 Week 3):
- Before: 2.6s for 50 objects
- After: 0.31s for 50 objects
- **Improvement: 88% faster**

### Performance Hotspots

**Optimized** ✅:
- Procrustes superimposition (convergence threshold optimization)

**Fast** ✅:
- PCA analysis (<10ms)
- Database queries (indexed)
- File I/O (buffered)

**To Monitor**:
- 3D rendering (complex meshes)
- Large image loading (>10MB)
- Very large datasets (>1000 objects)

## Configuration and Settings

### Application Settings (QSettings)

**Organization**: "YourOrganization"
**Application**: "Modan2"

**Stored Settings**:
```
geometry/                    # Window positions and sizes
    main_window
    analysis_result_dialog
    dataset_analysis_dialog

preferences/                 # User preferences
    remember_geometry
    default_dimension
    color_list
    marker_list

recent/                      # Recent files
    databases
    imports
```

### Environment Variables

```bash
# Qt platform plugin (Linux/WSL)
export QT_QPA_PLATFORM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt5/plugins/platforms

# Enable Qt debugging
export QT_DEBUG_PLUGINS=1

# Database location (default: ./modan.db)
export MODAN_DB_PATH=/path/to/database.db
```

## Build and Deployment

### PyInstaller Build

**Script**: `build.py`

**Configuration**:
```python
# Includes
--add-data "icons:icons"
--add-data "resources:resources"

# Excludes
--exclude-module matplotlib
--exclude-module PIL

# Options
--windowed              # No console window
--onefile              # Single executable
--icon=icons/modan.ico # Application icon
```

**Output**: `dist/Modan2.exe` (Windows) or `dist/Modan2` (Linux/Mac)

### Dependencies

**Core**:
- Python 3.12+
- PyQt5 5.15+
- numpy >= 2.0.0
- scipy
- pandas
- peewee (ORM)

**Optional**:
- opencv-python (image processing)
- trimesh (3D model loading)
- scikit-learn (additional statistics)

## Extension Points

### Adding New Analysis Methods

1. Add function to `MdStatistics.py`:
```python
def do_new_analysis(landmarks_data, **kwargs):
    """New analysis method."""
    # Implementation
    return result_dict
```

2. Update `ModanController.py`:
```python
def run_analysis(self, dataset, method, **params):
    if method == "new_analysis":
        result = MdStatistics.do_new_analysis(landmarks_data, **params)
```

3. Add UI in `NewAnalysisDialog`:
```python
self.cbxAnalysisMethod.addItem("New Analysis")
```

### Adding New File Formats

1. Add reader to `MdUtils.py`:
```python
def read_new_format(file_path):
    """Read new file format."""
    # Parse file
    return landmarks_data
```

2. Update `ImportDialog`:
```python
def _get_import_data(self, file_path):
    if file_path.endswith('.new'):
        return MdUtils.read_new_format(file_path)
```

### Adding New Dialogs

1. Create dialog in `dialogs/`:
```python
from dialogs.base_dialog import BaseDialog

class NewDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, title="New Dialog")
        self._create_widgets()
        self._create_layout()
```

2. Register in `dialogs/__init__.py`:
```python
from .new_dialog import NewDialog
__all__ = [..., 'NewDialog']
```

## Code Style and Conventions

### Naming Conventions

- **Classes**: PascalCase (e.g., `MdDataset`, `ObjectViewer2D`)
- **Functions**: snake_case (e.g., `do_pca_analysis`, `create_dataset`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_DIMENSION`)
- **Private methods**: _leading_underscore (e.g., `_create_widgets`)

### PyQt5 Conventions

- **Slots**: camelCase to match Qt convention (e.g., `onActionTriggered`)
- **Signals**: camelCase (e.g., `dataChanged`)
- **Widgets**: Prefix with type (e.g., `btnOK`, `edtName`, `cbxMethod`)

### File Organization

```python
# 1. Standard library imports
import sys
from pathlib import Path

# 2. Third-party imports
from PyQt5.QtWidgets import QDialog
import numpy as np

# 3. Local imports
import MdModel as mm
from dialogs.base_dialog import BaseDialog
```

### Documentation

**Docstrings**: Google style
```python
def function(param1, param2):
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input
    """
```

## Security Considerations

### Database

- **SQLite**: Local file-based (no network exposure)
- **Input validation**: All user inputs validated before DB insertion
- **SQL injection**: Protected by Peewee ORM parameter binding

### File Operations

- **Path validation**: All file paths validated before use
- **File type checking**: Extension and content validation
- **Size limits**: Prevent loading extremely large files

### User Data

- **Local storage only**: No network transmission
- **No telemetry**: No data collection or reporting
- **User control**: All data under user's control

## Future Considerations

### Potential Improvements

1. **Multi-threading**
   - Background analysis execution
   - Non-blocking UI during long operations
   - Progress reporting

2. **Plugin System**
   - Custom analysis methods
   - Custom file format handlers
   - User-contributed extensions

3. **Batch Processing**
   - Process multiple datasets
   - Automated workflows
   - Scripting support

4. **Cloud Features** (optional)
   - Dataset sharing
   - Collaborative analysis
   - Cloud storage integration

### Known Limitations

1. **GIL (Global Interpreter Lock)**
   - Python threading limited for CPU-bound tasks
   - Consider multiprocessing for future parallelization

2. **Memory Usage**
   - Large datasets (>1000 objects) may use significant memory
   - Consider streaming/chunking for very large data

3. **3D Rendering**
   - OpenGL dependency can be problematic on some systems
   - Consider WebGL alternative for cross-platform consistency

## References

### Internal Documentation

- `/devlog/` - Development logs and decision records
- `/docs/` - User and developer documentation
- `/benchmarks/` - Performance benchmark results
- `CLAUDE.md` - Project information for AI assistants

### External Resources

- **PyQt5**: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **Peewee ORM**: http://docs.peewee-orm.com/
- **Geometric Morphometrics**: Bookstein (1991), Rohlf & Marcus (1993)
- **Statistical Methods**: Jolliffe (2002) - PCA, Campbell & Atchley (1981) - CVA

---

**Maintained by**: Modan2 Development Team
**Last Review**: 2025-10-06 (Post Phase 4 Refactoring)
**Next Review**: After major architectural changes
