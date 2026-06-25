# Statistics Correctness — Surface MANOVA Variable Truncation

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 HIGH finding (silent MANOVA truncation to "first 20 variables" via a magic constant)
**Follows**: [165 CVA/MANOVA 3D Z coordinate](20260625_165_cva_manova_3d_z_coordinate.md)

---

## Summary

`do_manova_analysis_on_procrustes` capped the dependent variables to the **first
20** with an inline magic number and only a `logger.warning` — the returned result
reported `n_variables: 20` with no indication that the analysis had silently
dropped the rest. A caller (or the user) could not tell whether a MANOVA used all
60 coordinates or an arbitrary first-20 subset, even though that materially changes
the statistical result.

The cap itself is legitimate: statsmodels' MANOVA needs the residual covariance to
be invertible (roughly observations > variables + groups), which breaks for high
landmark counts. The problem was that the truncation was **silent**, not that it
existed. Made it explicit and reported.

---

## Changes (`MdStatistics.py`)

1. **Named the magic number** — module constant `MANOVA_MAX_VARIABLES = 20` with a
   docstring explaining the statistical reason.
2. **Surfaced the truncation in the result dict**:
   ```python
   "n_variables": len(column_names),       # kept (used count) for back-compat
   "n_variables_total": n_variables_total, # variables before any cap
   "n_variables_used": len(column_names),  # variables actually fed to MANOVA
   "truncated": truncated,                 # bool
   ```
   The warning log message now also states that the result reports `truncated=True`.

This is a data-layer fix: the result now carries the information needed for a
caller/dialog to tell the user "MANOVA used 20 of 60 variables" instead of
presenting a partial result as if it were complete. The numerical computation and
the cap value are unchanged, so existing behavior/results are preserved.

### Deliberately out of scope
The arbitrary *first*-20 selection is still statistically crude (a principled fix
is dimensionality reduction — which the controller already prefers via
`do_manova_analysis_on_pca`, using the procrustes path only as a fallback). That is
a redesign, not part of making the existing truncation honest.

## Tests (`tests/test_mdstatistics.py`)
- `test_manova_on_procrustes_variable_limiting` — extended to assert
  `n_variables_total == 45`, `n_variables_used == 20`, `truncated is True`.
- `test_manova_on_procrustes_not_truncated` (new) — 6 variables (< cap); asserts
  `truncated is False` and total == used == 6.

## Status of R01 statistics items — all done ✅
- C3 view→copy, inv → pinv, 3D Z-coordinate, MANOVA silent truncation — all
  resolved. This closes the **HIGH — Statistics** group from R01.

## Files changed
`MdStatistics.py`, `tests/test_mdstatistics.py`.
