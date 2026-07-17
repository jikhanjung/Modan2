# 193 — Shared `load_color_marker_lists` for the plot dialogs

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 4 — final)
**Related:** `devlog/20260717_192_...`

## What

Applied the module-level `load_color_marker_lists(settings, color_list,
default_color_list, marker_list)` helper (added to `dialogs/base_dialog.py` in 192)
in the two dialogs that duplicated the per-index colour/marker load loops:
`DataExplorationDialog.read_settings` and `DatasetAnalysisDialog.read_settings`. Each
pair of `for` loops collapses to one call.

## Why a free function (not a BaseDialog method)

Both dialogs extend `QDialog` directly, not `BaseDialog`, so they can't inherit a
BaseDialog method. A module-level helper deduplicates the logic without forcing an
inheritance change (which would alter their `super().__init__` contract). This is the
"settings mixin"-style option the TODO allowed for.

## Behavior preservation

Verbatim: identical loop bodies, same default fallbacks
(`default_color_list[i]` / current `marker_list[i]`).

## Verification

- `ruff check` + `ruff format --check` — clean (no circular import: `base_dialog` is
  a leaf module).
- `pytest tests/dialogs/test_data_exploration_scatter.py
  tests/dialogs/test_dataset_analysis_scatter.py` — 5 passed (both construct the
  dialog, exercising `read_settings` → `load_color_marker_lists`).

## Result — Batch C item 4 done, Batch C complete

Item 4 done: geometry-restore hoisted into `BaseDialog._restore_geometry` (192,
3 dialogs) and colour/marker loading shared via `load_color_marker_lists` (193,
2 dialogs). All four Batch C items are now complete — see `TODOs.md`.
