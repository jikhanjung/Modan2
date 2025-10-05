# Phase 3: 테스트 강화 및 CI/CD (1개월)

**Date**: 2025-10-05
**Duration**: 1 month
**Goal**: Comprehensive testing infrastructure and continuous integration
**Target Coverage**: 60% → 70%+
**Prerequisites**: Phase 1 and Phase 2 completed

---

## Overview

Phase 3 focuses on building a robust testing infrastructure including UI tests, integration tests, performance tests, and automated CI/CD pipeline. This phase ensures long-term code quality and prevents regressions.

---

## Critical Metrics

### Current State (Pre-Phase 3)
```
Overall Coverage:      60%
UI Coverage:          35% (dialogs/, components/)
Integration Tests:     Limited
CI/CD:                None
Performance Tests:     Minimal
```

### Target State (Post-Phase 3)
```
Overall Coverage:      70%+
UI Coverage:          50%+
Integration Tests:     Comprehensive
CI/CD:                Full pipeline (test, lint, build)
Performance Tests:     Benchmarks established
```

---

## Tasks

### 1. UI Testing with pytest-qt (Week 1-2)

#### 1.1 Setup pytest-qt Infrastructure
**Priority**: 🔴 Critical
**Estimated Time**: 4 hours

**Install Dependencies:**
```bash
pip install pytest-qt pytest-xvfb
```

**Configure pytest:**
Update `config/pytest.ini`:
```ini
[pytest]
qt_api = pyqt5

# Qt testing options
qt_log_level_fail = CRITICAL
qt_log_ignore =
    QWindowsWindow::setGeometry
    QXcbConnection

# Timeout for Qt tests
timeout = 300

# Use xvfb on headless systems (CI)
markers =
    gui: GUI tests requiring display
    slow: Slow tests (>5 seconds)
```

**Create Qt Fixtures:**
```python
# tests/conftest.py (update existing)
import pytest
from PyQt5.QtWidgets import QApplication
from ModanController import ModanController


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for all tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def qtbot(qapp, qtbot):
    """Enhanced qtbot with custom helpers."""
    return qtbot


@pytest.fixture
def mock_controller():
    """Create mock controller for UI tests."""
    from unittest.mock import Mock
    controller = Mock(spec=ModanController)
    # Setup common signals
    controller.analysis_started = Mock()
    controller.analysis_progress = Mock()
    controller.analysis_completed = Mock()
    return controller
```

---

#### 1.2 Test Dialog Initialization
**Priority**: 🔴 Critical
**Estimated Time**: 8 hours

**Test Structure:**
```python
# tests/dialogs/test_analysis_dialog.py
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit

from dialogs import NewAnalysisDialog


class TestNewAnalysisDialog:
    """Test suite for NewAnalysisDialog."""

    @pytest.fixture
    def dialog(self, qtbot, sample_dataset, mock_controller):
        """Create dialog instance."""
        dlg = NewAnalysisDialog(
            dataset=sample_dataset,
            controller=mock_controller
        )
        qtbot.addWidget(dlg)
        return dlg

    def test_initialization(self, dialog, sample_dataset):
        """Test dialog initializes with correct data."""
        assert dialog.dataset == sample_dataset
        assert dialog.windowTitle() == "New Analysis"
        assert dialog.edtAnalysisName is not None

    def test_ui_elements_present(self, dialog):
        """Test all UI elements are created."""
        # Input fields
        assert isinstance(dialog.edtAnalysisName, QLineEdit)
        assert dialog.comboSuperimposition is not None
        assert dialog.comboCvaGroupBy is not None

        # Buttons
        assert dialog.btnOK is not None
        assert dialog.btnCancel is not None

    def test_default_values(self, dialog):
        """Test default values are set correctly."""
        assert dialog.comboSuperimposition.currentText() == "Procrustes"
        assert dialog.progressBar.isHidden()

    def test_validation_empty_name(self, qtbot, dialog):
        """Test validation fails with empty analysis name."""
        dialog.edtAnalysisName.setText("")

        # Click OK
        qtbot.mouseClick(dialog.btnOK, Qt.LeftButton)

        # Should show warning (dialog not accepted)
        assert not dialog.result()

    def test_validation_valid_input(self, qtbot, dialog, mock_controller):
        """Test validation passes with valid input."""
        dialog.edtAnalysisName.setText("Test Analysis")

        # Click OK
        qtbot.mouseClick(dialog.btnOK, Qt.LeftButton)

        # Should call controller
        mock_controller.run_analysis.assert_called_once()

    def test_cancel_button(self, qtbot, dialog):
        """Test cancel button closes dialog."""
        qtbot.mouseClick(dialog.btnCancel, Qt.LeftButton)
        assert dialog.result() == 0  # Rejected

    def test_progress_updates(self, qtbot, dialog, mock_controller):
        """Test progress bar updates during analysis."""
        # Simulate progress signal
        dialog.on_analysis_progress(25)
        assert dialog.progressBar.value() == 25
        assert dialog.progressBar.isVisible()

        dialog.on_analysis_progress(100)
        assert dialog.progressBar.value() == 100
```

