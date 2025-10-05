import logging
import os
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import xlsxwriter
from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtCore import (
    QItemSelectionModel,
    QPoint,
    QRect,
    QSize,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    QTranslator,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QDoubleValidator,
    QFont,
    QImage,
    QKeySequence,
    QPainter,
    QPen,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
)
from PyQt5.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QShortcut,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import MdUtils as mu
from MdModel import MdDataset, MdDatasetOps, MdImage, MdObject
from MdStatistics import MdCanonicalVariate, MdPrincipalComponent
from ModanComponents import NTS, TPS, X1Y1, Morphologika, ObjectViewer3D

logger = logging.getLogger(__name__)


MODE = {}
MODE["NONE"] = 0
MODE["PAN"] = 12
MODE["EDIT_LANDMARK"] = 1
MODE["WIREFRAME"] = 2
MODE["READY_MOVE_LANDMARK"] = 3
MODE["MOVE_LANDMARK"] = 4
MODE["PRE_WIRE_FROM"] = 5
MODE["CALIBRATION"] = 6
MODE["VIEW"] = 7


MODE_EXPLORATION = 0
MODE_REGRESSION = 1
# MODE_GROWTH_TRAJECTORY = 2
MODE_AVERAGE = 2
MODE_COMPARISON = 3
MODE_COMPARISON2 = 4
# MODE_GRID = 6

BASE_LANDMARK_RADIUS = 2
DISTANCE_THRESHOLD = BASE_LANDMARK_RADIUS * 3
CENTROID_SIZE_VALUE = 9999
CENTROID_SIZE_TEXT = "CSize"

# glview modes
OBJECT_MODE = 1
DATASET_MODE = 2
VIEW_MODE = 1
PAN_MODE = 2
ROTATE_MODE = 3
ZOOM_MODE = 4
LANDMARK_MODE = 1
WIREFRAME_MODE = 2
COLOR = {
    "RED": (1, 0, 0),
    "GREEN": (0, 1, 0),
    "BLUE": (0, 0, 1),
    "YELLOW": (1, 1, 0),
    "CYAN": (0, 1, 1),
    "MAGENTA": (1, 0, 1),
    "WHITE": (1, 1, 1),
    "LIGHT_GRAY": (0.8, 0.8, 0.8),
    "GRAY": (0.5, 0.5, 0.5),
    "DARK_GRAY": (0.3, 0.3, 0.3),
    "BLACK": (0, 0, 0),
}

COLOR["SINGLE_SHAPE"] = COLOR["GREEN"]
COLOR["AVERAGE_SHAPE"] = COLOR["LIGHT_GRAY"]
COLOR["NORMAL_SHAPE"] = COLOR["BLUE"]
COLOR["NORMAL_TEXT"] = COLOR["WHITE"]
COLOR["SELECTED_SHAPE"] = COLOR["RED"]
COLOR["SELECTED_TEXT"] = COLOR["RED"]
COLOR["SELECTED_LANDMARK"] = COLOR["RED"]
COLOR["WIREFRAME"] = COLOR["YELLOW"]
COLOR["SELECTED_EDGE"] = COLOR["RED"]
COLOR["BACKGROUND"] = COLOR["DARK_GRAY"]

ICON = {}
ICON["landmark"] = mu.resource_path("icons/M2Landmark_2.png")
ICON["landmark_hover"] = mu.resource_path("icons/M2Landmark_2_hover.png")
ICON["landmark_down"] = mu.resource_path("icons/M2Landmark_2_down.png")
ICON["landmark_disabled"] = mu.resource_path("icons/M2Landmark_2_disabled.png")
ICON["wireframe"] = mu.resource_path("icons/M2Wireframe_2.png")
ICON["wireframe_hover"] = mu.resource_path("icons/M2Wireframe_2_hover.png")
ICON["wireframe_down"] = mu.resource_path("icons/M2Wireframe_2_down.png")
ICON["calibration"] = mu.resource_path("icons/M2Calibration_2.png")
ICON["calibration_hover"] = mu.resource_path("icons/M2Calibration_2_hover.png")
ICON["calibration_down"] = mu.resource_path("icons/M2Calibration_2_down.png")
ICON["calibration_disabled"] = mu.resource_path("icons/M2Calibration_2_disabled.png")

NEWLINE = "\n"


class DatasetOpsViewer(QLabel):
    # clicked = pyqtSignal()
    def __init__(self, widget):
        super().__init__(widget)
        self.ds_ops = None
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.show_index = True
        self.show_wireframe = False
        self.show_baseline = False
        self.show_average = True
        # self.setMinimumSize(200,200)

    def set_ds_ops(self, ds_ops):
        self.ds_ops = ds_ops
        self.calculate_scale_and_pan()

    def calculate_scale_and_pan(self):
        min_x = 100000000
        max_x = -100000000
        min_y = 100000000
        max_y = -100000000

        # get min and max x,y from landmarks
        for obj in self.ds_ops.object_list:
            for _idx, landmark in enumerate(obj.landmark_list):
                if landmark[0] < min_x:
                    min_x = landmark[0]
                if landmark[0] > max_x:
                    max_x = landmark[0]
                if landmark[1] < min_y:
                    min_y = landmark[1]
                if landmark[1] > max_y:
                    max_y = landmark[1]
        # print("min_x:", min_x, "max_x:", max_x, "min_y:", min_y, "max_y:", max_y)
        width = max_x - min_x
        height = max_y - min_y
        w_scale = (self.width() * 1.0) / (width * 1.5)
        h_scale = (self.height() * 1.0) / (height * 1.5)
        self.scale = min(w_scale, h_scale)
        self.pan_x = -min_x * self.scale + (self.width() - width * self.scale) / 2.0
        self.pan_y = -min_y * self.scale + (self.height() - height * self.scale) / 2.0
        # print("scale:", self.scale, "pan_x:", self.pan_x, "pan_y:", self.pan_y)
        self.repaint()

    def resizeEvent(self, ev):
        # print("resizeEvent")
        self.calculate_scale_and_pan()
        self.repaint()

        return super().resizeEvent(ev)

    def paintEvent(self, event):
        # print("paint event")
        # self.pixmap
        # return super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(mu.as_qt_color(COLOR["BACKGROUND"])))

        if self.ds_ops is None:
            return

        if self.show_wireframe:
            painter.setPen(QPen(mu.as_qt_color(COLOR["WIREFRAME"]), 2))
            painter.setBrush(QBrush(mu.as_qt_color(COLOR["WIREFRAME"])))

            # print("wireframe 2", dataset.edge_list, dataset.wireframe)
            landmark_list = self.ds_ops.get_average_shape().landmark_list
            # print("landmark_list:", landmark_list)
            for wire in self.ds_ops.edge_list:
                # print("wire:", wire, landmark_list[wire[0]], landmark_list[wire[1]])

                if wire[0] >= len(landmark_list) or wire[1] >= len(landmark_list):
                    continue
                from_x = landmark_list[wire[0]][0]
                from_y = landmark_list[wire[0]][1]
                to_x = landmark_list[wire[1]][0]
                to_y = landmark_list[wire[1]][1]
                # [ from_x, from_y, from_z ] = landmark_list[wire[0]]
                # [ to_x, to_y, to_z ] = landmark_list[wire[1]]
                painter.drawLine(
                    int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y))
                )
                # painter.drawLine(self.landmark_list[wire[0]][0], self.landmark_list[wire[0]][1], self.landmark_list[wire[1]][0], self.landmark_list[wire[1]][1])

        radius = 1
        painter.setFont(QFont("Helvetica", 12))
        for obj in self.ds_ops.object_list:
            # print("obj:", obj.id)
            if obj.id in self.ds_ops.selected_object_id_list:
                painter.setPen(QPen(mu.as_qt_color(COLOR["SELECTED_SHAPE"]), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR["SELECTED_SHAPE"])))
            else:
                painter.setPen(QPen(mu.as_qt_color(COLOR["NORMAL_SHAPE"]), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR["NORMAL_SHAPE"])))
            for idx, landmark in enumerate(obj.landmark_list):
                x = self._2canx(landmark[0])
                y = self._2cany(landmark[1])
                # print("x:", x, "y:", y, "lm", landmark[0], landmark[1], "scale:", self.scale, "pan_x:", self.pan_x, "pan_y:", self.pan_y)
                painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
                # painter.drawText(x+10, y+10, str(idx+1))

        # show average shape
        if self.show_average:
            radius = 3
            for idx, landmark in enumerate(self.ds_ops.get_average_shape().landmark_list):
                painter.setPen(QPen(mu.as_qt_color(COLOR["AVERAGE_SHAPE"]), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR["AVERAGE_SHAPE"])))
                x = self._2canx(landmark[0])
                y = self._2cany(landmark[1])
                painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
                if self.show_index:
                    painter.drawText(x + 10, y + 10, str(idx + 1))

    def _2canx(self, x):
        return int(x * self.scale + self.pan_x)

    def _2cany(self, y):
        return int(y * self.scale + self.pan_y)


class PicButton(QAbstractButton):
    def __init__(self, pixmap, pixmap_hover, pixmap_pressed, pixmap_disabled=None, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.pixmap_hover = pixmap_hover
        self.pixmap_pressed = pixmap_pressed
        if pixmap_disabled is None:
            result = pixmap_hover.copy()
            image = QPixmap.toImage(result)
            grayscale = image.convertToFormat(QImage.Format_Grayscale8)
            pixmap_disabled = QPixmap.fromImage(grayscale)
            # self.Changed_view.emit(pixmap)
        self.pixmap_disabled = pixmap_disabled

        self.pressed.connect(self.update)
        self.released.connect(self.update)

    def paintEvent(self, event):
        pix = self.pixmap_hover if self.underMouse() else self.pixmap
        if self.isDown():
            pix = self.pixmap_pressed
        if not self.isEnabled() and self.pixmap_disabled is not None:
            pix = self.pixmap_disabled

        painter = QPainter(self)
        painter.drawPixmap(self.rect(), pix)

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()

    def sizeHint(self):
        return QSize(200, 200)


class ProgressDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        # self.setupUi(self)
        # self.setGeometry(200, 250, 400, 250)
        self.setWindowTitle("Modan2 - Progress Dialog")
        self.parent = parent
        self.setGeometry(QRect(100, 100, 320, 180))
        self.move(self.parent.pos() + QPoint(100, 100))

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50, 50, 50, 50)

        self.lbl_text = QLabel(self)
        # self.lbl_text.setGeometry(50, 50, 320, 80)
        # self.pb_progress = QProgressBar(self)
        self.pb_progress = QProgressBar(self)
        # self.pb_progress.setGeometry(50, 150, 320, 40)
        self.pb_progress.setValue(0)
        self.stop_progress = False
        self.btnStop = QPushButton(self)
        # self.btnStop.setGeometry(175, 200, 50, 30)
        self.btnStop.setText("Stop")
        self.btnStop.clicked.connect(self.set_stop_progress)
        self.layout.addWidget(self.lbl_text)
        self.layout.addWidget(self.pb_progress)
        self.layout.addWidget(self.btnStop)
        self.setLayout(self.layout)

    def set_stop_progress(self):
        self.stop_progress = True

    def set_progress_text(self, text_format):
        self.text_format = text_format

    def set_max_value(self, max_value):
        self.max_value = max_value

    def set_curr_value(self, curr_value):
        self.curr_value = curr_value
        self.pb_progress.setValue(int((self.curr_value / float(self.max_value)) * 100))
        self.lbl_text.setText(self.text_format.format(self.curr_value, self.max_value))
        # self.lbl_text.setText(label_text)
        self.update()
        QApplication.processEvents()


class CalibrationDialog(QDialog):
    def __init__(self, parent, dist):
        super().__init__()
        self.setWindowTitle("Calibration")
        self.parent = parent
        self.last_calibration_unit = "mm"
        # print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 320, 180))
        self.move(self.parent.pos() + QPoint(100, 100))
        self.m_app = QApplication.instance()
        self.read_settings()

        self.status_bar = QStatusBar()
        self.lblText1 = QLabel("Calibration", self)
        self.lblText2 = QLabel("Calibration", self)
        self.edtLength = QLineEdit(self)
        self.edtLength.setValidator(QDoubleValidator())
        self.edtLength.setText("1.0")
        self.edtLength.setFixedWidth(100)
        self.edtLength.setFixedHeight(30)
        self.comboUnit = QComboBox(self)
        self.comboUnit.addItem("nm")
        self.comboUnit.addItem("um")
        self.comboUnit.addItem("mm")
        self.comboUnit.addItem("cm")
        self.comboUnit.addItem("m")
        # set combUnit to last calibration unit
        self.comboUnit.setFixedWidth(100)
        self.comboUnit.setFixedHeight(30)
        self.comboUnit.setCurrentText("mm")
        self.btnOK = QPushButton("OK", self)
        self.btnOK.setFixedWidth(100)
        self.btnOK.setFixedHeight(30)
        self.btnCancel = QPushButton("Cancel", self)
        self.btnCancel.setFixedWidth(100)
        self.btnCancel.setFixedHeight(30)
        self.btnOK.clicked.connect(self.btnOK_clicked)
        self.btnCancel.clicked.connect(self.btnCancel_clicked)
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.edtLength)
        self.hbox.addWidget(self.comboUnit)
        self.hbox.addWidget(self.btnOK)
        self.hbox.addWidget(self.btnCancel)
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.lblText1)
        self.vbox.addWidget(self.lblText2)
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)
        # print("last_calibration_unit:", self.last_calibration_unit)
        self.comboUnit.setCurrentText(self.last_calibration_unit)

        if dist is not None:
            self.set_pixel_number(dist)

    def read_settings(self):
        # print("read settings")
        self.last_calibration_unit = self.m_app.settings.value("Calibration/Unit", self.last_calibration_unit)
        # print("last_calibration_unit:", self.last_calibration_unit)

    def write_settings(self):
        # print("write settings")
        self.m_app.settings.setValue("Calibration/Unit", self.last_calibration_unit)
        # print("last_calibration_unit:", self.last_calibration_unit)

    def set_pixel_number(self, pixel_number):
        self.pixel_number = pixel_number
        # show number of pixel in calibration text
        self.lblText1.setText("Enter the unit length in metric scale.")
        self.lblText2.setText(f"{self.pixel_number:.2f} pixels are equivalent to:")
        # select all text in edtLength
        self.edtLength.selectAll()

    def btnOK_clicked(self):
        # self.parent.calibration_length = float(self.edtLength.text())
        # self.parent.calibration_unit = self.cbxUnit.currentText()
        self.parent.set_object_calibration(
            self.pixel_number, float(self.edtLength.text()), self.comboUnit.currentText()
        )
        self.last_calibration_unit = self.comboUnit.currentText()
        # print("last_calibration_unit:", self.last_calibration_unit)
        self.write_settings()
        self.close()

    def btnCancel_clicked(self):
        self.close()


class DatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Dataset Information"))
        self.parent = parent
        # print(self.parent.pos())
        # self.setGeometry(QRect(100, 100, 600, 400))
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        # self.move(self.parent.pos()+QPoint(100,100))
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        self.cbxParent = QComboBox()
        self.edtDatasetName = QLineEdit()
        self.edtDatasetDesc = QLineEdit()

        self.rbtn2D = QRadioButton("2D")
        self.rbtn2D.setChecked(True)
        self.rbtn3D = QRadioButton("3D")
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(self.rbtn2D)
        dim_layout.addWidget(self.rbtn3D)

        self.edtWireframe = QTextEdit()
        self.edtBaseline = QLineEdit()
        self.edtPolygons = QTextEdit()
        self.edtVariableNameStr = QTextEdit()
        self.lstVariableName = QListWidget()
        self.lstVariableName.setEditTriggers(
            QListWidget.DoubleClicked | QListWidget.EditKeyPressed | QListWidget.SelectedClicked
        )
        self.btnAddVariable = QPushButton(self.tr("Add Variable"))
        self.btnDeleteVariable = QPushButton(self.tr("Delete Variable"))
        self.btnMoveUp = QPushButton(self.tr("Move Up"))
        self.btnMoveDown = QPushButton(self.tr("Move Down"))
        self.variable_widget = QWidget()
        self.variable_layout = QVBoxLayout()
        self.variable_widget.setLayout(self.variable_layout)

        self.btnAddVariable.clicked.connect(self.addVariable)
        self.btnDeleteVariable.clicked.connect(self.deleteVariable)
        self.btnMoveUp.clicked.connect(self.moveUp)
        self.btnMoveDown.clicked.connect(self.moveDown)

        self.variable_button_widget = QWidget()
        self.variable_button_layout = QHBoxLayout()
        self.variable_button_widget.setLayout(self.variable_button_layout)
        self.variable_button_layout.addWidget(self.btnAddVariable)
        self.variable_button_layout.addWidget(self.btnDeleteVariable)
        self.variable_button_layout.addWidget(self.btnMoveUp)
        self.variable_button_layout.addWidget(self.btnMoveDown)

        self.variable_layout.addWidget(self.lstVariableName)
        self.variable_layout.addWidget(self.variable_button_widget)

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

        self.btnOkay = QPushButton()
        self.btnOkay.setText(self.tr("Save"))
        self.btnOkay.clicked.connect(self.Okay)

        self.btnDelete = QPushButton()
        self.btnDelete.setText(self.tr("Delete"))
        self.btnDelete.clicked.connect(self.Delete)

        self.btnCancel = QPushButton()
        self.btnCancel.setText(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.Cancel)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnOkay)
        btn_layout.addWidget(self.btnDelete)
        btn_layout.addWidget(self.btnCancel)
        self.main_layout.addRow(btn_layout)

        self.dataset = None
        self.load_parent_dataset()

        # self.edtDataFolder.setText(str(self.data_folder.resolve()))
        # self.edtServerAddress.setText(self.server_address)
        # self.edtServerPort.setText(self.server_port)

    def addVariable(self):
        item = QListWidgetItem(self.tr("New Variable"))
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setData(Qt.UserRole, -1)
        self.lstVariableName.addItem(item)
        # print("new variable")
        self.lstVariableName.editItem(item)

    def deleteVariable(self):
        for item in self.lstVariableName.selectedItems():
            self.lstVariableName.takeItem(self.lstVariableName.row(item))

    def moveUp(self):
        row = self.lstVariableName.currentRow()
        if row > 0:
            item = self.lstVariableName.takeItem(row)
            self.lstVariableName.insertItem(row - 1, item)
            self.lstVariableName.setCurrentItem(item)

    def moveDown(self):
        row = self.lstVariableName.currentRow()
        if row < self.lstVariableName.count() - 1:
            item = self.lstVariableName.takeItem(row)
            self.lstVariableName.insertItem(row + 1, item)
            self.lstVariableName.setCurrentItem(item)

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/DatasetDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos() + QPoint(100, 100))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/DatasetDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def load_parent_dataset(self, curr_dataset_id=None):
        self.cbxParent.clear()
        datasets = MdDataset.select()
        for dataset in datasets:
            if curr_dataset_id is None or dataset.id != curr_dataset_id:
                self.cbxParent.addItem(dataset.dataset_name, dataset.id)

    def read_dataset(self, dataset_id):
        try:
            dataset = MdDataset.get(MdDataset.id == dataset_id)
        except DoesNotExist:
            logger.warning(f"Dataset {dataset_id} not found")
            dataset = None
        self.dataset = dataset
        # self
        # return dataset

    def set_dataset(self, dataset):
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
        # print(dataset.dimension,self.dataset.objects)
        if len(self.dataset.object_list) > 0:
            self.rbtn2D.setEnabled(False)
            self.rbtn3D.setEnabled(False)
        self.edtWireframe.setText(dataset.wireframe)
        self.edtBaseline.setText(dataset.baseline)
        self.edtPolygons.setText(dataset.polygons)
        variable_name_list = dataset.get_variablename_list()
        for idx, variable_name in enumerate(variable_name_list):
            item = QListWidgetItem(variable_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setData(Qt.UserRole, idx)
            self.lstVariableName.addItem(item)
        # self.edtVariableNameStr.setText(dataset.propertyname_str)

    def set_parent_dataset(self, parent_dataset):
        # print("parent:", parent_dataset_id, "dataset:", self.dataset)
        if parent_dataset is None:
            self.cbxParent.setCurrentIndex(-1)
        else:
            self.cbxParent.setCurrentIndex(self.cbxParent.findData(parent_dataset.id))
            if parent_dataset.dimension == 2:
                self.rbtn2D.setChecked(True)
            elif parent_dataset.dimension == 3:
                self.rbtn3D.setChecked(True)
            # self.rbtn2D.setEnabled(False)
            # self.rbtn3D.setEnabled(False)

    """
    def Okay(self):
        logger.info("Dataset dialog Okay button pressed")

        if self.dataset is None:
            self.dataset = MdDataset()
        self.dataset.parent_id = self.cbxParent.currentData()
        self.dataset.dataset_name = self.edtDatasetName.text()
        self.dataset.dataset_desc = self.edtDatasetDesc.text()
        logger.info("Dataset name: %s, Dataset desc: %s", self.dataset.dataset_name, self.dataset.dataset_desc)
        if self.rbtn2D.isChecked():
            self.dataset.dimension = 2
        elif self.rbtn3D.isChecked():
            self.dataset.dimension = 3
        self.dataset.wireframe = self.edtWireframe.toPlainText()
        self.dataset.baseline = self.edtBaseline.text()
        self.dataset.polygons = self.edtPolygons.toPlainText()
        logger.info("Wireframe: %s, Baseline: %s, Polygons: %s", self.dataset.wireframe, self.dataset.baseline, self.dataset.polygons)
        self.dataset.propertyname_str = self.edtVariableNameStr.toPlainText()
        logger.info("variable names 1: %s", self.dataset.propertyname_str)
        variablename_list = []
        before_index_list = []
        after_index_list = []
        for idx in range(self.lstVariableName.count()):
            item = self.lstVariableName.item(idx)
            original_index = item.data(Qt.UserRole)
            variablename_list.append(item.text())
            before_index_list.append(original_index)
            after_index_list.append(idx)
        #print("before_index_list:", before_index_list)
        #print("after_index_list:", after_index_list)

        self.dataset.propertyname_str = ",".join(variablename_list)
        logger.info("variable names 2: %s", self.dataset.propertyname_str)
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


        #self.data
        #print(self.dataset.dataset_desc, self.dataset.dataset_name)
        logger.info("about to save")
        self.dataset.save()
        logger.info("saved")
        self.accept()
    """

    def Okay(self):
        try:
            logger.info("Dataset dialog Okay button pressed")

            try:
                if self.dataset is None:
                    self.dataset = MdDataset()
            except Exception as e:
                logger.error("Failed to create dataset: %s", str(e))
                raise

            try:
                self.dataset.parent_id = self.cbxParent.currentData()
                self.dataset.dataset_name = self.edtDatasetName.text()
                self.dataset.dataset_desc = self.edtDatasetDesc.text()
                logger.info("Dataset name: %s, Dataset desc: %s", self.dataset.dataset_name, self.dataset.dataset_desc)
            except AttributeError as e:
                logger.error("Failed to set basic dataset properties: %s", str(e))
                raise

            try:
                if self.rbtn2D.isChecked():
                    self.dataset.dimension = 2
                elif self.rbtn3D.isChecked():
                    self.dataset.dimension = 3

                self.dataset.wireframe = self.edtWireframe.toPlainText()
                self.dataset.baseline = self.edtBaseline.text()
                self.dataset.polygons = self.edtPolygons.toPlainText()
                logger.info(
                    "Wireframe: %s, Baseline: %s, Polygons: %s",
                    self.dataset.wireframe,
                    self.dataset.baseline,
                    self.dataset.polygons,
                )
            except AttributeError as e:
                logger.error("Failed to set geometric properties: %s", str(e))
                raise

            try:
                self.dataset.propertyname_str = self.edtVariableNameStr.toPlainText()
                logger.info("variable names 1: %s", self.dataset.propertyname_str)

                variablename_list = []
                before_index_list = []
                after_index_list = []

                for idx in range(self.lstVariableName.count()):
                    try:
                        item = self.lstVariableName.item(idx)
                        if item is None:
                            raise ValueError(f"No item found at index {idx}")

                        original_index = item.data(Qt.UserRole)
                        variablename_list.append(item.text())
                        before_index_list.append(original_index)
                        after_index_list.append(idx)
                    except Exception as e:
                        logger.error("Error processing variable at index %d: %s", idx, str(e))
                        raise

                self.dataset.propertyname_str = ",".join(variablename_list)
                logger.info("variable names 2: %s", self.dataset.propertyname_str)

            except Exception as e:
                logger.error("Failed to process variable names: %s", str(e))
                raise

            try:
                for obj in self.dataset.object_list:
                    try:
                        variable_list = obj.get_variable_list()
                        new_variable_list = []

                        for before_index in before_index_list:
                            if before_index == -1:
                                new_variable_list.append("")
                            else:
                                new_variable_list.append(variable_list[before_index])

                        obj.pack_variable(new_variable_list)
                        obj.save()
                    except Exception as e:
                        logger.error("Failed to process object: %s", str(e))
                        raise

            except Exception as e:
                logger.error("Failed to process object list: %s", str(e))
                raise

            try:
                logger.info("about to save")
                self.dataset.save()
                logger.info("saved")
                self.accept()
            except Exception as e:
                logger.error("Failed to save dataset: %s", str(e))
                raise

        except Exception as e:
            logger.error("Operation failed: %s", str(e))
            # You might want to show an error dialog to the user here
            QMessageBox.critical(self, "Error", f"Failed to save dataset: {str(e)}")
            return

    def Delete(self):
        ret = QMessageBox.question(
            self, "", self.tr("Are you sure to delete this dataset?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        # print("ret:", ret)
        if ret == QMessageBox.Yes:
            self.dataset.delete_instance()
            self.parent.selected_dataset = None
            # self.dataset.delete_dataset()
        # self.delete_dataset()
        self.accept()

    def Cancel(self):
        self.reject()


class NewAnalysisDialog(QDialog):
    def __init__(self, parent, dataset):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(self.tr("Modan2 - New Analysis"))
        self.setFixedSize(500, 450)  # Increased height for progress bar

        # Center the dialog on screen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.dataset = dataset
        self.name_edited = False
        self.controller = parent.controller  # Get controller reference
        self.analysis_running = False
        self.analysis_completed = False  # Track if analysis has completed
        self.lblAnalysisName = QLabel(self.tr("Analysis name"), self)
        self.edtAnalysisName = QLineEdit(self)
        self.edtAnalysisName.textChanged.connect(self.edtAnalysisName_changed)
        self.lblSuperimposition = QLabel(self.tr("Superimposition method"), self)
        self.comboSuperimposition = QComboBox(self)
        self.comboSuperimposition.addItem(self.tr("Procrustes"))
        self.comboSuperimposition.addItem(self.tr("Bookstein"))
        self.comboSuperimposition.addItem(self.tr("Resistant Fit"))
        # self.lblOrdination = QLabel("Ordination method", self)
        # self.comboOrdination = QComboBox(self)
        # self.comboOrdination.addItem("PCA")
        # self.comboOrdination.addItem("CVA")
        # self.comboOrdination.addItem("MANOVA")
        # self.comboOrdination.currentIndexChanged.connect(self.comboOrdination_changed)
        # self.comboOrdination.addItem("MDS")
        self.lblCvaGroupBy = QLabel(self.tr("CVA grouping variable"), self)
        self.comboCvaGroupBy = QComboBox(self)
        self.lblManovaGroupBy = QLabel(self.tr("MANOVA grouping variable"), self)
        self.comboManovaGroupBy = QComboBox(self)

        valid_property_index_list = self.dataset.get_grouping_variable_index_list()
        variablename_list = self.dataset.get_variablename_list()
        # print("valid_property_index_list", valid_property_index_list, variablename_list)
        for idx in valid_property_index_list:
            property = variablename_list[idx]
            self.comboCvaGroupBy.addItem(property, idx)
            self.comboManovaGroupBy.addItem(property, idx)

        self.ignore_change = False
        # self.comboOrdination_changed()

        self.btnOK = QPushButton(self.tr("OK"), self)
        self.btnCancel = QPushButton(self.tr("Cancel"), self)
        self.btnOK.clicked.connect(self.btnOK_clicked)
        self.btnCancel.clicked.connect(self.btnCancel_clicked)

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        i = 0
        self.layout.addWidget(self.lblAnalysisName, i, 0)
        self.layout.addWidget(self.edtAnalysisName, i, 1)
        i += 1
        self.layout.addWidget(self.lblSuperimposition, i, 0)
        self.layout.addWidget(self.comboSuperimposition, i, 1)
        # i+= 1
        # self.layout.addWidget(self.lblOrdination, i, 0)
        # self.layout.addWidget(self.comboOrdination, i, 1)
        i += 1
        self.layout.addWidget(self.lblCvaGroupBy, i, 0)
        self.layout.addWidget(self.comboCvaGroupBy, i, 1)
        i += 1
        self.layout.addWidget(self.lblManovaGroupBy, i, 0)
        self.layout.addWidget(self.comboManovaGroupBy, i, 1)

        # Add progress bar and status label
        i += 1
        self.progressBar = QProgressBar(self)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.hide()  # Initially hidden
        self.layout.addWidget(self.progressBar, i, 0, 1, 2)

        i += 1
        self.lblStatus = QLabel("", self)
        self.lblStatus.setAlignment(Qt.AlignCenter)
        self.lblStatus.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        self.lblStatus.hide()  # Initially hidden
        self.layout.addWidget(self.lblStatus, i, 0, 1, 2)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.btnOK)
        self.buttonLayout.addWidget(self.btnCancel)
        i += 1
        self.layout.addWidget(QLabel(""), i, 0, 1, 2)
        i += 1
        self.layout.addLayout(self.buttonLayout, i, 0, 1, 2)
        self.get_analysis_name()

        # Store signal connections for cleanup
        self.signal_connections = []

        # Connect controller signals for progress
        if hasattr(self.controller, "analysis_progress"):
            self.signal_connections.append((self.controller.analysis_progress, self.on_analysis_progress))
            self.controller.analysis_progress.connect(self.on_analysis_progress)
        if hasattr(self.controller, "analysis_completed"):
            self.signal_connections.append((self.controller.analysis_completed, self.on_analysis_completed))
            self.controller.analysis_completed.connect(self.on_analysis_completed)
        if hasattr(self.controller, "analysis_failed"):
            self.signal_connections.append((self.controller.analysis_failed, self.on_analysis_failed))
            self.controller.analysis_failed.connect(self.on_analysis_failed)

    def edtAnalysisName_changed(self):
        if self.ignore_change is True:
            pass
        else:
            self.name_edited = True
            # print("name edited")

    def comboOrdination_changed(self):
        if self.comboOrdination.currentText() in ["CVA", "MANOVA"]:
            self.comboGroupBy.setEnabled(True)
            self.comboGroupBy.show()
            self.lblGroupBy.show()
        else:
            self.comboGroupBy.setEnabled(False)
            self.comboGroupBy.hide()
            self.lblGroupBy.hide()

    def get_analysis_name(self):
        if self.name_edited is False:
            analysis_name = "Analysis"

            analysis_name_list = [analysis.analysis_name for analysis in self.dataset.analyses]
            if analysis_name in analysis_name_list:
                analysis_name = self.get_unique_name(analysis_name, analysis_name_list)
            self.ignore_change = True
            self.edtAnalysisName.setText(analysis_name)
            self.ignore_change = False

    def btnOK_clicked(self):
        """Run analysis with progress bar"""
        if self.analysis_running:
            return

        # Validate inputs
        if not self.edtAnalysisName.text().strip():
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Please enter an analysis name"))
            return

        # Store parameters for later use
        self.analysis_name = self.edtAnalysisName.text()
        self.superimposition_method = self.comboSuperimposition.currentText()
        self.cva_group_by = self.comboCvaGroupBy.currentData()
        self.manova_group_by = self.comboManovaGroupBy.currentData()

        # Disable controls during analysis
        self.set_controls_enabled(False)
        self.analysis_running = True

        # Set wait cursor during analysis
        QApplication.setOverrideCursor(Qt.WaitCursor)

        # Show progress bar and status
        self.progressBar.show()
        self.lblStatus.show()
        self.progressBar.setValue(0)
        self.lblStatus.setText(self.tr("Validating dataset..."))

        # Change button text
        self.btnOK.setText(self.tr("Running..."))
        self.btnCancel.setText(self.tr("Close"))

        try:
            # Validate dataset
            if not self.controller.validate_dataset_for_analysis(self.dataset):
                self.on_analysis_failed(self.tr("Dataset validation failed"))
                return

            self.lblStatus.setText(self.tr("Starting analysis..."))
            QApplication.processEvents()

            # Run analysis
            self.controller.run_analysis(
                dataset=self.dataset,
                analysis_name=self.analysis_name,
                superimposition_method=self.superimposition_method,
                cva_group_by=self.cva_group_by,
                manova_group_by=self.manova_group_by,
            )

        except Exception as e:
            self.on_analysis_failed(str(e))

    def btnCancel_clicked(self):
        # Disconnect signals before closing
        self.cleanup_connections()

        if self.analysis_completed:
            # If analysis completed successfully, accept
            self.accept()
        else:
            # Otherwise reject
            self.reject()

    def set_controls_enabled(self, enabled):
        """Enable/disable input controls"""
        self.edtAnalysisName.setEnabled(enabled)
        self.comboSuperimposition.setEnabled(enabled)
        self.comboCvaGroupBy.setEnabled(enabled)
        self.comboManovaGroupBy.setEnabled(enabled)
        self.btnOK.setEnabled(enabled)

    def on_analysis_progress(self, progress):
        """Update progress bar"""
        self.progressBar.setValue(progress)

        # Update status message based on progress
        if progress < 25:
            self.lblStatus.setText(self.tr("Validating objects and landmarks..."))
        elif progress < 50:
            self.lblStatus.setText(self.tr("Performing Procrustes superimposition..."))
        elif progress < 75:
            self.lblStatus.setText(self.tr("Running PCA analysis..."))
        elif progress < 90:
            self.lblStatus.setText(self.tr("Computing CVA and MANOVA..."))
        else:
            self.lblStatus.setText(self.tr("Finalizing results..."))

        QApplication.processEvents()

    def on_analysis_completed(self, analysis):
        """Handle successful analysis completion"""
        if self.analysis_completed:  # Prevent multiple calls
            return

        self.analysis_result = analysis
        self.analysis_completed = True
        self.analysis_running = False

        # Restore normal cursor
        QApplication.restoreOverrideCursor()

        self.progressBar.setValue(100)
        self.lblStatus.setText(self.tr("Analysis completed successfully!"))
        self.lblStatus.setStyleSheet("QLabel { color: green; font-weight: bold; }")

        # Re-enable controls
        self.set_controls_enabled(True)

        # Change button text
        self.btnOK.setText(self.tr("OK"))
        self.btnOK.hide()  # Hide OK button after success
        self.btnCancel.setText(self.tr("Close"))

        # Auto-close after a short delay (with cleanup)
        QTimer.singleShot(1500, self.close_dialog)

    def on_analysis_failed(self, error_msg):
        """Handle analysis failure"""
        # Restore normal cursor
        QApplication.restoreOverrideCursor()

        self.progressBar.setValue(0)
        self.lblStatus.setText(self.tr("Analysis failed: {}").format(error_msg))
        self.lblStatus.setStyleSheet("QLabel { color: red; font-weight: bold; }")

        # Re-enable controls
        self.set_controls_enabled(True)
        self.analysis_running = False

        # Reset button text
        self.btnOK.setText(self.tr("OK"))
        self.btnCancel.setText(self.tr("Cancel"))

        QMessageBox.critical(self, self.tr("Analysis Failed"), self.tr("Analysis failed:\n{}").format(error_msg))

    def cleanup_connections(self):
        """Disconnect all signal connections to prevent errors on close"""
        # Restore cursor if still in wait state
        QApplication.restoreOverrideCursor()

        for signal, slot in self.signal_connections:
            try:
                signal.disconnect(slot)
            except TypeError:
                # Signal might already be disconnected
                pass
        self.signal_connections.clear()

    def close_dialog(self):
        """Safely close the dialog"""
        self.cleanup_connections()
        if self.analysis_completed:
            self.accept()
        else:
            self.reject()

    def closeEvent(self, event):
        """Handle dialog close event"""
        self.cleanup_connections()
        event.accept()

    def get_unique_name(self, name, name_list):
        if name not in name_list:
            return name
        else:
            i = 1
            # get last index of current name which is in the form of "name (i)" using regular expression
            match = re.match(r"(.+)\s+\((\d+)\)", name)
            if match:
                name = match.group(1)
                i = int(match.group(2))
                i += 1
            while True:
                new_name = name + " (" + str(i) + ")"
                if new_name not in name_list:
                    return new_name
                i += 1


class AnalysisResultDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Dataset Analysis"))
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.parent = parent
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        self.color_list = self.default_color_list[:]
        self.marker_list = mu.MARKER_LIST[:]
        self.plot_size = "medium"
        self.read_settings()
        # self.setGeometry(QRect(100, 100, 1400, 800))
        self.ds_ops = None
        self.object_hash = {}
        self.shape_list = []
        self.shape_name_list = []

        self.initialize_UI()

        self.main_hsplitter = QSplitter(Qt.Horizontal)

    def initialize_UI(self):
        pass


def safe_remove_artist(artist, ax=None):
    """Safely remove matplotlib artist from plot"""
    if artist is None:
        return
    try:
        artist.remove()
    except NotImplementedError:
        # For scatter plots and other collections
        if ax is not None:
            if hasattr(ax, "collections") and artist in ax.collections:
                ax.collections.remove(artist)
            elif hasattr(ax, "texts") and artist in ax.texts:
                ax.texts.remove(artist)
            elif hasattr(ax, "lines") and artist in ax.lines:
                ax.lines.remove(artist)
    except Exception:
        pass  # Silently ignore if already removed or other issues


class DatasetAnalysisDialog(QDialog):
    def __init__(self, parent, dataset):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Dataset Analysis"))
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.parent = parent
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        self.color_list = self.default_color_list[:]
        self.marker_list = mu.MARKER_LIST[:]
        self.plot_size = "medium"
        self.read_settings()
        # self.setGeometry(QRect(100, 100, 1400, 800))
        self.ds_ops = None
        self.object_hash = {}
        self.shape_list = []
        self.shape_name_list = []

        self.main_hsplitter = QSplitter(Qt.Horizontal)

        # 2d shape
        self.lblShape2 = DatasetOpsViewer(self)
        self.lblShape2.setAlignment(Qt.AlignCenter)
        self.lblShape2.setMinimumWidth(400)
        self.lblShape2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # 3d shape
        self.lblShape3 = ObjectViewer3D(self)
        self.lblShape3.setMinimumWidth(400)
        self.lblShape3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if dataset.dimension == 3:
            self.lblShape2.hide()
            self.lblShape = self.lblShape3
        else:
            self.lblShape3.hide()
            self.lblShape = self.lblShape2

        # checkboxes
        self.cbxShowIndex = QCheckBox()
        self.cbxShowIndex.setText(self.tr("Index"))
        self.cbxShowIndex.setChecked(True)
        self.cbxShowWireframe = QCheckBox()
        self.cbxShowWireframe.setText(self.tr("Wireframe"))
        self.cbxShowWireframe.setChecked(False)
        self.cbxShowBaseline = QCheckBox()
        self.cbxShowBaseline.setText(self.tr("Baseline"))
        self.cbxShowBaseline.setChecked(False)
        self.cbxShowAverage = QCheckBox()
        self.cbxShowAverage.setText(self.tr("Average"))
        self.cbxShowAverage.setChecked(True)
        self.cbxAutoRotate = QCheckBox()
        self.cbxAutoRotate.setText(self.tr("Rotate"))
        self.cbxAutoRotate.setChecked(False)

        self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        self.cbxShowAverage.stateChanged.connect(self.show_average_state_changed)
        self.cbxAutoRotate.stateChanged.connect(self.auto_rotate_state_changed)

        self.checkbox_layout = QHBoxLayout()
        self.checkbox_layout.addWidget(self.cbxShowIndex)
        self.checkbox_layout.addWidget(self.cbxShowWireframe)
        self.checkbox_layout.addWidget(self.cbxShowBaseline)
        self.checkbox_layout.addWidget(self.cbxShowAverage)
        self.checkbox_layout.addWidget(self.cbxAutoRotate)
        self.cbx_widget = QWidget()
        self.cbx_widget.setLayout(self.checkbox_layout)

        self.shape_vsplitter = QSplitter(Qt.Vertical)
        self.shape_vsplitter.addWidget(self.lblShape)
        self.shape_vsplitter.addWidget(self.cbx_widget)
        self.shape_vsplitter.setSizes([800, 20])
        self.shape_vsplitter.setStretchFactor(0, 1)
        self.shape_vsplitter.setStretchFactor(1, 0)

        self.table_widget = QWidget()
        self.table_layout = QVBoxLayout()
        self.table_widget.setLayout(self.table_layout)

        self.table_tab = QTabWidget()

        self.tableView1 = QTableView()
        self.tableView1.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView1.setSortingEnabled(True)
        self.tableView1.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView1.setSortingEnabled(True)

        self.tableView2 = QTableView()
        self.tableView2.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView2.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.table_tab.addTab(self.tableView1, self.tr("Objects"))
        self.table_tab.addTab(self.tableView2, self.tr("Groups"))
        self.table_tab.setTabVisible(1, False)
        self.table_layout.addWidget(self.table_tab)

        self.table_control_widget = QWidget()
        self.table_control_layout = QHBoxLayout()
        self.table_control_widget.setLayout(self.table_control_layout)
        self.btnSelectAll = QPushButton()
        self.btnSelectAll.setText(self.tr("All"))
        self.btnSelectAll.clicked.connect(self.select_all)
        self.btnSelectNone = QPushButton()
        self.btnSelectNone.setText(self.tr("None"))
        self.btnSelectNone.clicked.connect(self.select_none)
        self.btnSelectInvert = QPushButton()
        self.btnSelectInvert.setText(self.tr("Invert"))
        self.btnSelectInvert.clicked.connect(self.select_invert)
        self.table_control_layout.addWidget(self.btnSelectAll)
        self.table_control_layout.addWidget(self.btnSelectNone)
        self.table_control_layout.addWidget(self.btnSelectInvert)
        self.table_control_layout.addStretch(1)

        self.table_layout.addWidget(self.table_control_widget)

        # plot widgets
        self.plot_widget2 = FigureCanvas(Figure(figsize=(20, 16), dpi=100))
        self.fig2 = self.plot_widget2.figure
        self.ax2 = self.fig2.add_subplot()
        self.toolbar2 = NavigationToolbar(self.plot_widget2, self)
        self.plot_widget3 = FigureCanvas(Figure(figsize=(20, 16), dpi=100))
        self.fig3 = self.plot_widget3.figure
        self.ax3 = self.fig3.add_subplot(projection="3d")
        self.toolbar3 = NavigationToolbar(self.plot_widget3, self)

        self.plot_layout = QVBoxLayout()
        self.plot_control_layout1 = QHBoxLayout()
        self.plot_control_layout2 = QHBoxLayout()
        self.plot_control_widget1 = QWidget()
        self.plot_control_widget2 = QWidget()
        self.plot_control_widget1.setMaximumHeight(80)
        self.plot_control_widget1.setLayout(self.plot_control_layout1)
        self.plot_control_widget2.setMaximumHeight(80)
        self.plot_control_widget2.setLayout(self.plot_control_layout2)

        # chart options
        self.comboAxis1 = QComboBox()
        self.comboAxis2 = QComboBox()
        self.comboAxis3 = QComboBox()
        self.cbxFlipAxis1 = QCheckBox()
        self.cbxFlipAxis1.setText("Flip")
        self.cbxFlipAxis1.setChecked(False)
        self.cbxFlipAxis2 = QCheckBox()
        self.cbxFlipAxis2.setText("Flip")
        self.cbxFlipAxis2.setChecked(False)
        self.cbxFlipAxis3 = QCheckBox()
        self.cbxFlipAxis3.setText("Flip")
        self.cbxFlipAxis3.setChecked(False)
        self.gbAxis1 = QGroupBox()
        self.gbAxis1.setTitle("Axis 1")
        self.gbAxis1.setLayout(QHBoxLayout())
        self.gbAxis1.layout().addWidget(self.comboAxis1)
        self.gbAxis1.layout().addWidget(self.cbxFlipAxis1)
        self.gbAxis2 = QGroupBox()
        self.gbAxis2.setTitle("Axis 2")
        self.gbAxis2.setLayout(QHBoxLayout())
        self.gbAxis2.layout().addWidget(self.comboAxis2)
        self.gbAxis2.layout().addWidget(self.cbxFlipAxis2)
        self.gbAxis3 = QGroupBox()
        self.gbAxis3.setTitle("Axis 3")
        self.gbAxis3.setLayout(QHBoxLayout())
        self.gbAxis3.layout().addWidget(self.comboAxis3)
        self.gbAxis3.layout().addWidget(self.cbxFlipAxis3)
        self.plot_control_layout1.addWidget(self.gbAxis1)
        self.plot_control_layout1.addWidget(self.gbAxis2)
        self.plot_control_layout1.addWidget(self.gbAxis3)

        self.cbxFlipAxis1.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis2.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis3.stateChanged.connect(self.flip_axis_changed)

        self.rb2DChartDim = QRadioButton("2D")
        self.rb3DChartDim = QRadioButton("3D")
        self.rb2DChartDim.toggled.connect(self.on_chart_dim_changed)
        self.rb3DChartDim.toggled.connect(self.on_chart_dim_changed)
        self.cbxDepthShade = QCheckBox()
        self.cbxDepthShade.setText(self.tr("Depth Shade"))
        self.cbxDepthShade.setChecked(False)
        self.cbxDepthShade.toggled.connect(self.on_chart_dim_changed)
        self.cbxLegend = QCheckBox()
        self.cbxLegend.setText(self.tr("Legend"))
        self.cbxLegend.setChecked(False)
        self.cbxLegend.toggled.connect(self.on_chart_dim_changed)
        self.cbxAxisLabel = QCheckBox()
        self.cbxAxisLabel.setText(self.tr("Axis"))
        self.cbxAxisLabel.setChecked(True)
        self.cbxAxisLabel.toggled.connect(self.on_chart_dim_changed)
        self.gbChartDim = QGroupBox()
        self.gbChartDim.setTitle(self.tr("Chart"))
        self.gbChartDim.setLayout(QHBoxLayout())
        self.gbChartDim.layout().addWidget(self.rb2DChartDim)
        self.gbChartDim.layout().addWidget(self.rb3DChartDim)
        self.gbChartDim.layout().addWidget(self.cbxDepthShade)
        self.gbChartDim.layout().addWidget(self.cbxLegend)
        self.gbChartDim.layout().addWidget(self.cbxAxisLabel)
        self.gbGroupBy = QGroupBox()
        self.gbGroupBy.setTitle(self.tr("Grouping variable"))
        self.gbGroupBy.setLayout(QHBoxLayout())
        self.comboPropertyName = QComboBox()
        self.comboPropertyName.setCurrentIndex(-1)
        self.comboPropertyName.currentIndexChanged.connect(self.propertyname_changed)
        self.gbGroupBy.layout().addWidget(self.comboPropertyName)

        self.plot_control_layout2.addWidget(self.gbChartDim)
        self.plot_control_layout2.addWidget(self.gbGroupBy)

        self.btnChartOptions = QPushButton(self.tr("Chart Options"))
        self.btnChartOptions.clicked.connect(self.chart_options_clicked)

        self.plot_view = QWidget()
        self.plot_view.setLayout(QVBoxLayout())
        self.plot_view.layout().addWidget(self.toolbar2)
        self.plot_view.layout().addWidget(self.plot_widget2)
        self.plot_view.layout().addWidget(self.toolbar3)
        self.plot_view.layout().addWidget(self.plot_widget3)

        self.plot_tab = QTabWidget()
        self.plot_tab.addTab(self.plot_view, "Chart")
        self.plot_data = QTableWidget()
        self.plot_data.setColumnCount(10)
        self.rotation_matrix_data = QTableWidget()
        self.rotation_matrix_data.setColumnCount(10)
        self.eigenvalue_data = QTableWidget()
        self.eigenvalue_data.setColumnCount(2)
        self.shapes_data = QTableWidget()
        self.shapes_data.setColumnCount(10)

        self.plot_tab.addTab(self.plot_data, self.tr("Result table"))
        self.plot_tab.addTab(self.rotation_matrix_data, self.tr("Rotation matrix"))
        self.plot_tab.addTab(self.eigenvalue_data, self.tr("Eigenvalues"))
        self.plot_tab.addTab(self.shapes_data, self.tr("Shapes"))

        self.plot_layout.addWidget(self.plot_tab)
        # self.plot_layout.addWidget(self.toolbar2)
        # self.plot_layout.addWidget(self.plot_widget2)
        # self.plot_layout.addWidget(self.toolbar3)
        # self.plot_layout.addWidget(self.plot_widget3)
        self.plot_layout.addWidget(self.plot_control_widget1)
        self.plot_layout.addWidget(self.plot_control_widget2)
        self.plot_layout.addWidget(self.btnChartOptions)

        self.plot_all_widget = QWidget()
        self.plot_all_widget.setLayout(self.plot_layout)

        # set value 1 to 10 for axis
        for i in range(1, 11):
            self.comboAxis1.addItem("PC" + str(i))
            self.comboAxis2.addItem("PC" + str(i))
            self.comboAxis3.addItem("PC" + str(i))
        self.comboAxis1.addItem("CSize")
        self.comboAxis1.setCurrentIndex(0)
        self.comboAxis2.setCurrentIndex(1)
        self.comboAxis3.setCurrentIndex(2)
        self.comboAxis1.currentIndexChanged.connect(self.axis_changed)
        self.comboAxis2.currentIndexChanged.connect(self.axis_changed)
        self.comboAxis3.currentIndexChanged.connect(self.axis_changed)

        self.main_hsplitter.addWidget(self.shape_vsplitter)
        self.main_hsplitter.addWidget(self.table_widget)
        self.main_hsplitter.addWidget(self.plot_all_widget)

        self.main_hsplitter.setSizes([400, 200, 400])
        self.main_hsplitter.setStretchFactor(0, 1)
        self.main_hsplitter.setStretchFactor(1, 0)
        self.main_hsplitter.setStretchFactor(2, 1)

        # bottom layout
        rbbox_height = 50

        self.left_bottom_layout = QVBoxLayout()
        self.middle_bottom_layout = QVBoxLayout()
        self.right_bottom_layout = QVBoxLayout()

        self.rbProcrustes = QRadioButton("Procrustes")
        self.rbBookstein = QRadioButton("Bookstein")
        self.rbResistantFit = QRadioButton("Resistant Fit")
        self.rbProcrustes.setChecked(True)
        self.rbBookstein.setEnabled(False)
        self.rbResistantFit.setEnabled(False)
        self.btnSuperimpose = QPushButton(self.tr("Superimpose"))
        self.btnSuperimpose.clicked.connect(self.on_btnSuperimpose_clicked)
        self.gbSuperimposition = QGroupBox()
        self.gbSuperimposition.setTitle(self.tr("Superimposition"))
        self.gbSuperimposition.setLayout(QHBoxLayout())
        self.gbSuperimposition.layout().addWidget(self.rbProcrustes)
        self.gbSuperimposition.layout().addWidget(self.rbBookstein)
        self.gbSuperimposition.layout().addWidget(self.rbResistantFit)
        self.gbSuperimposition.setMaximumHeight(rbbox_height)

        self.left_bottom_layout.addWidget(self.gbSuperimposition)
        self.left_bottom_layout.addWidget(self.btnSuperimpose)

        self.rbPCA = QRadioButton("PCA")
        self.rbPCA.setChecked(True)
        self.rbPCA.toggled.connect(self.on_analysis_type_changed)
        self.rbCVA = QRadioButton("CVA")
        self.rbCVA.setEnabled(False)
        self.rbCVA.toggled.connect(self.on_analysis_type_changed)
        self.gbAnalysis = QGroupBox()
        self.gbAnalysis.setTitle("Analysis")
        self.gbAnalysis.setLayout(QHBoxLayout())
        self.gbAnalysis.layout().addWidget(self.rbPCA)
        self.gbAnalysis.layout().addWidget(self.rbCVA)
        self.gbAnalysis.setMaximumHeight(rbbox_height)
        self.btnAnalyze = QPushButton(self.tr("Perform Analysis"))
        self.btnAnalyze.clicked.connect(self.on_btn_analysis_clicked)
        self.middle_bottom_layout.addWidget(self.gbAnalysis)
        self.middle_bottom_layout.addWidget(self.btnAnalyze)

        self.empty_widget = QWidget()
        self.btnSaveResults = QPushButton(self.tr("Save Results"))
        self.btnSaveResults.clicked.connect(self.on_btnSaveResults_clicked)
        self.rb1_layout = QVBoxLayout()
        self.rb1_layout.addWidget(self.empty_widget)
        self.rb1_widget = QWidget()
        self.rb1_widget.setMinimumHeight(rbbox_height)
        self.rb1_widget.setMaximumHeight(rbbox_height)
        self.rb1_widget.setLayout(self.rb1_layout)
        self.right_bottom_layout.addWidget(self.rb1_widget)
        self.right_bottom_layout.addWidget(self.btnSaveResults)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addLayout(self.left_bottom_layout)
        self.bottom_layout.addLayout(self.middle_bottom_layout)
        self.bottom_layout.addLayout(self.right_bottom_layout)

        self.status_bar = QStatusBar()
        self.status_bar.setMaximumHeight(20)

        # final layout done
        self.main_layout = QVBoxLayout()
        self.sub_layout = QHBoxLayout()
        self.main_layout.addWidget(self.main_hsplitter)
        self.main_layout.addLayout(self.bottom_layout)
        self.main_layout.addWidget(self.status_bar)
        self.setLayout(self.main_layout)

        # initialization
        self.pca_result = None
        self.selected_object_list = []
        self.selected_object_id_list = []
        self.scatter_result = {}
        self.scatter_data = {}

        self.show_chart_options = True
        self.selection_changed_off = False
        self.onpick_happened = False

        self.analysis_type = "PCA"
        self.analysis_done = False

        # data setting
        set_result = self.set_dataset(dataset)
        # print("set dataset result: ", set_result)
        if set_result is False:
            self.close()
            return
        elif set_result is None:
            self.close()
            return
        else:
            self.reset_tableView()
            self.load_object()
            self.chart_options_clicked()
            self.rb3DChartDim.setChecked(True)
            self.on_chart_dim_changed()
            self.on_btn_analysis_clicked()

            self.btnSaveResults.setFocus()

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        self.plot_size = self.m_app.settings.value("PlotSize", self.plot_size)
        for i in range(len(self.color_list)):
            self.color_list[i] = self.m_app.settings.value("DataPointColor/" + str(i), self.default_color_list[i])
        for i in range(len(self.marker_list)):
            self.marker_list[i] = self.m_app.settings.value("DataPointMarker/" + str(i), self.marker_list[i])

        if self.remember_geometry is True:
            self.setGeometry(
                self.m_app.settings.value("WindowGeometry/DatasetAnalysisWindow", QRect(100, 100, 1400, 800))
            )
        else:
            self.setGeometry(QRect(100, 100, 1400, 800))
            self.move(self.parent.pos() + QPoint(50, 50))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/DatasetAnalysisWindow", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def on_analysis_type_changed(self):
        self.analysis_done = False
        axis1 = self.comboAxis1.currentIndex()
        axis2 = self.comboAxis2.currentIndex()
        axis3 = self.comboAxis3.currentIndex()
        self.comboAxis1.clear()
        self.comboAxis2.clear()
        self.comboAxis3.clear()
        if self.rbPCA.isChecked():
            header = "PC"
        else:
            header = "CV"

        for i in range(1, 11):
            self.comboAxis1.addItem(header + str(i))
            self.comboAxis2.addItem(header + str(i))
            self.comboAxis3.addItem(header + str(i))
        self.comboAxis1.setCurrentIndex(axis1)
        self.comboAxis2.setCurrentIndex(axis2)
        self.comboAxis3.setCurrentIndex(axis3)
        # self.reset_tableView()
        # self.load_object()
        # self.on_btn_analysis_clicked()

    def select_all(self):
        pass

    def select_none(self):
        pass

    def select_invert(self):
        pass

    def chart_options_clicked(self):
        self.show_chart_options = not self.show_chart_options
        if self.show_chart_options:
            # self.gbChartOptions.show()
            self.plot_control_widget1.show()
            self.plot_control_widget2.show()
        else:
            # self.gbChartOptions.hide()
            self.plot_control_widget1.hide()
            self.plot_control_widget2.hide()

    def on_chart_dim_changed(self):
        if self.rb2DChartDim.isChecked():
            self.plot_widget3.hide()
            self.plot_widget2.show()
            self.toolbar2.show()
            self.toolbar3.hide()
            self.gbAxis3.hide()
            self.comboAxis3.hide()
            self.cbxFlipAxis3.hide()
            self.cbxDepthShade.hide()
        else:
            self.plot_widget2.hide()
            self.plot_widget3.show()
            self.toolbar2.hide()
            self.toolbar3.show()
            self.gbAxis3.show()
            self.comboAxis3.show()
            self.cbxFlipAxis3.show()
            self.cbxDepthShade.show()

        if self.ds_ops is not None:
            self.show_analysis_result()

    def set_dataset(self, dataset):
        # print("dataset:", dataset)
        self.dataset = dataset
        prev_lm_count = -1
        for obj in dataset.object_list:
            obj.unpack_landmark()
            obj.unpack_variable()
            # print("property:", obj.variable_list)
            lm_count = len(obj.landmark_list)
            # print("prev_lm_count:", prev_lm_count, "lm_count:", lm_count)
            if prev_lm_count != lm_count and prev_lm_count != -1:
                # show messagebox and close the window
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText(self.tr("Error: landmark count is not consistent"))
                msg.setWindowTitle("Error")
                msg.exec_()
                self.close()
                return False
            prev_lm_count = lm_count

        self.comboPropertyName.clear()
        self.comboPropertyName.addItem("Select Property")
        if len(self.dataset.variablename_list) > 0:
            for propertyname in self.dataset.variablename_list:
                self.comboPropertyName.addItem(propertyname)
                # self.comboAxis2.addItem(propertyname)
        self.comboPropertyName.setCurrentIndex(0)
        self.comboPropertyName.currentIndexChanged.connect(self.propertyname_changed)
        if self.dataset.dimension == 3:
            self.cbxAutoRotate.show()
        else:
            self.cbxAutoRotate.hide()

        self.show_index_state_changed()
        self.show_wireframe_state_changed()
        self.show_baseline_state_changed()
        self.show_average_state_changed()
        self.auto_rotate_state_changed
        # self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        # self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        # self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        # self.cbxShowAverage.stateChanged.connect(self.show_average_state_changed)
        # self.cbxAutoRotate.stateChanged.connect(self.auto_rotate_state_changed)
        return True

    def propertyname_changed(self):
        perform_analysis = False
        if self.comboPropertyName.currentIndex() > 0:
            self.rbCVA.setEnabled(True)
            self.cbxLegend.setChecked(True)
            perform_analysis = True
        else:
            self.rbCVA.setEnabled(False)
            self.cbxLegend.setChecked(False)

        if self.ds_ops is not None:
            self.reset_tableView()
            self.load_object()
            if perform_analysis:
                self.on_btn_analysis_clicked()
            self.show_analysis_result()

    def axis_changed(self):
        if self.ds_ops is not None and self.analysis_done is True:
            self.show_analysis_result()

    def flip_axis_changed(self, int):
        if self.ds_ops is not None:
            self.show_analysis_result()

    def on_btnSuperimpose_clicked(self):
        logger = logging.getLogger(__name__)
        logger.debug("on_btnSuperimpose_clicked")

    def on_btnAnalyze_clicked(self):
        # print("on_btnAnalyze_clicked")
        self.selected_object_id_list = []
        self.ds_ops.selected_object_id_list = self.selected_object_id_list
        self.load_object()
        self.on_object_selection_changed([], [])
        self.show_analysis_result()
        self.show_object_shape()

    def on_btnSaveResults_clicked(self):
        today = datetime.datetime.now()
        date_str = today.strftime("%Y%m%d_%H%M%S")

        filename_candidate = f"{self.ds_ops.dataset_name}_analysis_{date_str}.xlsx"
        filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
        # print("filepath:", filepath)
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Save File As"), filepath, "Excel format (*.xlsx)")
        if filename:
            # print("filename:", filename)
            doc = xlsxwriter.Workbook(filename)

            # PCA result
            property_count = len(self.ds_ops.variablename_list)
            header = ["object_name", *self.ds_ops.variablename_list]
            header.extend(
                [
                    self.analysis_type[:2] + str(i + 1)
                    for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))
                ]
            )
            header.extend("CSize")
            worksheet = doc.add_worksheet("Result coordinates")
            row_index = 0
            column_index = 0

            for colname in header:
                worksheet.write(row_index, column_index, colname)
                column_index += 1

            new_coords = self.analysis_result.rotated_matrix.tolist()
            for i, obj in enumerate(self.ds_ops.object_list):
                worksheet.write(i + 1, 0, obj.object_name)
                # print(obj.variable_list)
                for j in range(property_count):
                    # for j, property in enumerate(obj.variable_list):
                    worksheet.write(i + 1, j + 1, obj.variable_list[j])

                for k, val in enumerate(new_coords[i]):
                    worksheet.write(i + 1, k + property_count + 1, val)
                    # self.plot_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))
                obj = MdObject.get_by_id(obj.id)
                worksheet.write(i + 1, k + property_count + 2, obj.get_centroid_size(True))

            worksheet = doc.add_worksheet("Rotation matrix")
            row_index = 0
            column_index = 0
            rotation_matrix = self.analysis_result.rotation_matrix.tolist()
            # print("rotation_matrix[0][0]", [0][0], len(self.pca_result.rotation_matrix[0][0]))
            for i, row in enumerate(rotation_matrix):
                for j, val in enumerate(row):
                    worksheet.write(i, j, val)

            worksheet = doc.add_worksheet("Eigenvalues")
            for i, val in enumerate(self.analysis_result.raw_eigen_values):
                val2 = self.analysis_result.eigen_value_percentages[i]
                worksheet.write(i, 0, val)
                worksheet.write(i, 1, val2)

            # PCA result
            # header = [ "object_name", *self.ds_ops.variablename_list ]
            # header.extend( [self.analysis_type[:2]+str(i+1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))] )
            worksheet = doc.add_worksheet("Shapes")
            row_index = 0
            column_index = 0
            for i, colname in enumerate(self.shape_column_header_list):
                worksheet.write(row_index, i, colname)
                # column_index+=1

            for i, shape in enumerate(self.shape_list.tolist()):
                worksheet.write(i + 1, 0, self.shape_name_list[i])
                for j, val in enumerate(shape):
                    worksheet.write(i + 1, j + 1, val)
                    # self.shapes_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))

            doc.close()

        # print("on_btnSaveResults_clicked")

    def show_index_state_changed(self):
        if self.cbxShowIndex.isChecked():
            self.lblShape.show_index = True
            # print("show index CHECKED!")
        else:
            self.lblShape.show_index = False
            # print("show index UNCHECKED!")
        self.lblShape.update()

    def show_average_state_changed(self):
        if self.cbxShowAverage.isChecked():
            self.lblShape.show_average = True
            # print("show index CHECKED!")
        else:
            self.lblShape.show_average = False
            # print("show index UNCHECKED!")
        self.lblShape.update()

    def auto_rotate_state_changed(self):
        # print("auto_rotate_state_changed", self.cbxAutoRotate.isChecked())
        if self.cbxAutoRotate.isChecked():
            self.lblShape.auto_rotate = True
            # print("auto rotate CHECKED!")
        else:
            self.lblShape.auto_rotate = False
            # print("auto rotate UNCHECKED!")
        self.lblShape.update()

    def show_wireframe_state_changed(self):
        if self.cbxShowWireframe.isChecked():
            self.lblShape.show_wireframe = True
            # print("show index CHECKED!")
        else:
            self.lblShape.show_wireframe = False
            # print("show index UNCHECKED!")
        self.lblShape.update()

    def show_baseline_state_changed(self):
        if self.cbxShowBaseline.isChecked():
            self.lblShape.show_baseline = True
            # print("show index CHECKED!")
        else:
            self.lblShape.show_baseline = False
            # print("show index UNCHECKED!")
        self.lblShape.update()

        # connect
        # self.lblShape.sigPain

    def show_object_shape(self):
        self.lblShape.set_ds_ops(self.ds_ops)
        self.lblShape.repaint()

    def on_btn_analysis_clicked(self):
        # print("pca button clicked")
        # set wait cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()

        self.ds_ops = MdDatasetOps(self.dataset)
        self.analysis_done = False
        if self.rbCVA.isChecked():
            self.analysis_type = "CVA"
        elif self.rbPCA.isChecked():
            self.analysis_type = "PCA"

        if not self.ds_ops.procrustes_superimposition():
            logger = logging.getLogger(__name__)
            logger.error("procrustes superimposition failed")
            return
        self.show_object_shape()

        if self.dataset.object_list is None or len(self.dataset.object_list) < 5:
            logger = logging.getLogger(__name__)
            logger.warning("too small number of objects for PCA analysis")
            return

        if self.analysis_type == "CVA":
            self.analysis_result = self.PerformCVA(self.ds_ops)

        elif self.analysis_type == "PCA":
            self.analysis_result = self.PerformPCA(self.ds_ops)

        new_coords = self.analysis_result.rotated_matrix.tolist()
        for i, obj in enumerate(self.ds_ops.object_list):
            obj.analysis_result = new_coords[i]

        self.show_analysis_result()

        # end wait cursor
        self.analysis_done = True
        QApplication.restoreOverrideCursor()

        # print("pca_result.nVariable:",pca_result.nVariable)
        # with open('pca_result.txt', 'w') as f:
        #    for obj in ds_ops.object_list:
        #        f.write(obj.object_name + "\t" + "\t".join([str(x) for x in obj.pca_result]) + "\n")

    def show_analysis_result(self):
        # self.plot_widget.clear()

        self.show_result_table()
        # get axis1 and axis2 value from comboAxis1 and 2 index
        depth_shade = self.cbxDepthShade.isChecked()
        show_legend = self.cbxLegend.isChecked()
        show_axis_label = self.cbxAxisLabel.isChecked()
        axis1 = self.comboAxis1.currentIndex()
        axis2 = self.comboAxis2.currentIndex()
        axis3 = self.comboAxis3.currentIndex()
        axis1_title = self.comboAxis1.currentText()
        axis2_title = self.comboAxis2.currentText()
        axis3_title = self.comboAxis3.currentText()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() else 1.0
        flip_axis3 = -1.0 if self.cbxFlipAxis3.isChecked() else 1.0

        symbol_candidate = ["o", "s", "^", "x", "+", "d", "v", "<", ">", "p", "h"]
        color_candidate = ["blue", "green", "black", "cyan", "magenta", "yellow", "gray", "red"]
        color_candidate = self.color_list[:]
        symbol_candidate = self.marker_list[:]
        self.propertyname_index = self.comboPropertyName.currentIndex() - 1
        self.scatter_data = {}
        self.scatter_result = {}
        SCATTER_SMALL_SIZE = 30
        SCATTER_MEDIUM_SIZE = 50
        SCATTER_LARGE_SIZE = 60
        if self.plot_size.lower() == "small":
            scatter_size = SCATTER_SMALL_SIZE
        elif self.plot_size.lower() == "medium":
            scatter_size = SCATTER_MEDIUM_SIZE
        elif self.plot_size.lower() == "large":
            scatter_size = SCATTER_LARGE_SIZE

        key_list = []
        key_list.append("__default__")
        self.scatter_data["__default__"] = {
            "x_val": [],
            "y_val": [],
            "z_val": [],
            "data": [],
            "hoverinfo": [],
            "text": [],
            "property": "",
            "symbol": "o",
            "color": color_candidate[0],
            "size": scatter_size,
        }
        if len(self.selected_object_id_list) > 0:
            self.scatter_data["__selected__"] = {
                "x_val": [],
                "y_val": [],
                "z_val": [],
                "data": [],
                "hoverinfo": [],
                "text": [],
                "property": "",
                "symbol": "o",
                "color": "red",
                "size": SCATTER_LARGE_SIZE,
            }
            key_list.append("__selected__")

        for obj in self.ds_ops.object_list:
            key_name = "__default__"

            if obj.id in self.selected_object_id_list:
                key_name = "__selected__"
            elif self.propertyname_index > -1 and self.propertyname_index < len(obj.variable_list):
                key_name = obj.variable_list[self.propertyname_index]

            if key_name not in self.scatter_data.keys():
                self.scatter_data[key_name] = {
                    "x_val": [],
                    "y_val": [],
                    "z_val": [],
                    "data": [],
                    "property": key_name,
                    "symbol": "",
                    "color": "",
                    "size": scatter_size,
                }
            if axis1 == 10:
                mdobject = MdObject.get_by_id(obj.id)
                mdobject.get_centroid_size(True)
                # print("obj:", mdobject.id, "csize:", csize)
                self.scatter_data[key_name]["x_val"].append(flip_axis1 * mdobject.get_centroid_size(True))
            else:
                self.scatter_data[key_name]["x_val"].append(flip_axis1 * obj.analysis_result[axis1])
            self.scatter_data[key_name]["y_val"].append(flip_axis2 * obj.analysis_result[axis2])
            self.scatter_data[key_name]["z_val"].append(flip_axis3 * obj.analysis_result[axis3])
            self.scatter_data[key_name]["data"].append(obj)
            # group_hash[key_name]['text'].append(obj.object_name)
            # group_hash[key_name]['hoverinfo'].append(obj.id)

        # remove empty group
        if len(self.scatter_data["__default__"]["x_val"]) == 0:
            del self.scatter_data["__default__"]

        # assign color and symbol
        sc_idx = 0
        for key_name in self.scatter_data.keys():
            if self.scatter_data[key_name]["color"] == "":
                self.scatter_data[key_name]["color"] = color_candidate[sc_idx % len(color_candidate)]
                self.scatter_data[key_name]["symbol"] = symbol_candidate[sc_idx % len(symbol_candidate)]
                sc_idx += 1

        if self.rb2DChartDim.isChecked():
            self.ax2.clear()
            for name in self.scatter_data.keys():
                # print("name", name, "len(group_hash[name]['x_val'])", len(group_hash[name]['x_val']), group_hash[name]['symbol'])
                group = self.scatter_data[name]
                if len(group["x_val"]) > 0:
                    self.scatter_result[name] = self.ax2.scatter(
                        group["x_val"],
                        group["y_val"],
                        s=group["size"],
                        marker=group["symbol"],
                        color=group["color"],
                        data=group["data"],
                        picker=True,
                        pickradius=5,
                    )
                    # print("ret", ret)
                if name == "__selected__":
                    for idx, obj in enumerate(group["data"]):
                        self.ax2.annotate(obj.object_name, (group["x_val"][idx], group["y_val"][idx]))
            if show_legend:
                values = []
                keys = []
                for key in self.scatter_result.keys():
                    # print("key", key)
                    if key[0] == "_":
                        continue
                    else:
                        keys.append(key)
                        values.append(self.scatter_result[key])
                self.ax2.legend(values, keys, loc="upper right", bbox_to_anchor=(1.05, 1))
            if show_axis_label:
                self.ax2.set_xlabel(axis1_title)
                self.ax2.set_ylabel(axis2_title)
            self.fig2.tight_layout()
            self.fig2.canvas.draw()
            self.fig2.canvas.flush_events()
            self.fig2.canvas.mpl_connect("pick_event", self.on_pick)
            self.fig2.canvas.mpl_connect("button_press_event", self.on_canvas_button_press)
            self.fig2.canvas.mpl_connect("button_release_event", self.on_canvas_button_release)
        else:
            self.ax3.clear()
            for name in self.scatter_data.keys():
                group = self.scatter_data[name]
                # print("name", name, "len(group_hash[name]['x_val'])", len(group['x_val']), group['symbol'])
                if len(self.scatter_data[name]["x_val"]) > 0:
                    self.scatter_result[name] = self.ax3.scatter(
                        group["x_val"],
                        group["y_val"],
                        group["z_val"],
                        s=group["size"],
                        marker=group["symbol"],
                        color=group["color"],
                        data=group["data"],
                        depthshade=depth_shade,
                        picker=True,
                        pickradius=5,
                    )
                if name == "__selected__":
                    for idx, obj in enumerate(group["data"]):
                        self.ax3.text(group["x_val"][idx], group["y_val"][idx], group["z_val"][idx], obj.object_name)
                    # print("ret", ret)
            if show_legend:
                values = []
                keys = []
                for key in self.scatter_result.keys():
                    # print("key", key)
                    if key[0] == "_":
                        continue
                    else:
                        keys.append(key)
                        values.append(self.scatter_result[key])
                self.ax3.legend(values, keys, loc="upper left", bbox_to_anchor=(1.05, 1))
            # if show_legend:
            #    self.ax3.legend(self.scatter_result.values(), self.scatter_result.keys(), loc='upper left', bbox_to_anchor=(1.05, 1))
            if show_axis_label:
                self.ax3.set_xlabel(axis1_title)
                self.ax3.set_ylabel(axis2_title)
                self.ax3.set_zlabel(axis3_title)
            self.fig3.tight_layout()
            self.fig3.canvas.draw()
            self.fig3.canvas.flush_events()
            self.fig3.canvas.mpl_connect("pick_event", self.on_pick)
            self.fig3.canvas.mpl_connect("button_press_event", self.on_canvas_button_press)
            self.fig3.canvas.mpl_connect("button_release_event", self.on_canvas_button_release)

    def show_result_table(self):
        self.plot_data.clear()
        self.rotation_matrix_data.clear()

        # PCA data
        # set header as "PC1", "PC2", "PC3", ... "PCn
        if self.rbCVA.isChecked():
            header = ["CV" + str(i + 1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))]
        else:
            header = ["PC" + str(i + 1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))]
        header.append("CSize")
        # print("header", header)
        self.plot_data.setColumnCount(len(header) + 1)
        self.plot_data.setHorizontalHeaderLabels(["Name"] + header)

        new_coords = self.analysis_result.rotated_matrix.tolist()
        self.plot_data.setColumnCount(len(new_coords[0]) + 2)
        for i, obj in enumerate(self.ds_ops.object_list):
            self.plot_data.insertRow(i)
            self.plot_data.setItem(i, 0, QTableWidgetItem(obj.object_name))
            for j, val in enumerate(new_coords[i]):
                self.plot_data.setItem(i, j + 1, QTableWidgetItem(str(int(val * 10000) / 10000.0)))
            mdobject = MdObject.get_by_id(obj.id)
            csize = mdobject.get_centroid_size(True)
            # print("obj:", mdobject.id, "csize:", csize)
            self.plot_data.setItem(i, len(new_coords[0]) + 1, QTableWidgetItem(str(int(csize * 10000) / 10000.0)))

        # rotation matrix
        rotation_matrix = self.analysis_result.rotation_matrix.tolist()
        # print("rotation_matrix[0][0]", [0][0], len(self.pca_result.rotation_matrix[0][0]))
        self.rotation_matrix_data.setColumnCount(len(rotation_matrix[0]))
        for i, row in enumerate(rotation_matrix):
            self.rotation_matrix_data.insertRow(i)
            for j, val in enumerate(row):
                self.rotation_matrix_data.setItem(i, j, QTableWidgetItem(str(int(val * 10000) / 10000.0)))

        # self.analysis_result.rotated_matrix

        # eigen values
        self.eigenvalue_data.setColumnCount(2)
        for i, val in enumerate(self.analysis_result.raw_eigen_values):
            val2 = self.analysis_result.eigen_value_percentages[i]
            self.eigenvalue_data.insertRow(i)
            self.eigenvalue_data.setItem(i, 0, QTableWidgetItem(str(int(val * 10000) / 10000.0)))
            self.eigenvalue_data.setItem(i, 1, QTableWidgetItem(str(int(val2 * 10000) / 10000.0)))

        # shapes tab
        min_vector = self.analysis_result.rotated_matrix.min(axis=0)
        max_vector = self.analysis_result.rotated_matrix.max(axis=0)
        avg_vector = self.analysis_result.rotated_matrix.mean(axis=0)
        # combine 3 vectors to 1 matrix
        np.vstack((min_vector, avg_vector, max_vector))
        self.shapes_data.clear()
        self.shapes_data.setColumnCount(len(new_coords[0]) + 1)
        self.comboAxis1.currentIndex()
        self.comboAxis2.currentIndex()
        self.comboAxis3.currentIndex()
        self.comboAxis1.currentText()
        self.comboAxis2.currentText()
        self.comboAxis3.currentText()
        -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
        -1.0 if self.cbxFlipAxis2.isChecked() else 1.0
        -1.0 if self.cbxFlipAxis3.isChecked() else 1.0
        new_coords = self.analysis_result.rotated_matrix.tolist()
        for i, obj in enumerate(self.ds_ops.object_list):
            obj.analysis_result = new_coords[i]

        # print("shapes", shapes.shape)
        dimension = self.ds_ops.dimension
        vector_length = len(self.analysis_result.rotated_matrix.tolist()[0])
        if dimension == 2:
            axis_label = ["x", "y"]
        elif dimension == 3:
            axis_label = ["x", "y", "z"]

        column_header_list = ["name"]
        for i in range(vector_length):
            column_header_list.append(axis_label[i % dimension] + str(int(i / dimension) + 1))
        # column_header_list.append("CSize")

        """
        self.shapes_data.setHorizontalHeaderLabels(column_header_list)
        if self.rb2DChartDim.isChecked():
            dim = 2
            combination2 = [ "min", "avg", "max" ]
            shape_list = np.zeros((len(combination2)**dim,len(new_coords[0])))
            idx = 0
            for i1, m1 in enumerate(combination2):
                for i2, m2 in enumerate(combination2):
                    row_header_list.append(axis1_title + " " + m1 + " " + axis2_title + " " + m2)
                    row_idx1 = int(( i1 - 1 ) * flip_axis1 + 1)
                    row_idx2 = int(( i2 - 1 ) * flip_axis2 + 1)
                    #print("row_idx1", row_idx1, "row_idx2", row_idx2)
                    shape_list[idx,axis1] = flip_axis1 * shapes[ row_idx1, axis1]
                    shape_list[idx,axis2] = flip_axis2 * shapes[ row_idx2, axis2]
                    idx += 1

        elif self.rb3DChartDim.isChecked():
            dim = 3
            combination2 = [ "min", "avg", "max" ]
            shape_list = np.zeros((len(combination2)**dim,len(new_coords[0])))
            idx = 0
            for i1, m1 in enumerate(combination2):
                for i2, m2 in enumerate(combination2):
                    for i3, m3 in enumerate(combination2):
                        row_header_list.append(axis1_title + " " + m1 + " " + axis2_title + " " + m2 + axis3_title + " " + m3)
                        row_idx1 = int(( i1 - 1 ) * flip_axis1 + 1)
                        row_idx2 = int(( i2 - 1 ) * flip_axis2 + 1)
                        row_idx3 = int(( i3 - 1 ) * flip_axis3 + 1)
                        #print("row_idx1", row_idx1, "row_idx2", row_idx2, "row_idx3", row_idx3)

                        shape_list[idx,axis1] = flip_axis1 * shapes[ row_idx1, axis1]
                        shape_list[idx,axis2] = flip_axis2 * shapes[ row_idx2, axis2]
                        shape_list[idx,axis3] = flip_axis3 * shapes[ row_idx3, axis3]
                        idx += 1
        # add average shape to shape_list
        row_header_list.append("Average")
        average_shape = np.array(self.ds_ops.get_average_shape().landmark_list).reshape(1,-1)
        #print(average_shape)


        inverted_matrix = np.linalg.inv(self.analysis_result.rotation_matrix)
        #print("inverted_matrix", inverted_matrix)

        unrotated_shapes = np.dot(shape_list, inverted_matrix)
        unrotated_shapes += average_shape
        self.shape_list = unrotated_shapes
        self.shape_name_list = row_header_list
        self.shape_column_header_list = column_header_list

        for i, shape in enumerate(unrotated_shapes.tolist()):
            self.shapes_data.insertRow(i)
            self.shapes_data.setItem(i, 0, QTableWidgetItem(row_header_list[i]))
            for j, val in enumerate(shape):
                self.shapes_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))
        """

    def on_canvas_button_press(self, evt):
        # print("button_press", evt)
        self.canvas_down_xy = (evt.x, evt.y)
        # self.tableView.selectionModel().clearSelection()

    def on_canvas_button_release(self, evt):
        # print("button_release", evt)
        if self.onpick_happened:
            self.onpick_happened = False
            return
        self.canvas_up_xy = (evt.x, evt.y)
        if self.canvas_down_xy == self.canvas_up_xy:
            self.tableView1.selectionModel().clearSelection()

    def on_pick(self, evt):
        # print("onpick", evt)
        self.onpick_happened = True
        # print("evt", evt, evt.ind, evt.artist )
        selected_object_id_list = []
        for key_name in self.scatter_data.keys():
            if evt.artist == self.scatter_result[key_name]:
                # print("key_name", key_name)
                for idx in evt.ind:
                    obj = self.scatter_data[key_name]["data"][idx]
                    # print("obj", obj)
                    selected_object_id_list.append(obj.id)
                    # self.ds_ops.select_object(obj.id)

        # print("selected_object_id_list", selected_object_id_list)
        # select rows in tableView
        # self.tableView.clearSelection()
        # selectionModel = self.tableView.selectionModel()

        # print("selected_object_id_list", selected_object_id_list)
        self.selection_changed_off = True
        for id in selected_object_id_list:
            # item = self.object_model.findItems(str(id), Qt.MatchExactly, 0)
            item = self.object_hash[id]
            self.tableView1.selectionModel().select(item.index(), QItemSelectionModel.Rows | QItemSelectionModel.Select)
        self.selection_changed_off = False
        self.on_object_selection_changed([], [])

        # for row in range(self.object_model.rowCount()):
        #    if int(self.object_model.item(row,0).text()) in selected_object_id_list:
        #        self.tableView.selectionModel().select(self.object_model.item(row,0).index(),QItemSelectionModel.Rows | QItemSelectionModel.Select)

    def on_mouse_clicked(self, event):
        # print("mouse clicked:",event)
        # if event.double():
        #    print("double clicked")
        # else:
        #    print("single clicked")
        p = self.plot_widget.plotItem.vb.mapSceneToView(event.scenePos())
        self.status_bar.showMessage("scene pos:" + str(event.scenePos()) + ", data pos:" + str(p))

    def on_mouse_moved(self, pos):
        p = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        # print("plot widget:",self.plot_widget, "plotItem:",self.plot_widget.plotItem, "vb:",self.plot_widget.plotItem.vb, "mapSceneToView:",self.plot_widget.plotItem.vb.mapSceneToView(pos))
        # print("pos:",pos, pos.x(), pos.y(), "p:",p, p.x(), p.y())

        self.status_bar.showMessage("x: %d, y: %d, x2: %f, y2: %f" % (pos.x(), pos.y(), p.x(), p.y()))

    def on_scatter_item_clicked(self, plot, points):
        # print("scatter item clicked:",plot,points)
        self.selected_object_id_list = []
        for pt in points:
            # print("points:",str(pt.data()))
            self.selected_object_id_list.append(pt.data().id)
        # select rows in tableView
        for obj_id in self.selected_object_id_list:
            for row in range(self.object_model.rowCount()):
                if int(self.object_model.item(row, 0).text()) == obj_id:
                    self.tableView1.selectRow(row)
                    # break

    def PerformCVA(self, dataset_ops):
        cva = MdCanonicalVariate()

        property_index = self.comboPropertyName.currentIndex() - 1
        # print("property_index:",property_index)
        if property_index < 0:
            QMessageBox.information(self, "Information", "Please select a property.")
            return
        datamatrix = []
        category_list = []
        # obj = dataset_ops.object_list[0]
        # print(obj, obj.variable_list, property_index)
        for obj in dataset_ops.object_list:
            datum = []
            for lm in obj.landmark_list:
                datum.extend(lm)
            datamatrix.append(datum)
            category_list.append(obj.variable_list[property_index])

        cva.SetData(datamatrix)
        cva.SetCategory(category_list)
        cva.Analyze()

        min(cva.nObservation, cva.nVariable)

        return cva

    def PerformPCA(self, dataset_ops):
        pca = MdPrincipalComponent()
        datamatrix = []
        for obj in dataset_ops.object_list:
            datum = []
            for lm in obj.landmark_list:
                datum.extend(lm)
            datamatrix.append(datum)

        pca.SetData(datamatrix)
        pca.Analyze()

        min(pca.nObservation, pca.nVariable)

        return pca

    def load_object(self):
        # load objects into tableView
        # for object in self.dataset.object_list:
        self.object_model.clear()
        self.property_model.clear()
        self.reset_tableView()
        if self.dataset is None:
            return
        # objects = self.selected_dataset.objects
        self.object_hash = {}

        self.propertyname_index = self.comboPropertyName.currentIndex() - 1
        self.propertyname = self.comboPropertyName.currentText()

        self.variable_list = []
        for obj in self.dataset.object_list:
            item0 = QStandardItem()
            item0.setCheckable(True)
            item0.setCheckState(Qt.Checked)
            item0.setData(obj.id, Qt.DisplayRole)

            item1 = QStandardItem()
            item1.setData(obj.id, Qt.DisplayRole)
            item2 = QStandardItem(obj.object_name)
            self.object_hash[obj.id] = item1
            if self.propertyname_index >= 0:
                obj.unpack_variable()
                # print(obj.variable_list)
                item3 = QStandardItem(obj.variable_list[self.propertyname_index])
                if obj.variable_list[self.propertyname_index] not in self.variable_list:
                    self.variable_list.append(obj.variable_list[self.propertyname_index])
                    p_item0 = QStandardItem()
                    p_item0.setCheckable(True)
                    p_item0.setCheckState(Qt.Checked)
                    p_item1 = QStandardItem()
                    p_item1.setCheckable(True)
                    p_item1.setCheckState(Qt.Checked)
                    self.property_model.appendRow(
                        [p_item0, p_item1, QStandardItem(obj.variable_list[self.propertyname_index])]
                    )
                # self.variable_list.append(obj.variable_list[self.propertyname_index])
                self.object_model.appendRow([item0, item1, item2, item3])
            else:
                self.object_model.appendRow([item0, item1, item2])

    def reset_tableView(self):
        self.property_model = QStandardItemModel()
        self.property_model.setColumnCount(3)
        self.property_model.setHorizontalHeaderLabels(["Show", "Avg", "Group"])
        self.tableView2.setModel(self.property_model)

        self.tableView2.setColumnWidth(0, 20)
        self.tableView2.setColumnWidth(1, 20)
        self.tableView2.setColumnWidth(1, 100)
        header2 = self.tableView2.horizontalHeader()
        header2.setSectionResizeMode(0, QHeaderView.Fixed)
        header2.setSectionResizeMode(1, QHeaderView.Fixed)
        header2.setSectionResizeMode(2, QHeaderView.Stretch)

        self.object_model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.object_model)
        self.propertyname_index = self.comboPropertyName.currentIndex() - 1
        self.propertyname = self.comboPropertyName.currentText()
        self.object_model.setColumnCount(3)
        self.object_model.setHorizontalHeaderLabels(["", "ID", "Name"])
        self.tableView1.setModel(self.proxy_model)
        # self.tableView.setModel(self.object_model)
        self.tableView1.setColumnWidth(0, 20)
        self.tableView1.setColumnWidth(1, 50)
        self.tableView1.setColumnWidth(2, 150)
        self.tableView1.verticalHeader().setDefaultSectionSize(20)
        self.tableView1.verticalHeader().setVisible(False)
        self.tableView1.setSelectionBehavior(QTableView.SelectRows)
        # self.tableView.clicked.connect(self.on_tableView_clicked)
        self.object_selection_model = self.tableView1.selectionModel()
        self.object_selection_model.selectionChanged.connect(self.on_object_selection_changed)
        self.tableView1.setSortingEnabled(True)
        self.tableView1.sortByColumn(0, Qt.AscendingOrder)
        self.object_model.setSortRole(Qt.UserRole)

        header = self.tableView1.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header2 = self.tableView2.horizontalHeader()
        header2.setSectionResizeMode(0, QHeaderView.Fixed)
        header2.setSectionResizeMode(1, QHeaderView.Fixed)
        header2.setSectionResizeMode(2, QHeaderView.Stretch)

        if self.propertyname_index >= 0:
            self.object_model.setColumnCount(4)
            self.object_model.setHorizontalHeaderLabels(["", "ID", "Name", self.propertyname])
            self.tableView1.setColumnWidth(3, 150)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            self.property_model.setHorizontalHeaderLabels(["Show", "Avg", self.propertyname])

        self.tableView1.setStyleSheet(
            "QTreeView::item:selected{background-color: palette(highlight); color: palette(highlightedText);};"
        )

    def on_object_selection_changed(self, selected, deselected):
        if self.selection_changed_off:
            pass
        else:
            self.selected_object_id_list = self.get_selected_object_id_list()
            self.show_analysis_result()
            self.ds_ops.selected_object_id_list = self.selected_object_id_list
            self.show_object_shape()

    def get_selected_object_id_list(self):
        selected_indexes = self.tableView1.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return []

        new_index_list = []
        model = selected_indexes[0].model()
        if hasattr(model, "mapToSource"):
            for index in selected_indexes:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
            selected_indexes = new_index_list

        selected_object_id_list = []
        for index in selected_indexes:
            item = self.object_model.itemFromIndex(index)
            object_id = item.text()
            object_id = int(object_id)
            selected_object_id_list.append(object_id)

        return selected_object_id_list


class ExportDatasetDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Export"))
        self.parent = parent
        # print(self.parent.pos())
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()

        self.lblDatasetName = QLabel(self.tr("Dataset Name"))
        self.lblDatasetName.setMaximumHeight(20)
        self.edtDatasetName = QLineEdit()
        self.edtDatasetName.setMaximumHeight(20)
        self.lblObjectList = QLabel(self.tr("Object List"))
        self.lblExportList = QLabel(self.tr("Export List"))
        self.lblObjectList.setMaximumHeight(20)
        self.lblExportList.setMaximumHeight(20)
        self.lstObjectList = QListWidget()
        self.lstExportList = QListWidget()
        self.lstObjectList.setMinimumHeight(400)
        self.lstExportList.setMinimumHeight(400)
        self.btnExport = QPushButton(self.tr("Export"))
        self.btnExport.clicked.connect(self.export_dataset)
        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.close)
        self.btnMoveRight = QPushButton(">")
        self.btnMoveRight.clicked.connect(self.move_right)
        self.btnMoveLeft = QPushButton("<")
        self.btnMoveLeft.clicked.connect(self.move_left)

        self.lblExport = QLabel(self.tr("Export Format"))
        self.rbTPS = QRadioButton("TPS")
        self.rbTPS.setChecked(True)
        self.rbTPS.clicked.connect(self.on_rbTPS_clicked)
        self.rbTPS.setEnabled(True)
        self.rbNTS = QRadioButton("NTS")
        self.rbNTS.setChecked(True)
        self.rbNTS.clicked.connect(self.on_rbNTS_clicked)
        self.rbNTS.setEnabled(True)
        self.rbX1Y1 = QRadioButton("X1Y1")
        self.rbX1Y1.clicked.connect(self.on_rbX1Y1_clicked)
        self.rbX1Y1.setEnabled(True)
        self.rbX1Y1.setChecked(False)
        self.rbMorphologika = QRadioButton("Morphologika")
        self.rbMorphologika.clicked.connect(self.on_rbMorphologika_clicked)
        # self.rbMorphologika.setEnabled(False)
        # self.rbMorphologika.setChecked(False)

        # JSON+ZIP option
        self.rbJSONZip = QRadioButton("JSON+ZIP")
        self.rbJSONZip.clicked.connect(self.on_rbJSONZip_clicked)
        self.chkIncludeFiles = QCheckBox(self.tr("Include image and model files"))
        self.chkIncludeFiles.setChecked(True)
        self.chkIncludeFiles.setEnabled(False)
        self.chkIncludeFiles.toggled.connect(self.update_estimated_size)
        self.lblEstimatedSize = QLabel(self.tr("Estimated size: -"))

        self.lblSuperimposition = QLabel(self.tr("Superimposition"))
        self.rbProcrustes = QRadioButton(self.tr("Procrustes"))
        self.rbProcrustes.clicked.connect(self.on_rbProcrustes_clicked)
        self.rbProcrustes.setEnabled(True)
        self.rbProcrustes.setChecked(True)
        self.rbBookstein = QRadioButton(self.tr("Bookstein"))
        self.rbBookstein.clicked.connect(self.on_rbBookstein_clicked)
        self.rbBookstein.setEnabled(False)
        self.rbBookstein.setChecked(False)
        self.rbRFTRA = QRadioButton(self.tr("Resistant fit"))
        self.rbRFTRA.clicked.connect(self.on_rbRFTRA_clicked)
        self.rbRFTRA.setEnabled(False)
        self.rbRFTRA.setChecked(False)
        self.rbNone = QRadioButton(self.tr("None"))
        self.rbNone.clicked.connect(self.on_rbNone_clicked)
        self.rbNone.setEnabled(True)
        self.rbNone.setChecked(False)

        self.form_layout = QGridLayout()
        self.form_layout.addWidget(self.lblDatasetName, 0, 0)
        self.form_layout.addWidget(self.edtDatasetName, 0, 1, 1, 2)
        self.form_layout.addWidget(self.lblObjectList, 1, 0)
        self.form_layout.addWidget(self.lstObjectList, 2, 0, 2, 1)
        self.form_layout.addWidget(self.btnMoveRight, 2, 1)
        self.form_layout.addWidget(self.btnMoveLeft, 3, 1)
        self.form_layout.addWidget(self.lblExportList, 1, 2)
        self.form_layout.addWidget(self.lstExportList, 2, 2, 2, 1)

        self.button_layout1 = QHBoxLayout()
        self.button_layout1.addWidget(self.btnExport)
        self.button_layout1.addWidget(self.btnCancel)

        self.button_layout2 = QHBoxLayout()
        self.button_layout2.addWidget(self.lblExport)
        self.button_layout2.addWidget(self.rbTPS)
        self.button_layout2.addWidget(self.rbX1Y1)
        self.button_layout2.addWidget(self.rbMorphologika)
        self.button_layout2.addWidget(self.rbJSONZip)
        self.button_layout2.addWidget(self.chkIncludeFiles)
        self.button_layout2.addWidget(self.lblEstimatedSize)
        self.button_group2 = QButtonGroup()
        self.button_group2.addButton(self.rbTPS)
        self.button_group2.addButton(self.rbX1Y1)
        self.button_group2.addButton(self.rbMorphologika)
        self.button_group2.addButton(self.rbJSONZip)

        self.button_layout3 = QHBoxLayout()
        self.button_layout3.addWidget(self.lblSuperimposition)
        self.button_layout3.addWidget(self.rbNone)
        self.button_layout3.addWidget(self.rbProcrustes)
        self.button_layout3.addWidget(self.rbBookstein)
        self.button_layout3.addWidget(self.rbRFTRA)
        self.button_group3 = QButtonGroup()
        self.button_group3.addButton(self.rbNone)
        self.button_group3.addButton(self.rbProcrustes)
        self.button_group3.addButton(self.rbBookstein)
        self.button_group3.addButton(self.rbRFTRA)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.button_layout2)
        self.layout.addLayout(self.button_layout3)
        self.layout.addLayout(self.button_layout1)

        self.setLayout(self.layout)

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/ExportDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos() + QPoint(50, 50))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/ExportDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def set_dataset(self, dataset):
        self.dataset = dataset
        self.ds_ops = MdDatasetOps(dataset)
        self.edtDatasetName.setText(self.dataset.dataset_name)
        for object in self.dataset.object_list:
            self.lstExportList.addItem(object.object_name)

    def on_rbProcrustes_clicked(self):
        pass

    def on_rbBookstein_clicked(self):
        pass

    def on_rbRFTRA_clicked(self):
        pass

    def on_rbNone_clicked(self):
        pass

    def on_rbTPS_clicked(self):
        pass

    def on_rbNTS_clicked(self):
        pass

    def on_rbX1Y1_clicked(self):
        pass

    def on_rbMorphologika_clicked(self):
        pass

    def on_rbJSONZip_clicked(self):
        # Enable include files option and update estimate
        self.chkIncludeFiles.setEnabled(True)
        self.update_estimated_size()

    def update_estimated_size(self):
        try:
            include_files = self.chkIncludeFiles.isChecked()
            size_bytes = mu.estimate_package_size(self.ds_ops.id, include_files=include_files)

            # Format human-readable
            def fmt(sz):
                for unit in ["B", "KB", "MB", "GB", "TB"]:
                    if sz < 1024.0:
                        return f"{sz:3.1f} {unit}"
                    sz /= 1024.0
                return f"{sz:.1f} PB"

            self.lblEstimatedSize.setText(self.tr("Estimated size: ") + fmt(size_bytes))
        except Exception:
            self.lblEstimatedSize.setText(self.tr("Estimated size: -"))

    def move_right(self):
        selected_items = self.lstObjectList.selectedItems()
        for item in selected_items:
            self.lstObjectList.takeItem(self.lstObjectList.row(item))
            self.lstExportList.addItem(item)

    def move_left(self):
        selected_items = self.lstExportList.selectedItems()
        for item in selected_items:
            self.lstExportList.takeItem(self.lstExportList.row(item))
            self.lstObjectList.addItem(item)

    def export_dataset(self):
        ##export_list = []
        # for i in range(self.lstExportList.count()):
        ##    item = self.lstExportList.item(i)
        #    export_list.append(item.text())
        if self.rbProcrustes.isChecked():
            self.ds_ops.procrustes_superimposition()
        object_list = self.ds_ops.object_list
        today = datetime.datetime.now()
        date_str = today.strftime("%Y%m%d_%H%M%S")

        if self.rbTPS.isChecked():
            filename_candidate = f"{self.ds_ops.dataset_name}_{date_str}.tps"
            filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
            filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filepath, "TPS format (*.tps)")
            if filename:
                # open text file
                with open(filename, "w") as f:
                    for object in object_list:
                        f.write(f"LM={len(object.landmark_list)}\n")
                        for lm in object.landmark_list:
                            if self.ds_ops.dimension == 2:
                                f.write("{}\t{}\n".format(*lm))
                            else:
                                f.write("{}\t{}\t{}\n".format(*lm))
                        # if object.has_image():
                        #    f.write('IMAGE={}\n'.format(object.image_filename))
                        f.write(f"ID={object.object_name}\n")

        elif self.rbMorphologika.isChecked():
            filename_candidate = f"{self.ds_ops.dataset_name}_{date_str}.txt"
            filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
            filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filepath, "Morphologika format (*.txt)")
            if filename:
                result_str = ""
                result_str += "[individuals]" + NEWLINE + str(len(self.ds_ops.object_list)) + NEWLINE
                result_str += "[landmarks]" + NEWLINE + str(len(self.ds_ops.object_list[0].landmark_list)) + NEWLINE
                result_str += "[dimensions]" + NEWLINE + str(self.ds_ops.dimension) + NEWLINE
                label_values = "[labels]" + NEWLINE + "\t".join(self.dataset.variablename_list) + NEWLINE
                label_values += "[labelvalues]" + NEWLINE
                rawpoint_values = "[rawpoints]" + NEWLINE
                image_values = "[images]" + NEWLINE
                ppmm_values = "[pixelspermm]" + NEWLINE
                name_values = "[names]" + NEWLINE
                for mo in self.ds_ops.object_list:
                    label_values += "\t".join(mo.variable_list).strip() + NEWLINE
                    name_values += mo.object_name + NEWLINE
                    # print mo.objname
                    rawpoint_values += "'#" + mo.object_name + NEWLINE
                    for lm in mo.landmark_list:
                        rawpoint_values += "\t".join([str(c) for c in lm])
                        rawpoint_values += NEWLINE
                # print name_values
                result_str += name_values + label_values + rawpoint_values
                if len(self.dataset.edge_list) > 0:
                    result_str += "[wireframe]" + NEWLINE
                    self.dataset.unpack_wireframe()
                    for edge in self.dataset.edge_list:
                        # print edge
                        result_str += "\t".join([str(v) for v in edge]) + NEWLINE
                if len(self.dataset.polygon_list) > 0:
                    result_str += "[polygons]" + NEWLINE
                    self.dataset.unpack_polygons()
                    for polygon in self.dataset.polygon_list:
                        # print edge
                        result_str += "\t".join([str(v) for v in polygon]) + NEWLINE
                for obj_ops in self.ds_ops.object_list:
                    obj = MdObject.get_by_id(obj_ops.id)
                    if obj.has_image():
                        img = obj.get_image()
                        image_values += obj.get_name() + "." + img.get_file_path().split(".")[-1] + NEWLINE
                        old_filepath = img.get_file_path()
                        # get filepath from filename
                        new_image_path = os.path.join(
                            os.path.dirname(filename), obj.get_name() + "." + img.get_file_path().split(".")[-1]
                        )
                        shutil.copyfile(old_filepath, new_image_path)

                    else:
                        image_values = "" + NEWLINE
                    if obj.pixels_per_mm is not None and obj.pixels_per_mm > 0:
                        ppmm_values += str(obj.pixels_per_mm) + NEWLINE
                    else:
                        ppmm_values = "" + NEWLINE

                result_str += image_values
                result_str += ppmm_values
                # print("filename:", filename)
                # open text file
                with open(filename, "w") as f:
                    f.write(result_str)
        elif hasattr(self, "rbJSONZip") and self.rbJSONZip.isChecked():
            filename_candidate = f"{self.ds_ops.dataset_name}_{date_str}.zip"
            filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
            filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filepath, "ZIP archive (*.zip)")
            if filename:
                try:
                    # Simple progress dialog
                    progress = ProgressDialog(self)
                    progress.set_progress_text(self.tr("Exporting {}/{}..."))
                    progress.set_max_value(100)
                    progress.show()

                    def cb(curr, total):
                        try:
                            val = int((curr / float(total)) * 100) if total else 0
                        except Exception:
                            val = 0
                        progress.set_curr_value(val)

                    include_files = self.chkIncludeFiles.isChecked()
                    mu.create_zip_package(self.ds_ops.id, filename, include_files=include_files, progress_callback=cb)
                    progress.close()
                    QMessageBox.information(self, self.tr("Export"), self.tr("Export completed."))
                except Exception as e:
                    try:
                        progress.close()
                    except Exception:
                        pass
                    QMessageBox.critical(self, self.tr("Export"), self.tr("Export failed: ") + str(e))
        self.close()


class ImportDatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Import"))
        self.parent = parent
        # print(self.parent.pos())
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        # self.setGeometry(QRect(100, 100, 600, 400))
        # self.move(self.parent.pos()+QPoint(100,100))

        # add file open dialog
        self.filename_layout = QHBoxLayout()
        self.filename_widget = QWidget()
        self.btnOpenFile = QPushButton(self.tr("Open File"))
        self.btnOpenFile.clicked.connect(self.open_file)
        self.edtFilename = QLineEdit()
        self.edtFilename.setReadOnly(True)
        self.edtFilename.setText("")
        self.edtFilename.setPlaceholderText(self.tr("Select a file to import"))
        self.edtFilename.setMinimumWidth(400)
        self.edtFilename.setMaximumWidth(400)
        self.edtFilename.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.filename_layout.addWidget(self.edtFilename)
        self.filename_layout.addWidget(self.btnOpenFile)
        self.filename_widget.setLayout(self.filename_layout)

        # add file type checkbox group with TPS, X1Y1, Morphologika.
        self.chkFileType = QButtonGroup()
        self.rbnTPS = QRadioButton("TPS")
        self.rbnNTS = QRadioButton("NTS")
        self.rbnX1Y1 = QRadioButton("X1Y1")
        self.rbnMorphologika = QRadioButton("Morphologika")
        self.rbnJSONZip = QRadioButton("JSON+ZIP")
        # self.rbnX1Y1.setDisabled(True)
        # self.rbnMorphologika.setDisabled(True)
        self.chkFileType.addButton(self.rbnTPS)
        self.chkFileType.addButton(self.rbnNTS)
        self.chkFileType.addButton(self.rbnX1Y1)
        self.chkFileType.addButton(self.rbnMorphologika)
        self.chkFileType.addButton(self.rbnJSONZip)
        self.chkFileType.buttonClicked.connect(self.file_type_changed)
        self.chkFileType.setExclusive(True)
        # add qgroupbox for file type
        self.gbxFileType = QGroupBox()
        self.gbxFileType.setLayout(QHBoxLayout())
        self.gbxFileType.layout().addWidget(self.rbnTPS)
        self.gbxFileType.layout().addWidget(self.rbnNTS)
        self.gbxFileType.layout().addWidget(self.rbnX1Y1)
        self.gbxFileType.layout().addWidget(self.rbnMorphologika)
        self.gbxFileType.layout().addWidget(self.rbnJSONZip)
        self.gbxFileType.layout().addStretch(1)
        self.gbxFileType.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gbxFileType.setMaximumHeight(50)
        self.gbxFileType.setMinimumHeight(50)
        # self.gbxFileType.setTitle("File Type")

        self.rb2D = QRadioButton("2D")
        self.rb3D = QRadioButton("3D")
        self.gbxDimension = QGroupBox()
        self.gbxDimension.setLayout(QHBoxLayout())
        self.gbxDimension.layout().addWidget(self.rb2D)
        self.gbxDimension.layout().addWidget(self.rb3D)

        self.cbxInvertY = QCheckBox(self.tr("Inverted"))

        # add dataset name edit
        self.edtDatasetName = QLineEdit()
        self.edtDatasetName.setText("")
        self.edtDatasetName.setPlaceholderText(self.tr("Dataset Name"))
        self.edtDatasetName.setMinimumWidth(400)
        self.edtDatasetName.setMaximumWidth(400)
        self.edtDatasetName.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # add object count edit
        self.edtObjectCount = QLineEdit()
        self.edtObjectCount.setReadOnly(True)
        self.edtObjectCount.setText("")
        self.edtObjectCount.setPlaceholderText(self.tr("Object Count"))
        self.edtObjectCount.setMinimumWidth(100)
        self.edtObjectCount.setMaximumWidth(100)
        self.edtObjectCount.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.btnImport = QPushButton(self.tr("Excute Import"))
        self.btnImport.clicked.connect(self.import_file)
        self.btnImport.setEnabled(False)

        # add progress bar
        self.prgImport = QProgressBar()
        self.prgImport.setMinimum(0)
        self.prgImport.setMaximum(100)
        self.prgImport.setValue(0)
        self.prgImport.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # add layout
        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addRow(self.tr("File"), self.filename_widget)
        # self.main_layout.addRow("File Type", self.cbxFileType)
        self.main_layout.addRow(self.tr("File Type"), self.gbxFileType)
        self.main_layout.addRow(self.tr("Dataset Name"), self.edtDatasetName)
        self.main_layout.addRow(self.tr("Object Count"), self.edtObjectCount)
        self.main_layout.addRow(self.tr("Y coordinate"), self.cbxInvertY)
        self.main_layout.addRow(self.tr("Dimension"), self.gbxDimension)
        self.main_layout.addRow(self.tr("Progress"), self.prgImport)
        self.main_layout.addRow("", self.btnImport)

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/ImportDialog", QRect(100, 100, 500, 220)))
        else:
            self.setGeometry(QRect(100, 100, 500, 220))
            self.move(self.parent.pos() + QPoint(50, 50))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/ImportDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def open_file2(self, filename):
        self.edtFilename.setText(filename)
        self.btnImport.setEnabled(True)
        self.edtDatasetName.setText(self.suggest_unique_dataset_name(Path(filename).stem))
        self.edtObjectCount.setText("")
        self.prgImport.setValue(0)
        # get file extension
        self.file_ext = Path(filename).suffix
        # if extension is tps, set file type to tps
        if self.file_ext.lower() == ".tps":
            self.rbnTPS.setChecked(True)
            self.edtObjectCount.setText("")
            self.file_type_changed()
            import_data = TPS(filename, self.edtDatasetName.text(), self.cbxInvertY.isChecked())
        elif self.file_ext.lower() == ".nts":
            self.rbnNTS.setChecked(True)
            self.edtObjectCount.setText("")
            self.file_type_changed()
            import_data = NTS(filename, self.edtDatasetName.text(), self.cbxInvertY.isChecked())
        elif self.file_ext.lower() == ".x1y1":
            self.rbnX1Y1.setChecked(True)
            self.file_type_changed()
            import_data = X1Y1(filename, self.edtDatasetName.text(), self.cbxInvertY.isChecked())
        elif self.file_ext.lower() == ".txt":
            self.rbnMorphologika.setChecked(True)
            self.file_type_changed()
            import_data = Morphologika(filename, self.edtDatasetName.text(), self.cbxInvertY.isChecked())
        elif self.file_ext.lower() == ".zip":
            # JSON+ZIP
            self.rbnJSONZip.setChecked(True)
            self.file_type_changed()
            try:
                data = mu.read_json_from_zip(filename)
                ds_meta = data.get("dataset", {})
                objs = data.get("objects", [])
                # Suggest unique dataset name derived from package's dataset.json
                base_name = ds_meta.get("name") or self.tr("Imported Dataset")
                self.edtDatasetName.setText(self.suggest_unique_dataset_name(base_name))
                self.edtObjectCount.setText(str(len(objs)))
                if int(ds_meta.get("dimension", 2)) == 2:
                    self.rb2D.setChecked(True)
                else:
                    self.rb3D.setChecked(True)
                import_data = SimpleNamespace(
                    nobjects=len(objs),
                    dimension=int(ds_meta.get("dimension", 2)),
                    object_name_list=[o.get("name") for o in objs],
                )
            except Exception as e:
                QMessageBox.critical(self, self.tr("Import"), self.tr("Failed to read package: ") + str(e))
                return
        else:
            self.rbnTPS.setChecked(False)
            self.rbnNTS.setChecked(False)
            self.rbnX1Y1.setChecked(False)
            self.rbnMorphologika.setChecked(False)
            if hasattr(self, "rbnJSONZip"):
                self.rbnJSONZip.setChecked(False)
            self.btnImport.setEnabled(False)
            self.edtObjectCount.setText("")
            self.prgImport.setValue(0)
            self.edtDatasetName.setText("")
            self.edtFilename.setText("")
            QMessageBox.warning(self, self.tr("Warning"), self.tr("File type not supported."))
            return
        if len(import_data.object_name_list) > 0:
            self.edtObjectCount.setText(str(import_data.nobjects))
            if import_data.dimension == 2:
                self.rb2D.setChecked(True)
            else:
                self.rb3D.setChecked(True)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", mu.USER_PROFILE_DIRECTORY, "All Files (*.*)")
        if filename:
            self.open_file2(filename)

            # else:

    def file_type_changed(self):
        pass

    def suggest_unique_dataset_name(self, base_name: str) -> str:
        """Return a unique dataset name, appending (1), (2), ... if needed."""
        try:
            candidate = base_name
            suffix = 1
            while MdDataset.select().where(MdDataset.dataset_name == candidate).exists():
                candidate = f"{base_name} ({suffix})"
                suffix += 1
            return candidate
        except Exception:
            return base_name

    def import_file(self):
        filename = self.edtFilename.text()
        filetype = self.chkFileType.checkedButton().text()
        datasetname = self.suggest_unique_dataset_name(self.edtDatasetName.text())
        self.edtObjectCount.text()
        invertY = self.cbxInvertY.isChecked()
        import_data = None
        if filetype == "TPS":
            import_data = TPS(filename, datasetname, invertY)
        elif filetype == "NTS":
            import_data = NTS(filename, datasetname, invertY)
        elif filetype == "X1Y1":
            import_data = X1Y1(filename, datasetname, invertY)
        elif filetype == "Morphologika":
            import_data = Morphologika(filename, datasetname, invertY)
        elif filetype == "JSON+ZIP":
            # progress
            self.prgImport.setValue(0)

            def cb(curr, total):
                try:
                    val = int((curr / float(total)) * 100) if total else 0
                except Exception:
                    val = 0
                self.prgImport.setValue(val)
                self.prgImport.update()

            try:
                new_ds_id = mu.import_dataset_from_zip(filename, progress_callback=cb)
                self.prgImport.setValue(100)
                QMessageBox.information(
                    self, self.tr("Import"), self.tr("Import completed (Dataset ID: ") + str(new_ds_id) + ")"
                )
                # After the user closes the message box, close dialog and refresh tree
                try:
                    if hasattr(self.parent, "load_dataset"):
                        self.parent.load_dataset()
                except Exception:
                    pass
                self.close()
            except Exception as e:
                QMessageBox.critical(self, self.tr("Import"), self.tr("Import failed: ") + str(e))
            return

        if import_data is None:
            return

        self.btnImport.setEnabled(False)
        self.prgImport.setValue(0)
        self.prgImport.setFormat(self.tr("Importing..."))
        self.prgImport.update()
        self.prgImport.repaint()

        self.edtObjectCount.setText(str(import_data.nobjects))
        # print("objects:", tps.nobjects,tps.nlandmarks,tps.object_name_list)
        # create dataset
        dataset = MdDataset()
        dataset.dataset_name = datasetname
        dataset.dimension = import_data.dimension
        if len(import_data.variablename_list) > 0:
            dataset.variablename_list = import_data.variablename_list
            dataset.pack_variablename_str()
        if len(import_data.edge_list) > 0:
            dataset.edge_list = import_data.edge_list
            dataset.wireframe = dataset.pack_wireframe()
            # dataset.pack_edge_str()
        dataset.save()
        # add objects
        for i in range(import_data.nobjects):
            object = MdObject()
            object.object_name = import_data.object_name_list[i]
            # see if import_data.ppmm_list exist
            if hasattr(import_data, "ppmm_list") and len(import_data.ppmm_list) > 0:
                if mu.is_numeric(import_data.ppmm_list[i]):
                    object.pixels_per_mm = float(import_data.ppmm_list[i])
                else:
                    object.pixels_per_mm = None
            # print("object:", object.object_name)
            object.dataset = dataset
            object.landmark_str = ""
            landmark_list = []
            # print("object_name", object.object_name, import_data.landmark_data.keys())
            # if object.object_name in import_data.landmark_data.keys():
            #    print("key exist")
            # else:
            #    print("key not exist")
            for landmark in import_data.landmark_data[object.object_name]:
                landmark_list.append("\t".join([str(x) for x in landmark]))
            object.landmark_str = "\n".join(landmark_list)
            if len(import_data.variablename_list) > 0:
                object.variable_list = import_data.property_list_list[i]
                object.pack_variable()
            if object.object_name in import_data.object_comment.keys():
                object.object_desc = import_data.object_comment[import_data.object_name_list[i]]

            object.save()
            if object.object_name in import_data.object_images.keys():
                file_name = import_data.object_images[object.object_name]
                # check if file_name exists
                if not os.path.exists(file_name):
                    file_name = os.path.join(import_data.dirname, file_name)
                if not os.path.exists(file_name):
                    logger = logging.getLogger(__name__)
                    logger.error(f"file not found: {file_name}")
                else:
                    new_image = MdImage()
                    new_image.object = object
                    new_image.load_file_info(file_name)
                    new_filepath = new_image.get_file_path(self.m_app.storage_directory)
                    if not os.path.exists(os.path.dirname(new_filepath)):
                        os.makedirs(os.path.dirname(new_filepath))
                    shutil.copyfile(file_name, new_filepath)
                    new_image.save()

            val = int(float(i + 1) * 100.0 / float(import_data.nobjects))
            # print("progress:", i+1, tps.nobjects, val)
            self.update_progress(val)
            # progress = int( (i / float(tps.nobjects)) * 100)

        # print("tps import done")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText(self.tr(f"Finished importing a {filetype} file."))
        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec_()
        try:
            if hasattr(self.parent, "load_dataset"):
                self.parent.load_dataset()
        except Exception:
            pass
        self.close()
        # add dataset to project
        # self.parent.parent.project.datasets.append(dataset)
        # self.parent.parent.project.current_dataset = dataset

    def update_progress(self, value):
        self.prgImport.setValue(value)
        self.prgImport.setFormat(self.tr(f"Importing...{value}%"))
        self.prgImport.update()
        self.prgImport.repaint()
        QApplication.processEvents()


