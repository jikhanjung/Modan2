# 206 — Harden Med MdModel numeric/IO paths (audit batch 8)

**Date:** 2026-07-18
**Type:** implementation (NNN) — error-handling hardening (audit batch 8, Med)
**Related:** `devlog/20260717_198_error_handling_audit.md`, `..._205_...`

## What

Fourth Med batch, `MdModel.py` — these are model-layer routines (not slots), so the
fix is targeted guards / reordering rather than `@guard_slot`:

- **`change_dataset` move-before-save**: it previously `save()`d the object onto the
  new dataset *first*, then `os.rename`d the media file. If the rename failed, the DB
  row pointed at the new dataset while the file stayed at the old path — an orphaned /
  inconsistent object (data loss). Reordered: assign the dataset in memory, move the
  file, and only `save()` after the move succeeds. A move failure now leaves the DB
  untouched and consistent, and propagates to the guarded caller (`dropEvent`).

- **`rescale_to_unitsize` ZeroDivision guard**: `1 / centroid_size` crashed on a
  zero-centroid shape (single coincident point / empty landmark set). Now logs and
  skips the rescale instead of raising.

- **`rotation_matrix` SVD clear error**: `np.linalg.svd` on degenerate / non-finite
  landmark data (missing coords → NaN) raised a cryptic `LinAlgError`. Wrapped to
  re-raise a clear `ValueError` explaining the cause; the guarded analysis slot shows
  it.

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/test_mdmodel.py` — 266 passed.
- `pytest test_analysis_workflow + test_controller + tree_interactions` — 112 passed,
  6 skipped.

## Audit status

Med remaining: `MdUtils` zip I/O only — `import_dataset_from_zip` (file orphaning on
rollback, `int(dimension)`/`float(ppm)` on bad manifest), `safe_extract_zip` /
`read_json_from_zip` (BadZipFile/JSONDecodeError), `create_zip_package`
(json.dump/zip write). Low untouched.
