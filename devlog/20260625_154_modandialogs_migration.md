# ModanDialogs.py Removal (Legacy Dialog Migration)

**Date**: 2026-06-25
**Type**: Implementation log
**Follows**: [R01 Code Review](20260625_R01_code_review_legacy_and_db_patterns.md), [153 Test Isolation](20260625_153_test_isolation_and_overlay_shortcut.md)

---

## Summary

Deleted the 2539-line `ModanDialogs.py` — the single largest piece of dead code
identified in R01. Every dialog it defined had already been re-implemented in the
`dialogs/` package; the legacy file survived only because of one constant import
and stale test imports.

Net change: **+100 / −2637 lines** across 9 files. Full suite stays green
(**1181 passed, 74 skipped, 0 failed**).

---

## What was done

### 1. Relocate the `MODE` constant
`Modan2.py:71` was the only production importer of `ModanDialogs` (`from
ModanDialogs import MODE`). Added the canonical `MODE` dict to `MdConstants.py`
(UI Interaction Modes section) and repointed the import to
`from MdConstants import MODE`.

> Note: `MODE` is duplicated verbatim in ~16 UI modules (viewers, widgets,
> format handlers, `dialogs/object_dialog.py`, `ModanComponents.py`). This commit
> only establishes the canonical copy consumed by `Modan2.py`; de-duplicating the
> other copies is a separate cleanup.

### 2. Repoint test imports to the `dialogs/` package
`dialogs/__init__.py` already re-exports every needed class under the same name,
so `from ModanDialogs import X` → `from dialogs import X` across 5 test files
(`test_dataset_dialog_direct`, `test_analysis_workflow`, `test_import`,
`test_legacy_integration`, `test_ui_dialogs`). Also updated the
`@patch("ModanDialogs.<Class>.<method>")` decorators in `test_ui_dialogs.py` to
`@patch("dialogs.<Class>...")` (those test classes are `@pytest.mark.skip`, but
the targets are now correct if ever un-skipped).

`test_workflows.py` still contains `patch("ModanDialogs.Md*Dialog")` references,
but those tests are skipped **and** reference class names (`MdNewDatasetDialog`,
…) that never existed in any current module — left as-is (pre-existing dead,
skipped code; out of scope).

### 3. Delete `ModanDialogs.py` + clean up config
- `git rm ModanDialogs.py`
- `pyproject.toml`: removed the now-dead `ModanDialogs` entry from
  `known-first-party` and its `per-file-ignores` rule.
- `Modan2.py`: updated the (non-executed) `pylupdate5` i18n notes in the trailing
  docstring to reference `dialogs/*.py components/**/*.py` instead of the deleted
  file.

### 4. Fix tests that relied on legacy dialog behavior
Repointing surfaced a real interface difference (exactly the risk flagged in
R01): the migrated dialogs extend `BaseDialog`, whose `__init__` forwards the
parent to `QDialog.__init__`. The legacy `ModanDialogs` versions tolerated a
`Mock()` parent; the new ones raise:

```
TypeError: QDialog(...): argument 1 has unexpected type 'Mock'
```

Affected `DatasetDialog` / `ImportDatasetDialog` / `NewAnalysisDialog` tests
(13 tests across `test_legacy_integration.py`, `test_import.py`,
`test_analysis_workflow.py`). Fix: replace the `Mock()` parents with a real
`QWidget` parent (`parent = QWidget(); qtbot.addWidget(parent)`), which satisfies
both `QDialog.__init__` and the `self.parent.pos()` call in `read_settings`.

- `ObjectDialog` tests in `test_dataset_dialog_direct.py` were **not** changed:
  `ObjectDialog` extends `QDialog` directly and still tolerates a `Mock` parent,
  so those tests already passed.
- `test_dialog_with_invalid_parent` previously asserted graceful handling of a
  parent that raises on `pos()`. The migrated dialog reads geometry from settings
  (no `pos()` call in the default path), so that premise no longer applies; the
  test was reduced to a real-parent construction check.

---

## Verification

```
test_legacy_integration.py     10 passed
test_import.py                  8 passed
test_analysis_workflow.py       4 passed, 2 skipped
Full suite:                  1181 passed, 74 skipped, 0 failed
```

Smoke checks: `from MdConstants import MODE`, `from dialogs import DatasetDialog,
ImportDatasetDialog, NewAnalysisDialog, PreferencesDialog`, and AST parse of
`Modan2.py` / `MdConstants.py` all succeed.

## Files changed
- `MdConstants.py` — add canonical `MODE`
- `Modan2.py` — import `MODE` from `MdConstants`; update i18n note
- `ModanDialogs.py` — **deleted (2539 lines)**
- `pyproject.toml` — drop dead `ModanDialogs` config
- `tests/{test_dataset_dialog_direct,test_analysis_workflow,test_import,test_legacy_integration,test_ui_dialogs}.py`
  — repoint imports; real `QWidget` parents

## Next candidates
1. De-duplicate the ~16 copies of the `MODE` dict (import from `MdConstants`).
2. DB correctness items from R01: C1 (controller `.create()` field names),
   C2 (class-level mutable list attrs), C4 (missing `atomic()` transactions).
3. `numpy==1.26` (pinned) vs `2.5.0` (installed) version mismatch.
