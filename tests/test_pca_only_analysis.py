"""A dataset without variables runs a PCA-only analysis, and every analysis tab
opens Data Exploration without failing.

The validation used to refuse a dataset with no variables outright, while its
own warning said "Only PCA analysis will be available". Behind that gate, two
older failures waited: Data Exploration from the CVA tab of an analysis without
CV scores, and from the MANOVA tab of any analysis. Both raised inside a
``guard_slot`` handler, so they surfaced only as an error box and a log line;
the tests below therefore also assert that nothing was logged at ERROR.
"""

import logging

import numpy as np
import pytest
from PyQt5.QtWidgets import QMessageBox

import MdModel


def _dataset(variables=False, n=8):
    ds = MdModel.MdDataset.create(
        dataset_name="Shapes",
        dimension=2,
        landmark_count=5,
        propertyname_str="Group" if variables else "",
    )
    rng = np.random.default_rng(7)
    base = np.array([[0, 0], [10, 1], [12, 8], [5, 12], [-2, 7]], dtype=float)
    for i in range(n):
        points = base + rng.normal(scale=0.8, size=base.shape)
        landmarks = "\n".join(f"{x:.4f}\t{y:.4f}" for x, y in points)
        MdModel.MdObject.create(
            dataset=ds,
            object_name=f"obj{i}",
            sequence=i + 1,
            landmark_str=landmarks,
            property_str=("A" if i < n // 2 else "B") if variables else "",
        )
    return ds


def _run(controller, ds, group_by=None):
    controller.set_current_dataset(ds)
    return controller.run_analysis(
        dataset=ds,
        analysis_name="Analysis",
        superimposition_method="Procrustes",
        cva_group_by=group_by,
        manova_group_by=group_by,
    )


def _no_errors(caplog):
    return [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]


class TestNoVariables:
    def test_validation_accepts_a_dataset_without_variables(self, controller, monkeypatch):
        warnings = []
        monkeypatch.setattr("MdHelpers.show_warning", lambda *a, **k: warnings.append(a))
        ds = _dataset()
        assert controller.validate_dataset_for_analysis(ds) is True
        assert warnings == []

    def test_still_refuses_too_few_objects(self, controller, monkeypatch):
        monkeypatch.setattr("MdHelpers.show_warning", lambda *a, **k: None)
        assert controller.validate_dataset_for_analysis(_dataset(n=4)) is False

    def test_run_saves_pca_and_skips_cva_manova(self, controller):
        analysis = _run(controller, _dataset())
        assert analysis is not None
        assert analysis.pca_analysis_result_json
        assert not analysis.cva_analysis_result_json
        assert not analysis.manova_analysis_result_json

    def test_dialog_offers_no_grouping_variable(self, qtbot, main_window):
        from dialogs.analysis_dialog import NewAnalysisDialog

        dialog = NewAnalysisDialog(main_window, _dataset())
        qtbot.addWidget(dialog)
        for combo in (dialog.comboCvaGroupBy, dialog.comboManovaGroupBy):
            assert combo.count() == 1
            assert combo.currentData() is None
            assert not combo.isEnabled()
        dialog.set_controls_enabled(True)
        assert not dialog.comboCvaGroupBy.isEnabled()


def _show(main_window, analysis, tab, caplog):
    main_window.analysis_info_widget.set_analysis(analysis)
    main_window.analysis_info_widget.show_analysis_result()
    tabs = main_window.analysis_info_widget.analysis_tab
    tabs.setCurrentIndex([tabs.tabText(i) for i in range(tabs.count())].index(tab))
    main_window.exploration_dialog = None
    caplog.clear()  # only what the GUI path logs counts
    main_window.btnDataExploration_clicked()
    return main_window.exploration_dialog


class TestDataExplorationFromEachTab:
    @pytest.mark.parametrize("variables", [False, True])
    def test_pca_tab(self, qtbot, main_window, caplog, variables):
        analysis = _run(main_window.controller, _dataset(variables), 0 if variables else None)
        dialog = _show(main_window, analysis, "PCA", caplog)
        assert dialog is not None and dialog.analysis_method == "PCA"
        assert _no_errors(caplog) == []
        dialog.close()

    @pytest.mark.parametrize("variables", [False, True])
    def test_manova_tab_explores_the_pca_scores(self, qtbot, main_window, caplog, variables):
        analysis = _run(main_window.controller, _dataset(variables), 0 if variables else None)
        dialog = _show(main_window, analysis, "MANOVA", caplog)
        assert dialog is not None and dialog.analysis_method == "PCA"
        assert len(dialog.analysis_result_list) == 8
        assert _no_errors(caplog) == []
        dialog.close()

    def test_cva_tab_with_cv_scores(self, qtbot, main_window, caplog):
        analysis = _run(main_window.controller, _dataset(variables=True), 0)
        dialog = _show(main_window, analysis, "CVA", caplog)
        assert dialog is not None and dialog.analysis_method == "CVA"
        assert _no_errors(caplog) == []
        dialog.close()

    def test_cva_tab_without_cv_scores_says_so(self, qtbot, main_window, caplog, monkeypatch):
        shown = []
        monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: shown.append(a))
        analysis = _run(main_window.controller, _dataset())
        assert _show(main_window, analysis, "CVA", caplog) is None
        assert len(shown) == 1
        assert _no_errors(caplog) == []


class TestAnalysisDetailsFollowsTheAnalysis:
    """Analysis Details recomputes from the dataset; it used to do so with
    Procrustes whatever the stored analysis had used."""

    def _with_baseline(self):
        ds = _dataset(variables=True)
        ds.baseline = "1,2"
        ds.save()
        return ds

    @pytest.mark.parametrize("method", ["Bookstein", "Procrustes"])
    def test_opens_on_the_stored_method(self, qtbot, main_window, method):
        from dialogs.dataset_analysis_dialog import DatasetAnalysisDialog

        ds = self._with_baseline()
        dialog = DatasetAnalysisDialog(main_window, ds, method)
        qtbot.addWidget(dialog)
        assert dialog.rbBookstein.isEnabled()
        assert dialog.rbBookstein.isChecked() == (method == "Bookstein")
        if method == "Bookstein":
            # Bookstein coordinates put the baseline endpoints at (-0.5, 0), (0.5, 0).
            first = dialog.ds_ops.object_list[0].landmark_list
            assert first[0][:2] == pytest.approx([-0.5, 0.0])
            assert first[1][:2] == pytest.approx([0.5, 0.0])

    def test_without_a_baseline_falls_back_to_procrustes(self, qtbot, main_window):
        from dialogs.dataset_analysis_dialog import DatasetAnalysisDialog

        dialog = DatasetAnalysisDialog(main_window, _dataset(variables=True), "Bookstein")
        qtbot.addWidget(dialog)
        assert not dialog.rbBookstein.isEnabled()
        assert dialog.rbProcrustes.isChecked()
