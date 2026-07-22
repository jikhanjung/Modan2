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


class TestBuildCurveConfig:
    def test_start_indices_from_fixed_count(self):
        config = mu.build_curve_config(5, [20, 12])
        assert config == [
            {"id": "curve1", "n": 20, "method": "equidistant", "start": 5},
            {"id": "curve2", "n": 12, "method": "equidistant", "start": 25},
        ]

    def test_no_curves(self):
        assert mu.build_curve_config(5, []) == []

    def test_zero_fixed_count(self):
        config = mu.build_curve_config(0, [8])
        assert config[0]["start"] == 0


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


# --------------------------------------------------------------------------- #
# TPS curve import
# --------------------------------------------------------------------------- #

from ModanComponents import TPS  # noqa: E402
from ModanController import ModanController  # noqa: E402

TPS_WITH_CURVE = """LM=3
0 0
1 0
2 0
CURVES=1
POINTS=4
0 1
0 2
0 3
0 4
ID=obj1
LM=3
10 10
11 10
12 10
CURVES=1
POINTS=4
10 11
10 12
10 13
10 14
ID=obj2
"""

TPS_NO_CURVE = """LM=3
0 0
1 0
2 0
ID=a
LM=3
5 5
6 5
7 5
ID=b
"""


def _write_tps(tmp_path, content, name="in.tps"):
    path = tmp_path / name
    path.write_text(content)
    return str(path)


class TestTpsCurveParsing:
    def test_curve_points_kept_out_of_landmarks(self, tmp_path):
        tps = TPS(_write_tps(tmp_path, TPS_WITH_CURVE), "ds")
        # Landmarks are only the 3 fixed points, not the 4 curve points.
        assert tps.nlandmarks == 3
        assert len(tps.landmark_data["obj1"]) == 3
        assert tps.landmark_data["obj1"] == [[0, 0], [1, 0], [2, 0]]

    def test_curves_captured_per_object(self, tmp_path):
        tps = TPS(_write_tps(tmp_path, TPS_WITH_CURVE), "ds")
        assert list(tps.curve_data.keys()) == ["obj1", "obj2"]
        assert tps.curve_data["obj1"] == [[[0, 1], [0, 2], [0, 3], [0, 4]]]
        assert tps.curve_data["obj2"] == [[[10, 11], [10, 12], [10, 13], [10, 14]]]

    def test_landmark_only_file_has_no_curves(self, tmp_path):
        tps = TPS(_write_tps(tmp_path, TPS_NO_CURVE), "ds")
        assert tps.curve_data == {}
        assert len(tps.landmark_data["a"]) == 3

    def test_inverty_applies_to_curve_points(self, tmp_path):
        tps = TPS(_write_tps(tmp_path, TPS_WITH_CURVE), "ds", invertY=True)
        assert tps.curve_data["obj1"][0][0] == [0, -1]


class TestTpsCurveImport:
    def test_import_keeps_curves_as_raw_only(self, test_database, tmp_path):
        tps = TPS(_write_tps(tmp_path, TPS_WITH_CURVE), "ds")
        controller = ModanController()
        dataset = controller.import_dataset(tps, "Imported", str(tmp_path))

        # Dataset records one curve of 4 points starting after the 3 fixed ones.
        assert dataset.get_curve_config() == [{"id": "curve1", "n": 4, "method": "equidistant", "start": 3}]

        obj = dataset.object_list.order_by(mm.MdObject.id).first()
        obj.unpack_landmark()
        # landmark_str holds only the 3 fixed landmarks (merge-at-analysis model).
        assert len(obj.landmark_list) == 3
        # Curve points are kept as a raw trace instead.
        assert obj.get_curve_raw() == {"curve1": [[0, 1], [0, 2], [0, 3], [0, 4]]}

    def test_datasetops_merges_curves_into_landmarks(self, test_database, tmp_path):
        tps = TPS(_write_tps(tmp_path, TPS_WITH_CURVE), "ds")
        controller = ModanController()
        dataset = controller.import_dataset(tps, "Imported", str(tmp_path))

        ds_ops = mm.MdDatasetOps(dataset)
        # Analysis view: 3 fixed + 4 resampled semi-landmarks.
        for ops in ds_ops.object_list:
            assert len(ops.landmark_list) == 7

    def test_import_without_curves_leaves_config_empty(self, test_database, tmp_path):
        tps = TPS(_write_tps(tmp_path, TPS_NO_CURVE), "ds")
        controller = ModanController()
        dataset = controller.import_dataset(tps, "Plain", str(tmp_path))
        assert dataset.get_curve_config() == []
        obj = dataset.object_list.first()
        assert obj.get_curve_raw() == {}


