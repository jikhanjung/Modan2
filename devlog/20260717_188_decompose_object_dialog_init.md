# 188 — Decompose `ObjectDialog.__init__`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 1, dialog `__init__` god-methods — final)
**Related:** `devlog/20260717_187_...`, `HANDOFF.md`

## What

Extracted four cohesive widget-construction blocks from the 283-line
`ObjectDialog.__init__` into helpers, called in the original order:
- `_init_coord_input()` — the two-row X/Y/Z coordinate-input panel + its signals;
- `_init_tool_buttons()` — the landmark/wireframe/calibration exclusive PicButton group;
- `_init_option_checkboxes()` — the view-option checkboxes + Load-Image button;
- `_init_action_buttons()` — Previous/Save/Delete/Cancel/Next row + main-layout assembly.

`__init__` drops from **283 → 146 lines**.

## Behavior preservation

Pure verbatim relocation (blocks already at method-body indent). Call order matches
the original so cross-references resolve: `_init_coord_input` runs before
`form_layout.addRow("", self.inputWidget)`; `_init_tool_buttons` before
`right_top_widget.setLayout(self.btn_layout2)`; `_init_option_checkboxes` before the
`right_middle_layout.addWidget(self.cbxShowIndex/…)` assembly. The later checkbox
signal wiring (`show_index_state_changed`, …) stays inline at the end of `__init__`.

`ObjectDialog(parent=…)` is constructed directly by many existing tests
(`test_dataset_core`, `test_object_workflows`, `test_dataset_dialog_direct`, …), which
provide the construction safety net.

## Verification

- `ast.parse` OK; `ruff check` + `ruff format --check` — clean.
- `pytest tests/test_dataset_core.py tests/test_object_workflows.py
  tests/test_dataset_dialog_direct.py tests/test_ui_dialogs.py`
  — 49 passed, 19 skipped.

## Result — Batch C item 1 (god-methods) complete

All five item-1 god-methods are decomposed: `run_analysis` (176–178),
`prepare_scatter_data` (179–180), `read_settings` (185–186),
`DatasetAnalysisDialog.__init__` (187), `ObjectDialog.__init__` (188). `TODOs.md`
updated.

## Next

Batch C items 3–4: move dialog DB/file I/O into `ModanController`; hoist
`read_settings`/color-marker loading into `BaseDialog`. Next devlog: **189**.
