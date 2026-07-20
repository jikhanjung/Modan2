# 212 — Fix circular import introduced by the legend-italics change

**Date:** 2026-07-20
**Type:** implementation (NNN) — regression fix
**Related:** `devlog/20260720_210_legend_italic_markup.md`

## What broke

Devlog 210 added a module-level `from dialogs.scatter_utils import …` to
`components/widgets/analysis_info.py`. That closes a cycle:

```
components.widgets/__init__  ->  analysis_info  ->  dialogs/__init__  ->  components.widgets
                                                                          (partially initialised)
```

so importing `ModanComponents`, `components.widgets` or `components.viewers`
first raised:

```
ImportError: cannot import name 'DatasetOpsViewer' from partially initialized
module 'components.widgets' (most likely due to a circular import)
```

Commit `ff4398e` shipped with this.

## Why the suite missed it

Import cycles are order-dependent and `sys.modules` is process-global. By the
time any test reached `import ModanComponents`, an earlier test had already
imported `dialogs`, so the cached module satisfied the import and nothing failed.
**1294 tests passed over a broken import graph.** It only surfaced when a script
imported `ModanComponents` as the very first thing.

## Fix

Moved the import into the function that uses it — the idiom this codebase
already uses for circular-import avoidance (and which `TODOs.md` explicitly
flags as intentional in some places). `scatter_utils` has no heavy dependencies,
so the per-call cost is a dict lookup after the first import.

## Regression net

`tests/test_import_cycles.py` imports each top-level entry point in a **fresh
subprocess**, which is the only way to catch this class of bug — in-process the
module cache hides it. Verified the test actually fails when the module-level
import is restored: 3 failed (`ModanComponents`, `components.widgets`,
`components.viewers`), 6 passed.

## Verification

- `tests/test_import_cycles.py` — 9 entry points, all import standalone.
- `ModanComponents`, `components.widgets`, `dialogs`, `Modan2` each import
  cleanly in a bare interpreter.
- Full suite: **1335 passed, 75 skipped**.

## Takeaway

A green suite does not prove the import graph is sound. Any new cross-package
import between `components/` and `dialogs/` should be assumed circular until a
fresh-interpreter import says otherwise — `tests/test_import_cycles.py` now
does that automatically.
