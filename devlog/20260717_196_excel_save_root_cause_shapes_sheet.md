# 196 — Root cause of the analysis Excel-save crash: unset `shape_column_header_list`

**Date:** 2026-07-17
**Type:** implementation (NNN) — bug fix (follow-up to 195)
**Related:** `devlog/20260717_195_...`, user report (PCA save crash)

## Root cause found

195 made `on_btnSaveResults_clicked` crash-safe (try/except) and fixed several
fragile spots, but the user confirmed the crash happened on a **PCA** save. Tracing
the actual trigger:

`DatasetAnalysisDialog.show_result_table` contains a large block that computes the
shape grid and assigns `self.shape_list` / `self.shape_name_list` /
`self.shape_column_header_list` — but that entire block (roughly the current lines
1025–1080) is wrapped in a **`"""` triple-quoted string**, i.e. it's commented out.
So `self.shape_column_header_list` is **never assigned** in live code (only
`self.shape_list` / `self.shape_name_list` get `[]` defaults in `__init__`).

The export's "Shapes" worksheet did `for i, colname in enumerate(self.shape_column_header_list)`
→ **`AttributeError: 'DatasetAnalysisDialog' object has no attribute
'shape_column_header_list'`** → the exception escaped the Qt slot → the window died
silently. This hit **both PCA and CVA** (the attribute is never set regardless of
analysis type).

## Fix

Guard the Shapes worksheet: write it only when shape data actually exists
(`getattr(self, "shape_column_header_list", None)` truthy and `shape_list` non-empty).
Since the shape computation is currently disabled, the Shapes sheet is simply skipped
and the export completes with the three real sheets — **Result coordinates**,
**Rotation matrix**, **Eigenvalues** — for both PCA and CVA.

(The 195 try/except remains as a backstop for any other future failure.)

## Test strengthened

`test_save_results_writes_xlsx` now asserts `QMessageBox.critical` was **not** called
(genuine success, not the caught-error path) in addition to the file being written.
Before this fix that assertion would fail — the Shapes-sheet `AttributeError` routed
through the error path (which still wrote a partial file, so the old file-exists check
passed misleadingly).

## Follow-up worth considering (not done here)

The shape-grid feature is dead (commented out) — the "Shapes" result tab and its
export are effectively unimplemented. Either revive the computation or remove the dead
UI/tab. Left as a separate decision.

## Verification

- `ruff check` + `ruff format --check` — clean.
- `pytest tests/dialogs/test_dataset_analysis_scatter.py` — 4 passed (incl. the
  now-genuine success assertion for both the export and the error-handling path).
