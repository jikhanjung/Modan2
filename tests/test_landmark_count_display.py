"""Object-list landmark count: recorded number, plus a red (N) for missing."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import QRect, QSortFilterProxyModel, Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QStyle, QStyleOptionViewItem

from ModanComponents import MISSING_COUNT_ROLE, MdLandmarkCountDelegate, MdTableModel


@pytest.fixture
def model(qtbot):
    m = MdTableModel()
    m.setHorizontalHeader(["ID", "Seq", "Name", "Landmarks", "Csize"])
    m.appendRows(
        [
            [1, 1, "A", {"value": 10, "missing": 0}, 1.0],
            [2, 2, "B", {"value": 9, "missing": 1}, 1.0],
            [3, 3, "C", {"value": 2, "missing": 8}, 1.0],
        ]
    )
    return m


class TestModelRoles:
    def test_display_is_the_recorded_count(self, model):
        assert [model.data(model.index(r, 3), Qt.DisplayRole) for r in range(3)] == [10, 9, 2]

    def test_missing_count_is_exposed_separately(self, model):
        assert [model.data(model.index(r, 3), MISSING_COUNT_ROLE) for r in range(3)] == [0, 1, 8]

    def test_display_stays_an_int(self, model):
        """A composite string here would break the column's numeric sort."""
        assert all(isinstance(model.data(model.index(r, 3), Qt.DisplayRole), int) for r in range(3))

    def test_plain_cells_report_no_missing(self, model):
        assert model.data(model.index(0, 0), MISSING_COUNT_ROLE) == 0

    def test_appendrows_still_wraps_plain_values(self, model):
        assert model.data(model.index(0, 2), Qt.DisplayRole) == "A"

    def test_appendrows_preserves_changed_flag_default(self, model):
        assert model._data[1][3]["changed"] is False
        assert model._data[1][3]["missing"] == 1


class TestNumericSortPreserved:
    def test_sorts_numerically_not_lexicographically(self, model):
        proxy = QSortFilterProxyModel()
        proxy.setSourceModel(model)
        proxy.sort(3, Qt.AscendingOrder)
        # Lexicographic order would be 10, 2, 9.
        assert [proxy.data(proxy.index(r, 3)) for r in range(3)] == [2, 9, 10]


class TestDelegate:
    @pytest.fixture
    def delegate(self):
        return MdLandmarkCountDelegate(MISSING_COUNT_ROLE)

    @pytest.fixture
    def option(self):
        opt = QStyleOptionViewItem()
        opt.rect = QRect(0, 0, 120, 24)
        return opt

    def _paint(self, delegate, option, index):
        pixmap = QPixmap(200, 40)
        pixmap.fill()
        painter = QPainter(pixmap)
        try:
            delegate.paint(painter, option, index)
        finally:
            painter.end()

    def test_paints_without_missing(self, delegate, option, model):
        self._paint(delegate, option, model.index(0, 3))

    def test_paints_with_missing(self, delegate, option, model):
        self._paint(delegate, option, model.index(1, 3))

    def test_paints_when_selected(self, delegate, option, model):
        option.state |= QStyle.State_Selected
        self._paint(delegate, option, model.index(1, 3))

    def test_size_hint_grows_for_the_suffix(self, delegate, option, model):
        plain = delegate.sizeHint(option, model.index(0, 3)).width()
        annotated = delegate.sizeHint(option, model.index(2, 3)).width()
        assert annotated > plain

    def test_size_hint_unchanged_without_missing(self, delegate, option, model):
        from PyQt5.QtWidgets import QStyledItemDelegate

        base = QStyledItemDelegate().sizeHint(option, model.index(0, 3)).width()
        assert delegate.sizeHint(option, model.index(0, 3)).width() == base

    def test_tolerates_a_non_numeric_role_value(self, delegate, option, model):
        model._data[0][3]["missing"] = "oops"
        self._paint(delegate, option, model.index(0, 3))
        assert delegate._missing(model.index(0, 3)) == 0
