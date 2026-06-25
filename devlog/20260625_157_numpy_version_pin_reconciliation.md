# numpy Version Pin Reconciliation

**Date**: 2026-06-25
**Type**: Implementation log
**Follows**: [156 Viewer Constants Dedup](20260625_156_viewer_constants_dedup.md)

---

## Summary

Resolved the numpy version-spec inconsistency flagged across earlier devlogs: the
runtime/venv uses numpy **2.5.0** and the project officially supports
`numpy>2.0.0` (CLAUDE.md, `requirements.txt`), but `Modan2_env.txt` still pinned
`numpy==1.26`. Reconciled all specs and confirmed the code is numpy-2.x clean.

This is a config-only change (no source changes). The full suite already passes
on numpy 2.5.0 (1181 passed), so no behavior is affected.

---

## Before

| File | numpy spec |
|---|---|
| `requirements.txt` | `numpy>=2.0.0` (no upper bound) |
| `requirements_win.txt` | `numpy<3.0.0` (no lower bound) |
| `Modan2_env.txt` | `numpy==1.26` (stale, 2 places) |
| installed (venv) | `2.5.0` |
| CLAUDE.md | "numpy>2.0.0 is now supported" |

## After

| File | numpy spec |
|---|---|
| `requirements.txt` | `numpy>=2.0.0,<3.0.0` |
| `requirements_win.txt` | `numpy>=2.0.0,<3.0.0` |
| `Modan2_env.txt` | `numpy>=2.0.0` (both the package line and the `pip install` note) |

- The two strict requirements files now carry the same lower **and** upper bound
  (`>=2.0.0,<3.0.0`) — consistent, and guards against an untested numpy 3.0.
- `Modan2_env.txt` is setup notes (a conda/pip command list); kept as
  `numpy>=2.0.0` to avoid the `<` shell-redirection trap in its `pip install`
  line. The important fix there was dropping the `==1.26` pin.
- Validated with `packaging.SpecifierSet`: 2.5.0 satisfies both specs.

## numpy 2.x compatibility audit

The earlier `get_ellipse_params` `eig`→`eigh` fix ([152]) was one numpy-2.x
incompatibility. Before bumping the floor to 2.0, swept the codebase for other
removed/changed numpy 2.0 APIs:

- `np.float_/int_/complex_/bool_/NaN/infty/in1d/row_stack/alltrue/product/
  trapz/cast/source/lookfor/...` — **none found**
- bare removed aliases `np.float/np.int/np.bool/np.object/np.str` — **none found**
- `np.matrix`, `.ptp(...)`, `np.array(..., copy=False)` — **none found**

The codebase is clean for numpy 2.x; the full test suite passes on 2.5.0.

## Files changed
`requirements.txt`, `requirements_win.txt`, `Modan2_env.txt` (config only).

## Next candidates
1. DB correctness items from R01: C1 (controller `.create()` field names),
   C2 (class-level mutable list attrs), C4 (missing `atomic()` transactions).
2. The duplicated analysis-mode / `COLOR` constants still living in
   `data_exploration_dialog.py` / `dataset_ops_viewer.py` (distinct variants —
   only worth touching if a shared definition is genuinely desired).
