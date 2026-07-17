# 207 — Harden Med zip import I/O (audit batch 9, final Med)

**Date:** 2026-07-18
**Type:** implementation (NNN) — error-handling hardening (audit batch 9, Med)
**Related:** `devlog/20260717_198_error_handling_audit.md`, `..._206_...`

## What

Final Med batch, `MdUtils.import_dataset_from_zip`:

- **Orphaned-file cleanup on rollback** (the headline bug): the import runs inside
  `gDatabase.atomic()`, so a mid-import failure rolls the DB back — but any media
  already `shutil.copy2`'d into permanent storage stayed on disk, orphaned. Now every
  copied destination is tracked in `copied_files`, and an `except Exception` around
  the atomic block removes them before re-raising. The DB and the filesystem end up
  consistent either way.
- **Corrupt-package clear error**: `safe_extract_zip` / `read_json_from_zip` could
  raise `BadZipFile` / `KeyError` (no `dataset.json`) / `JSONDecodeError` on a
  damaged package. Wrapped to re-raise a single clear `ValueError`.
- **Bad-manifest numeric guards**: `int(dimension)` now raises a clear `ValueError`
  naming the offending value; `float(pixels_per_mm)` on a bad per-object value is
  logged and left unset (one bad object no longer aborts the whole import).

`create_zip_package` (export) was left as-is: its per-file copy is already guarded,
and its `json.dump` / zip-write raise into the already-guarded `_export_json_zip`
caller, so failures surface rather than dying silently.

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest -k "import or zip or mdutils"` — 150 passed, 7 skipped.
- `pytest tests/test_mdutils.py -k "zip or import or package or serialize"` — 20 passed
  (round-trip export→import exercised the rewritten atomic block).

## Audit status — Med complete

All audit **Med** items are now addressed (batches 5–9): main-window slots (203),
data-exploration (204), analysis/object dialogs (205), MdModel numeric/IO (206),
zip import (207). Remaining work is **Low** only (§Priority 3 of devlog 198):
`object_viewer_2d.set_image` silent-blank, `create_video_from_frames` cv2 failure,
`animate_shape` `int()` input, mostly-guarded outer slots, `MdImage.load_file_info`.
