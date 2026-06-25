# Refactor — Exception Chaining (`raise ... from e`)

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 MEDIUM "Broad except → sentinel/ValueError rewrap (loses traceback); missing `raise ... from e`"
**Follows**: [168 remove locals() control flow](20260625_168_remove_locals_control_flow.md)

---

## Summary

Several `except` handlers re-raised a `ValueError` without `from e`, so Python's
implicit-chaining note ("During handling of the above exception, another exception
occurred") was the only link to the original error and the rewrapped traceback
started at the `raise`, hiding where the failure actually happened. Added explicit
`from e` to chain the cause.

Found via AST (every `raise <Call>` inside an `except` with `cause is None`):
- `ModanController.py` — 6 sites (import/PCA/CVA/MANOVA failure rewraps)
- `MdUtils.py` — 10 sites (TPS/NTS/PLY/OBJ/STL parse & export rewraps)

`MdStatistics.py` and `MdModel.py` already chained correctly (0 missing).

---

## Changes

All 16 sites now read e.g.:

```python
except Exception as e:
    raise ValueError(f"PCA analysis failed: {str(e)}") from e
```

Two handlers in `MdUtils.py` (the malformed-TPS-`LM`-line and malformed-NTS-header
cases) caught `(ValueError, IndexError)` **without binding** the exception; they
were changed to `except (ValueError, IndexError) as e:` so the original parse error
can be chained.

No exception **types** changed (still `ValueError`), only `__cause__` is now set —
so `pytest.raises(ValueError)` assertions are unaffected. The user-facing message
text is unchanged.

## Tests

No new tests — this is a debuggability improvement, not a behavior change.
`test_mdutils.py`, `test_import.py`, `test_controller.py`, and
`test_error_recovery_workflow.py` (which exercise these error paths) pass
unchanged. Full suite green, ruff clean.

## Files changed
`ModanController.py`, `MdUtils.py`.
