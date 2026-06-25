# Test Isolation Fix & Overlay Shortcut Test

**Date**: 2026-06-25
**Type**: Implementation log
**Follows**: [152 Dead Code Cleanup & Test Fixes](20260625_152_dead_code_cleanup_and_test_fixes.md)

---

## Summary

Resolved the remaining 8 test failures from the [152] triage. The test suite is
now **fully green**:

```
Start of session:  13 failed, 1168 passed, 74 skipped
After 152 (G1+G3):  8 failed, 1173 passed
After this work:    0 failed, 1181 passed, 74 skipped
```

The 8 failures split into two unrelated causes (the original "GROUP 2" bucket
turned out to contain one mis-categorized test):

1. **7 failures — Qt translator leak** (genuine test-isolation bug)
2. **1 failure — headless QAction shortcut delivery** (mis-bucketed; failed
   standalone, not an isolation issue)

---

## Part 1 — Qt translator leak (7 tests)

### Symptom
Seven UI tests passed in isolation but failed in the full suite, all asserting
on UI strings that came back in **Korean**:

```
assert '모단2 - 새 분석' == 'Modan2 - New Analysis'
assert 'Modan2' in '모단2 v0.1.5-beta.2'
menu bar == ['파일', '편집', 'View', '데이터', '도움말']
```

Affected: `test_analysis_dialog_creation`, `test_analysis_dialog_default_values`,
`test_dataset_dialog_creation`, `test_object_dialog_creation`,
`test_import_dialog_creation`, `test_window_creation`, `test_menu_bar_exists`.

### Root cause
`tests/dialogs/test_preferences_dialog.py::test_language_selection_change` flips
the language combo box, firing `PreferencesDialog.comboLangIndexChanged`
(`dialogs/preferences_dialog.py:622`). That handler does:

```python
self.m_app = QApplication.instance()        # the shared singleton
...
translator = QTranslator()
translator.load(".../Modan2_ko.qm")
self.m_app.installTranslator(translator)    # installed globally, never removed
```

Because `m_app` is the process-wide `QApplication` singleton, the Korean
translator stays installed for **every subsequent test**, so later UI tests read
Korean. Pure ordering dependency — invisible when tests run alone.

### Fix
Added an `autouse` fixture in `tests/conftest.py` that snapshots and restores the
translator/language state around every test:

```python
@pytest.fixture(autouse=True)
def _restore_qt_translation_state():
    app = QApplication.instance()
    saved_translator = getattr(app, "translator", None) if app else None
    saved_language = getattr(app, "language", None) if app else None
    yield
    app = QApplication.instance()
    if app is None:
        return
    current = getattr(app, "translator", None)
    if current is not None and current is not saved_translator:
        app.removeTranslator(current)
        app.translator = saved_translator
    app.language = saved_language if saved_language is not None else "en"
```

- Cheap (attribute reads); no-op for non-Qt tests (`app is None`).
- `tests/conftest.py` already covers `tests/dialogs/` (no nested conftest), so the
  guard reaches the polluting test too.
- Fixes the whole class of issues, not just today's polluter — any future
  language-switching test is now contained.

Result: 7 → 0 of these failures, zero regressions.

## Part 2 — Overlay Ctrl+P shortcut test (1 test)

### Diagnosis
`test_object_overlay_persistence.py::test_keyboard_shortcut_toggles_overlay`
**failed even in isolation** — so it was never an isolation problem (mis-bucketed
in 152's GROUP 2).

It failed at the first `QTest.keyPress(main_window, Qt.Key_P, Qt.ControlModifier)`:
the overlay did not toggle. Evidence it is *not* a product bug:

- `actionTogglePreview` is correctly bound to `Ctrl+P` and added to both the
  toolbar (`Modan2.py:167`) and the View menu (`:195`) — a real user's Ctrl+P
  works.
- A sibling test toggles the same overlay via `QTest.mouseClick` on the toolbar
  button and **passes** → the toggle slot itself is fine.
- `QTest.keyPress`/`keyClick` to a window does not reliably activate QAction
  **shortcuts** under the `offscreen` platform (shortcuts go through the app
  shortcut map, not the focused-widget key path).

### Fix
Rewrote the test to assert the binding and exercise the behavior without relying
on simulated key delivery:

```python
assert main_window.actionTogglePreview.shortcut().toString() == "Ctrl+P"  # binding
main_window.actionTogglePreview.trigger()                                 # behavior
```

This still covers both the Ctrl+P binding and the toggle logic, and is robust
headlessly. `QTest`/`Qt` remain imported (used by other tests in the file).

---

## Result

```
0 failed, 1181 passed, 74 skipped
```

All pre-existing test failures from the start of the session are resolved.

## Files changed
- `tests/conftest.py` — autouse translator/language restore fixture
- `tests/test_object_overlay_persistence.py` — trigger action instead of
  simulating Ctrl+P

## Next candidates
1. `ModanDialogs.py` migration (relocate `MODE` → `MdConstants`, repoint 5 test
   files, delete the 2539-line dead file).
2. DB correctness items from [R01]: C1 (controller `.create()` field names),
   C2 (class-level mutable list attrs), C4 (missing `atomic()` transactions).
3. Investigate the `numpy==1.26` (pinned) vs `2.5.0` (installed) version
   mismatch flagged in [152].