---

#### 1.3 Test User Interactions
**Priority**: 🟡 High
**Estimated Time**: 12 hours

**Button Click Tests:**
```python
# tests/dialogs/test_data_exploration.py
import pytest
from PyQt5.QtCore import Qt


class TestDataExplorationDialog:
    """Test data exploration dialog interactions."""

    def test_tab_switching(self, qtbot, exploration_dialog):
        """Test switching between tabs."""
        # Initial tab
        assert exploration_dialog.tabWidget.currentIndex() == 0

        # Switch to wireframe tab
        exploration_dialog.tabWidget.setCurrentIndex(1)
        qtbot.wait(100)  # Let UI update

        assert exploration_dialog.current_plot_type == "wireframe"

    def test_plot_type_change(self, qtbot, exploration_dialog):
        """Test changing plot type updates visualization."""
        # Select 3D plot
        exploration_dialog.comboPlotType.setCurrentText("3D Scatter")
        qtbot.wait(100)

        # Verify plot updated
        assert exploration_dialog.plot_manager.current_plot == "3d_scatter"

    def test_group_by_selection(self, qtbot, exploration_dialog):
        """Test group-by variable selection."""
        # Select grouping variable
        exploration_dialog.comboGroupBy.setCurrentIndex(1)
        qtbot.wait(100)

        # Verify groups updated in plot
        assert len(exploration_dialog.plot_manager.groups) > 0

    def test_export_button(self, qtbot, exploration_dialog, tmp_path):
        """Test export functionality."""
        export_path = tmp_path / "export.png"

        # Mock file dialog
        with qtbot.waitSignal(exploration_dialog.export_completed):
            exploration_dialog.export_plot(str(export_path))

        assert export_path.exists()
```

**Keyboard Shortcuts:**
```python
def test_keyboard_shortcuts(self, qtbot, exploration_dialog):
    """Test keyboard shortcuts work."""
    # Ctrl+S to save
    qtbot.keyClick(exploration_dialog, Qt.Key_S, Qt.ControlModifier)
    # Should trigger save dialog

    # Ctrl+W to close
    qtbot.keyClick(exploration_dialog, Qt.Key_W, Qt.ControlModifier)
    assert not exploration_dialog.isVisible()
```

---

#### 1.4 Test Widget Rendering
**Priority**: 🟡 High
**Estimated Time**: 10 hours

**Viewer Tests:**
```python
# tests/components/test_viewer_2d.py
import pytest
import numpy as np
from PyQt5.QtCore import Qt, QPoint

from components.viewers import ObjectViewer2D
from MdModel import MdObject


class TestObjectViewer2D:
    """Test 2D object viewer."""

    @pytest.fixture
    def viewer(self, qtbot):
        """Create viewer widget."""
        widget = ObjectViewer2D()
        qtbot.addWidget(widget)
        widget.show()
        return widget

    @pytest.fixture
    def sample_object(self):
        """Create sample object with landmarks."""
        obj = MdObject.create(
            object_name="Test",
            landmark_str="0\t0\n1\t0\n0\t1"
        )
        obj.unpack_landmark()
        return obj

    def test_set_object(self, viewer, sample_object):
        """Test setting object updates viewer."""
        viewer.set_object(sample_object)

        assert viewer.obj == sample_object
        assert len(viewer.landmarks) == 3

    def test_zoom_in(self, qtbot, viewer, sample_object):
        """Test zoom in functionality."""
        viewer.set_object(sample_object)
        initial_zoom = viewer.zoom

        # Wheel up = zoom in
        qtbot.mouseMove(viewer, QPoint(100, 100))
        qtbot.mouseWheel(viewer, Qt.MouseButton.NoButton, delta=120)

        assert viewer.zoom > initial_zoom

    def test_zoom_out(self, qtbot, viewer, sample_object):
        """Test zoom out functionality."""
        viewer.set_object(sample_object)
        initial_zoom = viewer.zoom

        # Wheel down = zoom out
        qtbot.mouseWheel(viewer, Qt.MouseButton.NoButton, delta=-120)

        assert viewer.zoom < initial_zoom

    def test_pan(self, qtbot, viewer, sample_object):
        """Test panning with mouse drag."""
        viewer.set_object(sample_object)
        initial_offset = viewer.offset[:]

        # Simulate drag
        qtbot.mousePress(viewer, Qt.LeftButton, pos=QPoint(100, 100))
        qtbot.mouseMove(viewer, QPoint(150, 150))
        qtbot.mouseRelease(viewer, Qt.LeftButton, pos=QPoint(150, 150))

        assert viewer.offset != initial_offset

    def test_landmark_click(self, qtbot, viewer, sample_object):
        """Test clicking on landmark emits signal."""
        viewer.set_object(sample_object)

        with qtbot.waitSignal(viewer.landmark_clicked, timeout=1000) as blocker:
            # Click on first landmark (approx position)
            qtbot.mouseClick(viewer, Qt.LeftButton, pos=QPoint(100, 100))

        # Verify correct landmark index emitted
        assert blocker.args[0] >= 0
```

