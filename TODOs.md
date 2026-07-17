# Modan2 — Outstanding TODOs

Tracks remaining work from the **R01 code review**
(`devlog/20260625_R01_code_review_legacy_and_db_patterns.md`).

As of **2026-06-25**, all CRITICAL/HIGH **correctness** items and the HIGH
**statistics** items are done (see `devlog/20260625_152`–`175` and the table in
`HANDOFF.md`). What remains:

---

## 🔴 Batch C — Structural refactor (HIGH, not started)

Large, multi-file, higher-risk. Do **one item at a time**, each on its own
commit + devlog, keeping the suite green. Recommended order is roughly top-down.

- [ ] **Decompose god-methods**
  - [x] `ModanController.run_analysis` (~360 lines) → done (devlog 176–178): split
        into `_extract_group_values` / `_prepare_landmarks` / `_persist_analysis_results`;
        type-overloaded return smell resolved
  - [ ] `Modan2.py` `read_settings` (~250 lines, contains an inline nested class)
  - [ ] `dialogs/dataset_analysis_dialog.py` `__init__` (371 lines)
  - [ ] `dialogs/object_dialog.py` `__init__` (283 lines)
  - [x] `dialogs/data_exploration_dialog.py` `prepare_scatter_data` (285 lines) →
        done (devlog 179–180): golden-master net + split into 6 phase helpers
- [x] **Extract shared scatter-plot builder** — *rescoped & done* (devlog 181–184).
      The two sites are **not** a monolithic near-duplicate (different data sources,
      output structures, centroid/colour semantics), so a single builder was
      deliberately not built. Extracted the genuinely-shared seams into
      `dialogs/scatter_utils.py`: `build_scatter_group` (group-dict factory) and
      `build_scatter_legend`, applied in both dialogs. Guarded by unit tests + the
      exploration golden-master + a dataset-analysis smoke test.
- [ ] **Move DB/file I/O out of dialogs into `ModanController`**
      (mirror how `analysis_dialog.py` already delegates)
  - [ ] `dialogs/object_dialog.py` `save_object()`, `Delete()` (`os.remove` +
        `delete_instance`)
  - [ ] `dialogs/import_dialog.py` direct DB writes
- [ ] **Hoist `read_settings` / color-marker loading** copy-pasted across ~9
      dialogs into `BaseDialog` or a settings mixin

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
