# 176 — Extract `_extract_group_values` helper from `run_analysis`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 1, `run_analysis` decomposition)
**Related:** `HANDOFF.md`, `TODOs.md`, `devlog/20260625_R01_code_review_legacy_and_db_patterns.md`

## What

First micro-step of decomposing `ModanController.run_analysis` (~360 lines). The
CVA and MANOVA sub-blocks contained two near-verbatim ~20-line copies of the same
group-value extraction logic (map each superimposed object to a variable value by
index, else pass the value through). Extracted them into a single private helper:

```python
def _extract_group_values(self, group_by, ds_ops, objects_by_id, label): ...
```

Both call sites now read as one line each. Net ~40 duplicated lines removed.

## Why

- Kills the largest duplication inside `run_analysis`, the lowest-risk seam to cut
  first before the bigger prepare/persist splits.
- Makes the two remaining differences between the CVA and MANOVA paths explicit
  (only the params dict and the downstream `_run_*` call differ now).

## Behavior preservation

Behavior-preserving refactor. One deliberate **log-only harmonization**: the
original CVA path logged `warning("CVA group_by is string: ...")` when `group_by`
was a string, but the MANOVA path did not. The shared helper now emits the
equivalent warning for both (labelled `CVA`/`MANOVA`). No functional/data effect —
the UI always passes integer indices, so the string branch is a rare fallback.

The two latent inconsistencies noted during survey (dispatch `.upper()` vs bare
`== "PCA"` in persistence; three separate min-object validation thresholds) were
**not** touched here — they are behavior changes and belong in a separate fix
commit, not this structural pass.

## Verification

- `ruff check ModanController.py` + `ruff format --check` — clean.
- `pytest tests/test_controller.py tests/test_analysis_workflow.py` — 100 passed, 2 skipped.
- `pytest tests/test_integration_workflows.py tests/dialogs/test_analysis_dialog.py` — 44 passed.

## Next

Continue `run_analysis` decomposition: extract `_prepare_landmarks` (collect +
Procrustes + landmark extraction), then `_persist_analysis_results` (the ~135-line
MdAnalysis create + JSON block), leaving `run_analysis` as an orchestrator. Next
devlog number: **177**.
