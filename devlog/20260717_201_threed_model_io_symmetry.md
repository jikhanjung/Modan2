# 201 — 3D-model I/O hardening (audit batch 3, group G)

**Date:** 2026-07-17
**Type:** implementation (NNN) — error-handling hardening
**Related:** `devlog/20260717_198_error_handling_audit.md`, `199_...`, `200_...`

## What

### `MdThreeDModel.add_file` — mirror the guarded image path
It performed `os.makedirs` + `shutil.copyfile` with no handling (asymmetric with the
fully-guarded `MdImage.add_file`), so a disk/permission failure could raise uncaught
mid-add and leave a 3D-model row without its file. Rewrote it to mirror
`MdImage.add_file`: typed `ValueError` + `logger.error` on makedirs/copyfile failure,
and an outer log-and-reraise. The `os.stat` in `load_file_info` is now covered by this
outer guard.

### `ObjectViewer3D.set_threed_model` — guard OBJ parse, stop silent no-op
Only `.obj` was handled; `.ply`/`.stl` silently did nothing, and `OBJ(file_path)`
parsing was unguarded. Now the OBJ parse is wrapped (typed `ValueError` + log), and a
non-obj path logs a warning instead of silently loading nothing. (Real flows convert
stl/ply → obj via `mu.process_3d_file` first, which already raises on bad meshes, so
non-obj only reaches here as an edge case.)

### Guard the callers of the now-raising `set_threed_model`
- `ObjectViewer3D.dropEvent` (drop a 3D file onto the viewer) → `@guard_slot`
- `ObjectDialog.btnAddFile_clicked` (Load Image / 3D file button) → `@guard_slot`

So a corrupt/unsupported model surfaces an error dialog instead of killing the window.

## Behavior preservation

Success paths unchanged. Failures now log + (for the guarded slots) show a dialog
instead of crashing. No circular import: `MdHelpers` imports only PyQt/stdlib.

## Verification

- `ruff check` + `ruff format --check` — clean; `ast.parse` OK.
- New `tests/test_threed_model_io.py`: `add_file` with a missing source raises
  (surfaced) rather than silently creating a fileless row.
- `pytest tests/test_mdmodel.py tests/test_object_workflows.py
  tests/test_dataset_core.py tests/dialogs/test_dataset_analysis_scatter.py`
  — 292 passed.

## Next

202: remaining dialog High slots — `dataset_analysis_dialog.on_btn_analysis_clicked`
(numpy + wait cursor), `export_dialog.export_dataset`, `calibration_dialog.btnOK_clicked`,
`dataset_dialog.Delete`.
