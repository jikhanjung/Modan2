"""Accuracy of missing-landmark imputation, against known ground truth.

Both the object dialog's preview and Procrustes imputation fill gaps through
``impute_missing_landmarks``: fit the reference shape onto the landmarks an
object actually has (rotation + scale + translation), then borrow the missing
coordinates from the fitted reference.

The regression these guard: the analysis path used to copy the mean's
coordinates across directly, from inside the alignment loop and before the
first rotation, so estimates were off by the object's arbitrary starting
orientation — 61% of centroid size even on noise-free data — and were never
revisited afterwards. See devlog 227.
"""

import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdModel as mm
from MdModel import impute_missing_landmarks

# A well-spread asymmetric shape: symmetric ones can hide rotation errors.
SHAPE = [[0.0, 0.0], [1.0, 0.2], [1.6, 1.1], [1.0, 2.0], [0.0, 1.8], [-0.6, 1.0]]


def _rot(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])


def _transform(points, angle_deg=0.0, scale=1.0, tx=0.0, ty=0.0):
    r = _rot(angle_deg)
    return [list(scale * (r @ np.array(p)) + np.array([tx, ty])) for p in points]


class TestImputeHelper:
    """Unit-level behaviour of the shared helper."""

    @pytest.mark.parametrize("angle", [0, 37, 90, -120, 180])
    def test_recovers_landmark_under_similarity_transform(self, angle):
        truth = _transform(SHAPE, angle_deg=angle, scale=17.0, tx=250.0, ty=-80.0)
        observed = [list(p) for p in truth]
        observed[3] = [None, None]

        result = impute_missing_landmarks(observed, SHAPE)

        assert np.allclose(result[3], truth[3], atol=1e-6)
        for i in (0, 1, 2, 4, 5):
            assert result[i] == observed[i], "observed landmarks must not be touched"

    def test_reflected_shape_is_not_matched_by_reflection(self):
        """Kabsch excludes reflection: a mirrored specimen must not fit exactly."""
        mirrored = [[-x, y] for x, y in SHAPE]
        observed = [list(p) for p in mirrored]
        observed[2] = [None, None]

        result = impute_missing_landmarks(observed, SHAPE)

        assert not np.allclose(result[2], mirrored[2], atol=1e-6)

    def test_three_dimensional_shape(self):
        shape_3d = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.5], [0.5, 1.0, 0.0], [0.0, 0.5, 1.0]]
        truth = [[2 * x + 1, 2 * y - 3, 2 * z + 4] for x, y, z in shape_3d]
        observed = [list(p) for p in truth]
        observed[2] = [None, None, None]

        result = impute_missing_landmarks(observed, shape_3d)

        assert np.allclose(result[2], truth[2], atol=1e-6)

    def test_dimension_inferred_from_reference(self):
        shape_3d = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        observed = [list(p) for p in shape_3d]
        observed[3] = [None, None, None]

        result = impute_missing_landmarks(observed, shape_3d)

        assert np.allclose(result[3], shape_3d[3], atol=1e-6)

    def test_too_few_shared_landmarks_returns_input(self):
        observed = [[1.0, 2.0], [None, None], [None, None], [None, None], [None, None], [None, None]]
        assert impute_missing_landmarks(observed, SHAPE) == observed

    def test_landmark_missing_in_reference_too_is_left_alone(self):
        reference = [list(p) for p in SHAPE]
        reference[4] = [None, None]
        observed = _transform(SHAPE, angle_deg=25, scale=3.0)
        observed[4] = [None, None]

        result = impute_missing_landmarks(observed, reference)

        assert result[4] == [None, None]

    def test_empty_and_missing_reference_are_safe(self):
        assert impute_missing_landmarks([], SHAPE) == []
        assert impute_missing_landmarks([[1.0, 2.0]], None) == [[1.0, 2.0]]


