# Phase 2: 아키텍처 개선 (1개월)

**Date**: 2025-10-05
**Duration**: 1 month
**Goal**: Refactor large files and strengthen MVC architecture
**Target Coverage**: 50% → 60%
**Prerequisites**: Phase 1 completed

---

## Overview

Phase 2 focuses on breaking down massive monolithic files into manageable modules and enforcing proper separation of concerns through MVC pattern. This phase significantly improves code maintainability and testability.

---

## Critical Metrics

### Current State (Pre-Phase 2)
```
ModanDialogs.py:    7,303 lines, 11 classes, 275 methods, 21% coverage
ModanComponents.py: 4,651 lines, 16 classes, 25% coverage
MdModel.py:         2,049 lines, 9 classes, 54% coverage
Overall Coverage:   50%
```

### Target State (Post-Phase 2)
```
dialogs/*.py:       7 files, ~1,000 lines each, 35%+ coverage
components/*.py:    4 files, ~1,200 lines each, 40%+ coverage
MdModel.py:         2,049 lines, 70%+ coverage
Overall Coverage:   60%
```

---

## Tasks

### 1. ModanDialogs.py Splitting (Week 1-2)

#### 1.1 Analysis and Planning
**Priority**: 🔴 Critical
**Estimated Time**: 4 hours

**Extract Dialog Classes:**
```bash
# Count dialogs and their sizes
grep -n "^class.*Dialog" ModanDialogs.py

# Output:
# Line 48:   class NewDatasetDialog (200 lines)
# Line 250:  class EditDatasetDialog (150 lines)
# Line 550:  class NewAnalysisDialog (1,100 lines) ⚠️
# Line 1850: class DataExplorationDialog (2,800 lines) ⚠️
# Line 4650: class ExportDatasetDialog (800 lines)
# Line 5450: class ImportDatasetDialog (600 lines)
# Line 6050: class ShapeComparisonDialog (500 lines)
# ... (11 total)
```

**Create Split Plan:**
```
dialogs/
├── __init__.py                    # Export all dialogs
├── base_dialog.py                 # BaseDialog class with common functionality
├── dataset_dialogs.py             # NewDatasetDialog, EditDatasetDialog
├── analysis_dialog.py             # NewAnalysisDialog (1,100 lines)
├── data_exploration.py            # DataExplorationDialog (2,800 lines) ⚠️ Largest
├── export_dialog.py               # ExportDatasetDialog
├── import_dialog.py               # ImportDatasetDialog
└── comparison_dialog.py           # ShapeComparisonDialog, etc.
```

---

#### 1.2 Extract Common Base Class
**Priority**: 🔴 Critical
**Estimated Time**: 6 hours

**Create `dialogs/base_dialog.py`:**
```python
"""Base dialog class with common functionality."""
from PyQt5.QtWidgets import QDialog, QMessageBox, QProgressBar
from PyQt5.QtCore import Qt
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BaseDialog(QDialog):
    """Base class for all Modan2 dialogs.

    Provides common functionality:
    - Progress bar handling
    - Error message display
    - Wait cursor management
    - Standard button layout
    """

    def __init__(self, parent=None, title: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.progress_bar: Optional[QProgressBar] = None

    def show_error(self, message: str, title: str = "Error"):
        """Display error message dialog."""
        QMessageBox.critical(self, title, message)
        logger.error(f"{title}: {message}")

    def show_warning(self, message: str, title: str = "Warning"):
        """Display warning message dialog."""
        QMessageBox.warning(self, title, message)
        logger.warning(f"{title}: {message}")

    def show_info(self, message: str, title: str = "Information"):
        """Display information message dialog."""
        QMessageBox.information(self, title, message)
        logger.info(f"{title}: {message}")

    def set_progress(self, value: int, maximum: int = 100):
        """Update progress bar."""
        if self.progress_bar:
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(value)

    def with_wait_cursor(self, func):
        """Execute function with wait cursor."""
        from PyQt5.QtWidgets import QApplication
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            return func()
        finally:
            QApplication.restoreOverrideCursor()
```

