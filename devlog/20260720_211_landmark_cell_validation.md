# 211 — Validate hand-edited landmark cells at commit time

**Date:** 2026-07-20
**Type:** implementation (NNN) — correctness / UX
**Related:** `devlog/20260720_209_landmark_blank_field_parsing.md` (follow-up 1)

## Problem

The landmark table is directly editable (`edtLandmarkStr` never sets
`setEditTriggers`, so `QTableWidget`'s default applies) and nothing checked what
was typed. `unpack_landmark` maps **every** non-numeric token to `None`, so a
typo was indistinguishable from a deliberate missing marker:

```
user types "12.5o"  ->  stored verbatim  ->  parsed as None  ->  landmark is now MISSING
```

No error, no warning — a slip of the finger silently punched a hole in the data
and quietly changed what the analysis ran on.

## Approach — commit-time validation (option B)

Three options were on the table: (a) block invalid keystrokes with a
`QDoubleValidator`, (b) validate when the edit is committed and revert, (c)
accept and merely warn. **(b)** was chosen: (a) fights the user over legitimate
intermediate states (`-`, `1.`, `1e`), and (c) leaves the typo in the data.

`on_landmark_cell_changed` (on `itemChanged`) accepts:

- **a number** — stored as `float`, re-rendered in canonical form (`7` → `7.0`)
- **`MISSING`**, any case — stored as `None`, normalised back to the canonical
  marker
- **a blank cell** — treated as `MISSING`; clearing a cell reads as "no value",
  and this is exactly the gesture that used to crash (devlog 209)

Anything else is reverted to the stored value and reported with a
`QToolTip.showText` at the cell. A tooltip, not a modal — a typo does not
deserve a dialog.

## Side effect worth noting: the table and the model were out of sync

Editing a cell previously updated *only* the table; `self.landmark_list` (which
feeds both viewers) was untouched until save, because `make_landmark_str` reads
the table at save time. So a hand-edited coordinate did not move in the 2D/3D
viewer. The validator now writes accepted values into `landmark_list` and calls
`_refresh_landmark_views()`, so the viewer tracks the edit immediately.

## Refactor

`show_landmarks` had the same 11-line cell-construction block three times (X, Y,
Z) with only the coordinate index varying. Extracted `_make_landmark_item(value)`
and looped over the dimension count — 39 lines → 11, and the styling now lives in
one place, which is what let the validator re-render a cell consistently.

Also added a `None`-item guard in `make_landmark_str` (follow-up 2 of devlog
209): `.item(row, col).text()` raised `AttributeError` on an unpopulated cell;
such a cell now reads as missing.

## Reentrancy

Repopulating the table emits `itemChanged` per cell, and the validator itself
replaces items. `_populating_landmark_table` gates the handler; every
programmatic write goes through `_set_landmark_cell`, which sets and clears the
flag in a `finally`.

## Verification

- `tests/test_landmark_cell_validation.py` (new, 21 tests): accepted forms
  (number, negative, exponent, whitespace, `MISSING` case-insensitive, blank),
  rejected forms (`12.5o`, `abc`, `NA`, `?`, `1,2`, `--3`, `1.2.3`) each
  reverting to the stored value, viewer sync on accept and *not* on reject, the
  suppression flag, and an out-of-range cell.
- `show_landmarks` re-verified end-to-end for 2D and 3D: correct column count,
  `MISSING` markers rendered, and `make_landmark_str` round-tripping.
- Full suite: **1294 passed, 75 skipped** (was 1273 + 21 new).

### Test-harness note

`ObjectDialog.__init__` needs a full app parent, so the fixture builds a bare
instance — but `QDialog.__init__` must still run. Without the C++ base
initialised, **PyQt silently drops a connection to a bound method** and the slot
never fires, which reads exactly like a broken validator. Cost an investigation;
recorded here so the next person skips it.

## Still open (from devlog 209)

3. `-999` is not recognised as missing on import.
4. "Add Missing" only appends at the end — no insert-at-position.
