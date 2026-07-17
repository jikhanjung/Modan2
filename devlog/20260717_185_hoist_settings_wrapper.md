# 185 — Hoist `SettingsWrapper` out of `read_settings`

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 1, `Modan2.py read_settings` god-method)
**Related:** `HANDOFF.md`, `TODOs.md`

## What

`ModanMainWindow.read_settings` (~247 lines) defined a ~125-line `SettingsWrapper`
class **inline** inside an `if not hasattr(...)` block — the "inline nested class"
smell flagged in `TODOs.md`. Moved it to module scope in `Modan2.py` (right after the
module logger, before `ModanMainWindow`). The method body shrinks to:

```python
if not hasattr(self.m_app, "settings"):
    self.m_app.settings = SettingsWrapper(self.config, self)
```

## Why

- Cuts `read_settings` roughly in half and removes a class definition from a
  hot-path method (it was re-parsed conceptually on every call, and buried the
  actual settings-reading logic).
- Makes `SettingsWrapper` independently importable and testable.

## Behavior preservation

Pure move. The class took `config`/`parent` as constructor args (no closure over
method locals). Its `save()` references the module-level `logger` — as a nested
class its methods already resolved `logger` to the module global (not the method's
local `logger`), so module-level placement is identical.

Added `tests/test_settings_wrapper.py` (9 unit tests) covering key mapping, dynamic
`DataPointColor/Marker` keys, `WindowGeometry` → `QRect` conversion, the
`RememberGeometry` non-conversion special case, unmapped-key fallthrough, and
`setValue` nested-write + QRect→list conversion (with `save` stubbed so no
`~/.modan2` write). This class previously had no direct coverage.

## Verification

- `ruff check` + `ruff format --check Modan2.py` — clean; `ast.parse` OK.
- `pytest tests/test_settings_wrapper.py` — 9 passed.
- `pytest tests/test_analysis_workflow.py tests/test_object_overlay_persistence.py`
  — 19 passed, 2 skipped (these construct `ModanMainWindow` and exercise
  `read_settings`, incl. the object-overlay settings path).

## Next

**186**: extract the geometry-restore block (the `if not self.init_done:` body,
~100 lines with the nested `verify_position`) from `read_settings` into a helper,
finishing this god-method. Next devlog: **186**.
