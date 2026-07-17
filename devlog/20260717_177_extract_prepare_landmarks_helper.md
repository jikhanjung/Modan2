# 177 — Extract `_prepare_landmarks` helper from `run_analysis`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 1, `run_analysis` decomposition)
**Related:** `devlog/20260717_176_extract_group_values_helper.md`, `HANDOFF.md`

## What

Second micro-step of decomposing `ModanController.run_analysis`. Extracted the
validation + Procrustes + landmark-extraction phase (~34 lines) into a helper:

```python
def _prepare_landmarks(self):
    ...
    return ds_ops, landmarks_data
```

`run_analysis` now calls `ds_ops, landmarks_data = self._prepare_landmarks()` in
place of the inline block. The call stays inside the existing `try:` so the same
`except` still turns any raised `ValueError` into an `analysis_failed` signal.

## Why

- Pulls the prep phase out of the god-method so what remains reads as
  normalize → prepare → run → persist.
- The helper's three `raise ValueError` guards now document the prep contract in
  one place.

## Behavior preservation

Behavior-preserving apart from one dead-code removal: the old block also built an
`object_names` list (appended per object) that was never read anywhere after
construction — dropped it and rewrote the landmark loop as a comprehension.
Verified `object_names` had no other references before removal.

## Verification

- `ruff check ModanController.py` + `ruff format --check` — clean.
- `pytest tests/test_controller.py tests/test_analysis_workflow.py
  tests/test_integration_workflows.py tests/dialogs/test_analysis_dialog.py`
  — 144 passed, 2 skipped.

## Next

Extract `_persist_analysis_results` (the ~135-line `MdAnalysis.create` + JSON
serialization block) — the largest remaining chunk — leaving `run_analysis` as an
orchestrator and clearing the type-overloaded-return smell. Next devlog: **178**.
