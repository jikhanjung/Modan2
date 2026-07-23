"""Property-based (fuzz) tests for the semi-landmark resampling core.

resample_polyline turns a traced curve into evenly-spaced semi-landmarks and is
on the analysis path for every curve dataset, so it must be robust to whatever a
trace throws at it. Hypothesis generates many random polylines / counts to check
the contract holds and nothing crashes on odd input (degenerate segments, huge
coordinate ranges, tiny curves). See docs/CODE_QUALITY_GUIDE.md §3.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

import MdUtils as mu

_coord = st.floats(min_value=-1e4, max_value=1e4, allow_nan=False, allow_infinity=False)
_point2d = st.lists(_coord, min_size=2, max_size=2)
_points = st.lists(_point2d, min_size=2, max_size=30)

_SETTINGS = settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])


@_SETTINGS
@given(points=_points, n=st.integers(min_value=2, max_value=50), closed=st.booleans())
def test_output_shape_is_always_n_finite_points(points, n, closed):
    out = mu.resample_polyline(points, n, closed=closed)
    assert isinstance(out, list)
    assert len(out) == n
    assert all(len(p) == 2 for p in out)
    assert all(np.isfinite(p).all() for p in out)


@_SETTINGS
@given(points=_points, n=st.integers(min_value=2, max_value=50))
def test_open_curve_preserves_endpoints(points, n):
    pts = np.asarray(points, dtype=float)
    total = np.sqrt((np.diff(pts, axis=0) ** 2).sum(axis=1)).sum()
    assume(total > 0)  # endpoints are only meaningful when the curve has length

    out = mu.resample_polyline(points, n, closed=False)
    assert out[0] == pytest.approx(points[0], abs=1e-4)
    assert out[-1] == pytest.approx(points[-1], abs=1e-4)


@given(points=_points, bad_n=st.integers(max_value=1))
def test_rejects_n_below_two(points, bad_n):
    with pytest.raises(ValueError):
        mu.resample_polyline(points, bad_n)


@given(n=st.integers(min_value=2, max_value=10))
def test_rejects_fewer_than_two_points(n):
    with pytest.raises(ValueError):
        mu.resample_polyline([[0.0, 0.0]], n)
