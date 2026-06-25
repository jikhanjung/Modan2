# Code Review — Legacy & DB Patterns

**Date**: 2026-06-25
**Type**: Code Review (R-series, first entry)
**Reviewer**: Multi-agent review (4 parallel reviewers + manual verification)
**Scope**: Full codebase (~38K LOC), with emphasis on the database layer
**Trigger**: Suspicion that parts of the code are outdated / written by someone not fluent in Python, especially DB-related code.

---

## TL;DR

Code quality is **bimodal**:

- **Newer code is clean and modern** — `dialogs/base_dialog.py`, `dialogs/analysis_dialog.py`, `components/viewers/`, and the `MdStatistics.do_*` functions use f-strings, comprehensions, type hints, and controller delegation correctly.
- **Older / clumsy code is concentrated in three places**: the DB layer (`MdModel.py`), the legacy statistics classes (`MdPrincipalComponent` / `MdCanonicalVariate` in `MdStatistics.py`), and the three large dialogs (`ObjectDialog`, `DataExplorationDialog`, `DatasetAnalysisDialog`).

Good news: the worst legacy idioms (`bare except:`, mutable default args, `type(x) ==`, `== None`) are essentially **absent**. The real problems are **structural (duplicate parallel implementations)** and **DB access patterns**, not surface style.

### Root cause: triple parallel implementations

Almost every issue traces back to the same root: the same functionality exists in **three unsynced layers** — legacy classes ↔ `ModanController` ↔ `dialogs/`. Newer layers were written **without re-checking the model schema**, producing field-name bugs and silent data loss in not-yet-wired code paths.

---

## CRITICAL (verified)

### C1 — `.create()` called with non-existent field names (silent data loss)
**`ModanController.py:342-346, 368, 398-405`**

The controller import path passes kwargs that are **not model fields**:
- `MdObject.create(..., landmarks=...)` — real field is `landmark_str`
- `MdImage.create(file_path=..., dataset=...)` — real fields are `original_path`, `object`
- `MdThreeDModel.create(file_path=..., model_3d=...)` — same

Peewee does **not raise** on unknown kwargs — it sets them as non-persisted instance attributes and silently drops them. So imported objects would be saved with **no landmark data**.

**Verification**: Confirmed the field mismatch against the model definitions (`MdObject.landmark_str`, `MdImage.original_path/object`). **However**, the real application import path is `dialogs/import_dialog.py:424` (`obj.landmark_str = "\n".join(...)`), which works correctly. The buggy `ModanController.import_objects` / `_import_landmark_file` methods are a **parallel implementation called only by tests** — not wired into the UI.

**Severity nuance**: This is a **latent bug**, not a live one. The day someone routes UI import through the controller (the stated architectural goal), data loss begins. Tests pass today because they never assert that `landmark_str` is persisted (and Peewee swallows the bad kwargs).

**Fix**: Map to real fields — build `landmark_str` via the model's pack helper; set `MdImage.object` / `original_path`; drop `landmark_count` from the dataset `create()`. Better: collapse onto the single working import path in `import_dialog.py`.

### C2 — Mutable lists declared as class attributes (cross-instance data corruption)
**`MdModel.py:46-49` (MdDataset), `230-232` (MdObject)**

`baseline_point_list = []`, `landmark_list = []`, `variablename_list = []`, etc. are declared at **class level**, not in `__init__`. These are not Peewee fields — they are plain Python lists **shared by every instance of the class**. Any `self.x.append(...)` mutates shared state, leaking data between objects.

**Verification**: Confirmed these names are absent from the Peewee field definitions (so they are plain class attributes).

**Fix**: Initialize per-instance in `__init__` (e.g. `def __init__(self, *a, **k): super().__init__(*a, **k); self.landmark_list = []`). Never use mutable class-level defaults.

### C3 — numpy view-vs-copy bug in CVA (numerical corruption)
**`MdStatistics.py:221-222`**

`self.raw_eigen_values = s[:]` returns a numpy **view**, not a copy. The subsequent in-place `s /= sum(s)` then corrupts `raw_eigen_values`.

**Status**: Reported by reviewer; code logic is consistent with the bug, not runtime-verified.

**Fix**: `self.raw_eigen_values = s.copy()` and compute percentages without in-place mutation: `self.eigen_value_percentages = s / s.sum()`.

