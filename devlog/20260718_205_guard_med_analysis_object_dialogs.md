# 205 — Guard Med analysis/object dialog paths (audit batch 7)

**Date:** 2026-07-18
**Type:** implementation (NNN) — error-handling hardening (audit batch 7, Med)
**Related:** `devlog/20260717_198_error_handling_audit.md`, `..._204_...`

## What

Third Med batch, two dialogs:

- **`object_dialog.x_changed` → `@guard_slot` + per-line tolerance**: this is the
  `textChanged` slot on the X input. Pasting multiline tab-separated text feeds each
  row to `add_landmark`, which does `float(x)` — a pasted header row or any
  non-numeric cell raised `ValueError` and killed the dialog silently. Now the
  per-line parse is wrapped (bad rows are logged and skipped, good rows still added),
  with `@guard_slot` as a backstop.

- **`dataset_analysis_dialog.show_analysis_result` → `@guard_slot`**: the audit
  flagged `show_result_table` (`get_by_id` + `rotated_matrix.tolist()`), which is
  reached from five re-render slots — `axis_changed`, `flip_axis_changed`,
  `on_chart_dim_changed`, `propertyname_changed`, `on_btnAnalyze_clicked` — none
  guarded. Rather than decorate all five, guarding the single shared
  `show_analysis_result` entry point covers every caller (and the already-guarded
  `on_btn_analysis_clicked` still catches at its own layer).

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/dialogs/` — 224 passed.
- `pytest -k "object_dialog or dataset_analysis or analysis_dialog"` — 47 passed,
  5 skipped.

## Audit status

Med remaining: `MdModel` (change_dataset os.rename, rotation_matrix svd, rescale
ZeroDivision), `MdUtils` zip I/O (import_dataset_from_zip orphaning,
safe_extract_zip/read_json_from_zip, create_zip_package). Low untouched.
