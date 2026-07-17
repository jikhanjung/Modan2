# 204 — Guard Med data-exploration paths (audit batch 6)

**Date:** 2026-07-18
**Type:** implementation (NNN) — error-handling hardening (audit batch 6, Med)
**Related:** `devlog/20260717_198_error_handling_audit.md`, `..._203_...`

## What

Second Med batch, all in `dialogs/data_exploration_dialog.py`:

- **`update_chart` → `@guard_slot`**: this is the redraw slot wired to ~10 checkbox
  signals (legend, variance, depth-shade, average, convex hull, confidence ellipse,
  regression, extrapolate, degree, annotation) plus several direct calls. Any
  exception in `prepare_scatter_data`/`calculate_fit`/`show_analysis_result`
  previously killed the window on a checkbox toggle. Now logged + shown.
- **ConvexHull degenerate-group guard** (`_finalize_scatter_groups`): `ConvexHull`
  raises `QhullError` on a collinear/degenerate group; the toggle then crashed even
  though every *other* group was fine. Wrapped per group — the bad group simply gets
  no hull (the drawing side already gates on `"hull" in ...keys()`), the rest render.
- **`unrotate_shape` unbound-variable fix**: `rotation_matrix` was only assigned for
  `PCA`/`CVA`; any other `analysis_method` fell through to `np.linalg.inv(...)` with
  the name unbound → confusing `NameError`. Now raises a clear `ValueError`.

`set_analysis`'s bare `json.loads` calls (object_info/pca/cva) are reached only from
the two entry-point slots guarded in batch 5 (`btnDataExploration_clicked`,
`on_action_explore_data_triggered`), so corrupt-DB-JSON now surfaces as a dialog
rather than a silent death — no redundant guard added here.

## Verification

- `ruff check --fix` (import order) + `ruff format` — clean.
- `pytest -k "exploration"` — 3 passed, 2 skipped.

## Audit status

Med remaining: `dataset_analysis_dialog.show_result_table`, `object_dialog.x_changed`,
`MdModel` (change_dataset, rotation_matrix svd, rescale ZeroDivision), `MdUtils`
zip I/O. Low untouched.
