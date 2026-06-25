# Cleanup — Remove Unused Modules, Stale Build Specs; Fix Entry-Point Docs

**Date**: 2026-06-25
**Type**: Implementation log
**Trigger**: Audit of which root-level files are actually used (the real entry point is `main.py`, not `Modan2.py`).
**Follows**: [172 tr() i18n placeholders](20260625_172_tr_i18n_placeholders.md)

---

## Background — entry point clarification

`main.py` is the real application entry point (`python main.py`; also what
`build.py` packages and what `fix_qt_import.py` launches via `import main`).
`Modan2.py` has **no `__main__` block** and never constructs a `QApplication` — it
only defines `ModanMainWindow`, which `main.py` imports. So `Modan2.py` is a live
module (not dead), but `python Modan2.py` does nothing; the old CLAUDE.md
instruction was stale.

## Audit method

For every root-level `.py`, counted imports across the codebase (excluding self and
tests) and cross-checked test references and git history. Six modules had **zero**
runtime and zero test references; the standalone scripts that legitimately have no
importers (`build.py`, `setup.py`, `manage_version.py`, `fix_qt_import.py`,
`migrate.py`) were confirmed as entry points/utilities and kept.

## Removed — dead modules (6)

| File | Why it was dead |
|---|---|
| `modan_convert.py` | One-off DB converter that `import MdModel1` — **a module that does not exist**, so the script raised `ImportError` on the first line. |
| `MdLogger.py` | Superseded by the logging consolidation (per-module `getLogger`); imported nowhere. |
| `version_utils.py` | Version-validation helpers imported nowhere (`manage_version.py` parses `version.py` directly). |
| `debug_landmark.py` | One-off debug script (`sys.path.insert` + dump landmarks). |
| `extract_components.py` | One-time Phase-5 refactor automation (split `ModanComponents.py`); job long done. |
| `manova_test.py` | Scratch experiment running MANOVA on the sklearn iris dataset. |

The only repo references were in `.index/` (stale search index), generated
`modan2_code_visualization.html`, devlogs, and `pyproject.toml` ruff
per-file-ignore stanzas (lint config, not usage). The two obsolete `pyproject.toml`
ignore lines (`MdLogger.py`, `modan_convert.py`) were removed.

## Removed — stale PyInstaller specs (8)

`build.py` generates its own spec targeting `main.py` and references no `.spec`
file, so all committed/leftover specs pointing at `Modan2.py` were obsolete:

- Tracked in git (1): `Modan2_v0.1.2.exe.spec` → `git rm`.
- Gitignored local artifacts (7): `Modan2.spec`,
  `Modan2_v0.1.3_{20240611,20240617,20240708,20250113,20250120,20250121}.exe.spec`
  → removed from disk.

## Docs

`CLAUDE.md`: replaced the four `python Modan2.py` references with `python main.py`
and noted that `Modan2.py` is an imported module, not a runnable script.

## Verification

- `python -c "import main; import Modan2"` loads cleanly.
- None of the removed files were imported by any runtime or test module (verified
  by grep + AST before removal).
- Full test suite green, ruff clean.

## Files changed
Deleted: `MdLogger.py`, `version_utils.py`, `debug_landmark.py`,
`extract_components.py`, `manova_test.py`, `modan_convert.py`, and 8 `.spec`
files. Modified: `CLAUDE.md`, `pyproject.toml`.