**Common UI Components:**
```python
class BaseDialog(QDialog):
    # ... (previous methods)

    def create_button_box(self, ok_text: str = "OK", cancel_text: str = "Cancel"):
        """Create standard OK/Cancel button box."""
        from PyQt5.QtWidgets import QHBoxLayout, QPushButton

        layout = QHBoxLayout()

        self.btn_ok = QPushButton(ok_text)
        self.btn_ok.clicked.connect(self.accept)

        self.btn_cancel = QPushButton(cancel_text)
        self.btn_cancel.clicked.connect(self.reject)

        layout.addStretch()
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_cancel)

        return layout
```

---

#### 1.3 Split NewAnalysisDialog
**Priority**: 🟡 High
**Estimated Time**: 8 hours
**File**: `dialogs/analysis_dialog.py` (1,100 lines)

**Steps:**

1. **Create new file:**
   ```python
   """New Analysis Dialog - Create and run statistical analyses."""
   from PyQt5.QtWidgets import (
       QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
       QProgressBar, QLabel
   )
   from PyQt5.QtCore import pyqtSignal

   from dialogs.base_dialog import BaseDialog
   from ModanController import ModanController
   from MdModel import MdDataset
   import logging

   logger = logging.getLogger(__name__)


   class NewAnalysisDialog(BaseDialog):
       """Dialog for creating new analysis."""

       analysis_completed = pyqtSignal(object)  # Emits MdAnalysis

       def __init__(self, dataset: MdDataset, controller: ModanController, parent=None):
           super().__init__(parent, title="New Analysis")
           self.dataset = dataset
           self.controller = controller
           self.setup_ui()
           self.connect_signals()

       def setup_ui(self):
           """Initialize UI components."""
           # ... (extract from original)

       def connect_signals(self):
           """Connect controller signals."""
           self.controller.analysis_started.connect(self.on_analysis_started)
           self.controller.analysis_progress.connect(self.on_analysis_progress)
           # ...
   ```

2. **Move code from ModanDialogs.py:**
   - Copy class definition
   - Update imports
   - Update base class to `BaseDialog`
   - Test thoroughly

3. **Update imports in dependent files:**
   ```python
   # Before (in Modan2.py)
   from ModanDialogs import NewAnalysisDialog

   # After
   from dialogs import NewAnalysisDialog
   ```

---

#### 1.4 Split DataExplorationDialog
**Priority**: 🔴 Critical
**Estimated Time**: 16 hours
**File**: `dialogs/data_exploration.py` (2,800 lines - LARGEST)

**Challenge**: This is the largest single class. May need sub-splitting.

**Analysis:**
```python
class DataExplorationDialog:
    # Sections:
    # 1. Initialization (100 lines)
    # 2. UI Setup (400 lines)
    # 3. Plot Management (800 lines)  ← Extract to PlotManager
    # 4. Data Table (600 lines)       ← Extract to DataTableWidget
    # 5. Analysis Controls (500 lines)
    # 6. Export Functions (400 lines)  ← Extract to ExportManager
```

**Refactored Structure:**
```
dialogs/
├── data_exploration/
│   ├── __init__.py
│   ├── main_dialog.py         # DataExplorationDialog (800 lines)
│   ├── plot_manager.py        # PlotManager class (800 lines)
│   ├── data_table.py          # DataTableWidget (600 lines)
│   └── export_manager.py      # ExportManager (400 lines)
```

