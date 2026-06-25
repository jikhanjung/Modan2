# Handoff

## ▶ Next up: Batch C (structural refactor)

The remaining R01 work is **Batch C — the structural refactor**, which has not
been started. It is large and multi-file, so tackle it **one item at a time**,
each on its own commit + devlog, keeping `pytest` green and `ruff check .` clean.

See **`TODOs.md`** for the full checklist (Batch C items, deferred MEDIUM, LOW).

Batch C at a glance:
1. Decompose god-methods (`run_analysis`, `read_settings`, the big dialog
   `__init__`s, `prepare_scatter_data`) — `run_analysis` also clears the
   type-overloaded-return smell.
2. Extract a shared scatter-plot builder (dataset_analysis ↔ data_exploration).
3. Move DB/file I/O out of dialogs into `ModanController`.
4. Hoist duplicated `read_settings`/color-marker loading into `BaseDialog`.

---

## Context for whoever picks this up

- **Entry point**: `python main.py` (not `Modan2.py`, which is an imported module
  with no `__main__`). On Linux/WSL use `python fix_qt_import.py` for Qt plugin
  issues.
- **Before committing**: `pytest` (currently **1196 passed, 74 skipped**),
  `ruff check .` + `ruff format .` (clean repo-wide).
- **Review source of truth**:
  `devlog/20260625_R01_code_review_legacy_and_db_patterns.md`.
- **Convention**: one logical change per commit, each with a matching
  implementation devlog `devlog/YYYYMMDD_NNN_title.md` (next number: **176**).
  Doc types: `P##` plan, `NNN` implementation, `R##` review.

## What was completed on 2026-06-25 (R01 cleanup)

16 commits, all documented in `devlog/20260625_152`–`175`:

| Area | Items |
|---|---|
| DB correctness | C1 field names, C2 class-level mutable attrs, C4 transactions |
| N+1 queries | CVA/MANOVA group extraction, `change_dataset`, `get_average_shape` |
| Statistics (HIGH, all done) | C3 eigenvalue view-copy, inv→pinv, 3D Z-coord, MANOVA truncation surfaced, **CVA covariance vectorization** |
| MEDIUM patterns | latent bugs (regex/`is_numeric`/`utcnow`), `locals()` removal, `raise … from e`, `range(len)`→enumerate, module loggers, `tr()` i18n |
| Cleanup | removed 6 dead modules + 8 stale `.spec`, fixed entry-point docs, repo-wide ruff clean |

All R01 **CRITICAL/HIGH correctness** and **HIGH statistics** items are closed.
Remaining = Batch C (structural) + deliberately-deferred MEDIUM/LOW (see `TODOs.md`).
