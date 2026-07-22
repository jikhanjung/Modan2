"""Dataset Dialog for creating and editing datasets."""

import logging

from peewee import DoesNotExist
from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QShortcut,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import MdUtils as mu
from dialogs.base_dialog import BaseDialog
from MdHelpers import guard_slot
from MdModel import MdDataset, delete_curve_from_dataset

logger = logging.getLogger(__name__)


class DatasetDialog(BaseDialog):
    """Dialog for creating and editing dataset information.

    Features:
    - Dataset name and description
    - Dimension selection (2D/3D)
    - Wireframe and polygon configuration
    - Variable names management
    - Parent dataset selection
    """

    def __init__(self, parent):
        """Initialize dataset dialog.

        Args:
            parent: Parent window
        """
        super().__init__(parent, title="Modan2 - Dataset Information")
        self.setWindowTitle(self.tr("Modan2 - Dataset Information"))
        self.parent = parent
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        # Controller for DB/file persistence, same pattern as ObjectDialog: fall
        # back to a standalone one when there is no real parent window (tests
        # with a Mock parent), so deletes still target the active database.
        from ModanController import ModanController

        parent_controller = getattr(parent, "controller", None)
        self.controller = parent_controller if isinstance(parent_controller, ModanController) else ModanController()
        self.read_settings()

        # Keyboard shortcut
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        self._create_widgets()
        self._create_layout()

        self.dataset = None
        self.load_parent_dataset()

    def _create_widgets(self):
        """Create UI widgets."""
        # Basic info
        self.cbxParent = QComboBox()
        self.edtDatasetName = QLineEdit()
        self.edtDatasetDesc = QLineEdit()

        # Dimension selection
        self.rbtn2D = QRadioButton("2D")
        self.rbtn2D.setChecked(True)
        self.rbtn3D = QRadioButton("3D")

        # Geometric configuration
        self.edtWireframe = QTextEdit()
        self.edtBaseline = QLineEdit()
        self.edtPolygons = QTextEdit()
        self.edtVariableNameStr = QTextEdit()

        # Semi-landmark scheme (dataset-level, shared by every specimen): how many
        # fixed landmarks come first, and the per-curve semi-landmark counts. This
        # fixes an unambiguous layout so "where do the semi-landmarks start" is the
        # same for all objects (see devlog 237).
        self.edtFixedCount = QLineEdit()
        self.edtFixedCount.setPlaceholderText(self.tr("number of fixed landmarks, e.g. 5"))
        # Curve list: id, editable name, editable semi-landmark count N.
        # Right-click a row to delete the curve from the whole dataset.
        self.curveTable = QTableWidget(0, 4)
        self.curveTable.setHorizontalHeaderLabels(
            [self.tr("Curve"), self.tr("Name"), self.tr("Description"), self.tr("N")]
        )
        self.curveTable.setMaximumHeight(140)
        self.curveTable.verticalHeader().hide()
        self.curveTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.curveTable.customContextMenuRequested.connect(self.on_curve_table_context_menu)
        # Per-landmark name/abbreviation and description (dataset-wide).
        self.landmarkNameTable = QTableWidget(0, 3)
        self.landmarkNameTable.setHorizontalHeaderLabels([self.tr("#"), self.tr("Name"), self.tr("Description")])
        self.landmarkNameTable.setMaximumHeight(200)
        self.landmarkNameTable.verticalHeader().hide()

        # Variable management
        self.lstVariableName = QListWidget()
        self.lstVariableName.setEditTriggers(
            QListWidget.DoubleClicked | QListWidget.EditKeyPressed | QListWidget.SelectedClicked
        )
        self.btnAddVariable = QPushButton(self.tr("Add Variable"))
        self.btnDeleteVariable = QPushButton(self.tr("Delete Variable"))
        self.btnMoveUp = QPushButton(self.tr("Move Up"))
        self.btnMoveDown = QPushButton(self.tr("Move Down"))

        # Connect signals
        self.btnAddVariable.clicked.connect(self.addVariable)
        self.btnDeleteVariable.clicked.connect(self.deleteVariable)
        self.btnMoveUp.clicked.connect(self.moveUp)
        self.btnMoveDown.clicked.connect(self.moveDown)

        # Action buttons
        self.btnOkay = QPushButton(self.tr("Save"))
        self.btnOkay.clicked.connect(self.Okay)
        self.btnDelete = QPushButton(self.tr("Delete"))
        self.btnDelete.clicked.connect(self.Delete)
        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.Cancel)

    def _create_layout(self):
        """Create dialog layout."""
        # Dimension layout
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(self.rbtn2D)
        dim_layout.addWidget(self.rbtn3D)

        # Variable management layout
        self.variable_button_widget = QWidget()
        self.variable_button_layout = QHBoxLayout()
        self.variable_button_widget.setLayout(self.variable_button_layout)
        self.variable_button_layout.addWidget(self.btnAddVariable)
        self.variable_button_layout.addWidget(self.btnDeleteVariable)
        self.variable_button_layout.addWidget(self.btnMoveUp)
        self.variable_button_layout.addWidget(self.btnMoveDown)

        self.variable_widget = QWidget()
        self.variable_layout = QVBoxLayout()
        self.variable_widget.setLayout(self.variable_layout)
        self.variable_layout.addWidget(self.lstVariableName)
        self.variable_layout.addWidget(self.variable_button_widget)

        # Main form layout
        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.lblParent = QLabel(self.tr("Parent"))
        self.lblDatasetName = QLabel(self.tr("Dataset Name"))
        self.lblDatasetDesc = QLabel(self.tr("Description"))
        self.lblDimension = QLabel(self.tr("Dimension"))
        self.lblWireframe = QLabel(self.tr("Wireframe"))
        self.lblBaseline = QLabel(self.tr("Baseline"))
        self.lblPolygons = QLabel(self.tr("Polygons"))
        self.lblFixedCount = QLabel(self.tr("Fixed Landmarks"))
        self.lblCurves = QLabel(self.tr("Curves"))
        self.lblLandmarkNames = QLabel(self.tr("Landmark Names"))
        self.lblVariableNameStr = QLabel(self.tr("Variable Names"))
        self.main_layout.addRow(self.lblParent, self.cbxParent)
        self.main_layout.addRow(self.lblDatasetName, self.edtDatasetName)
        self.main_layout.addRow(self.lblDatasetDesc, self.edtDatasetDesc)
        self.main_layout.addRow(self.lblDimension, dim_layout)
        self.main_layout.addRow(self.lblWireframe, self.edtWireframe)
        self.main_layout.addRow(self.lblFixedCount, self.edtFixedCount)
        self.main_layout.addRow(self.lblCurves, self.curveTable)
        self.main_layout.addRow(self.lblLandmarkNames, self.landmarkNameTable)
        self.main_layout.addRow(self.lblBaseline, self.edtBaseline)
        self.main_layout.addRow(self.lblPolygons, self.edtPolygons)
        self.main_layout.addRow(self.lblVariableNameStr, self.variable_widget)

        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnOkay)
        btn_layout.addWidget(self.btnDelete)
        btn_layout.addWidget(self.btnCancel)
        self.main_layout.addRow(btn_layout)

    def addVariable(self):
        """Add new variable to the list."""
        item = QListWidgetItem(self.tr("New Variable"))
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setData(Qt.UserRole, -1)
        self.lstVariableName.addItem(item)
        self.lstVariableName.editItem(item)

    def deleteVariable(self):
        """Delete selected variables from the list."""
        for item in self.lstVariableName.selectedItems():
            self.lstVariableName.takeItem(self.lstVariableName.row(item))

    def moveUp(self):
        """Move selected variable up in the list."""
        row = self.lstVariableName.currentRow()
        if row > 0:
            item = self.lstVariableName.takeItem(row)
            self.lstVariableName.insertItem(row - 1, item)
            self.lstVariableName.setCurrentItem(item)

    def moveDown(self):
        """Move selected variable down in the list."""
        row = self.lstVariableName.currentRow()
        if row < self.lstVariableName.count() - 1:
            item = self.lstVariableName.takeItem(row)
            self.lstVariableName.insertItem(row + 1, item)
            self.lstVariableName.setCurrentItem(item)

    def read_settings(self):
        """Read window geometry from settings."""
        self._restore_geometry("WindowGeometry/DatasetDialog", QRect(100, 100, 600, 400), QPoint(100, 100))

    def write_settings(self):
        """Save window geometry to settings."""
        if self.remember_geometry:
            self.m_app.settings.setValue("WindowGeometry/DatasetDialog", self.geometry())

    def closeEvent(self, event):
        """Handle dialog close event.

        Args:
            event: QCloseEvent
        """
        self.write_settings()
        event.accept()

    def load_parent_dataset(self, curr_dataset_id=None):
        """Load available parent datasets into combo box.

        Args:
            curr_dataset_id: Current dataset ID to exclude from list
        """
        self.cbxParent.clear()
        datasets = MdDataset.select()
        for dataset in datasets:
            if curr_dataset_id is None or dataset.id != curr_dataset_id:
                self.cbxParent.addItem(dataset.dataset_name, dataset.id)

    def read_dataset(self, dataset_id):
        """Read dataset from database by ID.

        Args:
            dataset_id: ID of dataset to read
        """
        try:
            dataset = MdDataset.get(MdDataset.id == dataset_id)
        except DoesNotExist:
            logger.warning(f"Dataset {dataset_id} not found")
            dataset = None
        self.dataset = dataset

    def set_dataset(self, dataset):
        """Set dataset to edit.

        Args:
            dataset: MdDataset to edit, or None for new dataset
        """
        if dataset is None:
            self.dataset = None
            self.cbxParent.setCurrentIndex(-1)
            return

        self.dataset = dataset
        self.load_parent_dataset(dataset.id)
        self.cbxParent.setCurrentIndex(self.cbxParent.findData(dataset.parent_id))

        self.edtDatasetName.setText(dataset.dataset_name)
        self.edtDatasetDesc.setText(dataset.dataset_desc)
        if dataset.dimension == 2:
            self.rbtn2D.setChecked(True)
        elif dataset.dimension == 3:
            self.rbtn3D.setChecked(True)

        # Disable dimension change if dataset has objects
        if len(self.dataset.object_list) > 0:
            self.rbtn2D.setEnabled(False)
            self.rbtn3D.setEnabled(False)

        self.edtWireframe.setText(dataset.wireframe)
        self.edtBaseline.setText(dataset.baseline)
        self.edtPolygons.setText(dataset.polygons)

        # Semi-landmark scheme + landmark names (both dataset-wide).
        curve_config = dataset.get_curve_config()
        self.edtFixedCount.setText(str(curve_config[0].get("start", 0)) if curve_config else "")
        self._populate_curve_table(curve_config)
        self._populate_landmark_name_table()

        # Load variable names
        variable_name_list = dataset.get_variablename_list()
        for idx, variable_name in enumerate(variable_name_list):
            item = QListWidgetItem(variable_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setData(Qt.UserRole, idx)
            self.lstVariableName.addItem(item)

    def set_parent_dataset(self, parent_dataset):
        """Set parent dataset.

        Args:
            parent_dataset: Parent MdDataset or None
        """
        if parent_dataset is None:
            self.cbxParent.setCurrentIndex(-1)
        else:
            self.cbxParent.setCurrentIndex(self.cbxParent.findData(parent_dataset.id))
            if parent_dataset.dimension == 2:
                self.rbtn2D.setChecked(True)
            elif parent_dataset.dimension == 3:
                self.rbtn3D.setChecked(True)

    @staticmethod
    def _int(text, default):
        try:
            return int((text or "").strip() or default)
        except (ValueError, AttributeError):
            return default

    def _dataset_landmark_count(self):
        """Largest landmark count across the dataset's objects (0 if none)."""
        if self.dataset is None:
            return 0
        counts = []
        for obj in self.dataset.object_list:
            obj.unpack_landmark()
            counts.append(len(obj.landmark_list))
        return max(counts) if counts else 0

    def _populate_curve_table(self, config):
        self.curveTable.setRowCount(len(config))
        for row, curve in enumerate(config):
            id_item = QTableWidgetItem(str(curve.get("id", "")))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.curveTable.setItem(row, 0, id_item)
            self.curveTable.setItem(row, 1, QTableWidgetItem(curve.get("name", "")))
            self.curveTable.setItem(row, 2, QTableWidgetItem(curve.get("desc", "")))
            self.curveTable.setItem(row, 3, QTableWidgetItem(str(curve.get("n", 0))))
        self.curveTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def _populate_landmark_name_table(self):
        existing = self.dataset.get_landmark_names() if self.dataset is not None else []
        rows = max(self._dataset_landmark_count(), len(existing))
        self.landmarkNameTable.setRowCount(rows)
        for i in range(rows):
            index_item = QTableWidgetItem(str(i + 1))
            index_item.setFlags(index_item.flags() & ~Qt.ItemIsEditable)
            self.landmarkNameTable.setItem(i, 0, index_item)
            entry = existing[i] if i < len(existing) else {}
            self.landmarkNameTable.setItem(i, 1, QTableWidgetItem(entry.get("name", "")))
            self.landmarkNameTable.setItem(i, 2, QTableWidgetItem(entry.get("desc", "")))
        header = self.landmarkNameTable.horizontalHeader()
        header.resizeSection(0, 40)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

    def _build_curve_config(self):
        """Rebuild the curve config from the fixed count and the curve table.

        Each table row is one curve; ids renumber positionally while the edited
        name and count travel with it. Counts are clamped to a minimum of 2.
        """
        fixed_count = self._int(self.edtFixedCount.text(), 0)
        curves = []
        for row in range(self.curveTable.rowCount()):
            name_item = self.curveTable.item(row, 1)
            desc_item = self.curveTable.item(row, 2)
            n_item = self.curveTable.item(row, 3)
            curves.append(
                {
                    "n": max(2, self._int(n_item.text() if n_item else "", 2)),
                    "name": name_item.text().strip() if name_item else "",
                    "desc": desc_item.text().strip() if desc_item else "",
                }
            )
        return mu.build_curve_config(fixed_count, curves)

    def _landmark_names_from_table(self):
        names = []
        for i in range(self.landmarkNameTable.rowCount()):
            name_item = self.landmarkNameTable.item(i, 1)
            desc_item = self.landmarkNameTable.item(i, 2)
            names.append(
                {
                    "name": name_item.text().strip() if name_item else "",
                    "desc": desc_item.text().strip() if desc_item else "",
                }
            )
        return names

    def on_curve_table_context_menu(self, pos):
        """Right-click a curve row to delete it from the whole dataset."""
        if self.dataset is None:
            return
        row = self.curveTable.rowAt(pos.y())
        if row < 0 or row >= self.curveTable.rowCount():
            return
        menu = QMenu(self)
        del_action = menu.addAction(self.tr("Delete Curve (all specimens)"))
        if menu.exec_(self.curveTable.viewport().mapToGlobal(pos)) is del_action:
            # Commit current table edits, then remove the curve dataset-wide.
            self.dataset.set_curve_config(self._build_curve_config())
            self.dataset.save()
            delete_curve_from_dataset(self.dataset, row)
            self._populate_curve_table(self.dataset.get_curve_config())

    def Okay(self):
        """Save dataset and close dialog."""
        try:
            logger.info("Dataset dialog Okay button pressed")

            # Create dataset if new
            if self.dataset is None:
                self.dataset = MdDataset()

            # Set basic properties
            self.dataset.parent_id = self.cbxParent.currentData()
            self.dataset.dataset_name = self.edtDatasetName.text()
            self.dataset.dataset_desc = self.edtDatasetDesc.text()
            logger.info("Dataset name: %s, Dataset desc: %s", self.dataset.dataset_name, self.dataset.dataset_desc)

            # Set dimension
            if self.rbtn2D.isChecked():
                self.dataset.dimension = 2
            elif self.rbtn3D.isChecked():
                self.dataset.dimension = 3

            # Set geometric properties
            self.dataset.wireframe = self.edtWireframe.toPlainText()
            self.dataset.baseline = self.edtBaseline.text()
            self.dataset.polygons = self.edtPolygons.toPlainText()
            # Semi-landmark curve scheme (name/count) and landmark names.
            self.dataset.set_curve_config(self._build_curve_config())
            self.dataset.set_landmark_names(self._landmark_names_from_table())
            logger.info(
                "Wireframe: %s, Baseline: %s, Polygons: %s",
                self.dataset.wireframe,
                self.dataset.baseline,
                self.dataset.polygons,
            )

            # Process variable names
            variablename_list = []
            before_index_list = []

            for idx in range(self.lstVariableName.count()):
                item = self.lstVariableName.item(idx)
                if item is None:
                    raise ValueError(f"No item found at index {idx}")

                original_index = item.data(Qt.UserRole)
                variablename_list.append(item.text())
                before_index_list.append(original_index)

            self.dataset.propertyname_str = ",".join(variablename_list)
            logger.info("variable names: %s", self.dataset.propertyname_str)

            # Update object variables if variable order changed
            for obj in self.dataset.object_list:
                variable_list = obj.get_variable_list()
                new_variable_list = []

                for before_index in before_index_list:
                    if before_index == -1:
                        new_variable_list.append("")
                    else:
                        new_variable_list.append(variable_list[before_index])

                obj.pack_variable(new_variable_list)
                obj.save()

            # Save dataset
            logger.info("Saving dataset")
            self.dataset.save()
            logger.info("Dataset saved")
            self.accept()

        except Exception as e:
            logger.error("Failed to save dataset: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to save dataset: {str(e)}")

    @guard_slot("Failed to delete dataset")
    def Delete(self):
        """Delete dataset after confirmation."""
        ret = QMessageBox.question(
            self, "", self.tr("Are you sure to delete this dataset?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            # Through the controller so the dataset's stored images, archived
            # originals and 3D models go with it; deleting the row alone left
            # the whole <storage>/<dataset_id>/ tree behind (devlog 228).
            storage_directory = getattr(self.m_app, "storage_directory", None)
            self.controller.delete_dataset(self.dataset.id, storage_directory)
            self.parent.selected_dataset = None
        self.accept()

    def Cancel(self):
        """Cancel and close dialog."""
        self.reject()