**Example - Extract PlotManager:**
```python
# dialogs/data_exploration/plot_manager.py
"""Manages plots in Data Exploration Dialog."""
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from typing import List, Dict, Any
import numpy as np


class PlotManager:
    """Handles all plotting operations for data exploration."""

    def __init__(self, canvas: FigureCanvas):
        self.canvas = canvas
        self.figure = canvas.figure
        self.current_plot = None

    def plot_pca_2d(self, scores: np.ndarray, groups: List[str]):
        """Plot 2D PCA scatter plot."""
        ax = self.figure.add_subplot(111)
        # ... plotting logic

    def plot_pca_3d(self, scores: np.ndarray, groups: List[str]):
        """Plot 3D PCA scatter plot."""
        # ...

    def plot_wireframe(self, landmarks: List[List[float]]):
        """Plot landmark wireframe."""
        # ...

    def clear(self):
        """Clear all plots."""
        self.figure.clear()
        self.canvas.draw()
```

---

#### 1.5 Split Remaining Dialogs
**Priority**: 🟡 High
**Estimated Time**: 12 hours

**Split Plan:**

1. **`dialogs/dataset_dialogs.py`** (350 lines)
   - `NewDatasetDialog`
   - `EditDatasetDialog`

2. **`dialogs/export_dialog.py`** (800 lines)
   - `ExportDatasetDialog`
   - Format handlers

3. **`dialogs/import_dialog.py`** (600 lines)
   - `ImportDatasetDialog`
   - File parsers

4. **`dialogs/comparison_dialog.py`** (500 lines)
   - `ShapeComparisonDialog`
   - Other utility dialogs

---

#### 1.6 Create dialogs/__init__.py
**Priority**: 🟡 High
**Estimated Time**: 1 hour

**File**: `dialogs/__init__.py`
```python
"""Modan2 Dialog Modules.

This package contains all dialog classes for the application.
"""

from dialogs.base_dialog import BaseDialog
from dialogs.analysis_dialog import NewAnalysisDialog
from dialogs.dataset_dialogs import NewDatasetDialog, EditDatasetDialog
from dialogs.export_dialog import ExportDatasetDialog
from dialogs.import_dialog import ImportDatasetDialog
from dialogs.comparison_dialog import ShapeComparisonDialog

# Data Exploration (sub-package)
from dialogs.data_exploration import DataExplorationDialog

__all__ = [
    "BaseDialog",
    "NewAnalysisDialog",
    "NewDatasetDialog",
    "EditDatasetDialog",
    "ExportDatasetDialog",
    "ImportDatasetDialog",
    "ShapeComparisonDialog",
    "DataExplorationDialog",
]
```

---

### 2. ModanComponents.py Splitting (Week 2-3)

#### 2.1 Analysis and Planning
**Priority**: 🟡 High
**Estimated Time**: 3 hours

**Component Categories:**
```bash
# Analyze components
grep -n "^class " ModanComponents.py

# Categories:
# 1. Viewers: ObjectViewer2D, ObjectViewer3D (2,000 lines)
# 2. Widgets: Custom UI widgets (1,500 lines)
# 3. File Handlers: TPS, NTS, X1Y1, Morphologika (800 lines)
# 4. Helpers: ShapePreference, etc. (350 lines)
```

**Split Plan:**
```
components/
├── __init__.py
├── viewers/
│   ├── __init__.py
│   ├── viewer_2d.py           # ObjectViewer2D (1,000 lines)
│   └── viewer_3d.py           # ObjectViewer3D (1,000 lines)
├── widgets/
│   ├── __init__.py
│   ├── landmark_table.py
│   ├── variable_table.py
│   └── custom_controls.py
└── file_handlers/
    ├── __init__.py
    ├── tps.py                  # TPS format
    ├── nts.py                  # NTS format
    ├── morphologika.py         # Morphologika format
    └── x1y1.py                 # X1Y1 format
```

---

#### 2.2 Extract ObjectViewer2D
**Priority**: 🔴 Critical
**Estimated Time**: 8 hours
**File**: `components/viewers/viewer_2d.py`

**Steps:**
1. Create new file structure
2. Move `ObjectViewer2D` class
3. Extract dependencies
4. Update imports

