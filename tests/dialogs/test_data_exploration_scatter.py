"""Characterization (golden-master) tests for
``DataExplorationDialog.prepare_scatter_data``.

This method has no existing direct coverage and is slated for a Batch C
decomposition (and later a shared scatter-plot builder shared with
``dataset_analysis_dialog``). These tests pin its observable output — the
``scatter_data`` / ``average_shape`` / ``regression_data`` / ``data_range``
structures it builds on ``self`` — so the refactor can be proven
behavior-preserving.

The dataset and analysis are fully deterministic (fixed landmark strings), so the
golden values below are reproducible. If PCA/library internals legitimately change
the numbers, regenerate the goldens via the commented ``print`` in
``test_prepare_scatter_data_golden`` — but a pure structural refactor of
``prepare_scatter_data`` must not.
"""

import pytest

import MdModel
from dialogs.data_exploration_dialog import DataExplorationDialog
from ModanController import ModanController

ROUND = 8


def _build_grouped_analysis():
    """Create a 6-object, 2-group, 2D dataset and run a real PCA(+CVA/MANOVA)."""
    ds = MdModel.MdDataset.create(dataset_name="ExploreDS", dataset_desc="", dimension=2, propertyname_str="Sex")
    # 6 distinct shapes, 3 landmarks each, two groups (M/F) via property_str.
    coords = [
        "1.0\t1.0\n2.0\t2.0\n3.0\t3.0",
        "1.0\t1.2\n2.1\t2.0\n3.0\t3.3",
        "1.1\t0.9\n1.9\t2.2\n3.2\t3.0",
        "0.9\t1.1\n2.0\t1.8\n2.8\t3.1",
        "1.2\t1.0\n2.2\t2.1\n3.1\t2.9",
        "0.8\t1.0\n1.8\t2.0\n3.0\t3.2",
    ]
    for i, lm in enumerate(coords):
        MdModel.MdObject.create(
            dataset=ds,
            object_name=f"O{i}",
            sequence=i + 1,
            landmark_str=lm,
            property_str=("M" if i % 2 == 0 else "F"),
        )

    controller = ModanController()
    controller.set_current_dataset(ds)
    analysis = controller.run_analysis(ds, cva_group_by=0, manova_group_by=0)
    assert analysis is not None
    assert analysis.pca_analysis_result_json  # scatter needs PCA scores
    return analysis


def _prepared_dialog(qtbot, checks=None):
    """Construct the dialog, load the analysis, set deterministic combo/checkbox
    state, and run ``prepare_scatter_data``."""
    from PyQt5.QtWidgets import QApplication

    # read_settings() (called from __init__) reads these off the app; with a None
    # parent we must take the remember_geometry=True branch (the else branch moves
    # relative to parent.pos()).
    QApplication.instance().remember_geometry = True

    analysis = _build_grouped_analysis()
    dialog = DataExplorationDialog(None)
    qtbot.addWidget(dialog)
    dialog.set_analysis(analysis, "PCA", "Sex")

    # Deterministic axes: PC1 / PC2 / PC3 (data 0 / 1 / 2).
    dialog.comboAxis1.setCurrentIndex(dialog.comboAxis1.findData(0))
    dialog.comboAxis2.setCurrentIndex(dialog.comboAxis2.findData(1))
    dialog.comboAxis3.setCurrentIndex(dialog.comboAxis3.findData(2))

    checks = checks or {}
    dialog.cbxShapeGrid.setChecked(checks.get("shape_grid", False))
    dialog.cbxConvexHull.setChecked(checks.get("convex_hull", False))
    dialog.cbxConfidenceEllipse.setChecked(checks.get("confidence_ellipse", False))
    dialog.cbxRegression.setChecked(checks.get("regression", False))

    dialog.prepare_scatter_data()
    return dialog


def _snapshot(dialog):
    """JSON-able snapshot of the scatter output for golden comparison."""

    def group_block(store):
        out = {}
        for key in sorted(store.keys()):
            v = store[key]
            block = {"color": v.get("color", ""), "symbol": v.get("symbol", "")}
            for axis in ("x_val", "y_val", "z_val"):
                val = v.get(axis)
                if isinstance(val, list):
                    block[axis] = [round(float(x), ROUND) for x in val]
                else:
                    block[axis] = round(float(val), ROUND)
            block["n_data"] = len(v.get("data", []))
            out[key] = block
        return out

    return {
        "scatter_data": group_block(dialog.scatter_data),
        "average_shape": group_block(dialog.average_shape),
        "regression_data": group_block(dialog.regression_data),
        "data_range": {k: round(float(v), ROUND) for k, v in dialog.data_range.items()},
    }


