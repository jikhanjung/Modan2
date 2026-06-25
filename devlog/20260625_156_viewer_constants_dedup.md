# Viewer Constants De-duplication

**Date**: 2026-06-25
**Type**: Implementation log
**Follows**: [155 MODE Dict Dedup](20260625_155_mode_constant_dedup.md)

---

## Summary

Continuation of the [155] `MODE` dedup: the whole block of constants that was
copy-pasted **alongside** `MODE` (object-viewer rendering/interaction constants)
was duplicated across 14 modules. Consolidated the genuinely-used ones into
`MdConstants.py` and deleted the dead copies.

Net change: **+71 / −915 lines** across 15 files. Full suite green
(**1181 passed, 74 skipped, 0 failed**); `ruff check` + `ruff format` clean.

---

## Method

Used AST to find each constant's **real in-function usage** (vs. the copy-pasted
definition block, which makes everything look "used" by grep). The block —
`MODE_EXPLORATION … NEWLINE`, including the `COLOR` and `ICON` dicts — sat in 14
modules but was almost entirely dead.

### Consolidated to MdConstants (genuinely used)
Used only by `ObjectViewer2D` / `ObjectViewer3D`:

| Constant(s) | Used by |
|---|---|
| `COLOR` (RGB dict), `OBJECT_MODE`, `DATASET_MODE` | both viewers |
| `VIEW_MODE`, `PAN_MODE`, `ROTATE_MODE`, `ZOOM_MODE`, `WIREFRAME_MODE` | 3D viewer |
| `BASE_LANDMARK_RADIUS`, `DISTANCE_THRESHOLD` | 2D viewer |

Added under an "Object Viewer Constants" section in `MdConstants.py`; the two
viewers now `from MdConstants import …`. `ModanComponents.py` (compat shim)
re-exports them and its `__all__` was pruned of the dead names.

### Deleted as dead (defined but never used anywhere they were copied)
`MODE_EXPLORATION/REGRESSION/GROWTH_TRAJECTORY/AVERAGE/COMPARISON/COMPARISON2`,
`CENTROID_SIZE_VALUE`, `CENTROID_SIZE_TEXT`, `LANDMARK_MODE`, `NEWLINE`, and the
local `ICON` dicts — removed from all 14 modules (11 format/widget modules +
2 viewers + `ModanComponents`).

`ICON`: the only real user is `dialogs/object_dialog.py`, which already imports
`from MdConstants import ICONS as ICON`. The 14 local `ICON` copies (built with
`mu.resource_path`) were dead — deleted. `object_dialog.py` was left untouched.

## Important findings / things deliberately NOT changed

- **`CENTROID_SIZE_VALUE` differs by context**: `99` in the viewer copies (dead),
  but `9999` in `dialogs/data_exploration_dialog.py` (live). These are *different*
  constants that happen to share a name — NOT merged. The viewer copies were
  deleted; data_exploration keeps its own.
- **Analysis-mode constants are a separate cohort**: `MODE_EXPLORATION` etc. are
  defined and used only within `dialogs/data_exploration_dialog.py` (and `NEWLINE`
  in `export_dialog.py`). After removing the dead viewer copies they are each
  defined exactly once — no duplication remains. `MODE_GROWTH_TRAJECTORY` is now
  undefined but only appears in comments / an `if False:` block (no live ref).
- **Distinct `COLOR` variants left as-is**:
  - `components/widgets/dataset_ops_viewer.py` — a small hex-string COLOR dict
    (`"#FFFFFF"` …) with different keys; unrelated to the RGB-tuple viewer COLOR.
  - `dialogs/data_exploration_dialog.py` — same RGB base but only a 4-key subset
    of the extension keys (vs. 10 in the canonical). Not an exact duplicate;
    importing the shared canonical dict would also introduce shared-mutable-state
    risk. Left independent.
- **GLUT flags** (`GLUT_AVAILABLE`, `GLUT_INITIALIZED`, `glut`) are runtime state
  set per-module by GLUT init code — not constants; untouched.

## Verification
- AST usage audit + project-wide grep confirmed no module imports these constants
  from the edited files (only `tests/test_object_viewer_2d.py` imports `MODE`,
  still resolved via the new import).
- Smoke test: `COLOR`, `OBJECT_MODE`, mode constants resolve identically in both
  viewers and `ModanComponents`.
- `ruff check` / `ruff format --check`: clean. Full suite: 1181 passed.

## Files changed
`MdConstants.py` (+ viewer constants), `ModanComponents.py`, both viewers, and
11 format/widget modules (block deletions). See commit.

## Next candidates
1. DB correctness items from R01: C1/C2/C4.
2. `numpy==1.26` (pinned) vs `2.5.0` (installed) mismatch.
