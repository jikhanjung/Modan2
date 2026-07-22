"""Editor for per-landmark names/abbreviations and descriptions.

Names are a dataset-wide property (indexed by landmark position), so editing
them here writes straight back to the dataset.
"""

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)


class LandmarkNameDialog(QDialog):
    """Table of landmark index / name / description for a dataset."""

    def __init__(self, parent, dataset, landmark_count=0):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Landmark Names"))
        self.dataset = dataset

        existing = dataset.get_landmark_names() if dataset is not None else []
        row_count = max(landmark_count, len(existing))

        self.table = QTableWidget(row_count, 3)
        self.table.setHorizontalHeaderLabels([self.tr("#"), self.tr("Name"), self.tr("Description")])
        self.table.verticalHeader().hide()
        for i in range(row_count):
            index_item = QTableWidgetItem(str(i + 1))
            index_item.setFlags(index_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, index_item)
            entry = existing[i] if i < len(existing) else {}
            self.table.setItem(i, 1, QTableWidgetItem(entry.get("name", "")))
            self.table.setItem(i, 2, QTableWidgetItem(entry.get("desc", "")))
        header = self.table.horizontalHeader()
        header.resizeSection(0, 40)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        self.btnOkay = QPushButton(self.tr("Save"))
        self.btnOkay.clicked.connect(self.accept_names)
        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.reject)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btnOkay)
        button_layout.addWidget(self.btnCancel)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.resize(420, 440)

    def get_names(self):
        """Collect the edited names as a list of ``{"name", "desc"}``."""
        names = []
        for i in range(self.table.rowCount()):
            name_item = self.table.item(i, 1)
            desc_item = self.table.item(i, 2)
            names.append(
                {
                    "name": name_item.text().strip() if name_item else "",
                    "desc": desc_item.text().strip() if desc_item else "",
                }
            )
        return names

    def accept_names(self):
        if self.dataset is not None:
            self.dataset.set_landmark_names(self.get_names())
            self.dataset.save()
        self.accept()