# --------------------------------------------------------------------------- #
# ObjectDialog curve tracing (finish_curve)
# --------------------------------------------------------------------------- #

from unittest.mock import patch  # noqa: E402

from PyQt5.QtWidgets import QDialog, QTableWidget  # noqa: E402

from dialogs.object_dialog import ObjectDialog  # noqa: E402


class _FakeDataset:
    def __init__(self, dimension=2):
        self.dimension = dimension
        self._config = []
        self.saved = 0

    def get_curve_config(self):
        return list(self._config)

    def set_curve_config(self, cfg):
        self._config = cfg

    def save(self):
        self.saved += 1


class _FakeView:
    def __init__(self):
        self.landmark_list = None
        self.selected_curve_id = None
        self.edit_mode = None

    def set_mode(self, mode):
        self.edit_mode = mode

    def repaint(self):
        pass

    def update(self):
        pass


def _build_dialog(qtbot, landmarks=None):
    dlg = ObjectDialog.__new__(ObjectDialog)
    QDialog.__init__(dlg)
    dlg.remember_geometry = False
    qtbot.addWidget(dlg)
    dlg.dataset = _FakeDataset(2)
    dlg.object = None
    dlg.landmark_list = landmarks if landmarks is not None else [[1.0, 2.0], [3.0, 4.0]]
    dlg.curve_config = []
    dlg.curve_raw_map = {}
    dlg._orig_curve_config = []
    dlg._orig_curve_raw = {}
    dlg._populating_landmark_table = False
    dlg.selected_landmark_index = -1
    dlg.object_view_2d = _FakeView()
    dlg.object_view_3d = _FakeView()
    table = QTableWidget()
    qtbot.addWidget(table)
    table.setColumnCount(2)
    dlg.edtLandmarkStr = table
    curve_table = QTableWidget()
    qtbot.addWidget(curve_table)
    curve_table.setColumnCount(4)
    dlg.curveTable = curve_table
    dlg._populating_curve_table = False
    curve_table.itemChanged.connect(dlg.on_curve_cell_changed)
    curve_table.itemSelectionChanged.connect(dlg.on_curve_selected)
    dlg.object_view = dlg.object_view_2d
    dlg.on_landmark_selected = lambda: None
    dlg.show_landmarks()
    return dlg


SCHEME = [
    {"id": "curve1", "n": 10, "method": "equidistant", "start": 2},
    {"id": "curve2", "n": 8, "method": "equidistant", "start": 12},
]


