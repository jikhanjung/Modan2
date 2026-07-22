"""Tests for semi-landmark support -- step 1 (data model + resampling utils).

Covers the curve resampling utilities in MdUtils and the JSON accessors that
store curve configuration (dataset/analysis) and raw traces (object). Alignment-
time sliding is intentionally out of scope here (see devlog 237).
"""

import math
import os
import sys
import tempfile

import numpy as np
import pytest
from peewee import SqliteDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdModel as mm
import MdUtils as mu


@pytest.fixture
def test_database():
    """A temporary database with the models pointed at it (mirrors test_mdmodel)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        path = tmp.name
    db = SqliteDatabase(path, pragmas={"foreign_keys": 1})
    original = mm.gDatabase
    mm.gDatabase = db
    models = [mm.MdDataset, mm.MdObject, mm.MdImage, mm.MdThreeDModel, mm.MdAnalysis]
    for model in models:
        model._meta.database = db
    db.connect()
    db.create_tables(models)
    yield db
    db.drop_tables(models)
    db.close()
    mm.gDatabase = original
    for model in models:
        model._meta.database = original
    try:
        os.unlink(path)
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# Resampling utilities
# --------------------------------------------------------------------------- #


class TestResampleEquidistant:
    def test_straight_line_is_evenly_spaced(self):
        # A line from (0,0) to (10,0) resampled to 6 points -> spacing of 2.
        pts = mu.resample_polyline([[0.0, 0.0], [10.0, 0.0]], 6)
        assert len(pts) == 6
        xs = [p[0] for p in pts]
        assert xs == pytest.approx([0.0, 2.0, 4.0, 6.0, 8.0, 10.0])
        assert all(abs(p[1]) < 1e-12 for p in pts)

    def test_endpoints_preserved_for_open_curve(self):
        pts = mu.resample_polyline([[1.0, 1.0], [4.0, 5.0]], 4)
        assert pts[0] == pytest.approx([1.0, 1.0])
        assert pts[-1] == pytest.approx([4.0, 5.0])

    def test_arc_length_spacing_on_L_shape(self):
        # Two unit-length legs: total length 2, 3 points -> at 0, 1 (the corner), 2.
        pts = mu.resample_polyline([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]], 3)
        assert pts[0] == pytest.approx([0.0, 0.0])
        assert pts[1] == pytest.approx([1.0, 0.0])
        assert pts[2] == pytest.approx([1.0, 1.0])

    def test_spacing_uniform_across_an_inflection(self):
        # An S-shaped curve (sine over one period) has an inflection at the middle
        # -- equal arc-length spacing must stay uniform straight through it, which
        # is exactly why equidistant (not equal-angle) is the right choice.
        raw = [[x, math.sin(x)] for x in np.linspace(0, 2 * math.pi, 600)]
        pts = np.array(mu.resample_polyline(raw, 20))
        # Compare arc length between consecutive outputs via a dense recompute.
        gaps = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        # Chords slightly under-measure arc on curved bits, but uniformly, so the
        # spread stays small even across the inflection.
        assert (gaps.max() - gaps.min()) / gaps.mean() < 0.05

    def test_3d_curve(self):
        pts = mu.resample_polyline([[0, 0, 0], [0, 0, 4]], 5)
        assert len(pts) == 5
        assert all(len(p) == 3 for p in pts)
        assert [p[2] for p in pts] == pytest.approx([0, 1, 2, 3, 4])

    def test_closed_curve_count_and_no_duplicate_end(self):
        square = [[0, 0], [1, 0], [1, 1], [0, 1]]
        pts = mu.resample_polyline(square, 8, closed=True)
        assert len(pts) == 8
        # Closed loop omits the duplicated start/end, so first != last.
        assert pts[0] != pts[-1]

    def test_coincident_points_do_not_crash(self):
        pts = mu.resample_polyline([[2.0, 3.0], [2.0, 3.0]], 4)
        assert len(pts) == 4
        assert all(p == pytest.approx([2.0, 3.0]) for p in pts)


class TestResampleValidation:
    def test_too_few_input_points(self):
        with pytest.raises(ValueError):
            mu.resample_polyline([[0, 0]], 4)

    def test_n_too_small(self):
        with pytest.raises(ValueError):
            mu.resample_polyline([[0, 0], [1, 1]], 1)


class TestBuildLandmarksWithCurves:
    def test_fixed_landmarks_come_first_unchanged(self):
        fixed = [[0.0, 0.0], [1.0, 1.0]]
        curves = [{"id": "A", "n": 3, "raw": [[0, 0], [10, 0]]}]
        lms, config = mu.build_landmarks_with_curves(fixed, curves)
        assert lms[:2] == fixed
        assert len(lms) == 2 + 3

    def test_config_start_indices(self):
        fixed = [[0.0, 0.0], [1.0, 1.0]]
        curves = [
            {"id": "A", "n": 4, "raw": [[0, 0], [4, 0]]},
            {"id": "B", "n": 3, "raw": [[0, 5], [0, 8]]},
        ]
        lms, config = mu.build_landmarks_with_curves(fixed, curves)
        assert [c["start"] for c in config] == [2, 6]
        assert [c["n"] for c in config] == [4, 3]
        assert [c["id"] for c in config] == ["A", "B"]
        assert len(lms) == 2 + 4 + 3
        # Curve A occupies indices 2..5, curve B 6..8.
        assert lms[2] == pytest.approx([0, 0])
        assert lms[6] == pytest.approx([0, 5])

    def test_no_fixed_landmarks(self):
        curves = [{"id": "A", "n": 3, "raw": [[0, 0], [2, 0]]}]
        lms, config = mu.build_landmarks_with_curves([], curves)
        assert config[0]["start"] == 0
        assert len(lms) == 3

    def test_no_curves_returns_fixed_only(self):
        fixed = [[0.0, 0.0], [1.0, 1.0]]
        lms, config = mu.build_landmarks_with_curves(fixed, [])
        assert lms == fixed
        assert config == []

    def test_3d_curves(self):
        fixed = [[0.0, 0.0, 0.0]]
        curves = [{"id": "A", "n": 3, "raw": [[0, 0, 0], [0, 0, 2]]}]
        lms, config = mu.build_landmarks_with_curves(fixed, curves)
        assert all(len(p) == 3 for p in lms)
        assert lms[-1] == pytest.approx([0, 0, 2])

    def test_closed_curve_flag_passed_through(self):
        curves = [{"id": "A", "n": 4, "raw": [[0, 0], [1, 0], [1, 1], [0, 1]], "closed": True}]
        lms, config = mu.build_landmarks_with_curves([], curves)
        assert len(lms) == 4
        assert lms[0] != lms[-1]  # closed loop, no duplicated end


# --------------------------------------------------------------------------- #
# Model JSON accessors
# --------------------------------------------------------------------------- #

CONFIG = [
    {"id": "A", "n": 10, "method": "equidistant", "start": 5},
    {"id": "B", "n": 8, "method": "equidistant", "start": 15},
]


class TestDatasetCurveConfig:
    def test_round_trip(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        ds.set_curve_config(CONFIG)
        ds.save()
        reloaded = mm.MdDataset.get_by_id(ds.id)
        assert reloaded.get_curve_config() == CONFIG

    def test_default_empty(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        assert ds.get_curve_config() == []

    def test_set_empty_clears_column(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        ds.set_curve_config(CONFIG)
        ds.set_curve_config([])
        assert ds.curve_config_json is None
        assert ds.get_curve_config() == []

    def test_corrupt_json_yields_empty(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        ds.curve_config_json = "{not valid json"
        assert ds.get_curve_config() == []

    def test_non_list_json_yields_empty(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        ds.curve_config_json = '{"id": "A"}'
        assert ds.get_curve_config() == []


class TestObjectCurveRaw:
    def test_round_trip(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        obj = mm.MdObject.create(object_name="O", dataset=ds)
        raw = {"A": [[0.0, 0.0], [1.0, 2.0], [3.0, 3.0]]}
        obj.set_curve_raw(raw)
        obj.save()
        reloaded = mm.MdObject.get_by_id(obj.id)
        assert reloaded.get_curve_raw() == raw

    def test_default_empty(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        obj = mm.MdObject.create(object_name="O", dataset=ds)
        assert obj.get_curve_raw() == {}

    def test_corrupt_json_yields_empty(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        obj = mm.MdObject.create(object_name="O", dataset=ds)
        obj.curve_raw_json = "not json"
        assert obj.get_curve_raw() == {}

    def test_copy_object_carries_raw_traces(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        other = mm.MdDataset.create(dataset_name="DS2", dimension=2)
        obj = mm.MdObject.create(object_name="O", dataset=ds)
        raw = {"A": [[0.0, 0.0], [1.0, 1.0]]}
        obj.set_curve_raw(raw)
        obj.save()
        clone = obj.copy_object(other)
        assert clone.get_curve_raw() == raw


class TestAnalysisCurveConfigSnapshot:
    def test_round_trip(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        analysis = mm.MdAnalysis.create(dataset=ds, analysis_name="A", superimposition_method="procrustes")
        analysis.set_curve_config(CONFIG)
        analysis.save()
        reloaded = mm.MdAnalysis.get_by_id(analysis.id)
        assert reloaded.get_curve_config() == CONFIG

    def test_default_empty(self, test_database):
        ds = mm.MdDataset.create(dataset_name="DS", dimension=2)
        analysis = mm.MdAnalysis.create(dataset=ds, analysis_name="A", superimposition_method="procrustes")
        assert analysis.get_curve_config() == []
