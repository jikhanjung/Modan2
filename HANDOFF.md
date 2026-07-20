# Handoff

## ▶ Current state (updated 2026-07-20)

**v0.1.5 final released** (tag `v0.1.5`, commit `8f97494`, 2026-07-18). Working tree
clean on `main`, no commits after the release tag. Suite verified 2026-07-20:
**1242 passed, 75 skipped** (`pytest`, ~5.5 min).

Everything below the line is **done and closed**:

- **R01 review cleanup** (devlog 152–175) — all CRITICAL/HIGH correctness +
  HIGH statistics items.
- **Batch C structural refactor** (devlog 176–193) — god-methods decomposed,
  shared scatter helpers, dialog DB/file I/O moved to `ModanController`,
  `read_settings`/color-marker hoists.
- **R02 latent-bug pass** (devlog 194) — see detailed section below.
- **Bug fixes** (195–197) — silent-crash fixes (dataset click, Excel save),
  Excel-save root cause (Shapes sheet), scrollable preferences dialog.
- **Error-handling audit + full remediation** (198–208) — audit (198) then ten
  batches: `guard_slot` decorator on High/Med main-window & dialog slots,
  parser hardening (`components/formats/*`), 3D-model I/O symmetry, MdModel
  numeric/IO guards, zip-import orphan cleanup, viewer/animation guards.
- **Release chores** — frozen-build pytz crash fixed (pandas pinned `<3.0`),
  Inno Setup download pinned to 6.7.3, commit-count build numbers across CI
  workflows, atomic preferences persistence (settings-reset fix).

Since the release (2026-07-20, devlog 209–210):

- **Blank-cell landmark parsing fixed** (209) — clearing a cell in the
  ObjectDialog landmark table produced a short row and crashed
  `count_landmarks` / `has_missing_landmarks` / `procrustes_superimposition`
  with `IndexError`; a cleared X also silently shifted Y into X's slot.
- **Legend italics** (210) — `*Eurekia*` in a grouping value renders italic.

**Next devlog number: 211.**

### What's left (all deliberately deferred — see `TODOs.md`)

- **MEDIUM**: magic sentinels `99999` → `float('inf')`; per-method logger
  recreation in `Modan2.py` (9 sites); `range(len)` → `enumerate` in
  `MdHelpers.py` (1) / `dialogs/preferences_dialog.py` (9); in-method import
  hoisting (needs per-site judgment).
- **LOW**: builtin shadowing (`object`, `sum`), redundant `float()` casts,
  dead branch in `object_dialog.py:~936`.
- **Deferred R02 gap** (see below): CVA-only / MANOVA-only persist gap on
  UI-dead paths.
- **Missing-landmark follow-ups** (surfaced in devlog 209, in priority order):
  landmark-table cell validator (number or `MISSING` only — today any typo
  silently becomes a missing landmark); `None`-item guard in
  `make_landmark_str`; recognise the `-999` convention as missing on import;
  insert-at-position for "Add Missing" (it only appends).
- **Missing-landmark PCA**: works today when rows carry `Missing` markers so
  landmark *counts* match. Two gaps remain — a landmark missing in *every*
  object leaves `None` in the matrix (`float() argument must be … not
  'NoneType'`), and differing landmark counts fail `check_object_list` with the
  unhelpful `"Procrustes superimposition failed"`. Only `Missing`/`NA`/
  non-numeric tokens are detected as missing; `-999` parses as a coordinate.
- Housekeeping: 6 open dependabot PRs (numpy, pytest family); stale local
  branches `feature/missing-landmark`, `feature/pyqt6-quick-test`.

---

## R02 latent-bug pass — detail (devlog `20260717_194`)

Batch C was strictly behavior-preserving refactoring; two inconsistencies it
surfaced were deferred to a separate R02 pass so the fix wouldn't be buried in
a refactor commit. R02 ran on 2026-07-17. Outcome:

### 1. FIXED — case-sensitive `analysis_type` persist check (silent data loss)

`ModanController.run_analysis` **dispatched** case-insensitively
(`analysis_type.upper() == "PCA"` / `"CVA"` / `"MANOVA"`) but the
**persistence block** checked case-sensitively (`analysis_type == "PCA"`).
Consequence: a lowercase old-signature call — `run_analysis("pca", {...})` —
ran the full PCA (dispatch matched) but **skipped saving the result JSON**
(persist check failed): analysis computed, nothing stored, no error. The live
UI always passes the uppercase literal, so users never hit it — it was latent
on the backward-compat string path only.

