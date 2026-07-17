# 203 — Guard Med main-window slots + defensive selection parsing (audit batch 5)

**Date:** 2026-07-18
**Type:** implementation (NNN) — error-handling hardening (audit batch 5, Med)
**Related:** `devlog/20260717_198_error_handling_audit.md`, `..._202_...`

## What

First Med batch from the audit (198), all in `Modan2.py`:

- `@guard_slot` on the remaining main-window handlers that reach DB/UI chains
  unguarded: `btnAnalysisDetail_clicked`, `btnDataExploration_clicked`,
  `open_treeview_menu`, `on_action_explore_data_triggered`,
  `on_dataset_selection_changed`, `on_object_selection_changed`.
- **`btnDataExploration_clicked` NameError fix**: `group_by` was only bound inside
  the `PCA/CVA/MANOVA` if/elif chain — any other tab left it unbound and the
  following `set_analysis(...)` raised `NameError`. Now initialized to `""`.
- **`open_treeview_menu` None guard**: `itemFromIndex(index)` can return `None`;
  `item.data()` then raised `AttributeError`. Early-return on `None`.
- **`get_selected_object_list` per-row hardening**: the row read
  `int(self.object_model._data[row][0]["value"])` + `get_by_id` could raise
  `IndexError/KeyError/ValueError/DoesNotExist` and kill the whole selection.
  Now wrapped per row — malformed rows are logged and skipped, the rest still
  resolve. (This helper feeds several slots, so per-row tolerance beats
  all-or-nothing.)

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/test_modan2_*.py tests/test_ui_basic.py` — 44 passed, 37 skipped.

## Audit status

Med items remaining after this batch: `data_exploration_dialog` (ConvexHull,
set_analysis/unrotate_shape JSON), `dataset_analysis_dialog.show_result_table`,
`object_dialog.x_changed`, `MdModel` (change_dataset, rotation_matrix svd,
rescale ZeroDivision), `MdUtils` zip I/O. Low items untouched.
