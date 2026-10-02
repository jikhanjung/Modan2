"""Elliptic Fourier analysis of closed outlines (devlog 288).

Covers the pure math in MdOutline, the closed-curve flag in the curve scheme,
the outline dataset ops, and the controller's "Elliptic Fourier" analysis path.
"""

import json
import math

import numpy as np
import pytest
from peewee import SqliteDatabase

import MdModel as mm
import MdOutline as mo
import MdStatistics as ms
import MdUtils as mu


def _blob(n=200, lobes=3, amp=0.3, sx=1.5, phase=0.0):
    """A smooth star-like outline, clockwise as displayed (positive area)."""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = 1 + amp * np.cos(lobes * t + phase) + 0.1 * np.sin(5 * t)
    return np.column_stack([sx * r * np.cos(t), r * np.sin(t)])


def _transform(points, angle=0.0, scale=1.0, shift=(0.0, 0.0)):
    rot = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
    return (np.asarray(points) @ rot.T) * scale + np.asarray(shift)


def _reverse_keep_start(points):
    pts = np.asarray(points)
    return np.vstack([pts[:1], pts[:0:-1]])


class TestCleanAndDirection:
    def test_drops_repeats_and_closing_point(self):
        pts = mo.clean_outline([[0, 0], [0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])
        assert pts.tolist() == [[0, 0], [1, 0], [1, 1], [0, 1]]

    def test_too_few_points_rejected(self):
        with pytest.raises(ValueError):
            mo.clean_outline([[0, 0], [1, 1], [0, 0]])

    def test_clockwise_as_displayed_is_positive_area(self):
        # y grows downward on screen: top-left -> top-right -> bottom-right is
        # clockwise as the user sees it.
        assert mo.signed_area([[0, 0], [1, 0], [1, 1], [0, 1]]) > 0

    def test_counterclockwise_is_reversed_keeping_the_start(self):
        ccw = [[0, 0], [0, 1], [1, 1], [1, 0]]
        cw = mo.make_clockwise(ccw)
        assert cw[0].tolist() == [0, 0]
        assert cw.tolist() == [[0, 0], [1, 0], [1, 1], [0, 1]]

    def test_clockwise_trace_is_left_alone(self):
        cw = [[0, 0], [1, 0], [1, 1], [0, 1]]
        assert mo.make_clockwise(cw).tolist() == cw


class TestCoefficients:
    def test_matches_direct_fourier_integration(self):
        """Kuhl-Giardina's closed form equals the Fourier integral of the
        arc-length-parametrized polygon, computed here independently."""
        outline = mo.clean_outline(_blob(n=60))
        coeffs, center = mo.efa_coefficients(outline, 6)

        closed = np.vstack([outline, outline[:1]])
        seg = np.sqrt((np.diff(closed, axis=0) ** 2).sum(axis=1))
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        s = np.linspace(0, cum[-1], 200001)
        x = np.interp(s, cum, closed[:, 0])
        y = np.interp(s, cum, closed[:, 1])
        t = 2 * np.pi * s / cum[-1]
        for n in range(1, 7):
            expected = [
                np.trapezoid(x * np.cos(n * t), t) / np.pi,
                np.trapezoid(x * np.sin(n * t), t) / np.pi,
                np.trapezoid(y * np.cos(n * t), t) / np.pi,
                np.trapezoid(y * np.sin(n * t), t) / np.pi,
            ]
            assert np.allclose(coeffs[n - 1], expected, atol=1e-6)
        assert center[0] == pytest.approx(np.trapezoid(x, t) / (2 * np.pi), abs=1e-6)
        assert center[1] == pytest.approx(np.trapezoid(y, t) / (2 * np.pi), abs=1e-6)

    def test_reconstruction_converges_to_the_outline(self):
        outline = _blob(n=400)
        coeffs, center = mo.efa_coefficients(outline, 40)
        rec = mo.reconstruct(coeffs, 400, center)
        dist = np.sqrt(((rec[:, None, :] - outline[None]) ** 2).sum(-1)).min(axis=1)
        assert dist.max() < 0.03
        # t = 0 is the first traced point.
        assert np.allclose(rec[0], outline[0], atol=0.03)


class TestNormalization:
    def test_invariant_to_position_size_rotation_and_direction(self):
        base = mo.analyze_outline(_blob(), 12)
        moved = _reverse_keep_start(_transform(_blob(), angle=2.3, scale=4.0, shift=(50, -20)))
        other = mo.analyze_outline(moved, 12)
        assert np.allclose(base["coefficients"], other["coefficients"], atol=1e-9)
        assert other["size"] / base["size"] == pytest.approx(4.0)

    def test_starting_point_is_kept_not_normalized_away(self):
        """Two traces of one outline from different starting points differ: the
        start is homologous, so it is part of the shape."""
        outline = _blob()
        shifted = np.roll(outline, 40, axis=0)
        a = mo.analyze_outline(outline, 12)["coefficients"]
        b = mo.analyze_outline(shifted, 12)["coefficients"]
        assert not np.allclose(a, b, atol=1e-3)

    def test_first_ellipse_major_axis_lies_on_x(self):
        coeffs = mo.analyze_outline(_blob(), 8)["coefficients"]
        rec = mo.reconstruct(coeffs[:1], 720)
        far = rec[np.argmax((rec**2).sum(axis=1))]
        assert far[0] == pytest.approx(1.0, abs=1e-3)
        assert abs(far[1]) < 1e-2

    def test_degenerate_first_harmonic_rejected(self):
        with pytest.raises(ValueError):
            mo.normalize_coefficients(np.zeros((3, 4)))


class TestHarmonicPower:
    def test_pure_ellipse_needs_one_harmonic(self):
        coeffs = np.array([[2.0, 0, 0, 1.0], [0, 0, 0, 0], [0, 0, 0, 0]])
        assert mo.harmonics_for_power(coeffs, 0.99) == 1

    def test_counts_until_threshold(self):
        # Powers 0.5 * (4, 0.9, 0.08, 0.02) -> cumulative 0.8, 0.98, 0.996, 1.0
        coeffs = np.array(
            [[2, 0, 0, 0], [math.sqrt(0.9), 0, 0, 0], [math.sqrt(0.08), 0, 0, 0], [math.sqrt(0.02), 0, 0, 0]]
        )
        assert mo.harmonics_for_power(coeffs, 0.99) == 3
        assert mo.harmonics_for_power(coeffs, 0.95) == 2

    def test_dataset_count_covers_every_outline(self):
        smooth = _blob(amp=0.05)
        lobed = _blob(lobes=7, amp=0.4)
        both = mo.choose_harmonics([smooth, lobed])
        assert both == max(mo.choose_harmonics([smooth]), mo.choose_harmonics([lobed]))
        assert both > mo.choose_harmonics([smooth])

    def test_limited_by_the_coarsest_outline(self):
        coarse = _blob(n=12)
        assert mo.max_harmonics(coarse) == 6
        assert mo.choose_harmonics([_blob(), coarse]) <= 6


class TestShapePoints:
    def test_point_distances_equal_coefficient_distances(self):
        rng = np.random.default_rng(1)
        a, b = rng.normal(size=(7, 4)), rng.normal(size=(7, 4))
        m = mo.outline_points_count(7)
        pa, pb = mo.coefficients_to_points(a, m), mo.coefficients_to_points(b, m)
        assert ((pa - pb) ** 2).sum() == pytest.approx(((a - b) ** 2).sum())

    def test_too_few_points_rejected(self):
        with pytest.raises(ValueError):
            mo.coefficients_to_points(np.ones((10, 4)), 20)

    def test_pca_on_points_equals_pca_on_coefficients(self):
        """The reason the outline can ride the landmark statistics unchanged."""
        outlines = [_blob(lobes=3 + i % 3, amp=0.2 + 0.03 * i, phase=0.1 * i) for i in range(8)]
        h = 10
        m = mo.outline_points_count(h)
        coeffs = [mo.analyze_outline(o, h)["coefficients"] for o in outlines]
        points = [mo.coefficients_to_points(c, m).tolist() for c in coeffs]
        flat = [[[v] for v in c.ravel()] for c in coeffs]

        by_points = ms.do_pca_analysis(points)
        by_coeffs = ms.do_pca_analysis(flat)
        k = len(outlines) - 1
        assert np.allclose(by_points["eigenvalues"][:k], by_coeffs["eigenvalues"][:k], rtol=1e-6)
        sp = np.abs(np.array(by_points["scores"])[:, :k])
        sc = np.abs(np.array(by_coeffs["scores"])[:, :k])
        assert np.allclose(sp, sc, atol=1e-8)


class TestClosedCurveScheme:
    def test_closed_flag_travels_through_build(self):
        config = mu.build_curve_config(2, [{"n": 5, "name": "outline", "closed": True}, 4])
        assert config[0]["closed"] is True
        assert "closed" not in config[1]

    def test_scheme_entries_round_trip(self):
        config = mu.build_curve_config(0, [{"n": 5, "name": "o", "desc": "d", "closed": True}, {"n": 3}])
        rebuilt = mu.build_curve_config(0, mu.curve_scheme_entries(config))
        assert rebuilt == config


@pytest.fixture
def outline_db(bound_database, tmp_path):
    db = SqliteDatabase(str(tmp_path / "efa.db"), pragmas={"foreign_keys": 1})
    return bound_database(db, [mm.MdDataset, mm.MdObject, mm.MdImage, mm.MdThreeDModel, mm.MdAnalysis])


def _outline_dataset(n_objects=8, closed=True, dimension=2, traced=None):
    """A dataset with one fixed landmark and one outline curve."""
    ds = mm.MdDataset.create(dataset_name="Outlines", dimension=dimension)
    ds.variablename_list = ["Group"]
    ds.pack_variablename_str()
    ds.set_curve_config(mu.build_curve_config(1, [{"n": 16, "name": "margin", "closed": closed}]))
    ds.save()
    for i in range(n_objects):
        outline = _transform(
            _blob(n=120, lobes=3 + i % 2, amp=0.2 + 0.02 * i), angle=0.3 * i, scale=10 + i, shift=(200, 150)
        )
        if i % 3 == 0:
            outline = _reverse_keep_start(outline)
        obj = mm.MdObject.create(object_name=f"spec{i}", dataset=ds, sequence=i)
        obj.variable_list = ["A" if i % 2 else "B"]
        obj.pack_variable()
        obj.landmark_list = [outline[0].tolist()]
        obj.pack_landmark()
        if traced is None or i in traced:
            obj.set_curve_raw({"curve1": outline.tolist()})
        obj.save()
    ds.get_variablename_list()
    return ds


class TestOutlineDatasetOps:
    def test_shapes_are_outline_points(self, outline_db):
        ds = _outline_dataset()
        ds_ops, efa = mm.outline_dataset_ops(ds, "curve1", harmonics=8)
        assert efa["harmonics"] == 8 and efa["harmonics_auto"] is False
        assert efa["n_points"] == mo.outline_points_count(8)
        assert len(ds_ops.object_list) == 8
        for obj, entry in zip(ds_ops.object_list, efa["objects"], strict=True):
            assert len(obj.landmark_list) == efa["n_points"]
            assert len(entry["coefficients"]) == 8 * 4
            assert entry["id"] == obj.id
        assert ds_ops.wireframe.startswith("1-2,") and ds_ops.wireframe.endswith(f"{efa['n_points']}-1")

    def test_automatic_harmonics(self, outline_db):
        ds = _outline_dataset()
        _, efa = mm.outline_dataset_ops(ds, "curve1")
        assert efa["harmonics_auto"] is True
        assert efa["power_threshold"] == mo.DEFAULT_POWER_THRESHOLD
        assert 1 <= efa["harmonics"] <= mo.MAX_HARMONICS

    def test_size_is_calibrated(self, outline_db):
        ds = _outline_dataset(n_objects=2)
        obj = ds.object_list.order_by(mm.MdObject.sequence)[0]
        _, before = mm.outline_dataset_ops(ds, "curve1", harmonics=5)
        obj.pixels_per_mm = 4.0
        obj.save()
        _, after = mm.outline_dataset_ops(ds, "curve1", harmonics=5)
        assert after["objects"][0]["size"] == pytest.approx(before["objects"][0]["size"] / 4.0)

    def test_open_curve_rejected(self, outline_db):
        ds = _outline_dataset(closed=False)
        with pytest.raises(ValueError, match="not a closed outline"):
            mm.outline_dataset_ops(ds, "curve1")

    def test_untraced_objects_named(self, outline_db):
        ds = _outline_dataset(traced={0, 1, 2, 4, 5, 6, 7})
        with pytest.raises(ValueError, match="spec3"):
            mm.outline_dataset_ops(ds, "curve1")

    def test_3d_rejected(self, outline_db):
        ds = _outline_dataset(dimension=3)
        with pytest.raises(ValueError, match="2D"):
            mm.outline_dataset_ops(ds, "curve1")

    def test_closed_curve_semilandmarks_resampled_as_a_loop(self, outline_db):
        """The landmark path treats a closed curve as a loop too: no point is
        duplicated at the join."""
        ds = _outline_dataset(n_objects=1)
        ds_ops = mm.MdDatasetOps(ds)
        semis = np.array(ds_ops.object_list[0].landmark_list[1:])
        assert len(semis) == 16
        assert not np.allclose(semis[0], semis[-1])


class TestControllerOutlineAnalysis:
    def _controller(self, ds):
        from ModanController import ModanController

        controller = ModanController()
        controller.set_current_dataset(ds)
        return controller

    def test_run_analysis_stores_an_outline_analysis(self, outline_db):
        ds = _outline_dataset()
        controller = self._controller(ds)
        analysis = controller.run_analysis(
            dataset=ds,
            analysis_name="EFA",
            superimposition_method=mo.ELLIPTIC_FOURIER,
            cva_group_by=0,
            manova_group_by=0,
            outline_curve="curve1",
            harmonics=6,
        )
        assert analysis is not None
        analysis = mm.MdAnalysis.get_by_id(analysis.id)
        assert analysis.superimposition_method == mo.ELLIPTIC_FOURIER
        assert analysis.is_outline_analysis()
        efa = analysis.get_efa()
        assert efa["harmonics"] == 6 and efa["curve_id"] == "curve1"
        n_points = efa["n_points"]
        shapes = json.loads(analysis.superimposed_landmark_json)
        assert len(shapes) == 8 and all(len(s) == n_points for s in shapes)
        assert analysis.wireframe == mm.outline_loop_wireframe(n_points)
        assert analysis.baseline is None and analysis.polygons is None
        scores = json.loads(analysis.pca_analysis_result_json)
        assert len(scores) == 8
        # csize is the outline size, not the single fixed landmark's.
        info = json.loads(analysis.object_info_json)
        sizes = {o["id"]: o["size"] for o in efa["objects"]}
        assert all(entry["csize"] == pytest.approx(sizes[entry["id"]]) for entry in info)

    def test_landmark_analysis_is_untouched(self, outline_db):
        ds = _outline_dataset()
        controller = self._controller(ds)
        analysis = controller.run_analysis(dataset=ds, analysis_name="GPA", superimposition_method="Procrustes")
        assert analysis is not None
        assert not analysis.is_outline_analysis()
        assert analysis.get_efa() == {}

    def test_validation_counts_traced_outlines(self, outline_db, monkeypatch):
        import MdHelpers

        warnings = []
        monkeypatch.setattr(MdHelpers, "show_warning", lambda _parent, message: warnings.append(message))
        ds = _outline_dataset(traced={0, 1, 2})
        controller = self._controller(ds)
        assert controller.validate_dataset_for_analysis(ds, outline_curve="curve1") is False
        assert "outline traced (3)" in warnings[-1]

        ds_ok = _outline_dataset()
        assert controller.validate_dataset_for_analysis(ds_ok, outline_curve="curve1") is True

    def test_without_variables_runs_pca_only(self, outline_db, monkeypatch):
        # Like a landmark analysis (devlog 293): no variables means PCA only,
        # not a refused run.
        import MdHelpers

        monkeypatch.setattr(MdHelpers, "show_warning", lambda *a, **k: pytest.fail(f"warned: {a}"))
        ds = _outline_dataset()
        ds.propertyname_str = ""
        ds.save()
        for obj in ds.object_list:
            obj.property_str = ""
            obj.save()
        controller = self._controller(ds)
        assert controller.validate_dataset_for_analysis(ds, outline_curve="curve1") is True
        analysis = controller.run_analysis(
            dataset=ds,
            analysis_name="EFA",
            superimposition_method=mo.ELLIPTIC_FOURIER,
            cva_group_by=None,
            manova_group_by=None,
            outline_curve="curve1",
            harmonics=6,
        )
        assert analysis is not None
        assert len(json.loads(analysis.pca_analysis_result_json)) == 8
        assert not analysis.cva_analysis_result_json
        assert not analysis.manova_analysis_result_json


class TestDataExplorationOutline:
    """An outline analysis opens in Data Exploration and draws outlines."""

    def test_shapes_draw_as_closed_outlines(self, outline_db, qtbot):
        from PyQt5.QtWidgets import QApplication

        from dialogs.data_exploration_dialog import DataExplorationDialog
        from ModanController import ModanController

        QApplication.instance().remember_geometry = True
        ds = _outline_dataset()
        controller = ModanController()
        controller.set_current_dataset(ds)
        analysis = controller.run_analysis(
            dataset=ds,
            analysis_name="EFA",
            superimposition_method=mo.ELLIPTIC_FOURIER,
            cva_group_by=0,
            manova_group_by=0,
            outline_curve="curve1",
            harmonics=6,
        )
        n_points = analysis.get_efa()["n_points"]

        dialog = DataExplorationDialog(None)
        qtbot.addWidget(dialog)
        dialog.set_analysis(analysis, "PCA", "Group")
        # Every PC of the outline points is offered (not the 1 fixed landmark's 2).
        assert dialog.comboAxis2.count() == n_points * 2

        dialog.cbxShapeGrid.setChecked(True)
        dialog.prepare_scatter_data()
        dialog.show_analysis_result()

        shape = dialog.unrotate_shape(np.zeros((1, n_points * 2)))[0]
        dialog.show_shape(shape, 0)
        view = dialog.shape_view_list[0]
        assert len(view.landmark_list) == n_points
        # Drawn as a loop over the outline points; the real dataset is untouched.
        assert len(view.edge_list) == n_points
        assert view.dataset.id == -1
        assert mm.MdDataset.get_by_id(ds.id).wireframe in (None, "")
