"""Insert-at-position behaviour for the ObjectDialog "Add Missing" button.

Landmark identity is positional, so a placeholder is only useful if it lands
where the gap actually is.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QDialog, QTableWidget

from dialogs.object_dialog import MISSING_TEXT, ObjectDialog


class _Dataset:
    def __init__(self, dimension=2):
        self.dimension = dimension


class _View:
    def __init__(self):
        self.landmark_list = None
        self.updated = 0

    def update(self):
        self.updated += 1


def _build(qtbot, dimension=2, landmarks=None):
    dlg = ObjectDialog.__new__(ObjectDialog)
    QDialog.__init__(dlg)
    dlg.remember_geometry = False
    qtbot.addWidget(dlg)

    dlg.dataset = _Dataset(dimension)
    dlg.landmark_list = landmarks if landmarks is not None else [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
    dlg._populating_landmark_table = False
    dlg.selected_landmark_index = -1
    dlg.object_view_2d = _View()
    dlg.object_view_3d = _View()

    table = QTableWidget()
    qtbot.addWidget(table)
    table.setColumnCount(dimension)
    dlg.edtLandmarkStr = table

    # on_landmark_selected touches the coordinate input widgets; stub it out so
    # these tests stay focused on list mutation.
    from PyQt5.QtWidgets import QPushButton

    dlg.btnAddMissing = QPushButton()
    dlg.on_landmark_selected = lambda: None
    dlg.show_landmarks()
    return dlg


@pytest.fixture
def dialog(qtbot):
    return _build(qtbot)


class TestInsertPosition:
    def test_inserts_before_selected_row(self, dialog):
        dialog.selected_landmark_index = 1
        dialog.btnAddMissing_clicked()
        assert dialog.landmark_list == [[1.0, 2.0], [None, None], [3.0, 4.0], [5.0, 6.0]]

    def test_inserting_at_first_row(self, dialog):
        dialog.selected_landmark_index = 0
        dialog.btnAddMissing_clicked()
        assert dialog.landmark_list[0] == [None, None]
        assert dialog.landmark_list[1] == [1.0, 2.0]

    def test_inserting_at_last_row_pushes_it_down(self, dialog):
        dialog.selected_landmark_index = 2
        dialog.btnAddMissing_clicked()
        assert dialog.landmark_list == [[1.0, 2.0], [3.0, 4.0], [None, None], [5.0, 6.0]]

    def test_appends_when_nothing_selected(self, dialog):
        dialog.selected_landmark_index = -1
        dialog.btnAddMissing_clicked()
        assert dialog.landmark_list == [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [None, None]]

    def test_appends_when_selection_is_out_of_range(self, dialog):
        dialog.selected_landmark_index = 99
        dialog.btnAddMissing_clicked()
        assert len(dialog.landmark_list) == 4
        assert dialog.landmark_list[-1] == [None, None]

    def test_appends_on_empty_list(self, qtbot):
        dialog = _build(qtbot, landmarks=[])
        dialog.btnAddMissing_clicked()
        assert dialog.landmark_list == [[None, None]]


class TestSelectionFollowsInsertion:
    def test_new_row_becomes_selected(self, dialog):
        dialog.selected_landmark_index = 1
        dialog.btnAddMissing_clicked()
        assert dialog.selected_landmark_index == 1

    def test_consecutive_inserts_stack_in_order(self, dialog):
        """Two clicks at row 1 must not walk backwards up the list."""
        dialog.selected_landmark_index = 1
        dialog.btnAddMissing_clicked()
        dialog.btnAddMissing_clicked()
        assert dialog.landmark_list == [[1.0, 2.0], [None, None], [None, None], [3.0, 4.0], [5.0, 6.0]]

    def test_append_selects_the_appended_row(self, dialog):
        dialog.selected_landmark_index = -1
        dialog.btnAddMissing_clicked()
        assert dialog.selected_landmark_index == 3


class TestDimensions:
    def test_2d_placeholder_has_two_slots(self, dialog):
        dialog.btnAddMissing_clicked()
        assert dialog.landmark_list[-1] == [None, None]

    def test_3d_placeholder_has_three_slots(self, qtbot):
        dialog = _build(qtbot, dimension=3, landmarks=[[1.0, 2.0, 3.0]])
        dialog.btnAddMissing_clicked()
        assert dialog.landmark_list[-1] == [None, None, None]

    def test_no_dataset_is_a_noop(self, dialog):
        dialog.dataset = None
        dialog.btnAddMissing_clicked()
        assert len(dialog.landmark_list) == 3


class TestCoordinateInputsAreSynced:
    """With the real selection handler wired to real input widgets.

    selectRow emits nothing when the row was already selected, so without an
    explicit sync the inputs keep the previous landmark's values — and Update
    would write them straight into the new blank row.
    """

    @pytest.fixture
    def dialog(self, qtbot):
        from PyQt5.QtWidgets import QLineEdit, QPushButton

        dlg = ObjectDialog.__new__(ObjectDialog)
        QDialog.__init__(dlg)
        dlg.remember_geometry = False
        qtbot.addWidget(dlg)

        dlg.dataset = _Dataset(2)
        dlg.landmark_list = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        dlg._populating_landmark_table = False
        dlg.selected_landmark_index = -1
        dlg.object_view_2d = _View()
        dlg.object_view_3d = _View()

        table = QTableWidget()
        qtbot.addWidget(table)
        table.setColumnCount(2)
        dlg.edtLandmarkStr = table
        for name in ("inputX", "inputY", "inputZ"):
            setattr(dlg, name, QLineEdit())
        for name in ("btnUpdateInput", "btnDeleteInput", "btnAddInput", "btnAddMissing"):
            setattr(dlg, name, QPushButton())

        dlg.show_landmarks()
        return dlg

    def test_inputs_cleared_after_inserting_at_selected_row(self, dialog):
        dialog.edtLandmarkStr.selectRow(1)
        assert dialog.inputX.text() == "3.0"  # the row the user had selected

        dialog.btnAddMissing_clicked()

        assert dialog.landmark_list[1] == [None, None]
        # Inputs now describe the new blank row, not the pushed-down one.
        assert dialog.inputX.text() == ""
        assert dialog.inputY.text() == ""

    def test_inputs_cleared_when_appending(self, dialog):
        dialog.edtLandmarkStr.selectRow(0)
        dialog.selected_landmark_index = -1
        dialog.btnAddMissing_clicked()
        assert dialog.inputX.text() == ""


class TestButtonLabelFollowsSelection:
    """The action depends on the selection, so the label must say which one."""

    @pytest.fixture
    def dialog(self, qtbot):
        from PyQt5.QtWidgets import QLineEdit, QPushButton

        dlg = ObjectDialog.__new__(ObjectDialog)
        QDialog.__init__(dlg)
        dlg.remember_geometry = False
        qtbot.addWidget(dlg)

        dlg.dataset = _Dataset(2)
        dlg.landmark_list = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        dlg._populating_landmark_table = False
        dlg.selected_landmark_index = -1
        dlg.object_view_2d = _View()
        dlg.object_view_3d = _View()

        table = QTableWidget()
        qtbot.addWidget(table)
        table.setColumnCount(2)
        dlg.edtLandmarkStr = table
        for name in ("inputX", "inputY", "inputZ"):
            setattr(dlg, name, QLineEdit())
        for name in ("btnUpdateInput", "btnDeleteInput", "btnAddInput", "btnAddMissing"):
            setattr(dlg, name, QPushButton())

        dlg.show_landmarks()
        return dlg

    def test_says_add_when_nothing_selected(self, dialog):
        dialog._update_missing_button_text()
        assert dialog.btnAddMissing.text() == "Add Missing"

    def test_says_insert_once_a_row_is_selected(self, dialog):
        dialog.edtLandmarkStr.selectRow(1)
        assert dialog.btnAddMissing.text() == "Insert Missing"

    def test_reverts_to_add_when_selection_is_cleared(self, dialog):
        dialog.edtLandmarkStr.selectRow(1)
        assert dialog.btnAddMissing.text() == "Insert Missing"
        dialog.edtLandmarkStr.clearSelection()
        dialog.on_landmark_selected()
        assert dialog.btnAddMissing.text() == "Add Missing"

    def test_tooltip_tracks_the_label(self, dialog):
        dialog.edtLandmarkStr.selectRow(0)
        assert "Insert" in dialog.btnAddMissing.toolTip()
        dialog.edtLandmarkStr.clearSelection()
        dialog.on_landmark_selected()
        assert "Append" in dialog.btnAddMissing.toolTip()

    def test_stays_insert_after_an_insert(self, dialog):
        dialog.edtLandmarkStr.selectRow(1)
        dialog.btnAddMissing_clicked()
        # The new blank row stays selected, so another click still inserts.
        assert dialog.btnAddMissing.text() == "Insert Missing"


class TestTableAndViewers:
    def test_table_shows_the_placeholder(self, dialog):
        dialog.selected_landmark_index = 1
        dialog.btnAddMissing_clicked()
        assert dialog.edtLandmarkStr.rowCount() == 4
        assert dialog.edtLandmarkStr.item(1, 0).text() == MISSING_TEXT
        assert dialog.edtLandmarkStr.item(2, 0).text() == "3.0"

    def test_viewers_are_refreshed(self, dialog):
        dialog.btnAddMissing_clicked()
        assert dialog.object_view_2d.landmark_list is dialog.landmark_list
        assert dialog.object_view_2d.updated > 0
        assert dialog.object_view_3d.updated > 0
