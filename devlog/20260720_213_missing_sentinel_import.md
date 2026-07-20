# 213 — Ask whether `-999` means "missing landmark" on import

**Date:** 2026-07-20
**Type:** implementation (NNN) — feature
**Related:** `devlog/20260720_209_landmark_blank_field_parsing.md` (follow-up 3)

## Problem

`-999` is the morphometrics convention for "this landmark was not recorded"
(tpsDig and friends write it; geomorph reads it as `NA`). Modan2 had no notion of
it: `unpack_landmark` parses `-999` as a perfectly valid float, so every sentinel
imported as a **real point at (-999, -999)**, dragging the centroid and wrecking
the Procrustes fit — silently, with no warning anywhere.

Converting unconditionally is not safe either: a dataset *could* legitimately
contain -999. So the import asks.

## Behaviour

After parsing and before persisting, the import scans the landmark data. If any
sentinel is found:

> **Missing landmarks**
> Found 3 coordinate(s) with the value -999.
> -999 is the usual placeholder for a landmark that was not recorded. Treat these
> as missing landmarks?
> *If you keep them, they are imported as real coordinates.*
> ☐ Always treat -999 as a missing landmark
> **[Yes]** [No] [Cancel]

- **Yes** (default) — each sentinel becomes `None`, persisted as the `Missing`
  marker the rest of the pipeline already understands.
- **No** — imported verbatim as coordinates.
- **Cancel** — aborts the import, data untouched.
- **Checkbox** — remembers the answer in `Import/TreatSentinelAsMissing` and
  skips the prompt from then on. Unset means ask again.

No sentinels in the file → no prompt.

## The invert-Y trap

The format readers apply invert-Y **inside the constructor**, i.e. *before* the
scan runs. A `-999` in the Y column has already been negated to `+999` by then,
so a naive `value == -999` test silently misses every Y sentinel whenever the
user ticks "invert Y" — exactly the case that looks like it works.

`find_missing_sentinels(landmark_data, inverted_y=...)` therefore flips the
target for column 1 when invert-Y is on. Verified end-to-end against a real TPS
file: both `invertY=False` and `invertY=True` find the same 3 sentinels, while
genuine coordinates invert normally (20.0 → -20.0).

Deliberately *not* done: matching `abs(value) == 999`. That would catch the
inverted case without threading the flag through, but it also swallows a real
+999 coordinate — and with "always" ticked the user would never be asked again.

## Implementation

- `MdUtils.find_missing_sentinels(landmark_data, inverted_y, sentinel)` → list of
  `(object_name, row, col)`; `MdUtils.replace_missing_sentinels(data, hits)`
  blanks them in place. Split in two so the count can be reported in the prompt
  before anything is mutated, and so nothing is touched when the user cancels.
- `ImportDatasetDialog._resolve_missing_sentinels` / `_ask_about_sentinels` —
  the ask/remember/convert decision, kept separate from the `QMessageBox` so the
  logic is testable without a live dialog.
- `ModanController._import_object` now writes `None` as `Missing` rather than
  `str(None)` → `"None"`. Both happen to round-trip (`unpack_landmark` maps any
  non-numeric token to `None`), but `"None"` in the DB is not the documented
  format and `pack_landmark` already writes `Missing`.

## Verification

- `tests/test_missing_sentinel_import.py` (new, 32 tests): detection across
  columns/objects/3D, near-misses (`-999.5`, `-99`, `999`) rejected, invert-Y in
  both directions, in-place replacement, the full ask/remember/cancel matrix
  (including QSettings handing booleans back as `"true"`), and the controller
  storing `Missing` and round-tripping to `None`.
- Live dialog checked offscreen: title, text, checkbox label, and **Yes as the
  default button**.
- End-to-end against a TPS file with sentinels in both a full landmark and a
  single coordinate.
- Full suite: **1335 passed, 75 skipped**.

## Still open (from devlog 209)

4. "Add Missing" only appends at the end — no insert-at-position.

Also unaddressed: the JSON+ZIP import path (`_import_json_zip`) bypasses this
scan entirely, since it restores an already-Modan2-native dataset where missing
landmarks are stored as `Missing`.
