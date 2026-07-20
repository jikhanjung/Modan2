"""Commit-time validation of hand-edited ObjectDialog landmark cells.

Without validation, ``unpack_landmark`` maps every non-numeric token to ``None``,
so a typo silently converts a landmark into a missing one.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QDialog, QTableWidget, QTableWidgetItem

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


@pytest.fixture
def dialog(qtbot):
    """A minimally-wired ObjectDialog: the real table + the real handlers.

    ``ObjectDialog.__init__`` needs a full app parent, so build a bare instance
    instead. ``QDialog.__init__`` still has to run: without the C++ base
    initialised, PyQt silently drops a connection to a bound method and the slot
    never fires.
    """
    dlg = ObjectDialog.__new__(ObjectDialog)
    QDialog.__init__(dlg)
    # closeEvent -> write_settings runs when qtbot tears the widget down.
    dlg.remember_geometry = False
    qtbot.addWidget(dlg)
    dlg.dataset = _Dataset(dimension=2)
    dlg.landmark_list = [[1.0, 2.0], [3.0, 4.0], [None, None]]
    dlg._populating_landmark_table = False
    dlg.object_view_2d = _View()
    dlg.object_view_3d = _View()

    table = QTableWidget()
    qtbot.addWidget(table)
    table.setColumnCount(2)
    table.setRowCount(len(dlg.landmark_list))
    dlg.edtLandmarkStr = table

    dlg._populating_landmark_table = True
    for row, lm in enumerate(dlg.landmark_list):
        for col, value in enumerate(lm):
            table.setItem(row, col, dlg._make_landmark_item(value))
    dlg._populating_landmark_table = False

    table.itemChanged.connect(dlg.on_landmark_cell_changed)
    return dlg


def _edit(dialog, row, col, text):
    """Simulate a user committing ``text`` into a cell."""
    dialog.edtLandmarkStr.item(row, col).setText(text)


class TestAcceptedInput:
    def test_number_is_stored(self, dialog):
        _edit(dialog, 0, 0, "9.5")
        assert dialog.landmark_list[0][0] == 9.5
        assert dialog.edtLandmarkStr.item(0, 0).text() == "9.5"

    def test_negative_and_exponent(self, dialog):
        _edit(dialog, 0, 0, "-3.25")
        assert dialog.landmark_list[0][0] == -3.25
        _edit(dialog, 0, 1, "1e2")
        assert dialog.landmark_list[0][1] == 100.0

    def test_integer_is_normalised_to_float_text(self, dialog):
        _edit(dialog, 0, 0, "7")
        assert dialog.landmark_list[0][0] == 7.0
        assert dialog.edtLandmarkStr.item(0, 0).text() == "7.0"

    def test_surrounding_whitespace_tolerated(self, dialog):
        _edit(dialog, 0, 0, "  5.5  ")
        assert dialog.landmark_list[0][0] == 5.5

    def test_missing_keyword_marks_missing(self, dialog):
        _edit(dialog, 0, 0, MISSING_TEXT)
        assert dialog.landmark_list[0][0] is None
        assert dialog.edtLandmarkStr.item(0, 0).text() == MISSING_TEXT

    def test_missing_keyword_is_case_insensitive(self, dialog):
        _edit(dialog, 0, 0, "missing")
        assert dialog.landmark_list[0][0] is None
        # Normalised back to the canonical marker.
        assert dialog.edtLandmarkStr.item(0, 0).text() == MISSING_TEXT

    def test_blank_cell_counts_as_missing(self, dialog):
        _edit(dialog, 0, 0, "")
        assert dialog.landmark_list[0][0] is None
        assert dialog.edtLandmarkStr.item(0, 0).text() == MISSING_TEXT

    def test_missing_cell_can_be_given_a_value(self, dialog):
        assert dialog.landmark_list[2][0] is None
        _edit(dialog, 2, 0, "8.0")
        assert dialog.landmark_list[2][0] == 8.0


class TestRejectedInput:
    @pytest.mark.parametrize("bad", ["12.5o", "abc", "NA", "?", "1,2", "--3", "1.2.3"])
    def test_non_numeric_is_reverted(self, dialog, bad):
        _edit(dialog, 0, 0, bad)
        # Value untouched...
        assert dialog.landmark_list[0][0] == 1.0
        # ...and the cell shows the stored value again, not the typo.
        assert dialog.edtLandmarkStr.item(0, 0).text() == "1.0"

    def test_reverting_a_missing_cell_keeps_it_missing(self, dialog):
        _edit(dialog, 2, 0, "oops")
        assert dialog.landmark_list[2][0] is None
        assert dialog.edtLandmarkStr.item(2, 0).text() == MISSING_TEXT

    def test_rejection_does_not_touch_other_cells(self, dialog):
        before = [lm[:] for lm in dialog.landmark_list]
        _edit(dialog, 1, 1, "not a number")
        assert dialog.landmark_list == before


class TestViewerSync:
    def test_accepted_edit_refreshes_viewers(self, dialog):
        _edit(dialog, 0, 0, "9.5")
        assert dialog.object_view_2d.landmark_list is dialog.landmark_list
        assert dialog.object_view_2d.updated > 0
        assert dialog.object_view_3d.updated > 0

    def test_rejected_edit_does_not_refresh_viewers(self, dialog):
        _edit(dialog, 0, 0, "nope")
        assert dialog.object_view_2d.updated == 0


class TestGuardFlag:
    def test_repopulating_does_not_run_validation(self, dialog):
        """A programmatic repopulate must not be mistaken for a user edit."""
        dialog._populating_landmark_table = True
        dialog.edtLandmarkStr.item(0, 0).setText("garbage")
        dialog._populating_landmark_table = False
        # Model untouched — the validator stood down.
        assert dialog.landmark_list[0][0] == 1.0

    def test_out_of_range_cell_is_ignored(self, dialog):
        dialog.edtLandmarkStr.setRowCount(4)
        dialog.edtLandmarkStr.setItem(3, 0, QTableWidgetItem("5.0"))
        assert len(dialog.landmark_list) == 3  # no IndexError, no phantom row
