# 179 — Characterization test for `prepare_scatter_data` (pre-refactor safety net)

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 1 prep for `prepare_scatter_data`; also
de-risks item 2 shared scatter-builder)
**Related:** `HANDOFF.md`, `TODOs.md`

## What

Added `tests/dialogs/test_data_exploration_scatter.py` — golden-master
characterization tests for `DataExplorationDialog.prepare_scatter_data`, which had
**zero direct coverage**. Committed *before* touching the method so the upcoming
decomposition can be proven behavior-preserving.

The test:
1. Builds a deterministic 6-object / 2-group / 2D dataset and runs a real
   `ModanController.run_analysis` (PCA + CVA/MANOVA) to produce a persisted
   `MdAnalysis`.
2. Constructs the dialog, calls `set_analysis(...)`, pins axes to PC1/PC2/PC3.
3. Calls `prepare_scatter_data()` and snapshots the resulting `scatter_data`,
   `average_shape`, `regression_data`, and `data_range` into a JSON-able dict.
4. Compares against a frozen `GOLDEN` via a recursive comparator — numbers within
   `abs=1e-6`, strings (colour/symbol) exact — so it tolerates cross-environment FP
   noise but catches any real logic change.

A second test exercises the convex-hull + confidence-ellipse overlay branches
(asserts `hull`/`ellipse` keys get populated per group).

## Why

`prepare_scatter_data` (~285 lines) is the highest-risk Batch C god-method: no
tests, heavy `self.*` mutation, and near-duplicated with
`dataset_analysis_dialog.show_analysis_result` (item 2 territory). A golden-master
net is the responsible precondition for refactoring untested code, and the same
net will guard the later shared-builder extraction.

## Notes / setup quirks

- The dialog's `__init__` calls `read_settings()`, which reads
  `self.m_app.remember_geometry`; with a `None` parent the test sets it `True` to
  avoid the parent-relative `move()` branch.
- Shape-grid overlay is intentionally left off in these tests (it spawns
  `ObjectViewer2D/3D` GL widgets — out of scope for a data-shape characterization).

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/dialogs/test_data_exploration_scatter.py` — 2 passed.

## Next

Decompose `prepare_scatter_data` into phase helpers (read options → init
containers → per-object populate → overlays/colour assignment), keeping this
golden green. Next devlog: **180**.
