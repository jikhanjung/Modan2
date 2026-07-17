# 200 — Import parser hardening (audit batch 2, group A)

**Date:** 2026-07-17
**Type:** implementation (NNN) — error-handling hardening
**Related:** `devlog/20260717_198_error_handling_audit.md`, `199_...`

## What

Malformed import files (TPS/NTS/X1Y1/Morphologika) raised out of the import dialog and
silently killed it. Two entry points construct the parsers:
- `open_file2` — runs the parser **immediately on file selection** (to preview the
  object count) — this is the *first* crash point;
- `import_file` → `_get_import_data` — on the Import button.

Guarded both with `@guard_slot` (from 199): a bad file now logs + shows an error
dialog instead of crashing. Also fixed `Morphologika.read` to use `with open(...)`
(the previous bare `open()` leaked the file handle when parsing raised).

## Behavior preservation

Success paths unchanged. On a malformed file the user sees an error dialog at
selection and/or import; no dataset is created (the parser raises before any DB
write). The JSON+ZIP path already had its own try/except (untouched).

## Verification

- `ruff check` + `ruff format` — clean.
- New `tests/test_import_error_handling.py`: a garbage `.tps` file → `open_file2` and
  `import_file` both surface an error (`QMessageBox.critical` called) without raising,
  and no partial dataset is persisted.
- `pytest tests/test_import.py` — 8 passed (existing happy-path imports unaffected).

## Note

Deeper parser-level hardening (typed error messages per format, defensive token
parsing) is deferred — the guard already prevents the silent crash. The zip-import
file-orphaning concern (atomic DB rollback but copied files remain) is a separate Med
audit item.

## Next

201: 3D-model I/O symmetry (`MdThreeDModel.add_file`/`load_file_info`,
`set_threed_model` .ply/.stl). 202: dialog High slots.
