"""Smoke / characterization test for
``DatasetAnalysisDialog.show_analysis_result``.

This plotting method had no direct end-to-end coverage. It builds ``scatter_data``
groups (via the shared ``build_scatter_group`` factory) and renders a matplotlib
scatter + legend. This test drives the real PCA path and asserts the group/legend
structures get built, guarding both the factory application (devlog 182) and the
upcoming shared legend-builder (devlog 183).

It intentionally reproduces the core of ``on_btn_analysis_clicked`` while skipping
``show_object_shape`` (object-shape GL viewers) — the scatter/legend path is what we
want to exercise.
"""

import os
from unittest.mock import Mock

import MdModel
from dialogs.dataset_analysis_dialog import DatasetAnalysisDialog
from MdModel import MdDatasetOps


def _build_dataset():
    ds = MdModel.MdDataset.create(dataset_name="AnalDS", dataset_desc="", dimension=2, propertyname_str="Sex")
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
    ds.unpack_variablename_str()  # populate ds.variablename_list for set_dataset()
    return ds


def _run_show_analysis_result(qtbot, chart_2d=True, legend=True):
    from PyQt5.QtWidgets import QApplication

    QApplication.instance().remember_geometry = True  # see test_data_exploration_scatter

    ds = _build_dataset()
    dialog = DatasetAnalysisDialog(None, ds)  # __init__ calls set_dataset(ds)
    qtbot.addWidget(dialog)

    dialog.rbPCA.setChecked(True)
    dialog.rb2DChartDim.setChecked(chart_2d)
    dialog.rb3DChartDim.setChecked(not chart_2d)
    dialog.comboPropertyName.setCurrentIndex(1)  # "Sex" -> propertyname_index 0
    dialog.cbxLegend.setChecked(legend)

    # Core of on_btn_analysis_clicked, minus show_object_shape().
    dialog.ds_ops = MdDatasetOps(ds)
    assert dialog.ds_ops.procrustes_superimposition()
    dialog.analysis_result = dialog.PerformPCA(dialog.ds_ops)
    new_coords = dialog.analysis_result.rotated_matrix.tolist()
    for i, obj in enumerate(dialog.ds_ops.object_list):
        obj.analysis_result = new_coords[i]

    dialog.show_analysis_result()
    return dialog


def test_show_analysis_result_builds_groups_and_legend(qtbot, mock_database):
    dialog = _run_show_analysis_result(qtbot, chart_2d=True, legend=True)

    # Grouped by "Sex" -> M/F groups, __default__ dropped (all objects grouped).
    assert "M" in dialog.scatter_data
    assert "F" in dialog.scatter_data
    assert "__default__" not in dialog.scatter_data
    for key in ("M", "F"):
        grp = dialog.scatter_data[key]
        assert len(grp["x_val"]) == 3
        assert grp["color"] != ""  # colour assigned
        assert grp["symbol"] != ""  # symbol assigned
        assert grp["size"] == 50

    # matplotlib scatter handles created for each non-empty group.
    assert set(dialog.scatter_result.keys()) >= {"M", "F"}


def test_show_analysis_result_3d_path(qtbot, mock_database):
    """The 3D branch (ax3) also builds groups without error."""
    dialog = _run_show_analysis_result(qtbot, chart_2d=False, legend=True)
    assert "M" in dialog.scatter_data
    assert "F" in dialog.scatter_data
    assert set(dialog.scatter_result.keys()) >= {"M", "F"}


def test_save_results_writes_xlsx(qtbot, mock_database, tmp_path, monkeypatch):
    """on_btnSaveResults_clicked exports an .xlsx via the *success* path.

    Regression for the real silent-crash root cause: show_result_table's shape
    computation is disabled (commented out), so shape_column_header_list is never set;
    accessing it in the export raised AttributeError. The Shapes sheet is now skipped
    when unavailable, so the export completes without hitting the error path."""
    from PyQt5.QtWidgets import QFileDialog, QMessageBox

    dialog = _run_show_analysis_result(qtbot, chart_2d=True)
    out = str(tmp_path / "analysis.xlsx")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (out, ""))
    crit = Mock()
    monkeypatch.setattr(QMessageBox, "critical", crit)

    dialog.on_btnSaveResults_clicked()

    assert os.path.exists(out) and os.path.getsize(out) > 0
    crit.assert_not_called()  # genuine success, not the caught-error path


def test_save_results_surfaces_error_instead_of_crashing(qtbot, mock_database, tmp_path, monkeypatch):
    """A failure mid-export must show a message box, not silently kill the dialog."""
    from PyQt5.QtWidgets import QFileDialog, QMessageBox

    dialog = _run_show_analysis_result(qtbot, chart_2d=True)
    out = str(tmp_path / "analysis.xlsx")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (out, ""))
    # Break the export partway so it raises inside the try/except.
    dialog.analysis_result = None
    crit = Mock()
    monkeypatch.setattr(QMessageBox, "critical", crit)

    dialog.on_btnSaveResults_clicked()  # must not raise

    crit.assert_called_once()
