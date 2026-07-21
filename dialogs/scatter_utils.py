"""Shared helpers for scatter-plot data construction.

Both ``DataExplorationDialog`` and ``DatasetAnalysisDialog`` build the same
per-group scatter dict structure and the same legend-from-scatter_result block.
These small factories deduplicate those literals without forcing a single
monolithic builder (the two dialogs' data sources, output structures, and feature
sets differ too much for that — see devlog 181).
"""

import re

# A ``*...*`` span marks text the user wants italicised (taxon names, e.g.
# ``*Eurekia*``). ``[^*]+`` keeps the match non-greedy across multiple spans and
# leaves an unmatched lone asterisk untouched.
_ITALIC_SPAN = re.compile(r"\*([^*]+)\*")
_FULL_ITALIC = re.compile(r"^\*([^*]+)\*$")

# Characters mathtext treats specially; a literal space must be escaped too or
# mathtext collapses it.
_MATHTEXT_ESCAPES = {
    "\\": r"\backslash ",
    "$": r"\$",
    "{": r"\{",
    "}": r"\}",
    "_": r"\_",
    "^": r"\^",
    "#": r"\#",
    "%": r"\%",
    "&": r"\&",
    "~": r"\sim ",
    " ": r"\ ",
}


def _escape_mathtext(text):
    return "".join(_MATHTEXT_ESCAPES.get(ch, ch) for ch in text)


def format_legend_label(label):
    """Translate ``*...*`` spans in a legend label into italics.

    Returns ``(text, italic)``:

    - **Whole label wrapped** (``*Eurekia*``) — asterisks stripped and
      ``italic=True``, so the caller sets ``fontstyle`` on the legend ``Text``.
      This path renders any script (Hangul included), which mathtext cannot.
    - **Partial spans** (``*Eurekia* sp.``) — the span is rewritten as mathtext
      and ``italic=False``, since only part of the label is italic.
    - **No span / lone asterisk** — returned unchanged with ``italic=False``.
    """
    if not isinstance(label, str) or "*" not in label:
        return label, False

    full = _FULL_ITALIC.match(label)
    if full and full.group(1).strip():
        return full.group(1), True

    def to_mathtext(match):
        inner = match.group(1).strip()
        if not inner:
            return match.group(0)
        return r"$\mathit{" + _escape_mathtext(inner) + r"}$"

    return _ITALIC_SPAN.sub(to_mathtext, label), False


def apply_legend_italics(legend, labels):
    """Italicise the legend entries whose source label was fully ``*``-wrapped.

    ``labels`` is the original (pre-``format_legend_label``) label sequence, in
    the same order the legend was built from.
    """
    texts = legend.get_texts()
    for text_obj, label in zip(texts, labels):
        if format_legend_label(label)[1]:
            text_obj.set_fontstyle("italic")
    return legend


def build_scatter_group(size, *, property_name="", symbol="", color="", meta=False, empty=None):
    """Return a fresh scatter/regression/average group dict.

    Args:
        size: marker size stored under ``"size"``.
        property_name: group label stored under ``"property"``.
        symbol: marker symbol (``""`` for auto-assign-later groups, ``"o"`` for
            seeded ``__default__``/``__selected__`` groups).
        color: marker colour (``""`` for auto-assign-later groups).
        meta: when True, include the ``hoverinfo``/``text`` lists carried by the
            seeded default/selected groups.
        empty: initial value for ``x_val``/``y_val``/``z_val``. ``None`` (default)
            seeds a fresh empty list for each; pass ``0`` for the average-shape
            default seed, which starts scalar.
    """

    def fresh():
        # A new list per axis when empty is None so the three don't alias.
        return [] if empty is None else empty

    group = {
        "x_val": fresh(),
        "y_val": fresh(),
        "z_val": fresh(),
        "data": [],
    }
    if meta:
        group["hoverinfo"] = []
        group["text"] = []
    group["property"] = property_name
    group["symbol"] = symbol
    group["color"] = color
    group["size"] = size
    return group


def build_scatter_legend(ax, scatter_result, *, loc, bbox_to_anchor=(1.05, 1)):
    """Build a legend from a ``scatter_result`` mapping, skipping internal groups.

    Groups whose key starts with ``"_"`` (``__default__``/``__selected__``) are
    omitted. Returns the matplotlib legend so callers can post-process it.
    """
    values = []
    keys = []
    for key in scatter_result.keys():
        if key.startswith("_"):
            continue
        keys.append(key)
        values.append(scatter_result[key])
    labels = [format_legend_label(key)[0] for key in keys]
    legend = ax.legend(values, labels, loc=loc, bbox_to_anchor=bbox_to_anchor)
    return apply_legend_italics(legend, keys)
