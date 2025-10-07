# Integration Testing Strategy - Phase 6

**Date**: 2025-10-07
**Phase**: Phase 6 - Integration Testing
**Status**: 🚀 STARTING

---

## Overview

After completing Phase 5 (Component Testing), we now move to Phase 6: Integration Testing.
This phase focuses on testing complete user workflows that span multiple components, dialogs, and data operations.

---

## Current State Analysis

### Existing Integration Tests

**Files**:
- `test_integration_workflows.py` - 10 tests (all passing)
- `test_analysis_workflow.py` - 6 tests (4 passing, 2 skipped)
- `test_workflows.py` - 10 tests (all skipped due to timeout issues)
- `test_legacy_integration.py` - 10 tests (all passing)

**Total**: 36 integration tests (24 passing, 12 skipped)

### Test Coverage Gaps

**Missing Workflows**:
1. Complete dataset lifecycle (create → add objects → edit → delete)
2. Multi-analysis workflow (PCA → CVA → MANOVA on same dataset)
3. Calibration → Object creation workflow
4. 3D object manipulation workflows
5. Data exploration → Export workflow
6. Variable management across objects
7. Error recovery scenarios

---

## Integration Test Strategy

### Principles

1. **End-to-End Focus**: Test complete user workflows, not isolated functions
2. **Real Data Flow**: Use actual database operations, not mocks (where possible)
3. **Component Integration**: Verify components work together correctly
4. **State Management**: Test state changes across multiple operations
5. **Error Handling**: Test failure scenarios and recovery

### Test Organization

```
tests/
├── test_integration_workflows.py      # Import/Export workflows (existing)
├── test_analysis_workflow.py          # Analysis workflows (existing)
├── test_dataset_lifecycle.py          # NEW: Dataset CRUD workflows
├── test_object_workflows.py           # NEW: Object manipulation workflows
├── test_calibration_workflow.py       # NEW: Calibration + object workflows
├── test_multi_analysis_workflow.py    # NEW: Multiple analysis types
└── test_error_recovery.py             # NEW: Error handling workflows
```

---

## Planned Integration Tests

### Priority 1: Dataset Lifecycle (HIGH)

**File**: `test_dataset_lifecycle.py`

**Tests** (10-12 tests):
1. Create dataset → Add variables → Add objects
2. Create parent dataset → Create child dataset
3. Edit dataset properties → Verify objects updated
4. Add wireframe → Verify all objects show wireframe
5. Reorder variables → Verify object data migrated
6. Delete dataset → Verify cascade deletion
7. Import dataset → Modify → Export → Reimport
8. Copy dataset with objects
9. Dataset with baseline and polygons
10. Large dataset (100+ objects)

**Estimated Time**: 3-4 hours

### Priority 2: Object Workflows (HIGH)

**File**: `test_object_workflows.py`

**Tests** (8-10 tests):
1. Create object → Edit landmarks → Save
2. Import landmarks from file → Attach image
3. Calibrate image → Digitize landmarks → Save
4. Copy object to another dataset
5. Delete object → Verify dataset updated
6. Edit object variables → Verify dataset consistency
7. Batch create objects (10+)
8. Object with 3D model attachment
9. Object landmark validation
10. Undo/redo landmark changes

**Estimated Time**: 3-4 hours

### Priority 3: Multi-Analysis Workflow (MEDIUM)

**File**: `test_multi_analysis_workflow.py`

**Tests** (6-8 tests):
1. Create dataset → Run PCA → Run CVA → Run MANOVA
2. PCA analysis → Export results → Reimport
3. CVA with different grouping variables
4. MANOVA on multiple datasets
5. Analysis comparison (same data, different methods)
6. Large dataset analysis (100+ objects, 50+ landmarks)
7. Analysis with missing data handling
8. Analysis result persistence

**Estimated Time**: 2-3 hours

### Priority 4: Calibration Workflow (MEDIUM)

**File**: `test_calibration_workflow.py`

**Tests** (5-6 tests):
1. Load image → Calibrate → Create object → Digitize
2. Multiple calibrations on same image
3. Calibration with different units (mm, cm, pixels)
4. Save/load calibration settings
5. Apply calibration to existing objects
6. Batch calibration workflow

**Estimated Time**: 2-3 hours

### Priority 5: Error Recovery (LOW)

**File**: `test_error_recovery.py`

**Tests** (5-6 tests):
1. Import invalid file → Error → Recover
2. Save object with missing data → Validation → Fix
3. Run analysis with insufficient data → Error message
4. Database corruption recovery
5. Concurrent access handling
6. Memory error recovery (large datasets)

**Estimated Time**: 2-3 hours

---

## Implementation Plan

### Week 1: Core Workflows

**Day 1** (Today):
- ✅ Create strategy document
- [ ] Implement Priority 1: Dataset Lifecycle (5-6 tests)
- [ ] Verify tests pass

