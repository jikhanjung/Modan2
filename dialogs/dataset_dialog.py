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
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QShortcut,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import MdUtils as mu
from dialogs.base_dialog import BaseDialog
from MdModel import MdDataset

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
        super().__init__(parent, title=self.tr("Modan2 - Dataset Information"))
        self.parent = parent
        self.remember_geometry = True
        self.m_app = QApplication.instance()
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
        self.lblVariableNameStr = QLabel(self.tr("Variable Names"))
        self.main_layout.addRow(self.lblParent, self.cbxParent)
        self.main_layout.addRow(self.lblDatasetName, self.edtDatasetName)
        self.main_layout.addRow(self.lblDatasetDesc, self.edtDatasetDesc)
        self.main_layout.addRow(self.lblDimension, dim_layout)
        self.main_layout.addRow(self.lblWireframe, self.edtWireframe)
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
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/DatasetDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos() + QPoint(100, 100))

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

    def Delete(self):
        """Delete dataset after confirmation."""
        ret = QMessageBox.question(
            self, "", self.tr("Are you sure to delete this dataset?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            self.dataset.delete_instance()
            self.parent.selected_dataset = None
        self.accept()

    def Cancel(self):
        """Cancel and close dialog."""
        self.reject()