### C4 — Multi-row writes/deletes without a transaction
**`ModanController.py:151-168` (delete loop), `243-286` (import loop)**

Multi-object delete and import run as per-row loops with **no `atomic()` wrapping**. A mid-loop failure leaves the DB half-modified. The delete path also manually recurses (`obj.delete_instance(recursive=True)` per object) even though the FKs already declare `on_delete="CASCADE"`.

**Fix**: Wrap in `with MdModel.gDatabase.atomic():`; rely on cascade (or a single bulk `delete().where(...)`). Consider `bulk_create` for large imports.

---

## HIGH (by area)

### DB / performance
- **N+1 queries** — `ModanController.py:594-597, 635-637`: CVA/MANOVA group extraction issues a separate `.where(id==obj.id).first()` per object (2N queries). Fix: build `{o.id: o}` dict once.
- **Redundant image queries** — `MdModel.py:316-348`: `has_image()` (COUNT) + `get_image()` (`self.image[0]`, raises `IndexError` instead of returning `None`) called up to 4× in `change_dataset`. Fix: `img = self.image.first()` once.
- **Parallel-list accumulators** — `MdModel.py:1041+, 1787`: `get_average_shape` maintains six parallel `sum_x/sum_y/sum_z/count_x...` lists via `range(len())`. Replace with numpy (also a known performance hotspot).

### Statistics (legacy classes)
- **Quadruple-nested Python loops** — `MdStatistics.py:138-206`: CVA covariance built element-by-element. Catastrophically slow with many landmarks. Vectorize with `np.cov` / matrix products.
- **Explicit matrix inversion** — `MdStatistics.py:212`: `np.linalg.inv(w)` fails hard on near-singular `w` (variables ≫ observations is the morphometric norm). Use `scipy.linalg.eig(b, w)` or `pinv` — the modern `do_manova_analysis` at line 802 already uses `pinv` (inconsistent).
- **3D Z-coordinate silently dropped** — `MdStatistics.py:509, 758`: `landmark[:2]` hard-codes 2D in CVA/MANOVA, inconsistent with PCA. Correctness bug for 3D data.
- **Silent MANOVA truncation** — `MdStatistics.py:607-612`: silently caps to "first 20 variables" via a magic constant, changing the statistical result without user-facing notice.

### Structure
- **God-methods** — `Modan2.py:371-619` `read_settings` (~250 lines, with an inline nested class); `ModanController.run_analysis` (~360 lines); `dataset_analysis_dialog.__init__` (371 lines); `object_dialog.__init__` (283 lines); `data_exploration_dialog.prepare_scatter_data` (285 lines).
- **Scatter-plot duplication** — hundreds of near-identical lines between `dataset_analysis_dialog.py:775` and `data_exploration_dialog.py:1639/2010`. Extract a shared builder/mixin.
- **DB/file I/O embedded in dialogs** — `object_dialog.py:1058 save_object()`, `:1109 Delete()` (`os.remove` + `delete_instance`), `import_dialog.py:364`. Should move to `ModanController` (as `analysis_dialog.py` already does correctly).
- **`read_settings`/color-marker loading copy-pasted across 9 dialogs** — hoist into `BaseDialog` or a settings mixin.

---

## MEDIUM — recurring patterns

| Pattern | Representative locations | Recommendation |
|---|---|---|
| **`locals()`-based control flow** (worst smell) | `ModanController.py:531, 764, 804` | Initialize vars (`analysis_type=None`, ...) at function top |
| **Type-overloaded parameters** (return type differs per branch) | `run_analysis`, `validate_dataset_for_analysis` | Split into separate methods |
| **Broad `except Exception` → sentinel/`ValueError` rewrap** (loses traceback) | controller & stats throughout; missing `raise ... from e` | Catch specific exceptions; chain with `from e` |
| **In-method imports** (already imported at top) | nearly all `MdStatistics.do_*`, `object_dialog.py:579/640`, many | Hoist to module scope |
| **Per-method `logger = getLogger(__name__)` recreation** | `MdModel` / `Modan2` 8+ sites | Use module-level logger |
| **`for i in range(len())` index loops** | `MdHelpers`, `preferences_dialog`, `MdModel` many | `enumerate` / `zip` / numpy |
| **`if x == "" / is None` repeated** | `MdModel` dozens of sites | `if not x:` helper |
| **Magic sentinels `99999 / -99999`** | `data_exploration_dialog.py:1695` + twin | `min`/`max` or `float('inf')` |
| **f-strings/concat inside `tr()`** (breaks i18n extraction) | `import_dialog.py:356, 362, 397` | placeholder + `.format()` |
| **Index-loop vector math despite numpy dependency** | `MdHelpers.py:860-948` (centroid/bbox/translate) | `np.mean/min/max(axis=0)` |

