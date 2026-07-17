# 194 — R02: fix case-sensitive `analysis_type` check in analysis persistence

**Date:** 2026-07-17
**Type:** implementation (NNN) — R02 latent-bug pass
**Batch:** post-C (R02 fixes for issues surfaced during Batch C)
**Related:** `devlog/20260717_176_...`, `178_...`, `HANDOFF.md`

## Background

Batch C was done as behavior-preserving structural refactoring; two latent
inconsistencies it surfaced were deliberately deferred to this R02 pass.

## Fixed: persist path `analysis_type == "PCA"` → `.upper()`

`ModanController.run_analysis` dispatches with `analysis_type.upper() == "PCA"` (and
`"CVA"`/`"MANOVA"`), but the persistence block checked a **case-sensitive**
`analysis_type == "PCA"`. An old-signature *lowercase* call — `run_analysis("pca",
{...})` — therefore ran PCA (dispatch matched) but saved **no** result JSON (persist
skipped): silent data loss.

Fix: harmonize the persist check to `analysis_type.upper() == "PCA"`.

The new UI path always passes the uppercase literal `"PCA"`, so this never affected
the live app — it's a latent bug on the backward-compat string path.

### Regression test (proves the bug, then the fix)

Added `tests/test_controller_r02.py`:
- `test_run_analysis_lowercase_pca_persists_results` — **failed before the fix**
  (`pca_analysis_result_json is None`), passes after.
- `test_run_analysis_uppercase_pca_still_persists_results` — guards the unchanged
  uppercase path.

## Not changed (with rationale)

- **Triple min-object validation thresholds** — `_validate_dataset_for_analysis_type`
  (PCA 2 / CVA·MANOVA 6), `_validate_dataset_for_general_analysis` (5 + requires
  grouping vars), and the inline `< 2` run guard are **different gates for different
  entry points** (per-type validation vs the UI "analyze" pre-check vs the hard
  mathematical floor), not a single duplicated threshold. Consolidating them is a
  product decision (it would change UI gating), so left as-is — not a bug.
- **CVA-only / MANOVA-only paths save no result JSON** — the persist block only
  serializes CVA/MANOVA from `cva_result`/`manova_result`, which are populated solely
  by the comprehensive PCA path; the standalone `run_analysis("CVA"/"MANOVA")` paths
  set only `result` and never persist it. This is a real gap but on **UI-dead paths**
  (the app always runs the comprehensive PCA path). Left for a future change if those
  entry points are ever revived; not fixed here to avoid a behavior change on
  effectively-dead code.

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/test_controller_r02.py tests/test_controller.py
  tests/test_analysis_workflow.py` — 102 passed, 2 skipped.
