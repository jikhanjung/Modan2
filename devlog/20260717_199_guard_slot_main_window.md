# 199 — Add `guard_slot` decorator; apply to main-window High-risk slots

**Date:** 2026-07-17
**Type:** implementation (NNN) — error-handling hardening (audit 198, batch 1)
**Related:** `devlog/20260717_198_error_handling_audit.md`

## What

Added `MdHelpers.guard_slot(user_message)` — a decorator for Qt signal handlers that
wraps the body in `try/except`: on any exception it logs with a traceback, pops any
leftover override (wait) cursor, and shows a `QMessageBox.critical`. This converts a
silent window death into a visible, recoverable error.

```python
@guard_slot("Failed to delete object")
def on_action_delete_object_triggered(self): ...
```

Applied to the High-priority `Modan2.py` slots from the audit:
- drop/import: `dropEvent`, `tableView_drop_event` (the latter also left the wait
  cursor stuck on error — the decorator pops it);
- DB delete/save: `on_action_delete_object_triggered`,
  `on_action_delete_analysis_triggered`, `on_btnSaveChanges_clicked`,
  `on_action_add_variable_triggered`;
- open-dialog chains: `on_treeView_doubleClicked`, `on_tableView_doubleClicked`;
- `load_dataset` — highest leverage: it's the Reload action target **and** is called
  from every controller-signal refresh (`on_dataset_created/updated`,
  `on_object_added/updated`, `on_analysis_completed`), so one guard covers them all.

## Behavior

On success: unchanged (pure pass-through). On failure: logged + dialog + returns
`None` (slot return values are ignored by Qt). The cursor-pop loop
(`while overrideCursor() is not None: restoreOverrideCursor()`) fixes the
stuck-wait-cursor symptom.

## Verification

- `ruff check` + `ruff format --check` — clean; `ast.parse` OK.
- `tests/test_guard_slot.py` (3 tests): pass-through on success, catch+dialog on
  error, override-cursor restored after a failing handler.
- `pytest tests/test_analysis_workflow.py tests/test_object_overlay_persistence.py
  tests/test_modan2_toolbar_actions.py tests/test_object_workflows.py` — 44 passed,
  12 skipped.

## Next (audit batches)

200: parser hardening (TPS/NTS/X1Y1/Morphologika + import_dialog). 201: 3D-model I/O
symmetry (`MdThreeDModel.add_file`, `set_threed_model` .ply/.stl). 202: dialog High
slots (`on_btn_analysis_clicked`, `export_dataset`, `calibration.btnOK_clicked`,
`dataset_dialog.Delete`).
