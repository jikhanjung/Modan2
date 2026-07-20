# 210 — Italicise `*...*` spans in scatter legends

**Date:** 2026-07-20
**Type:** implementation (NNN) — feature

## What

Grouping-variable values wrapped in asterisks now render italic in plot legends,
so taxon names can be typeset correctly: `*Eurekia*` → *Eurekia*.

## Approach

Two rendering paths, picked per label — this split is the substance of the
change, not an implementation detail:

| label | handling | why |
|---|---|---|
| `*Eurekia*` (whole label wrapped) | strip the asterisks, `Text.set_fontstyle("italic")` | avoids mathtext entirely, so **any script renders** — mathtext cannot typeset Hangul, and `*유레키아*` is a plausible group value here |
| `*Eurekia* sp.` (partial span) | rewrite the span as `$\mathit{...}$` | only part of the label is italic, which `fontstyle` cannot express |
| `Group *`, `**` | left verbatim | an unmatched asterisk is literal text |

The mathtext path escapes the characters mathtext treats specially
(`_ ^ $ { } # % & ~ \`) and, critically, spaces — `\ ` — otherwise
`*Eurekia bella*` would render as `Eurekiabella`.

## API

`dialogs/scatter_utils.py`:

- `format_legend_label(label) -> (text, italic)` — pure, testable.
- `apply_legend_italics(legend, labels) -> legend` — sets `fontstyle` on the
  legend `Text` objects whose source label was fully wrapped. Takes the
  **original** labels, in legend order.

## Call sites

All four legend constructions were updated — the shared builder plus the three
that bypass it:

- `dialogs/scatter_utils.py` `build_scatter_legend` (covers DataExploration +
  DatasetAnalysis, 3 of the call sites)
- `dialogs/data_exploration_dialog.py:~2117` — regression-curve legend
- `components/widgets/analysis_info.py:~602` — 3D analysis-result legend

## Verification

- `tests/test_legend_italics.py` (new, 14 tests): full/partial/absent spans,
  multi-span, non-ASCII, mathtext escaping, lone asterisk, non-string
  passthrough, and `apply_legend_italics` selectivity.
- Real matplotlib render (`fig.canvas.draw()`) over all cases — mathtext syntax
  errors only surface at draw time, so a parse-free unit test would not have
  caught them. Confirmed `*유레키아*` → `유레키아` with `fontstyle=italic` and no
  `$` wrapper.
- Full suite: **1273 passed, 75 skipped**.

## Known limitation

A label mixing a partial `*...*` span with a pre-existing literal `$` could have
its dollar signs pair up wrongly inside mathtext. Not worth guarding until such
a label actually appears.
