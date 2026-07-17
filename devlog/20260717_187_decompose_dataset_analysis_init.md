# 187 — Decompose `DatasetAnalysisDialog.__init__`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 1, dialog `__init__` god-methods)
**Related:** `devlog/20260717_183_...` (smoke-test net), `HANDOFF.md`

## What

Extracted the three largest cohesive widget-construction blocks from the 371-line
`DatasetAnalysisDialog.__init__` into helpers, called in the same order:
- `_init_object_table()` — the object/group table tab + select all/none/invert;
- `_init_plot_area()` — 2D/3D plot canvases, axis & chart-option controls, result
  tables → `self.plot_all_widget`;
- `_init_bottom_controls()` — superimposition / analysis-type / save-results row →
  `self.bottom_layout` + `self.status_bar`.

`__init__` drops from **371 → 132 lines** and now reads as: window/state setup →
shape viewers → `_init_object_table` → `_init_plot_area` → main-splitter assembly →
`_init_bottom_controls` → final layout → analysis state → `set_dataset`.

## Behavior preservation

Pure verbatim relocation (the moved blocks were already at method-body indent, so no
re-indentation). Call order matches the original construction order, and every
widget/layout is still stored on `self`, so the later assembly steps
(`main_hsplitter.addWidget(self.plot_all_widget)`, `main_layout.addLayout(self.bottom_layout)`)
resolve unchanged.

Verified by the 183 smoke test, which constructs the dialog and drives
`show_analysis_result` end-to-end (2D + 3D).

## Verification

- `ast.parse` OK; `ruff check` + `ruff format --check` — clean.
- `pytest tests/dialogs/test_dataset_analysis_scatter.py
  tests/test_multi_analysis_workflow.py tests/test_integration_workflows.py`
  — 21 passed.

## Next

Last item-1 god-method: `dialogs/object_dialog.py` `__init__` (283 lines).
Next devlog: **188**.
