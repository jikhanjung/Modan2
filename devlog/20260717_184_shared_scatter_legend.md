# 184 — Shared `build_scatter_legend`, applied in both dialogs (Batch C item 2)

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 2, rescoped — final step)
**Related:** `devlog/20260717_181_...`, `183_...`

## What

Applied the shared `build_scatter_legend(ax, scatter_result, *, loc, ...)` helper
(added in 181) to the three duplicated legend-building blocks:
- `dataset_analysis_dialog.show_analysis_result` — ax2 (`loc="upper right"`) and
  ax3 (`loc="upper left"`);
- `data_exploration_dialog.show_analysis_result` — ax2 (`loc="upper right"`), which
  keeps its extra `add_artist` / bbox post-processing around the returned legend.

Each ~11-line block collapses to a single call.

## Behavior preservation

Behavior-preserving. The helper skips groups whose key starts with `"_"`. The
exploration copy previously wrote `if key[0] == "_" or key == ""`; the `or key == ""`
was **dead** (`key[0]` on an empty string raises `IndexError` before that clause is
reached), so folding it to `key[0] == "_"` changes nothing observable — both keep the
same behavior (skip `_`-prefixed keys; still raise on a genuinely empty key, which
group names never are here).

## Coverage

Both edited plotting bodies are now exercised end-to-end with `show_legend=True`:
- `dataset_analysis` via the 183 smoke test (2D + 3D);
- `data_exploration` via a new `test_show_analysis_result_runs_with_legend` added to
  the exploration test file (reuses the golden fixture).

## Verification

- `ruff check` + `ruff format --check` — clean.
- `pytest tests/dialogs/ tests/test_multi_analysis_workflow.py
  tests/test_integration_workflows.py tests/test_analysis_info_widget.py`
  — 259 passed.

## Item 2 status — done (rescoped)

Item 2 is complete as rescoped: shared `build_scatter_group` factory (181/182) and
`build_scatter_legend` (184), guarded by unit tests + the exploration golden + the
analysis smoke test. The monolithic "shared builder" in the original TODO was
deliberately **not** built — see 181 for the rationale (divergent data sources,
output structures, and colour/centroid semantics). `TODOs.md` updated accordingly.

## Next

Remaining Batch C item 1 god-methods (`Modan2.py read_settings`, dialog `__init__`s),
or items 3–4 (dialog DB/file I/O → controller; `read_settings`/color-marker →
BaseDialog). Next devlog: **185**.