class TestObjectDialogFinishCurve:
    """Merge-at-analysis model: finish_curve stores only the raw trace."""

    def _dlg(self, qtbot, scheme):
        dlg = _build_dialog(qtbot)  # 2 fixed landmarks
        dlg.curve_config = [dict(c) for c in scheme]
        return dlg

    def test_stores_raw_for_next_curve_without_touching_landmarks(self, qtbot):
        dlg = self._dlg(qtbot, SCHEME)
        raw = [[0, 0], [10, 0], [10, 10]]
        dlg.finish_curve(raw)
        assert dlg.curve_raw_map == {"curve1": raw}
        # Landmark list (fixed only) is untouched -- semis are not stored.
        assert len(dlg.landmark_list) == 2

    def test_second_trace_fills_second_curve(self, qtbot):
        dlg = self._dlg(qtbot, SCHEME)
        dlg.finish_curve([[0, 0], [4, 0]])
        dlg.finish_curve([[0, 5], [0, 9]])
        assert set(dlg.curve_raw_map.keys()) == {"curve1", "curve2"}
        assert len(dlg.landmark_list) == 2

    def test_empty_scheme_creates_first_curve_and_asks_n(self, qtbot):
        dlg = _build_dialog(qtbot)  # empty curve config, 2 fixed landmarks
        with patch("dialogs.object_dialog.QInputDialog.getInt", return_value=(15, True)):
            dlg.finish_curve([[0, 0], [1, 0]])
        config = dlg.curve_config
        assert [c["id"] for c in config] == ["curve1"]
        assert config[0]["n"] == 15  # count from the prompt
        assert config[0]["start"] == 2  # after the 2 fixed landmarks
        assert "curve1" in dlg.curve_raw_map

    def test_new_curve_prompt_cancelled_is_noop(self, qtbot):
        dlg = _build_dialog(qtbot)
        with patch("dialogs.object_dialog.QInputDialog.getInt", return_value=(0, False)):
            dlg.finish_curve([[0, 0], [1, 0]])
        assert dlg.curve_raw_map == {}
        assert dlg.curve_config == []

    def test_trace_beyond_scheme_grows_it(self, qtbot):
        dlg = self._dlg(qtbot, [SCHEME[0]])  # one defined curve
        dlg.finish_curve([[0, 0], [1, 0]])  # fills curve1 (existing, no prompt)
        with patch("dialogs.object_dialog.QInputDialog.getInt", return_value=(6, True)):
            dlg.finish_curve([[2, 2], [3, 3]])  # new curve -> prompt
        config = dlg.curve_config
        assert [c["id"] for c in config] == ["curve1", "curve2"]
        assert config[1]["n"] == 6
        assert set(dlg.curve_raw_map.keys()) == {"curve1", "curve2"}

    def test_too_few_points_is_noop(self, qtbot):
        dlg = self._dlg(qtbot, SCHEME)
        dlg.finish_curve([[0, 0]])
        assert dlg.curve_raw_map == {}


class TestObjectDialogCurveTable:
    def _dlg(self, qtbot, scheme):
        dlg = _build_dialog(qtbot)
        dlg.curve_config = [dict(c) for c in scheme]
        return dlg

    def test_show_curves_lists_scheme_with_traced_endpoints(self, qtbot):
        dlg = self._dlg(qtbot, SCHEME)
        dlg.curve_raw_map = {"curve1": [[0.0, 0.0], [5.0, 1.0], [10.0, 2.0]]}
        dlg.show_curves()
        assert dlg.curveTable.rowCount() == 2
        assert dlg.curveTable.item(0, 0).text() == "curve1"
        assert dlg.curveTable.item(0, 3).text() == "10"  # N
        assert dlg.curveTable.item(0, 1).text() == "(0.0, 0.0)"  # start
        assert dlg.curveTable.item(0, 2).text() == "(10.0, 2.0)"  # end
        # Untraced curve has blank endpoints.
        assert dlg.curveTable.item(1, 1).text() == ""

    def test_editing_n_updates_config_dataset_wide(self, qtbot):
        dlg = self._dlg(qtbot, SCHEME)
        dlg.show_curves()
        # Simulate the user editing curve1's N from 10 to 15.
        dlg.curveTable.item(0, 3).setText("15")
        config = dlg.curve_config
        assert config[0]["n"] == 15
        # Following curve's start index shifts accordingly (2 + 15).
        assert config[1]["start"] == 17

    def test_editing_n_to_invalid_reverts(self, qtbot):
        dlg = self._dlg(qtbot, SCHEME)
        dlg.show_curves()
        dlg.curveTable.item(0, 3).setText("abc")
        # Config unchanged.
        assert dlg.curve_config[0]["n"] == 10


# --------------------------------------------------------------------------- #
# DatasetDialog curve scheme (number of curves vs semi-landmarks per curve)
# --------------------------------------------------------------------------- #

from PyQt5.QtWidgets import QLineEdit  # noqa: E402

from dialogs.dataset_dialog import DatasetDialog  # noqa: E402


