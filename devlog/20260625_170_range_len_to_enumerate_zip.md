# Refactor — `range(len(...))` Index Loops → `enumerate` / `zip` / slice

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 MEDIUM "`for i in range(len())` index loops" (`MdModel`)
**Follows**: [169 exception chaining](20260625_169_exception_chaining_raise_from.md)

---

## Summary

Converted the `for i in range(len(x))` loops in `MdModel.py` that exist purely to
index back into `x` (a C-style idiom) to direct iteration. Behavior-preserving;
purely a readability change.

`MdModel.py` had 10 such loops; **3** were genuine smells and were converted, and
**4** were left intentionally (see below).

---

## Converted

| Loop | Before | After |
|---|---|---|
| `rotate_to_reference_shape` coord copy | `for j in range(len(lm)): coords[j] = lm[j]` | `for j, value in enumerate(lm): coords[j] = value` |
| `is_same_shape` landmark compare | `for i in range(len(shape1.landmark_list)): ... shape1.landmark_list[i] ... shape2.landmark_list[i]` | `for lm1, lm2 in zip(shape1.landmark_list, shape2.landmark_list, strict=False):` |
| `backup` pruning | `for i in range(len(backup_list) - 10): os.remove(... backup_list[i])` | `for old_backup in backup_list[:-10]: os.remove(... old_backup)` |

- The `zip(..., strict=False)` matches the previous "stop at the shorter list"
  effect (procrustes convergence always compares equal-length shapes; `strict`
  documents the intent and satisfies flake8-bugbear B905).
- `backup_list[:-10]` reproduces the old index range exactly, including the
  `len <= 10` case (both yield no removals).

## Left as-is (intentional)

- `for j in range(len(self.object_list)): self.rotate_*(j)` (4 sites — lines
  ~1616/1624/1672/1742) iterate **only for the index**, which is passed to a
  method; there is no value to bind, so `range(len(...))` is the correct,
  non-smell form here. `enumerate` would just introduce an unused variable.
- Two loops in `estimate_missing_landmarks` / `_apply_rotated_shape` (lines
  ~1442/1553) use the index for several cross-structure lookups; converting them
  is higher-risk churn for little gain, so they were skipped.

## Tests

No new tests — behavior is unchanged. `test_mdmodel.py` (266 tests, incl. the
Procrustes/convergence paths that exercise `is_same_shape`) passes; full suite
green, ruff clean.

## Files changed
`MdModel.py`.
