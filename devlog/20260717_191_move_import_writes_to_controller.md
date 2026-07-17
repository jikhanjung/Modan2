# 191 — Move `ImportDatasetDialog` DB/file writes into `ModanController`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 3, dialog DB/file I/O → controller — final)
**Related:** `devlog/20260717_189_...`, `190_...`

## What

Added `ModanController.import_dataset(import_data, dataset_name, storage_directory,
progress_callback=None)` (plus `_import_object` / `_import_object_image` helpers,
moved verbatim from the dialog) and refactored
`ImportDatasetDialog._execute_import` to delegate.

The dialog now only does UI: builds the parsed `import_data`, shows progress via a
`progress_callback(done, total)` passed to the controller, then shows the completion
message and refreshes the parent. All `MdDataset`/`MdObject`/`MdImage` creation,
`.save()`, `os.makedirs`, and `shutil.copyfile` now live in the controller.

Controller wiring mirrors 189: `self.controller = parent.controller if
isinstance(parent.controller, ModanController) else ModanController()`. Removed the
now-unused `os` / `shutil` / `MdObject` / `MdImage` imports from `import_dialog`
(kept `MdDataset` — still used for the name-uniqueness check); added `import shutil`
to the controller.

## Behavior preservation

Verbatim move. Per-object progress is unchanged: the callback computes
`int(float(done) * 100 / total)` after each object, exactly as the old inline loop
did. Image-import precedence, the `dirname` fallback path, and the missing-file
`logger.error`-and-skip are preserved (`self.logger` in the controller).

## Coverage

`test_import.py` calls `dialog.import_file()` end-to-end for multiple formats
(8 tests), which now exercises `controller.import_dataset` and asserts the dataset /
objects are created — so the delegation is covered without a separate fixture.

## Verification

- `ruff check` (+ autofix of unused imports) + `ruff format` — clean.
- `pytest tests/test_import.py tests/dialogs/test_import_dialog.py
  tests/test_controller_object_io.py` — 35 passed.

## Result — Batch C item 3 done

Dialog DB/file I/O moved to `ModanController`: `save_object` (189),
`delete_object_with_files` (190), `import_dataset` (191). `TODOs.md` updated.

## Next

Batch C item 4: hoist `read_settings` / color-marker loading into `BaseDialog`
(copy-pasted across ~9 dialogs). Next devlog: **192**.
