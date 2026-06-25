# Refactor — Use Module-Level Logger Instead of Per-Function Recreation

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 MEDIUM "Per-method `logger = getLogger(__name__)` recreation"
**Follows**: [170 range(len) → enumerate/zip](20260625_170_range_len_to_enumerate_zip.md)

---

## Summary

`MdUtils.py` and `MdModel.py` re-created the logger with
`logger = logging.getLogger(__name__)` **inside** many functions / except blocks
(15 in `MdUtils`, 12 in `MdModel`). `logging.getLogger(__name__)` always returns
the same singleton for a given module, so these local rebinds were pure
redundancy. Removed them in favor of one module-level logger.

- `MdModel.py` already had a module-level `logger` (line 22); removed the 12
  shadowing in-function copies.
- `MdUtils.py` had **no** module-level logger; added one after the imports and
  removed the 15 in-function copies.

---

## Method

Removed every **indented** `logger = logging.getLogger(__name__)` line (the
module-level definitions sit at column 0 and were preserved). Verified beforehand
that none of the removed lines was the sole statement in its block, so no empty
blocks resulted.

Behavior is identical: every `logger.xxx(...)` call now resolves to the
module-level logger, which is the same object the local rebinds produced.

## Tests

No new tests — pure redundancy removal. Module imports verified; `test_mdutils.py`,
`test_mdmodel.py`, `test_import.py` pass; full suite green, ruff clean.

## Files changed
`MdUtils.py`, `MdModel.py`.
