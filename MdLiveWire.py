"""Live-wire (intelligent scissors) curve auto-detection.

When tracing a semi-landmark curve over an image, clicking every point by hand is
tedious. Live-wire lets the user click a seed point and then have the trace
*snap* to the strongest image edge on the way to the cursor: the path that costs
least to travel, where travelling along a high-gradient boundary is cheap and
crossing a flat region is expensive (Mortensen & Barrett 1995, "Intelligent
Scissors for Image Composition").

The module is split so each half is independently testable:

* :func:`compute_cost_field` turns a grayscale image into a per-pixel traversal
  cost that is *low* on edges (high image gradient) and *high* on flat areas.
* :class:`LiveWire` builds a grid graph from a cost field and answers repeated
  shortest-path queries from one seed to many cursor positions cheaply -- one
  Dijkstra pass per seed, then O(path length) back-traces as the mouse moves.

:func:`build_livewire` ties them together and, for large images, works on a
downscaled cost field while exposing full-resolution ``(x, y)`` coordinates.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

# Cost is kept strictly positive so Dijkstra edge weights never hit zero (a zero
# edge would let a path wander along an edge for free and pick an arbitrary
# route among equal-cost ones).
_MIN_COST = 1e-3

# Neighbour offsets as (dx, dy, distance): 4-orthogonal at unit distance and
# 4-diagonal at sqrt(2), so diagonal moves are not unfairly cheap.
_SQRT2 = float(np.sqrt(2.0))
_NEIGHBOURS = [
    (1, 0, 1.0),
    (-1, 0, 1.0),
    (0, 1, 1.0),
    (0, -1, 1.0),
    (1, 1, _SQRT2),
    (1, -1, _SQRT2),
    (-1, 1, _SQRT2),
    (-1, -1, _SQRT2),
]


def _sobel_gradient(arr):
    """Sobel gradient components ``(gx, gy)`` and their magnitude."""
    gx = ndimage.sobel(arr, axis=1, mode="nearest")
    gy = ndimage.sobel(arr, axis=0, mode="nearest")
    return gx, gy, np.hypot(gx, gy)


def compute_cost_field(gray, return_gradient=False):
    """Per-pixel traversal cost from a grayscale image (low on edges).

    Args:
        gray: 2D array-like of image intensities (any numeric dtype).
        return_gradient: also return the Sobel gradient components ``(gx, gy)``,
            which the direction term needs to keep a trace running *along* an edge.

    Returns:
        ``float64`` cost array, same shape as ``gray``, in ``[_MIN_COST, 1]``:
        pixels on a strong edge get costs near ``_MIN_COST``, flat regions near
        ``1``. If ``return_gradient`` is set, returns ``(cost, gx, gy)``.

    Raises:
        ValueError: if ``gray`` is not two-dimensional.
    """
    arr = np.asarray(gray, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("gray must be a 2D image")
    if arr.size == 0:
        return (arr.copy(), arr.copy(), arr.copy()) if return_gradient else arr.copy()

    gx, gy, magnitude = _sobel_gradient(arr)
    peak = magnitude.max()
    if peak <= 0:
        # No gradient anywhere (a flat image): every pixel is equally costly.
        cost = np.ones_like(arr)
    else:
        strength = magnitude / peak  # 1 on the strongest edge, 0 on flat areas.
        cost = np.clip(1.0 - strength, _MIN_COST, 1.0)
    return (cost, gx, gy) if return_gradient else cost


class LiveWire:
    """Shortest-path snapping over a fixed cost field.

    Coordinates are ``(x, y)`` with ``x`` the column and ``y`` the row, matching
    image/screen conventions. A single seed drives many cursor queries, so
    :meth:`set_seed` does the expensive Dijkstra pass and :meth:`path_to` is a
    cheap back-trace reused on every mouse move.
    """

    # Blend of the two edge-cost terms. The magnitude term pulls the path onto
    # strong edges; the direction term keeps it running *along* the edge instead
    # of cutting across, which is what lets a gently curved outline be traced
    # from just its endpoints (Mortensen & Barrett use ~0.43 / 0.14 alongside a
    # Laplacian term we omit; without it these two are renormalised).
    _W_MAGNITUDE = 0.6
    _W_DIRECTION = 0.4
    # How many seed predecessor trees to keep (one per curve anchor is plenty).
    _SEED_CACHE_CAP = 16

    def __init__(self, cost, scale=1.0, gradient=None):
        """Build the traversal graph once from ``cost``.

        Args:
            cost: 2D cost field (e.g. from :func:`compute_cost_field`).
            scale: full-resolution pixels per cost-field pixel. Public
                coordinates are full-resolution; internally divided by ``scale``
                to index ``cost`` and multiplied back on output. ``1.0`` means
                the cost field is already full resolution.
            gradient: optional ``(gx, gy)`` Sobel components matching ``cost``'s
                shape. When given, a gradient-direction term is added so the path
                follows the edge tangent smoothly. Omit for magnitude-only.
        """
        self.cost = np.asarray(cost, dtype=np.float64)
        if self.cost.ndim != 2:
            raise ValueError("cost must be a 2D field")
        self.height, self.width = self.cost.shape
        self.scale = float(scale)
        self._edge_dir = self._unit_edge_direction(gradient)
        self._graph = self._build_graph()
        self._seed_index = None
        self._predecessors = None
        # Predecessor trees keyed by seed pixel index. Dragging one anchor of a
        # multi-anchor curve re-snaps the segments to its fixed neighbours every
        # mouse move; caching those neighbours' trees turns all but the first
        # move into cheap back-traces instead of a fresh Dijkstra each time.
        self._pred_cache = {}

    # -- graph construction -------------------------------------------------- #
    def _unit_edge_direction(self, gradient):
        """Per-pixel unit vector *along* the edge (perpendicular to the gradient).

        Returns ``(dirx, diry)`` flattened, or ``None`` when no gradient is given.
        """
        if gradient is None:
            return None
        gx, gy = (np.asarray(g, dtype=np.float64) for g in gradient)
        if gx.shape != self.cost.shape or gy.shape != self.cost.shape:
            raise ValueError("gradient components must match the cost field shape")
        mag = np.hypot(gx, gy)
        safe = mag > 0
        # Edge tangent = gradient rotated 90 degrees: (gy, -gx), normalised.
        dirx = np.where(safe, gy / np.where(safe, mag, 1.0), 0.0)
        diry = np.where(safe, -gx / np.where(safe, mag, 1.0), 0.0)
        return dirx.reshape(-1), diry.reshape(-1)

    def _direction_cost(self, src, dst, lx, ly):
        """Mortensen-Barrett link direction feature f_D in ``[0, 1]`` per edge.

        ``0`` when the link aligns with the edge tangent at both endpoints (travel
        along the edge), rising toward ``1`` as the link turns across it. ``lx/ly``
        is the unit link direction from src to dst.
        """
        dirx, diry = self._edge_dir
        dp_signed = dirx[src] * lx + diry[src] * ly
        sign = np.where(dp_signed >= 0, 1.0, -1.0)
        dp = np.abs(dp_signed)  # link oriented so this endpoint's dot is >= 0
        dq = sign * (dirx[dst] * lx + diry[dst] * ly)
        feat = (np.arccos(np.clip(dp, -1.0, 1.0)) + np.arccos(np.clip(dq, -1.0, 1.0))) / np.pi
        return feat

    def _build_graph(self):
        """Directed 8-connected grid graph; edge weight blends magnitude + direction."""
        h, w = self.height, self.width
        n = h * w
        cost_flat = self.cost.reshape(-1)
        yy, xx = np.mgrid[0:h, 0:w]
        xx = xx.reshape(-1)
        yy = yy.reshape(-1)
        src_all = []
        dst_all = []
        wgt_all = []
        for dx, dy, dist in _NEIGHBOURS:
            nx = xx + dx
            ny = yy + dy
            valid = (nx >= 0) & (nx < w) & (ny >= 0) & (ny < h)
            src = (yy[valid] * w + xx[valid]).astype(np.int64)
            dst = (ny[valid] * w + nx[valid]).astype(np.int64)
            # Magnitude term: cost of stepping onto the destination pixel.
            local = cost_flat[dst]
            if self._edge_dir is not None:
                inv_dist = 1.0 / dist
                fdir = self._direction_cost(src, dst, dx * inv_dist, dy * inv_dist)
                local = self._W_MAGNITUDE * local + self._W_DIRECTION * fdir
            # Scale by move length so diagonal steps are not unfairly cheap.
            wgt = local * dist
            src_all.append(src)
            dst_all.append(dst)
            wgt_all.append(wgt)
        src = np.concatenate(src_all)
        dst = np.concatenate(dst_all)
        wgt = np.concatenate(wgt_all)
        return csr_matrix((wgt, (src, dst)), shape=(n, n))

    # -- coordinate helpers -------------------------------------------------- #
    def _clamp(self, x, y):
        """Full-res ``(x, y)`` -> in-bounds cost-field integer ``(cx, cy)``."""
        cx = int(round(x / self.scale))
        cy = int(round(y / self.scale))
        cx = min(max(cx, 0), self.width - 1)
        cy = min(max(cy, 0), self.height - 1)
        return cx, cy

    def _to_full(self, cx, cy):
        """Cost-field ``(cx, cy)`` -> full-resolution ``(x, y)``."""
        if self.scale == 1.0:
            return [int(cx), int(cy)]
        return [int(round(cx * self.scale)), int(round(cy * self.scale))]

    # -- queries ------------------------------------------------------------- #
    def set_seed(self, seed):
        """Run Dijkstra from ``seed`` (full-res ``(x, y)``); cache predecessors."""
        cx, cy = self._clamp(seed[0], seed[1])
        index = cy * self.width + cx
        if index == self._seed_index and self._predecessors is not None:
            return
        predecessors = self._pred_cache.get(index)
        if predecessors is None:
            _dist, predecessors = dijkstra(self._graph, directed=True, indices=index, return_predecessors=True)
            self._pred_cache[index] = predecessors
            if len(self._pred_cache) > self._SEED_CACHE_CAP:
                # dict preserves insertion order -> drop the oldest seed.
                self._pred_cache.pop(next(iter(self._pred_cache)))
        self._seed_index = index
        self._predecessors = predecessors

    def path_to(self, target):
        """Least-cost path seed -> ``target`` as full-res ``[[x, y], ...]``.

        Includes both endpoints. Falls back to a straight two-point segment if no
        seed is set or the target is unreachable. Call :meth:`set_seed` first.
        """
        cx, cy = self._clamp(target[0], target[1])
        if self._predecessors is None:
            return [self._to_full(cx, cy)]
        target_index = cy * self.width + cx
        chain = [target_index]
        guard = self.height * self.width + 1
        node = target_index
        while node != self._seed_index:
            node = int(self._predecessors[node])
            if node < 0 or len(chain) > guard:
                # Unreachable (disconnected) -- straight segment as a safe default.
                seed_pt = self._to_full(self._seed_index % self.width, self._seed_index // self.width)
                return [seed_pt, self._to_full(cx, cy)]
            chain.append(node)
        chain.reverse()
        return [self._to_full(idx % self.width, idx // self.width) for idx in chain]

    def find_path(self, seed, target):
        """Convenience: :meth:`set_seed` then :meth:`path_to` in one call."""
        self.set_seed(seed)
        return self.path_to(target)


def build_livewire(gray, max_dim=1024):
    """Build a :class:`LiveWire` from a grayscale image, downscaling if large.

    Args:
        gray: 2D grayscale image array.
        max_dim: cap on the cost field's longer side. Images above this are
            downsampled by an integer factor so the graph stays tractable; the
            returned live-wire still speaks full-resolution ``(x, y)``.

    Returns:
        A :class:`LiveWire`, or ``None`` if ``gray`` is empty / not 2D.
    """
    arr = np.asarray(gray)
    if arr.ndim != 2 or arr.size == 0:
        return None

    scale = 1.0
    longer = max(arr.shape)
    if max_dim and longer > max_dim:
        factor = int(np.ceil(longer / max_dim))
        arr = arr[::factor, ::factor]
        scale = float(factor)

    cost, gx, gy = compute_cost_field(arr, return_gradient=True)
    return LiveWire(cost, scale=scale, gradient=(gx, gy))