class TestDatasetDialogCurveScheme:
    def _dlg(self, qtbot, existing=None):
        dlg = DatasetDialog.__new__(DatasetDialog)
        dlg.edtFixedCount = QLineEdit()
        dlg.edtNumCurves = QLineEdit()
        dlg.edtSemiPerCurve = QLineEdit()
        for edt in (dlg.edtFixedCount, dlg.edtNumCurves, dlg.edtSemiPerCurve):
            qtbot.addWidget(edt)
        dlg.dataset = _FakeDataset(2)
        if existing:
            dlg.dataset._config = existing
        return dlg

    def test_number_of_curves_and_uniform_default(self, qtbot):
        dlg = self._dlg(qtbot)
        dlg.edtFixedCount.setText("5")
        dlg.edtNumCurves.setText("2")
        dlg.edtSemiPerCurve.setText("20")
        config = dlg._build_curve_config()
        assert [c["n"] for c in config] == [20, 20]
        assert [c["start"] for c in config] == [5, 25]

    def test_preserves_existing_per_curve_counts(self, qtbot):
        existing = [
            {"id": "curve1", "n": 20, "method": "equidistant", "start": 5},
            {"id": "curve2", "n": 12, "method": "equidistant", "start": 25},
        ]
        dlg = self._dlg(qtbot, existing)
        dlg.edtFixedCount.setText("5")
        dlg.edtNumCurves.setText("3")  # add one curve
        dlg.edtSemiPerCurve.setText("8")  # default for the new curve only
        config = dlg._build_curve_config()
        # Existing per-curve counts kept; only the new (3rd) curve uses the default.
        assert [c["n"] for c in config] == [20, 12, 8]

    def test_zero_curves_clears_config(self, qtbot):
        dlg = self._dlg(qtbot)
        dlg.edtNumCurves.setText("")
        assert dlg._build_curve_config() == []


# --------------------------------------------------------------------------- #
# Curve point editing (viewer hit-testing + row selection)
# --------------------------------------------------------------------------- #

from ModanComponents import ObjectViewer2D  # noqa: E402


class _RawDlg:
    def __init__(self, raw_map):
        self.curve_raw_map = raw_map
        self.curve_config = [{"id": cid, "n": 5, "method": "equidistant", "start": 0} for cid in raw_map]
        self.curves_refreshed = 0

    def show_curves(self):
        self.curves_refreshed += 1


class TestCurvePointEditingHelpers:
    def _viewer(self, qtbot, raw):
        v = ObjectViewer2D()
        qtbot.addWidget(v)
        v.scale = 1.0
        v.pan_x = v.pan_y = v.temp_pan_x = v.temp_pan_y = 0
        v.image_canvas_ratio = 1.0
        v.object_dialog = _RawDlg({"curve1": raw})
        v.selected_curve_id = "curve1"
        return v

    def test_point_hit_test(self, qtbot):
        v = self._viewer(qtbot, [[0, 0], [10, 0], [20, 0]])
        assert v._curve_point_within_threshold([10, 0]) == 1
        assert v._curve_point_within_threshold([50, 50]) == -1

    def test_segment_hit_test(self, qtbot):
        v = self._viewer(qtbot, [[0, 0], [20, 0]])
        assert v._curve_segment_within_threshold([10, 0]) == 0
        assert v._curve_segment_within_threshold([10, 50]) == -1

    def test_selected_raw_is_the_live_list(self, qtbot):
        raw = [[0, 0], [10, 0]]
        v = self._viewer(qtbot, raw)
        assert v._selected_curve_raw() is raw

    def test_point_segment_distance(self):
        assert ObjectViewer2D._point_segment_distance([5, 3], [0, 0], [10, 0]) == pytest.approx(3.0)
        assert ObjectViewer2D._point_segment_distance([15, 0], [0, 0], [10, 0]) == pytest.approx(5.0)

    def test_curve_at_position_finds_nearby_curve(self, qtbot):
        v = self._viewer(qtbot, [[0, 0], [10, 0], [20, 0]])
        v.selected_curve_id = None  # trace mode: still finds the curve to select
        assert v._curve_at_position([10, 0]) == "curve1"
        assert v._curve_at_position([10, 50]) is None


