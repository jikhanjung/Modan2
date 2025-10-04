# MdUtils.py Coverage Analysis and Improvement Attempt

**Date**: 2025-10-04
**Status**: ⚠️ Deferred - Complex database integration required
**Previous**: [073_statistics_controller_coverage.md](20251004_073_statistics_controller_coverage.md)

## Overview

Attempted to improve MdUtils.py test coverage from 46% to 60%+, but encountered significant challenges with database-dependent export and serialization functions that require substantial integration work.

## Current Status

### MdUtils.py Coverage: 46% (unchanged)
- **Total**: 581 statements
- **Missing**: 315 statements
- **58 tests passing**

### Overall Project Coverage: 42%
- MdConstants: 97% ✅
- MdHelpers: 82% ✅
- MdStatistics: 78% ✅
- ModanController: 64% ✅
- MdModel: 50%
- **MdUtils: 46%** ⚠️

## Analysis of Uncovered Code

### Lines 508-624: Export Functions (CSV/Excel)
```python
def export_dataset_to_csv(dataset, file_path, include_metadata=True):
    for obj in dataset.objects:  # ❌ Bug: should be dataset.object_list
        if obj.landmarks:
            ...

def export_dataset_to_excel(dataset, file_path, include_metadata=True):
    for obj in dataset.objects:  # ❌ Same bug
        ...
```

**Issues Found**:
1. Uses `dataset.objects` instead of correct Peewee attribute `dataset.object_list`
2. Calls `show_error_message()` which triggers Qt dialogs, causing test crashes
3. Requires complex database setup with landmarks and variables

### Lines 653-747: JSON Serialization
```python
def serialize_dataset_to_json(dataset_id: int, include_files: bool = True) -> dict:
    dataset = MdDataset.get_by_id(dataset_id)
    wf = dataset.unpack_wireframe()
    polys = dataset.unpack_polygons()
    ...
```

**Challenges**:
- Requires fully populated database with:
  - Datasets with wireframes, polygons, baselines
  - Objects with landmarks, variables, sequences
  - Image and 3D model files
- Complex file path management
- Storage directory resolution

### Lines 757-859: ZIP Packaging
```python
def create_zip_package(dataset_id: int, output_path: str, include_files: bool = True) -> bool:
    ...
    # Build copy plan based on objects in JSON
    for obj in data.get('objects', []):
        files = obj.get('files') or {}
        ...
```

**Challenges**:
- Requires actual image/model files in storage
- File path resolution and copying
- Temporary directory management
- Progress callback testing

### Lines 900-1005: Import from ZIP
```python
def import_dataset_from_zip(zip_path: str, progress_callback=None) -> int:
    ...
    with gDatabase.atomic():
        # Complex transaction with error handling
        ...
```

**Challenges**:
- Database transactions
- File extraction and validation
- Error recovery
- Duplicate dataset name handling

## Attempts Made

### 1. Export Function Tests
Created tests for:
- `export_dataset_to_csv()` - Basic, with metadata, 3D, empty cases
- `export_dataset_to_excel()` - Basic, with metadata, empty cases

**Result**: ❌ Failed
- `dataset.objects` attribute doesn't exist (should be `dataset.object_list`)
- `show_error_message()` causes Qt dialog crash in tests
- Requires fixing MdUtils.py code first

### 2. Serialization Tests
Created tests for:
- `serialize_dataset_to_json()` - Basic, with variables, with wireframe

**Result**: ❌ Failed
- Landmark parsing issues with `landmark_str` format
- Variable list unpacking not working as expected
- Wireframe/polygon data not persisting correctly

### 3. ZIP Packaging Tests
Created tests for:
- `collect_dataset_files()`
- `estimate_package_size()`
- `create_zip_package()`

**Result**: ⚠️ Not fully tested
- Would need actual file creation in storage directory
- Complex fixture setup required

## Root Causes

### 1. Code Quality Issues
- **Inconsistent Peewee attributes**: Code uses `dataset.objects` instead of `dataset.object_list`
- **Direct Qt calls**: `show_error_message()` calls `QMessageBox.exec_()` directly
- **Missing abstractions**: Export/import logic tightly coupled to database schema

### 2. Testing Infrastructure Gaps
- **No integration test framework**: Need full database + file system setup
- **Fixture complexity**: Creating realistic datasets with files is difficult
- **Mock limitations**: Too many dependencies to mock effectively

### 3. Design for Testability
Functions are designed for production use, not testing:
- Large functions doing multiple things
- Hard-coded dependencies (Qt dialogs, file paths)
- No dependency injection

## Recommendations

