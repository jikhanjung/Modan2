# 182 — Apply `build_scatter_group` in `dataset_analysis_dialog`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 2, rescoped)
**Related:** `devlog/20260717_181_...`

## What

Applied the shared `build_scatter_group` factory to the three group-dict seed sites
in `DatasetAnalysisDialog.show_analysis_result`:
- `__default__` seed → `build_scatter_group(scatter_size, symbol="o", color=color_candidate[0], meta=True)`
- `__selected__` seed → `build_scatter_group(SCATTER_LARGE_SIZE, symbol="o", color="red", meta=True)`
- per-group non-default seed → `build_scatter_group(scatter_size, property_name=key_name)`

## Behavior preservation & coverage note

Pure literal→factory replacement. Each call was mapped against the original dict
literal field-by-field; the factory's dict-shape is proven by the unit tests in
`tests/dialogs/test_scatter_utils.py` (181).

**Coverage gap (flagged honestly):** unlike the exploration side, there is **no
direct end-to-end test that calls `DatasetAnalysisDialog.show_analysis_result`** —
the `show_analysis_result` references in `test_analysis_info_widget.py` are for a
different widget and are mostly mocked. This change's confidence therefore rests on
(a) the factory unit tests (exact dict equivalence) and (b) the field-by-field
mapping, not on an integration test hitting the seed path. That is acceptable for a
trivial literal swap; it also means the follow-up legend refactor (183), which is a
*behavioral* change in this same untested method, carries more risk and is being
reconsidered separately.

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/test_multi_analysis_workflow.py tests/test_integration_workflows.py
  tests/test_analysis_info_widget.py` — 38 passed (these exercise the analysis
  workflow but not the plotting seed path; see note above).
- `pytest tests/dialogs/test_scatter_utils.py` — 5 passed.

## Next

Reassess **183** (shared `build_scatter_legend`): it edits the untested
`show_analysis_result` plotting bodies in both dialogs, so it is the shakiest of the
item-2 steps. Decide whether to proceed with it or defer it as not worth the risk
without a characterization harness. Next devlog: **183**.
