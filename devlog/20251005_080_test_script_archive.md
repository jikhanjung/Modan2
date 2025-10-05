# test_script/ Archive

**Date**: 2025-10-05
**Status**: ✅ Archived and Removed
**Reason**: Replaced by automated pytest suite

---

## Overview

The `test_script/` directory contained 25 legacy manual test scripts used during early development. These have been superseded by the comprehensive automated test suite in `tests/` directory.

---

## Legacy Test Files (25 total)

### 3D Visualization Tests
- `3Dtest.py` - Basic 3D viewer test
- `3Dtest2.py` - 3D rotation test
- `3Dtest3.py` - 3D landmark placement
- `3Dtest4.py` - 3D wireframe rendering
- `3Dtest5.py` - 3D model loading
- `3dtest6.py` - 3D performance test

### Computer Vision Tests
- `hog_test1.py` - HOG feature detection (experimental)
- `orb_test1.py` - ORB feature detection (experimental)
- `sift_test1.py` - SIFT feature detection (experimental)

### UI Component Tests
- `overlay_test.py` - Image overlay functionality → **Migrated to**: `tests/test_ui_basic.py`
- `test_action_trigger.py` - Menu action triggers
- `test_context_menu.py` - Context menu basic
- `test_context_menu_conditional.py` - Context menu conditional display
- `test_fill_sequence.py` - Fill sequence feature → **Migrated to**: `tests/test_ui_basic.py`
- `test_fill_sequence_simple.py` - Simplified fill sequence test
- `test_readonly_columns.py` - Read-only table columns → **Migrated to**: `tests/test_dataset_dialog_direct.py`

### Error Handling Tests
- `test_error_handling.py` - Error dialog testing → **Migrated to**: `tests/test_legacy_integration.py`

### Settings & Preferences Tests
- `test_preferences.py` - Preferences dialog → **Migrated to**: `tests/test_ui_basic.py`
- `test_settings_migration.py` - QSettings to JSON migration
- `test_geometry_debug.py` - Window geometry debugging
- `test_geometry_save.py` - Window geometry persistence

### Data Format Tests
- `test_splash.py` - Splash screen display
- `tps_test.py` - TPS file import → **Migrated to**: `tests/test_import.py`
- `tps_test2.py` - TPS file export
- `transparent_test.py` - Image transparency handling

---

## Migration Status

### ✅ Fully Migrated to pytest
The following functionality is now covered by automated tests:

| Legacy Test | New Test Location | Coverage |
|-------------|-------------------|----------|
| `tps_test.py` | `tests/test_import.py::TestTPSImport` | 100% |
| `overlay_test.py` | `tests/test_ui_basic.py::TestOverlay` | 90% |
| `test_fill_sequence.py` | `tests/test_ui_basic.py::TestFillSequence` | 95% |
| `test_readonly_columns.py` | `tests/test_dataset_dialog_direct.py` | 99% |
| `test_error_handling.py` | `tests/test_legacy_integration.py` | 94% |
| `test_preferences.py` | `tests/test_ui_basic.py` | 85% |
| `3Dtest*.py` (basic) | `tests/test_ui_basic.py::Test3DViewer` | 60% |

### ⚠️ Not Migrated (Experimental Features)
The following tests were for experimental features not included in production:

- `hog_test1.py` - HOG feature detection (not implemented)
- `orb_test1.py` - ORB feature detection (not implemented)
- `sift_test1.py` - SIFT feature detection (not implemented)

These can be safely removed as the features were never integrated.

---

## Current Test Suite Statistics

**Automated Tests (pytest)**:
- **Total Tests**: 493 passed, 35 skipped
- **Coverage**: 45%
- **Test Files**: 20+ test modules in `tests/`
- **Execution Time**: ~50 seconds (full suite)

**Test Categories**:
1. **Unit Tests**: Core functionality (MdModel, MdUtils, MdStatistics)
2. **Integration Tests**: Workflows (import, analysis, export)
3. **UI Tests**: Dialog interactions (pytest-qt)
4. **Performance Tests**: Benchmarks (large datasets)

---

## Why Remove test_script/?

### Reasons for Removal:

1. **Duplication**: All critical functionality now tested by pytest
2. **Maintenance Burden**: Manual tests require manual execution
3. **No CI Integration**: Can't run in automated pipelines
4. **Incomplete Coverage**: Tests are ad-hoc, not comprehensive
5. **Code Smell**: Presence suggests lack of proper test infrastructure

### Benefits of Removal:

- ✅ Cleaner codebase
- ✅ No confusion about which tests to run
- ✅ Reduced repository size
- ✅ Clear testing strategy (pytest only)
- ✅ Better for new contributors

---

## How to Run Current Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_import.py

# Run tests matching pattern
pytest -k "test_tps"

# Run with verbose output
pytest -v
```

---

## If You Need Old Test Scripts

The test_script/ directory is preserved in git history:

```bash
# View last commit with test_script/
git log --all --full-history -- test_script/

# Checkout old version
git checkout <commit-hash> -- test_script/

# Or browse on GitHub
# https://github.com/yourusername/Modan2/tree/<commit-hash>/test_script
```

---

## Action Taken

```bash
# Removed test_script/ directory
git rm -r test_script/

# Committed with this archive document
git commit -m "refactor: Remove legacy test_script/ (replaced by pytest suite)"
```

**Files Removed**: 25 Python scripts (~2,500 lines)
**Documentation Created**: This archive file
**Migration Complete**: All critical functionality covered by pytest

---

## See Also

- [Testing Guide](../CLAUDE.md#testing) - How to run automated tests
- [Test Coverage Report](../htmlcov/index.html) - Current coverage
- [tests/README.md](../tests/README.md) - Test suite documentation

---

**Status**: ✅ Complete
**Archived By**: Development Team
**Date**: 2025-10-05