# Golden snapshot captured on the pre-refactor implementation (see module
# docstring). A pure structural refactor of prepare_scatter_data must reproduce
# these exactly (within 1e-6). Regenerate via the print in _snapshot's caller only
# if the underlying PCA/library math legitimately changes.
GOLDEN = {
    "scatter_data": {
        "F": {
            "color": "#FF0000",
            "symbol": "s",
            "x_val": [-0.09178866, -0.12508326, -0.00104061],
            "y_val": [0.00487506, -0.0015675, 0.0396063],
            "z_val": [-0.0003308, -0.00437171, 0.00460326],
            "n_data": 3,
        },
        "M": {
            "color": "#0000FF",
            "symbol": "o",
            "x_val": [0.01372182, 0.14431907, 0.05987165],
            "y_val": [-0.01070517, 0.02803998, -0.06024867],
            "z_val": [0.00432623, -0.00448432, 0.00025735],
            "n_data": 3,
        },
    },
    "average_shape": {
        "F": {"color": "", "symbol": "", "x_val": -0.07263751, "y_val": 0.01430462, "z_val": -3.308e-05, "n_data": 0},
        "M": {"color": "", "symbol": "", "x_val": 0.07263751, "y_val": -0.01430462, "z_val": 3.308e-05, "n_data": 0},
    },
    "regression_data": {
        "F": {
            "color": "#FF0000",
            "symbol": "s",
            "x_val": [-0.09178866, -0.12508326, -0.00104061],
            "y_val": [0.00487506, -0.0015675, 0.0396063],
            "z_val": [-0.0003308, -0.00437171, 0.00460326],
            "n_data": 3,
        },
        "M": {
            "color": "#0000FF",
            "symbol": "o",
            "x_val": [0.01372182, 0.14431907, 0.05987165],
            "y_val": [-0.01070517, 0.02803998, -0.06024867],
            "z_val": [0.00432623, -0.00448432, 0.00025735],
            "n_data": 3,
        },
    },
    "data_range": {
        "x_min": -0.12508326,
        "x_max": 0.14431907,
        "y_min": -0.06024867,
        "y_max": 0.0396063,
        "z_min": -0.00448432,
        "z_max": 0.00460326,
        "x_sum": 0.0,
        "y_sum": 0.0,
        "z_sum": 0.0,
        "x_avg": 0.0,
        "y_avg": 0.0,
        "z_avg": 0.0,
    },
}


def _assert_close(actual, expected, path=""):
    """Recursively compare snapshot vs golden: numbers within 1e-6, others exact."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"type mismatch at {path or '<root>'}"
        assert set(actual) == set(expected), f"key mismatch at {path or '<root>'}: {set(actual) ^ set(expected)}"
        for k in expected:
            _assert_close(actual[k], expected[k], f"{path}.{k}")
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), f"list mismatch at {path}"
        for i, (a, e) in enumerate(zip(actual, expected)):
            _assert_close(a, e, f"{path}[{i}]")
    elif isinstance(expected, bool):
        assert actual == expected, f"mismatch at {path}: {actual!r} != {expected!r}"
    elif isinstance(expected, (int, float)):
        assert actual == pytest.approx(expected, abs=1e-6), f"value mismatch at {path}: {actual} != {expected}"
    else:
        assert actual == expected, f"mismatch at {path}: {actual!r} != {expected!r}"


def test_prepare_scatter_data_golden(qtbot, mock_database):
    """Pin the full scatter output for the plain (no-overlay) path."""
    dialog = _prepared_dialog(qtbot)
    snap = _snapshot(dialog)

    # To regenerate GOLDEN after a legitimate math change:
    # print("\nGOLDEN_START", json.dumps(snap), "GOLDEN_END")

    _assert_close(snap, GOLDEN)


def test_show_analysis_result_runs_with_legend(qtbot, mock_database):
    """Drive the exploration plotting method (incl. the shared legend builder)
    after prepare_scatter_data; it must render without error and build the legend."""
    dialog = _prepared_dialog(qtbot)
    dialog.cbxLegend.setChecked(True)
    dialog.show_analysis_result()
    # scatter handles created for the M/F groups
    assert set(dialog.scatter_result.keys()) >= {"M", "F"}


def test_prepare_scatter_data_with_overlays(qtbot, mock_database):
    """Convex hull + confidence ellipse populate per-group geometry keys."""
    dialog = _prepared_dialog(qtbot, checks={"convex_hull": True, "confidence_ellipse": True})
    for key in ("M", "F"):
        grp = dialog.scatter_data[key]
        # 3 points per group (>1) -> hull + ellipse computed
        assert "hull" in grp
        assert "ellipse" in grp
        assert len(grp["ellipse"]) == 3


def test_data_point_labels_annotate_each_point(qtbot, mock_database):
    """With 'Show labels' on, every plotted point gets its object-name annotation."""
    dialog = _prepared_dialog(qtbot)
    dialog.cbxDataPointLabels.setChecked(True)
    dialog.show_analysis_result()
    texts = {t.get_text() for t in dialog.ax2.texts}
    # 6 objects O0..O5 across the two groups
    assert {f"O{i}" for i in range(6)} <= texts


def test_data_point_labels_off_by_default(qtbot, mock_database):
    """Without the option, object-name labels are not drawn."""
    dialog = _prepared_dialog(qtbot)
    assert dialog.cbxDataPointLabels.isChecked() is False
    dialog.show_analysis_result()
    texts = {t.get_text() for t in dialog.ax2.texts}
    assert not ({f"O{i}" for i in range(6)} & texts)


def test_data_point_label_helper_handles_dict_and_object():
    """The label helper reads dict 'name' and object .object_name, tolerating both."""
    assert DataExplorationDialog._data_point_label({"name": "spec-1"}) == "spec-1"
    assert DataExplorationDialog._data_point_label({}) == ""

    class _Obj:
        object_name = "spec-2"

    assert DataExplorationDialog._data_point_label(_Obj()) == "spec-2"


def test_find_nearest_data_point_snaps_and_misses(qtbot, mock_database):
    """Snapping returns the closest plotted point for a coincident cursor and
    None when the cursor is far from any point."""
    dialog = _prepared_dialog(qtbot)
    dialog.show_analysis_result()  # draw so ax2.transData is valid

    grp = dialog.scatter_data["M"]
    px, py = grp["x_val"][0], grp["y_val"][0]

    # Cursor exactly on a data point -> snaps to it (0px distance).
    nearest = dialog._find_nearest_data_point(px, py)
    assert nearest is not None
    sx, sy, obj = nearest
    assert (sx, sy) == (px, py)
    assert dialog._data_point_label(obj) == obj["name"]

    # Cursor far outside the data cloud -> no snap.
    assert dialog._find_nearest_data_point(1000.0, 1000.0) is None
