# 181 — Shared `build_scatter_group` factory (Batch C item 2, rescoped)

**Date:** 2026-07-17
**Type:** implementation (NNN)
**Batch:** C — structural refactor (item 2, shared scatter builder — **rescoped**)
**Related:** `devlog/20260717_180_...`, `HANDOFF.md`, `TODOs.md`

## Item 2 rescope (important)

`TODOs.md` framed item 2 as "extract a shared scatter-plot builder — hundreds of
near-identical lines" between `data_exploration_dialog` and
`dataset_analysis_dialog`. Inspecting the actual code, that framing is **overstated**:

- `prepare_scatter_data` (exploration) vs the scatter section of
  `show_analysis_result` (dataset analysis) differ in **data source** (JSON
  `object_info_list` dicts vs `ds_ops.object_list` MdObjects), **output structures**
  (exploration builds scatter + regression + average_shape + data_range; analysis
  builds scatter_data only, plus a `__selected__` group), **centroid handling**
  (`obj["csize"]` / sentinel `9999` vs `get_centroid_size()` / sentinel `10`), and
  **colour-assignment semantics** (`enumerate` index vs a separate counter that
  only advances on assignment).
- The two `show_analysis_result` plotting methods overlap only in a ~20-line basic
  scatter loop + legend block; exploration additionally does regression curves,
  average-shape markers, convex hull, ellipse; analysis additionally does 3D.

A single monolithic builder would be a flag-heavy leaky abstraction across two
different data models. So item 2 is rescoped to the genuinely-shared, low-risk
seams: a **scatter-group dict factory** (this commit) and a **legend builder**
(follow-up).

## What

- New `dialogs/scatter_utils.py` with `build_scatter_group(...)` (and
  `build_scatter_legend(...)` for the follow-up commit).
- `build_scatter_group` replaces the repeated group-dict literal
  (`{"x_val": [], "y_val": [], ...}`), parameterized over size / property / symbol /
  colour, `meta` (include `hoverinfo`/`text` for seeded default/selected groups),
  and `empty` (scalar `0` init for the average-shape default seed).
- Applied at all six seed sites in `data_exploration_dialog`'s
  `_init_scatter_containers` / `_populate_scatter_groups`.
- Added `tests/dialogs/test_scatter_utils.py` (5 unit tests, incl. an aliasing
  guard that x/y/z lists are independent objects).

## Behavior preservation

Verified by the 179 golden-master (green before and after) plus the new unit tests.

## Verification

- `ruff check` + `ruff format` — clean.
- `pytest tests/dialogs/test_scatter_utils.py
  tests/dialogs/test_data_exploration_scatter.py` — 7 passed.

## Next

- **182**: apply `build_scatter_group` to `dataset_analysis_dialog`'s scatter seeds.
- **183**: apply `build_scatter_legend` to the 3 legend blocks (exploration ax2,
  analysis ax2/ax3). Next devlog: **182**.
