# Modan2 — Outstanding TODOs

Tracks remaining work from the **R01 code review**
(`devlog/20260625_R01_code_review_legacy_and_db_patterns.md`).

As of **2026-06-25**, all CRITICAL/HIGH **correctness** items and the HIGH
**statistics** items are done (see `devlog/20260625_152`–`175` and the table in
`HANDOFF.md`). What remains:

---

## ✅ Batch C — Structural refactor (HIGH) — **COMPLETE** (devlog 176–193)

All four items done (god-method decomposition, shared scatter helpers, dialog I/O →
controller, read_settings/color-marker hoist), each on its own commit + devlog with
the suite kept green. Kept as a record below.

- [x] **Decompose god-methods** — all done
  - [x] `ModanController.run_analysis` (~360 lines) → done (devlog 176–178): split
        into `_extract_group_values` / `_prepare_landmarks` / `_persist_analysis_results`;
        type-overloaded return smell resolved
  - [x] `Modan2.py` `read_settings` (~250 lines) → done (devlog 185–186): `SettingsWrapper`
        hoisted to module level (+ unit tests) and `_restore_main_window_geometry` extracted;
        247 → 39 lines
  - [x] `dialogs/dataset_analysis_dialog.py` `__init__` (371 → 132 lines) → done (devlog 187):
        `_init_object_table` / `_init_plot_area` / `_init_bottom_controls`
  - [x] `dialogs/object_dialog.py` `__init__` (283 → 146 lines) → done (devlog 188):
        `_init_coord_input` / `_init_tool_buttons` / `_init_option_checkboxes` / `_init_action_buttons`
  - [x] `dialogs/data_exploration_dialog.py` `prepare_scatter_data` (285 lines) →
        done (devlog 179–180): golden-master net + split into 6 phase helpers
- [x] **Extract shared scatter-plot builder** — *rescoped & done* (devlog 181–184).
      The two sites are **not** a monolithic near-duplicate (different data sources,
      output structures, centroid/colour semantics), so a single builder was
      deliberately not built. Extracted the genuinely-shared seams into
      `dialogs/scatter_utils.py`: `build_scatter_group` (group-dict factory) and
      `build_scatter_legend`, applied in both dialogs. Guarded by unit tests + the
      exploration golden-master + a dataset-analysis smoke test.
- [x] **Move DB/file I/O out of dialogs into `ModanController`** — done (devlog 189–191)
  - [x] `dialogs/object_dialog.py` `save_object()` → `ModanController.save_object` (189);
        `Delete()` → `ModanController.delete_object_with_files` (190)
  - [x] `dialogs/import_dialog.py` direct DB writes → `ModanController.import_dataset`
        (+ `_import_object` / `_import_object_image`) (191)
  - Controller injected into both dialogs via `parent.controller` with an
    `isinstance(ModanController)` guard + standalone fallback for Mock/parentless tests.
- [x] **Hoist `read_settings` / color-marker loading** — done (devlog 192–193)
  - [x] `BaseDialog._restore_geometry(key, default_rect, move_offset)` — applied in
        `DatasetDialog` / `ExportDatasetDialog` / `AnalysisResultDialog` (192)
  - [x] module-level `load_color_marker_lists` — applied in `DataExplorationDialog` /
        `DatasetAnalysisDialog` (both `QDialog`, so a free function not a BaseDialog
        method) (193)

---

## ✅ Test infra — dialog-test memory accumulation — **RESOLVED 2026-07-21**

Investigated and fixed (devlog 224/225). Root cause was NOT a Python-side leak:
pytest-qt's teardown calls `deleteLater()`, but `DeferredDelete` events are never
delivered without an event loop, so every qtbot-registered widget tree survived
the session (~5000 live widgets, RSS to ~825 MB). Fixed with a
`pytest_runtest_logfinish` hook in `tests/conftest.py` that delivers the pending
deletes (`sendPostedEvents(None, DeferredDelete)` + `gc.collect(0)`). Peak RSS
825 → 531 MB, surviving widgets 0 per test.

The investigation also exposed a REAL app leak with the same symptom: parented
dialogs are never deleted on close, so every dialog ever opened accumulated as a
hidden child of the main window. Fixed in `Modan2.py` (WA_DeleteOnClose for
non-modal show() dialogs, deleteLater() after every exec_() site) — devlog 225.

---

## 🟠 R03 improvement review (2026-07-21) — see `devlog/20260721_R03_improvement_review.md`

Post-0.1.8 review items, in priority order:

