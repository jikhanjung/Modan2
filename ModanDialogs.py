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
from dialogs.dataset_analysis_dialog import DatasetAnalysisDialog

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
