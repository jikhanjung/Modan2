"""Shared helpers for scatter-plot data construction.

Both ``DataExplorationDialog`` and ``DatasetAnalysisDialog`` build the same
per-group scatter dict structure and the same legend-from-scatter_result block.
These small factories deduplicate those literals without forcing a single
monolithic builder (the two dialogs' data sources, output structures, and feature
sets differ too much for that — see devlog 181).
"""


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
        if key[0] == "_":
            continue
        keys.append(key)
        values.append(scatter_result[key])
    return ax.legend(values, keys, loc=loc, bbox_to_anchor=bbox_to_anchor)
