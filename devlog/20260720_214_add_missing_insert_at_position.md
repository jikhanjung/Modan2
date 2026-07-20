# 214 — Insert "Add Missing" placeholders at the selected row

**Date:** 2026-07-20
**Type:** implementation (NNN) — UX fix
**Related:** `devlog/20260720_209_landmark_blank_field_parsing.md` (follow-up 4)

## Problem

"Add Missing" appended `[None, None]` to the **end** of the landmark list, always.
But landmark identity is positional — landmark 3 of a file is row 3 here — so an
end-appended placeholder is in the wrong place by construction whenever the gap
is anywhere but last.

Marking landmark 3 of 5 missing therefore meant the roundabout route: select row
3, clear X and Y, commit. The button could not do the one thing its name
promises.

## Behaviour

- **A row is selected** — the placeholder is inserted *before* it, so the new row
  takes the selected row's number and everything below shifts down. Spreadsheet
  convention: "insert here" puts the new thing where you were pointing.
- **Nothing selected** — appends, as before.
- The new row is left selected, so consecutive clicks stack placeholders in
  order rather than walking backwards up the list.

A tooltip now states the rule, since the button text alone cannot.

## Bug found while verifying: stale coordinate inputs

`QTableWidget.selectRow` emits nothing when that row was **already** selected —
the common case here, since the user selects row N and inserts at row N. So
`on_landmark_selected` did not re-run and the X/Y inputs kept showing the
*previous* landmark's coordinates while a blank row sat selected. Clicking
Update then wrote those stale coordinates straight into the new placeholder,
quietly filling the gap the user had just created.

Fixed by calling `on_landmark_selected()` explicitly after `selectRow`. Caught
only by driving the real handler with real input widgets — the unit tests stub it
out, so `TestCoordinateInputsAreSynced` builds a dialog with genuine `QLineEdit`s
to pin it.

## Note on landmark counts

Inserting into one object makes its landmark count differ from its siblings,
which `check_object_list` rejects. That is the intended use, not a regression:
this is how an object that is short a landmark gets brought up to the dataset's
count.

## Verification

- `tests/test_add_missing_landmark.py` (new, 16 tests): insert before first /
  middle / last row, append on no-selection and on an out-of-range index, empty
  list, 2D vs 3D placeholder width, no-dataset no-op, selection following the
  insert, consecutive inserts ordering, table rendering, viewer refresh, and the
  coordinate-input sync above.
- Full suite: **1351 passed, 75 skipped** (was 1335 + 16 new).

## Missing-landmark follow-ups from devlog 209: all closed

1. cell validator — 211
2. `make_landmark_str` `None` guard — 211
3. `-999` recognised on import — 213
4. insert-at-position — this devlog
