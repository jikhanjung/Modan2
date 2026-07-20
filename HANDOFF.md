# Handoff

## ▶ Current state (updated 2026-07-20)

**v0.1.6 released** (tag `v0.1.6`, commit `b4fd1a2`, 2026-07-20). Suite verified
2026-07-20: **1404 passed, 75 skipped** (`pytest`, ~4.5 min), coverage **59%**.

Release convention from 2026-07-20: **each release bumps the patch version by
one**, no prerelease suffixes. Edit `version.py` only — everything else reads
from it (`MdUtils.PROGRAM_VERSION`, `MdConstants.APP_VERSION` and `main.py`'s
strings are `ImportError` fallbacks). The GitHub release body is now the tag's
own `CHANGELOG.md` section, extracted by `release.yml`.

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

Shipped in 0.1.6 (2026-07-20, devlog 209–218) — the missing-landmark path end to
end, plus the crashes found along the way:

- **Blank-cell landmark parsing fixed** (209) — clearing a cell in the
  ObjectDialog landmark table produced a short row and crashed
  `count_landmarks` / `has_missing_landmarks` / `procrustes_superimposition`
  with `IndexError`; a cleared X also silently shifted Y into X's slot.
- **Legend italics** (210) — `*Eurekia*` in a grouping value renders italic.
- **Landmark cell validation** (211) — hand-edited cells accept a number or
  `MISSING` and revert anything else; previously a typo silently became a
  missing landmark. Edits now also sync to `landmark_list`/the viewers.

- **Circular import fix** (212) — 210's module-level `dialogs.scatter_utils`
  import in `analysis_info` broke `import ModanComponents` in a fresh
  interpreter; the suite missed it because `sys.modules` is process-global.
  `tests/test_import_cycles.py` now imports each entry point in a subprocess.
- **`-999` on import** (213) — the import asks whether the morphometrics
  sentinel means "missing landmark" (default yes, with an "always" checkbox
  stored in `Import/TreatSentinelAsMissing`). Note the readers apply invert-Y
  *before* the scan, so a Y sentinel reads as `+999`.

- **"Add Missing" inserts at position** (214) — was always appending, which is
  wrong for a positional landmark list. Also fixed stale coordinate inputs after
  an insert (`selectRow` emits nothing when the row was already selected).

- **"Insert Missing" label** (follow-up to 214) — the button says Insert vs Add
  depending on whether a row is selected.
- **One landmark-count definition** (215) — the controller compared a
  missing-*excluding* expected count against missing-*including* actuals, so an
  object with a missing landmark failed against itself while `check_object_list`
  passed it. Both now use `MdModel.find_landmark_count_mismatch`.
- **Missing shown as red `(N)`** (216) — object-list Landmarks column reads
  `9 (1)`. Uncovered and fixed a pre-existing segfault: item delegates were set
  **unparented**, so Qt kept a pointer to a garbage-collected object.

- **Actionable count-mismatch message** (217) — a short object is now rejected
  with "Object 'O2' has 3 landmarks but this dataset expects 4. Open the object
  and use \"Insert Missing\"…", shared by all three gates, instead of a bare
  `"Procrustes superimposition failed"`.

- **Unimputable landmarks rejected** (218) — a landmark missing in *every*
  object has nothing to estimate it from; it is now named up front instead of
  surfacing as a `NoneType` error from inside PCA. Detection is per coordinate
  (an axis missing throughout crashed identically).

Also on 2026-07-20, after the release (no devlog — CI/tooling only):
`pre-commit` installed (and stopped from corrupting `AppDir/` symlinks), ruff
pinned to match, all GitHub Actions bumped to Node 24 runtimes, and the Codecov
upload dropped.

**Next devlog number: 219.**

### ▶ Next up (2026-07-21)

Two gaps found in the 2026-07-20 coverage run (**59% overall**; `MdModel` is up
from 56% → 71% since the figure quoted in `CLAUDE.md`):

1. **`ModanWidgets.py` (555 statements, 21%) looks like dead code.** Its five
   classes — `DatasetTreeWidget`, `ObjectTableWidget`, `LandmarkViewer2D`,
   `AnalysisResultWidget`, `ProgressIndicator` — are imported by **nothing in
   production**. The only references are a logging-config string key in
   `MdConstants.py:591` and `tests/test_modan_widgets.py`, i.e. the module is
   kept alive solely by its own test. The live UI uses `components/widgets/`.
   Same shape as the `ModanDialogs.py` removal in 0.1.5 (2,539 lines). **Verify
   once more before deleting** — check for dynamic/late imports.
2. **`components/formats/x1y1.py` is at 18%.** Its sibling parsers are far
   better covered (`tps` 91%, `morphologika` 88%, `nts` 62%). Pure parsing
   logic, so it is cheap to test, and importing an X1Y1 file currently exercises
   a barely-verified path. `nts.py` at 62% is a smaller version of the same gap.

Low coverage elsewhere is expected and not worth chasing: the OpenGL/Qt viewers
(`object_viewer_3d` 20%, `object_viewer_2d` 39%) and the entry-point scripts
(`main.py`, `MdAppSetup.py`, `MdSplashScreen.py`, `manage_version.py` at 0%).

### What's left (all deliberately deferred — see `TODOs.md`)

- **MEDIUM**: magic sentinels `99999` → `float('inf')`; per-method logger
  recreation in `Modan2.py` (9 sites); `range(len)` → `enumerate` in
  `MdHelpers.py` (1) / `dialogs/preferences_dialog.py` (9); in-method import
  hoisting (needs per-site judgment).
- **LOW**: builtin shadowing (`object`, `sum`), redundant `float()` casts,
  dead branch in `object_dialog.py:~936`.
- **Deferred R02 gap** (see below): CVA-only / MANOVA-only persist gap on
  UI-dead paths.
- ~~Missing-landmark follow-ups from devlog 209~~ — **all closed** (cell
  validator + `make_landmark_str` guard in 211, `-999` import handling in 213,
  insert-at-position in 214).
- ~~Missing-landmark PCA gaps~~ — **all closed**. Positions that disagree are
  rejected with an actionable message (217); landmarks nothing can impute are
  named and declined (218).
- **Delete `RELEASE_NOTES.md`** (deferred 2026-07-20, do it next session). It is
  420 stale lines still describing itself as "Version: 0.1.5-alpha.1 / Status:
  Pre-release / Alpha". Nothing reads it any more — `release.yml` now builds the
  release body from the tag's `CHANGELOG.md` section — so it is dead weight that
  reads like current release documentation.
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
- **Before committing**: `pytest` (currently **1404 passed, 75 skipped**),
  `ruff check .` + `ruff format .` (clean repo-wide; note `ruff` may need
  `pip install ruff` in a fresh shell).
- **Review sources of truth**:
  `devlog/20260625_R01_code_review_legacy_and_db_patterns.md` (R01),
  `devlog/20260717_198_error_handling_audit.md` (error-handling audit).
- **Convention**: one logical change per commit, each with a matching devlog
  `devlog/YYYYMMDD_NNN_title.md` (next number: **209**). Doc types: `P##`
  plan, `NNN` implementation, `R##` review.
- **Release flow**: version lives in `version.py` (single source of truth,
  currently `0.1.6`); each release bumps the patch version by one. CI build
  numbers are commit-count based; Windows
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
