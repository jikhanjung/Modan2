# 178 — Extract `_persist_analysis_results` from `run_analysis`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 1, `run_analysis` decomposition — final step)
**Related:** `devlog/20260717_176_...`, `devlog/20260717_177_...`, `HANDOFF.md`

## What

Final step of the `run_analysis` decomposition. Extracted the largest remaining
chunk — group-name resolution + `MdAnalysis.create` + the best-effort JSON
serialization block (~155 lines) — into a helper:

```python
def _persist_analysis_results(self, analysis_type, analysis_name,
        superimposition_method, cva_group_by, manova_group_by,
        result, cva_result, manova_result, ds_ops) -> MdAnalysis: ...
```

`run_analysis` now reads as a clean orchestrator:
`_normalize args → _prepare_landmarks → run branches → _persist_analysis_results
→ emit completion`.

## Why

- Removes the last big inline block; `run_analysis`'s body is now a short pipeline.
- Isolates all persistence/serialization concerns (DB write + JSON columns) behind
  one method, so future changes to the stored format touch one place.
- The best-effort `try/except` around JSON generation is preserved inside the
  helper, so a serialization failure still logs a warning and returns the saved
  record rather than failing the analysis.

## Behavior preservation

Behavior-preserving. Signal emission (`analysis_progress(75/100)`,
`analysis_completed`, `info_message`) stays in `run_analysis` around the call, so
signal order/timing is unchanged. `ruff format` reflowed one long CVA `elif`
condition (whitespace only). No logic changes.

Note (unchanged, deliberately): the `analysis_type == "PCA"` bare-string check
inside the persistence path (vs `.upper()` used for dispatch) is carried over
verbatim. Harmonizing it is a behavior change reserved for a separate fix commit,
consistent with 176/177.

## Verification

- `ruff check` + `ruff format --check ModanController.py` — clean.
- `pytest tests/test_controller.py tests/test_analysis_workflow.py
  tests/test_integration_workflows.py tests/dialogs/test_analysis_dialog.py`
  — 144 passed, 2 skipped.

## Result — item 1 (god-method `run_analysis`) done

`run_analysis` decomposed across 176–178 into `_extract_group_values`,
`_prepare_landmarks`, `_persist_analysis_results`. The type-overloaded-return
smell is resolved: `run_analysis` consistently returns `MdAnalysis | None`, and
the internal result dicts are confined to the run/persist helpers.

## Next

Batch C item 1 remaining god-methods (`Modan2.py read_settings`, dialog
`__init__`s, `prepare_scatter_data`), or item 2 (shared scatter-plot builder).
Next devlog: **179**.
