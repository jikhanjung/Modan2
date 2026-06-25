# Dead Code Cleanup & Test Fixes

**Date**: 2026-06-25
**Type**: Implementation log
**Follows**: [R01 Code Review — Legacy & DB Patterns](20260625_R01_code_review_legacy_and_db_patterns.md)
**Commits**: `d28059a` (cleanup), `da21136` (fixes)

---

## Summary

First implementation pass following the R01 code review. Two logical units:

1. **Dead code / duplicate definition cleanup** — removed provably unreachable
   or duplicated code surfaced by the review (zero behavior change).
2. **Test failure triage & fixes** — investigated 13 pre-existing test
   failures, fixed 1 real code bug + 2 stale tests; isolated the remaining 8 as
   a test-infrastructure issue.

Test suite went from **13 failed / 1168 passed** to **8 failed / 1173 passed**.
The 8 remaining failures are pre-existing test-isolation issues, untouched here.

---

## Part 1 — Dead code & duplicate removal (`d28059a`)

83 lines removed across 3 source files; all changes are pure deletion of
duplicate or unreachable code. Verified by full-suite diff (identical 13
failures / 1168 passes before and after → zero regressions).

| File | Removed |
|---|---|
| `MdUtils.py` | Duplicate `resource_path()` definition (second copy shadowed the first) |
| `MdModel.py` | Duplicate `cva_group_by` field, misplaced under the `""" PCA result """` section (the real one lives under `""" CVA result """`) |
| `Modan2.py` | Duplicate `treeView_drag_move_event()` (dead first definition) |
| `Modan2.py` | Dead `if False:` block in `update_language()` (referenced an undefined `language`) |
| `Modan2.py` | Unreachable code after `return` in `tableView_drag_enter_event()` |
| `Modan2.py` | Unused `_tableView_drag_move_event()` method (never referenced) |

Also: `.gitignore` now ignores `.vscode/` and `.idea/`; the R01 review doc was
committed alongside.

### Verification
- All 3 source files parse (`ast.parse`).
- Each removed symbol confirmed to now appear exactly once (or zero times).
- Used handlers (`tableView_drag_enter_event`, `tableView_drag_move_event`,
  `treeView_drag_move_event`, `update_language`) all preserved and still wired
  to their call sites (`Modan2.py:1480-1481`).

### Deferred
- **`ModanDialogs.py` (2539 lines)** — dead/duplicated (fully re-implemented in
  the `dialogs/` package) but **not** a simple delete: `Modan2.py:71` imports
  the `MODE` constant from it, and 5 test files still import its classes
  (`test_ui_dialogs`, `test_legacy_integration`, `test_import`,
  `test_analysis_workflow`, `test_dataset_dialog_direct`). Removing it requires
  relocating `MODE` (→ `MdConstants`) and repointing those tests. Left for a
  dedicated migration pass.

---

## Part 2 — Test failure triage (13 pre-existing failures)

The 13 failures present before this work were categorized by running each
group both in isolation and in the full suite.

### GROUP 1 — Real code bug (3 tests) → FIXED
`test_get_ellipse_params` (×2), `test_get_ellipse_params_rotated`

**Root cause**: `MdUtils.get_ellipse_params` called `np.linalg.eig` on a
covariance matrix. Covariance is symmetric (real eigenvalues), but the general
`eig` can return a **complex dtype**, which `np.arctan2` rejects under numpy
2.x:
```
TypeError: ufunc 'arctan2' not supported for the input types ...
```
This affected the actual application (confidence-ellipse rendering in scatter
plots), not just tests.

**Fix** (`da21136`): use `np.linalg.eigh` (symmetric/Hermitian solver — returns
real eigenvalues/eigenvectors). Also removed the dead `1 *` multiplier.

### GROUP 2 — Test isolation (8 tests) → NOT a code bug, deferred
`test_analysis_dialog_creation`, `test_analysis_dialog_default_values`,
`test_dataset_dialog_creation`, `test_object_dialog_creation`,
`test_import_dialog_creation`, `test_keyboard_shortcut_toggles_overlay`,
`test_window_creation`, `test_menu_bar_exists`

**Diagnosis**: all 8 **pass when run alone** but fail in the full suite →
shared DB / Qt singleton state leaking across tests (ordering-dependent).
Production code is fine. Fixing this means finding the polluting test and
hardening fixture teardown — left as a separate task.

### GROUP 3 — Stale test assumptions (2 tests) → FIXED
**Root cause**: the `sample_dataset` fixture (`conftest.py:243`) now
pre-creates **3 objects**, which both tests predate.

- `test_run_analysis_insufficient_objects` — expected `run_analysis` to return
  `None`, but the guard only rejects `< 2` objects with landmarks
  (`ModanController.py:544`); the fixture's 3 valid objects are *sufficient*, so
  PCA ran and returned an analysis. **Fix**: the test now builds its own
  1-object dataset to actually exercise the insufficient-data path.
- `test_get_dataset_summary` — asserted `object_count == 3`, but fixture's 3 +
  the test's 3 = 6. **Fix**: assert relative to `initial_count + 3`, robust to
  future fixture changes.

---

## Result

```
Before:  13 failed, 1168 passed, 74 skipped
After:    8 failed, 1173 passed, 74 skipped   (+5 fixed, 0 regressions)
```

Remaining 8 = GROUP 2 test-isolation issues (pre-existing, not code bugs).

## Next candidates
1. GROUP 2 — trace the state-leaking test, harden fixture teardown.
2. `ModanDialogs.py` migration (relocate `MODE`, repoint 5 test files, delete file).
3. DB correctness items from R01 (C1 controller field names, C2 class-level
   mutable attrs, C4 missing `atomic()` transactions).

## Environment note
Tests run via the project venv at `/home/jikhanjung/venv/Modan2` with
`QT_QPA_PLATFORM=offscreen`. The venv carried runtime deps (numpy 2.5.0, PyQt5,
pandas, scipy, peewee, trimesh) but `pytest`/dev deps were installed this
session from `config/requirements-dev.txt`. Note numpy is **2.5.0** here despite
`Modan2_env.txt` pinning `numpy==1.26` — the version mismatch is what surfaced
the GROUP 1 `eig`/`arctan2` bug.
