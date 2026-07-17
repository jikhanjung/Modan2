# 195 — Fix two silent crashes: dataset-tree click and analysis Excel export

**Date:** 2026-07-17
**Type:** implementation (NNN) — bug fixes (user-reported)
**Related:** user report (mid-session)

Two "the window just dies with no message" bugs — both unhandled exceptions escaping
Qt slots. Fixed defensively (surface/skip instead of dying) and repaired the likely
root causes.

## Bug 1 — clicking a dataset in the tree silently dies

`ModanMainWindow.load_object` (run from the tree-selection slot
`on_dataset_selected_from_tree`) loops over every object building a table row via
`obj.count_landmarks()` / `obj.get_centroid_size()` / `obj.unpack_variable()`. One
object with malformed/empty landmark or variable data raises, the exception escapes
the slot, and the window appears to die on click.

**Fix:** wrap the per-object row build in `try/except` — log the offending object id/
name and skip it, so the rest of the dataset still loads. Also renamed the inner loop
variable (`idx` → `var_idx`) that shadowed the outer enumerate index.

## Bug 2 — "Save Results" → Excel export silently dies

`DatasetAnalysisDialog.on_btnSaveResults_clicked` wrote four worksheets with **no**
error handling. Several fragile spots could raise and kill the dialog silently:
- `header.extend("CSize")` — extends with the *characters* `C,S,i,z,e` (a bug) rather
  than appending the column name;
- `obj.variable_list[j]` — `IndexError` when an object has fewer variables than the
  dataset defines;
- `self.shape_list.tolist()` — `AttributeError` when `shape_list` is a plain list, not
  a numpy array;
- `self.analysis_result.raw_eigen_values` / `eigen_value_percentages` — may be absent
  on some result types.

**Fix:**
- Wrap the whole export in `try/except`; on failure log with traceback, close the
  half-written workbook, and show a `QMessageBox.critical` — no more silent death.
- `header.append("CSize")` instead of `extend`.
- Guard `variable_list[j]` with a bounds check (blank when missing).
- `shape_list.tolist() if hasattr(..., "tolist") else shape_list`.
- Compute the CSize column index explicitly instead of relying on the post-loop
  value of `k` (also avoids a `NameError` on an empty coordinate row).

## Tests

Added to `tests/dialogs/test_dataset_analysis_scatter.py` (reusing the smoke fixture,
which runs a real PCA and `show_result_table`, populating `shape_list`/eigenvalues):
- `test_save_results_writes_xlsx` — the **success** path now exports an `.xlsx`
  end-to-end without crashing (the export had no prior test).
- `test_save_results_surfaces_error_instead_of_crashing` — a forced mid-export failure
  shows `QMessageBox.critical` and does **not** raise.

## Note

The exact production data that triggered each crash wasn't reproduced here (needs the
app + that dataset), but both slots are now crash-safe and the concrete fragile spots
above are repaired. If a specific dataset still fails to load, the skipped-object
`logger.error` line now names the offending object.

## Verification

- `ruff check` + `ruff format` — clean; `ast.parse` OK.
- `pytest tests/dialogs/test_dataset_analysis_scatter.py` — 4 passed.