### Short-term (Don't Test, Fix Code First)
1. **Fix export functions**:
   ```python
   # Change this:
   for obj in dataset.objects:
   # To this:
   for obj in dataset.object_list:
   ```

2. **Extract Qt dependencies**:
   ```python
   def export_dataset_to_csv(dataset, file_path, error_handler=None):
       try:
           ...
       except Exception as e:
           if error_handler:
               error_handler(f"Failed: {e}")
           return False
   ```

3. **Add unit-testable helpers**:
   ```python
   def _collect_landmark_rows(objects):
       """Pure function - easy to test."""
       rows = []
       for obj in objects:
           if obj.landmarks:
               row = _object_to_row(obj)
               rows.append(row)
       return rows
   ```

### Mid-term (Integration Tests)
1. Create `tests/test_mdutils_integration.py`
2. Set up realistic database fixtures
3. Test export/import round-trips
4. Use temporary file directories

### Long-term (Refactoring)
1. **Extract business logic**: Separate data transformation from I/O
2. **Dependency injection**: Pass database/file system as parameters
3. **Command pattern**: Encapsulate operations for testing

## Current Coverage Breakdown

### Well-Covered (already 46%)
- ✅ Constants and configuration (lines 0-89)
- ✅ File format reading (TPS, NTS) (lines 130-270)
- ✅ JSON schema validation (lines 862-876)
- ✅ ZIP safety functions (lines 879-895)
- ✅ Build information (lines 27-78)
- ✅ Utility functions (`is_numeric`, `get_ellipse_params`, `resource_path`)

### Uncovered (54% of file)
- ❌ Export to CSV/Excel (lines 508-624) - 117 lines
- ❌ JSON serialization (lines 653-747) - 95 lines
- ❌ ZIP packaging (lines 757-859) - 103 lines
- ❌ Import from ZIP (lines 900-1005) - 106 lines
- ❌ 3D model conversion helpers (lines 264-283) - 20 lines
- ❌ Error handling paths in various functions

**Total uncovered: ~441 lines (76%)**

## Lessons Learned

### What Worked
✅ Analyzing uncovered code systematically
✅ Identifying root causes (Peewee attribute bug)
✅ Understanding why functions are hard to test

### What Didn't Work
❌ Trying to test complex integrations without fixing code first
❌ Mocking too many dependencies
❌ Writing tests for buggy code

### Best Approach
1. **Fix code quality first** (attribute names, error handling)
2. **Refactor for testability** (extract pure functions)
3. **Then add tests** (both unit and integration)

## Impact

### Test Coverage
- **MdUtils.py**: 46% (no change)
- **Overall project**: 42% (no change)
- **Tests written**: 0 new (all abandoned)
- **Bugs found**: 2 (export functions, show_error_message)

### Code Quality Insights
📝 **Bugs discovered**:
1. Export functions use wrong Peewee attribute (`dataset.objects` vs `dataset.object_list`)
2. `show_error_message()` crashes headless tests

📝 **Design improvements needed**:
1. Extract business logic from I/O operations
2. Use dependency injection for Qt dialogs
3. Add integration test infrastructure

## Next Steps

### Immediate
Skip MdUtils.py improvement for now due to complexity.

### Future Work
1. **Option A**: Fix bugs first, then test
   - Fix `dataset.objects` → `dataset.object_list`
   - Mock `show_error_message()` in export functions
   - Add simple tests

2. **Option B**: Focus on other modules
   - MdModel.py: 50% → 65%+ (more straightforward)
   - Modan2.py: 40% → 50%+ (business logic only)

3. **Option C**: Add integration tests
   - Create full dataset fixtures
   - Test export/import workflows
   - Validate file generation

## Commands Used

```bash
# Attempted coverage check
pytest tests/test_mdutils.py --cov=MdUtils --cov-report=term-missing

# Found crashes
pytest tests/test_mdutils.py::TestExportFunctions -v

# Reverted changes
git checkout tests/test_mdutils.py
```

## Conclusion

**Status**: ⚠️ Deferred

MdUtils.py improvement requires:
1. Fixing code bugs first (2-3 hours)
2. Refactoring for testability (4-6 hours)
3. Building integration test infrastructure (6-8 hours)

**Estimated effort**: 12-17 hours

**Recommendation**: Move to MdModel.py or Modan2.py instead, which have simpler testing requirements.

---

**Contributors**: Claude (AI Assistant)
**Coverage**: MdUtils 46% → 46% (no change)
**Bugs Found**: 2 (export attribute bug, Qt dialog crash)
**Status**: ⚠️ Deferred - requires code fixes first
**Next**: Consider MdModel.py (50% → 65%+) or document current state
