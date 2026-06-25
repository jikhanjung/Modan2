# Latent Bug Fixes — Regex Double-Escape, `is_numeric(None)`, `utcnow()`

**Date**: 2026-06-25
**Type**: Implementation log
**Addresses**: R01 MEDIUM "Confirmed dead code / latent bugs" (three small, independent defects)
**Follows**: [166 MANOVA silent truncation](20260625_166_manova_silent_truncation.md)

---

## Summary

Three small latent bugs flagged by R01, grouped into one change. None changes
runtime behavior of currently-exercised paths in a risky way; each is a
correctness fix with a regression test.

---

## 1. `MdConstants.REGEX_PATTERNS` — double-backslash in raw strings

```python
# Before (raw strings -> a LITERAL backslash followed by the next char)
"file_extension": r"\\.([a-zA-Z0-9]+)$",
"number":         r"^[+-]?\\d*\\.?\\d+$",
# After
"file_extension": r"\.([a-zA-Z0-9]+)$",
"number":         r"^[+-]?\d*\.?\d+$",
```

In a raw string `r"\\d"` is two characters `\` `\` then `d`, so the regex engine
saw `\\` (a literal backslash) instead of the intended `\d`/`\.`/`\s` classes —
the patterns could never match normal input. Four of the seven entries had this
(the other three already used single backslashes, confirming a copy-paste slip).

`REGEX_PATTERNS` is currently **unused** anywhere in the codebase, so this was a
latent bug — fixed (rather than deleted) because the dict is clearly intended as a
reusable validation resource, and a test now locks the patterns to their intent.

## 2. `MdUtils.is_numeric(None)` raised `TypeError`

```python
try:
    float(value)
    return True
except (ValueError, TypeError):   # was: except ValueError
    return False
```

`float("abc")` raises `ValueError` (handled), but `float(None)` /
`float([1, 2])` raise `TypeError`, which escaped the function. `is_numeric` is a
predicate and should return `False` for non-numeric input of any type, not raise.

## 3. `MdUtils` — `datetime.utcnow()` deprecated (3.12+)

```python
# Before
"export_date": datetime.utcnow().isoformat() + "Z",
# After (from datetime import UTC, datetime)
"export_date": datetime.now(UTC).replace(tzinfo=None).isoformat() + "Z",
```

`datetime.utcnow()` is deprecated and slated for removal. `datetime.now(UTC)` is
the timezone-aware replacement; `.replace(tzinfo=None)` keeps the exact previous
output shape (naive ISO string + explicit `"Z"` suffix), so the serialized
`export_date` format is unchanged.

## Tests
- `test_mdutils.py::test_is_numeric` — added `is_numeric(None)` and
  `is_numeric([1, 2])` → both `False`.
- `test_mdconstants.py::TestRegexPatterns` (new) — asserts each pattern matches
  intended inputs (`scan.obj` → ext `obj`, `"1.5  -2.0"` landmark line, signed
  numbers/integers) and rejects invalid ones; all would fail under the old `\\`.

## Files changed
`MdConstants.py`, `MdUtils.py`, `tests/test_mdconstants.py`, `tests/test_mdutils.py`.
