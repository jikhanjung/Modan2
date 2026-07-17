# 189 — Move `ObjectDialog.save_object` DB/file I/O into `ModanController`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 3, dialog DB/file I/O → controller)
**Related:** `HANDOFF.md`, `TODOs.md`

## What

Added `ModanController.save_object(obj, dataset, *, object_name, sequence,
object_desc, landmark_str, property_str=None, image_path=None, image_changed=False,
model_path=None)` and refactored `ObjectDialog.save_object` to gather UI values and
delegate the persistence. The dialog no longer touches `MdObject().save()`,
`add_image/update_image`, or `add_threed_model` directly — mirroring how
`analysis_dialog` delegates to the controller.

Controller wiring: `ObjectDialog.__init__` now resolves
`self.controller = parent.controller if isinstance(parent.controller,
ModanController) else ModanController()`.

## Behavior preservation

The controller method is a verbatim move of the original logic (field assignment →
`obj.save()` → image-add/update-else-model precedence). `property_str=None` leaves
the field untouched, matching the dialog only setting it when the dataset defines
variables. No try/except or signal emit was added, so exception propagation is
unchanged.

**Test-compat gotcha:** many tests construct `ObjectDialog(parent=Mock())`.
`getattr(Mock(), "controller", None)` returns a *truthy Mock*, not `None`, so a naive
`or ModanController()` fallback left `save_object` calling a Mock no-op (objects
never persisted → 5 failures). The `isinstance(..., ModanController)` guard rejects
Mock/absent controllers and falls back to a real standalone controller, which
persists to the active (monkeypatched) database.

## Verification

- `ruff check` + `ruff format --check` — clean.
- `pytest tests/test_dataset_dialog_direct.py tests/test_dataset_core.py
  tests/test_object_workflows.py tests/test_analysis_workflow.py` — 52 passed,
  2 skipped (these call `dialog.save_object()` directly ~10×).

## Next

**190**: move `ObjectDialog.Delete` file/DB I/O (`os.remove` image file +
`delete_instance`) into the controller. Then `import_dialog` direct DB writes.
Next devlog: **190**.
