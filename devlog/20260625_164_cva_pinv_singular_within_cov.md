# Statistics Robustness — CVA `inv()` → `pinv()` on Singular Within-Covariance

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 HIGH finding (explicit matrix inversion fails on near-singular `w`)
**Follows**: [163 CVA eigenvalue view/copy (C3)](20260625_163_c3_cva_eigenvalue_view_copy.md)

---

## Summary

`MdCanonicalVariate.Analyze()` inverted the within-group covariance with
`numpy.linalg.inv(w)`. In morphometrics the number of variables routinely exceeds
the within-group degrees of freedom, making `w` **singular** — `inv()` then raised
`LinAlgError` and aborted CVA entirely (`Analyze()` → `False` → `PerformCVA()` →
`None`). Switched to `numpy.linalg.pinv(w)` (Moore-Penrose pseudo-inverse), which
handles the rank-deficient case. This also makes the legacy CVA class consistent
with the modern `do_manova_analysis`, which already uses `np.linalg.pinv`.

---

## Before / After

```python
# Before
try:
    wi = numpy.linalg.inv(w)        # raises on singular w -> CVA aborts
except numpy.linalg.LinAlgError:
    return False
x = numpy.dot(wi, b)

# After
try:
    wi = numpy.linalg.pinv(w)       # handles rank-deficient w
except numpy.linalg.LinAlgError:    # now only the rare SVD-non-convergence
    return False
x = numpy.dot(wi, b)
```

The `try/except` is kept so `PerformCVA`'s `if not analysis_return: return None`
safety contract is preserved for the rare case where the underlying SVD itself
fails to converge. For ordinary well-conditioned `w`, `pinv` equals `inv` to
numerical precision, so existing results are unchanged.

## Why it matters

CVA on typical landmark data (variables ≫ observations) previously failed
silently — `PerformCVA` returned `None` whenever the within-group covariance was
singular, which is the common case, not the exception.

## Test

`tests/test_mdstatistics.py::TestMdCanonicalVariate::test_cva_handles_singular_within_covariance`
builds 2 groups × 2 observations × 3 variables. The within-group covariance is
3×3 with **rank 2** (verified: `numpy.linalg.inv` raises `LinAlgError` on it), so
the old code aborted. The test asserts `Analyze()` now returns `True` and produces
a `rotated_matrix`.

## Status of R01 statistics items
- C3 view→copy — done.
- inv → pinv robustness — done (this entry). ✅
- 3D Z-coordinate dropped (`landmark[:2]`) — next.
- MANOVA silent 20-variable truncation — pending.

## Files changed
`MdStatistics.py`, `tests/test_mdstatistics.py`.
