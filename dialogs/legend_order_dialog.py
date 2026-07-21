"""Reorder legend entries by dragging them into the order you want."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)


class LegendOrderDialog(QDialog):
    """Pick the order of legend entries for the current grouping variable.

    Groups otherwise appear in whatever order specimens happened to be
    encountered in the dataset. The chosen order is returned by
    :meth:`ordered_keys`; the caller decides where to persist it.
    """

    def __init__(self, parent, keys):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Legend Order"))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Drag entries into the order you want:")))

        self.listWidget = QListWidget()
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.listWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.listWidget.setDefaultDropAction(Qt.MoveAction)
        self.listWidget.addItems(list(keys))
        layout.addWidget(self.listWidget)

        self.btnSortAsc = QPushButton(self.tr("Sort A-Z"))
        self.btnSortAsc.clicked.connect(lambda: self.sort_entries(reverse=False))
        self.btnSortDesc = QPushButton(self.tr("Sort Z-A"))
        self.btnSortDesc.clicked.connect(lambda: self.sort_entries(reverse=True))
        shortcut_row = QHBoxLayout()
        shortcut_row.addWidget(self.btnSortAsc)
        shortcut_row.addWidget(self.btnSortDesc)
        shortcut_row.addStretch()
        layout.addLayout(shortcut_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.resize(280, 340)

    def sort_entries(self, reverse=False):
        """Alphabetical order — the common case, without dragging every row."""
        keys = sorted(self.ordered_keys(), key=str.lower, reverse=reverse)
        self.listWidget.clear()
        self.listWidget.addItems(keys)

    def ordered_keys(self):
        return [self.listWidget.item(row).text() for row in range(self.listWidget.count())]
