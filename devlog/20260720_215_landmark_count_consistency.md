# 215 — One definition of "landmark count", shared by every gate

**Date:** 2026-07-20
**Type:** implementation (NNN) — correctness fix

## Problem

Two counting notions existed and got mixed:

| | counts | used by |
|---|---|---|
| `MdObject.count_landmarks()` | **recorded** landmarks (missing excluded, by default) | object table display |
| `len(obj.landmark_list)` | landmark **positions** (missing included) | `check_object_list`, the Procrustes gate |

The controller's pre-analysis validation compared **one against the other**:

```python
expected_count = first_obj.count_landmarks()        # excludes missing
for obj in objects_with_landmarks:
    obj.unpack_landmark()
    if len(obj.landmark_list) != expected_count:    # includes missing
        return False, f"Inconsistent landmark count in object '{obj.object_name}'"
```

So if the **first** object had any missing landmark, `expected_count` was
deflated and every object failed — including the first one, against itself.
Reproduced: a 3-object dataset with one missing landmark in object 0 gave

```
(False, "Inconsistent landmark count in object 'O0'")
```

while `check_object_list()` — the gate that actually decides whether Procrustes
runs — said `True`. The two gates disagreed about the same dataset.

## Root cause, and the fix

Two places answering the same question separately. Consolidated into one
implementation in `MdModel`:

- `landmark_position_count(obj)` — positions, missing included; works for both
  `MdObject` (unpacking on demand) and `MdObjectOps`.
- `find_landmark_count_mismatch(objects)` → `(object, expected, found)` or
  `None`.

Now used by `check_object_list` and both controller validators, so they cannot
drift apart again. Two further sites that used the missing-excluding count
against position counts were corrected the same way: the import-time count
warning, and `get_dataset_info`'s reported `landmark_count` (a specimen with a
gap must not shrink the dataset's landmark count).

`count_landmarks()` keeps its default — it is the right measure for "how many
landmarks were actually recorded", which is what the object table shows — with a
docstring note pointing consistency checks at the new function.

## Behaviour

| dataset | before | after |
|---|---|---|
| complete | passes | passes |
| missing landmark in first object | **rejected** | passes |
| missing landmark in a later object | passes | passes |
| object genuinely short a landmark | rejected | rejected (message now names expected vs found) |

## Verification

- `tests/test_landmark_count_consistency.py` (new, 14 tests): position counting
  vs recorded counting, `MdObjectOps` support, mismatch detection and reporting,
  and a `TestGatesAgree` class asserting `check_object_list` and the controller
  validator give the *same* verdict on the same dataset — which is the property
  that was actually broken.
- Full suite: **1383 passed, 75 skipped**.
