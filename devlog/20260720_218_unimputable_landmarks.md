# 218 — Reject landmarks that are missing in every object

**Date:** 2026-07-20
**Type:** implementation (NNN) — correctness / UX
**Related:** `devlog/20260720_215_landmark_count_consistency.md`,
`devlog/20260720_217_actionable_landmark_mismatch_message.md`

## Problem

Procrustes fills a missing coordinate from the per-coordinate mean of the other
objects. When **every** object is missing the same coordinate, that mean is
undefined (`nanmean` of an all-NaN slice → `NaN` → `None`), so the `None`
survived superimposition and only blew up much later, inside the analysis matrix:

```
ValueError: PCA analysis failed: float() argument must be a string or a real number, not 'NoneType'
```

Nothing in that message says which landmark, that the cause is a gap in the data,
or that the situation is unfixable by imputation in principle.

## Change

`MdModel.find_unimputable_landmarks(objects)` returns the 0-based landmark
indices that no object records, and `unimputable_landmarks_message` renders the
shared wording (1-based, to match the object dialog's table):

> Landmark 3 is missing in every object, so there is nothing to estimate it from.
> Record it in at least one object, or remove that landmark from the dataset.

Wired into the same three gates as the count-mismatch check: `_prepare_landmarks`
(raises) and both controller validators (return False / warn).

## Detection is per coordinate, reporting is per landmark

A landmark whose X is present everywhere but whose Y is absent everywhere is just
as unimputable as one that is wholly absent — and it crashed identically. So the
scan tests each coordinate independently and reports the landmark it belongs to.
Verified: a dataset where only the Y of landmark 3 is missing throughout is
caught, where a naive "is the whole landmark missing" check would have let it
through to the same opaque failure.

## Behaviour

| dataset | before | after |
|---|---|---|
| landmark missing in one object | imputed, analysis runs | unchanged |
| landmark missing in all but one object | imputed, analysis runs | unchanged |
| landmark missing in **every** object | `NoneType` error from deep inside PCA | named up front, analysis declined |
| one axis missing in every object | same `NoneType` error | named up front |

## Verification

- `tests/test_unimputable_landmarks.py` (new, 16 tests): detection (whole
  landmark, single axis, several landmarks, 3D Z), the imputable cases that must
  *not* trip it (missing in one object, missing in all but one), a single-object
  dataset, message singular/plural and 1-based numbering, and all three gates —
  including an assertion that the raised message no longer mentions `NoneType`,
  and that an imputable dataset still completes `_prepare_landmarks` with no
  `None` left.
- Full suite: **1404 passed, 75 skipped**.

## Closes

The last open gap from the missing-landmark work — `HANDOFF.md` listed this as
the one remaining PCA failure mode.