**Example:**
```python
# components/viewers/viewer_2d.py
"""2D Object Viewer Component."""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, pyqtSignal
from typing import List, Optional
import numpy as np

from MdModel import MdObject


class ObjectViewer2D(QWidget):
    """Widget for displaying 2D landmark data."""

    landmark_clicked = pyqtSignal(int)  # Emits landmark index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.obj: Optional[MdObject] = None
        self.zoom = 1.0
        self.offset = [0, 0]

    def set_object(self, obj: MdObject):
        """Set object to display."""
        self.obj = obj
        self.update()

    def paintEvent(self, event):
        """Render landmarks and wireframe."""
        if not self.obj:
            return

        painter = QPainter(self)
        self._draw_landmarks(painter)
        self._draw_wireframe(painter)

    def _draw_landmarks(self, painter: QPainter):
        """Draw landmark points."""
        # ... (extract from original)
```

---

#### 2.3 Extract File Format Handlers
**Priority**: 🟢 Medium
**Estimated Time**: 6 hours

**Current State:**
```python
# All in ModanComponents.py
class TPS:
    def read(filename): ...
    def write(filename, data): ...

class NTS:
    def read(filename): ...
    def write(filename, data): ...
```

**New Structure:**
```python
# components/file_handlers/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class FileFormatHandler(ABC):
    """Abstract base class for file format handlers."""

    @abstractmethod
    def read(self, filename: str) -> Dict[str, Any]:
        """Read file and return parsed data."""
        pass

    @abstractmethod
    def write(self, filename: str, data: Dict[str, Any]):
        """Write data to file."""
        pass

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate data structure."""
        pass


# components/file_handlers/tps.py
from .base import FileFormatHandler

class TPSHandler(FileFormatHandler):
    """TPS file format handler."""

    def read(self, filename: str) -> Dict[str, Any]:
        """Read TPS file."""
        # ... (extract from original TPS class)

    def write(self, filename: str, data: Dict[str, Any]):
        """Write TPS file."""
        # ...
```

---

### 3. MVC Pattern Enforcement (Week 3)

#### 3.1 Move Business Logic to Controller
**Priority**: 🔴 Critical
**Estimated Time**: 12 hours

**Current Problem:**
```python
# dialogs/data_exploration.py (BAD)
class DataExplorationDialog(BaseDialog):
    def perform_pca(self):
        # Business logic in UI! ❌
        landmarks = self.get_landmarks()
        result = MdStatistics.do_pca_analysis(landmarks)
        self.display_results(result)
```

**Solution:**
```python
# ModanController.py (GOOD)
class ModanController:
    def run_pca_for_exploration(
        self,
        dataset: MdDataset,
        n_components: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run PCA analysis for data exploration."""
        # Extract landmarks
        landmarks = self._extract_landmarks(dataset)

        # Run analysis
        result = MdStatistics.do_pca_analysis(landmarks, n_components)

        # Emit signals
        self.analysis_completed.emit("PCA", result)

        return result

# dialogs/data_exploration.py (GOOD)
class DataExplorationDialog(BaseDialog):
    def perform_pca(self):
        # Just coordinate! ✅
        result = self.controller.run_pca_for_exploration(
            dataset=self.dataset,
            n_components=self.get_n_components()
        )
        self.display_results(result)
```

**Refactoring Checklist:**
- [ ] Move all MdStatistics calls to Controller
- [ ] Move all MdModel database operations to Controller
- [ ] Dialogs only handle UI and user input
- [ ] Controller emits signals for UI updates

---

#### 3.2 Implement Dependency Injection
**Priority**: 🟡 High
**Estimated Time**: 8 hours

**Current (Tight Coupling):**
```python
class NewAnalysisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dataset = MdDataset.get_by_id(1)  # ❌ Direct DB access
        self.controller = ModanController()     # ❌ Creates own controller
```

**Improved (Dependency Injection):**
```python
class NewAnalysisDialog(BaseDialog):
    def __init__(
        self,
        dataset: MdDataset,              # ✅ Injected
        controller: ModanController,     # ✅ Injected
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent, title="New Analysis")
        self.dataset = dataset
        self.controller = controller
        self.setup_ui()
```