class TestCurveRowSelection:
    def test_selecting_row_enables_curve_editing(self, qtbot):
        dlg = _build_dialog(qtbot)
        dlg.curve_config = [dict(c) for c in SCHEME]
        dlg.curve_raw_map = {"curve1": [[0, 0], [1, 1]]}
        dlg.show_curves()
        dlg.curveTable.selectRow(1)
        assert dlg.object_view.selected_curve_id == "curve2"
        assert dlg.object_view.edit_mode == mm_mode_edit_curve()


def mm_mode_edit_curve():
    from MdConstants import MODE

    return MODE["EDIT_CURVE"]


class TestCurveEditingHeldInMemory:
    def test_finish_curve_does_not_persist_until_save(self, qtbot, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        obj = mm.MdObject.create(object_name="o", dataset=ds, landmark_str="1\t1\n2\t2")
        dlg = _build_dialog(qtbot)
        dlg.dataset = ds
        dlg.object = obj
        with patch("dialogs.object_dialog.QInputDialog.getInt", return_value=(4, True)):
            dlg.finish_curve([[10, 10], [20, 10], [30, 10]])
        # Held in the dialog's working copies...
        assert "curve1" in dlg.curve_raw_map
        assert dlg.curve_config[0]["n"] == 4
        # ...but not written to the database until Save.
        assert mm.MdObject.get_by_id(obj.id).get_curve_raw() == {}
        assert mm.MdDataset.get_by_id(ds.id).get_curve_config() == []

    def test_cancel_detects_unsaved_curve_edits(self, qtbot):
        dlg = _build_dialog(qtbot)
        dlg._orig_curve_raw = {}
        dlg._orig_curve_config = []
        assert dlg._has_unsaved_curve_changes() is False
        dlg.curve_raw_map = {"curve1": [[0, 0], [1, 1]]}
        assert dlg._has_unsaved_curve_changes() is True


class TestExpectedLandmarks:
    def test_expected_filled_after_two_placed(self, qtbot, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        # Two complete 4-landmark specimens so a mean shape can be computed.
        mm.MdObject.create(object_name="a", dataset=ds, landmark_str="0\t0\n1\t0\n1\t1\n0\t1")
        mm.MdObject.create(object_name="b", dataset=ds, landmark_str="0.1\t0\n1.1\t0\n1\t1\n0\t1.1")
        dlg = _build_dialog(qtbot)
        dlg.dataset = ds
        dlg._aligned_mean_cache = None
        dlg.show_expected = True
        dlg.landmark_list = [[0.0, 0.0], [1.0, 0.0]]  # two placed on a new specimen
        dlg.update_expected_landmarks()
        # Full-length list; the two unplaced positions are filled in.
        assert dlg.expected_landmark_list is not None
        assert len(dlg.expected_landmark_list) == 4
        assert all(v is not None for v in dlg.expected_landmark_list[2])
        assert all(v is not None for v in dlg.expected_landmark_list[3])

    def test_no_expected_with_fewer_than_two_placed(self, qtbot, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        mm.MdObject.create(object_name="a", dataset=ds, landmark_str="0\t0\n1\t0\n1\t1\n0\t1")
        mm.MdObject.create(object_name="b", dataset=ds, landmark_str="0.1\t0\n1.1\t0\n1\t1\n0\t1.1")
        dlg = _build_dialog(qtbot)
        dlg.dataset = ds
        dlg._aligned_mean_cache = None
        dlg.show_expected = True
        dlg.landmark_list = [[0.0, 0.0]]  # only one placed
        dlg.update_expected_landmarks()
        assert dlg.expected_landmark_list is None

    def test_no_expected_when_disabled(self, qtbot, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        mm.MdObject.create(object_name="a", dataset=ds, landmark_str="0\t0\n1\t0\n1\t1\n0\t1")
        mm.MdObject.create(object_name="b", dataset=ds, landmark_str="0.1\t0\n1.1\t0\n1\t1\n0\t1.1")
        dlg = _build_dialog(qtbot)
        dlg.dataset = ds
        dlg._aligned_mean_cache = None
        dlg.show_expected = False
        dlg.landmark_list = [[0.0, 0.0], [1.0, 0.0]]
        dlg.update_expected_landmarks()
        assert dlg.expected_landmark_list is None
