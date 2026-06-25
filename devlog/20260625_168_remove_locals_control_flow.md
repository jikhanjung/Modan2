# Refactor — Remove `locals()`-Based Control Flow in `run_analysis`

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 MEDIUM "`locals()`-based control flow (worst smell)" (`ModanController.run_analysis`)
**Follows**: [167 latent bugs](20260625_167_latent_bugs_regex_isnumeric_utcnow.md)

---

## Summary

`run_analysis` used `"<name>" in locals()` three times to branch on whether a
variable had been assigned earlier in the same function:

```python
if "analysis_type" not in locals():
    analysis_type = "PCA"          # default for the new-signature path
...
if "cva_result" in locals() and cva_result:   # save section
...
if "manova_result" in locals() and manova_result:
```

Introspecting `locals()` to test "did an earlier branch set this name?" is fragile
(a rename or a moved assignment silently changes control flow) and obscures intent.
Replaced with explicit up-front initialization. Behavior is preserved exactly.

---

## Why the guards were load-bearing

`run_analysis` dispatches on `analysis_type`:

```python
if analysis_type.upper() == "PCA":      # comprehensive: sets cva_result/manova_result
    ...
elif analysis_type.upper() == "CVA":    # sets `result` only
    result = self._run_cva(...)
elif analysis_type.upper() == "MANOVA": # sets `result` only
    result = self._run_manova(...)
```

The shared save section afterward references `cva_result` / `manova_result`. On a
CVA-only or MANOVA-only run those names were **never assigned**, so the
`in locals()` checks were actually doing real work — not just style noise.

## The fix

- **`analysis_type`**: the old-signature branch already sets it from the string
  argument; the new-signature (`else`) branch now sets `analysis_type = "PCA"`
  explicitly (the new UI path is always the comprehensive PCA run). The
  `if "analysis_type" not in locals()` block is gone.
- **`cva_result` / `manova_result`**: initialized to `None` **before** the
  `if/elif/else` dispatch instead of only inside the PCA branch. The save section
  now reads `if cva_result:` / `if manova_result:`. For CVA-/MANOVA-only runs they
  stay `None`, so those save blocks are skipped exactly as before.

No behavioral change: every previously-reachable path assigns the same values and
takes the same save branches.

## Tests

No new tests needed — the existing analysis suites
(`test_controller.py`, `test_analysis_workflow.py`,
`test_multi_analysis_workflow.py`) exercise the PCA-comprehensive, CVA-only, and
MANOVA-only paths and all pass unchanged. Full suite green, ruff clean.

## Files changed
`ModanController.py`.
