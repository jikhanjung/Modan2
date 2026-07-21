"""Legend arrangement in DataExplorationDialog: entry order and position.

Group keys otherwise appear in whatever order specimens were encountered in the
dataset, which is arbitrary to the reader, and a legend the user drags would be
reset by the next redraw. Both arrangements are stored on the analysis
(``chart_settings_json``) per grouping variable.
"""

import pytest
from PyQt5.QtWidgets import QApplication

import MdModel
from dialogs.data_exploration_dialog import DataExplorationDialog
from dialogs.legend_order_dialog import LegendOrderDialog
from dialogs.scatter_utils import order_legend_keys
from ModanController import ModanController


class TestOrderLegendKeys:
    """The ordering rule itself, independent of Qt."""

    def test_no_saved_order_keeps_input_order(self):
        assert order_legend_keys(["b", "a", "c"], []) == ["b", "a", "c"]
        assert order_legend_keys(["b", "a"], None) == ["b", "a"]

    def test_saved_order_is_applied(self):
        assert order_legend_keys(["b", "a", "c"], ["c", "a", "b"]) == ["c", "a", "b"]

    def test_groups_missing_from_the_order_keep_their_place_at_the_end(self):
        """A group added after the order was saved must still be listed."""
        assert order_legend_keys(["a", "b", "new"], ["b", "a"]) == ["b", "a", "new"]

    def test_stale_entries_in_the_order_are_ignored(self):
        """A renamed or deleted group must not resurrect or break ordering."""
        assert order_legend_keys(["a", "b"], ["gone", "b", "a"]) == ["b", "a"]

    def test_duplicate_keys_in_the_order_are_consumed_once(self):
        assert order_legend_keys(["a", "b"], ["a", "a", "b"]) == ["a", "b"]


def _analysis():
    ds = MdModel.MdDataset.create(dataset_name="LegendDS", dataset_desc="", dimension=2, propertyname_str="Sex")
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
    return analysis


@pytest.fixture
def dialog(qtbot, mock_database):
    QApplication.instance().remember_geometry = True
    dlg = DataExplorationDialog(None)
    qtbot.addWidget(dlg)
    dlg.set_analysis(_analysis(), "PCA", "Sex")
    dlg.comboAxis1.setCurrentIndex(dlg.comboAxis1.findData(0))
    dlg.comboAxis2.setCurrentIndex(dlg.comboAxis2.findData(1))
    dlg.update_chart()
    return dlg


class TestChartSettingsStorage:
    def test_defaults_to_empty(self, mock_database):
        analysis = MdModel.MdAnalysis.create(analysis_name="A", superimposition_method="Procrustes")
        assert analysis.get_chart_settings() == {}

    def test_round_trips_through_the_database(self, mock_database):
        analysis = MdModel.MdAnalysis.create(analysis_name="A", superimposition_method="Procrustes")
        analysis.set_chart_settings({"legend_order": {"Sex": ["M", "F"]}})
        analysis.save()

        reloaded = MdModel.MdAnalysis.get_by_id(analysis.id)
        assert reloaded.get_chart_settings() == {"legend_order": {"Sex": ["M", "F"]}}

    def test_unreadable_settings_do_not_raise(self, mock_database):
        """Cosmetics must never stop an analysis from opening."""
        analysis = MdModel.MdAnalysis.create(analysis_name="A", superimposition_method="Procrustes")
        analysis.chart_settings_json = "{not json"
        assert analysis.get_chart_settings() == {}


class TestLegendOrderInDialog:
    def test_order_is_saved_against_the_grouping_variable(self, dialog):
        dialog.save_legend_order(["F", "M"])

        stored = MdModel.MdAnalysis.get_by_id(dialog.analysis.id).get_chart_settings()
        assert stored["legend_order"] == {"Sex": ["F", "M"]}

    def test_saved_order_drives_the_legend(self, dialog):
        keys = dialog.legend_group_keys()
        assert set(keys) == {"M", "F"}

        dialog.save_legend_order(list(reversed(keys)))

        assert dialog.legend_group_keys() == list(reversed(keys))

    def test_order_for_another_grouping_variable_is_not_applied(self, dialog):
        dialog.save_legend_order(["F", "M"])
        settings = dialog.analysis.get_chart_settings()
        settings["legend_order"] = {"Locality": ["F", "M"]}
        dialog.analysis.set_chart_settings(settings)

        assert dialog.get_legend_order() == []

    def test_reordering_survives_a_redraw(self, dialog):
        dialog.save_legend_order(["F", "M"])
        dialog.update_chart()
        assert dialog.legend_group_keys() == ["F", "M"]


class TestLegendPlacement:
    def test_placement_round_trips(self, dialog):
        dialog.save_legend_placement((0.1, 0.2, 0.3, 0.4))
        assert dialog.get_legend_placement() == [0.1, 0.2, 0.3, 0.4]

    def test_malformed_placement_is_ignored(self, dialog):
        settings = dialog.analysis.get_chart_settings()
        settings["legend_placement"] = {"Sex": [1, 2]}
        dialog.analysis.set_chart_settings(settings)
        assert dialog.get_legend_placement() is None

    def test_companion_controls_follow_the_legend_checkbox(self, dialog):
        dialog.cbxLegend.setChecked(False)
        assert not dialog.cbxLegendDraggable.isEnabled()
        assert not dialog.btnLegendOrder.isEnabled()

        dialog.cbxLegend.setChecked(True)
        assert dialog.cbxLegendDraggable.isEnabled()
        assert dialog.btnLegendOrder.isEnabled()

    def test_draggable_legend_renders(self, dialog):
        """Turning dragging on must not break the redraw path."""
        dialog.cbxLegendDraggable.setChecked(True)
        dialog.update_chart()
        assert dialog.legend_group_keys()


class TestLegendOrderDialog:
    def test_returns_keys_in_list_order(self, qtbot):
        dlg = LegendOrderDialog(None, ["b", "a", "c"])
        qtbot.addWidget(dlg)
        assert dlg.ordered_keys() == ["b", "a", "c"]

    def test_sort_buttons(self, qtbot):
        dlg = LegendOrderDialog(None, ["b", "C", "a"])
        qtbot.addWidget(dlg)

        dlg.sort_entries(reverse=False)
        assert dlg.ordered_keys() == ["a", "b", "C"]

        dlg.sort_entries(reverse=True)
        assert dlg.ordered_keys() == ["C", "b", "a"]
