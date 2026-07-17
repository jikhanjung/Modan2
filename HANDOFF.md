# Handoff

## ▶ Next up: Batch C is DONE — remaining is deferred MEDIUM / LOW

**Batch C (structural refactor) is complete** (devlog 176–193, on `main`). All four
items landed one-at-a-time, each with a matching devlog, `pytest` green
(**1219 passed, 74 skipped**) and `ruff` clean:

1. **God-methods decomposed** — `run_analysis` (176–178, clears the type-overloaded
   return), `prepare_scatter_data` (179–180), `read_settings` (185–186),
   `DatasetAnalysisDialog.__init__` (187), `ObjectDialog.__init__` (188).
2. **Shared scatter helpers** (181–184) — `build_scatter_group` + `build_scatter_legend`
   in `dialogs/scatter_utils.py`. The monolithic "shared builder" in the old TODO was
   deliberately **not** built (divergent data sources/semantics — see devlog 181).
3. **Dialog DB/file I/O → `ModanController`** (189–191) — `save_object`,
   `delete_object_with_files`, `import_dataset`.
4. **read_settings / color-marker hoist** (192–193) — `BaseDialog._restore_geometry`
   + module-level `load_color_marker_lists`.

New test coverage added for previously-untested areas (golden-master for
`prepare_scatter_data`, smoke test for `DatasetAnalysisDialog.show_analysis_result`,
`SettingsWrapper`, controller object/import I/O).

**What's left** (see `TODOs.md`): only the deliberately-deferred **MEDIUM** and
**LOW** items, plus the latent bugs surfaced during Batch C that were intentionally
left for a separate **R02** fix pass (e.g. the `analysis_type == "PCA"` vs `.upper()`
inconsistency, the triple min-object validation thresholds). Next devlog number: **194**.

---

## Context for whoever picks this up

- **Entry point**: `python main.py` (not `Modan2.py`, which is an imported module
  with no `__main__`). On Linux/WSL use `python fix_qt_import.py` for Qt plugin
  issues.
- **Before committing**: `pytest` (currently **1219 passed, 74 skipped**),
  `ruff check .` + `ruff format .` (clean repo-wide).
- **Review source of truth**:
  `devlog/20260625_R01_code_review_legacy_and_db_patterns.md`.
- **Convention**: one logical change per commit, each with a matching
  implementation devlog `devlog/YYYYMMDD_NNN_title.md` (next number: **194**).
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