**Benefits:**
- Easier testing (can inject mocks)
- Clearer dependencies
- Better separation of concerns

---

### 4. Testing Improvements (Week 4)

#### 4.1 Test New Dialog Modules
**Priority**: 🔴 Critical
**Estimated Time**: 16 hours

**Test Structure:**
```
tests/
├── dialogs/
│   ├── __init__.py
│   ├── test_base_dialog.py
│   ├── test_analysis_dialog.py
│   ├── test_dataset_dialogs.py
│   ├── test_export_dialog.py
│   └── test_data_exploration.py
└── components/
    ├── __init__.py
    ├── test_viewer_2d.py
    ├── test_viewer_3d.py
    └── test_file_handlers.py
```

**Example Test:**
```python
# tests/dialogs/test_analysis_dialog.py
import pytest
from unittest.mock import Mock, MagicMock
from PyQt5.QtWidgets import QApplication

from dialogs import NewAnalysisDialog
from MdModel import MdDataset
from ModanController import ModanController


@pytest.fixture
def qtapp(qapp):
    """Ensure Qt application exists."""
    return qapp


@pytest.fixture
def mock_dataset():
    """Create mock dataset."""
    dataset = Mock(spec=MdDataset)
    dataset.id = 1
    dataset.dataset_name = "Test Dataset"
    dataset.dimension = 2
    return dataset


@pytest.fixture
def mock_controller():
    """Create mock controller."""
    controller = Mock(spec=ModanController)
    controller.analysis_started = Mock()
    controller.analysis_completed = Mock()
    return controller


def test_dialog_initialization(qtapp, mock_dataset, mock_controller):
    """Test dialog initializes correctly."""
    dialog = NewAnalysisDialog(
        dataset=mock_dataset,
        controller=mock_controller
    )

    assert dialog.dataset == mock_dataset
    assert dialog.controller == mock_controller
    assert dialog.windowTitle() == "New Analysis"


def test_dialog_start_analysis(qtapp, mock_dataset, mock_controller):
    """Test starting analysis."""
    dialog = NewAnalysisDialog(mock_dataset, mock_controller)

    # Simulate user input
    dialog.edtAnalysisName.setText("Test Analysis")

    # Trigger analysis
    dialog.btnOK_clicked()

    # Verify controller called
    mock_controller.run_analysis.assert_called_once()
```

---

#### 4.2 Increase MdModel.py Coverage: 54% → 70%
**Priority**: 🟡 High
**Estimated Time**: 10 hours

**Focus on MdDatasetOps:**
```python
# tests/test_mdmodel.py

class TestMdDatasetOps:
    """Test MdDatasetOps methods."""

    def test_procrustes_superimposition(self, sample_dataset):
        """Test Procrustes alignment."""
        ops = MdDatasetOps(sample_dataset)
        result = ops.procrustes_superimposition()

        assert result is True
        # Verify objects are aligned
        for obj in ops.object_list:
            centroid = obj.get_centroid()
            assert abs(centroid[0]) < 1e-10  # Centered
            assert abs(centroid[1]) < 1e-10

    def test_get_average_shape(self, sample_dataset):
        """Test average shape calculation."""
        ops = MdDatasetOps(sample_dataset)
        ops.procrustes_superimposition()

        avg_shape = ops.get_average_shape()

        assert avg_shape is not None
        assert len(avg_shape.landmark_list) == sample_dataset.landmark_count

    def test_missing_landmark_imputation(self, dataset_with_missing):
        """Test missing landmark handling."""
        ops = MdDatasetOps(dataset_with_missing)

        # Should use imputation method
        result = ops.procrustes_superimposition()

        assert result is True
        # Verify missing landmarks imputed
        # ...
```

**Target Lines:**
- 1064-1222: MdDatasetOps methods
- 1438-1883: MdObjectOps methods
- File operations: 611-728

---