### Confirmed dead code / duplicate definitions
- `MdUtils.py:119-125` ↔ `194-200` — `resource_path` defined **twice** (identical).
- `MdModel.py:2037, 2043` — `cva_group_by` field declared **twice**.
- `Modan2.py:1305 vs 1314` — `treeView_drag_move_event` defined **twice** (first is dead).
- `Modan2.py:660` `if False:` block (references undefined `language`); `:1557, :1604` unreachable code after `return`.
- **`ModanDialogs.py` — entire 2539-line file is dead/duplicated.** Fully re-implemented in `dialogs/`; alive only via `from ModanDialogs import MODE` (`Modan2.py:71`) and test imports. (Contrast: `ModanComponents.py` is a correct, intentional re-export shim — keep it.)
- `MdConstants.py:537-541` — regex `REGEX_PATTERNS` use `\\.` (double backslash) in raw strings → matches a literal backslash; almost certainly a bug.
- `MdUtils.py:597` — `datetime.utcnow()` (deprecated in 3.12+); `MdUtils.py:286` — `is_numeric(None)` raises `TypeError` instead of returning `False`.

---

## LOW (selected)
- Shadowing builtins `object` / `sum`: `Modan2.py:1037, 1436`, `object_dialog.py:711, 1141`, `MdStatistics.py:51`.
- Py2-isms: `int(x / float(total) * 100)` — drop `float()` (`Modan2.py:1377, 1515`).
- `dialogs/object_dialog.py:936` — `None if dim == 3 else None` (both branches `None`).
- Stale commented-out cruft throughout `object_dialog.py` (dozens of `# self.x...` lines).
- `MdHelpers.py:982` — hardcoded `"qt_version": "5.15.x"` instead of `QT_VERSION_STR`.

---

## What is good (do NOT "fix")
- `dialogs/base_dialog.py`, `analysis_dialog.py`, `import_dialog.py`, `export_dialog.py` — well-decomposed (`_create_widgets`/`_create_layout` pattern), use f-strings, comprehensions, `with_wait_cursor`, controller delegation.
- `components/viewers/object_viewer_2d.py`, `object_viewer_3d.py` — modern idioms; their long `paintEvent`/`draw_object` are inherent to custom painting, not a smell.
- `MdStatistics.do_*` functions — modern (aside from in-function imports and broad except).
- No `bare except:`, no mutable default args, no `type(x) ==`, no live `== None`.

---

## Recommended fix order (value vs. risk)

1. **Remove confirmed dead code / duplicate definitions** (low risk, immediate): `resource_path` dup, `cva_group_by` dup, `treeView_drag_move_event` dup, `if False:` block, delete `ModanDialogs.py` (move `MODE` to `MdConstants`/`MdUtils` first, repoint tests). Removes thousands of lines.
2. **DB correctness** (high risk, high value, separate branch + tests): C2 (class-level mutable attrs → `__init__`), C1 (fix controller field names or unify on the `import_dialog` path), C4 (`atomic()` wrapping + rely on CASCADE).
3. **Statistics correctness**: C3 (view→copy), 3D Z-drop, `inv → pinv/solve`, MANOVA 20-variable silent truncation.
4. **N+1 query elimination** (performance): controller group extraction, `has_image`/`get_image`.
5. **Structural refactor** (medium-term): migrate the three large dialogs onto `BaseDialog` + controller; extract shared scatter builder; decompose `run_analysis` (`locals()` / type overload).

---

## Method note
Review performed by 4 parallel reviewers over: (1) DB layer — `MdModel.py` + controller/migrate DB usage; (2) utils/controller — `MdUtils.py`, `MdHelpers.py`, `ModanController.py`, `MdConstants.py`; (3) stats/main — `MdStatistics.py`, `Modan2.py`; (4) UI — `dialogs/`, `components/`, legacy shims. CRITICAL findings C1–C2 were manually verified against model definitions and call sites; C3–C4 are reviewer-reported and code-consistent but not runtime-verified. All line numbers reference the working tree as of 2026-06-25.
