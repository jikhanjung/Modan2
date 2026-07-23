"""Tests for live-wire (intelligent scissors) curve auto-detection (MdLiveWire).

Covers the cost field (low on edges) and the shortest-path snapping that routes a
trace along the cheapest -- i.e. strongest-edge -- channel between two points.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdLiveWire as lw

# --------------------------------------------------------------------------- #
# Cost field
# --------------------------------------------------------------------------- #


class TestComputeCostField:
    def test_flat_image_is_uniform_cost(self):
        cost = lw.compute_cost_field(np.full((10, 10), 128.0))
        assert cost.shape == (10, 10)
        assert np.allclose(cost, 1.0)

    def test_edge_pixels_are_cheaper_than_flat(self):
        # A step edge: left half dark, right half bright.
        img = np.zeros((10, 20), dtype=float)
        img[:, 10:] = 255.0
        cost = lw.compute_cost_field(img)
        # The boundary column is far cheaper to travel than a flat interior one.
        boundary_cost = cost[:, 9:11].mean()
        flat_cost = cost[:, 0:3].mean()
        assert boundary_cost < flat_cost
        assert boundary_cost < 0.5

    def test_cost_stays_in_range(self):
        rng = np.random.default_rng(0)
        img = rng.uniform(0, 255, size=(30, 30))
        cost = lw.compute_cost_field(img)
        assert cost.min() >= lw._MIN_COST - 1e-9
        assert cost.max() <= 1.0 + 1e-9

    def test_non_2d_raises(self):
        with pytest.raises(ValueError):
            lw.compute_cost_field(np.zeros((3, 3, 3)))

    def test_empty_image(self):
        cost = lw.compute_cost_field(np.zeros((0, 0)))
        assert cost.size == 0


# --------------------------------------------------------------------------- #
# LiveWire shortest-path snapping
# --------------------------------------------------------------------------- #


def _channel_cost(h, w, channel_col):
    """A cost field with one cheap column (a strong vertical edge) amid costly flat."""
    cost = np.ones((h, w))
    cost[:, channel_col] = lw._MIN_COST
    return cost


class TestLiveWirePath:
    def test_path_endpoints_are_seed_and_target(self):
        wire = lw.LiveWire(np.ones((8, 8)))
        path = wire.find_path((0, 0), (7, 7))
        assert path[0] == [0, 0]
        assert path[-1] == [7, 7]

    def test_path_is_connected_by_single_steps(self):
        wire = lw.LiveWire(np.ones((8, 8)))
        path = wire.find_path((0, 0), (7, 5))
        for (x0, y0), (x1, y1) in zip(path, path[1:]):
            assert max(abs(x1 - x0), abs(y1 - y0)) == 1  # 8-connected neighbours

    def test_snaps_onto_the_cheap_channel(self):
        # Seed and target sit off the cheap column; the least-cost route should
        # detour onto it rather than cut straight across the costly flat field.
        cost = _channel_cost(20, 20, channel_col=10)
        wire = lw.LiveWire(cost)
        path = wire.find_path((10, 0), (10, 19))
        xs = [p[0] for p in path]
        # Every point rides the cheap column.
        assert all(x == 10 for x in xs)

    def test_detours_to_edge_when_cheaper_than_straight(self):
        cost = _channel_cost(30, 30, channel_col=5)
        wire = lw.LiveWire(cost)
        # From (0,0) to (0,29): straight down column 0 crosses 29 costly pixels;
        # detouring to the cheap column 5 and back is cheaper, so the path visits it.
        path = wire.find_path((0, 0), (0, 29))
        assert any(x == 5 for x, _y in path)

    def test_set_seed_reused_across_targets(self):
        cost = _channel_cost(15, 15, channel_col=7)
        wire = lw.LiveWire(cost)
        wire.set_seed((7, 0))
        p1 = wire.path_to((7, 14))
        p2 = wire.path_to((7, 10))
        assert p1[0] == [7, 0] and p2[0] == [7, 0]
        assert p1[-1] == [7, 14] and p2[-1] == [7, 10]

    def test_seed_cache_holds_multiple_seeds(self):
        cost = _channel_cost(15, 15, channel_col=7)
        wire = lw.LiveWire(cost)
        wire.set_seed((7, 0))
        wire.set_seed((7, 14))  # a different seed
        # Both predecessor trees are cached (drives fast live drag re-snap).
        assert 0 * wire.width + 7 in wire._pred_cache
        assert 14 * wire.width + 7 in wire._pred_cache

    def test_seed_cache_is_capped(self):
        wire = lw.LiveWire(np.ones((6, 6)))
        for x in range(wire._SEED_CACHE_CAP + 5):
            wire.set_seed((x % 6, x // 6))
        assert len(wire._pred_cache) <= wire._SEED_CACHE_CAP

    def test_path_without_seed_returns_target_only(self):
        wire = lw.LiveWire(np.ones((5, 5)))
        assert wire.path_to((3, 3)) == [[3, 3]]

    def test_target_out_of_bounds_is_clamped(self):
        wire = lw.LiveWire(np.ones((5, 5)))
        path = wire.find_path((0, 0), (100, 100))
        assert path[-1] == [4, 4]  # clamped to the last valid pixel

    def test_non_2d_cost_raises(self):
        with pytest.raises(ValueError):
            lw.LiveWire(np.ones((4, 4, 4)))


# --------------------------------------------------------------------------- #
# Downscaling factory
# --------------------------------------------------------------------------- #


class TestBuildLiveWire:
    def test_small_image_full_resolution(self):
        wire = lw.build_livewire(np.ones((10, 10)))
        assert wire is not None
        assert wire.scale == 1.0
        assert wire.cost.shape == (10, 10)

    def test_large_image_downscaled_but_full_res_coords(self):
        img = np.ones((3000, 3000))
        wire = lw.build_livewire(img, max_dim=1024)
        assert wire.scale > 1.0
        # Cost field shrank, yet queries and results use full-resolution coords.
        assert max(wire.cost.shape) <= 1024
        path = wire.find_path((0, 0), (2999, 2999))
        assert path[0] == [0, 0]
        assert path[-1][0] <= 2999 and path[-1][1] <= 2999

    def test_empty_or_bad_input_returns_none(self):
        assert lw.build_livewire(np.zeros((0, 0))) is None
        assert lw.build_livewire(np.zeros((4, 4, 3))) is None

    def test_downscaled_path_snaps_to_edge(self):
        # A bright vertical bar in a large image; the snapped path should hug it.
        img = np.zeros((2000, 2000))
        img[:, 1000:1010] = 255.0
        wire = lw.build_livewire(img, max_dim=500)
        path = wire.find_path((1005, 0), (1005, 1999))
        xs = [p[0] for p in path]
        # Stays close to the bar's edge (within the downscale factor's slack).
        assert all(abs(x - 1005) <= 2 * wire.scale for x in xs)


# --------------------------------------------------------------------------- #
# Curve following (the direction term at work)
# --------------------------------------------------------------------------- #


def _disk(h=120, w=120, cx=60, cy=60, r=45, noise=0.0, seed=0):
    yy, xx = np.mgrid[0:h, 0:w]
    img = ((xx - cx) ** 2 + (yy - cy) ** 2 <= r * r).astype(float) * 255.0
    if noise:
        img = np.clip(img + np.random.default_rng(seed).normal(0, noise, img.shape), 0, 255)
    return img


def _arc_deviation(path, cx, cy, r):
    """Mean |distance-from-centre - r| over a path -- 0 means it rode the circle."""
    return float(np.mean([abs(np.hypot(px - cx, py - cy) - r) for px, py in path]))


class TestCurveFollowing:
    def test_gradient_shape_mismatch_raises(self):
        with pytest.raises(ValueError):
            lw.LiveWire(np.ones((5, 5)), gradient=(np.ones((5, 5)), np.ones((4, 4))))

    def test_traces_a_curved_edge_from_endpoints_only(self):
        # A big circular outline: clicking just the top and bottom should follow
        # the arc, not cut a straight chord across the disk.
        wire = lw.build_livewire(_disk())
        path = wire.find_path((60, 15), (60, 105))  # top and bottom of the circle
        assert _arc_deviation(path, 60, 60, 45) < 2.0
        # It bulges out to one side (rides an arc) rather than staying on x=60.
        xs = [p[0] for p in path]
        assert max(xs) - min(xs) > 40

    def test_curve_following_survives_noise(self):
        wire = lw.build_livewire(_disk(noise=60.0))
        path = wire.find_path((60, 15), (60, 105))
        # Even with heavy noise the arc is still tracked to within a couple pixels.
        assert _arc_deviation(path, 60, 60, 45) < 3.0

    def test_midpoint_picks_the_intended_side(self):
        # The two endpoints alone are ambiguous (two arcs). A midpoint on the left
        # arc forces the trace around the left side.
        wire = lw.build_livewire(_disk())
        left = wire.find_path((60, 15), (15, 60)) + wire.find_path((15, 60), (60, 105))
        assert all(x <= 62 for x, _y in left)  # stays on the left half
