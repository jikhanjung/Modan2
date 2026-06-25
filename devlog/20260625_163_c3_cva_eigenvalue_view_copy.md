# Statistics Correctness C3 — CVA Eigenvalue numpy View-vs-Copy

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 finding **C3** (numpy view aliasing corrupts CVA `raw_eigen_values`)
**Follows**: [162 class-level mutable attrs (C2)](20260625_162_c2_class_level_mutable_attrs.md)

---

## Summary

`MdCanonicalVariate.Analyze()` stored the CVA eigenvalues with a numpy **view**,
then normalized the underlying array in place — silently overwriting the "raw"
eigenvalues with the normalized percentages.

```python
self.raw_eigen_values = s[:]      # s[:] is a VIEW of s, not a copy
s /= sum(s)                       # in-place -> also mutates raw_eigen_values
self.eigen_value_percentages = s[:]
```

After this block `raw_eigen_values` and `eigen_value_percentages` referenced the
**same normalized data**. The legacy CVA class is live (instantiated by
`do_cva_analysis` and directly by `dataset_analysis_dialog.py`), and the CVA
detail eigenvalue table reads both:

```python
# dialogs/dataset_analysis_dialog.py:652
for i, val in enumerate(self.analysis_result.raw_eigen_values):
    val2 = self.analysis_result.eigen_value_percentages[i]
```

So the "Eigenvalue" and "%" columns showed identical normalized numbers — a
visible, live bug, not just latent.

## Fix

```python
self.raw_eigen_values = s.copy()
self.eigen_value_percentages = s / s.sum()
```

`s.copy()` decouples the raw values from later mutation, and `s / s.sum()`
produces the percentages without mutating `s` in place. Raw eigenvalues and
percentages are now independent arrays. (The PCA class at line 50 was already
safe — it builds percentages with an append loop and never mutates `s`.)

## Test

`tests/test_mdstatistics.py::TestMdCanonicalVariate::test_cva_raw_eigenvalues_not_normalized`
runs CVA on the grouped fixture and asserts:
- `sum(eigen_value_percentages) ≈ 1.0`,
- `eigen_value_percentages == raw_eigen_values / raw_eigen_values.sum()`,
- `raw_eigen_values` is **not** already normalized (`not np.allclose(raw, pct)`)
  — the assertion that fails under the old aliasing bug.

## Status of R01 statistics items
- **C3** view→copy — done (this entry). ✅
- inv → pinv robustness (`MdStatistics.py:212`) — next.
- 3D Z-coordinate dropped (`landmark[:2]`) — pending.
- MANOVA silent 20-variable truncation — pending.

## Files changed
`MdStatistics.py`, `tests/test_mdstatistics.py`.
