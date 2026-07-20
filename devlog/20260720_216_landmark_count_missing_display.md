# 216 — Show missing landmarks as a red `(N)` in the object list

**Date:** 2026-07-20
**Type:** implementation (NNN) — feature + latent-crash fix

## What

The object list's Landmarks column now reads `9 (1)`: the number is the count of
*recorded* landmarks, and the red parenthesised figure is how many positions are
missing. Objects with no gaps are unchanged.

## Design

The suffix is **painted**, not folded into the display text, because the cell's
value has to stay an `int` — a composite string would make the column sort
lexicographically (`10, 2, 9`). So:

- `MdTableModel` exposes the missing tally under a new `MISSING_COUNT_ROLE`
  (`Qt.UserRole + 1`); `DisplayRole` still returns the recorded count as an int.
- `appendRows` now passes a caller-supplied cell dict through instead of nesting
  it, so `Modan2.load_object` can hand in `{"value": recorded, "missing": n}`.
  Plain values still get wrapped exactly as before.
- `MdLandmarkCountDelegate` draws the background via the style, then the two text
  segments in different colours, honouring the column's centre alignment and the
  selection palette. It takes the role as a constructor argument to avoid
  importing `table_view` (which already imports `delegates`).

## The latent crash this uncovered

Adding the delegate made `tests/test_object_overlay_persistence.py` **segfault**.
It was not the new code: on a clean tree, adding a bare
`QStyledItemDelegate` on column 3 crashed identically, and the delegate's own
`paint`/`sizeHint` were never even called (verified with file-based tracing,
since prints are lost across a segfault).

The real bug was pre-existing, one line away:

```python
self.tableView.setItemDelegateForColumn(1, MdSequenceDelegate())   # unparented
```

`setItemDelegateForColumn` does **not** take ownership. With no parent and no
Python reference, the delegate was garbage-collected while Qt kept a raw pointer
to it. It had survived on GC-timing luck for as long as it was the only
per-column delegate; allocating a second one shifted that timing and the
dangling pointer was dereferenced on the next paint.

Both delegates are now parented to the view and held on the window. Confirmed by
bisection: on a clean tree, parenting the *existing* delegate alone makes the
added-delegate crash disappear.

### Note for next time

A green suite proved nothing here — the crash needed a specific GC interleaving.
The diagnosis came from bisecting against a stashed tree (`git stash` → add one
line → run) rather than from reading the new code, which was innocent.

Two related smells left alone, since they are not defects today and this commit
is already carrying a crash fix: `MdTableView.paintEvent` ends its painter via
`painter.end() if "painter" in locals() else None`, and it calls `visualRect()`
with that painter active. A first attempt blamed this path and was reverted when
bisection disproved it.

## Verification

- `tests/test_landmark_count_display.py` (new, 13 tests): DisplayRole stays an
  int, the missing tally is exposed separately, `appendRows` still wraps plain
  values and preserves `changed`, **numeric sort is preserved** (`2, 9, 10`, not
  `10, 2, 9`), and the delegate paints with/without missing, when selected,
  grows its size hint for the suffix, and tolerates a non-numeric role value.
- Full suite: **1383 passed, 75 skipped**.
