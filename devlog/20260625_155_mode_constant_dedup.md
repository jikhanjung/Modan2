# MODE Dict De-duplication

**Date**: 2026-06-25
**Type**: Implementation log
**Follows**: [154 ModanDialogs Migration](20260625_154_modandialogs_migration.md)

---

## Summary

The `MODE` interaction-mode dict was copy-pasted, verbatim, into **15 modules**.
Consolidated to the single canonical definition added to `MdConstants.py` in
[154]. Net change: **+5 / −163 lines** across 15 files. Full suite stays green
(**1181 passed, 74 skipped, 0 failed**).

`MODE` maps the object viewers' mouse-interaction states:
`NONE / PAN / VIEW / EDIT_LANDMARK / MOVE_LANDMARK / READY_MOVE_LANDMARK /
WIREFRAME / PRE_WIRE_FROM / CALIBRATION`.

---

## Who actually used MODE?

Audited every definition for real `MODE[...]` references (vs. the 10-line
definition block itself):

| Module | Real uses | Action |
|---|---|---|
| `components/viewers/object_viewer_2d.py` | ~30 | import from MdConstants |
| `components/viewers/object_viewer_3d.py` | ~20 | import from MdConstants |
| `dialogs/object_dialog.py` | ~6 | import from MdConstants |
| `ModanComponents.py` | 0 (only `__all__` export) | import from MdConstants (keep export) |
| `components/formats/{tps,nts,morphologika,x1y1}.py` | 0 | **delete definition** |
| `components/widgets/{delegates,overlay_widget,drag_widgets,shape_preference,analysis_info,tree_view,table_view}.py` | 0 | **delete definition** |

**Finding**: `MODE` is only genuinely used by the 2D/3D object viewers and the
object-editing dialog that embeds them — i.e. the landmark-editing interaction
surface. The other 12 copies were dead duplication, left over from when these
modules were split out of the monolithic `ModanComponents`.

## How

- **4 used modules**: replaced the local 10-line block with
  `from MdConstants import MODE`. `ruff check --fix` / `ruff format` then
  organized the import placement.
- **11 dead modules**: deleted the block outright (no import added — adding an
  unused import would trip F401). Verified none of them export `MODE` via
  `__all__` or are imported-from elsewhere.

## Safety checks
- Only external importer of `MODE` from these modules:
  `tests/test_object_viewer_2d.py` (`from components.viewers.object_viewer_2d
  import MODE`). Still works — the module now obtains `MODE` via import, so it
  remains a module attribute.
- `ModanComponents.MODE` kept in `__all__` for backward-compat (no current
  importer, but the shim's public API is preserved).
- Smoke test: `MODE` resolves identically (9 keys) in all 4 used modules and via
  the external test import path.
- `ruff check` and `ruff format --check` pass on all changed files. The only
  non-blank additions in the diff are the 4 `from MdConstants import MODE` lines.

## Result

```
1181 passed, 74 skipped, 0 failed
```

## Files changed
15 modules (4 import / 11 delete) — see commit.

## Next candidates
1. DB correctness items from R01: C1 (controller `.create()` field names),
   C2 (class-level mutable list attrs), C4 (missing `atomic()` transactions).
2. `numpy==1.26` (pinned) vs `2.5.0` (installed) version mismatch.
3. Other constants duplicated alongside `MODE` (e.g. `MODE_EXPLORATION`,
   `OBJECT_MODE`, color/landmark constants) may warrant the same treatment.
