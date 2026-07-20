# 209 — Fix blank-cell landmark parsing (IndexError crash + silent coord shift)

**Date:** 2026-07-20
**Type:** implementation (NNN) — correctness fix
**Related:** `devlog/20251004_060_missing_landmark_visualization_implementation.md`

## Symptom

Clearing a cell in the ObjectDialog landmark table crashed every downstream
consumer of that object, taking the whole dataset's analysis with it:

```
landmark_list = [[1.0, 2.0], [], [3.0, 4.0]]
has_missing_landmarks       -> IndexError: list index out of range
procrustes_superimposition  -> IndexError: list index out of range
count_landmarks             -> IndexError: list index out of range
```

The table is directly editable — `edtLandmarkStr` never sets `setEditTriggers`,
so `QTableWidget`'s default (double-click / any-key) applies — making this a
plain user action, not an edge case. `make_landmark_str` writes the cleared cell
out as an empty field, so the object persists in the broken state.

## Root cause

One line in `MdObject.unpack_landmark`:

```python
coords = [x.strip() for x in coords if x.strip()]   # drops blanks *and* their position
```

The `if x.strip()` filter ran regardless of separator. It exists to absorb the
empty strings a run of spaces produces, but it was also applied to tab- and
comma-delimited rows, where an empty field is a **missing coordinate at a known
position**, not padding. So:

| stored | parsed (before) |
|---|---|
| `"\t"` (both cells cleared) | `[]` |
| `"5.0\t"` (Y cleared) | `[5.0]` |
| `"\t5.0"` (X cleared) | `[5.0]` |

The rest of the codebase indexes `lm[0]`/`lm[1]`/`lm[2]` unconditionally, so a
short row raises. The third row above is worse than a crash: it parses without
error but **shifts Y into X's slot** — silent coordinate corruption.

## Fix

1. **Separator-aware blank handling** — tab/comma are positional, so their empty
   fields are kept and become `None`; whitespace runs stay filtered as before.
2. **`_normalize_landmark_widths()`** (new) — gives every row one slot per
   dimension, so the unconditional `lm[0]`/`lm[1]`/`lm[2]` indexing elsewhere is
   structurally safe. Width comes from `self.dataset.dimension` (mirroring what
   `pack_landmark` already does), falling back to the widest row when the
   dataset isn't reachable, floored at 2. Only **trailing `None`** is trimmed —
   a row with more real numbers than the dataset dimension keeps them, so data
   loss is never silent.

## Behaviour

| input | before | after |
|---|---|---|
| `"\t"` | `[]` 💥 | `[None, None]` |
| `"5.0\t"` | `[5.0]` 💥 | `[5.0, None]` |
| `"\t5.0"` | `[5.0]` (X/Y swapped) | `[None, 5.0]` |
| `"1.0,2.0,"` | `[1.0, 2.0]` | `[1.0, 2.0]` (unchanged) |
| `"1.0  2.0"` | `[1.0, 2.0]` | `[1.0, 2.0]` (unchanged) |
| `"1.0\t2.0\t9.0"` in a 2D dataset | `[1.0, 2.0, 9.0]` | `[1.0, 2.0, 9.0]` (real values kept) |

`Missing` / `NA` / any non-numeric token keeps mapping to `None` as before.

## Verification

- `tests/test_landmark_parsing.py` (new, 17 tests): positional blanks (2D + 3D),
  width normalisation, whitespace separators unchanged, and the three
  previously-crashing calls (`count_landmarks`, `has_missing_landmarks`,
  `procrustes_superimposition`).
- End-to-end: a dataset containing an object with a cleared cell now completes
  Procrustes → PCA with finite scores and no residual `None`.
- Full suite: **1273 passed, 75 skipped** (was 1256 + 17 new).

## Notes / follow-ups

Found while tracing how ObjectDialog marks landmarks missing. Related gaps still
open, in priority order:

1. **Table cell validator** — accept only a number or `MISSING`; today any typo
   silently becomes a missing landmark (`unpack_landmark` maps every
   non-numeric token to `None`).
2. **`make_landmark_str` has no `None`-item guard** (`object_dialog.py:1114`) —
   `.item(row, col).text()` raises `AttributeError` on an unpopulated cell.
3. **`-999` is not recognised as missing on import** — the morphometrics
   convention parses as a real coordinate.
4. **"Add Missing" only appends at the end** — no insert-at-position, so marking
   landmark 3 of 5 missing requires the select-row → clear-X/Y route.