#### 4.3 Integration Tests for Refactored Modules
**Priority**: 🟢 Medium
**Estimated Time**: 8 hours

**Test Scenarios:**
```python
# tests/integration/test_analysis_workflow.py

def test_complete_analysis_workflow(qtbot, tmp_path):
    """Test complete analysis from dataset to export."""
    # 1. Create dataset
    dataset = create_test_dataset(tmp_path)

    # 2. Initialize controller
    controller = ModanController()
    controller.set_current_dataset(dataset)

    # 3. Run analysis
    analysis = controller.run_analysis(
        dataset=dataset,
        analysis_name="Integration Test",
        superimposition_method="Procrustes"
    )

    assert analysis is not None
    assert analysis.pca_analysis_result_json is not None

    # 4. Open data exploration
    dialog = DataExplorationDialog(analysis, controller)
    qtbot.addWidget(dialog)

    # 5. Export results
    export_path = tmp_path / "export.xlsx"
    dialog.export_to_excel(str(export_path))

    assert export_path.exists()
```

---

### 5. Documentation Updates (Week 4)

#### 5.1 Update Architecture Docs
**Priority**: 🟡 High
**Estimated Time**: 4 hours

**Create `docs/ARCHITECTURE.md`:**
```markdown
# Modan2 Architecture

## Overview

Modan2 follows an MVC (Model-View-Controller) architecture with PyQt5.

## Directory Structure

```
modan2/
├── dialogs/              # View layer (dialogs)
│   ├── base_dialog.py   # Base class
│   └── ...              # Specific dialogs
├── components/           # View layer (widgets)
│   ├── viewers/         # 2D/3D viewers
│   ├── widgets/         # Custom widgets
│   └── file_handlers/   # File I/O
├── ModanController.py    # Controller layer
├── MdModel.py           # Model layer (database)
├── MdStatistics.py      # Business logic (statistics)
└── MdUtils.py           # Utilities

## Design Patterns

### Model-View-Controller (MVC)

- **Model**: `MdModel.py` - Database entities (Peewee ORM)
- **View**: `dialogs/`, `components/` - PyQt5 UI
- **Controller**: `ModanController.py` - Business logic coordinator

### Dependency Injection

All dialogs receive dependencies via constructor:

```python
dialog = NewAnalysisDialog(
    dataset=current_dataset,      # Injected
    controller=main_controller    # Injected
)
```

### Signal-Slot Pattern

Controller emits signals for async operations:

```python
# Controller
self.analysis_started.emit("PCA")
self.analysis_progress.emit(50)
self.analysis_completed.emit(result)

# Dialog
controller.analysis_progress.connect(self.on_progress)
```
```

---

#### 5.2 Update CLAUDE.md
**Priority**: 🟡 High
**Estimated Time**: 2 hours

**Add sections:**
```markdown
## Project Structure (Updated)

### Core Modules
- `dialogs/` - PyQt5 dialog classes (7 files)
  - `base_dialog.py` - Common dialog functionality
  - `analysis_dialog.py` - Analysis creation/execution
  - `data_exploration/` - Data exploration (sub-package)
- `components/` - Custom PyQt5 widgets (organized by type)
  - `viewers/` - 2D/3D object viewers
  - `widgets/` - Custom UI controls
  - `file_handlers/` - File format readers/writers