---

### 2. Integration Testing (Week 2-3)

#### 2.1 Full Workflow Tests
**Priority**: 🔴 Critical
**Estimated Time**: 12 hours

**Test Complete Analysis Pipeline:**
```python
# tests/integration/test_complete_workflow.py
import pytest
from pathlib import Path

from ModanController import ModanController
from MdModel import MdDataset, MdObject, MdAnalysis


class TestCompleteAnalysisWorkflow:
    """Test complete analysis from import to export."""

    @pytest.fixture
    def controller(self, test_db):
        """Create controller with test database."""
        return ModanController()

    @pytest.fixture
    def tps_file(self, tmp_path):
        """Create sample TPS file."""
        tps_content = """LM=3
0.0 0.0
1.0 0.0
0.0 1.0
IMAGE=sample1.jpg
ID=1

LM=3
0.1 0.1
1.1 0.1
0.1 1.1
IMAGE=sample2.jpg
ID=2
"""
        file_path = tmp_path / "test.tps"
        file_path.write_text(tps_content)
        return file_path

    def test_import_to_analysis_workflow(
        self, controller, tps_file, tmp_path
    ):
        """Test: Import → Procrustes → PCA → Export."""

        # 1. Import TPS file
        dataset = controller.import_dataset(
            file_path=str(tps_file),
            dataset_name="Integration Test",
            format="tps"
        )

        assert dataset is not None
        assert dataset.object_list.count() == 2

        # 2. Run analysis
        analysis = controller.run_analysis(
            dataset=dataset,
            analysis_name="Test Analysis",
            superimposition_method="Procrustes"
        )

        assert analysis is not None
        assert analysis.pca_analysis_result_json is not None

        # 3. Verify PCA results
        import json
        pca_scores = json.loads(analysis.pca_analysis_result_json)
        assert len(pca_scores) == 2  # 2 objects
        assert len(pca_scores[0]) > 0  # Has PC scores

        # 4. Export results
        export_path = tmp_path / "results.xlsx"
        controller.export_analysis_results(
            analysis=analysis,
            output_path=str(export_path),
            format="xlsx"
        )

        assert export_path.exists()
        assert export_path.stat().st_size > 0

    def test_missing_landmark_workflow(
        self, controller, tmp_path
    ):
        """Test workflow with missing landmarks."""

        # Create dataset with missing data
        dataset = MdDataset.create(
            dataset_name="Missing Data Test",
            dimension=2
        )

        # Object 1: Complete
        obj1 = MdObject.create(
            dataset=dataset,
            object_name="Complete",
            landmark_str="0\t0\n1\t0\n0\t1"
        )

        # Object 2: Missing landmark 2
        obj2 = MdObject.create(
            dataset=dataset,
            object_name="Incomplete",
            landmark_str="0\t0\nNA\tNA\n0\t1"
        )

        # Run analysis
        analysis = controller.run_analysis(
            dataset=dataset,
            analysis_name="Missing Data Analysis"
        )

        # Should complete successfully using imputation
        assert analysis is not None
        assert analysis.superimposed_landmark_json is not None
```

---

#### 2.2 Database Transaction Tests
**Priority**: 🟡 High
**Estimated Time**: 8 hours

