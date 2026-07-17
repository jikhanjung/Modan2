# 190 — Move `ObjectDialog.Delete` file/DB I/O into `ModanController`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 3, dialog DB/file I/O → controller)
**Related:** `devlog/20260717_189_...`

## What

Added `ModanController.delete_object_with_files(obj, storage_directory)` and
refactored `ObjectDialog.Delete` to delegate. The dialog keeps the `QMessageBox`
confirmation + `accept()` (UI); the controller now owns the `os.remove(image_file)`
+ `delete_instance()` I/O. Removed the now-unused `import os` from `object_dialog`.
Added `import os` to `ModanController`.

## Behavior preservation

Verbatim move: remove the first image's file (when it exists under
`storage_directory`) then `delete_instance()` — a **non-recursive** delete, matching
the original dialog. This is intentionally distinct from the existing
`delete_object(object_id)` (recursive, emits `object_deleted`, clears
`current_object`); a docstring note points between them.

## Coverage

`ObjectDialog.Delete` had **no** test coverage. Added
`tests/test_controller_object_io.py` (4 tests) covering both new controller helpers:
`save_object` (create + persist; `property_str=None` leaves the field untouched) and
`delete_object_with_files` (no-image path; and the image-file-removal path built via
a real `MdImage` + on-disk file at `get_file_path(storage)`).

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/test_controller_object_io.py tests/test_dataset_dialog_direct.py
  tests/test_object_workflows.py` — 43 passed.

## Next

Last item-3 target: `import_dialog` direct DB writes (`dataset.save()`,
`MdObject()/MdImage()` creation) → controller. Next devlog: **191**.
