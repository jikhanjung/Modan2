"""Tests for ObjectDialog.estimate_missing_for_object.

The mean shape lives in the Procrustes-aligned frame while the object is in
image coordinates, so mapping mean -> object must fit a full similarity
transform (rotation + scale + translation) on the shared valid landmarks.
A specimen photographed at an angle exposed the old centroid+scale-only fit:
estimated landmarks landed in the wrong place.
"""

import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dialogs.object_dialog import ObjectDialog

# A unit-ish "mean shape" in the aligned frame: 5 well-spread landmarks.
MEAN_LANDMARKS = [
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0],
    [0.5, 1.5],
]


class _Shape:
    def __init__(self, landmark_list):
        self.landmark_list = landmark_list


class _Obj:
    def __init__(self, landmark_list):
        self.landmark_list = landmark_list
        self.object_name = "test-obj"

    def unpack_landmark(self):
        pass


def _dialog_with_mean(mean_landmarks):
    """ObjectDialog stub whose compute_aligned_mean returns a fixed shape."""
    dlg = ObjectDialog.__new__(ObjectDialog)  # skip QDialog __init__
    dlg.compute_aligned_mean = lambda: _Shape(mean_landmarks)
    return dlg


def _similarity_transform(points, angle_deg, scale, tx, ty):
    """Rotate+scale+translate a list of [x, y] points."""
    a = math.radians(angle_deg)
    r = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return [list(scale * (r @ np.array(p)) + np.array([tx, ty])) for p in points]


@pytest.mark.parametrize("angle_deg", [0, 30, 90, -45, 180])
def test_estimate_recovers_missing_landmark_under_rotation(angle_deg):
    """A missing landmark on a rotated specimen is recovered at (nearly) its
    true position: the fit must include rotation, not just centroid+scale."""
    scale, tx, ty = 40.0, 500.0, 300.0
    true_coords = _similarity_transform(MEAN_LANDMARKS, angle_deg, scale, tx, ty)

    observed = [list(p) for p in true_coords]
    observed[2] = [None, None]  # knock out one landmark

    dlg = _dialog_with_mean(MEAN_LANDMARKS)
    result = dlg.estimate_missing_for_object(_Obj(observed))

    est = np.array(result[2])
    truth = np.array(true_coords[2])
    assert np.allclose(est, truth, atol=1e-6), f"angle={angle_deg}: estimated {est}, expected {truth}"
    # valid landmarks pass through untouched
    for i in (0, 1, 3, 4):
        assert result[i] == observed[i]


def test_estimate_without_rotation_still_works():
    """Pure scale+translation case (the old code's only correct case)."""
    true_coords = _similarity_transform(MEAN_LANDMARKS, 0, 10.0, 100.0, 50.0)
    observed = [list(p) for p in true_coords]
    observed[4] = [None, None]

    dlg = _dialog_with_mean(MEAN_LANDMARKS)
    result = dlg.estimate_missing_for_object(_Obj(observed))

    assert np.allclose(result[4], true_coords[4], atol=1e-6)


def test_estimate_skips_indices_invalid_in_mean_shape():
    """Indices missing in BOTH object and mean can't be estimated and must not
    skew the fit of the others (index-aligned pairing)."""
    mean = [list(p) for p in MEAN_LANDMARKS]
    mean[1] = [None, None]  # mean shape lacks landmark 1

    true_coords = _similarity_transform(MEAN_LANDMARKS, 30, 20.0, 0.0, 0.0)
    observed = [list(p) for p in true_coords]
    observed[1] = [17.0, 23.0]  # valid in object, invalid in mean -> excluded from fit
    observed[3] = [None, None]  # to be estimated

    dlg = _dialog_with_mean(mean)
    result = dlg.estimate_missing_for_object(_Obj(observed))

    assert np.allclose(result[3], true_coords[3], atol=1e-6)
    # landmark 1 stays as observed; it must not be "estimated"
    assert result[1] == [17.0, 23.0]


def test_estimate_returns_original_when_too_few_valid():
    observed = [[1.0, 2.0], [None, None], [None, None], [None, None], [None, None]]
    dlg = _dialog_with_mean(MEAN_LANDMARKS)
    result = dlg.estimate_missing_for_object(_Obj(observed))
    assert result == observed


def test_estimate_no_missing_returns_as_is():
    observed = [list(p) for p in MEAN_LANDMARKS]
    dlg = _dialog_with_mean(MEAN_LANDMARKS)
    result = dlg.estimate_missing_for_object(_Obj(observed))
    assert result == observed


def test_estimate_none_object_returns_empty():
    dlg = _dialog_with_mean(MEAN_LANDMARKS)
    assert dlg.estimate_missing_for_object(None) == []