**Test CRUD Operations:**
```python
# tests/integration/test_database_operations.py
import pytest
from peewee import IntegrityError

from MdModel import MdDataset, MdObject, MdAnalysis, database


class TestDatabaseOperations:
    """Test database operations and transactions."""

    def test_cascade_delete_dataset(self, test_db):
        """Test deleting dataset deletes all related objects."""
        # Create dataset with objects
        dataset = MdDataset.create(dataset_name="Test")
        obj1 = MdObject.create(dataset=dataset, object_name="Obj1")
        obj2 = MdObject.create(dataset=dataset, object_name="Obj2")

        dataset_id = dataset.id

        # Delete dataset
        dataset.delete_instance(recursive=True)

        # Verify objects deleted
        assert MdDataset.select().where(
            MdDataset.id == dataset_id
        ).count() == 0
        assert MdObject.select().where(
            MdObject.dataset == dataset_id
        ).count() == 0

    def test_transaction_rollback(self, test_db):
        """Test transaction rollback on error."""
        with database.atomic() as transaction:
            dataset = MdDataset.create(dataset_name="Test")

            try:
                # This should fail (duplicate name)
                MdDataset.create(dataset_name="Test")
            except IntegrityError:
                transaction.rollback()

        # Dataset should not exist
        assert MdDataset.select().where(
            MdDataset.dataset_name == "Test"
        ).count() == 0

    def test_concurrent_updates(self, test_db):
        """Test handling concurrent updates."""
        dataset = MdDataset.create(dataset_name="Test")

        # Simulate two processes updating same record
        ds1 = MdDataset.get_by_id(dataset.id)
        ds2 = MdDataset.get_by_id(dataset.id)

        ds1.dataset_name = "Updated1"
        ds1.save()

        ds2.dataset_name = "Updated2"
        ds2.save()

        # Last write wins
        assert MdDataset.get_by_id(dataset.id).dataset_name == "Updated2"
```

---

### 3. Performance Testing (Week 3)

#### 3.1 Benchmark Tests
**Priority**: 🟡 High
**Estimated Time**: 10 hours

**Create Performance Suite:**
```python
# tests/performance/test_benchmarks.py
import pytest
import time
import numpy as np

from MdModel import MdDataset, MdObject, MdDatasetOps
from MdStatistics import do_pca_analysis


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for critical operations."""

    @pytest.fixture
    def large_dataset(self):
        """Create large dataset (1000 objects, 50 landmarks)."""
        dataset = MdDataset.create(
            dataset_name="Large Dataset",
            dimension=2
        )

        # Generate random landmarks
        for i in range(1000):
            landmarks = np.random.randn(50, 2)
            landmark_str = "\n".join(
                f"{x}\t{y}" for x, y in landmarks
            )
            MdObject.create(
                dataset=dataset,
                object_name=f"Object_{i:04d}",
                landmark_str=landmark_str
            )

        return dataset

    def test_procrustes_performance(self, large_dataset, benchmark):
        """Benchmark Procrustes superimposition."""
        ops = MdDatasetOps(large_dataset)

        # Benchmark
        result = benchmark(ops.procrustes_superimposition)

        assert result is True
        # Should complete in < 5 seconds for 1000 objects
        assert benchmark.stats['mean'] < 5.0

    def test_pca_performance(self, large_dataset, benchmark):
        """Benchmark PCA analysis."""
        ops = MdDatasetOps(large_dataset)
        ops.procrustes_superimposition()

        # Extract landmarks
        landmarks = [obj.landmark_list for obj in ops.object_list]

        # Benchmark
        result = benchmark(do_pca_analysis, landmarks)

        assert result is not None
        # Should complete in < 2 seconds
        assert benchmark.stats['mean'] < 2.0

    def test_database_query_performance(self, large_dataset, benchmark):
        """Benchmark database queries."""
        def query_all_objects():
            return list(large_dataset.object_list)

        # Benchmark
        objects = benchmark(query_all_objects)

        assert len(objects) == 1000
        # Should complete in < 0.1 seconds
        assert benchmark.stats['mean'] < 0.1
```

**Run Benchmarks:**
```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Run benchmarks
pytest tests/performance/ --benchmark-only

# Save baseline
pytest tests/performance/ --benchmark-save=baseline

# Compare against baseline
pytest tests/performance/ --benchmark-compare=baseline
```

---

#### 3.2 Memory Profiling
**Priority**: 🟢 Medium
**Estimated Time**: 6 hours

