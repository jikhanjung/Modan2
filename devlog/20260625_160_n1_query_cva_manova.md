# N+1 Query Fix — CVA/MANOVA Group Extraction

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 N+1 finding #1 (per-object query inside the CVA/MANOVA group-extraction loops)
**Follows**: [159 DB create field names (C1)](20260625_159_db_create_field_names_c1.md)

---

## Summary

`run_analysis`'s comprehensive PCA path extracts per-object group labels for CVA
and MANOVA. Each loop issued **one SELECT per object** to map a superimposed
object back to its source row — an N+1 over the dataset's objects, run for *both*
CVA and MANOVA (so ~2N queries per analysis). Replaced with a single prebuilt
`{id: object}` map.

Performance change only (results unchanged). Full suite **1185 passed** (+1 new
coverage test), 74 skipped, 0 failed. ruff clean.

---

## Before

```python
# CVA loop (and an identical MANOVA loop)
for obj in ds_ops.object_list:                          # N superimposed objects
    obj_model = self.current_dataset.object_list.where(  # one SELECT per object
        MdModel.MdObject.id == obj.id
    ).first()
    ...
```

For a dataset of N objects this is N queries for CVA + N for MANOVA = ~2N
redundant SELECTs, all hitting the same `object_list` relation.

## After

```python
# Built once, only when a grouping is actually requested:
objects_by_id = {}
if cva_group_by is not None or manova_group_by is not None:
    objects_by_id = {o.id: o for o in self.current_dataset.object_list}

# Both loops now do an in-memory lookup:
for obj in ds_ops.object_list:
    obj_model = objects_by_id.get(obj.id)
    ...
```

~2N queries → **1** (the single map-building query), and only when CVA/MANOVA
grouping is requested. Lookup is by primary key, so `objects_by_id.get(obj.id)`
returns exactly the object the old `.where(id == obj.id).first()` did — behavior
is identical.

## Scope notes
- Minimal, behavior-preserving change. Deliberately did **not** merge the two
  near-identical CVA/MANOVA extraction blocks into a shared helper (a separate
  R01 duplication finding) — kept each block's existing logging/edge-case
  handling intact to keep the diff focused on the N+1.
- Other N+1-ish items from R01 (`has_image()`+`get_image()` double query in
  `MdModel.change_dataset`; `get_average_shape` parallel-list accumulation)
  are untouched here.

## Test

Added `TestAnalysisParameters::test_pca_cva_group_extraction_maps_objects`:
builds a small dataset (4 distinct shapes, two `property_str` groups, one
variable name), mocks `_run_cva` to capture the extracted `groups`, runs
`run_analysis(ds, cva_group_by=0)`, and asserts the extraction produced one
correct label per object with no `"Unknown"` — i.e. the id map resolved every
object. Targets the extraction logic directly rather than the downstream CVA
math.

## Files changed
`ModanController.py`, `tests/test_controller.py`.
