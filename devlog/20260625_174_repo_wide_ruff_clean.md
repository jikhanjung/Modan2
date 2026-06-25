# Cleanup — Repo-Wide Ruff Lint/Format Clean

**Date**: 2026-06-25
**Type**: Implementation log
**Trigger**: Running `ruff check .` over the whole repository (not just touched files) while removing the obsolete per-file-ignore stanzas in `pyproject.toml`.
**Follows**: [173 remove dead modules and stale specs](20260625_173_remove_dead_modules_and_stale_specs.md)

---

## Summary

While cleaning up `pyproject.toml` ruff ignores in commit `7fbb2f5`, a full-repo
`ruff check .` surfaced **8 pre-existing lint issues** that had been present on
`HEAD` all along (confirmed via a `git stash` test — they were not introduced by
this session's work; earlier commits only ran `ruff check <specific files>`, never
the whole tree). Fixed them so `ruff check .` is clean repo-wide.

Committed separately from the dead-file removal (`f10d5c0`) to keep that change
focused.

---

## Fixed (via `ruff check --fix .`)

- **`Modan2.py`** — removed three unused imports `QEvent`, `QTimer`, `QTranslator`
  (`F401`). `QTimer` is re-imported locally inside the function that uses it, so
  the module-level binding was dead. Sorted the import block (`I001`).
- **`tests/test_object_overlay_persistence.py`** — removed unused `MdObject`
  import (`F401`); sorted imports (`I001`).
- **`tests/test_analysis_workflow.py`, `tests/test_import.py`** — import-block
  sorting (`I001`).

## Normalized (via `ruff format .`)

Formatting drift in four files (no lint errors, just non-canonical layout):
- `ModanController.py`, `tests/conftest.py`, `tests/test_controller.py` —
  collapsed multi-line `.create(...)` calls that fit within the 120-col limit onto
  a single line.
- `tests/test_mdstatistics.py` — blank line after a test docstring.

## Verification

All changes are behavior-preserving (unused-import removal, import ordering, and
whitespace/line-wrapping only). `ruff check .` now passes for the entire
repository; full suite **1195 passed**, 0 failed.

## Files changed
`Modan2.py`, `ModanController.py`, `tests/conftest.py`, `tests/test_controller.py`,
`tests/test_mdstatistics.py`, `tests/test_analysis_workflow.py`,
`tests/test_import.py`, `tests/test_object_overlay_persistence.py`.