**Memory Tests:**
```python
# tests/performance/test_memory.py
import pytest
import tracemalloc

from MdModel import MdDataset, MdObject


@pytest.mark.memory
class TestMemoryUsage:
    """Test memory usage for large operations."""

    def test_large_dataset_memory(self):
        """Test memory doesn't leak with large datasets."""
        tracemalloc.start()

        # Create large dataset
        dataset = MdDataset.create(dataset_name="Memory Test")

        for i in range(10000):
            MdObject.create(
                dataset=dataset,
                object_name=f"Obj{i}",
                landmark_str="0\t0\n1\t1"
            )

        # Get memory snapshot
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')

        # Print top memory consumers
        for stat in top_stats[:10]:
            print(stat)

        # Cleanup
        dataset.delete_instance(recursive=True)

        # Memory should be released
        snapshot2 = tracemalloc.take_snapshot()
        # Assert memory decreased
        # (actual assertion depends on environment)

        tracemalloc.stop()
```

---

### 4. CI/CD Pipeline (Week 3-4)

#### 4.1 GitHub Actions Setup
**Priority**: 🔴 Critical
**Estimated Time**: 8 hours

**Create Workflow File:**
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install system dependencies (Ubuntu)
      if: runner.os == 'Linux'
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
          libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
          libglut-dev libglut3.12 python3-opengl \
          xvfb

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r config/requirements-dev.txt

    - name: Run linting
      run: |
        ruff check .
        ruff format --check .

    - name: Run type checking
      run: |
        mypy MdStatistics.py MdUtils.py ModanController.py || true

    - name: Run tests (Linux with xvfb)
      if: runner.os == 'Linux'
      run: |
        xvfb-run -a pytest --cov=. --cov-report=xml --cov-report=term

    - name: Run tests (Windows/Mac)
      if: runner.os != 'Linux'
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

    - name: Run benchmarks
      run: |
        pytest tests/performance/ --benchmark-only --benchmark-json=benchmark.json

    - name: Store benchmark result
      uses: benchmark-action/github-action-benchmark@v1
      with:
        tool: 'pytest'
        output-file-path: benchmark.json
        github-token: ${{ secrets.GITHUB_TOKEN }}
        auto-push: true
