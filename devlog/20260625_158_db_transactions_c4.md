# DB Correctness C4 — Transaction Wrapping

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 finding **C4** (multi-row writes/deletes without a transaction)
**Follows**: [157 numpy pin reconciliation](20260625_157_numpy_version_pin_reconciliation.md)

---

## Summary

`ModanController` performed several multi-row DB operations with **no transaction**
— a failure part-way through could leave the database half-modified (half-deleted
dataset, orphan image/3D-model rows, partially-imported file). There were **zero**
`atomic()` calls in the codebase.

Wrapped the multi-statement operations in `MdModel.gDatabase.atomic()` so each is
all-or-nothing, and moved observer signals to fire **after** commit. Added a test
that proves rollback actually happens.

Full suite: **1182 passed** (+1 new rollback test), 74 skipped, 0 failed. ruff clean.

---

## Changes (`ModanController.py`)

| Method | Was | Now |
|---|---|---|
| `delete_dataset` | object loop + analyses loop + dataset delete, unguarded | all three wrapped in one `atomic()`; selection-clear + signals moved after commit |
| `delete_object` | `delete_instance(recursive=True)` (object + image + 3D rows) | wrapped in `atomic()` |
| `_import_landmark_file` | N `MdObject.create` in a loop | loop wrapped in `atomic()`; `object_added` emitted after commit |
| `_import_image_file` | `MdImage.create` then `MdObject.create` | both wrapped in `atomic()` (no orphan image on failure) |
| `_import_3d_file` | `MdThreeDModel.create` then `MdObject.create` | both wrapped in `atomic()`; the filesystem conversion (`process_3d_file`) deliberately kept outside the txn |

### Design notes
- **Signals after commit**: `dataset_deleted` / `object_added` etc. now fire only
  once the transaction commits, so observers never react to a state that gets
  rolled back.
- **Per-file atomicity for imports**: `import_objects` keeps its per-file
  try/except (partial import across multiple files is intentional). Each
  `_import_single_file` is now individually atomic — one bad file no longer
  half-imports, but good files still succeed.
- **Single-row ops left as-is**: `create_object`, `update_*`, and the analysis
  save are single `create`/`save` statements (already atomic); not wrapped.
- Did **not** change the manual recursive-delete mechanism (CASCADE could replace
  it, but that is a behavior change beyond C4's transactional-correctness scope).

## New test
`tests/test_controller.py::TestDeleteOperations::test_delete_dataset_rolls_back_on_failure`
— patches `MdDataset.delete_instance` to raise *after* the object loop has deleted
rows, then asserts the dataset **and** all its objects still exist (transaction
rolled back). Verifies the wrapping is real, not cosmetic.

## Not addressed here (separate R01 items)
- **C1**: the import methods still pass non-model field names
  (`landmarks=`, `file_path=`, `image=`, `model_3d=`) — left for the C1 task.
- **C2**: class-level mutable list attributes in `MdModel`.
- N+1 query patterns (performance, not correctness).

## Files changed
`ModanController.py`, `tests/test_controller.py`.