- [x] **1. Orphaned files on image replacement** — DONE 2026-07-21 (devlog
      226): `update_image` now removes the old working copy and `originals/`
      archive before writing the replacement. The related deletion gap is done
      too (devlog 228): dataset deletion removes `<storage>/<ds.id>/`, object
      deletion removes the object's files, and both UI paths now go through the
      controller instead of calling `delete_instance()` directly.
- [x] **2. Unify display-estimate vs analysis-imputation** — DONE 2026-07-21
      (devlog 227). Both paths now share `MdModel.impute_missing_landmarks`
      (fit the mean onto the observed landmarks, then borrow the gaps). The
      analysis path turned out to be badly wrong, not merely different: it
      imputed before the first rotation and never revisited the value, giving
      61% of centroid size error on noise-free synthetic data. Rebuilt as EM
      refinement — now 0.0%. Worth a sanity check on a real dataset, since
      analysis output changes for datasets with missing landmarks.
- [x] **3. Qt.SmoothTransformation for viewer pixmap scaling** — DONE
      2026-07-21 (devlog 231). Benchmarking settled the cost worry: smooth is
      1.4–2.8x slower when downscaling but only 5–14 ms absolute, and ~3x
      *faster* when upscaling, so it was applied to both call sites.
- [x] **4. Korean translation update** — DONE 2026-07-21 (devlog 229): 237 →
      290 messages, 54 translated, 0 unfinished, `.qm` rebuilt and verified via
      QTranslator. Note the pylupdate5 trap documented there: entries that
      carry a translation but keep `type="unfinished"` are dropped by lrelease.
      Left alone: `translations/Modan2_en.ts` (empty translations fall back to
      the source, which is already correct). The stale root-level
      `Modan2_ko.ts`/`.qm` that nothing referenced were deleted.
- [x] **5. Refresh CLAUDE.md + `.index/`** — DONE 2026-07-21 (devlog 230):
      version, structure (dialogs//components/), test counts, pytest.ini
      location, key-file table, hotspots and stats all corrected against the
      repo. Also fixed `tools/build_index.py`, whose case-sensitive filename
      check meant `--dialog` searches had silently returned nothing since the
      dialogs moved into `dialogs/` (0 → 83 indexed).
- [ ] **6. Triage 75 skipped tests** (LOW) — classify env-skips vs rot.

---

## 🟡 MEDIUM — deliberately deferred (low value / higher risk)

Skipped on purpose during the 2026-06-25 pass; revisit only if desired.

- [ ] In-method imports → hoist to module scope (some are intentional lazy /
      circular-import avoidance — needs per-site judgment)
- [ ] `if x == "" / x is None` → `if not x` (semantic risk: `0` / `[]` are falsy)
- [ ] Magic sentinels `99999 / -99999` → `float('inf')` / `min`/`max`
      (`dialogs/data_exploration_dialog.py:~1695` + twin)
- [ ] Vectorize thin helpers in `MdHelpers.py` (centroid/bbox/translate) — not a
      live hotspot, so low priority

### Partially done (same pattern remains in other files)
- [ ] Per-method `logger = getLogger(__name__)` recreation — **`Modan2.py` (9 sites)**
      still to do (done in `MdUtils.py` / `MdModel.py`)
- [ ] `for i in range(len(...))` → `enumerate`/`zip` — **`MdHelpers.py` (1)** and
      **`dialogs/preferences_dialog.py` (9)** still to do (done in `MdModel.py`)

---

## ⚪ LOW — nice-to-have

- [ ] Builtin shadowing (`object`, `sum`): `Modan2.py:~1037/1436`,
      `object_dialog.py:~711/1141`, `MdStatistics.py:~51`
- [ ] Py2-isms: drop redundant `float()` in `int(x / float(total) * 100)`
      (`Modan2.py:~1377/1515`)
- [ ] Dead branch `None if dim == 3 else None` (`dialogs/object_dialog.py:~936`)
- [ ] Stale commented-out cruft in `object_dialog.py` (dozens of `# self.x...`)
- [ ] Hardcoded `"qt_version": "5.15.x"` → `QT_VERSION_STR` (`MdHelpers.py:~982`)

---

*Done items (for reference): C1/C2/C4 DB correctness; N+1 #1/#2/#3; C3 eigenvalue
view-copy; CVA inv→pinv; 3D Z-coordinate; MANOVA truncation surfaced; CVA
covariance vectorization; latent bugs (regex/`is_numeric`/`utcnow`); `locals()`
control flow; `raise … from e`; module-level loggers (MdUtils/MdModel); `tr()`
i18n placeholders; dead-module & stale-spec removal; repo-wide ruff clean.*