class PreferencesDialog(QDialog):
    """
    PreferencesDialog shows preferences.

    Args:
        None

    Attributes:
        well..
    """

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.m_app = QApplication.instance()

        self.m_app.remember_geometry = True
        self.toolbar_icon_small = False
        self.toolbar_icon_medium = False
        self.toolbar_icon_large = False
        self.m_app.plot_size = "medium"

        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        # ['blue','green','black','cyan','magenta','yellow','gray','red']
        self.m_app.color_list = self.default_color_list[:]
        self.m_app.marker_list = mu.MARKER_LIST[:]

        self.m_app.landmark_pref = {"2D": {"size": 1, "color": "#0000FF"}, "3D": {"size": 1, "color": "#0000FF"}}
        self.m_app.wireframe_pref = {
            "2D": {"thickness": 1, "color": "#FFFF00"},
            "3D": {"thickness": 1, "color": "#FFFF00"},
        }
        self.m_app.index_pref = {"2D": {"size": 1, "color": "#FFFFFF"}, "3D": {"size": 1, "color": "#FFFFFF"}}
        self.m_app.bgcolor = "#AAAAAA"
        # print("landmark_pref:", self.landmark_pref)
        # print("wireframe_pref:", self.wireframe_pref)

        self.setWindowTitle("Preferences")
        # self.lbl_main_view.setMinimumSize(400, 300)
        # print("landmark_pref:", self.landmark_pref)
        # print("wireframe_pref:", self.wireframe_pref)

        self.rbRememberGeometryYes = QRadioButton(self.tr("Yes"))
        self.rbRememberGeometryYes.setChecked(self.m_app.remember_geometry)
        self.rbRememberGeometryYes.clicked.connect(self.on_rbRememberGeometryYes_clicked)
        self.rbRememberGeometryNo = QRadioButton(self.tr("No"))
        self.rbRememberGeometryNo.setChecked(not self.m_app.remember_geometry)
        self.rbRememberGeometryNo.clicked.connect(self.on_rbRememberGeometryNo_clicked)

        self.gbRememberGeomegry = QGroupBox()
        self.gbRememberGeomegry.setLayout(QHBoxLayout())
        self.gbRememberGeomegry.layout().addWidget(self.rbRememberGeometryYes)
        self.gbRememberGeomegry.layout().addWidget(self.rbRememberGeometryNo)

        self.toolbar_icon_large = True if self.m_app.toolbar_icon_size.lower() == "large" else False
        self.rbToolbarIconLarge = QRadioButton(self.tr("Large"))
        self.rbToolbarIconLarge.setChecked(self.toolbar_icon_large)
        self.rbToolbarIconLarge.clicked.connect(self.on_rbToolbarIconLarge_clicked)
        self.rbToolbarIconSmall = QRadioButton(self.tr("Small"))
        self.rbToolbarIconSmall.setChecked(self.toolbar_icon_small)
        self.rbToolbarIconSmall.clicked.connect(self.on_rbToolbarIconSmall_clicked)
        self.rbToolbarIconMedium = QRadioButton(self.tr("Medium"))
        self.rbToolbarIconMedium.setChecked(self.toolbar_icon_medium)
        self.rbToolbarIconMedium.clicked.connect(self.on_rbToolbarIconMedium_clicked)

        self.gb2DLandmarkPref = QGroupBox()
        self.gb2DLandmarkPref.setLayout(QHBoxLayout())
        self.gb2DLandmarkPref.setTitle("2D")
        self.combo2DLandmarkSize = QComboBox()
        self.combo2DLandmarkSize.addItems([self.tr("Small"), self.tr("Medium"), self.tr("Large")])
        self.combo2DLandmarkSize.setCurrentIndex(int(self.m_app.landmark_pref["2D"]["size"]))
        self.lbl2DLandmarkColor = QPushButton()
        self.lbl2DLandmarkColor.setMinimumSize(20, 20)
        self.lbl2DLandmarkColor.setStyleSheet("background-color: " + self.m_app.landmark_pref["2D"]["color"])
        self.lbl2DLandmarkColor.setToolTip(self.m_app.landmark_pref["2D"]["color"])
        self.lbl2DLandmarkColor.setCursor(Qt.PointingHandCursor)
        self.lbl2DLandmarkColor.mousePressEvent = lambda event, dim="2D": self.on_lblLmColor_clicked(event, "2D")
        self.combo2DLandmarkSize.currentIndexChanged.connect(
            lambda event, dim="2D": self.on_comboLmSize_currentIndexChanged(event, "2D")
        )

        self.gb2DLandmarkPref.layout().addWidget(self.combo2DLandmarkSize)
        self.gb2DLandmarkPref.layout().addWidget(self.lbl2DLandmarkColor)

        self.gb3DLandmarkPref = QGroupBox()
        self.gb3DLandmarkPref.setLayout(QHBoxLayout())
        self.gb3DLandmarkPref.setTitle(self.tr("3D"))
        self.combo3DLandmarkSize = QComboBox()
        self.combo3DLandmarkSize.addItems([self.tr("Small"), self.tr("Medium"), self.tr("Large")])
        self.combo3DLandmarkSize.setCurrentIndex(int(self.m_app.landmark_pref["3D"]["size"]))
        self.lbl3DLandmarkColor = QPushButton()
        self.lbl3DLandmarkColor.setMinimumSize(20, 20)
        self.lbl3DLandmarkColor.setStyleSheet("background-color: " + self.m_app.landmark_pref["3D"]["color"])
        self.lbl3DLandmarkColor.setToolTip(self.m_app.landmark_pref["3D"]["color"])
        self.lbl3DLandmarkColor.setCursor(Qt.PointingHandCursor)
        self.lbl3DLandmarkColor.mousePressEvent = lambda event, dim="3D": self.on_lblLmColor_clicked(event, "3D")
        self.combo3DLandmarkSize.currentIndexChanged.connect(
            lambda event, dim="3D": self.on_comboLmSize_currentIndexChanged(event, "3D")
        )

        self.gb3DLandmarkPref.layout().addWidget(self.combo3DLandmarkSize)
        self.gb3DLandmarkPref.layout().addWidget(self.lbl3DLandmarkColor)

        self.landmark_layout = QHBoxLayout()
        self.landmark_layout.addWidget(self.gb2DLandmarkPref)
        self.landmark_layout.addWidget(self.gb3DLandmarkPref)
        self.landmark_widget = QWidget()
        self.landmark_widget.setLayout(self.landmark_layout)

        self.gb2DWireframePref = QGroupBox()
        self.gb2DWireframePref.setLayout(QHBoxLayout())
        self.gb2DWireframePref.setTitle(self.tr("2D"))
        self.combo2DWireframeThickness = QComboBox()
        self.combo2DWireframeThickness.addItems([self.tr("Thin"), self.tr("Medium"), self.tr("Thick")])
        self.combo2DWireframeThickness.setCurrentIndex(int(self.m_app.wireframe_pref["2D"]["thickness"]))
        self.lbl2DWireframeColor = QPushButton()
        self.lbl2DWireframeColor.setMinimumSize(20, 20)
        self.lbl2DWireframeColor.setStyleSheet("background-color: " + self.m_app.wireframe_pref["2D"]["color"])
        self.lbl2DWireframeColor.setToolTip(self.m_app.wireframe_pref["2D"]["color"])
        self.lbl2DWireframeColor.setCursor(Qt.PointingHandCursor)
        self.lbl2DWireframeColor.mousePressEvent = lambda event, dim="2D": self.on_lblWireframeColor_clicked(
            event, "2D"
        )
        self.combo2DWireframeThickness.currentIndexChanged.connect(
            lambda event, dim="2D": self.on_comboWireframeThickness_currentIndexChanged(event, "2D")
        )

        self.gb2DWireframePref.layout().addWidget(self.combo2DWireframeThickness)
        self.gb2DWireframePref.layout().addWidget(self.lbl2DWireframeColor)

        self.gb3DWireframePref = QGroupBox()
        self.gb3DWireframePref.setLayout(QHBoxLayout())
        self.gb3DWireframePref.setTitle(self.tr("3D"))
        self.combo3DWireframeThickness = QComboBox()
        self.combo3DWireframeThickness.addItems([self.tr("Thin"), self.tr("Medium"), self.tr("Thick")])
        self.combo3DWireframeThickness.setCurrentIndex(int(self.m_app.wireframe_pref["3D"]["thickness"]))
        self.lbl3DWireframeColor = QPushButton()
        self.lbl3DWireframeColor.setMinimumSize(20, 20)
        self.lbl3DWireframeColor.setStyleSheet("background-color: " + self.m_app.wireframe_pref["3D"]["color"])
        self.lbl3DWireframeColor.setToolTip(self.m_app.wireframe_pref["3D"]["color"])
        self.lbl3DWireframeColor.setCursor(Qt.PointingHandCursor)
        self.lbl3DWireframeColor.mousePressEvent = lambda event, dim="3D": self.on_lblWireframeColor_clicked(
            event, "3D"
        )
        self.combo3DWireframeThickness.currentIndexChanged.connect(
            lambda event, dim="3D": self.on_comboWireframeThickness_currentIndexChanged(event, "3D")
        )

        self.gb3DWireframePref.layout().addWidget(self.combo3DWireframeThickness)
        self.gb3DWireframePref.layout().addWidget(self.lbl3DWireframeColor)

        self.wireframe_layout = QHBoxLayout()
        self.wireframe_layout.addWidget(self.gb2DWireframePref)
        self.wireframe_layout.addWidget(self.gb3DWireframePref)
        self.wireframe_widget = QWidget()
        self.wireframe_widget.setLayout(self.wireframe_layout)

        self.gb2DIndexPref = QGroupBox()
        self.gb2DIndexPref.setLayout(QHBoxLayout())
        self.gb2DIndexPref.setTitle(self.tr("2D"))
        self.combo2DIndexSize = QComboBox()
        self.combo2DIndexSize.addItems([self.tr("Small"), self.tr("Medium"), self.tr("Large")])
        self.combo2DIndexSize.setCurrentIndex(int(self.m_app.index_pref["2D"]["size"]))
        self.lbl2DIndexColor = QPushButton()
        self.lbl2DIndexColor.setMinimumSize(20, 20)
        self.lbl2DIndexColor.setStyleSheet("background-color: " + self.m_app.index_pref["2D"]["color"])
        self.lbl2DIndexColor.setToolTip(self.m_app.index_pref["2D"]["color"])
        self.lbl2DIndexColor.setCursor(Qt.PointingHandCursor)
        self.lbl2DIndexColor.mousePressEvent = lambda event, dim="2D": self.on_lblIndexColor_clicked(event, "2D")
        self.combo2DIndexSize.currentIndexChanged.connect(
            lambda event, dim="2D": self.on_comboIndexSize_currentIndexChanged(event, "2D")
        )

        self.gb2DIndexPref.layout().addWidget(self.combo2DIndexSize)
        self.gb2DIndexPref.layout().addWidget(self.lbl2DIndexColor)

        self.gb3DIndexPref = QGroupBox()
        self.gb3DIndexPref.setLayout(QHBoxLayout())
        self.gb3DIndexPref.setTitle(self.tr("3D"))
        self.combo3DIndexSize = QComboBox()
        self.combo3DIndexSize.addItems([self.tr("Small"), self.tr("Medium"), self.tr("Large")])
        self.combo3DIndexSize.setCurrentIndex(int(self.m_app.index_pref["3D"]["size"]))
        self.lbl3DIndexColor = QPushButton()
        self.lbl3DIndexColor.setMinimumSize(20, 20)
        self.lbl3DIndexColor.setStyleSheet("background-color: " + self.m_app.index_pref["3D"]["color"])
        self.lbl3DIndexColor.setToolTip(self.m_app.index_pref["3D"]["color"])
        self.lbl3DIndexColor.setCursor(Qt.PointingHandCursor)
        self.lbl3DIndexColor.mousePressEvent = lambda event, dim="3D": self.on_lblIndexColor_clicked(event, "3D")
        self.combo3DIndexSize.currentIndexChanged.connect(
            lambda event, dim="3D": self.on_comboIndexSize_currentIndexChanged(event, "3D")
        )

        self.gb3DIndexPref.layout().addWidget(self.combo3DIndexSize)
        self.gb3DIndexPref.layout().addWidget(self.lbl3DIndexColor)

        self.index_layout = QHBoxLayout()
        self.index_layout.addWidget(self.gb2DIndexPref)
        self.index_layout.addWidget(self.gb3DIndexPref)
        self.index_widget = QWidget()
        self.index_widget.setLayout(self.index_layout)

        self.lblBgcolor = QPushButton()
        self.lblBgcolor.setMinimumSize(20, 20)
        self.lblBgcolor.setStyleSheet("background-color: " + self.m_app.bgcolor)
        self.lblBgcolor.setToolTip(self.m_app.bgcolor)
        self.lblBgcolor.setCursor(Qt.PointingHandCursor)
        self.lblBgcolor.mousePressEvent = lambda event: self.on_lblBgcolor_clicked(event)

        self.gbToolbarIconSize = QGroupBox()
        self.gbToolbarIconSize.setLayout(QHBoxLayout())
        self.gbToolbarIconSize.layout().addWidget(self.rbToolbarIconSmall)
        self.gbToolbarIconSize.layout().addWidget(self.rbToolbarIconMedium)
        self.gbToolbarIconSize.layout().addWidget(self.rbToolbarIconLarge)

        self.gbPlotColors = QGroupBox()
        self.gbPlotColors.setLayout(QGridLayout())
        self.gbPlotMarkers = QGroupBox()
        self.gbPlotMarkers.setLayout(QHBoxLayout())
        # symbol_candidate = ['o','s','^','x','+','d','v','<','>','p','h']

        self.rbPlotLarge = QRadioButton(self.tr("Large"))
        self.rbPlotLarge.setChecked(self.m_app.plot_size.lower() == "large")
        self.rbPlotLarge.clicked.connect(self.on_rbPlotLarge_clicked)
        self.rbPlotSmall = QRadioButton(self.tr("Small"))
        self.rbPlotSmall.setChecked(self.m_app.plot_size.lower() == "small")
        self.rbPlotSmall.clicked.connect(self.on_rbPlotSmall_clicked)
        self.rbPlotMedium = QRadioButton(self.tr("Medium"))
        self.rbPlotMedium.setChecked(self.m_app.plot_size.lower() == "medium")
        self.rbPlotMedium.clicked.connect(self.on_rbPlotMedium_clicked)

        self.gbPlotSize = QGroupBox()
        self.gbPlotSize.setLayout(QHBoxLayout())
        self.gbPlotSize.layout().addWidget(self.rbPlotSmall)
        self.gbPlotSize.layout().addWidget(self.rbPlotMedium)
        self.gbPlotSize.layout().addWidget(self.rbPlotLarge)

        self.btnResetMarkers = QPushButton()
        self.btnResetMarkers.setText(self.tr("Reset"))
        self.btnResetMarkers.clicked.connect(self.on_btnResetMarkers_clicked)
        self.btnResetMarkers.setMinimumSize(60, 20)
        self.btnResetMarkers.setMaximumSize(100, 20)

        self.comboMarker_list = []
        for i in range(len(self.m_app.marker_list)):
            self.comboMarker_list.append(QComboBox())
            self.comboMarker_list[i].addItems(mu.MARKER_LIST)
            self.comboMarker_list[i].setCurrentIndex(mu.MARKER_LIST.index(self.m_app.marker_list[i]))
            self.comboMarker_list[i].currentIndexChanged.connect(
                lambda event, index=i: self.on_comboMarker_currentIndexChanged(event, index)
            )
            self.gbPlotMarkers.layout().addWidget(self.comboMarker_list[i])
        self.gbPlotMarkers.layout().addWidget(self.btnResetMarkers)

        self.btnResetVivid = QPushButton()
        self.btnResetVivid.setText(self.tr("Vivid"))
        self.btnResetVivid.clicked.connect(self.on_btnResetVivid_clicked)
        self.btnResetVivid.setMinimumSize(60, 20)
        self.btnResetVivid.setMaximumSize(100, 20)
        self.btnResetPastel = QPushButton()
        self.btnResetPastel.setText(self.tr("Pastel"))
        self.btnResetPastel.clicked.connect(self.on_btnResetPastel_clicked)
        self.btnResetPastel.setMinimumSize(60, 20)
        self.btnResetPastel.setMaximumSize(100, 20)

        self.lblColor_list = []
        for i in range(len(self.m_app.color_list)):
            self.lblColor_list.append(QPushButton())
            self.lblColor_list[i].setMinimumSize(20, 20)
            # self.lblColor_list[i].setMaximumSize(20,20)
            self.lblColor_list[i].setStyleSheet("background-color: " + self.m_app.color_list[i])
            self.lblColor_list[i].setToolTip(self.m_app.color_list[i])
            self.lblColor_list[i].setCursor(Qt.PointingHandCursor)
            self.lblColor_list[i].setText(str(i + 1))
            # self.lblColor_list[i].mousePressEvent = self.on_lblColor_clicked
            self.lblColor_list[i].mousePressEvent = lambda event, index=i: self.on_lblColor_clicked(event, index)
            # self.gbPlotColors.layout().addWidget(self.lblColor_list[i])
            # put into layout in two rows
            self.gbPlotColors.layout().addWidget(self.lblColor_list[i], i // 10, i % 10)

        # self.gbPlotColors.layout().addWidget(self.rbToolbarIconSmall)
        self.gbPlotColors.layout().addWidget(self.btnResetVivid, 0, 10)
        self.gbPlotColors.layout().addWidget(self.btnResetPastel, 1, 10)

        self.lang_layout = QHBoxLayout()
        self.comboLang = QComboBox()
        self.comboLang.addItem(self.tr("English"))
        self.comboLang.addItem(self.tr("Korean"))
        if self.m_app.language == "en":
            self.comboLang.setCurrentIndex(0)
        elif self.m_app.language == "ko":
            self.comboLang.setCurrentIndex(1)
        self.comboLang.currentIndexChanged.connect(self.comboLangIndexChanged)
        self.lang_layout.addWidget(self.comboLang)
        self.lang_widget = QWidget()
        self.lang_widget.setLayout(self.lang_layout)

        self.btnOkay = QPushButton()
        self.btnOkay.setText(self.tr("Close"))
        self.btnOkay.clicked.connect(self.Okay)

        self.btnCancel = QPushButton()
        self.btnCancel.setText(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.Cancel)

        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.lblGeometry = QLabel(self.tr("Remember Geometry"))
        self.lblToolbarIconSize = QLabel(self.tr("Toolbar Icon Size"))
        self.lblPlotSize = QLabel(self.tr("Data point size"))
        self.lblPlotColors = QLabel(self.tr("Data point colors"))
        self.lblPlotMarkers = QLabel(self.tr("Data point markers"))
        self.lblLandmark = QLabel(self.tr("Landmark"))
        self.lblWireframe = QLabel(self.tr("Wireframe"))
        self.lblIndex = QLabel(self.tr("Index"))
        self.lblBgcolor = QLabel(self.tr("Background Color"))
        self.lblLang = QLabel(self.tr("Language"))

        self.main_layout.addRow(self.lblGeometry, self.gbRememberGeomegry)
        self.main_layout.addRow(self.lblToolbarIconSize, self.gbToolbarIconSize)
        self.main_layout.addRow(self.lblPlotSize, self.gbPlotSize)
        self.main_layout.addRow(self.lblPlotColors, self.gbPlotColors)
        self.main_layout.addRow(self.lblPlotMarkers, self.gbPlotMarkers)
        self.main_layout.addRow(self.lblLandmark, self.landmark_widget)
        self.main_layout.addRow(self.lblWireframe, self.wireframe_widget)
        self.main_layout.addRow(self.lblIndex, self.index_widget)
        self.main_layout.addRow(self.lblBgcolor, self.lblBgcolor)
        self.main_layout.addRow(self.lblLang, self.lang_widget)
        self.main_layout.addRow("", self.btnOkay)

        self.read_settings()

    def comboLangIndexChanged(self, index):
        if index == 0:
            self.m_app.language = "en"
        elif index == 1:
            self.m_app.language = "ko"

        if self.m_app.translator is not None:
            self.m_app.removeTranslator(self.m_app.translator)
            # print("removed translator")
            self.m_app.translator = None
        else:
            pass
        translator = QTranslator()
        translator_path = mu.resource_path(f"translations/Modan2_{self.m_app.language}.qm")
        if os.path.exists(translator_path):
            translator.load(translator_path)
            self.m_app.installTranslator(translator)
            self.m_app.translator = translator
        else:
            pass

        self.update_language()

    def on_comboMarker_currentIndexChanged(self, event, index):
        self.current_lblMarker = self.comboMarker_list[index]
        self.m_app.marker_list[self.comboMarker_list.index(self.current_lblMarker)] = (
            self.current_lblMarker.currentText()
        )
        # print(self.marker_list)

    def on_lblColor_clicked(self, event, index):
        self.current_lblColor = self.lblColor_list[index]
        # dialog = ColorPickerDialog(color=QColor(self.current_lblColor.toolTip()))
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.current_lblColor.toolTip()))  # return type is QColor
        # print("color: ", color)
        if color is not None:
            self.current_lblColor.setStyleSheet("background-color: " + color.name())
            self.current_lblColor.setToolTip(color.name())
            self.m_app.color_list[self.lblColor_list.index(self.current_lblColor)] = color.name()
            # print(self.color_list)

    def on_lblBgcolor_clicked(self, event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.m_app.bgcolor))
        if color is not None:
            self.m_app.bgcolor = color.name()
            self.lblBgcolor.setStyleSheet("background-color: " + self.m_app.bgcolor)
            self.lblBgcolor.setToolTip(self.m_app.bgcolor)
        self.parent.update_settings()

    def on_comboLmSize_currentIndexChanged(self, event, dim):
        if dim == "2D":
            self.current_comboLmSize = self.combo2DLandmarkSize
        elif dim == "3D":
            self.current_comboLmSize = self.combo3DLandmarkSize
        self.m_app.landmark_pref[dim]["size"] = self.current_comboLmSize.currentIndex()
        self.parent.update_settings()

    def on_lblLmColor_clicked(self, event, dim):
        if dim == "2D":
            self.current_lblLmColor = self.lbl2DLandmarkColor
        elif dim == "3D":
            self.current_lblLmColor = self.lbl3DLandmarkColor
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.current_lblLmColor.toolTip()))
        if color is not None:
            self.current_lblLmColor.setStyleSheet("background-color: " + color.name())
            self.current_lblLmColor.setToolTip(color.name())
            self.m_app.landmark_pref[dim]["color"] = color.name()
        self.parent.update_settings()

    def on_comboIndexSize_currentIndexChanged(self, event, dim):
        if dim == "2D":
            self.current_comboIndexSize = self.combo2DIndexSize
        elif dim == "3D":
            self.current_comboIndexSize = self.combo3DIndexSize
        self.m_app.index_pref[dim]["size"] = self.current_comboIndexSize.currentIndex()
        self.parent.update_settings()

    def on_lblIndexColor_clicked(self, event, dim):
        if dim == "2D":
            self.current_lblIndexColor = self.lbl2DIndexColor
        elif dim == "3D":
            self.current_lblIndexColor = self.lbl3DIndexColor
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.current_lblIndexColor.toolTip()))
        if color is not None:
            self.current_lblIndexColor.setStyleSheet("background-color: " + color.name())
            self.current_lblIndexColor.setToolTip(color.name())
            self.m_app.index_pref[dim]["color"] = color.name()
        self.parent.update_settings()

    def on_comboWireframeThickness_currentIndexChanged(self, event, dim):
        if dim == "2D":
            self.current_comboWireframeThickness = self.combo2DWireframeThickness
        elif dim == "3D":
            self.current_comboWireframeThickness = self.combo3DWireframeThickness
        self.m_app.wireframe_pref[dim]["thickness"] = self.current_comboWireframeThickness.currentIndex()
        self.parent.update_settings()

    def on_lblWireframeColor_clicked(self, event, dim):
        if dim == "2D":
            self.current_lblWireframeColor = self.lbl2DWireframeColor
        elif dim == "3D":
            self.current_lblWireframeColor = self.lbl3DWireframeColor
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.current_lblWireframeColor.toolTip()))
        if color is not None:
            self.current_lblWireframeColor.setStyleSheet("background-color: " + color.name())
            self.current_lblWireframeColor.setToolTip(color.name())
            self.m_app.wireframe_pref[dim]["color"] = color.name()
        self.parent.update_settings()

    def read_settings(self):
        self.m_app.remember_geometry = mu.value_to_bool(
            self.m_app.settings.value("WindowGeometry/RememberGeometry", True)
        )
        self.m_app.toolbar_icon_size = self.m_app.settings.value("ToolbarIconSize", "Medium")
        # print("toolbar_icon_size:", self.m_app.toolbar_icon_size)
        if self.m_app.toolbar_icon_size.lower() == "small":
            self.toolbar_icon_small = True
            self.toolbar_icon_large = False
            self.toolbar_icon_medium = False
        elif self.m_app.toolbar_icon_size.lower() == "medium":
            self.toolbar_icon_small = False
            self.toolbar_icon_medium = True
            self.toolbar_icon_large = False
        elif self.m_app.toolbar_icon_size.lower() == "large":
            self.toolbar_icon_small = False
            self.toolbar_icon_medium = False
            self.toolbar_icon_large = True

        for i in range(len(self.m_app.color_list)):
            self.m_app.color_list[i] = self.m_app.settings.value("DataPointColor/" + str(i), self.default_color_list[i])

        for i in range(len(self.m_app.marker_list)):
            self.m_app.marker_list[i] = self.m_app.settings.value(
                "DataPointMarker/" + str(i), self.m_app.marker_list[i]
            )
        self.m_app.plot_size = self.m_app.settings.value("PlotSize", self.m_app.plot_size)

        self.m_app.landmark_pref["2D"]["size"] = self.m_app.settings.value(
            "LandmarkSize/2D", self.m_app.landmark_pref["2D"]["size"]
        )
        self.m_app.landmark_pref["2D"]["color"] = self.m_app.settings.value(
            "LandmarkColor/2D", self.m_app.landmark_pref["2D"]["color"]
        )
        self.m_app.landmark_pref["3D"]["size"] = self.m_app.settings.value(
            "LandmarkSize/3D", self.m_app.landmark_pref["3D"]["size"]
        )
        self.m_app.landmark_pref["3D"]["color"] = self.m_app.settings.value(
            "LandmarkColor/3D", self.m_app.landmark_pref["3D"]["color"]
        )
        self.m_app.wireframe_pref["2D"]["thickness"] = self.m_app.settings.value(
            "WireframeThickness/2D", self.m_app.wireframe_pref["2D"]["thickness"]
        )
        self.m_app.wireframe_pref["2D"]["color"] = self.m_app.settings.value(
            "WireframeColor/2D", self.m_app.wireframe_pref["2D"]["color"]
        )
        self.m_app.wireframe_pref["3D"]["thickness"] = self.m_app.settings.value(
            "WireframeThickness/3D", self.m_app.wireframe_pref["3D"]["thickness"]
        )
        self.m_app.wireframe_pref["3D"]["color"] = self.m_app.settings.value(
            "WireframeColor/3D", self.m_app.wireframe_pref["3D"]["color"]
        )
        self.m_app.index_pref["2D"]["size"] = self.m_app.settings.value(
            "IndexSize/2D", self.m_app.index_pref["2D"]["size"]
        )
        self.m_app.index_pref["2D"]["color"] = self.m_app.settings.value(
            "IndexColor/2D", self.m_app.index_pref["2D"]["color"]
        )
        self.m_app.index_pref["3D"]["size"] = self.m_app.settings.value(
            "IndexSize/3D", self.m_app.index_pref["3D"]["size"]
        )
        self.m_app.index_pref["3D"]["color"] = self.m_app.settings.value(
            "IndexColor/3D", self.m_app.index_pref["3D"]["color"]
        )
        self.m_app.bgcolor = self.m_app.settings.value("BackgroundColor", self.m_app.bgcolor)
        self.m_app.language = self.m_app.settings.value("Language", "en")
        # print("read language:", self.m_app.language)
        self.update_language()

        if self.m_app.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/PreferencesDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos() + QPoint(100, 100))

    def write_settings(self):
        self.m_app.settings.setValue("ToolbarIconSize", self.m_app.toolbar_icon_size)
        self.m_app.settings.setValue("PlotSize", self.m_app.plot_size)
        self.m_app.settings.setValue("WindowGeometry/RememberGeometry", self.m_app.remember_geometry)
        # print(self.color_list)
        for i in range(len(self.m_app.marker_list)):
            self.m_app.settings.setValue("DataPointMarker/" + str(i), self.m_app.marker_list[i])

        for i in range(len(self.m_app.color_list)):
            self.m_app.settings.setValue("DataPointColor/" + str(i), self.m_app.color_list[i])

        if self.m_app.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/PreferencesDialog", self.geometry())

        self.m_app.settings.setValue("LandmarkSize/2D", self.m_app.landmark_pref["2D"]["size"])
        self.m_app.settings.setValue("LandmarkColor/2D", self.m_app.landmark_pref["2D"]["color"])
        self.m_app.settings.setValue("LandmarkSize/3D", self.m_app.landmark_pref["3D"]["size"])
        self.m_app.settings.setValue("LandmarkColor/3D", self.m_app.landmark_pref["3D"]["color"])
        self.m_app.settings.setValue("WireframeThickness/2D", self.m_app.wireframe_pref["2D"]["thickness"])
        self.m_app.settings.setValue("WireframeColor/2D", self.m_app.wireframe_pref["2D"]["color"])
        self.m_app.settings.setValue("WireframeThickness/3D", self.m_app.wireframe_pref["3D"]["thickness"])
        self.m_app.settings.setValue("WireframeColor/3D", self.m_app.wireframe_pref["3D"]["color"])
        self.m_app.settings.setValue("BackgroundColor", self.m_app.bgcolor)
        self.m_app.settings.setValue("IndexSize/2D", self.m_app.index_pref["2D"]["size"])
        self.m_app.settings.setValue("IndexColor/2D", self.m_app.index_pref["2D"]["color"])
        self.m_app.settings.setValue("IndexSize/3D", self.m_app.index_pref["3D"]["size"])
        self.m_app.settings.setValue("IndexColor/3D", self.m_app.index_pref["3D"]["color"])
        self.m_app.settings.setValue("Language", self.m_app.language)
        # print("write language:", self.m_app.language)

    def update_language(self):
        """
        Update the language of the application.

        Args:
            language (str): The language to be set.

        Returns:
            None
        """

        self.lblGeometry.setText(self.tr("Remember Geometry"))
        self.lblToolbarIconSize.setText(self.tr("Toolbar Icon Size"))
        self.lblPlotSize.setText(self.tr("Data point size"))
        self.lblPlotColors.setText(self.tr("Data point colors"))
        self.lblPlotMarkers.setText(self.tr("Data point markers"))
        self.lblLandmark.setText(self.tr("Landmark"))
        self.lblWireframe.setText(self.tr("Wireframe"))
        self.lblIndex.setText(self.tr("Index"))
        self.lblBgcolor.setText(self.tr("Background Color"))
        self.lblLang.setText(self.tr("Language"))

        self.rbRememberGeometryYes.setText(self.tr("Yes"))
        self.rbRememberGeometryNo.setText(self.tr("No"))
        self.rbToolbarIconLarge.setText(self.tr("Large"))
        self.rbToolbarIconSmall.setText(self.tr("Small"))
        self.rbToolbarIconMedium.setText(self.tr("Medium"))
        self.rbPlotLarge.setText(self.tr("Large"))
        self.rbPlotSmall.setText(self.tr("Small"))
        self.rbPlotMedium.setText(self.tr("Medium"))
        self.btnResetMarkers.setText(self.tr("Reset"))
        self.btnResetVivid.setText(self.tr("Vivid"))
        self.btnResetPastel.setText(self.tr("Pastel"))
        self.btnOkay.setText(self.tr("Okay"))
        self.btnCancel.setText(self.tr("Cancel"))

        item_list = [(self.tr("Small"), "Small"), (self.tr("Medium"), "Medium"), (self.tr("Large"), "Large")]
        for item in item_list:
            self.combo2DLandmarkSize.addItem(item[0], item[1])
            self.combo3DLandmarkSize.addItem(item[0], item[1])
            self.combo2DIndexSize.addItem(item[0], item[1])
            self.combo3DIndexSize.addItem(item[0], item[1])

        item_list = [(self.tr("Thin"), "Thin"), (self.tr("Medium"), "Medium"), (self.tr("Thick"), "Thick")]
        for item in item_list:
            self.combo2DWireframeThickness.addItem(item[0], item[1])
            self.combo3DWireframeThickness.addItem(item[0], item[1])

    def closeEvent(self, event):
        self.write_settings()
        self.parent.update_settings()
        event.accept()

    def on_btnResetMarkers_clicked(self):
        self.m_app.marker_list = mu.MARKER_LIST[:]
        for i in range(len(self.m_app.marker_list)):
            self.comboMarker_list[i].setCurrentText(self.m_app.marker_list[i])

    def on_btnResetPastel_clicked(self):
        self.m_app.color_list = mu.PASTEL_COLOR_LIST[:]
        for i in range(len(self.m_app.color_list)):
            self.lblColor_list[i].setStyleSheet("background-color: " + self.m_app.color_list[i])
            self.lblColor_list[i].setToolTip(self.m_app.color_list[i])

    def on_btnResetVivid_clicked(self):
        self.m_app.color_list = mu.VIVID_COLOR_LIST[:]
        for i in range(len(self.m_app.color_list)):
            self.lblColor_list[i].setStyleSheet("background-color: " + self.m_app.color_list[i])
            self.lblColor_list[i].setToolTip(self.m_app.color_list[i])

    def on_rbPlotLarge_clicked(self):
        self.m_app.plot_size = "Large"

    def on_rbPlotMedium_clicked(self):
        self.m_app.plot_size = "Medium"

    def on_rbPlotSmall_clicked(self):
        self.m_app.plot_size = "Small"

    def on_rbToolbarIconLarge_clicked(self):
        self.toolbar_icon_large = True
        self.toolbar_icon_medium = False
        self.toolbar_icon_small = False
        self.m_app.toolbar_icon_size = "Large"
        self.parent.update_settings()

    def on_rbToolbarIconSmall_clicked(self):
        self.toolbar_icon_small = True
        self.toolbar_icon_medium = False
        self.toolbar_icon_large = False
        self.m_app.toolbar_icon_size = "Small"
        self.parent.update_settings()

    def on_rbToolbarIconMedium_clicked(self):
        self.toolbar_icon_small = False
        self.toolbar_icon_medium = True
        self.toolbar_icon_large = False
        self.m_app.toolbar_icon_size = "Medium"
        self.parent.update_settings()

    def on_rbRememberGeometryYes_clicked(self):
        self.m_app.remember_geometry = True

    def on_rbRememberGeometryNo_clicked(self):
        self.m_app.remember_geometry = False

    def Okay(self):
        self.write_settings()
        self.close()

    def Cancel(self):
        self.close()

    def select_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select a folder", str(self.data_folder)))
        if folder:
            self.data_folder = Path(folder).resolve()
            self.edtDataFolder.setText(folder)