Fix: persist check harmonized to `.upper()`. Regression tests in
`tests/test_controller_r02.py` (lowercase test failed before the fix, passes
after; uppercase test guards the unchanged path).

### 2. NOT A BUG — triple min-object validation thresholds

Three different minimum-object checks coexist, but they are **different gates
for different entry points**, not an accidentally-duplicated threshold:

- `_validate_dataset_for_analysis_type` — per-type: PCA ≥ 2, CVA/MANOVA ≥ 6
- `_validate_dataset_for_general_analysis` — UI "analyze" pre-check: ≥ 5 +
  grouping variables required
- inline `< 2` guard in the run path — hard mathematical floor

Consolidating them would **change UI gating behavior** — that's a product
decision, not a correctness fix. Left as-is deliberately.

### 3. REAL GAP, DEFERRED — CVA-only / MANOVA-only results never persisted

The persist block serializes CVA/MANOVA only from `cva_result`/`manova_result`,
which are populated **solely by the comprehensive PCA path**. The standalone
`run_analysis("CVA")` / `run_analysis("MANOVA")` entry points set only
`result` and never persist it. This is a genuine gap, but on **UI-dead paths**
— the app always runs the comprehensive PCA path. Fixing it would change
behavior on effectively-dead code, so it's deferred until/unless those entry
points are revived. If you revive them, fix the persistence at the same time.

---

## Context for whoever picks this up

- **Entry point**: `python main.py` (not `Modan2.py`, which is an imported
  module with no `__main__`). On Linux/WSL use `python fix_qt_import.py` for
  Qt plugin issues.
- **Before committing**: `pytest` (currently **1242 passed, 75 skipped**),
  `ruff check .` + `ruff format .` (clean repo-wide; note `ruff` may need
  `pip install ruff` in a fresh shell).
- **Review sources of truth**:
  `devlog/20260625_R01_code_review_legacy_and_db_patterns.md` (R01),
  `devlog/20260717_198_error_handling_audit.md` (error-handling audit).
- **Convention**: one logical change per commit, each with a matching devlog
  `devlog/YYYYMMDD_NNN_title.md` (next number: **209**). Doc types: `P##`
  plan, `NNN` implementation, `R##` review.
- **Release flow**: version lives in `version.py` (single source of truth,
  currently `0.1.5`); CI build numbers are commit-count based; Windows
  installer via `InnoSetup/Modan2.iss` (Inno Setup pinned 6.7.3).

## Historical record

### Batch C (structural refactor) — complete (devlog 176–193)

1. **God-methods decomposed** — `run_analysis` (176–178, clears the
   type-overloaded return), `prepare_scatter_data` (179–180), `read_settings`
   (185–186), `DatasetAnalysisDialog.__init__` (187),
   `ObjectDialog.__init__` (188).
2. **Shared scatter helpers** (181–184) — `build_scatter_group` +
   `build_scatter_legend` in `dialogs/scatter_utils.py`. The monolithic
   "shared builder" in the old TODO was deliberately **not** built (divergent
   data sources/semantics — see devlog 181).
3. **Dialog DB/file I/O → `ModanController`** (189–191) — `save_object`,
   `delete_object_with_files`, `import_dataset`.
4. **read_settings / color-marker hoist** (192–193) —
   `BaseDialog._restore_geometry` + module-level `load_color_marker_lists`.

### R01 cleanup — complete (2026-06-25, devlog 152–175)

| Area | Items |
|---|---|
| DB correctness | C1 field names, C2 class-level mutable attrs, C4 transactions |
| N+1 queries | CVA/MANOVA group extraction, `change_dataset`, `get_average_shape` |
| Statistics (HIGH, all done) | C3 eigenvalue view-copy, inv→pinv, 3D Z-coord, MANOVA truncation surfaced, **CVA covariance vectorization** |
| MEDIUM patterns | latent bugs (regex/`is_numeric`/`utcnow`), `locals()` removal, `raise … from e`, `range(len)`→enumerate, module loggers, `tr()` i18n |
| Cleanup | removed 6 dead modules + 8 stale `.spec`, fixed entry-point docs, repo-wide ruff clean |
