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
        dialog.save_legend_placement((0.6, 0.7))
        assert dialog.get_legend_placement() == [0.6, 0.7]

    def test_malformed_placement_is_ignored(self, dialog):
        settings = dialog.analysis.get_chart_settings()
        settings["legend_placement"] = {"Sex": [1]}
        dialog.analysis.set_chart_settings(settings)
        assert dialog.get_legend_placement() is None

    def test_saved_position_is_used_when_building_the_legend(self, dialog):
        dialog.save_legend_placement((0.6, 0.7))

        kwargs = dialog.legend_placement_kwargs()

        assert kwargs["loc"] == (0.6, 0.7)
        # The default anchor must go, or it would fight the explicit position.
        assert kwargs["bbox_to_anchor"] is None

    def test_default_position_without_a_saved_one(self, dialog):
        assert dialog.legend_placement_kwargs() == {"loc": "upper right", "bbox_to_anchor": (1.05, 1)}

    def test_a_dragged_position_survives_a_redraw(self, dialog):
        """The point of saving it at all."""
        dialog.cbxLegendDraggable.setChecked(True)
        dialog.update_chart()
        dialog.save_legend_placement((0.55, 0.62))

        dialog.update_chart()

        legend = dialog.ax2.get_legend()
        assert legend is not None
        placed = dialog._legend_placement_of(legend)
        assert placed is not None
        assert placed[0] == pytest.approx(0.55, abs=0.02)
        assert placed[1] == pytest.approx(0.62, abs=0.02)

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

    def test_position_read_after_a_drag_is_usable(self, dialog):
        """Ending a drag must leave a position that can be stored and reused.

        With update="bbox" it did not: _update_bbox_to_anchor applies transAxes
        to a value already in canvas coordinates and stores the result as the
        anchor, a zero-size point holding enormous numbers. Saving that and
        applying it on the next redraw threw the legend off the canvas — an
        FT2Font "_set_transform" error, then no legend at all.
        """
        dialog.cbxLegendDraggable.setChecked(True)
        dialog.update_chart()
        legend = dialog.ax2.get_legend()
        draggable = legend.set_draggable(True, update="loc")

        # Exactly what finalize_offset does at the end of a drag.
        draggable._update_loc((500.0, 300.0))

        placement = dialog._legend_placement_of(legend)
        assert placement is not None, "a finished drag must yield a usable position"
        assert dialog._is_sane_placement(placement)

        dialog.save_legend_placement(placement)
        dialog.update_chart()  # the redraw that used to fail
        assert dialog.ax2.get_legend() is not None

    def test_a_corrupt_stored_position_is_discarded(self, dialog):
        """Anyone already carrying a bad value from 0.1.9 gets their legend back."""
        settings = dialog.analysis.get_chart_settings()
        settings["legend_placement"] = {"Sex": [170963420737.0, 61716190414.0, 0.0, 0.0]}
        dialog.analysis.set_chart_settings(settings)

        assert dialog.get_legend_placement() is None
        dialog.update_chart()
        assert dialog.ax2.get_legend() is not None

    def test_the_0_1_9_shape_is_rejected(self, dialog):
        """0.1.9 stored a four-number box; only a two-number point is valid now."""
        assert not dialog._is_sane_placement([1.05, 1.0, 0.0, 0.0])

    def test_non_finite_positions_are_rejected(self, dialog):
        assert not dialog._is_sane_placement([float("nan"), 0.2])
        assert not dialog._is_sane_placement([float("inf"), 0.2])

    def test_far_off_canvas_positions_are_rejected(self, dialog):
        assert not dialog._is_sane_placement([170963420737.0, 61716190414.0])

    def test_a_normal_position_is_accepted(self, dialog):
        assert dialog._is_sane_placement([0.6, 0.7])

    def test_saving_refuses_a_corrupt_position(self, dialog):
        dialog.save_legend_placement([170963420737.0, 61716190414.0])
        assert dialog.get_legend_placement() is None


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


class TestLegendDragDoesNotReachThePlot:
    """A press that grabs the legend belongs to the drag, not to the chart.

    Without this the same click also acted on the plot underneath — picking a
    shape, or dropping a regression line where the legend happened to sit.
    """

    @staticmethod
    def _press_at(dialog, x, y):
        from matplotlib.backend_bases import MouseButton, MouseEvent

        return MouseEvent("button_press_event", dialog.fig2.canvas, x, y, MouseButton.LEFT)

    @staticmethod
    def _legend_centre(dialog):
        box = dialog.ax2.get_legend().get_window_extent()
        return (box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2

    def test_press_on_the_legend_is_taken_by_the_drag(self, dialog):
        dialog.cbxLegendDraggable.setChecked(True)
        dialog.update_chart()
        x, y = self._legend_centre(dialog)

        dialog.on_canvas_button_press(self._press_at(dialog, x, y))

        assert dialog._legend_grabbed

    def test_press_elsewhere_reaches_the_chart(self, dialog):
        dialog.cbxLegendDraggable.setChecked(True)
        dialog.update_chart()

        dialog.on_canvas_button_press(self._press_at(dialog, 5, 5))

        assert not dialog._legend_grabbed

    def test_the_legend_is_only_grabbed_while_movable_is_on(self, dialog):
        dialog.cbxLegendDraggable.setChecked(False)
        dialog.update_chart()
        x, y = self._legend_centre(dialog)

        dialog.on_canvas_button_press(self._press_at(dialog, x, y))

        assert not dialog._legend_grabbed

    def test_release_ends_the_grab(self, dialog):
        dialog.cbxLegendDraggable.setChecked(True)
        dialog.update_chart()
        x, y = self._legend_centre(dialog)
        dialog.on_canvas_button_press(self._press_at(dialog, x, y))
        assert dialog._legend_grabbed

        dialog.on_canvas_button_release(self._press_at(dialog, x, y))

        assert not dialog._legend_grabbed, "a later click must reach the chart again"

    def test_dragging_does_not_start_shape_picking(self, dialog):
        """The visible symptom: the drag also grabbed a shape from the plot."""
        dialog.cbxLegendDraggable.setChecked(True)
        dialog.update_chart()
        dialog.is_picking_shape = False
        x, y = self._legend_centre(dialog)

        dialog.on_canvas_button_press(self._press_at(dialog, x, y))
        dialog.on_canvas_move(self._press_at(dialog, x + 20, y + 20))

        assert not dialog.is_picking_shape
