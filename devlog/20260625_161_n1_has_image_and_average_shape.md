# N+1 / Hotspot Fixes — `change_dataset` Media Queries & `get_average_shape`

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 findings **N+1 #2** (redundant image/3D queries in `change_dataset`) and **#3** (parallel-list accumulators in `get_average_shape`)
**Follows**: [160 N+1 CVA/MANOVA group extraction](20260625_160_n1_query_cva_manova.md)

---

## Summary

Two `MdModel` cleanups from R01:

1. **`MdObject.change_dataset`** issued up to **8 queries** (`has_image()`/`has_threed_model()` COUNTs + `get_image()`/`get_threed_model()` indexed fetches, repeated before *and* after the save) to relocate one media file. Now fetches the linked media **once**.
2. **`MdDatasetOps.get_average_shape`** built six parallel Python lists (`sum_x/y/z`, `count_x/y/z`) growing them by index in a hand-rolled loop — a known performance hotspot. Replaced with a single vectorized `np.nanmean`.

Both are behavior-preserving (with one latent crash now fixed — see below). Full suite green, ruff clean.

---

## N+1 #2 — `change_dataset` (`MdModel.py`)

### Before
```python
def change_dataset(self, dataset):
    if self.has_image():            # COUNT
        source_path = self.get_image().get_file_path()   # self.image[0]
    if self.has_threed_model():     # COUNT
        source_path = self.get_threed_model().get_file_path()
    self.dataset = dataset
    self.save()
    if self.has_image():            # COUNT (again)
        target_path = self.get_image().get_file_path()
    if self.has_threed_model():     # COUNT (again)
        target_path = self.get_threed_model().get_file_path()
    if os.path.exists(source_path):  # NameError if object has neither!
        ...
```

Two problems:
- **Redundant queries**: 4 COUNTs + up to 4 indexed fetches for a single relocate.
- **Latent crash**: a landmark-only object (no image, no 3D model) never assigns
  `source_path`, so `os.path.exists(source_path)` raised `NameError`. The one
  caller (`Modan2.py` shift-drag "move object to dataset") could hit this with a
  landmark-only object.

### After
```python
def change_dataset(self, dataset):
    media = self.image.first() or self.threed_model.first()   # 1–2 queries
    source_path = media.get_file_path() if media is not None else None
    self.dataset = dataset
    self.save()
    if media is None:
        return                                                # no file to move
    media.object = self      # refresh the cached relation to the saved object
    target_path = media.get_file_path()
    if os.path.exists(source_path):
        ...
```

**The subtle bit — `media.object = self`.** `get_file_path()` resolves the storage
directory through `self.object.dataset.id`. The `media.object` relation is cached
on the `media` instance and still pointed at the *old* dataset after our save, so
naively reusing `media` would have computed `target_path` from the old dataset and
silently no-op'd the move. Re-attaching the just-saved `self` makes
`media.get_file_path()` resolve the **new** dataset. `source_path` is computed
*before* the save, while the cached relation still reflects the old dataset — so it
stays correct.

## N+1 #3 — `get_average_shape` (`MdModel.py`)

Replaced the six parallel `sum_*/count_*` lists and manual index-growing loop with:

```python
n_dim = 3 if self.dimension == 3 else 2
n_landmarks = max((len(mo.landmark_list) for mo in self.object_list), default=0)
# (n_objects, n_landmarks, n_dim); missing/None coords -> NaN, ragged objects padded
stacked = np.array([...], dtype=float)
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)  # all-NaN slice
    means = np.nanmean(stacked, axis=0)
average_shape.landmark_list = [[None if np.isnan(v) else float(v) for v in row] for row in means]
```

`object_list` is an in-memory list of `MdObjectOps` (not a query), so this was a
CPU hotspot rather than a query problem. Behavior preserved exactly:
- per-coordinate masking of `None`/missing values (`np.nanmean` ignores `NaN`),
- ragged landmark counts padded to the max,
- a coordinate missing in *every* object → `None` (the all-NaN slice, whose numpy
  `RuntimeWarning` is suppressed),
- 2D → `[x, y]`, 3D → `[x, y, z]`.

## Tests (`tests/test_mdmodel.py`)

- **`test_change_dataset`** — rewritten to actually call `change_dataset()` on a
  landmark-only object (it previously *avoided* the call and hand-set the field
  because the old code crashed). Guards the `NameError` fix.
- **`test_change_dataset_moves_media_file`** (new) — links a real `MdImage`,
  writes a file at the computed source path, calls `change_dataset`, and asserts
  the file now lives under the **new** dataset's directory and the old path is
  gone. Directly guards the `media.object = self` staleness fix. Cleans up files
  in a `finally`.
- **`test_get_average_shape_ragged_counts`** (new) — objects with 3 vs 2 landmarks;
  asserts the result sizes to the max and the extra landmark averages only its one
  contributor.
- **`test_get_average_shape_all_missing_coordinate`** (new) — a landmark that is
  `None` in every object averages to `[None, None]` (no crash, no warning leak).

Existing 2D/missing/3D average-shape tests pass unchanged.

## Status of R01 N+1 / DB items
- **C4** transactions, **C1** field names, **N+1 #1** CVA/MANOVA — done.
- **N+1 #2** (`change_dataset`), **#3** (`get_average_shape`) — done (this entry).
- **C2** (class-level mutable list attributes in `MdModel`) — remaining correctness item.

## Files changed
`MdModel.py`, `tests/test_mdmodel.py`.