**Day 2**:
- [ ] Complete Priority 1: Dataset Lifecycle (remaining tests)
- [ ] Implement Priority 2: Object Workflows (4-5 tests)

**Day 3**:
- [ ] Complete Priority 2: Object Workflows (remaining tests)
- [ ] Start Priority 3: Multi-Analysis Workflow (3-4 tests)

### Week 2: Advanced Workflows

**Day 1**:
- [ ] Complete Priority 3: Multi-Analysis Workflow
- [ ] Implement Priority 4: Calibration Workflow

**Day 2**:
- [ ] Complete Priority 4: Calibration Workflow
- [ ] Implement Priority 5: Error Recovery
- [ ] Review and refactor

**Day 3**:
- [ ] Fix any failing tests
- [ ] Documentation
- [ ] Phase 6 completion summary

---

## Testing Patterns

### Pattern 1: Full Workflow Test

```python
def test_complete_dataset_workflow(qtbot, mock_database):
    """Test complete dataset creation and usage workflow."""
    # Step 1: Create dataset
    dataset = MdDataset.create(
        dataset_name="Test Dataset",
        dimension=2,
        landmark_count=5
    )

    # Step 2: Add variables
    dataset.propertyname_str = "Sex,Age,Location"
    dataset.save()

    # Step 3: Create objects
    for i in range(3):
        obj = MdObject.create(
            dataset=dataset,
            object_name=f"Obj_{i}",
            landmark_str="1,2\n3,4\n5,6\n7,8\n9,10",
            propertyvalue_str="M,25,Site1"
        )

    # Step 4: Verify consistency
    assert dataset.object_list.count() == 3
    assert dataset.get_variablename_list() == ["Sex", "Age", "Location"]

    # Step 5: Edit dataset
    dataset.propertyname_str = "Sex,Age,Location,Group"
    dataset.save()

    # Step 6: Verify objects updated
    for obj in dataset.object_list:
        values = obj.propertyvalue_str.split(",")
        assert len(values) == 4  # Should have 4 values now
```

### Pattern 2: Dialog Integration Test

```python
def test_dialog_to_data_workflow(qtbot, mock_database):
    """Test dialog interaction creates correct data."""
    # Create dialog
    dialog = DatasetDialog(parent=None)
    qtbot.addWidget(dialog)

    # Simulate user input
    dialog.edtDatasetName.setText("Test")
    dialog.rbtn2D.setChecked(True)
    dialog.lstVariableName.addItem("Variable1")

    # Trigger save
    dialog.btnOkay.click()

    # Verify data created
    dataset = MdDataset.select().order_by(MdDataset.id.desc()).first()
    assert dataset.dataset_name == "Test"
    assert dataset.dimension == 2
    assert "Variable1" in dataset.get_variablename_list()
```

### Pattern 3: Multi-Component Integration

```python
def test_main_window_dataset_selection(qtbot, mock_database, main_window):
    """Test main window responds to dataset selection."""
    # Create dataset
    dataset = MdDataset.create(dataset_name="Test", dimension=2)

    # Reload main window tree
    main_window.load_dataset()

    # Simulate selection in tree
    root = main_window.dataset_model.invisibleRootItem()
    item = root.child(0, 0)
    index = main_window.dataset_model.indexFromItem(item)
    main_window.treeView.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

    # Verify main window state updated
    assert main_window.selected_dataset == dataset
    assert main_window.actionNewObject.isEnabled()
```

---

## Success Criteria

### Quantitative

- ✅ Add 30-40 new integration tests
- ✅ All integration tests passing
- ✅ Test execution time < 2 minutes
- ✅ Coverage of major user workflows

### Qualitative

- ✅ Tests represent real user scenarios
- ✅ Tests catch integration bugs
- ✅ Tests are maintainable
- ✅ Documentation is clear

---

## Risk Analysis

### Risks

1. **Performance**: Integration tests may be slow
   - **Mitigation**: Use in-memory database, mock file I/O

2. **Flakiness**: Tests may be unstable
   - **Mitigation**: Proper qtbot.waitUntil usage, avoid race conditions

3. **Complexity**: Hard to debug failures
   - **Mitigation**: Clear test names, good logging, step-by-step assertions

4. **Maintenance**: Tests break with UI changes
   - **Mitigation**: Focus on data flow, not UI details

---

## Related Documents

- Phase 5 Completion: `devlog/20251007_128_phase5_completion.md`
- Timeout Resolution: `devlog/20251007_129_test_timeout_resolution.md`
- Existing Integration Tests: `tests/test_integration_workflows.py`

---

**Status**: Strategy Defined ✅

**Next Step**: Implement Priority 1 (Dataset Lifecycle Tests)

**Estimated Phase Duration**: 2 weeks

**Target Completion**: 2025-10-21