def _dataset_from(coords_list, dimension=2):
    """MdDatasetOps over in-memory objects, bypassing the DB-reading __init__."""
    ops = mm.MdDatasetOps.__new__(mm.MdDatasetOps)
    ops.id = None
    ops.dataset_name = "t"
    ops.dataset_desc = ""
    ops.dimension = dimension
    ops.wireframe = ""
    ops.baseline = ""
    ops.polygons = ""
    ops.selected_object_id_list = []
    ops.edge_list = []
    ops.variablename_list = []
    ops.baseline_point_list = []
    ops.reference_shape = None
    ops.object_list = []
    for i, coords in enumerate(coords_list):
        obj = mm.MdObjectOps.__new__(mm.MdObjectOps)
        obj.id = i + 1
        obj.object_name = f"O{i}"
        obj.object_desc = ""
        obj.pixel_per_mm = None
        obj.sequence = i + 1
        obj.landmark_str = ""
        obj.property_str = ""
        obj.variable_list = []
        obj.centroid_size = -1
        obj.landmark_list = [list(p) for p in coords]
        ops.object_list.append(obj)
    return ops


def _aligned(ops):
    return [np.array(o.landmark_list, dtype=float) for o in ops.object_list]


def _error_vs_truth(got, truth, knocked_lm):
    """Distance between the imputed point and truth, as % of centroid size.

    Both configurations are Procrustes results in their own frames, so compare
    after aligning on the landmarks that were never missing.
    """
    keep = [i for i in range(len(truth)) if i != knocked_lm]
    a, b = got[keep], truth[keep]
    ca, cb = a.mean(0), b.mean(0)
    centered_a, centered_b = a - ca, b - cb
    u, _, vt = np.linalg.svd(centered_a.T @ centered_b)
    d = np.sign(np.linalg.det(vt.T @ u.T)) or 1.0
    r = vt.T @ np.diag([1.0, d]) @ u.T
    s = np.sqrt((centered_b**2).sum()) / np.sqrt((centered_a**2).sum())
    placed = (r @ (got[knocked_lm] - ca)) * s + cb
    size = np.sqrt(((truth - truth.mean(0)) ** 2).sum())
    return np.linalg.norm(placed - truth[knocked_lm]) / size * 100


def _spread_specimens(seed=0, count=8):
    """Identical shapes at assorted orientations, scales and positions."""
    rng = np.random.default_rng(seed)
    return [
        _transform(
            SHAPE,
            angle_deg=rng.uniform(-180, 180),
            scale=rng.uniform(0.5, 2.0),
            tx=rng.uniform(-50, 50),
            ty=rng.uniform(-50, 50),
        )
        for _ in range(count)
    ]


class TestProcrustesImputationAccuracy:
    @pytest.mark.parametrize("knocked_lm", range(len(SHAPE)))
    def test_recovers_knocked_out_landmark(self, knocked_lm):
        """With no shape variation the estimate should be essentially exact.

        Every specimen is the same shape, so the gap is fully determined; a
        rotation-blind or normalisation-blind estimate misses by tens of
        percent here.
        """
        specimens = _spread_specimens()

        complete = _dataset_from(specimens)
        assert complete.procrustes_superimposition()
        truth = _aligned(complete)[0]

        with_gap = _dataset_from(specimens)
        with_gap.object_list[0].landmark_list[knocked_lm] = [None, None]
        assert with_gap.procrustes_superimposition()
        got = _aligned(with_gap)[0]

        assert _error_vs_truth(got, truth, knocked_lm) < 0.5

    def test_no_landmark_is_left_missing(self):
        specimens = _spread_specimens()
        ops = _dataset_from(specimens)
        ops.object_list[0].landmark_list[2] = [None, None]
        ops.object_list[3].landmark_list[0] = [None, None]

        assert ops.procrustes_superimposition()

        for obj in ops.object_list:
            for lm in obj.landmark_list:
                assert all(c is not None for c in lm)

    def test_complete_dataset_is_unaffected_by_the_imputation_path(self):
        specimens = _spread_specimens(seed=3)
        plain = _dataset_from(specimens)
        plain.procrustes_superimposition()

        forced = _dataset_from(specimens)
        forced.procrustes_superimposition_with_imputation()

        for a, b in zip(_aligned(plain), _aligned(forced)):
            assert np.allclose(a, b, atol=1e-6)

    def test_landmark_missing_everywhere_stays_missing(self):
        """Nothing to estimate from — the analysis gate reports these separately."""
        specimens = _spread_specimens(count=4)
        ops = _dataset_from(specimens)
        for obj in ops.object_list:
            obj.landmark_list[1] = [None, None]

        assert ops.procrustes_superimposition()

        assert all(obj.landmark_list[1] == [None, None] for obj in ops.object_list)
