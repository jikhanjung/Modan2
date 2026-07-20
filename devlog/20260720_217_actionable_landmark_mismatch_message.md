# 217 — Tell the user to use "Insert Missing" when landmark counts disagree

**Date:** 2026-07-20
**Type:** implementation (NNN) — UX fix
**Related:** `devlog/20260720_214_add_missing_insert_at_position.md`,
`devlog/20260720_215_landmark_count_consistency.md`

## Problem

An object short a landmark was rejected with messages that named no cause and no
cure:

- analysis path — `"Procrustes superimposition failed"` (from `_prepare_landmarks`
  when `check_object_list` returns False). Says nothing about *which* object or
  *why*.
- validation paths — `"Inconsistent landmark count in object 'O2'"`. Names the
  object, but not what to do about it.

Since devlog 214 there *is* a fix the user can apply — select the row and press
"Insert Missing" to put a placeholder at the position that was not recorded — but
nothing pointed at it.

## Change

One wording, shared by all three gates (`landmark_mismatch_message` in
`ModanController`, alongside the single `find_landmark_count_mismatch` from 215):

> Object 'O2' has 3 landmarks but this dataset expects 4. Open the object and use
> "Insert Missing" to add a placeholder at each position that was not recorded.

`_prepare_landmarks` now runs the mismatch check *before* Procrustes and raises
this instead of the generic failure. The generic
`"Procrustes superimposition failed"` remains for the other ways superimposition
can fail — it is now only reached when the counts already agree, so it no longer
masks the common, fixable case.

## Verification

- `tests/test_landmark_count_consistency.py` grew a
  `TestMismatchMessageIsActionable` class (5 tests): the message names the object
  and both counts, mentions "Insert Missing", and both the validation path and
  the analysis path (`_prepare_landmarks`) actually surface it.
- `tests/test_controller.py::test_validate_inconsistent_landmark_count` asserted
  the old wording; updated to assert the object name and the remedy instead of
  the literal phrase, which is the property worth pinning.
- Full suite: **1388 passed, 75 skipped**.