```

---

#### 4.2 Build and Release Pipeline
**Priority**: 🟡 High
**Estimated Time**: 10 hours

**Build Workflow:**
```yaml
# .github/workflows/build.yml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller

    - name: Build with PyInstaller
      run: |
        python build.py

    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: modan2-${{ matrix.os }}
        path: dist/

    - name: Create Release
      if: startsWith(github.ref, 'refs/tags/')
      uses: softprops/action-gh-release@v1
      with:
        files: dist/*
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

#### 4.3 Code Quality Checks
**Priority**: 🟡 High
**Estimated Time**: 4 hours

**Quality Gate Workflow:**
```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install ruff mypy bandit safety

    - name: Check code formatting
      run: ruff format --check .

    - name: Lint code
      run: ruff check .

    - name: Type checking
      run: mypy . --ignore-missing-imports || true

    - name: Security scan
      run: |
        bandit -r . -x tests,venv
        safety check

    - name: Check dependencies
      run: pip-audit
```

---

### 5. Advanced Testing (Week 4)

#### 5.1 Mutation Testing
**Priority**: 🟢 Low
**Estimated Time**: 6 hours

**Setup mutmut:**
```bash
pip install mutmut
```

**Run Mutation Tests:**
```bash
# Test MdStatistics module
mutmut run --paths-to-mutate=MdStatistics.py

# Show results
mutmut results

# Show specific mutations
mutmut show <id>
```

**Configuration:**
```python
# setup.cfg
[mutmut]
paths_to_mutate=MdStatistics.py,MdUtils.py,ModanController.py
backup=False
runner=pytest
tests_dir=tests/
```

---

#### 5.2 Property-Based Testing
**Priority**: 🟢 Low
**Estimated Time**: 8 hours

**Install Hypothesis:**
```bash
pip install hypothesis
```

**Property Tests:**
```python
# tests/property/test_statistics_properties.py
from hypothesis import given, strategies as st
import numpy as np

from MdStatistics import do_pca_analysis


class TestPCAProperties:
    """Property-based tests for PCA."""

    @given(
        n_samples=st.integers(min_value=10, max_value=100),
        n_features=st.integers(min_value=2, max_value=10),
        n_landmarks=st.integers(min_value=3, max_value=20)
    )
    def test_pca_variance_explained_sums_to_one(
        self, n_samples, n_features, n_landmarks
    ):
        """Test PCA explained variance ratios sum to 1.0."""
        # Generate random landmark data
        landmarks = []
        for _ in range(n_samples):
            landmark = np.random.randn(n_landmarks, 2).tolist()
            landmarks.append(landmark)

        # Run PCA
        result = do_pca_analysis(landmarks)

        # Property: explained variance should sum to ~1.0
        explained_var = result['explained_variance_ratio']
        assert abs(sum(explained_var) - 1.0) < 0.01

    @given(
        n_samples=st.integers(min_value=10, max_value=50),
        n_landmarks=st.integers(min_value=5, max_value=15)
    )
    def test_pca_scores_orthogonal(self, n_samples, n_landmarks):
        """Test PCA scores are orthogonal."""
        # Generate data
        landmarks = [
            np.random.randn(n_landmarks, 2).tolist()
            for _ in range(n_samples)
        ]

        result = do_pca_analysis(landmarks)
        scores = np.array(result['scores'])

        # Property: PCs should be orthogonal
        # Calculate correlation between PCs
        if scores.shape[1] > 1:
            corr = np.corrcoef(scores, rowvar=False)
            off_diagonal = corr[np.triu_indices_from(corr, k=1)]

            # Off-diagonal correlations should be near 0
            assert np.all(np.abs(off_diagonal) < 0.1)
```

---

## Deliverables

### Testing Infrastructure
- [ ] pytest-qt configured and operational
- [ ] 50+ UI tests covering all dialogs
- [ ] 30+ integration tests
- [ ] Performance benchmarks established
- [ ] Memory profiling tools in place

### CI/CD Pipeline
- [ ] GitHub Actions workflows configured
- [ ] Automated testing on push/PR
- [ ] Multi-platform testing (Linux, Windows, macOS)
- [ ] Code quality gates
- [ ] Automated builds on tags
- [ ] Coverage reporting to Codecov

### Test Coverage
- [ ] Overall coverage: 70%+
- [ ] UI components: 50%+
- [ ] Core logic: 90%+
- [ ] Integration scenarios: Comprehensive

### Documentation
- [ ] Testing guide created
- [ ] CI/CD documentation
- [ ] Benchmark results documented
- [ ] Contributing guidelines updated

---

## Success Criteria

1. ✅ Coverage ≥70% overall
2. ✅ All dialogs have UI tests
3. ✅ Integration tests cover main workflows
4. ✅ CI pipeline runs on all commits
5. ✅ Build succeeds on 3 platforms
6. ✅ Performance benchmarks pass
7. ✅ No critical security issues (bandit)
8. ✅ Documentation complete

---

## Metrics and Monitoring

### Coverage Tracking
```bash
# Generate coverage badge
coverage-badge -o coverage.svg

# Track coverage over time
pytest --cov --cov-report=json
# Store in coverage_history.json
```

### Performance Monitoring
```bash
# Run benchmarks and compare
pytest --benchmark-compare=baseline

# Alert if performance degrades >10%
```

### Quality Metrics
- Code coverage: ≥70%
- Test success rate: 100%
- Build success rate: ≥95%
- Security issues: 0 critical

---

## Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | UI testing setup | pytest-qt configured, 20+ dialog tests |
| **Week 2** | Integration tests | 30+ integration tests, workflow coverage |
| **Week 3** | Performance + CI/CD | Benchmarks, GitHub Actions pipeline |
| **Week 4** | Advanced testing + docs | Property tests, documentation complete |

---

## Risks & Mitigation

### Risk 1: UI Tests Flaky on CI
**Impact**: Medium
**Mitigation**:
- Use xvfb for headless testing
- Add retries for flaky tests
- Increase timeouts on slower CI runners

### Risk 2: Performance Regressions
**Impact**: Low
**Mitigation**:
- Establish baseline benchmarks
- Alert on >10% regression
- Profile before merging large changes

### Risk 3: Coverage Plateau
**Impact**: Low
**Mitigation**:
- Focus on high-value code paths
- Accept lower coverage for UI glue code
- Use mutation testing to verify quality

---

## Next Steps

**Post-Phase 3:**
- Continuous improvement of test suite
- Regular performance monitoring
- Expand to contract testing (if needed)
- Consider E2E testing for critical workflows

---

**Status**: 📝 Planning
**Dependencies**: Phase 1 and Phase 2 completed
**Owner**: Development Team
**Last Updated**: 2025-10-05
