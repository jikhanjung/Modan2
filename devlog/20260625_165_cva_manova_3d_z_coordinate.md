# Statistics Correctness — CVA/MANOVA Dropped the 3D Z Coordinate

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 HIGH finding (3D Z-coordinate silently dropped via `landmark[:2]`)
**Follows**: [164 CVA inv→pinv](20260625_164_cva_pinv_singular_within_cov.md)

---

## Summary

`do_cva_analysis` and `do_manova_analysis` flattened landmark data with
`flat_coords.extend(landmark[:2])` — hard-coding 2 dimensions and **discarding the
Z coordinate of every landmark for 3D datasets**. `do_pca_analysis` already keeps
all coordinates (`datum.extend(lm)  # Use all coordinates (X, Y, Z for 3D)`), so
the three analyses were inconsistent: a 3D dataset's PCA used X/Y/Z while its CVA
used only X/Y.

Changed both to `extend(landmark)`. For 2D data this is identical
(`landmark[:2] == landmark`); for 3D data the Z axis is now included.

---

## Scope

| Function | Status | Live? |
|---|---|---|
| `do_cva_analysis` (line ~515) | fixed | **Yes** — `ModanController._run_cva` → `do_cva_analysis` |
| `do_manova_analysis` (line ~764) | fixed | No — not called outside tests, but fixed for consistency |
| `do_manova_analysis_on_procrustes` | already correct | Yes — the controller flattens with `extend(landmark)` (full coords) before calling it |
| `do_manova_analysis_on_pca` | n/a | Yes — operates on PCA scores, not raw landmarks |

So the user-visible bug was **CVA on 3D datasets**: the Z axis was thrown away
before the LDA, silently degrading (or invalidating) the canonical variates for
3D morphometric data.

## Test

`tests/test_mdstatistics.py::TestMdCanonicalVariate::test_cva_uses_z_coordinate_for_3d`
builds two groups of 3D specimens that are **identical in X and Y and differ only
in Z** (group A z≈0, group B z≈10). With Z included the groups separate perfectly
(`accuracy == 100`); under the old `landmark[:2]` every feature is constant and
the groups are indistinguishable (LDA errors / ~50%). Asserts `accuracy >= 99.0`.

## Status of R01 statistics items
- C3 view→copy — done.
- inv → pinv — done.
- 3D Z-coordinate dropped — done (this entry). ✅
- MANOVA silent 20-variable truncation — next (last statistics item).

## Files changed
`MdStatistics.py`, `tests/test_mdstatistics.py`.
