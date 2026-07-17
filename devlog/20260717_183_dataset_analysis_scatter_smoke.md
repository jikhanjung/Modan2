# 183 — Smoke test for `DatasetAnalysisDialog.show_analysis_result`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 2, rescoped — safety net)
**Related:** `devlog/20260717_182_...`, `devlog/20260717_181_...`

## What

Added `tests/dialogs/test_dataset_analysis_scatter.py`, driving
`DatasetAnalysisDialog.show_analysis_result` end-to-end (2D and 3D chart paths) via
a real PCA on a deterministic 6-object / 2-group dataset. Asserts the `scatter_data`
groups (M/F), colour/symbol assignment, and matplotlib `scatter_result` handles get
built, and the legend path runs without error.

The test reproduces the core of `on_btn_analysis_clicked` while skipping
`show_object_shape` (object-shape GL viewers) so it isolates the scatter/legend path.

## Why

`show_analysis_result` had **no direct end-to-end coverage**. This:
1. Retroactively guards devlog 182 (the `build_scatter_group` factory application in
   this method), which until now rested only on the factory unit tests.
2. Is the safety net for devlog 184 (shared `build_scatter_legend`), which edits this
   method's legend-building body.

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/dialogs/test_dataset_analysis_scatter.py` — 2 passed.

## Next

**184**: apply the shared `build_scatter_legend` helper to the three legend blocks
(exploration ax2, analysis ax2/ax3), now guarded by this test plus the exploration
golden. Next devlog: **184**.
