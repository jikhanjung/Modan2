# Performance — Vectorize CVA Covariance Construction

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 HIGH "Quadruple-nested Python loops — CVA covariance built element-by-element (catastrophically slow with many landmarks)"
**Follows**: [174 repo-wide ruff clean](20260625_174_repo_wide_ruff_clean.md)

---

## Summary

`MdCanonicalVariate.Analyze()` built the within- and between-group covariance
matrices with **quadruple-nested Python loops** (`p × q × observation` and
`p × q × category`), i.e. `O(nVar² · nObs)` pure-Python work. For morphometric
data (dozens of landmarks → 40–90 variables) this dominated CVA runtime. Replaced
the loops with numpy matrix products. Eigenvalues are numerically identical and
the significant canonical variates are preserved.

---

## What changed (`MdStatistics.py`)

The covariance construction is now:

```python
X = numpy.asarray(self.data, dtype=float)          # (nObs, nVar)
total_avg = X.mean(axis=0)
variances = ((X - total_avg) ** 2).sum(axis=0)
kept = variances != 0                               # drop zero-variance variables

# within: center each obs on its group mean, then Sᵀ S / (n − groups)
within_dev = X - numpy.array([group_means[c] for c in cat_arr])
within_full = (within_dev.T @ within_dev) / (total_count - n_cat)

# between: group-mean deviations weighted by group size
dev = numpy.array([group_means[k] - total_avg for k in category_set])
weights = numpy.array([counts[k] for k in category_set], dtype=float)
between_full = (dev.T * weights) @ dev / n_cat

w = within_full[numpy.ix_(kept, kept)]
b = between_full[numpy.ix_(kept, kept)]
```

The rotation-matrix scatter and the `np_data` copy loop were vectorized too:

```python
rotation_matrix = numpy.zeros((self.nVariable, self.nVariable))
rotation_matrix[numpy.ix_(kept_idx, kept_idx)] = u   # was a p × q double loop
self.rotated_matrix = numpy.dot(X, rotation_matrix)  # was an element-wise copy loop
```

The `pinv`/`svd`/eigenvalue section (and its prior R01 fixes) is unchanged.

### Dead code removed along the way
Three locals that were computed but never read were dropped:
- `covariance_matrix` (a full PCA-style covariance built with its own `p×q×obs`
  triple loop — never stored or used),
- `within_by_category` / `between_by_category` dicts (allocated, never written/read).

## Numerical equivalence (verified)

Compared the new output against a verbatim reimplementation of the old loops on
several datasets (2-group/2-var, 3-group/4-var, and a case with a constant
zero-variance column):

- **Eigenvalues match** to ~1e-12 in every case.
- **Rotated matrix matches** exactly where the result is well-defined. In the
  3-group/4-var case the *raw* rotated matrices differed — but only in the columns
  for **zero eigenvalues** (the SVD null space, whose basis is arbitrary and
  swings under ~1e-12 input perturbations in both old and new code). The columns
  for the **non-zero (significant) canonical variates match up to sign**, which is
  the inherent SVD sign convention. No information-bearing output changed.

## Test

Added `test_cva_drops_zero_variance_column`: a 3-variable dataset whose middle
variable is constant; asserts `Analyze()` succeeds, the rotation matrix's row and
column for the constant variable are zero, and the varying variables still carry
loadings. Locks in the `kept`-mask / `ix_` scatter path. Existing CVA tests
(shapes, eigenvalue ordering, raw≠pct, singular-`w`) pass unchanged.

## Files changed
`MdStatistics.py`, `tests/test_mdstatistics.py`.
