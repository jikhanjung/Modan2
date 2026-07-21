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

## 🟠 Test infra — dialog-test memory accumulation (2026-07-21)

Full-suite RSS climbs monotonically to ~800 MB and never comes back down; nearly
all of the growth is in dialog-heavy test files. Not the WSL OOM cause (that was
the removed image-scaling zoom test — devlog 220), but worth fixing before the
suite grows further. Per-file RSS deltas measured with a per-test VmRSS logger
(methodology in devlog 220):

| file | RSS growth |
|---|---|
| `tests/dialogs/test_data_exploration_scatter.py` | +110 MB |
| `tests/dialogs/test_export_dialog.py` | +69 MB |
| `tests/dialogs/test_preferences_dialog.py` | +58 MB |
| `tests/dialogs/test_dataset_analysis_scatter.py` | +53 MB |
| `tests/dialogs/test_object_dialog_modes.py` | +39 MB |
| `tests/test_analysis_workflow.py` | +33 MB |
| `tests/dialogs/test_analysis_dialog.py` | +31 MB |
| individual tests | +15–46 MB each, never released |

- [ ] **Investigate**: after each dialog test, run `gc.collect()` +
      `processEvents()` and count surviving `QDialog` / `FigureCanvas` /
      `ObjectViewer3D` instances (`gc.get_objects()` or objgraph) to separate
      "Python refs keep dialogs alive" from "freed but RSS not returned to OS".
- [ ] Prime suspects to check:
      - `Figure(figsize=(20, 16), dpi=100)` canvases in
        `data_exploration_dialog.py` / `dataset_analysis_dialog.py` — 2000×1600 px
        ⇒ ~12.8 MB Agg buffer each, 2–3 per dialog instance
      - parentless `ObjectViewer3D(parent=None, transparent=True)` stored in
        `shape_grid` (`data_exploration_dialog.py:1845`) — top-level widgets not
        destroyed with the dialog (`closeEvent` only calls `.close()`)
      - `QGLWidget` GL contexts per viewer (llvmpipe arenas under WSL)
      - PyQt reference cycles that need an explicit `gc.collect()` to break
- [ ] **Fix**: an autouse fixture (gc + deferred-delete flush) and/or explicit
      `deleteLater()` for shape-grid views; re-measure and record the new peak.

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
