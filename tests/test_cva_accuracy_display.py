"""The CVA tab shows the classification accuracy.

Every CVA run computed a cross-validated and a resubstitution accuracy, but
nothing stored them, so nothing could show them -- although the 0.2.0 release
notes said the resubstitution figure "is still shown". They are now stored on
the analysis (``cva_accuracy_json``) and summarized under the CV score plot.
"""

import json

import numpy as np
import pytest

import MdModel


def _dataset(n=12, variables=True):
    ds = MdModel.MdDataset.create(
        dataset_name="Groups", dimension=2, landmark_count=5, propertyname_str="Group" if variables else ""
    )
    rng = np.random.default_rng(11)
    base = np.array([[0, 0], [10, 1], [12, 8], [5, 12], [-2, 7]], dtype=float)
    for i in range(n):
        group = "A" if i < n // 2 else "B"
        shift = np.array([[0, 0], [0, 0], [3, 0], [0, 0], [0, 0]]) if group == "B" else 0
        points = base + shift + rng.normal(scale=0.6, size=base.shape)
        MdModel.MdObject.create(
            dataset=ds,
            object_name=f"obj{i}",
            sequence=i + 1,
            landmark_str="\n".join(f"{x:.4f}\t{y:.4f}" for x, y in points),
            property_str=group if variables else "",
        )
    return ds


def _run(controller, ds, group_by=0):
    controller.set_current_dataset(ds)
    return controller.run_analysis(
        dataset=ds,
        analysis_name="Analysis",
        superimposition_method="Procrustes",
        cva_group_by=group_by,
        manova_group_by=group_by,
    )


class TestStored:
    def test_a_cva_run_stores_its_accuracy(self, controller):
        analysis = _run(controller, _dataset())
        accuracy = MdModel.MdAnalysis.get_by_id(analysis.id).get_cva_accuracy()
        assert set(accuracy) == set(MdModel.CVA_ACCURACY_KEYS)
        assert accuracy["accuracy_method"] == "leave-one-out"
        assert accuracy["chance_accuracy"] == pytest.approx(50.0)
        assert 0 <= accuracy["cross_validated_accuracy"] <= 100
        assert accuracy["resubstitution_accuracy"] >= accuracy["cross_validated_accuracy"]

    def test_no_cva_no_accuracy(self, controller):
        analysis = _run(controller, _dataset(variables=False), group_by=None)
        assert MdModel.MdAnalysis.get_by_id(analysis.id).get_cva_accuracy() == {}

    def test_unreadable_blob_is_ignored(self, mock_database):
        ds = _dataset(n=1)
        analysis = MdModel.MdAnalysis.create(
            dataset=ds, analysis_name="x", superimposition_method="Procrustes", cva_accuracy_json="{not json"
        )
        assert analysis.get_cva_accuracy() == {}


def _shown(main_window, analysis):
    widget = main_window.analysis_info_widget
    widget.set_analysis(analysis)
    widget.show_analysis_result()
    return widget.lblCvaAccuracy.text()


class TestShown:
    def test_the_cva_tab_summarizes_the_accuracy(self, qtbot, main_window):
        analysis = _run(main_window.controller, _dataset())
        accuracy = analysis.get_cva_accuracy()
        text = _shown(main_window, analysis)
        assert text.startswith("Classification accuracy: ")
        assert f"{accuracy['cross_validated_accuracy']:.1f}% (leave-one-out cross-validation)" in text
        assert "chance 50.0%" in text
        assert f"resubstitution {accuracy['resubstitution_accuracy']:.1f}%" in text

    def test_analysis_without_cva(self, qtbot, main_window):
        analysis = _run(main_window.controller, _dataset(variables=False), group_by=None)
        assert _shown(main_window, analysis).startswith("No CVA results")

    def test_analysis_saved_before_accuracy_was_stored(self, qtbot, main_window):
        analysis = _run(main_window.controller, _dataset())
        analysis.cva_accuracy_json = None
        analysis.save()
        assert "Run it again" in _shown(main_window, analysis)

    def test_switching_to_a_legacy_analysis_clears_the_line(self, qtbot, main_window):
        widget = main_window.analysis_info_widget
        _shown(main_window, _run(main_window.controller, _dataset()))
        legacy = MdModel.MdAnalysis.create(
            dataset=_dataset(n=1), analysis_name="old", superimposition_method="Procrustes"
        )
        widget.set_analysis(legacy)
        widget.show_analysis_result()
        assert widget.lblCvaAccuracy.text() == ""


class TestText:
    @pytest.fixture
    def widget(self, qtbot, main_window):
        return main_window.analysis_info_widget

    def _accuracy(self, **overrides):
        accuracy = dict.fromkeys(MdModel.CVA_ACCURACY_KEYS)
        accuracy.update(
            cross_validated_accuracy=62.5,
            accuracy_method="leave-one-out",
            resubstitution_accuracy=90.0,
            chance_accuracy=33.3333,
            reduced=False,
        )
        accuracy.update(overrides)
        return accuracy

    def test_cross_validation_unavailable(self, widget):
        text = widget.cva_accuracy_text(
            self._accuracy(cross_validated_accuracy=None, accuracy_method="unavailable"), True
        )
        assert text.startswith("Classification accuracy: not available")
        assert "resubstitution 90.0%" in text

    def test_stratified_folds(self, widget):
        text = widget.cva_accuracy_text(self._accuracy(accuracy_method="stratified 5-fold"), True)
        assert "62.5% (stratified 5-fold cross-validation)" in text

    def test_reduced_data_says_how_many_variables(self, widget):
        text = widget.cva_accuracy_text(self._accuracy(reduced=True, n_variables_used=12, n_variables_total=40), True)
        assert text.endswith("12 of 40 variables used")

    def test_solver_warning_is_the_tooltip(self, qtbot, main_window):
        analysis = _run(main_window.controller, _dataset())
        accuracy = analysis.get_cva_accuracy()
        accuracy["warning"] = "The fast solver did not converge."
        analysis.cva_accuracy_json = json.dumps(accuracy)
        analysis.save()
        _shown(main_window, analysis)
        assert main_window.analysis_info_widget.lblCvaAccuracy.toolTip() == "The fast solver did not converge."
