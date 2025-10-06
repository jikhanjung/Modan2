# Phase 4 Week 2 - MdModel.py Coverage Analysis

**Date**: 2025-10-06
**Status**: 🔍 In Progress
**Phase**: Phase 4 - Week 2 - Test Coverage Improvement

## Current Status

### Coverage Metrics
- **Current Coverage**: 31% (432/1384 statements)
- **Target Coverage**: 70%+
- **Gap**: 39 percentage points
- **Tests Passing**: 76/76

### Missing Coverage Breakdown

Based on the coverage report, the following areas need testing:

#### 1. MdDataset Methods (Lines 55-72, 106-348)
**Untested Methods**:
- `get_grouping_variable_index_list()` (lines 53-71)
- Image/model path operations (lines 106, 118, 130-132)
- Edge parsing and wireframe operations (lines 211-247)
- Polygon operations (lines 291-348)

**Priority**: HIGH - These are core dataset operations

#### 2. MdObject Methods (Lines 367-731)
**Untested Methods**:
- Image attachment operations (lines 367-381, 405-428)
- 3D model operations (lines 460-477, 483-486)
- Landmark manipulation (lines 531, 548-589)
- Variable operations (lines 600-650, 653-731)

**Priority**: HIGH - Object CRUD operations

#### 3. MdDatasetOps Class (Lines 750-1220)
**Untested Methods**:
- Initialization and setup (lines 750-760, 763-769)
- Object list operations (lines 777-811)
- Procrustes superimposition (lines 854-947)
- Shape extraction (lines 950-962, 966-1048)
- Advanced operations (lines 1051-1220)

**Priority**: MEDIUM - Complex analysis operations

#### 4. MdImage and MdThreeDModel (Lines 1229-1509)
**Untested Methods**:
- Image EXIF reading (lines 1229-1306)
- Image copy operations (lines 1311-1338)
- 3D model operations (lines 1449-1509)

**Priority**: MEDIUM - Supporting functionality

#### 5. Helper Functions (Lines 1539-2070)
**Untested Functions**:
- File I/O operations (lines 1539-1619)
- Import/export functions (lines 1624-1903)
- Utility functions (lines 1913-2070)

**Priority**: LOW-MEDIUM - Supporting utilities

## Testing Strategy

### Week 2 Plan

#### Day 1-2: Core Dataset Operations
**Focus**: Get coverage to ~45%
- Test `get_grouping_variable_index_list` with various scenarios
- Test wireframe/baseline/polygon packing/unpacking
- Test edge list operations
- **Estimated**: 15-20 new tests

#### Day 3: Object Operations
**Focus**: Get coverage to ~55%
- Test image attachment/detachment
- Test 3D model operations
- Test landmark manipulation methods
- **Estimated**: 15-20 new tests

#### Day 4: MdDatasetOps Operations
**Focus**: Get coverage to ~65%
- Test object list management
- Test basic superimposition
- Test shape extraction
- **Estimated**: 10-15 tests

#### Day 5: Polish and Edge Cases
**Focus**: Get coverage to 70%+
- Test MdImage EXIF operations
- Test file I/O edge cases
- Test error handling
- **Estimated**: 10-15 tests

### Total Estimated New Tests
**50-70 new tests** to reach 70% coverage (currently 76 tests)

## Test Categories to Add

### 1. Dataset Grouping Tests
```python
- test_get_grouping_variable_with_multiple_groups
- test_get_grouping_variable_with_many_unique_values
- test_get_grouping_variable_empty_dataset
- test_get_grouping_variable_no_variables
```

### 2. Wireframe/Polygon Tests
```python
- test_pack_unpack_wireframe_complex
- test_get_edge_list_with_invalid_data
- test_pack_unpack_polygons
- test_get_polygon_list
- test_baseline_operations
```

### 3. Object Image Tests
```python
- test_attach_image_to_object
- test_detach_image_from_object
- test_has_image_true
- test_get_image_path
- test_copy_image_file
```

### 4. Object 3D Model Tests
```python
- test_attach_3d_model_to_object
- test_detach_3d_model_from_object
- test_has_threed_model_true
- test_get_3d_model_path
```

### 5. MdDatasetOps Tests
```python
- test_dataset_ops_initialization
- test_add_multiple_objects
- test_procrustes_basic
- test_get_shape_from_index
- test_object_filtering
```

### 6. MdImage Tests
```python
- test_read_exif_data
- test_copy_image_with_exif
- test_image_without_exif
```

## Expected Outcome

### Coverage Improvement
```
Before:  31% (432/1384 statements)
After:   70% (969/1384 statements)
Increase: +537 statements covered
```

### Test Count
```
Before:  76 tests
After:   126-146 tests
Increase: +50-70 tests
```

### Quality Metrics
- ✅ All existing tests still passing
- ✅ No regressions
- ✅ Better edge case coverage
- ✅ More reliable codebase

## Implementation Notes

### Key Principles
1. **One test, one assertion (mostly)** - Keep tests focused
2. **Use fixtures** - Leverage conftest.py for common setup
3. **Test edge cases** - Empty inputs, None values, invalid data
4. **Test error paths** - Not just happy paths
5. **Document complex tests** - Add docstrings for clarity

### Fixtures to Add
```python
@pytest.fixture
def dataset_with_images():
    """Dataset with objects that have images attached."""

@pytest.fixture
def dataset_with_3d_models():
    """Dataset with 3D model objects."""

@pytest.fixture
def dataset_with_wireframe():
    """Dataset with wireframe configuration."""

@pytest.fixture
def dataset_with_grouping_variables():
    """Dataset with multiple grouping variables."""
```

## Success Criteria

- ✅ Coverage reaches 70%+ for MdModel.py
- ✅ All 76 existing tests still pass
- ✅ 50-70 new tests added
- ✅ No decrease in performance (tests run < 30 seconds)
- ✅ Documentation updated

---

**Next Step**: Start implementing Day 1 tests (dataset operations)
