# DB Correctness C1 — Controller `.create()` Field Names

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 finding **C1** (`.create()` called with non-model field names → silent data loss)
**Follows**: [158 DB transactions (C4)](20260625_db_transactions_c4.md)

---

## Summary

`ModanController`'s create/import methods passed keyword arguments that are **not
model fields**. Peewee silently ignores unknown kwargs, so the data was dropped
without error — most importantly, imported **landmarks were never persisted**.

Fixed all call sites to use the real fields / model relationships, and added two
regression tests that read the data back from the DB. Full suite **1184 passed**
(+2), 74 skipped, 0 failed. ruff clean.

---

## The bugs (all in `ModanController.py`)

| Call | Wrong kwarg | Reality |
|---|---|---|
| `create_dataset` | `MdDataset.create(..., landmark_count=...)` | no such field; count is derived from objects |
| `_import_landmark_file` | `MdObject.create(..., landmarks=...)` | field is `landmark_str` (packed string) |
| `_import_image_file` | `MdImage.create(file_path=, dataset=)` + `MdObject.create(..., image=)` | `MdImage` has `original_path` + `object` FK; there is no `image` field on `MdObject` |
| `_import_3d_file` | `MdThreeDModel.create(file_path=, dataset=)` + `MdObject.create(..., model_3d=)` | `MdThreeDModel` has `original_path` + `object` FK; no `model_3d` field on `MdObject` |

Because Peewee accepts and discards unknown kwargs, none of these raised — the
import path "succeeded" while saving empty/unlinked records. (This path is
currently reached only by tests, not the live UI, which goes through
`dialogs/import_dialog.py`; so it was a **latent** bug — it would bite the moment
UI import is routed through the controller, the stated architectural goal.)

## The fix

- **`create_dataset`**: drop `landmark_count=` from `create()` (kept as a
  validation/logging parameter only).
- **`_import_landmark_file`**: create the object, then populate the real field via
  the model helper — `obj.landmark_list = landmarks; obj.pack_landmark(); obj.save()`.
- **`_import_image_file` / `_import_3d_file`**: create the **object first**, then
  create the child record with the correct relationship —
  `MdImage.create(object=obj, original_path=..., original_filename=...)` (and the
  `MdThreeDModel` equivalent). Both remain inside the C4 transaction.

Chose to keep `MdImage.create(...)` / `MdThreeDModel.create(...)` (rather than the
`obj.add_image()` helper that also copies the file to managed storage) because
the fix here is about **field-name correctness**; switching to file-copying
behavior is a separate concern and would have broken the existing mock-based
tests. The records now store `original_path` and link via the `object` FK.

## Tests

Existing tests needed **no changes** — they mock `MdImage.create` /
`MdThreeDModel.create` and only assert `called_once()`, which still holds.

Added two regression guards in `TestObjectOperations` (would have failed before
the fix):
- `test_import_tps_persists_landmarks` — reloads the imported object from the DB
  and asserts `landmark_str` is non-empty and `count_landmarks() == 3`.
- `test_import_image_links_to_object` — asserts the imported object has exactly
  one linked `image` and its `original_path` is correct.

## Status of R01 DB items
- **C4** (transactions) — done ([158]).
- **C1** (field names) — done (this entry).
- **C2** (class-level mutable list attributes in `MdModel`) — remaining.
- N+1 query patterns — remaining (performance, not correctness).

## Files changed
`ModanController.py`, `tests/test_controller.py`.
