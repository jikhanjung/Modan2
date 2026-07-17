# 192 — Hoist geometry-restore into `BaseDialog._restore_geometry`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 4, read_settings / color-marker hoist)
**Related:** `HANDOFF.md`, `TODOs.md`

## What

Added `BaseDialog._restore_geometry(geometry_key, default_rect, move_offset=None)`,
which encapsulates the copy-pasted `read_settings` geometry block (set
`remember_geometry` from `WindowGeometry/RememberGeometry`; restore saved geometry or
fall back to a default rect, optionally moved relative to the parent).

Applied it in the three BaseDialog-derived dialogs whose `read_settings` was a
near-verbatim copy:
- `DatasetDialog` → key `WindowGeometry/DatasetDialog`, default 600×400, move (100,100)
- `ExportDatasetDialog` → `WindowGeometry/ExportDialog`, 600×400, move (50,50)
- `AnalysisResultDialog` → `WindowGeometry/AnalysisResultDialog`, 1400×800, no move
  (keeps its `hasattr(self.m_app, "settings")` guard)

Each `read_settings` collapses to a single delegating call.

## Scope note

Only BaseDialog-derived dialogs can use the method. `ObjectDialog`,
`DatasetAnalysisDialog`, and `DataExplorationDialog` extend `QDialog` directly (not
BaseDialog) and are left as-is here; the shared **colour/marker** loop those last two
duplicate is handled separately via a module-level helper (devlog 193), since it
doesn't require inheritance.

## Behavior preservation

Verbatim: `move_offset=None` reproduces the branches that set a default rect without
moving (AnalysisResultDialog); the QPoint offsets match each original.

## Verification

- `ruff check` (+ autofix unused `mu` import) + `ruff format` — clean.
- `pytest tests/dialogs/test_dataset_dialog.py tests/dialogs/test_export_dialog.py
  tests/dialogs/test_analysis_result_dialog.py tests/dialogs/test_base_dialog.py`
  — 99 passed.

## Next

**193**: apply the shared `load_color_marker_lists` helper (already added to
`base_dialog.py`) in `DataExplorationDialog` / `DatasetAnalysisDialog`. Next devlog: **193**.
