# DB Correctness C2 — Class-Level Mutable Attributes in `MdModel`

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 finding **C2** (mutable list defaults declared at class scope, shared across all instances)
**Follows**: [161 N+1 has_image / get_average_shape](20260625_161_n1_has_image_and_average_shape.md)

---

## Summary

`MdDataset` and `MdObject` declared their non-DB "scratch" attributes as
**class-level** values:

```python
class MdDataset(Model):
    ...
    baseline_point_list = []
    edge_list = []
    polygon_list = []
    variablename_list = []

class MdObject(Model):
    ...
    landmark_list = []
    variable_list = []
    centroid_size = -1
```

In Python a `= []` at class scope creates **one list object shared by every
instance**. Any code that mutates it in place (`self.edge_list.append(...)`,
`self.landmark_list.sort()`, etc.) without first rebinding `self.x = [...]`
mutates that shared list — so data could leak from one dataset/object into
another. Moved all of them into `__init__` so each instance gets its own.

Full suite green, ruff clean.

---

## Why it was (mostly) latent

Most accessors rebind before use — e.g. `unpack_landmark` starts with
`self.landmark_list = []`, which creates a fresh **instance** attribute that
shadows the class one. So the common read/write paths happened to be safe. The
danger lived in the in-place mutators (`pack_wireframe` sorts `self.edge_list` in
place; any `.append` onto a never-rebound list) and in the simple fact that two
freshly-constructed instances shared identity (`a.landmark_list is b.landmark_list`
was `True`). It was a correctness landmine, not a guaranteed crash.

## The fix

Removed the class-level assignments and initialize per instance in an `__init__`
override that chains to Peewee:

```python
class MdObject(Model):
    ...
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.landmark_list = []
        self.variable_list = []
        self.centroid_size = -1
```

(`MdDataset` does the same for its four lists.)

### Why this is safe with Peewee
Peewee instantiates rows through the model constructor — its cursor wrapper does
`obj = self.constructor(__no_default__=1, **result)` (peewee 4.1.0,
`ModelObjectCursorWrapper.process_row`). That means **both** `Model.create(...)`
*and* loading objects from a query go through `__init__`. Calling
`super().__init__(*args, **kwargs)` first preserves all of Peewee's field/default
handling; we only add our non-field scratch attributes afterward. These names are
not `Field` instances, so they never participate in `__data__` / the DB schema.

`centroid_size` stays `-1`: `get_centroid_size()` treats `<= 0` as "not yet
computed" and recomputes, so the sentinel behavior is unchanged.

The `MdObjectOps` / `MdDatasetOps` wrapper classes already initialized these in
their own `__init__` (e.g. `self.centroid_size = -1`), so they were never
affected and needed no change.

## Tests (`tests/test_mdmodel.py`)
- `test_scratch_lists_are_per_instance` — two `MdObject`s have distinct
  `landmark_list`/`variable_list` (`is not`), and mutating one leaves the other
  empty; `centroid_size` defaults to `-1`.
- `test_dataset_scratch_lists_are_per_instance` — same guarantee for
  `MdDataset.edge_list` / `variablename_list`.

Both would have failed against the old class-level lists.

## Status of R01 DB correctness items
- **C1** field names, **C4** transactions — done.
- **C2** class-level mutable attributes — done (this entry). ✅
- N+1 query patterns (#1 CVA/MANOVA, #2 change_dataset, #3 get_average_shape) — done.

All R01 DB-correctness and N+1 items are now resolved.

## Files changed
`MdModel.py`, `tests/test_mdmodel.py`.