### Removed Files
- ~~`Modan2_original.py`~~ - Removed in Phase 1
- ~~`test_script/`~~ - Replaced by pytest suite
```

---

## Deliverables

### Code Refactoring
- [ ] ModanDialogs.py split into 7 files (~1,000 lines each)
- [ ] ModanComponents.py split into 4 packages
- [ ] BaseDialog class created with common functionality
- [ ] All business logic moved to Controller
- [ ] Dependency injection implemented

### File Structure
```
New:
├── dialogs/
│   ├── __init__.py
│   ├── base_dialog.py (300 lines)
│   ├── analysis_dialog.py (1,100 lines)
│   ├── dataset_dialogs.py (350 lines)
│   ├── export_dialog.py (800 lines)
│   ├── import_dialog.py (600 lines)
│   ├── comparison_dialog.py (500 lines)
│   └── data_exploration/
│       ├── __init__.py
│       ├── main_dialog.py (800 lines)
│       ├── plot_manager.py (800 lines)
│       ├── data_table.py (600 lines)
│       └── export_manager.py (400 lines)
└── components/
    ├── __init__.py
    ├── viewers/
    │   ├── viewer_2d.py (1,000 lines)
    │   └── viewer_3d.py (1,000 lines)
    ├── widgets/
    │   └── ... (custom widgets)
    └── file_handlers/
        ├── base.py
        ├── tps.py
        ├── nts.py
        └── ... (format handlers)

Removed:
- ModanDialogs.py (7,303 lines) → Split
- ModanComponents.py (4,651 lines) → Split
```

### Testing
- [ ] Coverage: 50% → 60%
- [ ] Dialog tests: 35%+ coverage each
- [ ] MdModel.py: 54% → 70%
- [ ] Integration tests for refactored workflows

### Documentation
- [ ] ARCHITECTURE.md created
- [ ] CLAUDE.md updated
- [ ] Inline documentation improved
- [ ] Migration guide for developers

---

## Success Criteria

1. ✅ No file >2,000 lines (except legacy)
2. ✅ All dialogs inherit from BaseDialog
3. ✅ Zero business logic in dialog classes
4. ✅ All dependencies injected via constructor
5. ✅ Coverage increased to 60%+
6. ✅ All existing features work unchanged
7. ✅ Build time <3 minutes
8. ✅ Test suite runs in <60 seconds

---

## Risks & Mitigation

### Risk 1: Import Errors After Split
**Impact**: High
**Mitigation**:
- Update all imports incrementally
- Run test suite after each file split
- Use IDE refactoring tools

### Risk 2: Breaking Existing Code
**Impact**: Critical
**Mitigation**:
- Feature branches for each major split
- Comprehensive testing before merge
- Keep original files until verified

### Risk 3: Merge Conflicts
**Impact**: Medium
**Mitigation**:
- Coordinate team commits
- Split work into smaller PRs
- Use feature toggles if needed

### Risk 4: Time Overrun
**Impact**: Medium
**Mitigation**:
- Prioritize critical files (DataExplorationDialog first)
- Can extend some tasks to Phase 3
- Regular progress reviews

---

## Migration Guide

### For Developers

**Before:**
```python
from ModanDialogs import NewAnalysisDialog, DataExplorationDialog

dialog = NewAnalysisDialog()
dialog.exec_()
```

**After:**
```python
from dialogs import NewAnalysisDialog, DataExplorationDialog

dialog = NewAnalysisDialog(
    dataset=current_dataset,
    controller=main_controller
)
dialog.exec_()
```

### Updating Existing Code

1. **Replace imports:**
   ```bash
   # Use sed or find-replace
   sed -i 's/from ModanDialogs import/from dialogs import/g' *.py
   ```

2. **Add dependency injection:**
   - Pass `dataset` and `controller` to all dialogs
   - Remove direct database access from dialogs

3. **Update tests:**
   - Use `pytest-qt` fixtures
   - Mock controller methods
   - Test UI behavior, not business logic

---

## Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | ModanDialogs split (Part 1) | BaseDialog, 3 dialog files |
| **Week 2** | ModanDialogs split (Part 2) | DataExplorationDialog, remaining dialogs |
| **Week 3** | ModanComponents split + MVC | Components package, business logic moved |
| **Week 4** | Testing + Documentation | Tests, docs, final verification |

---

## Next Steps

After Phase 2 completion:
- **Phase 3**: Advanced testing (UI tests, CI/CD, performance optimization)

---

**Status**: 📝 Planning
**Dependencies**: Phase 1 must be completed first
**Owner**: Development Team
**Last Updated**: 2025-10-05
