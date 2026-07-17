# 180 — Decompose `prepare_scatter_data` into phase helpers

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 1, `prepare_scatter_data` god-method)
**Related:** `devlog/20260717_179_...` (golden-master net), `HANDOFF.md`

## What

Split `DataExplorationDialog.prepare_scatter_data` (~285 lines) into an
orchestrator plus five phase helpers, each mutating the same `self.*` scatter
state in place:

| Helper | Responsibility |
|---|---|
| `_read_scatter_options()` | read option widgets (checkboxes, axes, flips) → dict |
| `_resolve_scatter_variables()` | grouping/regression variable name → column index |
| `_init_scatter_containers(size, default_color)` | reset stores + data_range, drop old shape-grid views, seed `__default__` |
| `_populate_scatter_groups(opts, size)` | per-object group assignment + x/y/z accumulation + running range |
| `_build_shape_grid()` | 3×3 min/avg/max shape-grid view construction |
| `_finalize_scatter_groups(opts, colors, symbols)` | drop empty default, average shapes, convex hull, confidence ellipse, colour/symbol assignment |

`prepare_scatter_data` is now a ~15-line orchestrator.

## Why

Largest and highest-risk Batch C god-method, and near-duplicated with
`dataset_analysis_dialog.show_analysis_result`. Decomposing into named phases makes
the shared structure explicit and sets up the item 2 shared-builder extraction
(these helpers are the natural seams to lift into a shared mixin/builder).

## Behavior preservation

Behavior-preserving, verified by the golden-master added in 179. Dead code removed
in the move (no functional effect):
- duplicate `symbol_candidate`/`color_candidate` literal assignments that were
  immediately overwritten by `self.marker_list`/`self.color_list`;
- two discarded widget reads (`comboRegressionBasedOn.currentText()`,
  `cbxRegression.isChecked()`) whose results were never used;
- an unused `key_list` accumulator and commented-out `regression_by` cruft.

`select_group_list` is still computed in `_read_scatter_options` (its only
consumers are commented-out) — left in place as it is harmless and documents intent.

## Verification

- `ruff check` + `ruff format --check` — clean.
- `pytest tests/dialogs/test_data_exploration_scatter.py` — 2 passed (golden green
  pre- and post-refactor).
- `pytest tests/dialogs/ tests/test_analysis_info_widget.py
  tests/test_modan2_menu_actions.py` — 232 passed, 23 skipped.

## Next

Item 2 — extract a shared scatter-plot builder between
`data_exploration_dialog` and `dataset_analysis_dialog.show_analysis_result`
(the golden net now guards the exploration side). Or continue item 1 god-methods
(`Modan2.py read_settings`, dialog `__init__`s). Next devlog: **181**.
