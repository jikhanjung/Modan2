# 197 — Make the Preferences dialog scrollable (low-res monitors)

**Date:** 2026-07-17
**Type:** implementation (NNN) — UX fix (user-reported)
**Related:** user report (bottom of Preferences clipped on low-res monitors)

## Problem

`PreferencesDialog` set its `QFormLayout` directly on the dialog, so the window's
natural height equalled the full form. On low-resolution monitors the bottom rows
(Language, Save button) were clipped and unreachable — no scrolling.

## Fix

`_create_layout` now builds the form into a container `QWidget`, wraps it in a
`QScrollArea` (`setWidgetResizable(True)`), and sets the dialog's layout to a
`QVBoxLayout` of `[scroll_area, btnOkay]`. The **Save button is pinned below** the
scroll area so it's always visible; only the preference rows scroll.

Because a scroll area's own size hint is small, `__init__` now sets a sensible initial
size after layout: `resize(560, min(760, 90% of the screen's available height))` and a
480px minimum width. So it opens showing most of the form on normal monitors and, on
small screens, opens within the screen and scrolls the overflow. Horizontal scrollbar
is disabled (`Qt.ScrollBarAlwaysOff`).

Also hoisted the previously in-method `from PyQt5.QtWidgets import QWidget` to the
module imports (with the new `QScrollArea` / `QVBoxLayout`).

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/dialogs/test_preferences_dialog.py` — 38 passed, incl. a new
  `test_preferences_are_scrollable` asserting the form is in a resizable QScrollArea,
  the dialog's top layout is the outer QVBoxLayout, and the Save button lives outside
  the scrolled widget.
