# 186 — Extract `_restore_main_window_geometry` from `read_settings`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 1, `Modan2.py read_settings` — final step)
**Related:** `devlog/20260717_185_...`

## What

Extracted the `if self.m_app.remember_geometry: ... else: ...` geometry-restore
block (~87 lines, including the nested `verify_position` and all the multi-monitor
debug logging) from `read_settings` into `_restore_main_window_geometry()`.

Combined with 185 (SettingsWrapper hoist), `read_settings` drops from ~247 lines to
**39 lines** and now reads as: guard → app basics → settings wrapper → init-only
block (object-overlay prefs + `self._restore_main_window_geometry()`) → language →
matplotlib rcParams.

## Behavior preservation

Pure move. The helper re-derives its own `logger = logging.getLogger(__name__)`
(same object as the caller's local logger). The nested `verify_position` closure and
its `QTimer.singleShot(100, ...)` scheduling are preserved verbatim.

## Verification

- `ruff check` + `ruff format --check Modan2.py` — clean.
- `pytest tests/test_settings_wrapper.py tests/test_analysis_workflow.py
  tests/test_object_overlay_persistence.py` — 28 passed, 2 skipped (the latter two
  construct `ModanMainWindow` and run `read_settings` including the geometry path).

## Result — `read_settings` god-method done

Item 1's `read_settings` is decomposed (185 SettingsWrapper hoist + 186 geometry
extraction). Remaining item-1 god-methods: the two dialog `__init__`s
(`dataset_analysis_dialog` 371 lines, `object_dialog` 283 lines).

## Next

Decompose `dialogs/dataset_analysis_dialog.py` `__init__` (or `object_dialog`
`__init__`). Next devlog: **187**.
