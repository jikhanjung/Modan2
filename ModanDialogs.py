from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QCheckBox, QColorDialog, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, QStatusBar, QMessageBox, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QSizePolicy, \
                            QTableWidget, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox, QListWidgetItem,\
                            QTabWidget, QListWidget, QSpinBox, QPlainTextEdit, QSlider, QScrollArea, QShortcut, QSpacerItem
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem, QImage,\
                        QFont, QPainter, QBrush, QMouseEvent, QWheelEvent, QDoubleValidator, QIcon, QCursor,\
                        QFontMetrics, QIntValidator, QKeySequence
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSize, QPoint, QTranslator, \
                         pyqtSlot, pyqtSignal, QItemSelectionModel, QTimer, QEvent

import logging

from OBJFileLoader import OBJ

from ModanComponents import ObjectViewer2D, ObjectViewer3D, ShapePreference, \
                            X1Y1, Morphologika, TPS, NTS

from scipy.spatial import ConvexHull
from scipy import stats

import tempfile
import cv2
import glob
import xlsxwriter
import json
import math, re, os, sys, shutil, copy, random, struct
from pathlib import Path
from PIL.ExifTags import TAGS
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib

from MdStatistics import MdPrincipalComponent, MdCanonicalVariate
from MdModel import *
import MdUtils as mu

from MdLogger import setup_logger
logger = setup_logger(__name__)


MODE = {}
MODE['NONE'] = 0
MODE['PAN'] = 12
MODE['EDIT_LANDMARK'] = 1
MODE['WIREFRAME'] = 2
MODE['READY_MOVE_LANDMARK'] = 3
MODE['MOVE_LANDMARK'] = 4
MODE['PRE_WIRE_FROM'] = 5
MODE['CALIBRATION'] = 6
MODE['VIEW'] = 7


MODE_EXPLORATION = 0
MODE_REGRESSION = 1
#MODE_GROWTH_TRAJECTORY = 2
MODE_AVERAGE = 2
MODE_COMPARISON = 3
MODE_COMPARISON2 = 4
#MODE_GRID = 6

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
COLOR = { 'RED': (1,0,0), 'GREEN': (0,1,0), 'BLUE': (0,0,1), 'YELLOW': (1,1,0), 'CYAN': (0,1,1), 'MAGENTA': (1,0,1), 'WHITE': (1,1,1), 'LIGHT_GRAY': (0.8,0.8,0.8), 'GRAY': (0.5,0.5,0.5), 'DARK_GRAY': (0.3,0.3,0.3), 'BLACK': (0,0,0)}

COLOR['SINGLE_SHAPE'] = COLOR['GREEN']
COLOR['AVERAGE_SHAPE'] = COLOR['LIGHT_GRAY']
COLOR['NORMAL_SHAPE'] = COLOR['BLUE']
COLOR['NORMAL_TEXT'] = COLOR['WHITE']
COLOR['SELECTED_SHAPE'] = COLOR['RED']
COLOR['SELECTED_TEXT'] = COLOR['RED']
COLOR['SELECTED_LANDMARK'] = COLOR['RED']
COLOR['WIREFRAME'] = COLOR['YELLOW']
COLOR['SELECTED_EDGE'] = COLOR['RED']
COLOR['BACKGROUND'] = COLOR['DARK_GRAY']

ICON = {}
ICON['landmark'] = mu.resource_path('icons/M2Landmark_2.png')
ICON['landmark_hover'] = mu.resource_path('icons/M2Landmark_2_hover.png')
ICON['landmark_down'] = mu.resource_path('icons/M2Landmark_2_down.png')
ICON['landmark_disabled'] = mu.resource_path('icons/M2Landmark_2_disabled.png')
ICON['wireframe'] = mu.resource_path('icons/M2Wireframe_2.png')
ICON['wireframe_hover'] = mu.resource_path('icons/M2Wireframe_2_hover.png')
ICON['wireframe_down'] = mu.resource_path('icons/M2Wireframe_2_down.png')
ICON['calibration'] = mu.resource_path('icons/M2Calibration_2.png')
ICON['calibration_hover'] = mu.resource_path('icons/M2Calibration_2_hover.png')
ICON['calibration_down'] = mu.resource_path('icons/M2Calibration_2_down.png')
ICON['calibration_disabled'] = mu.resource_path('icons/M2Calibration_2_disabled.png')

NEWLINE = '\n'




class DatasetOpsViewer(QLabel):
    #clicked = pyqtSignal()
    def __init__(self, widget):
        super(DatasetOpsViewer, self).__init__(widget)
        self.ds_ops = None
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.show_index = True
        self.show_wireframe = False
        self.show_baseline = False
        self.show_average = True
        #self.setMinimumSize(200,200)

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
            for idx, landmark in enumerate(obj.landmark_list):
                if landmark[0] < min_x:
                    min_x = landmark[0]
                if landmark[0] > max_x:
                    max_x = landmark[0]
                if landmark[1] < min_y:
                    min_y = landmark[1]
                if landmark[1] > max_y:
                    max_y = landmark[1]
        #print("min_x:", min_x, "max_x:", max_x, "min_y:", min_y, "max_y:", max_y)
        width = max_x - min_x
        height = max_y - min_y
        w_scale = ( self.width() * 1.0 ) / ( width * 1.5 )
        h_scale = ( self.height() * 1.0 ) / ( height * 1.5 )
        self.scale = min(w_scale, h_scale)
        self.pan_x = -min_x * self.scale + (self.width() - width * self.scale) / 2.0
        self.pan_y = -min_y * self.scale + (self.height() - height * self.scale) / 2.0
        #print("scale:", self.scale, "pan_x:", self.pan_x, "pan_y:", self.pan_y)
        self.repaint()
    
    def resizeEvent(self, ev):
        #print("resizeEvent")
        self.calculate_scale_and_pan()
        self.repaint()

        return super().resizeEvent(ev)

    def paintEvent(self, event):
        #print("paint event")
        #self.pixmap
        #return super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(mu.as_qt_color(COLOR['BACKGROUND'])))

        if self.ds_ops is None:
            return

        if self.show_wireframe == True:
            painter.setPen(QPen(mu.as_qt_color(COLOR['WIREFRAME']), 2))
            painter.setBrush(QBrush(mu.as_qt_color(COLOR['WIREFRAME'])))

            #print("wireframe 2", dataset.edge_list, dataset.wireframe)
            landmark_list = self.ds_ops.get_average_shape().landmark_list
            #print("landmark_list:", landmark_list)
            for wire in self.ds_ops.edge_list:
                #print("wire:", wire, landmark_list[wire[0]], landmark_list[wire[1]])

                if wire[0] >= len(landmark_list) or wire[1] >= len(landmark_list):
                    continue
                from_x = landmark_list[wire[0]][0]
                from_y = landmark_list[wire[0]][1]
                to_x = landmark_list[wire[1]][0]
                to_y = landmark_list[wire[1]][1]
                #[ from_x, from_y, from_z ] = landmark_list[wire[0]]
                #[ to_x, to_y, to_z ] = landmark_list[wire[1]]
                painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))
                #painter.drawLine(self.landmark_list[wire[0]][0], self.landmark_list[wire[0]][1], self.landmark_list[wire[1]][0], self.landmark_list[wire[1]][1])

        radius = 1
        painter.setFont(QFont('Helvetica', 12))
        for obj in self.ds_ops.object_list:
            #print("obj:", obj.id)
            if obj.id in self.ds_ops.selected_object_id_list:
                painter.setPen(QPen(mu.as_qt_color(COLOR['SELECTED_SHAPE']), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR['SELECTED_SHAPE'])))
            else:
                painter.setPen(QPen(mu.as_qt_color(COLOR['NORMAL_SHAPE']), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR['NORMAL_SHAPE'])))
            for idx, landmark in enumerate(obj.landmark_list):
                x = self._2canx(landmark[0])
                y = self._2cany(landmark[1])
                #print("x:", x, "y:", y, "lm", landmark[0], landmark[1], "scale:", self.scale, "pan_x:", self.pan_x, "pan_y:", self.pan_y)
                painter.drawEllipse(x-radius, y-radius, radius*2, radius*2)
                #painter.drawText(x+10, y+10, str(idx+1))

        # show average shape
        if self.show_average:
            radius=3
            for idx, landmark in enumerate(self.ds_ops.get_average_shape().landmark_list):
                painter.setPen(QPen(mu.as_qt_color(COLOR['AVERAGE_SHAPE']), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR['AVERAGE_SHAPE'])))
                x = self._2canx(landmark[0])
                y = self._2cany(landmark[1])
                painter.drawEllipse(x-radius, y-radius, radius*2, radius*2)
                if self.show_index:
                    painter.drawText(x+10, y+10, str(idx+1))

    def _2canx(self, x):
        return int(x*self.scale + self.pan_x)
    def _2cany(self, y):
        return int(y*self.scale + self.pan_y)


class PicButton(QAbstractButton):
    def __init__(self, pixmap, pixmap_hover, pixmap_pressed, pixmap_disabled=None, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap
        self.pixmap_hover = pixmap_hover
        self.pixmap_pressed = pixmap_pressed
        if pixmap_disabled is None:
            result = pixmap_hover.copy()
            image = QPixmap.toImage(result)
            grayscale = image.convertToFormat(QImage.Format_Grayscale8)
            pixmap_disabled = QPixmap.fromImage(grayscale)
            #self.Changed_view.emit(pixmap)            
        self.pixmap_disabled = pixmap_disabled

        self.pressed.connect(self.update)
        self.released.connect(self.update)

    def paintEvent(self, event):
        pix = self.pixmap_hover if self.underMouse() else self.pixmap
        if self.isDown():
            pix = self.pixmap_pressed
        if self.isEnabled() == False and self.pixmap_disabled is not None:
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
    def __init__(self,parent):
        super().__init__()
        #self.setupUi(self)
        #self.setGeometry(200, 250, 400, 250)
        self.setWindowTitle("Modan2 - Progress Dialog")
        self.parent = parent
        self.setGeometry(QRect(100, 100, 320, 180))
        self.move(self.parent.pos()+QPoint(100,100))

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50,50, 50, 50)

        self.lbl_text = QLabel(self)
        #self.lbl_text.setGeometry(50, 50, 320, 80)
        #self.pb_progress = QProgressBar(self)
        self.pb_progress = QProgressBar(self)
        #self.pb_progress.setGeometry(50, 150, 320, 40)
        self.pb_progress.setValue(0)
        self.stop_progress = False
        self.btnStop = QPushButton(self)
        #self.btnStop.setGeometry(175, 200, 50, 30)
        self.btnStop.setText("Stop")
        self.btnStop.clicked.connect(self.set_stop_progress)
        self.layout.addWidget(self.lbl_text)
        self.layout.addWidget(self.pb_progress)
        self.layout.addWidget(self.btnStop)
        self.setLayout(self.layout)

    def set_stop_progress(self):
        self.stop_progress = True

    def set_progress_text(self,text_format):
        self.text_format = text_format

    def set_max_value(self,max_value):
        self.max_value = max_value

    def set_curr_value(self,curr_value):
        self.curr_value = curr_value
        self.pb_progress.setValue(int((self.curr_value/float(self.max_value))*100))
        self.lbl_text.setText(self.text_format.format(self.curr_value, self.max_value))
        #self.lbl_text.setText(label_text)
        self.update()
        QApplication.processEvents()

class CalibrationDialog(QDialog):
    def __init__(self,parent,dist):
        super().__init__()
        self.setWindowTitle("Calibration")
        self.parent = parent
        self.last_calibration_unit = "mm"
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 320, 180))
        self.move(self.parent.pos()+QPoint(100,100))
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
        #print("last_calibration_unit:", self.last_calibration_unit)
        self.comboUnit.setCurrentText(self.last_calibration_unit)

        if dist is not None:
            self.set_pixel_number(dist)

    def read_settings(self):
        #print("read settings")
        self.last_calibration_unit = self.m_app.settings.value("Calibration/Unit", self.last_calibration_unit)
        #print("last_calibration_unit:", self.last_calibration_unit)
    
    def write_settings(self):
        #print("write settings")
        self.m_app.settings.setValue("Calibration/Unit", self.last_calibration_unit)
        #print("last_calibration_unit:", self.last_calibration_unit)


    def set_pixel_number(self, pixel_number):
        self.pixel_number = pixel_number
        # show number of pixel in calibration text 
        self.lblText1.setText("Enter the unit length in metric scale.") 
        self.lblText2.setText(f"{self.pixel_number:.2f} pixels are equivalent to:")
        # select all text in edtLength
        self.edtLength.selectAll()
        
    def btnOK_clicked(self):
        #self.parent.calibration_length = float(self.edtLength.text())
        #self.parent.calibration_unit = self.cbxUnit.currentText()        
        self.parent.set_object_calibration( self.pixel_number, float(self.edtLength.text()),self.comboUnit.currentText())
        self.last_calibration_unit = self.comboUnit.currentText()
        #print("last_calibration_unit:", self.last_calibration_unit)
        self.write_settings()
        self.close()
    
    def btnCancel_clicked(self):
        self.close()

class DatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Dataset Information"))
        self.parent = parent
        #print(self.parent.pos())
        #self.setGeometry(QRect(100, 100, 600, 400))
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        #self.move(self.parent.pos()+QPoint(100,100))
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
        self.lstVariableName.setEditTriggers(QListWidget.DoubleClicked|QListWidget.EditKeyPressed|QListWidget.SelectedClicked)
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

        #self.edtDataFolder.setText(str(self.data_folder.resolve()))
        #self.edtServerAddress.setText(self.server_address)
        #self.edtServerPort.setText(self.server_port)

    def addVariable(self):
        item = QListWidgetItem(self.tr("New Variable"))
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setData(Qt.UserRole, -1)
        self.lstVariableName.addItem(item)
        #print("new variable")
        self.lstVariableName.editItem(item)
    
    def deleteVariable(self):
        for item in self.lstVariableName.selectedItems():
            self.lstVariableName.takeItem(self.lstVariableName.row(item))
    
    def moveUp(self):
        row = self.lstVariableName.currentRow()
        if row > 0:
            item = self.lstVariableName.takeItem(row)
            self.lstVariableName.insertItem(row-1, item)
            self.lstVariableName.setCurrentItem(item)

    def moveDown(self):
        row = self.lstVariableName.currentRow()
        if row < self.lstVariableName.count() - 1:
            item = self.lstVariableName.takeItem(row)
            self.lstVariableName.insertItem(row+1, item)
            self.lstVariableName.setCurrentItem(item)

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/DatasetDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos()+QPoint(100,100))


    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/DatasetDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def load_parent_dataset(self,curr_dataset_id = None):
        self.cbxParent.clear()
        datasets = MdDataset.select()
        for dataset in datasets:
            if curr_dataset_id is None or dataset.id != curr_dataset_id:
                self.cbxParent.addItem(dataset.dataset_name, dataset.id)

    def read_dataset(self, dataset_id):
        try:
            dataset = MdDataset.get(dataset.id == dataset_id)
        except:
            dataset = None
        self.dataset = dataset
        #self
        #return dataset

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
        #print(dataset.dimension,self.dataset.objects)
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
        #self.edtVariableNameStr.setText(dataset.propertyname_str)
    
    def set_parent_dataset(self, parent_dataset):
        #print("parent:", parent_dataset_id, "dataset:", self.dataset)
        if parent_dataset is None:
            self.cbxParent.setCurrentIndex(-1)
        else:
            self.cbxParent.setCurrentIndex(self.cbxParent.findData(parent_dataset.id))
            if parent_dataset.dimension == 2:
                self.rbtn2D.setChecked(True)
            elif parent_dataset.dimension == 3:
                self.rbtn3D.setChecked(True)
            #self.rbtn2D.setEnabled(False)
            #self.rbtn3D.setEnabled(False)
    '''
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
    '''
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
                logger.info("Dataset name: %s, Dataset desc: %s", 
                        self.dataset.dataset_name, 
                        self.dataset.dataset_desc)
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
                logger.info("Wireframe: %s, Baseline: %s, Polygons: %s", 
                        self.dataset.wireframe, 
                        self.dataset.baseline, 
                        self.dataset.polygons)
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
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save dataset: {str(e)}"
            )
            return
    def Delete(self):
        ret = QMessageBox.question(self, "", self.tr("Are you sure to delete this dataset?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        #print("ret:", ret)
        if ret == QMessageBox.Yes:
            self.dataset.delete_instance()
            self.parent.selected_dataset = None
            #self.dataset.delete_dataset()
        #self.delete_dataset()
        self.accept()

    def Cancel(self):
        self.reject()

class ObjectDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Object Information"))
        self.parent = parent
        #print(self.parent.pos())
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        #self.move(self.parent.pos()+QPoint(50,50))
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close) 

        self.status_bar = QStatusBar()
        self.landmark_list = []

        self.hsplitter = QSplitter(Qt.Horizontal)
        self.vsplitter = QSplitter(Qt.Vertical)

        #self.vsplitter.addWidget(self.tableView)
        #self.vsplitter.addWidget(self.tableWidget)

        #self.hsplitter.addWidget(self.treeView)
        #self.hsplitter.addWidget(self.vsplitter)

        self.inputLayout = QHBoxLayout()
        self.inputCoords = QWidget()
        self.inputCoords.setLayout(self.inputLayout)
        self.inputX = QLineEdit()
        self.inputY = QLineEdit()
        self.inputZ = QLineEdit()

        self.inputLayout.addWidget(self.inputX)
        self.inputLayout.addWidget(self.inputY)
        self.inputLayout.addWidget(self.inputZ)
        self.inputLayout.setContentsMargins(0,0,0,0)
        self.inputLayout.setSpacing(0)
        self.btnAddInput = QPushButton()
        self.btnAddInput.setText(self.tr("Add"))
        self.inputLayout.addWidget(self.btnAddInput)
        self.inputX.returnPressed.connect(self.input_coords_process)
        self.inputY.returnPressed.connect(self.input_coords_process)
        self.inputZ.returnPressed.connect(self.input_coords_process)
        self.inputX.textChanged[str].connect(self.x_changed)
        self.btnAddInput.clicked.connect(self.input_coords_process)

        self.edtObjectName = QLineEdit()
        self.edtSequence = QLineEdit()
        self.edtSequence.setValidator(QIntValidator())
        self.edtObjectDesc = QTextEdit()
        self.edtObjectDesc.setMaximumHeight(100)
        self.edtLandmarkStr = QTableWidget()
        self.lblDataset = QLabel()

        self.main_layout = QVBoxLayout()
        self.sub_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        self.object_view = None

        self.object_view_3d = ObjectViewer3D(self)
        self.object_view_3d.setMinimumWidth(300)
        self.object_view_3d.setMinimumHeight(300)
        self.object_view_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.object_view_3d.object_dialog = self
        self.object_view_3d.setMouseTracking(True)
        self.object_view_3d.show_index = True  # Enable landmark index display in ObjectDialog

        self.object_view_2d = ObjectViewer2D(self)
        self.object_view_2d.object_dialog = self
        self.object_view_2d.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        #self.image_label.clicked.connect(self.on_image_clicked)

        self.pixmap = QPixmap(1024,768)
        self.object_view_2d.setPixmap(self.pixmap)

        self.form_layout = QFormLayout()
        self.lblDatasetName = QLabel(self.tr("Dataset Name"))
        self.lblObjectName = QLabel(self.tr("Object Name"))
        self.lblSequence = QLabel(self.tr("Sequence"))
        self.lblObjectDesc = QLabel(self.tr("Description"))
        self.lblLandmarkStr = QLabel(self.tr("Landmarks"))
        self.form_layout.addRow(self.lblDatasetName, self.lblDataset)
        self.form_layout.addRow(self.lblObjectName, self.edtObjectName)
        self.form_layout.addRow(self.lblSequence, self.edtSequence)
        self.form_layout.addRow(self.lblObjectDesc, self.edtObjectDesc)
        self.form_layout.addRow(self.lblLandmarkStr, self.edtLandmarkStr)
        self.form_layout.addRow("", self.inputCoords)

        self.btnGroup = QButtonGroup() 
        self.btnLandmark = PicButton(QPixmap(ICON['landmark']), QPixmap(ICON['landmark_hover']), QPixmap(ICON['landmark_down']), QPixmap(ICON['landmark_disabled']))
        self.btnWireframe = PicButton(QPixmap(ICON['wireframe']), QPixmap(ICON['wireframe_hover']), QPixmap(ICON['wireframe_down']))
        self.btnCalibration = PicButton(QPixmap(ICON['calibration']), QPixmap(ICON['calibration_hover']), QPixmap(ICON['calibration_down']),QPixmap(ICON['calibration_disabled']))
        self.btnGroup.addButton(self.btnLandmark)
        self.btnGroup.addButton(self.btnWireframe)
        self.btnGroup.addButton(self.btnCalibration)
        self.btnLandmark.setCheckable(True)
        self.btnWireframe.setCheckable(True)
        self.btnCalibration.setCheckable(True)
        self.btnLandmark.setChecked(True)
        self.btnWireframe.setChecked(False)
        self.btnCalibration.setChecked(False)
        self.btnLandmark.setAutoExclusive(True)
        self.btnWireframe.setAutoExclusive(True)
        self.btnCalibration.setAutoExclusive(True)
        self.btnLandmark.clicked.connect(self.btnLandmark_clicked)
        self.btnWireframe.clicked.connect(self.btnWireframe_clicked)
        self.btnCalibration.clicked.connect(self.btnCalibration_clicked)
        BUTTON_SIZE = 48
        self.btnLandmark.setFixedSize(BUTTON_SIZE,BUTTON_SIZE)
        self.btnWireframe.setFixedSize(BUTTON_SIZE,BUTTON_SIZE)
        self.btnCalibration.setFixedSize(BUTTON_SIZE,BUTTON_SIZE)
        self.btn_layout2 = QGridLayout()
        self.btn_layout2.addWidget(self.btnLandmark,0,0)
        self.btn_layout2.addWidget(self.btnWireframe,0,1)
        self.btn_layout2.addWidget(self.btnCalibration,1,0)

        self.cbxShowIndex = QCheckBox()
        self.cbxShowIndex.setText(self.tr("Index"))
        self.cbxShowIndex.setChecked(True)
        self.cbxShowWireframe = QCheckBox()
        self.cbxShowWireframe.setText(self.tr("Wireframe"))
        self.cbxShowWireframe.setChecked(True)
        self.cbxShowPolygon = QCheckBox()
        self.cbxShowPolygon.setText(self.tr("Polygon"))
        self.cbxShowPolygon.setChecked(True)
        self.cbxShowBaseline = QCheckBox()
        self.cbxShowBaseline.setText(self.tr("Baseline"))
        self.cbxShowBaseline.setChecked(True)
        self.cbxShowBaseline.hide()
        self.cbxAutoRotate = QCheckBox()
        self.cbxAutoRotate.setText(self.tr("Rotate"))
        self.cbxAutoRotate.setChecked(False)
        self.cbxShowModel = QCheckBox()
        self.cbxShowModel.setText(self.tr("3D Model"))
        self.cbxShowModel.setChecked(False)
        self.btnAddFile = QPushButton()
        self.btnAddFile.setText(self.tr("Load Image"))
        self.btnAddFile.clicked.connect(self.btnAddFile_clicked)

        #self.btnFBO = QPushButton()
        #self.btnFBO.setText("FBO")
        #self.btnFBO.clicked.connect(self.btnFBO_clicked)


        self.left_widget = QWidget()
        self.left_widget.setLayout(self.form_layout)

        self.right_top_widget = QWidget()
        self.right_top_widget.setLayout(self.btn_layout2)
        self.right_middle_widget = QWidget()
        self.right_middle_layout = QVBoxLayout()
        self.right_middle_layout.addWidget(self.cbxShowIndex)
        self.right_middle_layout.addWidget(self.cbxShowWireframe)
        self.right_middle_layout.addWidget(self.cbxShowPolygon)
        self.right_middle_layout.addWidget(self.cbxShowBaseline)
        self.right_middle_layout.addWidget(self.cbxShowModel)
        self.right_middle_layout.addWidget(self.cbxAutoRotate)
        self.right_middle_layout.addWidget(self.btnAddFile)
        #self.right_middle_layout.addWidget(self.btnFBO)
        self.right_middle_widget.setLayout(self.right_middle_layout)
        self.right_bottom_widget = QWidget()
        self.vsplitter.addWidget(self.right_top_widget)
        self.vsplitter.addWidget(self.right_middle_widget)
        self.vsplitter.addWidget(self.right_bottom_widget)
        self.vsplitter.setSizes([50,50,400])
        self.vsplitter.setStretchFactor(0, 0)
        self.vsplitter.setStretchFactor(1, 0)
        self.vsplitter.setStretchFactor(2, 1)

        self.object_view_layout = QVBoxLayout()
        self.object_view_layout.addWidget(self.object_view_2d)
        self.object_view_layout.addWidget(self.object_view_3d)
        self.object_view_widget = QWidget()
        self.object_view_widget.setLayout(self.object_view_layout)


        self.hsplitter.addWidget(self.left_widget)
        self.hsplitter.addWidget(self.object_view_widget)
        #self.hsplitter.addWidget(self.object_view_3d)
        self.hsplitter.addWidget(self.vsplitter)
        #self.hsplitter.addWidget(self.right_widget)
        self.hsplitter.setSizes([200,800,100])
        self.hsplitter.setStretchFactor(0, 0)
        self.hsplitter.setStretchFactor(1, 1)
        self.hsplitter.setStretchFactor(2, 0)

        self.btnPrevious = QPushButton()
        self.btnPrevious.setText(self.tr("Previous"))
        self.btnPrevious.clicked.connect(self.Previous)
        self.btnNext = QPushButton()
        self.btnNext.setText(self.tr("Next"))
        self.btnNext.clicked.connect(self.Next)

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
        btn_layout.addWidget(self.btnPrevious)
        btn_layout.addWidget(self.btnOkay)
        btn_layout.addWidget(self.btnDelete)
        btn_layout.addWidget(self.btnCancel)
        btn_layout.addWidget(self.btnNext)

        self.status_bar.setMaximumHeight(20)
        #self.main_layout.addLayout(self.sub_layout)
        self.main_layout.addWidget(self.hsplitter)
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.status_bar)

        self.dataset = None
        self.object = None
        self.edtPropertyList = []
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        self.cbxShowPolygon.stateChanged.connect(self.show_polygon_state_changed)
        self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        self.cbxAutoRotate.stateChanged.connect(self.auto_rotate_state_changed)
        self.cbxShowModel.stateChanged.connect(self.show_model_state_changed)
        self.object_deleted = False

        #self.show_index_state_changed()

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/ObjectDialog", QRect(100, 100, 1400, 800)))
        else:
            self.setGeometry(QRect(100, 100, 1400, 800))
            self.move(self.parent.pos()+QPoint(100,100))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/ObjectDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def btnAddFile_clicked(self):
        # open file dialog
        #print("btnAddFile_clicked")
        if self.dataset is None:

            return
        #print("btnAddFile_clicked")

        if self.dataset.dimension == 2:
            extension = " ".join([ "*."+x for x in mu.IMAGE_EXTENSION_LIST])
            file_path, _ = QFileDialog.getOpenFileName(self, self.tr("Open File"), mu.USER_PROFILE_DIRECTORY, "Image Files ("+extension+")")
            if file_path == "":
                return
            self.object_view.set_image(file_path)
            self.object_view.calculate_resize()
            self.set_object_name(Path(file_path).stem)
            self.enable_landmark_edit()


        else:
            file_path, _ = QFileDialog.getOpenFileName(self, self.tr("Open File"), mu.USER_PROFILE_DIRECTORY, "3D Files (*.obj *.stl *.ply)")
            if file_path == "":
                return
            #print("file_path 1:", file_path)
            file_path = mu.process_3d_file(file_path)
            #print("file_path 2:", file_path)

            self.object_view.set_threed_model(file_path)
            self.object_view.calculate_resize()
            self.set_object_name(Path(file_path).stem)
            self.enable_landmark_edit()

        

    def set_object_calibration(self, pixels, calibration_length, calibration_unit):
        self.object.pixels_per_mm = pixels * 1.0 / calibration_length
        if calibration_unit == 'mm':
            self.object.pixels_per_mm /= 1.0
        elif calibration_unit == 'cm':
            self.object.pixels_per_mm /= 10.0
        elif calibration_unit == 'm':
            self.object.pixels_per_mm /= 1000.0
        elif calibration_unit == 'um':
            self.object.pixels_per_mm /= 0.001
        elif calibration_unit == 'nm':
            self.object.pixels_per_mm /= 0.000001
        self.object_view_2d.pixels_per_mm = self.object.pixels_per_mm
        #print(pixels, calibration_length, calibration_unit, self.object.pixels_per_mm)
        #self.object.save()

    #def btnFBO_clicked(self):
    #    self.object_view_3d.show_picker_buffer()

    def show_index_state_changed(self):
        self.object_view.show_index = self.cbxShowIndex.isChecked()
        self.object_view.update()

    def show_model_state_changed(self, int):
        self.object_view.show_model = self.cbxShowModel.isChecked()
        self.object_view.update()

    def show_baseline_state_changed(self, int):
        self.object_view.show_baseline = self.cbxShowBaseline.isChecked()
        self.object_view.update()

    def auto_rotate_state_changed(self, int):
        self.object_view.auto_rotate = self.cbxAutoRotate.isChecked()

    def show_wireframe_state_changed(self, int):
        self.object_view.show_wireframe = self.cbxShowWireframe.isChecked()
        self.object_view.update()

    def show_polygon_state_changed(self, int):
        self.object_view.show_polygon = self.cbxShowPolygon.isChecked()
        self.object_view.update()

    def btnLandmark_clicked(self):
        #self.edit_mode = MODE_ADD_LANDMARK
        #if self.object.image.count() == 0:
        #    return
        self.object_view.set_mode(MODE['EDIT_LANDMARK'])
        self.object_view.update()
        self.btnLandmark.setDown(True)
        self.btnLandmark.setChecked(True)
        self.btnWireframe.setDown(False)
        self.btnWireframe.setChecked(False)
        self.btnCalibration.setDown(False)
        self.btnCalibration.setChecked(False)

    def btnCalibration_clicked(self):
        #self.edit_mode = MODE_ADD_LANDMARK
        self.object_view.set_mode(MODE['CALIBRATION'])
        self.object_view.update()
        self.btnCalibration.setDown(True)
        self.btnCalibration.setChecked(True)
        self.btnLandmark.setDown(False)
        self.btnLandmark.setChecked(False)
        self.btnWireframe.setDown(False)
        self.btnWireframe.setChecked(False)

    def calibrate(self, dist):
        logger = logging.getLogger(__name__)
        logger.debug(f"calibrate start - edit_mode: {self.object_view.edit_mode}, CALIBRATION: {MODE['CALIBRATION']}")
        self.calibrate_dlg = CalibrationDialog(self, dist)
        logger.debug(f"calibrate dialog created - edit_mode: {self.object_view.edit_mode}")
        self.calibrate_dlg.setModal(True)
        logger.debug(f"calibrate before exec - edit_mode: {self.object_view.edit_mode}")
        self.calibrate_dlg.exec_()
        logger.debug(f"calibrate after exec - edit_mode: {self.object_view.edit_mode}")

    def btnWireframe_clicked(self):
        #self.edit_mode = MODE_ADD_LANDMARK
        self.object_view.set_mode(MODE['WIREFRAME'])
        self.object_view.update()
        self.btnWireframe.setDown(True)
        self.btnWireframe.setChecked(True)
        self.btnLandmark.setDown(False)
        self.btnLandmark.setChecked(False)
        self.btnCalibration.setDown(False)
        self.btnCalibration.setChecked(False)

    def set_object_name(self, name):
        #print("set_object_name", self.edtObjectName.text(), name)

        if self.edtObjectName.text() == "":
            self.edtObjectName.setText(name)

    def set_dataset(self, dataset):
        #print("object dialog set_dataset", dataset.dataset_name)
        if dataset is None:
            self.dataset = None
            self.lblDataset.setText("No dataset selected")
            return
        self.dataset = dataset
        self.lblDataset.setText(dataset.dataset_name)

        header = self.edtLandmarkStr.horizontalHeader()    
        if self.dataset.dimension == 2:
            self.edtLandmarkStr.setColumnCount(2)
            self.edtLandmarkStr.setHorizontalHeaderLabels(["X","Y"])
            #self.edtLandmarkStr.setColumnWidth(0, 80)
            #self.edtLandmarkStr.setColumnWidth(1, 80)
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            self.cbxAutoRotate.hide()
            self.cbxShowModel.hide()
            #self.btnCalibration.show()
            self.inputZ.hide()
            self.object_view_3d.hide()
            self.object_view = self.object_view_2d
            input_width = 80
        elif self.dataset.dimension == 3:
            self.edtLandmarkStr.setColumnCount(3)
            self.edtLandmarkStr.setHorizontalHeaderLabels(["X","Y","Z"])
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            self.cbxAutoRotate.show()
            self.cbxShowModel.show()
            #self.btnCalibration.hide()
            self.inputZ.show()
            self.object_view_2d.hide()
            self.object_view = self.object_view_3d
            input_width = 60
        if self.dataset.propertyname_str is not None and self.dataset.propertyname_str != "":
            self.edtPropertyList = []
            self.dataset.unpack_variablename_str()
            for variablename in self.dataset.variablename_list:
                self.edtPropertyList.append( QLineEdit() )
                self.form_layout.addRow(variablename, self.edtPropertyList[-1])
        #self.inputX.setFixedWidth(input_width)
        #self.inputY.setFixedWidth(input_width)
        #self.inputZ.setFixedWidth(input_width)
        #self.btnAddInput.setFixedWidth(input_width)

    def set_object(self, object):
        #print("set_object", object.object_name, object.dataset.dimension)
        if object is not None:
            self.object = object
            self.edtObjectName.setText(object.object_name)
            self.edtSequence.setText(str(object.sequence or 1))
            self.edtObjectDesc.setText(object.object_desc)
            #self.edtLandmarkStr.setText(object.landmark_str)
            object.unpack_landmark()
            self.landmark_list = copy.deepcopy(object.landmark_list)
            # Use object's dataset if self.dataset is None
            dataset_to_use = self.dataset if self.dataset is not None else object.dataset
            if dataset_to_use is not None:
                self.edge_list = dataset_to_use.unpack_wireframe()
            else:
                self.edge_list = []
            #for lm in self.landmark_list:
            #    self.show_landmark(*lm)
            #self.show_landmarks()

        # Use object's dataset if self.dataset is None
        dataset_to_use = self.dataset if self.dataset is not None else (object.dataset if object is not None else None)
        if dataset_to_use is not None and dataset_to_use.dimension == 3:
            #print("set_object 3d 1")
            self.object_view = self.object_view_3d
            self.object_view.auto_rotate = False
            #obj_ops = MdObjectOps(object)
            #self.object_view.set_dataset(object.dataset)
            #self.btnLandmark.setDisabled(True)
            #print("set_object 3d 2")
            self.btnCalibration.setDisabled(True)
            self.cbxAutoRotate.show()
            self.cbxShowModel.show()
            self.cbxShowPolygon.show()
            #self.cbxShowModel.setEnabled(True)
            self.btnAddFile.setText(self.tr("Load 3D Model"))
            #print("set_object 3d 3")
            if object is not None:
                #print("object dialog self.landmark_list in set object 3d", self.landmark_list)
                self.object_view.set_object(object)
                self.object_view.landmark_list = self.landmark_list
                self.object_view.update_landmark_list()
                self.object_view.calculate_resize()
                if object.threed_model is not None and len(object.threed_model) > 0:
                    self.enable_landmark_edit()
                    #self.cbxShowModel.show()
                    self.cbxShowModel.setEnabled(True)
                    self.cbxShowModel.setChecked(True)
                else:
                    self.disable_landmark_edit()
                    self.cbxShowModel.setEnabled(False)
                #self.object_view.landmark_list = self.landmark_list
        else:
            #print("set_object 2d")
            self.object_view = self.object_view_2d
            self.cbxAutoRotate.hide()
            self.cbxShowModel.hide()
            self.cbxShowPolygon.hide()
            #self.cbxShowModel.setEnabled(True)
            self.btnAddFile.setText(self.tr("Load Image"))

            if object is not None:
                if object.image is not None and len(object.image) > 0:
                    #img = object.image[0]
                    #image_path = img.get_file_path(self.m_app.storage_directory)
                    ##check if image_path exists
                    #if os.path.exists(image_path):
                    #    self.object_view.set_image(image_path)
                    self.btnCalibration.setEnabled(True)
                    self.enable_landmark_edit()
                    if object.pixels_per_mm is None:
                        self.btnCalibration_clicked()
                        #self.btnCalibration.setDisabled(False)
                else:
                    self.btnCalibration.setDisabled(True)
                    self.disable_landmark_edit()
                #elif len(self.landmark_list) > 0:
                #print("objectdialog self.landmark_list in set object 2d", self.landmark_list)
                self.object_view.clear_object()
                self.object_view.set_object(object)
                self.object_view.image_changed = False
                self.object_view.landmark_list = self.landmark_list
                self.object_view.update_landmark_list()
                self.object_view.calculate_resize()

        if len(self.dataset.variablename_list) >0:
            self.object.unpack_variable()
            self.dataset.unpack_variablename_str()
            for idx, propertyname in enumerate(self.dataset.variablename_list):
                if idx < len(object.variable_list):
                    self.edtPropertyList[idx].setText(object.variable_list[idx])

            #self.object_view_3d.landmark_list = self.landmark_list
        #self.set_dataset(object.dataset)
        self.show_index_state_changed()
        self.object_view.align_object()
        self.show_landmarks()

    def enable_landmark_edit(self):
        self.btnLandmark.setEnabled(True)
        self.btnLandmark.setDown(True)
        self.object_view.set_mode(MODE['EDIT_LANDMARK'])

    def disable_landmark_edit(self):
        self.btnLandmark.setDisabled(True)
        self.btnLandmark.setDown(False)
        self.object_view.set_mode(MODE['VIEW'])


    @pyqtSlot(str)
    def x_changed(self, text):
        # if text is multiline and tab separated, add to table
        #print("x_changed called with", text)
        if "\n" in text:
            lines = text.split("\n")
            for line in lines:
                #print(line)
                if "\t" in line:
                    coords = line.split("\t")
                    #add landmarks using add_landmark method
                    if self.dataset.dimension == 2 and len(coords) == 2:
                        self.add_landmark(coords[0], coords[1])
                    elif self.dataset.dimension == 3 and len(coords) == 3:
                        self.add_landmark(coords[0], coords[1], coords[2])
            self.inputX.setText("")
            self.inputY.setText("")
            self.inputZ.setText("")

    def update_landmark(self, idx, x, y, z=None):
        if self.dataset.dimension == 2:
            self.landmark_list[idx] = [x,y]
        elif self.dataset.dimension == 3:
            self.landmark_list[idx] = [x,y,z]
        self.show_landmarks()

    def add_landmark(self, x, y, z=None):
        #print("adding landmark", x, y, z, self.landmark_list)
        if self.dataset.dimension == 2:
            self.landmark_list.append([float(x),float(y)])
        elif self.dataset.dimension == 3:
            self.landmark_list.append([float(x),float(y),float(z)])
        self.show_landmarks()
        #self.object_view.calculate_resize()

    def delete_landmark(self, idx):
        #print("delete_landmark", idx)
        self.landmark_list.pop(idx)
        self.show_landmarks()

    def input_coords_process(self):
        x_str = self.inputX.text()
        y_str = self.inputY.text()
        z_str = self.inputZ.text()
        if self.dataset.dimension == 2:
            if x_str == "" or y_str == "":
                return
            # add landmark to table using add_landmark method
            self.add_landmark(x_str, y_str)

        elif self.dataset.dimension == 3:
            if x_str == "" or y_str == "" or z_str == "":
                return
            self.add_landmark(x_str, y_str, z_str)
        self.inputX.setText("")
        self.inputY.setText("")
        self.inputZ.setText("")
        self.inputX.setFocus()
        self.object_view.update_landmark_list()
        self.object_view.calculate_resize()

    def show_landmarks(self):
        self.edtLandmarkStr.setRowCount(len(self.landmark_list))
        for idx, lm in enumerate(self.landmark_list):
            #print(idx, lm)

            item_x = QTableWidgetItem(str(float(lm[0])*1.0))
            item_x.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            self.edtLandmarkStr.setItem(idx, 0, item_x)

            item_y = QTableWidgetItem(str(float(lm[1])*1.0))
            item_y.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            self.edtLandmarkStr.setItem(idx, 1, item_y)

            if self.dataset.dimension == 3:
                item_z = QTableWidgetItem(str(float(lm[2])*1.0))
                item_z.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                self.edtLandmarkStr.setItem(idx, 2, item_z)
        

    def save_object(self):
        #print("save object")

        if self.object is None:
            self.object = MdObject()
        self.object.dataset_id = self.dataset.id
        self.object.object_name = self.edtObjectName.text()
        self.object.sequence = int(self.edtSequence.text())
        self.object.object_desc = self.edtObjectDesc.toPlainText()
        #self.object.landmark_str = self.edtLandmarkStr.text()
        self.object.landmark_str = self.make_landmark_str()
        #print("scale:", self.object.pixels_per_mm)
        if self.dataset.propertyname_str is not None and self.dataset.propertyname_str != "":
            self.object.property_str = ",".join([ edt.text() for edt in self.edtPropertyList ])

        self.object.save()
        #print("object_view_2d.fullpath in save_object:", self.object_view_2d.fullpath, "has image", self.object.has_image(), "image changed", self.object_view_2d.image_changed)
        if self.object_view_2d.fullpath is not None:
            if not self.object.has_image():
                img = self.object.add_image(self.object_view_2d.fullpath)
                img.save()
            elif self.object_view_2d.image_changed is True:
                img = self.object.update_image(self.object_view_2d.fullpath)
                img.save()
            #print("img:", img)
            
        elif self.object_view_3d.fullpath is not None and not self.object.has_threed_model():
            mdl = self.object.add_threed_model(self.object_view_3d.fullpath)
            mdl.save()

    def make_landmark_str(self):
        # from table, make landmark_str
        landmark_str = ""
        for row in range(self.edtLandmarkStr.rowCount()):
            for col in range(self.edtLandmarkStr.columnCount()):
                landmark_str += self.edtLandmarkStr.item(row, col).text()
                if col < self.edtLandmarkStr.columnCount()-1:
                    landmark_str += "\t"
            if row < self.edtLandmarkStr.rowCount()-1:
                landmark_str += "\n"
        return landmark_str

    def set_tableview(self, tableview):
        self.tableView = tableview

    def Delete(self):
        ret = QMessageBox.question(self, "", self.tr("Are you sure to delete this object?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            if self.object.image.count() > 0:
                image_path = self.object.image[0].get_file_path(self.m_app.storage_directory)
                if os.path.exists(image_path):
                    os.remove(image_path)
            self.object.delete_instance()
        #self.delete_dataset()
        self.object_deleted = True
        self.accept()

    def get_selected_object_list(self):
        selected_indexes = self.tableView.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return None

        new_index_list = []
        model = selected_indexes[0].model()
        if hasattr(model, 'mapToSource'):
            for index in selected_indexes:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
            selected_indexes = new_index_list
        
        selected_object_list = []
        for index in selected_indexes:
            item = self.object_model.itemFromIndex(index)
            object_id = item.text()
            object_id = int(object_id)
            object = MdObject.get_by_id(object_id)
            selected_object_list.append(object)

        return selected_object_list


    def Previous(self):
        # get all items from tableView
        model = self.tableView.model()
        object_id_list = []
        proxy_index_list = []
        for row in range(model.rowCount()):
            proxy_index = self.tableView.model().index(row, 0)
            proxy_index_list.append(proxy_index)
            index = self.tableView.model().mapToSource(proxy_index)

            object_id = self.parent.object_model._data[index.row()][0]["value"]
            object_id = int(object_id)
            object_id_list.append(object_id)

        new_index = -1
        if object_id_list.index(self.object.id) > 0:
            new_index = object_id_list.index(self.object.id) - 1
            new_object_id = object_id_list[new_index]
            new_object = MdObject.get_by_id(new_object_id)

        if new_index >= 0:
            # enable or disable prev and next button 
            if new_index == 0:
                self.btnPrevious.setEnabled(False)
            else:
                self.btnPrevious.setEnabled(True)
            if new_index == len(object_id_list)-1:
                self.btnNext.setEnabled(False)
            else:
                self.btnNext.setEnabled(True)
                
            self.save_object()
            self.set_object(new_object)
            # select new object in tableView
            new_proxy_index = proxy_index_list[new_index]
            #new_index = self.object_model.indexFromId(new_object_id)
            self.tableView.selectRow(new_proxy_index.row())
            
            #self.accept()

    def Next(self):
        # get all items from tableView
        model = self.tableView.model()
        object_id_list = []
        proxy_index_list = []
        for row in range(model.rowCount()):
            proxy_index = self.tableView.model().index(row, 0)
            proxy_index_list.append(proxy_index)
            index = self.tableView.model().mapToSource(proxy_index)

            object_id = self.parent.object_model._data[index.row()][0]["value"]
            object_id = int(object_id)
            object_id_list.append(object_id)

        new_index = -1
        if object_id_list.index(self.object.id) < len(object_id_list)-1:
            new_index = object_id_list.index(self.object.id) + 1
            new_object_id = object_id_list[new_index]
            new_object = MdObject.get_by_id(new_object_id)

        if new_index >= 0:
            # enable or disable prev and next button 
            if new_index == 0:
                self.btnPrevious.setEnabled(False)
            else:
                self.btnPrevious.setEnabled(True)
            if new_index == len(object_id_list)-1:
                self.btnNext.setEnabled(False)
            else:
                self.btnNext.setEnabled(True)
            
            self.save_object()    
            self.set_object(new_object)            
            new_proxy_index = proxy_index_list[new_index]
            #new_index = self.object_model.indexFromId(new_object_id)
            self.tableView.selectRow(new_proxy_index.row())
            #self.accept()

    def Okay(self):
        self.save_object()
        self.object_deleted = False
        self.accept()

    def Cancel(self):
        self.reject()

    def resizeEvent(self, event):
        #print("Window has been resized",self.image_label.width(), self.image_label.height())
        #self.pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        #self.edtObjectDesc.resize(self.edtObjectDesc.height(),300)
        #self.image_label.setPixmap(self.pixmap)
        QDialog.resizeEvent(self, event)


class NewAnalysisDialog(QDialog):
    def __init__(self,parent,dataset):
        super().__init__()
        self.parent = parent
        self.setGeometry(QRect(100, 100, 400, 300))
        self.setWindowTitle(self.tr("Modan2 - New Analysis"))
        self.move(self.parent.pos()+QPoint(100,100))
        #self.status_bar = QStatusBar()
        self.dataset = dataset
        self.name_edited = False
        self.lblAnalysisName = QLabel(self.tr("Analysis name"), self)
        self.edtAnalysisName = QLineEdit(self)
        self.edtAnalysisName.textChanged.connect(self.edtAnalysisName_changed)
        self.lblSuperimposition = QLabel(self.tr("Superimposition method"), self)
        self.comboSuperimposition = QComboBox(self)
        self.comboSuperimposition.addItem(self.tr("Procrustes"))
        self.comboSuperimposition.addItem(self.tr("Bookstein"))
        self.comboSuperimposition.addItem(self.tr("Resistant Fit"))
        #self.lblOrdination = QLabel("Ordination method", self)
        #self.comboOrdination = QComboBox(self)
        #self.comboOrdination.addItem("PCA")
        #self.comboOrdination.addItem("CVA")
        #self.comboOrdination.addItem("MANOVA")
        #self.comboOrdination.currentIndexChanged.connect(self.comboOrdination_changed)
        #self.comboOrdination.addItem("MDS")
        self.lblCvaGroupBy = QLabel(self.tr("CVA grouping variable"), self)
        self.comboCvaGroupBy = QComboBox(self)
        self.lblManovaGroupBy = QLabel(self.tr("MANOVA grouping variable"), self)
        self.comboManovaGroupBy = QComboBox(self)

        valid_property_index_list = self.dataset.get_grouping_variable_index_list()
        variablename_list = self.dataset.get_variablename_list()
        #print("valid_property_index_list", valid_property_index_list, variablename_list)
        for idx in valid_property_index_list:
            property = variablename_list[idx]
            self.comboCvaGroupBy.addItem(property, idx)
            self.comboManovaGroupBy.addItem(property, idx)

        self.ignore_change = False
        #self.comboOrdination_changed()

        self.btnOK = QPushButton(self.tr("OK"), self)
        self.btnCancel = QPushButton(self.tr("Cancel"), self)
        self.btnOK.clicked.connect(self.btnOK_clicked)
        self.btnCancel.clicked.connect(self.btnCancel_clicked)

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        i = 0
        self.layout.addWidget(self.lblAnalysisName, i, 0)
        self.layout.addWidget(self.edtAnalysisName, i, 1)
        i+= 1
        self.layout.addWidget(self.lblSuperimposition, i, 0)
        self.layout.addWidget(self.comboSuperimposition, i, 1)
        #i+= 1
        #self.layout.addWidget(self.lblOrdination, i, 0)
        #self.layout.addWidget(self.comboOrdination, i, 1)
        i+= 1
        self.layout.addWidget(self.lblCvaGroupBy, i, 0)   
        self.layout.addWidget(self.comboCvaGroupBy, i, 1)
        i+= 1
        self.layout.addWidget(self.lblManovaGroupBy, i, 0)   
        self.layout.addWidget(self.comboManovaGroupBy, i, 1)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.btnOK)
        self.buttonLayout.addWidget(self.btnCancel)
        i += 1
        self.layout.addWidget(QLabel(""), i, 0, 1, 2)
        i+= 1
        self.layout.addLayout(self.buttonLayout, i, 0, 1, 2)
        self.get_analysis_name()

    def edtAnalysisName_changed(self):
        if self.ignore_change is True:
            pass
        else:
            self.name_edited = True
            #print("name edited")

    def comboOrdination_changed(self):
        if self.comboOrdination.currentText() in ["CVA","MANOVA"]:
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
        #self.parent.set_object_calibration( self.pixel_number, float(self.edtLength.text()),self.comboUnit.currentText())
        self.accept()
    
    def btnCancel_clicked(self): 
        self.close()

    def get_unique_name(self, name, name_list):
        if name not in name_list:
            return name
        else:
            i = 1
            # get last index of current name which is in the form of "name (i)" using regular expression
            match = re.match(r"(.+)\s+\((\d+)\)",name)
            if match:
                name = match.group(1)
                i = int(match.group(2))
                i += 1
            while True:
                new_name = name + " ("+str(i)+")"
                if new_name not in name_list:
                    return new_name
                i += 1        

class AnalysisResultDialog(QDialog):
    def __init__(self,parent):
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
        #self.setGeometry(QRect(100, 100, 1400, 800))
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
            if hasattr(ax, 'collections') and artist in ax.collections:
                ax.collections.remove(artist)
            elif hasattr(ax, 'texts') and artist in ax.texts:
                ax.texts.remove(artist)
            elif hasattr(ax, 'lines') and artist in ax.lines:
                ax.lines.remove(artist)
    except Exception:
        pass  # Silently ignore if already removed or other issues

class DataExplorationDialog(QDialog):
    def __init__(self, parent):
        self.initialized = False
        super().__init__()
        #print("DataExplorationDialog init")
        self.parent = parent
        self.setWindowTitle(self.tr("Modan2 - Data Exploration"))
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        #self.setWindowFlags(Qt.FramelessWindowHint)  # Removes window decoration
        #self.setAttribute(Qt.WA_TranslucentBackground)  # Enables transparency
        #self.setAttribute(Qt.WA_NoSystemBackground, True)  # Avoids system background paint

        #self.windowActivated.connect(self.handle_window_focus)
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close) 

        self.m_app = QApplication.instance()
        self.fig2 = None
        self.default_color_list = mu.VIVID_COLOR_LIST[:]        
        self.color_list = self.default_color_list[:]
        #print("color_list", self.color_list)        
        self.marker_list = mu.MARKER_LIST[:]
        self.plot_size = "medium"
        self.remember_geometry = True
        self.on_pick_happened = False
        self.bgcolor = "#AAAAAA"        

        self.curve_list = []
        self.shape_view_list = []
        self.shape_label_list = []
        self.shape_preference_list = []
        self.custom_shape_hash = {}
        self.shape_grid = {}
        self.shape_grid_pref_dict = {}
        self.shape_button_list = []
        #self.shape_combo_list = []
        self.vertical_line_xval = None
        #self.ds_ops = None
        self.vertical_line_style = "dashed"
        self.axvline = None
        self.temp_rotate_x = 0
        self.temp_rotate_y = 0
        self.shape_view_pan_x = 0
        self.shape_view_pan_y = 0
        self.shape_view_dolly = 0
        self.is_picking_shape = False
        self.pick_idx = -1
        self.animation_counter = 0
        self.show_arrow = True
        self.arrow_color = "red"
        self.object_info_list = []
        #self.shape_mode = MODE_REGRESSION
        self.rotation_matrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
        ])

        self.read_settings()
        self.mode = MODE_EXPLORATION
        self.ignore_change = False
        self.init_UI()

    def init_UI(self):

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.lblAnalysisName = QLabel(self.tr("Analysis name"))
        self.lblAnalysisName.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.edtAnalysisName = QLineEdit()
        self.edtAnalysisName.setEnabled(False)
        self.lblSuperimposition = QLabel(self.tr("Superimposition method"))
        self.lblSuperimposition.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.edtSuperimposition = QLineEdit()
        self.edtSuperimposition.setEnabled(False)
        self.lblOrdination = QLabel(self.tr("Ordination method"))
        self.lblOrdination.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.edtOrdination = QLineEdit()
        self.edtOrdination.setEnabled(False)
        self.lblVisualization = QLabel(self.tr("Shape view"))
        self.lblVisualization.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.comboVisualization = QComboBox()
        self.comboVisualization.addItem(self.tr("Exploration"),MODE_EXPLORATION)
        self.comboVisualization.addItem(self.tr("Regression"),MODE_REGRESSION)
        self.comboVisualization.addItem(self.tr("Average"),MODE_AVERAGE)
        self.comboVisualization.addItem(self.tr("Comparison"),MODE_COMPARISON)
        self.comboVisualization.addItem(self.tr("Comparison (overlap)"),MODE_COMPARISON2)
        self.comboVisualization.currentIndexChanged.connect(self.comboVisualizationMethod_changed)
        self.comboVisualization.setCurrentIndex(0)

        self.title_row_widget = QWidget()
        self.title_row_layout = QHBoxLayout()
        self.title_row_widget.setLayout(self.title_row_layout)
        self.title_row_layout.addWidget(self.lblAnalysisName,1)
        self.title_row_layout.addWidget(self.edtAnalysisName,2)
        self.title_row_layout.addWidget(self.lblSuperimposition,1)
        self.title_row_layout.addWidget(self.edtSuperimposition,2)
        self.title_row_layout.addWidget(self.lblOrdination,1)
        self.title_row_layout.addWidget(self.edtOrdination,2)
        #self.title_row_layout.addWidget(self.lblGroupBy,1)
        #self.title_row_layout.addWidget(self.comboGroupBy,2)
        #self.title_row_layout.addWidget(self.lblVisualization,1)
        #self.title_row_layout.addWidget(self.comboVisualization,2)
        self.layout.addWidget(self.title_row_widget)


        self.plot_widget2 = FigureCanvas(Figure(figsize=(20, 16),dpi=100))
        self.fig2 = self.plot_widget2.figure
        self.ax2 = self.fig2.add_subplot()
        self.ax2.set_xlabel("X-axis Label")
        self.ax2.set_ylabel("Y-axis Label")
        self.toolbar2 = NavigationToolbar(self.plot_widget2, self)
        #self.fig2.canvas.mpl_connect('pick_event',self.on_pick)
        self.fig2.canvas.mpl_connect('button_press_event', self.on_canvas_button_press)
        self.fig2.canvas.mpl_connect('button_release_event', self.on_canvas_button_release)
        self.fig2.canvas.mpl_connect('motion_notify_event', self.on_canvas_move)
        self.fig2.canvas.mpl_connect('resize_event', self.resizeEvent)
        #self.fig2.canvas.mpl_connect('motion_notify_event', self.on_hover_enter)
        #self.fig2.canvas.mpl_connect('motion_notify_event', self.on_hover_leave)

        self.plot_widget3 = FigureCanvas(Figure(figsize=(20, 16),dpi=100))
        self.fig3 = self.plot_widget3.figure
        self.ax3 = self.fig3.add_subplot(projection='3d')
        self.toolbar3 = NavigationToolbar(self.plot_widget3, self)        

        self.plot_setting_widget = QWidget()
        self.plot_setting_layout = QVBoxLayout()
        self.plot_setting_widget.setLayout(self.plot_setting_layout)
        self.plot_setting_widget.hide()

        self.axis_option_widget = QWidget()
        self.axis_option_layout = QHBoxLayout()
        self.axis_option_widget.setLayout(self.axis_option_layout)

        # basic chart options
        self.gbChartBasics = QWidget()
        #self.gbChartBasics.setTitle(self.tr("Basic settings"))
        self.gbChartBasics.setLayout(QHBoxLayout())
        
        spacer1 = QWidget()
        spacer1.setMinimumWidth(20)
        spacer2 = QWidget()
        spacer2.setMinimumWidth(20)

        self.lblGroupBy = QLabel(self.tr("Grouping variable"))
        self.lblGroupBy.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.comboGroupBy = QComboBox()
        self.comboGroupBy.setEnabled(False)
        self.comboGroupBy.currentIndexChanged.connect(self.comboGroupBy_changed)
        self.lblChartDim = QLabel(self.tr("Chart dimension:"))
        self.rb2DChartDim = QRadioButton("2D")
        self.rb3DChartDim = QRadioButton("3D")
        self.grpRadioButton1 = QButtonGroup()
        self.grpRadioButton1.addButton(self.rb2DChartDim)
        self.grpRadioButton1.addButton(self.rb3DChartDim)
        self.rb3DChartDim.setEnabled(False)
        self.rb2DChartDim.setChecked(True)
        self.rb2DChartDim.toggled.connect(self.on_chart_dim_changed)
        self.rb3DChartDim.toggled.connect(self.on_chart_dim_changed)
        self.cbxLegend = QCheckBox()
        self.cbxLegend.setText(self.tr("Show legend"))
        self.cbxLegend.setChecked(True)
        self.cbxLegend.toggled.connect(self.update_chart)
        self.gbChartBasics.layout().addWidget(self.lblGroupBy)
        self.gbChartBasics.layout().addWidget(self.comboGroupBy)
        self.gbChartBasics.layout().addWidget(spacer1)
        #self.gbChartBasics.layout().addWidget(self.lblChartDim)
        #self.gbChartBasics.layout().addWidget(self.rb2DChartDim)
        #self.gbChartBasics.layout().addWidget(self.rb3DChartDim)
        self.gbChartBasics.layout().addWidget(self.cbxLegend)
        self.gbChartBasics.layout().addWidget(spacer2)
        #self.axis_option_layout.addWidget(self.gbChartBasics)

        self.lblAxis1 = QLabel("Axis 1")
        self.lblAxis2 = QLabel("Axis 2")
        self.lblAxis3 = QLabel("Axis 3")
        self.comboAxis1 = QComboBox()
        self.comboAxis2 = QComboBox()
        self.comboAxis3 = QComboBox()
        self.cbxFlipAxis1 = QCheckBox()
        self.cbxFlipAxis1.setText(self.tr("Flip"))
        self.cbxFlipAxis1.setChecked(False)
        self.cbxFlipAxis2 = QCheckBox()
        self.cbxFlipAxis2.setText(self.tr("Flip"))
        self.cbxFlipAxis2.setChecked(False)
        self.cbxFlipAxis3 = QCheckBox()
        self.cbxFlipAxis3.setText(self.tr("Flip"))
        self.cbxFlipAxis3.setChecked(False)

        self.cbxFlipAxis1.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis2.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis3.stateChanged.connect(self.flip_axis_changed)

        for i in range(1,11):
            self.comboAxis1.addItem("PC"+str(i))
            self.comboAxis2.addItem("PC"+str(i))
            self.comboAxis3.addItem("PC"+str(i))
        self.comboAxis1.addItem("CSize")
        self.comboAxis1.setCurrentIndex(0)
        self.comboAxis2.setCurrentIndex(1)
        self.comboAxis3.setCurrentIndex(2)
        self.comboAxis1.currentIndexChanged.connect(self.axis_changed)
        self.comboAxis2.currentIndexChanged.connect(self.axis_changed)
        self.comboAxis3.currentIndexChanged.connect(self.axis_changed)

        #self.gbAxis= QGroupBox()
        #self.gbAxis.setTitle(self.tr("Axes settings"))
        #self.gbAxis.setLayout(QHBoxLayout())
        self.gbChartBasics.layout().addWidget(self.lblAxis1,0)
        self.gbChartBasics.layout().addWidget(self.comboAxis1,1)
        self.gbChartBasics.layout().addWidget(self.cbxFlipAxis1,0)
        self.gbChartBasics.layout().addWidget(self.lblAxis2,0)
        self.gbChartBasics.layout().addWidget(self.comboAxis2,1)
        self.gbChartBasics.layout().addWidget(self.cbxFlipAxis2,0)
        self.gbChartBasics.layout().addWidget(self.lblAxis3,0)
        self.gbChartBasics.layout().addWidget(self.comboAxis3,1)
        self.gbChartBasics.layout().addWidget(self.cbxFlipAxis3,0)

        #self.axis_option_layout.addWidget(self.gbAxis)
        
        #self.plot_setting_layout.addWidget(self.gbChartBasics)

        self.overlay_setting_widget = QWidget()
        self.overlay_setting_layout = QHBoxLayout()
        self.overlay_setting_widget.setLayout(self.overlay_setting_layout)

        self.gbOverlay = QGroupBox()
        self.gbOverlay.setTitle(self.tr("Overlay settings"))
        self.gbOverlay.setLayout(QHBoxLayout())

        self.cbxDepthShade = QCheckBox()
        self.cbxDepthShade.setText(self.tr("Depth shade"))
        self.cbxDepthShade.setChecked(False)
        self.cbxDepthShade.toggled.connect(self.update_chart)

        self.cbxAverage = QCheckBox()
        self.cbxAverage.setText(self.tr("Group average"))
        self.cbxAverage.setChecked(False)        
        self.cbxAverage.stateChanged.connect(self.update_chart)
        self.cbxConvexHull = QCheckBox()
        self.cbxConvexHull.setText(self.tr("Convex hull"))
        self.cbxConvexHull.setChecked(False)
        self.cbxConvexHull.stateChanged.connect(self.update_chart)
        self.cbxConfidenceEllipse = QCheckBox()
        self.cbxConfidenceEllipse.setText(self.tr("Confidence ellipse"))
        self.cbxConfidenceEllipse.setChecked(False)
        self.cbxConfidenceEllipse.stateChanged.connect(self.update_chart)
        self.cbxShapeGrid = QCheckBox()
        self.cbxShapeGrid.setText(self.tr("Shape grid"))
        self.cbxShapeGrid.setChecked(False)
        self.cbxShapeGrid.stateChanged.connect(self.cbxShapeGrid_state_changed)
        self.sgpWidget = ShapePreference(self)
        self.sgpWidget.set_title("")
        self.sgpWidget.hide_name()
        self.sgpWidget.hide_title()
        self.sgpWidget.hide_cbxShow()
        self.sgpWidget.set_color("gray")
        self.sgpWidget.set_opacity(0.8)
        self.sgpWidget.hide()
        self.cbxArrow = QCheckBox(self.tr("Show arrow"))
        self.cbxArrow.setChecked(True)
        self.cbxArrow.stateChanged.connect(self.arrow_preference_changed)
        self.btnArrowColor = QPushButton(self.tr("Arrow color"))
        self.btnArrowColor.setMinimumSize(20,20)
        self.btnArrowColor.setStyleSheet("background-color: yellow")
        self.btnArrowColor.setToolTip("yellow")
        self.btnArrowColor.setCursor(Qt.PointingHandCursor)
        self.btnArrowColor.clicked.connect(self.on_btnArrowColor_clicked)
        self.sgpWidget.shape_preference_changed.connect(self.shape_grid_preference_changed)


        self.gbOverlay.layout().addWidget(self.cbxDepthShade,1)
        self.gbOverlay.layout().addWidget(self.cbxAverage,1)
        self.gbOverlay.layout().addWidget(self.cbxConvexHull,1)
        self.gbOverlay.layout().addWidget(self.cbxConfidenceEllipse,1)
        self.gbOverlay.layout().addWidget(self.cbxShapeGrid,1)
        self.gbOverlay.layout().addWidget(self.sgpWidget,2)
        self.plot_setting_layout.addWidget(self.gbOverlay)

        ''' regression related controls '''
        self.cbxRegression = QCheckBox()
        self.cbxRegression.setText(self.tr("Show regression"))
        self.cbxRegression.setChecked(False)
        self.cbxRegression.stateChanged.connect(self.update_chart)
        self.lblRegressionBasedon = QLabel(self.tr("Group by"))
        self.comboRegressionBasedOn = QComboBox()
        self.comboRegressionBasedOn.currentIndexChanged.connect(self.comboRegressionBasedOn_changed)

        self.comboRegressionBy = QComboBox()
        self.comboRegressionBy.addItem("All")
        self.comboRegressionBy.addItem("By group")
        self.comboRegressionBy.addItem("Select group")
        self.comboRegressionBy.setCurrentIndex(1)
        self.comboRegressionBy.currentIndexChanged.connect(self.comboRegressionBy_changed)
        self.comboSelectGroup = QComboBox()        
        self.comboSelectGroup.currentIndexChanged.connect(self.comboSelectGroup_changed)
        self.comboSelectGroup.hide()
        model = self.comboSelectGroup.model()
        model.itemChanged.connect(self.comboSelectGroup_itemChanged)
        self.cbxExtrapolate = QCheckBox(self.tr("Extrapolate"))
        self.cbxExtrapolate.setChecked(True)
        self.cbxExtrapolate.stateChanged.connect(self.update_chart)
        self.lblDegree = QLabel(self.tr("Degree"))
        self.sbxDegree = QSpinBox()
        self.sbxDegree.setValue(1)
        self.sbxDegree.textChanged.connect(self.update_chart)
        self.cbxAnnotation = QCheckBox()
        self.cbxAnnotation.setText(self.tr("Annotation"))
        self.cbxAnnotation.stateChanged.connect(self.update_chart)
        self.cbxAnnotation.setChecked(False)

        self.gbRegression = QGroupBox()
        self.gbRegression.setTitle(self.tr("Regression settings"))
        self.gbRegression.setLayout(QHBoxLayout())

        self.gbRegression.layout().addWidget(self.cbxRegression, 1)
        self.gbRegression.layout().addWidget(self.lblRegressionBasedon, 0)
        self.gbRegression.layout().addWidget(self.comboRegressionBasedOn, 1)
        #self.gbRegression.layout().addWidget(self.comboRegressionBy, 1)
        self.gbRegression.layout().addWidget(self.comboSelectGroup, 1)
        self.gbRegression.layout().addWidget(self.cbxExtrapolate, 1)
        self.gbRegression.layout().addWidget(self.lblDegree, 0)
        self.gbRegression.layout().addWidget(self.sbxDegree, 1)
        self.gbRegression.layout().addWidget(self.cbxAnnotation, 1)
        self.plot_setting_layout.addWidget(self.gbRegression)


        self.visualization_layout = QGridLayout()
        self.visualization_widget = QWidget()
        self.visualization_widget.setLayout(self.visualization_layout)
        self.plot_layout = QVBoxLayout()
        self.plot_widget = QWidget()
        self.plot_widget.setLayout(self.plot_layout)
        #self.plot_layout.addWidget(self.plot_control_widget)
        #self.plot_layout.addWidget(self.regression_widget)
        self.plot_preference_button = QPushButton(QIcon(mu.resource_path('icons/M2Preferences_1.png')), "")
        self.plot_preference_button.setStyleSheet("border: none; padding: 0px;")
        self.plot_preference_button.setIconSize(QSize(32, 32))
        self.plot_preference_button.clicked.connect(self.show_plot_preference)
        self.plot_preference_button.setAutoDefault(False)
        self.btn_save_plot = QPushButton(self.tr("Export Chart"))
        self.btn_save_plot.clicked.connect(self.export_chart)


        self.toolbar_widget = QWidget()
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_widget.setLayout(self.toolbar_layout)
        self.toolbar_layout.addWidget(self.toolbar2)
        self.toolbar_layout.addWidget(self.toolbar3)
        self.toolbar_layout.addWidget(self.gbChartBasics)
        self.toolbar_layout.addWidget(self.btn_save_plot)
        self.toolbar_layout.addWidget(self.plot_preference_button)

        self.plot_layout.addWidget(self.toolbar_widget)
        self.plot_layout.addWidget(self.plot_setting_widget)
        self.plot_layout.addWidget(self.plot_widget2)
        self.plot_layout.addWidget(self.plot_widget3)

        self.view_layout = QVBoxLayout()
        self.view_widget = QWidget()
        self.view_widget.setLayout(self.view_layout)
        self.shape_view_layout = QVBoxLayout()

        self.btnResetPose = QPushButton(self.tr("Reset Pose"))
        self.btnResetPose.clicked.connect(self.reset_shape_pose)
        self.btnAnimate = QPushButton(self.tr("Animate"))
        self.btnAnimate.clicked.connect(self.animate_shape)
        self.cbxRecordAnimation = QCheckBox()
        self.cbxRecordAnimation.setText(self.tr("Record"))
        self.cbxRecordAnimation.setChecked(False)
        self.cbxRecordAnimation.stateChanged.connect(self.record_animation_changed)
        self.edtNumFrames = QLineEdit()
        self.total_frame = 120
        self.pause_frame = 0
        self.edtNumFrames.setText(str(self.total_frame))
        self.edtNumFrames.setFixedWidth(40)
        self.record_animation = False
        self.animation_frame_list = []

        self.animate_option_widget = QWidget()
        self.animate_option_layout = QHBoxLayout()
        self.animate_option_widget.setLayout(self.animate_option_layout)
        self.animate_option_layout.addWidget(self.btnAnimate)
        self.animate_option_layout.addWidget(self.cbxRecordAnimation)
        self.animate_option_layout.addWidget(self.edtNumFrames)

        self.shape_preference_button = QPushButton(QIcon(mu.resource_path('icons/M2Preferences_1.png')), "")
        self.shape_preference_button.setStyleSheet("border: none; padding: 0px;")
        self.shape_preference_button.setIconSize(QSize(32, 32))
        self.shape_preference_button.clicked.connect(self.shape_preference_button_clicked)
        self.shape_preference_button.setAutoDefault(False)

        self.shape_option_widget = QWidget()
        self.shape_option_layout = QHBoxLayout()
        self.shape_option_widget.setLayout(self.shape_option_layout)
        self.shape_option_layout.addWidget(self.lblVisualization,0)
        self.shape_option_layout.addWidget(self.comboVisualization,1)

        self.shape_option_layout.addWidget(self.animate_option_widget,1)
        self.shape_option_layout.addWidget(self.btnResetPose,0)
        self.shape_option_layout.addWidget(self.shape_preference_button,0)
        self.view_layout.addWidget(self.shape_option_widget,0)

        self.shape_preference_widget = QWidget()
        self.shape_preference_layout = QVBoxLayout()
        self.shape_preference_widget.setLayout(self.shape_preference_layout)
        self.shape_preference_widget.hide()
        self.view_layout.addWidget(self.shape_preference_widget,0)

        self.arrow_widget = QWidget()
        self.arrow_layout = QHBoxLayout()
        self.arrow_widget.setLayout(self.arrow_layout)
        self.arrow_layout.addWidget(self.cbxArrow)
        self.arrow_layout.addWidget(self.btnArrowColor)
        self.view_layout.addWidget(self.arrow_widget,0)

        self.shape_view_widget = QWidget()
        self.shape_view_widget.setLayout(self.shape_view_layout)
        self.shape_view_scroll_area = QScrollArea()
        self.shape_view_scroll_area.setWidgetResizable(True)
        self.shape_view_scroll_area.setWidget(self.shape_view_widget)
        self.view_layout.addWidget(self.shape_view_scroll_area)

        self.visualization_splitter = QSplitter(Qt.Horizontal)
        self.visualization_splitter.addWidget(self.plot_widget)
        self.visualization_splitter.addWidget(self.view_widget)
        self.visualization_splitter.setSizes([800, 300])
        self.visualization_splitter.splitterMoved.connect(self.on_splitter_moved)

        self.layout.addWidget(self.visualization_splitter)
        self.on_chart_dim_changed()
        self.initialized = True

    def comboSelectGroup_changed(self):
        #print("comboSelectGroup_changed")
        #self.update_chart()
        return
    
    def comboSelectGroup_itemChanged(self, item):
        #print("comboSelectGroup_itemChanged", self.ignore_change)
        if self.ignore_change == True:
            return

        self.update_chart()

    def comboRegressionBy_changed(self):
        self.comboSelectGroup.hide()
        if self.comboRegressionBy.currentText() == "By group":            
            for shape_view in self.shape_view_list:
                shape_view.show()
        else:
            if self.comboRegressionBy.currentText() == "Select group":
                self.comboSelectGroup.show()
            for idx, shape_view in enumerate(self.shape_view_list):
                if idx == 0:
                    shape_view.show()
                else:
                    shape_view.hide()
        
            
        self.update_chart()

    def comboRegressionBasedOn_changed(self):
        if len(self.object_info_list) == 0:
            return  
        self.update_chart()
        #pass
        #self.update_chart()

    def cbxShapeGrid_state_changed(self):
        #print("cbxShape_state_changed")
        if self.cbxShapeGrid.isChecked() == True:
            self.sgpWidget.show()
            self.update_chart()
        else:
            self.sgpWidget.hide()
            self.update_chart()


    def export_chart(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilter("PNG (*.png);;JPG (*.jpg);;PDF (*.pdf);;SVG (*.svg);;All files (*.*)")
        dialog.setDefaultSuffix("png")
        #dialog.setDirectory(self.m_app.last_opened_dir)
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
            #self.m_app.last_opened_dir = dialog.directory().absolutePath()
            if filename:
                if self.cbxShapeGrid.isChecked() == True:
                    self.save_composite_plot(filename)
                else:
                    self.fig2.savefig(filename)

    def save_composite_plot(self, filename):
    #def export_composite_image(chart_widget, shape_widgets, filename, format="PNG"):
        # 1. Create the combined canvas (QPixmap)
        canvas_width = self.plot_widget2.width()
        canvas_height = self.plot_widget2.height()
        #chart_aspect_ratio = canvas_width / canvas_height
        #target_width = 2048
        #canvas_width = target_width
        #size_ratio = target_width / canvas_width
        #canvas_height = int(target_width / chart_aspect_ratio)  # Maintain aspect ratio
        canvas = QPixmap(canvas_width, canvas_height)

        #canvas = QPixmap(canvas_width, canvas_height)
        #fig = self.plot_widget2.figure  # Assuming your chart widget has a 'figure' attribute
        #fig.set_size_inches(canvas_width / fig.dpi, canvas_height / fig.dpi)
        #chart_widget.render(painter)        

        # 2. Initialize QPainter for drawing on the canvas
        painter = QPainter(canvas)

        # 3. Draw the Matplotlib chart onto the canvas
        self.plot_widget2.render(painter)

        # 4. Overlay the shape images
        for keyname in self.shape_grid.keys():
            view = self.shape_grid[keyname]['view']
            if view:
                #print("keyname", keyname, "x_val", self.shape_grid[keyname]['x_val'], "y_val", self.shape_grid[keyname]['y_val'])
                transform = self.ax2.transData
                display_coords =    transform.transform((self.shape_grid[keyname]['x_val'], self.shape_grid[keyname]['y_val']))
                x_pixel, y_pixel = display_coords   
                if sys.platform == 'darwin':
                    x_pixel = x_pixel / 2
                    y_pixel = y_pixel / 2
                #print("display_coords", display_coords, "x_pixel", x_pixel, "y_pixel", y_pixel)
                fig_height = self.fig2.canvas.height()
                fig_width = self.fig2.canvas.width()
                view_height = int( fig_height / 4 )
                view_width = int( fig_width / 4 )
                x_pos = int( x_pixel )
                y_pos = int( fig_height - y_pixel )
                w, h = view.width(), view.height()
                w, h = 120, 90
                w = max(w, view_width)
                h = max(h, view_height)
                #print("view size", w, h, "view pos", x_pixel, y_pixel, "fig_size", fig_width, fig_height, "view pos 2", x_pos, y_pos)
                '''
                self.shape_grid[keyname]['x_pos'] = x_pixel
                self.shape_grid[keyname]['y_pos'] = y_pixel
                #print("view size 2  ", w, h, "view pos", x_pixel, y_pixel, "fig_size", fig_width, fig_height)

                view.setGeometry(self.shape_grid[keyname]['x_pos']-int(w/2), self.shape_grid[keyname]['y_pos']-int(h/2), w, h)
                '''


            #for shape_widget, (x, y) in zip(shape_widgets, pca_coordinates):
                # Convert PCA coordinates to pixel positions on the canvas
                #x_pixel, y_pixel = map_coordinates_to_pixels(x, y, canvas_width, canvas_height)

                # Draw the shape image onto the canvas
                view.update()
                if isinstance(view,ObjectViewer3D):
                    buffer = QPixmap(view.grabFrameBuffer(True))
                else:
                    buffer = QPixmap(view.grab())
                #print(buffer)
                painter.drawPixmap(x_pos-int(w/2), y_pos-int(h/2), buffer)

        # 5. End painting
        painter.end()

        # 6. Save the composite image
        canvas.save(filename, "PNG")        

    def on_btnArrowColor_clicked(self,event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.btnArrowColor.toolTip()))
        if color is not None:
            self.btnArrowColor.setStyleSheet("background-color: " + color.name())
            self.btnArrowColor.setToolTip(color.name())
            self.arrow_color = color.name()
            #self.m_app.landmark_pref[dim]['color'] = color.name()        
        self.arrow_preference_changed()

    def shape_grid_preference_changed(self, pref):
        self.shape_grid_pref_dict = pref
        if self.cbxShapeGrid.isChecked() == True:
            for key in self.shape_grid:
                if self.shape_grid[key]['view'] is not None:
                    self.shape_grid[key]['view'].set_shape_preference(self.shape_grid_pref_dict)
                    self.shape_grid[key]['view'].update()

    def event(self, event):
        if event.type() in [ QEvent.WindowActivate, QEvent.WindowStateChange] and self.initialized == True:
            #print("Window has been activated")
            self.handle_window_focus()
        return super().event(event)
    
    def handle_window_focus(self):
        #print("handle_window_focus")
        if self.cbxShapeGrid.isChecked() == True:
            for key in self.shape_grid:
                if self.shape_grid[key]['view'] is not None:
                    self.shape_grid[key]['view'].raise_()
                    self.shape_grid[key]['view'].update()

    def shape_preference_button_clicked(self):
        #print("shape preference button clicked")
        if self.shape_preference_widget.isVisible():
            self.shape_preference_widget.hide()
            self.arrow_widget.hide()
        else:
            self.shape_preference_widget.show()
            if self.mode == MODE_COMPARISON2:
                self.arrow_widget.show()
            #self.chart_option_widget.hide()

    def record_animation_changed(self):
        self.record_animation = self.cbxRecordAnimation.isChecked()


    def chart_animation(self):
        #print("chart_animation", self.animation_counter)
        idx = 0
        if self.animation_counter < self.pause_frame:
            idx = 0
        elif self.animation_counter >= self.pause_frame and self.animation_counter < self.half_frame + self.pause_frame:
            # 0 -> half frame
            idx = self.animation_counter - self.pause_frame
        elif self.animation_counter >= self.half_frame + self.pause_frame and self.animation_counter < self.half_frame + 2 * self.pause_frame:
            idx = self.half_frame - 1
        elif self.animation_counter >= self.half_frame + 2 * self.pause_frame and self.animation_counter < self.total_frame + 2 * self.pause_frame:
            # half_frame -> 0
            idx = self.total_frame - self.animation_counter + 2 * self.pause_frame - 1
        elif self.animation_counter >= self.total_frame + 2 * self.pause_frame and self.animation_counter < self.total_frame + 3 * self.pause_frame:
            idx = 0
        elif self.animation_counter == self.total_frame + 3 * self.pause_frame:
            safe_remove_artist(self.animation_shape['point'], self.ax2)
            self.animation_shape['point'] = None
            self.timer.stop()
            self.fig2.canvas.draw()
            # wait cursor
            if self.record_animation == True:
                self.create_video_from_frames()
            QApplication.restoreOverrideCursor()
            self.toolbar_widget.show()
            self.shape_option_widget.show()
            return
        #print("chart_animation", self.animation_counter, idx, self.pause_frame, self.half_frame, self.total_frame)

        x = self.animation_x_range[idx]
        y = self.animation_y_range[idx]
        #print("chart_animation", x, y, self.animation_counter)
        #self.animation_shape['point']
        self.animation_shape['point'].set_offsets([x, y])
        self.fig2.canvas.draw()
        self.animation_counter += 1

        ''' show shape '''
        axis1 = self.comboAxis1.currentData()
        axis2 = self.comboAxis2.currentData()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0
        shape_to_visualize = np.zeros((1,len(self.analysis_result_list[0])))
        x_value = flip_axis1 * x
        y_value = flip_axis2 * y
        if axis1 != CENTROID_SIZE_VALUE:
            shape_to_visualize[0][axis1] = x_value
        shape_to_visualize[0][axis2] = y_value
        unrotated_shape = self.unrotate_shape(shape_to_visualize)
        
        #print("0-4:",datetime.datetime.now())
        self.show_shape(unrotated_shape[0], 0)

        if self.record_animation == True:
            screen = QApplication.primaryScreen()
            x, y, width, height = self.geometry().getRect()
            #print("x,y,width,height", x, y, width, height)
            pixmap = screen.grabWindow(self.winId(), 0, 0, width, height)
            self.animation_frame_list.append(pixmap)
            #print("frame added", len(self.animation_frame_list))


        #print("chart_animation done")

    def create_video_from_frames(self):
        with tempfile.TemporaryDirectory() as temp_dir:        
            for idx, frame in enumerate(self.animation_frame_list):
                # padding 3 digits
                filename = f"{temp_dir}/frame{idx:03}.png"
                #print("saving frame", filename)
                frame.save(filename)
            # Specify the path to your image files
            #image_folder = 'd:/'
            #video_name = 'output_video.avi'

            images = [img for img in sorted(glob.glob(f"{temp_dir}/frame*.png"))]
            if len(images) == 0:
                logger = logging.getLogger(__name__)
                logger.warning("No frame found")
                return
            frame = cv2.imread(images[0])
            height, width, layers = frame.shape

            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'DIVX')  # or use 'XVID'

            # ask user for video directory
            #options = QFileDialog.Options()
            #options |= QFileDialog.DontUseNativeDialog
            video_name, _ = QFileDialog.getSaveFileName(self, "Save video file", "", "Video Files (*.avi)")
            if video_name == "":
                return
            #print("video_name", video_name)
            
            video = cv2.VideoWriter(video_name, fourcc, 20.0, (width, height))

            for image in images:
                video.write(cv2.imread(image))

            cv2.destroyAllWindows()
            video.release()            



    def animate_shape(self):
        if self.mode not in [ MODE_COMPARISON, ]:# or self.comboRegressionBy.currentText() == "By group":
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.pause_frame = 15
        self.toolbar_widget.hide()
        self.shape_option_widget.hide()
        self.total_frame = int(self.edtNumFrames.text())
        self.half_frame = int(self.total_frame / 2)

        if self.mode in [MODE_COMPARISON]:
            from_shape = self.custom_shape_hash[0]
            to_shape = self.custom_shape_hash[1]
            x_from, y_from = from_shape['coords']
            x_to, y_to = to_shape['coords']
            #print("animate_shape", x_from, y_from, x_to, y_to)

            self.animation_x_range = np.linspace(x_from, x_to, self.half_frame)
            self.animation_y_range = np.linspace(y_from, y_to, self.half_frame)
            self.animation_shape = { 'coords': [x_from, y_from], 'point': None}


        elif self.mode in []:
            x_from = min(self.regression_data['x_val'])
            x_to = max(self.regression_data['x_val'])

            self.animation_x_range = np.linspace(x_from, x_to, self.half_frame)
            self.animation_y_range = np.zeros(self.half_frame)
            show_extrapolate = self.cbxExtrapolate.isChecked()
            curve = self.curve_list[0]
            #print("curve", curve)
            model = curve['model']
            #if show_extrapolate:
            #    model = curve['curve2']
            #else:
            #    model = curve['curve']
            #print("model", model)
            for idx, x in enumerate(self.animation_x_range):
                self.animation_y_range[idx] = np.polyval(model, x)
            y_from = self.animation_y_range[0]
            self.animation_shape = { 'coords': [x_from, y_from], 'point': None}

        self.animation_counter = 0
        self.animation_frame_list = []
        self.animation_shape['point'] = self.ax2.scatter(x_from, y_from, s=100, c='red', marker='o')
        self.fig2.canvas.draw()

        self.timer = QTimer()
        self.timer.timeout.connect(self.chart_animation)
        self.timer.start(100)


    def reset_shape_pose(self):
        #print("reset_shape_pose")
        self.rotation_matrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
        ])
        for shape_view in self.shape_view_list:
            shape_view.reset_pose()
            shape_view.update()
            
        for key in self.shape_grid.keys():
            view = self.shape_grid[key]['view']
            if view:
                view.reset_pose()
                view.update()

    def on_chart_dim_changed(self):
        #print("on chart dim changed")
        if self.rb2DChartDim.isChecked():
            self.toolbar3.hide()
            self.toolbar2.show()
            self.plot_widget3.hide()
            self.plot_widget2.show()
            self.toolbar2.show()
            self.toolbar3.hide()
            self.lblAxis3.hide()
            self.comboAxis3.hide()
            self.cbxFlipAxis3.hide()
            self.comboAxis3.hide()
            self.cbxFlipAxis3.hide()
            self.cbxDepthShade.hide()
        else:
            self.toolbar3.show()
            self.toolbar2.hide()
            self.plot_widget2.hide()
            self.plot_widget3.show()
            self.toolbar2.hide()
            self.toolbar3.show()
            self.lblAxis3.show()
            self.comboAxis3.show()
            self.cbxFlipAxis3.show()
            self.comboAxis3.show()
            self.cbxFlipAxis3.show()
            self.cbxDepthShade.show()        

    def show_plot_preference(self):
        if self.plot_setting_widget.isVisible():
            self.plot_setting_widget.hide()
        else:
            self.plot_setting_widget.show()
        
    def on_splitter_moved(self):
        self.resizeEvent(None)

    def showEvent(self, event):
        #print("show event")
        self.resizeEvent(None)

    def comboVisualizationMethod_changed(self):
        new_mode = self.comboVisualization.currentIndex()
        #print("before set_mode")
        self.set_mode(new_mode)
        #print("after set_mode")
        
    def set_growth_trajectory_mode(self):
        #self.mode = MODE_GROWTH_TRAJECTORY
        #self.comboGroupBy.setEnabled(False)
        #self.comboGroupBy.hide()
        #self.lblGroupBy.hide()
        #self.show_analysis_result()
        
        self.comboAxis1.setCurrentText(CENTROID_SIZE_TEXT)
        self.comboAxis2.setCurrentIndex(0)
        self.update_chart()

    def set_mode(self, mode):
        #print("set mode", mode)
        self.mode = mode

        self.ignore_change = True
        if False: #mode == MODE_GROWTH_TRAJECTORY:
            self.comboAxis1.setCurrentText(CENTROID_SIZE_TEXT)
            self.comboAxis2.setCurrentIndex(0)
            self.comboAxis3.setCurrentIndex(1)
        else:
            #elif mode == MODE_CUSTOM:
            self.comboAxis1.setCurrentIndex(1)
            self.comboAxis2.setCurrentIndex(1)
            self.comboAxis3.setCurrentIndex(2)
        #print("inside set_mode 1")
        self.cbxRegression.setChecked(False)
        if mode in [ MODE_REGRESSION ]:
            self.cbxRegression.setChecked(True)

        #print("inside set_mode 1.5")
        self.cbxAverage.setChecked(False)
        if mode == MODE_AVERAGE:
            self.cbxAverage.setChecked(True)
        self.ignore_change = False

        if mode in [MODE_COMPARISON, MODE_REGRESSION]:
            self.animate_option_widget.show()
        else:
            self.animate_option_widget.hide()

        if mode == MODE_COMPARISON2:
            self.arrow_widget.show()
        else:
            self.arrow_widget.hide()

        self.prepare_shape_view()
        self.resizeEvent(None)

        #print("inside set_mode 3")
        if mode == MODE_EXPLORATION:
            self.pick_idx = 0
            self.is_picking_shape = True
            self.plot_widget2.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.is_picking_shape = False
            self.pick_idx = -1
            self.plot_widget2.setCursor(QCursor(Qt.ArrowCursor))

    def prepare_shape_view(self):
        for shape_label in self.shape_label_list:
            shape_label.deleteLater()
        for shape_button in self.shape_button_list:
            shape_button.deleteLater()
        for shape_preference in self.shape_preference_list:
            shape_preference.deleteLater()
        for shape_view in self.shape_view_list:
            self.shape_view_layout.removeWidget(shape_view)
            shape_view.deleteLater()
        for key in self.custom_shape_hash.keys():
            self.custom_shape_hash[key]['coords'] = []
            if self.custom_shape_hash[key]['point'] != None:
                safe_remove_artist(self.custom_shape_hash[key]['point'], self.ax2)
            self.custom_shape_hash[key]['point'] = None
            if self.custom_shape_hash[key]['label'] != None:
                safe_remove_artist(self.custom_shape_hash[key]['label'], self.ax2)
            self.custom_shape_hash[key]['label'] = None
        self.arrow_widget.hide()

        #self.custom_shape_list = []
        self.shape_view_list = []
        self.shape_label_list = []
        self.shape_button_list = []
        self.shape_preference_list = []
        self.custom_shape_hash = {}
        self.grid_view_list = []
      
        if self.mode in [ MODE_REGRESSION, MODE_AVERAGE]:
            keyname_list = self.scatter_data.keys()
        elif self.mode == MODE_COMPARISON:
            keyname_list = [ "A", "B"]
            for idx, keyname in enumerate(keyname_list):
                self.custom_shape_hash[idx] = {'name': keyname, 'coords': [], 'point': None, 'color': None, 'label': None}
        elif self.mode == MODE_COMPARISON2:
            keyname_list = [ "A", "B" ]
            for idx, keyname in enumerate(keyname_list):
                self.custom_shape_hash[idx] = {'name': keyname, 'coords': [], 'point': None, 'color': None, 'label': None}
        elif self.mode == MODE_EXPLORATION:
            keyname_list = [ ''  ]
            for idx, keyname in enumerate(keyname_list):
                self.custom_shape_hash[idx] = {'name': keyname, 'coords': [], 'point': None, 'color': None, 'label': None}

        for idx, keyname in enumerate(keyname_list):
            if self.analysis.dimension == 2:
                shape_view = ObjectViewer2D(self)
                shape_view.show_index = False
            else:
                shape_view = ObjectViewer3D(self)
            self.shape_view_list.append(shape_view)

            if self.mode in [MODE_COMPARISON, MODE_COMPARISON2]:
                shape_button = QPushButton(QIcon(mu.resource_path('icons/M2Landmark_2.png')), "")
                # send idx to lambda function
                shape_button.clicked.connect(lambda checked, idx=idx: self.shape_button_clicked(idx))
                
                shape_button.setParent(shape_view)
                self.shape_button_list.append(shape_button)
                shape_button.setAutoDefault(False)

                #print("shape_preference", idx)
                shape_preference = ShapePreference(self)
                if idx == 0:
                    shape_preference.set_title(self.tr("Source shape"))
                    shape_preference.set_color("red")
                    shape_preference.set_opacity(1.0)
                else:
                    shape_preference.set_title(self.tr("Target shape"))
                    shape_preference.set_color("blue")
                    shape_preference.set_opacity(0.5)
                shape_preference.set_name(keyname)
                shape_preference.set_index(idx)
                #shape_preference.set_color(self.color_list[idx])
                # connect shape_preference signal to self.shape_preference_changed
                shape_preference.shape_preference_changed.connect(self.shape_preference_changed)

                self.shape_preference_list.append(shape_preference)
                self.shape_preference_layout.addWidget(shape_preference)
            else:
                shape_preference = ShapePreference(self)
                shape_preference.hide_title()
                shape_preference.hide_name()
                shape_preference.hide_cbxShow()
                shape_preference.set_name(keyname)
                shape_preference.set_index(idx)
                
                shape_preference.set_color(self.color_list[idx])
                self.shape_preference_list.append(shape_preference)
                self.shape_preference_layout.addWidget(shape_preference)
                shape_preference.shape_preference_changed.connect(self.shape_preference_changed)


            shape_label = QLabel(keyname)
            shape_label.setParent(shape_view)
            shape_label.setStyleSheet("background-color: "+self.bgcolor+"; color: white")

            self.shape_label_list.append(shape_label)
            if keyname == '__default__' :
                shape_label.hide()

            self.shape_view_layout.addWidget(shape_view,1)
            shape_view.set_object_name(keyname)
            shape_view.show()  
        if self.mode == MODE_AVERAGE:
            self.show_average_shapes()
            #pass
        if self.mode == MODE_COMPARISON2:
            #self.arrow_widget.hi()
            self.shape_label_list[1].setParent(self.shape_view_list[0])
            self.shape_button_list[1].setParent(self.shape_view_list[0])
            self.shape_label_list[1].show()
            self.shape_button_list[1].show()
            self.shape_view_list[1].hide()
            #self.shape_view_list[0].set_source_shape_color(QColor(255,0,0))
            #self.shape_view_list[0].set_target_shape_color(QColor(0,0,255))
            self.shape_view_list[0].show_arrow = True

    def arrow_preference_changed(self):
        self.shape_view_list[0].show_arrow = self.cbxArrow.isChecked()
        self.shape_view_list[0].arrow_color = self.arrow_color
        self.shape_view_list[0].update()

    def shape_preference_changed(self, pref_dict):
        #print("shape_preference_changed", pref_dict)
        idx = pref_dict['index']
        name = pref_dict['name']
        #color = pref_dict['color']
        #self.custom_shape_hash[idx]['color'] = color
        shape_label = self.shape_label_list[idx]
        shape_label.setText(name)
        #label = QLabel("Your sample text")
        font_metrics = QFontMetrics(shape_label.font())
        text_rect = font_metrics.boundingRect(shape_label.text())

        width = text_rect.width() + 10  # Add some padding for visual comfort
        height = shape_label.height()
        x, y = shape_label.pos().x(), shape_label.pos().y()  # Get current position
        shape_label.setGeometry(x, y, width, height) 

        #shape_label.adjustSize()

        #rendered_width = text_rect.width()
        #print("Rendered width:", rendered_width)        

        if self.mode == MODE_COMPARISON2:
            self.custom_shape_hash[idx]['name'] = name
            shape_view = self.shape_view_list[0]
            idx = pref_dict['index']
            if idx == 0:
                shape_view.set_source_shape_preference(pref_dict)
            else:
                shape_view.set_target_shape_preference(pref_dict)
            shape_view.update()
        else:
            shape_view = self.shape_view_list[idx]
            shape_view.set_shape_preference(pref_dict)
            shape_view.update()

        #self.custom_shape_hash[idx]['point'].set_color(color)
        #self.custom_shape_hash[idx]['label'].set_color(color)
        #self.custom_shape_hash[idx]['label'].setText(name)


    def show_average_shapes(self):
        keyname_list = self.scatter_data.keys()
        #print("show_average_shapes", keyname_list, self.average_shape)
        for idx, keyname in enumerate(keyname_list):
            #shape_view = ObjectViewer3D(self)
            #for idx, shape_view in enumerate(self.shape_view_list):
            axis1 = self.comboAxis1.currentData()
            axis2 = self.comboAxis2.currentData()

            x_average = self.average_shape[keyname]['x_val']
            y_average = self.average_shape[keyname]['y_val']
            flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
            flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0
            x_value = flip_axis1 * x_average
            y_value = flip_axis2 * y_average
            shape_to_visualize = np.zeros((1,len(self.analysis_result_list[0])))

            if axis1 != CENTROID_SIZE_VALUE:
                shape_to_visualize[0][axis1] = x_value
            shape_to_visualize[0][axis2] = y_value
            unrotated_shape = self.unrotate_shape(shape_to_visualize)            
            self.show_shape(unrotated_shape[0], idx)        
            
            #shape_view.show()

    def shape_regression(self, evt):
        #print("shape regression", evt.xdata)
        for idx, shape_view in enumerate(self.shape_view_list):
            #print("0-1:",datetime.datetime.now())
            #shape_view.clear_object()

            
            axis1 = self.comboAxis1.currentData()
            axis2 = self.comboAxis2.currentData()
            flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
            flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0
            shape_to_visualize = np.zeros((1,len(self.analysis_result_list[0])))
            #if axis1 == 10:
            #fit regression line
            y_value = 0
            curve = self.curve_list[idx]
            #print("0-2:",datetime.datetime.now(), evt.xdata, min(curve['size_range2']), max(curve['size_range2']))
            if evt.xdata >= min(curve['size_range2']) and evt.xdata <= max(curve['size_range2']):
                y_value = np.polyval(curve['model'], evt.xdata)
            else:
                continue
            x_value = flip_axis1 * evt.xdata
            #y_value = flip_axis2 * y_value


            if axis1 != CENTROID_SIZE_VALUE:
                shape_to_visualize[0][axis1] = x_value

            shape_to_visualize[0][axis2] = flip_axis2 * y_value
            #print("0-3:",datetime.datetime.now())
            unrotated_shape = self.unrotate_shape(shape_to_visualize)
            #print("0-4:",datetime.datetime.now())
            self.show_shape(unrotated_shape[0], idx)        



    def shape_button_clicked(self, idx):
        #print("shape_button_clicked", idx)
        self.is_picking_shape = True
        self.pick_idx = idx
        self.plot_widget2.setCursor(QCursor(Qt.CrossCursor))

        #self.shape_view_list[idx].show()

    def update_chart(self):
        #if self.ds_ops is not None and self.analysis_done is True:
        self.prepare_scatter_data()
        self.calculate_fit()
        #print("update chart", self.curve_list)
        self.show_analysis_result()

    def axis_changed(self):
        #if self.ds_ops is not None and self.analysis_done is True:
        if self.ignore_change:
            return
        
        self.update_chart()

    def flip_axis_changed(self, int):
        #if self.ds_ops is not None:
        self.update_chart()

    def read_settings(self):
        #self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        self.plot_size = self.m_app.settings.value("PlotSize", self.plot_size)
        for i in range(len(self.color_list)):
            self.color_list[i] = self.m_app.settings.value("DataPointColor/"+str(i), self.default_color_list[i])
        for i in range(len(self.marker_list)):
            self.marker_list[i] = self.m_app.settings.value("DataPointMarker/"+str(i), self.marker_list[i])
        self.bgcolor = self.m_app.settings.value("BackgroundColor", self.bgcolor)
        if self.m_app.remember_geometry is True:
            #print('loading geometry', self.remember_geometry)
            
            is_maximized = mu.value_to_bool(self.m_app.settings.value("IsMaximized/DataExplorationWindow", False))
            if is_maximized == True:
                #print("maximized true. restoring maximized state")
                #self.showMaximized()
                self.setWindowState(Qt.WindowMaximized)
            else:
                self.setGeometry(self.m_app.settings.value("WindowGeometry/DataExplorationWindow", QRect(100, 100, 1400, 800)))
                #self.setGeometry(self.m_app.settings.value("WindowGeometry/DataExplorationWindow", QRect(100, 100, 1400, 800)))
                #print("maximized false")
                #self.showNormal()
                #pass
        else:
            self.setGeometry(QRect(100, 100, 1400, 800))
            self.move(self.parent.pos()+QPoint(50,50))

    def write_settings(self):
        self.m_app.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.m_app.remember_geometry is True:
            #print("maximized:", self.isMaximized(), "geometry:", self.geometry())
            
            if self.isMaximized():
                self.m_app.settings.setValue("IsMaximized/DataExplorationWindow", True)
            else:
                self.m_app.settings.setValue("IsMaximized/DataExplorationWindow", False)
                self.m_app.settings.setValue("WindowGeometry/DataExplorationWindow", self.geometry())
                #print("save maximized false")

    def closeEvent(self, event):
        self.write_settings()
        #for shape_view in self.shape_view_list:
        #    shape_view.close()
        for key in self.shape_grid.keys():
            if self.shape_grid[key]['view']:
                self.shape_grid[key]['view'].close()
        #if self.analysis_dialog is not None:
        #    self.analysis_dialog.close()
        event.accept()



    def store_rotation(self,x_rad, y_rad):
        #print("store_rotation", x_rad, y_rad)
        rotationXMatrix = np.array([
            [1, 0, 0, 0],
            [0, np.cos(y_rad), -np.sin(y_rad), 0],
            [0, np.sin(y_rad), np.cos(y_rad), 0],
            [0, 0, 0, 1]
        ])

        rotationYMatrix = np.array([
            [np.cos(x_rad), 0, np.sin(x_rad), 0],
            [0, 1, 0, 0],
            [-np.sin(x_rad), 0, np.cos(x_rad), 0],
            [0, 0, 0, 1]
        ])
        #print(rotationXMatrix)
        #print(rotationYMatrix)
        #print("rotation matrix before\n",self.rotation_matrix)
        new_rotation_matrix = np.dot(rotationXMatrix, rotationYMatrix)
        self.rotation_matrix = np.dot(new_rotation_matrix, self.rotation_matrix)
        #print("rotation matrix after\n",self.rotation_matrix)



    def sync_rotation(self):
        if len(self.shape_view_list) > 0:
            temp_rotate_x = math.radians(self.shape_view_list[0].temp_rotate_x)
            temp_rotate_y = math.radians(self.shape_view_list[0].temp_rotate_y)
            #(math.radians(self.rotate_x),math.radians(self.rotate_y),apply_rotation_to_vertex)
            self.store_rotation(temp_rotate_x,temp_rotate_y)
        for key in self.shape_grid.keys():
            if self.shape_grid[key]['view']:
                self.shape_grid[key]['view'].sync_rotation()
                self.shape_grid[key]['view'].update()

        for sv in self.shape_view_list:
            #self.temp_rotate_x = sv.temp_rotate_x
            #self.temp_rotate_y = sv.temp_rotate_y
            #sv.rotate_x = sv.temp_rotate_x
            #sv.rotate_y = sv.temp_rotate_y
            sv.sync_rotation()
            sv.update()


    def sync_temp_pan(self, shape_view, temp_pan_x, temp_pan_y):
        for sv in self.shape_view_list:
            if sv != shape_view:
                sv.temp_pan_x = temp_pan_x
                sv.temp_pan_y = temp_pan_y
                #sv.sync_zoom()
                sv.update()



    def sync_pan(self, shape_view, pan_x, pan_y):
        if len(self.shape_view_list) > 0:
            self.shape_view_pan_x = self.shape_view_list[0].pan_x
            self.shape_view_pan_y = self.shape_view_list[0].pan_y
        for sv in self.shape_view_list:
            if sv != shape_view:
                sv.pan_x = pan_x
                sv.pan_y = pan_y
                #sv.sync_zoom()
                sv.update()


    def sync_zoom(self, shape_view, zoom_factor):
        #print("sync_zoom", shape_view, zoom_factor)
        is_2D = False
        if isinstance(shape_view, ObjectViewer2D):
            is_2D = True
            
        if len(self.shape_view_list) > 0:
            if is_2D:
                pass
                #self.shape_view_dolly = self.shape_view_list[0].scale                
            else:
                self.shape_view_dolly = self.shape_view_list[0].dolly
                        
        for sv in self.shape_view_list:
            if sv != shape_view:
                if is_2D:
                    sv.adjust_scale(zoom_factor, recurse=False)
                else:
                    sv.dolly = zoom_factor
                #sv.sync_zoom()
                sv.update()
        for key in self.shape_grid.keys():
            if self.shape_grid[key]['view']:
                if is_2D:
                    self.shape_grid[key]['view'].adjust_scale(zoom_factor)
                else:
                    self.shape_grid[key]['view'].dolly = zoom_factor
                self.shape_grid[key]['view'].update()

    def sync_temp_zoom(self, shape_view, temp_dolly):
        for sv in self.shape_view_list:
            if sv != shape_view:
                sv.temp_dolly = temp_dolly
                #sv.sync_zoom()
                sv.update()
        for key in self.shape_grid.keys():
            if self.shape_grid[key]['view']:
                self.shape_grid[key]['view'].temp_dolly = temp_dolly
                self.shape_grid[key]['view'].update()

    def sync_temp_rotation(self, shape_view, temp_rotate_x, temp_rotate_y):
        for sv in self.shape_view_list:
            if sv != shape_view:
                sv.temp_rotate_x = temp_rotate_x
                sv.temp_rotate_y = temp_rotate_y
                #sv.sync_rotation()
                sv.update()
        for key in self.shape_grid.keys():
            view = self.shape_grid[key]['view']
            if view:
                view.temp_rotate_x = temp_rotate_x
                view.temp_rotate_y = temp_rotate_y
                view.update()

        #self.object_view_3d.sync_rotation(rotation_x, rotation_y)
    def moveEvent(self, event):
        self.reposition_shape_grid()

    def resizeEvent(self, event):
        for idx, shape_view in enumerate(self.shape_view_list):
            width = int(shape_view.width())
            half_width = int(width/2)
            y_pos=0
            x_pos = 0
            if self.mode == MODE_COMPARISON2:
                y_pos = (idx)*32
                x_pos = 32
            if self.mode == MODE_COMPARISON:
                x_pos = 32
            #else:
            shape_label = self.shape_label_list[idx]
            font_metrics = QFontMetrics(shape_label.font())
            text_rect = font_metrics.boundingRect(shape_label.text())

            width = text_rect.width() + 10  # Add some padding for visual comfort
            height = shape_label.height()
            #x, y = shape_label.pos().x(), shape_label.pos().y()  # Get current position
            #shape_label.setGeometry(x, y, width, height) 

            self.shape_label_list[idx].setGeometry(x_pos,y_pos,width,height)
        for idx, button in enumerate(self.shape_button_list):
            #button = self.shape_button_list[idx]
            y_pos=0
            if self.mode == MODE_COMPARISON2:
                y_pos = (idx)*32
            button.setGeometry(0,y_pos,32,32)
        self.reposition_shape_grid()

    def load_comboSelectgroup(self):
        #print("load_comboSelectgroup", self.ignore_change)
        #if self.comboRegressionBy.
        propertyname_index = self.comboGroupBy.currentData()        
        self.comboSelectGroup.clear()
        unique_groupname_list = []
        for idx, obj in enumerate(self.object_info_list):
            if 'variable_list' in obj.keys():
                if propertyname_index > -1 and propertyname_index < len(obj['variable_list']):
                    key_name = obj['variable_list'][self.scatter_variable_index]
                    if key_name not in unique_groupname_list:
                        unique_groupname_list.append(key_name)
                        self.comboSelectGroup.addItem(key_name)
            else:
                if propertyname_index > -1 and propertyname_index < len(obj['property_list']):
                    key_name = obj['property_list'][self.scatter_variable_index]
                    if key_name not in unique_groupname_list:
                        unique_groupname_list.append(key_name)
                        self.comboSelectGroup.addItem(key_name)
        model = self.comboSelectGroup.model()
        # Make all items checkable
        for i in range(model.rowCount()):
            item = model.item(i)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked)  # Initially unchecked                


    def comboGroupBy_changed(self):

        if self.ignore_change == True:
            return
        self.load_comboSelectgroup()            
        self.update_chart()
        self.prepare_shape_view()
        self.resizeEvent(None)
            #shape_combo.setGeometry(150,0,150,20)
        #self.prepare_scatter_data()
        #self.calculate_fit()
        #self.show_analysis_result()

    def comboShapeview_changed(self):
        logger = logging.getLogger(__name__)
        logger.debug("shape_combo_changed")
        #shape_view_index = self.shape_combo_list.index(combo)
        #shape_view = self.shape_view_list[shape_view_index]

        return


    def set_analysis(self, analysis, analysis_method, group_by):
        self.ignore_change = True
        #print("set_analysis", analysis, analysis_method, group_by, self.ignore_change)
        self.analysis = analysis
        self.analysis_method = analysis_method
        self.edtAnalysisName.setText(analysis.analysis_name)
        self.edtSuperimposition.setText(analysis.superimposition_method)
        self.edtOrdination.setText(self.analysis_method)
        #self.edtGroupBy.setText(analysis.group_by)
        self.comboGroupBy.clear()
        self.comboGroupBy.addItem("Select property", -1)
        self.comboRegressionBasedOn.clear()
        self.comboRegressionBasedOn.addItem("Select property", -1)

        valid_property_index_list = analysis.dataset.get_grouping_variable_index_list()
        variablename_list = analysis.dataset.get_variablename_list()
        for idx in valid_property_index_list:
            property = variablename_list[idx]
            self.comboGroupBy.addItem(property, idx)
            self.comboRegressionBasedOn.addItem(property, idx)

        #print("set_analysis 2", analysis, analysis_method, group_by, self.ignore_change)
        if analysis_method == 'PCA':
            #self.lblGroupBy.hide()
            self.comboGroupBy.setEnabled(True)
            self.comboRegressionBasedOn.setEnabled(True)
        else:
            #self.lblGroupBy.show()
            self.comboGroupBy.setEnabled(False)
            self.comboRegressionBasedOn.setEnabled(False)
        
        if group_by in analysis.dataset.get_variablename_list():
            self.comboGroupBy.setCurrentText(group_by)
            self.comboRegressionBasedOn.setCurrentText(group_by)
        else:
            self.comboGroupBy.setCurrentIndex(0)
            self.comboRegressionBasedOn.setCurrentIndex(0)
        #print("going to set mode")

        obj = self.analysis.dataset.object_list[0]
        lm_list = obj.get_landmark_list()
        dim = self.analysis.dataset.dimension
        analysis_dim = len(lm_list)*dim
        #print("set_analysis 3", analysis, analysis_method, group_by, self.ignore_change)

        self.comboAxis1.clear()
        self.comboAxis2.clear()
        self.comboAxis3.clear()

        self.comboAxis1.addItem(CENTROID_SIZE_TEXT,CENTROID_SIZE_VALUE)
        for i in range(analysis_dim):
            self.comboAxis1.addItem("PC"+str(i+1),i)
            self.comboAxis2.addItem("PC"+str(i+1),i)
            self.comboAxis3.addItem("PC"+str(i+1),i)
        #print("set_analysis 4", analysis, analysis_method, group_by, self.ignore_change)

        #print("set_analysis 5", analysis, analysis_method, group_by, self.ignore_change)
        self.object_info_list = json.loads(self.analysis.object_info_json)
        for obj in self.object_info_list:
            if 'property_list' in obj.keys():
                obj['variable_list'] = obj['property_list']
        if self.analysis_method == 'PCA':
            self.analysis_result_list = json.loads(self.analysis.pca_analysis_result_json)
        elif self.analysis_method == 'CVA':
            self.analysis_result_list = json.loads(self.analysis.cva_analysis_result_json)

        #print("set_analysis 6", analysis, analysis_method, group_by, self.ignore_change)

        scatter_variable_name = self.comboGroupBy.currentText()
        regression_variable_name = self.comboRegressionBasedOn.currentText()
        if self.analysis.propertyname_str:
            self.variablename_list = self.analysis.propertyname_str.split(",")
        else:
            # Fallback to dataset's variable names if analysis doesn't have them
            self.variablename_list = self.analysis.dataset.get_variablename_list()
        self.scatter_variable_index = self.variablename_list.index(scatter_variable_name) if scatter_variable_name in self.variablename_list else -1
        self.regression_variable_index = self.variablename_list.index(regression_variable_name) if regression_variable_name in self.variablename_list else -1
        #self.scatter_variable_index = self.variablename_list.index(propertyname) if propertyname in self.variablename_list else -1
        #print("set analysis load_comboselect", self.ignore_change)
        self.load_comboSelectgroup()
        self.set_mode(MODE_EXPLORATION)
        self.ignore_change = False


    def prepare_scatter_data(self):
        show_shape_grid = self.cbxShapeGrid.isChecked()
        show_convex_hull = self.cbxConvexHull.isChecked()
        show_confidence_ellipse = self.cbxConfidenceEllipse.isChecked()
        regression_based_on = self.comboRegressionBasedOn.currentText()
        #regression_by = self.comboRegressionBy.currentText()
        regression_by = "By group"
        show_regression = self.cbxRegression.isChecked()

        select_group_list = []
        for i in range(self.comboSelectGroup.count()):
            item = self.comboSelectGroup.model().item(i)
            if item.checkState() == Qt.Checked:
                select_group_list.append(item.text())
        #print("select_group_list", select_group_list)

        #regression_by_group = self.rbByGroup.isChecked()
        #regression_all_at_once = self.rbAllAtOnce.isChecked()

        axis1 = self.comboAxis1.currentData()
        axis2 = self.comboAxis2.currentData()
        axis3 = self.comboAxis3.currentData()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0
        flip_axis3 = -1.0 if self.cbxFlipAxis3.isChecked() == True else 1.0

        if self.analysis.propertyname_str:
            self.variablename_list = self.analysis.propertyname_str.split(",")
        else:
            # Fallback to dataset's variable names if analysis doesn't have them
            self.variablename_list = self.analysis.dataset.get_variablename_list()
        symbol_candidate = ['o','s','^','x','+','d','v','<','>','p','h']
        symbol_candidate = self.marker_list[:]
        color_candidate = ['blue','green','black','cyan','magenta','yellow','gray','red']
        color_candidate = self.color_list[:]
        #print("color list:", self.color_list, "marker list:", self.marker_list)
        #print("color candidate:", color_candidate, "symbol candidate:", symbol_candidate)

        scatter_variable_name = self.comboGroupBy.currentText()
        regression_variable_name = self.comboRegressionBasedOn.currentText()

        self.scatter_variable_index = self.variablename_list.index(scatter_variable_name) if scatter_variable_name in self.variablename_list else -1
        self.regression_variable_index = self.variablename_list.index(regression_variable_name) if regression_variable_name in self.variablename_list else -1
        self.scatter_data = {}
        self.scatter_result = {}
        self.average_shape = {}
        self.regression_data = {}
        #self.regression_data = { 'x_val':[], 'y_val':[], 'z_val':[] }
        #self.shape_grid = {}
        self.data_range = { 'x_min':99999, 'x_max':-99999, 'y_min':99999, 'y_max':-99999, 'z_min':99999, 'z_max':-99999, 'x_sum': 0, 'y_sum': 0, 'z_sum': 0, 'x_avg': 0, 'y_avg': 0, 'z_avg': 0}
        SCATTER_SMALL_SIZE = 30
        SCATTER_MEDIUM_SIZE = 50
        SCATTER_LARGE_SIZE = 60
        scatter_size = SCATTER_MEDIUM_SIZE
        #if self.plot_size.lower() == 'small':
        #    scatter_size = SCATTER_SMALL_SIZE
        #elif self.plot_size.lower() == 'medium':
        #    scatter_size = SCATTER_MEDIUM_SIZE
        #elif self.plot_size.lower() == 'large':
        #    scatter_size = SCATTER_LARGE_SIZE
        
        #print("removing shape grid")
        for scatter_key_name in self.shape_grid.keys():
            #print("removing shape grid", key_name)
            if self.shape_grid[scatter_key_name]['view'] is not None:
                self.shape_grid[scatter_key_name]['view'].hide()
                self.shape_grid[scatter_key_name]['view'].deleteLater()
                self.shape_grid[scatter_key_name]['view'] = None

        key_list = []
        key_list.append('__default__')
        self.scatter_data['__default__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':color_candidate[0], 'size':scatter_size}
        self.average_shape['__default__'] = { 'x_val':0, 'y_val':0, 'z_val':0, 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':color_candidate[0], 'size':scatter_size}
        self.regression_data['__default__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':color_candidate[0], 'size':scatter_size}
        #regression_key_name = ''
        #scatter_key_name = ''

        for idx, obj in enumerate(self.object_info_list):
            scatter_key_name = '__default__'
            regression_key_name = '__default__'

            if 'variable_list' in obj.keys():  
                if self.scatter_variable_index > -1 and self.scatter_variable_index < len(obj['variable_list']):
                    scatter_key_name = obj['variable_list'][self.scatter_variable_index]
                if self.regression_variable_index > -1 and self.regression_variable_index < len(obj['variable_list']):
                    regression_key_name = obj['variable_list'][self.regression_variable_index]
            else:
                if self.scatter_variable_index > -1 and self.scatter_variable_index < len(obj['property_list']):
                    scatter_key_name = obj['property_list'][self.scatter_variable_index]

            if scatter_key_name not in self.scatter_data.keys():
                self.scatter_data[scatter_key_name] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'property':scatter_key_name, 'symbol':'', 'color':'', 'size':scatter_size}
                self.average_shape[scatter_key_name] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'property':scatter_key_name, 'symbol':'', 'color':'', 'size':scatter_size}
            
            if regression_key_name not in self.regression_data.keys():
                self.regression_data[regression_key_name] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'property':regression_key_name, 'symbol':'', 'color':'', 'size':scatter_size}

            if axis1 == CENTROID_SIZE_VALUE:
                #print("obj:", obj)
                self.scatter_data[scatter_key_name]['x_val'].append(obj['csize'])
                self.regression_data[regression_key_name]['x_val'].append(obj['csize'])
                #if regression_by == 'All' or ( regression_by == 'Select group' and scatter_key_name in select_group_list ):
                #    self.regression_data['x_val'].append(obj['csize'])
            else:
                self.scatter_data[scatter_key_name]['x_val'].append(flip_axis1 * self.analysis_result_list[idx][axis1])
                self.regression_data[regression_key_name]['x_val'].append(flip_axis1 * self.analysis_result_list[idx][axis1])
                #if regression_by == 'All' or ( regression_by == 'Select group' and scatter_key_name in select_group_list ):
                #    self.regression_data['x_val'].append(flip_axis1 * self.analysis_result_list[idx][axis1])
            self.scatter_data[scatter_key_name]['y_val'].append(flip_axis2 * self.analysis_result_list[idx][axis2])
            self.regression_data[regression_key_name]['y_val'].append(flip_axis2 * self.analysis_result_list[idx][axis2])
            #if regression_by == 'All' or ( regression_by == 'Select group' and scatter_key_name in select_group_list ):
            #    self.regression_data['y_val'].append(flip_axis2 * self.analysis_result_list[idx][axis2])
            self.scatter_data[scatter_key_name]['z_val'].append(flip_axis3 * self.analysis_result_list[idx][axis3])
            self.regression_data[regression_key_name]['z_val'].append(flip_axis3 * self.analysis_result_list[idx][axis3])
            #if regression_by == 'All' or ( regression_by == 'Select group' and scatter_key_name in select_group_list ):
            #    self.regression_data['z_val'].append(flip_axis3 * self.analysis_result_list[idx][axis3])

            self.scatter_data[scatter_key_name]['data'].append(obj)
            self.regression_data[regression_key_name]['data'].append(obj)

            self.data_range['x_max'] = max(self.data_range['x_max'], self.scatter_data[scatter_key_name]['x_val'][-1])
            self.data_range['x_min'] = min(self.data_range['x_min'], self.scatter_data[scatter_key_name]['x_val'][-1])
            self.data_range['x_sum'] += self.scatter_data[scatter_key_name]['x_val'][-1]
            self.data_range['y_max'] = max(self.data_range['y_max'], self.scatter_data[scatter_key_name]['y_val'][-1])
            self.data_range['y_min'] = min(self.data_range['y_min'], self.scatter_data[scatter_key_name]['y_val'][-1])
            self.data_range['y_sum'] += self.scatter_data[scatter_key_name]['y_val'][-1]
            self.data_range['z_max'] = max(self.data_range['z_max'], self.scatter_data[scatter_key_name]['z_val'][-1])
            self.data_range['z_min'] = min(self.data_range['z_min'], self.scatter_data[scatter_key_name]['z_val'][-1])
            self.data_range['z_sum'] += self.scatter_data[scatter_key_name]['z_val'][-1]
        
        if show_shape_grid:
            self.data_range['x_avg'] = self.data_range['x_sum'] / len(self.object_info_list)
            self.data_range['y_avg'] = self.data_range['y_sum'] / len(self.object_info_list)
            x_key_list = [ 'x_min', 'x_avg', 'x_max']
            y_key_list = [ 'y_min', 'y_avg', 'y_max']
            for x_key in x_key_list:
                for y_key in y_key_list:
                    scatter_key_name = x_key+"_"+y_key
                    self.shape_grid[scatter_key_name] = { 'x_val': self.data_range[x_key], 'y_val': self.data_range[y_key]}
                    if self.analysis.dataset.dimension == 3:
                        self.shape_grid[scatter_key_name]['view'] = ObjectViewer3D(parent=None,transparent=True)
                    else:
                        self.shape_grid[scatter_key_name]['view'] = ObjectViewer2D(parent=None,transparent=True)
                        self.shape_grid[scatter_key_name]['view'].show_index = False
                    self.shape_grid[scatter_key_name]['view'].set_object_name(scatter_key_name)

        # remove empty group
        if len(self.scatter_data['__default__']['x_val']) == 0:
            del self.scatter_data['__default__']
            del self.average_shape['__default__']
            del self.regression_data['__default__']

        for scatter_key_name in self.scatter_data.keys():
            self.average_shape[scatter_key_name]['x_val'] = np.mean(self.scatter_data[scatter_key_name]['x_val'])
            self.average_shape[scatter_key_name]['y_val'] = np.mean(self.scatter_data[scatter_key_name]['y_val'])
            self.average_shape[scatter_key_name]['z_val'] = np.mean(self.scatter_data[scatter_key_name]['z_val'])
            #group_hash[key_name]['text'].append(obj.object_name)
            #group_hash[key_name]['hoverinfo'].append(obj.id)

        if show_convex_hull:
            for scatter_key_name in self.scatter_data.keys():
                if len(self.scatter_data[scatter_key_name]['x_val']) > 1:
                    self.scatter_data[scatter_key_name]['points'] = np.array([self.scatter_data[scatter_key_name]['x_val'], self.scatter_data[scatter_key_name]['y_val']]).T
                    hull = ConvexHull(self.scatter_data[scatter_key_name]['points'])
                    self.scatter_data[scatter_key_name]['hull'] = hull

        if show_confidence_ellipse:
            for scatter_key_name in self.scatter_data.keys():
                if len(self.scatter_data[scatter_key_name]['x_val']) > 1:
                    covariance = np.cov([self.scatter_data[scatter_key_name]['x_val'], self.scatter_data[scatter_key_name]['y_val']])
                    confidence_level = 0.90  # For 95% confidence ellipse
                    alpha = 1 - confidence_level
                    n_std = stats.chi2.ppf(1 - alpha, df=2)  # Degrees of freedom = 2 for 2D ellipse
                    width, height, angle = mu.get_ellipse_params(covariance, n_std) 
                    self.scatter_data[scatter_key_name]['ellipse'] = (width, height, angle)

        if len(self.scatter_data.keys()) == 0:
            return

        # assign color and symbol
        #sc_idx = 0
        for sc_idx, scatter_key_name in enumerate(self.scatter_data.keys()):
            if self.scatter_data[scatter_key_name]['color'] == '':
                self.scatter_data[scatter_key_name]['color'] = color_candidate[sc_idx % len(color_candidate)]
                self.scatter_data[scatter_key_name]['symbol'] = symbol_candidate[sc_idx % len(symbol_candidate)]
                #sc_idx += 1

        #rg_idx = 0
        for rg_idx, regression_key_name in enumerate(self.regression_data.keys()):
            if self.regression_data[regression_key_name]['color'] == '':
                self.regression_data[regression_key_name]['color'] = color_candidate[rg_idx % len(color_candidate)]
                self.regression_data[regression_key_name]['symbol'] = symbol_candidate[rg_idx % len(symbol_candidate)]
                #sc_idx += 1

    def calculate_fit(self):
        #self.scatter_data[key_name]['y_val']
        show_regression = self.cbxRegression.isChecked()
        if show_regression == False:
            return
        regression_by = "By group" #self.comboRegressionBy.currentText()

        key_list = self.regression_data.keys()
        #print("key list:", key_list)
        self.curve_list = []
        #data_range = self.data_range
        degree_text = self.sbxDegree.text()
        if degree_text == "":
            return
        
        degree = int(degree_text)
        if regression_by == "By group":
            for idx, key in enumerate(key_list):
                x_vals = np.array(self.regression_data[key]['x_val'])
                y_vals = np.array(self.regression_data[key]['y_val'])

                if len(x_vals) < 2:
                    self.curve_list.append( None )
                    #self.shape_view_list[idx].hide()
                else:
                    #self.shape_view_list[idx].show()
                    model = np.polyfit( x_vals, y_vals, degree)
                    #model_list.append(model)
                    r_squared = self.calculate_r_squared(model, x_vals, y_vals)
                    #print(key, model, r_squared)
                    size_range = np.linspace(min(self.regression_data[key]['x_val']), max(self.regression_data[key]['x_val']), 100)
                    size_range2 = np.linspace(self.data_range['x_min'], self.data_range['x_max'], 100)
                    curve = np.polyval(model, size_range)
                    curve2 = np.polyval(model, size_range2)
                    self.curve_list.append( { 'key': key, 'model': model, 'size_range': size_range, 'size_range2': size_range2, 'curve': curve, 'curve2': curve2, 'r_squared': r_squared, 'color': self.regression_data[key]['color'] } )
        else:
            color_candidate = ['blue','green','black','cyan','magenta','yellow','gray','red']
            color_candidate = self.color_list[:]
            color = color_candidate[len(self.scatter_data.keys())]

            x_vals = np.array(self.regression_data['x_val'])
            y_vals = np.array(self.regression_data['y_val'])
            if len(x_vals) < 2:
                self.curve_list.append( None )
                #self.shape_view_list[idx].hide()
            else:
                #self.shape_view_list[idx].show()
                model = np.polyfit( x_vals, y_vals, degree)
                r_squared = self.calculate_r_squared(model, x_vals, y_vals)
                size_range = np.linspace(min(self.regression_data['x_val']), max(self.regression_data['x_val']), 100)
                size_range2 = np.linspace(self.data_range['x_min'], self.data_range['x_max'], 100)
                curve = np.polyval(model, size_range)
                curve2 = np.polyval(model, size_range2)
                self.curve_list.append( { 'key': "All", 'model': model, 'size_range': size_range, 'size_range2': size_range2, 'curve': curve, 'curve2': curve2, 'r_squared': r_squared, 'color': color } )

    def calculate_r_squared(self, model, x_vals, y_vals):
        y_mean = np.mean(y_vals)
        ss_total = np.sum((y_vals - y_mean)**2)
        ss_res = np.sum((y_vals - np.polyval(model, x_vals))**2)
        r_squared = 1 - (ss_res/ss_total)
        return r_squared    

    def show_analysis_result(self):
        #print("show analysis result", datetime.datetime.now())
        #self.plot_widget.clear()
        self.ax2.clear()

        # get axis1 and axis2 value from comboAxis1 and 2 index
        #depth_shade = False
        show_average_shape = self.cbxAverage.isChecked()
        show_regression = self.cbxRegression.isChecked()
        show_annotation = self.cbxAnnotation.isChecked()
        show_legend = self.cbxLegend.isChecked()
        show_convex_hull = self.cbxConvexHull.isChecked()
        show_confidence_ellipse = self.cbxConfidenceEllipse.isChecked()
        show_axis_label = True
        show_extraplolate = self.cbxExtrapolate.isChecked()

        axis1_title = self.comboAxis1.currentText()
        axis2_title = self.comboAxis2.currentText()
        axis3_title = self.comboAxis3.currentText()

        if True:
            self.ax2.clear()
            for name in self.scatter_data.keys():
                #print("name", name, "len(group_hash[name]['x_val'])", len(group_hash[name]['x_val']), group_hash[name]['symbol'])
                group = self.scatter_data[name]
                if len(group['x_val']) > 0:
                    self.scatter_result[name] = self.ax2.scatter(group['x_val'], group['y_val'], s=group['size'], marker=group['symbol'], color=group['color'], data=group['data'], picker=True, pickradius=5)
                    #print("ret", ret)
                if name == '__selected__':
                    for idx, obj in enumerate(group['data']):
                        self.ax2.annotate(obj.object_name, (group['x_val'][idx], group['y_val'][idx]))
            
                if show_average_shape:
                    self.ax2.scatter(self.average_shape[name]['x_val'], self.average_shape[name]['y_val'], s=group['size']*3, marker=group['symbol'], color=group['color'])




            if show_regression:
                if self.curve_list is not None and len(self.curve_list) > 0:
                    for curve in self.curve_list:
                        if curve is None:
                            continue
                        self.ax2.plot(curve['size_range'], curve['curve'], label=curve['key'], color=curve['color']) 
                        if show_extraplolate:
                            self.ax2.plot(curve['size_range2'], curve['curve2'], label=curve['key'], color=curve['color'], linestyle='dashed')
                        degree = len(curve['model'])-1
                        model_text = "Y="
                        #superscript_list = ["⁰","¹","²","³","⁴","⁵","⁶","⁷","⁸","⁹"]
                        for i in range(degree+1):
                            coeff = round(curve['model'][i]*1000)/1000
                            if coeff == 0.0:
                                continue
                            model_text += str(coeff) 
                            
                            if degree != i:
                                model_text += "X"
                                model_text += "^"+str(degree-i) if degree-i > 1 else ""
                                #model_text += str(superscript_list[degree-i]) if degree-i > 1 else ""
                            if i < degree:
                                model_text += " + "
                        r_squared_text = "R^2="+str(round(curve['r_squared']*1000)/1000)                    
                        
                        #self.ax2.annotate(str(curve['model'])+" "+str(curve['r_squared']), (curve['size_range'][50], curve['curve'][50]))
                        if show_annotation:
                            annotation1 = self.ax2.annotate(rf"${model_text}$", (curve['size_range'][10], curve['curve'][10]),fontname='Times New Roman')
                            annotation2 =self.ax2.annotate(rf"${r_squared_text}$", (curve['size_range'][90], curve['curve'][90]),fontname='Times New Roman')
                            annotation1.set_bbox(dict(boxstyle="round", facecolor="white", edgecolor="none", alpha=0.7))
                            annotation2.set_bbox(dict(boxstyle="round", facecolor="white", edgecolor="none", alpha=0.7))


                #self.ax2.plot(size_range, group_a_curve, label='Group A')
            #print("show_legend:", show_legend)
            if show_legend:
                values = []
                keys = []
                for key in self.scatter_result.keys():
                    #print("key", key)
                    if key[0] == '_' or key == '':
                        continue
                    else:
                        keys.append(key)
                        values.append(self.scatter_result[key])
                scatter_legend = self.ax2.legend(values, keys, loc='upper right', bbox_to_anchor=(1.05, 1))
                self.ax2.add_artist(scatter_legend)
                bbox = scatter_legend.get_window_extent()
                # Convert to axis coordinates
                bbox_axis = bbox.transformed(self.ax2.transAxes.inverted())
                # Calculate the height of first legend in axis coordinates
                scatter_legend_height = bbox_axis.height

                if show_regression and self.regression_variable_index != self.scatter_variable_index:
                    values = []
                    keys = []
                    for curve in self.curve_list:
                        #print("curve", curve)
                        if curve:
                            keys.append( curve['key'] )
                            values.append( curve )
                    regression_legend = self.ax2.legend(values,keys, loc='lower right', bbox_to_anchor=(1.05, 0))
                    self.ax2.add_artist(regression_legend)

            #print("show axis label:", show_axis_label)
            if show_axis_label:
                #print("show axis label true")
                ret_x = self.ax2.set_xlabel(axis1_title)
                #print("ret_x", ret_x)
                
                ret_y = self.ax2.set_ylabel(axis2_title)
                #print("ret_y", ret_y)

            #if self.vertical_line_xval is not None:
                #self.ax2.axvline(x=self.vertical_line_xval, color='gray', linestyle=self.vertical_line_style)

            if show_convex_hull:
                #print("showing convex hull")
                for key_name in self.scatter_data.keys():
                    if 'hull' in self.scatter_data[key_name].keys():
                        hull = self.scatter_data[key_name]['hull']
                        for simplex in hull.simplices:
                            self.ax2.plot(self.scatter_data[key_name]['points'][simplex, 0], self.scatter_data[key_name]['points'][simplex, 1], color=self.scatter_data[key_name]['color'])

                        hull_vertices_x = self.scatter_data[key_name]['points'][hull.vertices, 0]
                        hull_vertices_y = self.scatter_data[key_name]['points'][hull.vertices, 1]
                        hull_vertices_x = np.append(hull_vertices_x, hull_vertices_x[0])
                        hull_vertices_y = np.append(hull_vertices_y, hull_vertices_y[0])
                        self.ax2.fill(hull_vertices_x, hull_vertices_y, color=self.scatter_data[key_name]['color'], alpha=0.5)

            if show_confidence_ellipse:
                for key_name in self.scatter_data.keys():
                    if 'ellipse' in self.scatter_data[key_name].keys():
                        width, height, angle = self.scatter_data[key_name]['ellipse']
                        ellipse = matplotlib.patches.Ellipse(xy=(self.average_shape[key_name]['x_val'], self.average_shape[key_name]['y_val']), width=width, height=height, angle=angle, color=self.scatter_data[key_name]['color'], lw=2, alpha=0.3,fill=True)
                        self.ax2.add_patch(ellipse) 

            #self.fig2.tight_layout()
            self.fig2.canvas.draw()
            self.fig2.canvas.flush_events()

            ''' overlay shapes '''
            # shape grid
            show_shape_grid = self.cbxShapeGrid.isChecked()
            # get widget position
            #print("fig_pos", fig_pos)
            if show_shape_grid:
                for keyname in self.shape_grid.keys():
                    shape = self.raw_chart_coords_to_shape(self.shape_grid[keyname]['x_val'], self.shape_grid[keyname]['y_val'])
                    obj = self.shape_to_object(shape)
                    
                    view = self.shape_grid[keyname]['view']
                    view.show()
                    view.set_object(obj)
                    view.apply_rotation(self.rotation_matrix)
                    view.set_shape_preference(self.sgpWidget.get_preference())
                self.reposition_shape_grid()

    def reposition_shape_grid(self):
        #check if self has fig2
        if self.fig2 is None:
            return

        pos_x = self.fig2.canvas.mapToGlobal(QPoint(0, 0)).x()
        pos_y = self.fig2.canvas.mapToGlobal(QPoint(0, 0)).y()
        #print("pos_x", pos_x, "pos_y", pos_y)
        for keyname in self.shape_grid.keys():
            view = self.shape_grid[keyname]['view']
            if view:
                #print("keyname", keyname, "x_val", self.shape_grid[keyname]['x_val'], "y_val", self.shape_grid[keyname]['y_val'])
                transform = self.ax2.transData
                display_coords =    transform.transform((self.shape_grid[keyname]['x_val'], self.shape_grid[keyname]['y_val']))
                x_pixel, y_pixel = display_coords 
                if sys.platform == 'darwin':
                    x_pixel = x_pixel / 2
                    y_pixel = y_pixel / 2
                #print("display_coords", display_coords, "x_pixel", x_pixel, "y_pixel", y_pixel)
                fig_height = self.fig2.canvas.height()
                fig_width = self.fig2.canvas.width()
                view_height = int( fig_height / 4 )
                view_width = int( fig_width / 4 )
                x_pixel = int( x_pixel + pos_x )
                y_pixel = int( fig_height - y_pixel + pos_y )
                self.shape_grid[keyname]['x_pos'] = x_pixel
                self.shape_grid[keyname]['y_pos'] = y_pixel
                w, h = view.width(), view.height()
                #print("view size", w, h, "view pos", x_pixel, y_pixel, "fig_size", fig_width, fig_height)
                w, h = 120, 90
                w = max(w, view_width)
                h = max(h, view_height)
                #print("view size 2  ", w, h, "view pos", x_pixel, y_pixel, "fig_size", fig_width, fig_height)

                view.setGeometry(self.shape_grid[keyname]['x_pos']-int(w/2), self.shape_grid[keyname]['y_pos']-int(h/2), w, h)


    def on_hover_enter(self,event):
        return
        if event.inaxes == self.ax2:  # Check if mouse is over the axes
            self.fig2.canvas.setCursor(QCursor(Qt.CrossCursor))

    def on_hover_leave(self,event):
        return
        self.fig2.canvas.setCursor(QCursor(Qt.ArrowCursor))

    def on_canvas_move(self, evt):
        
        if evt.xdata is None or evt.ydata is None or self.mode == MODE_AVERAGE:
            return

        x_val = evt.xdata
        y_val = evt.ydata
        if self.comboRegressionBy.currentText() == "By group" :
            if x_val > self.data_range['x_max']:
                x_val = self.data_range['x_max']
            if x_val < self.data_range['x_min']:
                x_val = self.data_range['x_min']
            if y_val > self.data_range['y_max']:
                y_val = self.data_range['y_max']
            if y_val < self.data_range['y_min']:
                y_val = self.data_range['y_min']
        else:
            if x_val > max(self.regression_data['x_val']):
                x_val = max(self.regression_data['x_val'])
            if x_val < min(self.regression_data['x_val']):
                x_val = min(self.regression_data['x_val'])
            if y_val > max(self.regression_data['y_val']):
                y_val = max(self.regression_data['y_val'])
            if y_val < min(self.regression_data['y_val']):
                y_val = min(self.regression_data['y_val'])


        if self.axvline is not None:
            #print("remove axvline",self.axvline)
            safe_remove_artist(self.axvline, self.ax2)
            self.axvline = None

        #print(evt.button, evt.xdata, evt.ydata)
        if self.mode in [ MODE_REGRESSION]:
            if evt.button is None:
                self.vertical_line_xval = x_val
                self.vertical_line_style = 'dashed'
                self.axvline = self.ax2.axvline(x=self.vertical_line_xval, color='gray', linestyle=self.vertical_line_style)
                self.fig2.canvas.draw()
                #self.ax2.axvline(x=evt.xdata, color='gray', linestyle='dashed')
                #self.show_analysis_result()
            elif evt.button == 1:
                self.vertical_line_xval = x_val
                self.vertical_line_style = 'solid'
                #print("2-0:",datetime.datetime.now())
                #self.show_analysis_result()
                if self.axvline is not None:
                    safe_remove_artist(self.axvline, self.ax2)
                    self.axvline = None
                self.axvline = self.ax2.axvline(x=self.vertical_line_xval, color='gray', linestyle=self.vertical_line_style)
                self.fig2.canvas.draw()
                #print("2-1:",datetime.datetime.now())
                #self.ax2.axvline(x=evt.xdata, color='gray', linestyle='solid')
                #print("evt:", evt)
                #self.vertical_line_xval = evt.xdata
                #self.ax2.axvline(x=evt.xdata, color='gray', linestyle='solid')
                self.shape_regression(evt)
        elif self.mode in [ MODE_COMPARISON, MODE_EXPLORATION, MODE_COMPARISON2 ]:
            if evt.button == 1 and self.is_picking_shape:
                self.pick_shape(x_val, y_val)
                self.fig2.canvas.draw()
        return

    def on_canvas_button_release(self, evt):
        if self.mode == MODE_AVERAGE:
            return

        if evt.button == 1:
            if self.is_picking_shape:
                # set cursor to crosshair
                if self.mode == MODE_COMPARISON:
                    self.plot_widget2.setCursor(QCursor(Qt.ArrowCursor))
                    self.is_picking_shape = False
                    self.pick_idx = -1
                elif self.mode == MODE_EXPLORATION:
                    self.plot_widget2.setCursor(QCursor(Qt.CrossCursor))
                    self.is_picking_shape = True
                    self.pick_idx = 0
            else:
                self.vertical_line_xval = evt.xdata
                self.vertical_line_style = 'dashed'
        return
        #print("button_release", evt)
        if self.onpick_happened == True:
            self.onpick_happened = False
            return
        self.canvas_up_xy = (evt.x, evt.y)
        if self.canvas_down_xy == self.canvas_up_xy:
            self.tableView1.selectionModel().clearSelection()

    def shape_to_object(self, shape):
        obj = MdObject()
        obj.dataset = self.analysis.dataset
        #print("ds 1:", obj.dataset)
        #ds = MdDataset()
        #print("ds id", self.analysis.dataset_id)
        ds = MdDataset.get(MdDataset.id==self.analysis.dataset_id)
        #print("ds 2:", ds)
        obj.dataset = ds
        #print("dataset:", obj.dataset, obj.dataset_id, obj.dataset.polygon_list, obj.dataset.edge_list)
        obj.landmark_list = []
        for i in range(0,len(shape),self.analysis.dimension):
            landmark = shape[i:i+self.analysis.dimension]
            obj.landmark_list.append(landmark)
        obj.pack_landmark()
        obj.unpack_landmark()
        return obj

    def show_shape(self, shape, idx):
        obj = self.shape_to_object(shape)

        shape_view = self.shape_view_list[idx]

        
        if self.mode == MODE_COMPARISON2:
            shape_view = self.shape_view_list[0]
            shape_view.show_average = False
            shape_view.show_polygon = True
            shape_view.show_wireframe = True
            shape_view.dataset = obj.dataset
            shape_view.polygon_list = obj.dataset.get_polygon_list()
            shape_view.edge_list = obj.dataset.get_edge_list()
            #print("edge_list", obj.dataset.edge_list, "polygon_list:", obj.dataset.polygon_list, "show average:", shape_view.show_average, "show polygon:", shape_view.show_polygon, "show wireframe:", shape_view.show_wireframe)

            if idx == 0:
                shape_view.set_source_shape(obj)
                shape_view.generate_reference_shape()
                shape_view.set_source_shape_preference(self.shape_preference_list[idx].get_preference())
            elif idx == 1:
                shape_view.set_target_shape(obj)
                shape_view.generate_reference_shape()
                shape_view.set_target_shape_preference(self.shape_preference_list[idx].get_preference())
        else:
            shape_view.set_object(obj)
            shape_view.set_shape_preference(self.shape_preference_list[idx].get_preference())

        shape_view.apply_rotation(self.rotation_matrix)
        if self.analysis.dimension == 3:
            shape_view.pan_x = self.shape_view_pan_x
            shape_view.pan_y = self.shape_view_pan_y
            shape_view.dolly = self.shape_view_dolly
        shape_view.update()

    def on_canvas_button_press(self, evt):
        #print("button_press", evt)

        if self.mode == MODE_AVERAGE:
            return

        x_val = evt.xdata
        y_val = evt.ydata
        if x_val is None or y_val is None:
            return
        if x_val > self.data_range['x_max']:
            x_val = self.data_range['x_max']
        if x_val < self.data_range['x_min']:
            x_val = self.data_range['x_min']
        if y_val > self.data_range['y_max']:
            y_val = self.data_range['y_max']
        if y_val < self.data_range['y_min']:
            y_val = self.data_range['y_min']


        if self.mode in [ MODE_REGRESSION ]:
            if evt.button == 1 :
                self.vertical_line_xval = x_val
                self.vertical_line_style = 'solid'
                #print("2-0:",datetime.datetime.now())
                #self.show_analysis_result()
                if self.axvline is not None:
                    safe_remove_artist(self.axvline, self.ax2)
                    self.axvline = None
                if evt.xdata is not None:
                #print("xdata", evt.xdata)
                    self.axvline = self.ax2.axvline(x=self.vertical_line_xval, color='gray', linestyle=self.vertical_line_style)
                    self.fig2.canvas.draw()
                    self.shape_regression(evt)
        elif self.mode in [ MODE_COMPARISON, MODE_EXPLORATION, MODE_COMPARISON2 ]:
            if evt.button == 1 and self.is_picking_shape:
                self.plot_widget2.setCursor(QCursor(Qt.CrossCursor))
                self.pick_shape(x_val, y_val)
                self.fig2.canvas.draw()

        return
        self.canvas_down_xy = (evt.x, evt.y)
        #self.tableView.selectionModel().clearSelection()

    def pick_shape(self, x_val, y_val):
        if self.pick_idx == -1:
            return
        #print("pick_shape", evt.xdata, evt.ydata, self.pick_idx)
        scatter_data_len = len(self.scatter_data.keys())
        marker_list = self.marker_list
        while scatter_data_len+2 > len(marker_list):
            marker_list += self.marker_list
        #print("scatter_data_len", scatter_data_len, self.marker_list, marker_list)
        symbol_candidate = marker_list[scatter_data_len:scatter_data_len+2]
        color_list = self.color_list
        while scatter_data_len+2 > len(color_list):
            color_list += self.color_list
        color_candidate = color_list[scatter_data_len:scatter_data_len+2]
        #print("pick_shape", evt.xdata, evt.ydata, self.pick_idx, scatter_data_len, symbol_candidate, color_candidate)
        shape = self.custom_shape_hash[self.pick_idx]

        if shape['point'] is not None:
            try:
                shape['point'].remove()
            except NotImplementedError:
                # For scatter plots, we need to remove from the axes collection
                if shape['point'] in self.ax2.collections:
                    self.ax2.collections.remove(shape['point'])
            shape['point'] = None
        if shape['label'] is not None:
            try:
                shape['label'].remove()
            except NotImplementedError:
                # For annotations, try removing from axes
                if shape['label'] in self.ax2.texts:
                    self.ax2.texts.remove(shape['label'])
            shape['label'] = None

        ''' need to improve speed by using offset, not creating new annotation every time '''
        #print("shape['name']", shape['name'], x_val, y_val, self.pick_idx, symbol_candidate, color_candidate)
        shape['coords'] = [x_val, y_val]
        shape['point'] = self.ax2.scatter([x_val],[y_val], s=150, marker=symbol_candidate[self.pick_idx], color=color_candidate[self.pick_idx] )
        #print("shape['name']", shape['name'])
        if shape['name'] != '':
            shape['label'] = self.ax2.annotate(shape['name'], (x_val, y_val), xycoords='data',textcoords='offset pixels', xytext=(15,15), ha='center', fontsize=12, color='black')
        #print("point:", self.custom_shape_hash[self.pick_idx]['point'])
        #self.ax2.scatter(self.average_shape[name]['x_val'], self.average_shape[name]['y_val'], s=150, marker=group['symbol'], color=group['color'])

        axis1 = self.comboAxis1.currentData()
        axis2 = self.comboAxis2.currentData()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0
        shape_to_visualize = np.zeros((1,len(self.analysis_result_list[0])))
        x_value = flip_axis1 * x_val
        y_value = flip_axis2 * y_val
        if axis1 != CENTROID_SIZE_VALUE:
            shape_to_visualize[0][axis1] = x_value
        if axis2 != CENTROID_SIZE_VALUE:
            shape_to_visualize[0][axis2] = y_value
        unrotated_shape = self.unrotate_shape(shape_to_visualize)
        #print("0-4:",datetime.datetime.now())
        self.show_shape(unrotated_shape[0], self.pick_idx)

        #self.axvline = self.ax2.axvline(x=self.vertical_line_xval, color='gray', linestyle=self.vertical_line_style)

    def raw_chart_coords_to_shape(self, x_val, y_val):
        axis1 = self.comboAxis1.currentData()
        axis2 = self.comboAxis2.currentData()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0

        x_value = flip_axis1 * x_val
        y_value = flip_axis2 * y_val

        shape_to_visualize = np.zeros((1,len(self.analysis_result_list[0])))
        if axis1 != CENTROID_SIZE_VALUE:
            shape_to_visualize[0][axis1] = x_value
        shape_to_visualize[0][axis2] = y_value
        unrotated_shape = self.unrotate_shape(shape_to_visualize)

        return unrotated_shape[0]

    def shape_regression(self, evt):
        #self.scatter_data[key_name]['y_val']
        #show_regression = self.cbxRegression.isChecked()
        #if show_regression == False:
        #    return
        regression_by = self.comboRegressionBy.currentText()

        #key_list = self.scatter_data.keys()
        #self.curve_list = []
        #data_range = self.data_range
        #degree_text = self.sbxDegree.text()
        #if degree_text == "":
        #    return

        #degree = int(degree_text)
        if regression_by == "By group":

            #print("shape regression", evt.xdata)
            for idx, shape_view in enumerate(self.shape_view_list):
                axis1 = self.comboAxis1.currentData()
                axis2 = self.comboAxis2.currentData()
                flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
                flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0

                x_value = evt.xdata
                if x_value > self.data_range['x_max']:
                    x_value = self.data_range['x_max']
                if x_value < self.data_range['x_min']:
                    x_value = self.data_range['x_min']
                y_value = 0

                # regress curve
                curve = self.curve_list[idx]
                if curve is None:
                    continue
                if x_value >= min(curve['size_range2']) and x_value <= max(curve['size_range2']):
                    y_value = np.polyval(curve['model'], x_value)

                shape = self.raw_chart_coords_to_shape(x_value, y_value)
                self.show_shape(shape, idx)
        else:
            axis1 = self.comboAxis1.currentData()
            axis2 = self.comboAxis2.currentData()
            flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
            flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0

            # regress curve
            idx = 0
            #print("curve_list", self.curve_list)
            curve = self.curve_list[idx]
            if curve is None:
                return

            x_value = evt.xdata
            show_extrapolate = self.cbxExtrapolate.isChecked()
            if show_extrapolate:
                if x_value > self.data_range['x_max']:
                    x_value = self.data_range['x_max']
                if x_value < self.data_range['x_min']:
                    x_value = self.data_range['x_min']
            else:
                if x_value > max(curve['size_range']):
                    x_value = max(curve['size_range'])
                if x_value < min(curve['size_range']):
                    x_value = min(curve['size_range'])
                
            y_value = 0


            if curve is not None:
                y_value = np.polyval(curve['model'], x_value)

            shape = self.raw_chart_coords_to_shape(x_value, y_value)
            self.show_shape(shape, idx)


    def on_pick(self,evt):
        #print("onpick", evt)
        return
        self.onpick_happened = True
        #print("evt", evt, evt.ind, evt.artist )
        selected_object_id_list = []
        for key_name in self.scatter_data.keys():
            if evt.artist == self.scatter_result[key_name]:
                #print("key_name", key_name)
                for idx in evt.ind:
                    obj = self.scatter_data[key_name]['data'][idx]
                    #print("obj", obj)
                    selected_object_id_list.append(obj['id'])
                    #self.ds_ops.select_object(obj.id)

        #print("selected_object_id_list", selected_object_id_list)
        # select rows in tableView
        #self.tableView.clearSelection()
        #selectionModel = self.tableView.selectionModel()

        #print("selected_object_id_list", selected_object_id_list)
        self.selection_changed_off = True
        for id in selected_object_id_list:
            #item = self.object_model.findItems(str(id), Qt.MatchExactly, 0)
            item = self.object_hash[id]
            self.tableView1.selectionModel().select(item.index(),QItemSelectionModel.Rows | QItemSelectionModel.Select)
        self.selection_changed_off = False
        self.on_object_selection_changed([],[])

        #for row in range(self.object_model.rowCount()):
        #    if int(self.object_model.item(row,0).text()) in selected_object_id_list:
        #        self.tableView.selectionModel().select(self.object_model.item(row,0).index(),QItemSelectionModel.Rows | QItemSelectionModel.Select)

    def unrotate_shape(self, shape):
        if self.analysis_method == 'PCA':
            rotation_matrix = json.loads(self.analysis.pca_rotation_matrix_json)
        elif self.analysis_method == 'CVA':
            rotation_matrix = json.loads(self.analysis.cva_rotation_matrix_json)
        #rotation_matrix = json.loads(self.analysis.rotation_matrix_json)
        inverted_matrix = np.linalg.inv(rotation_matrix)
        #print("inverted_matrix", inverted_matrix)
        
        unrotated_shape = np.dot(shape, inverted_matrix)
        
        all_shapes = np.array(json.loads(self.analysis.superimposed_landmark_json))
        # get average of all_shapes
        average_shape = np.mean(all_shapes, axis=0)
        average_shape = average_shape.reshape(1,-1)
        
        # For PCA/CVA space (144D) to original 3D space (216D) conversion
        if average_shape.shape[1] != unrotated_shape.shape[1]:
            # Instead of complex transformation, use the picked point from original space
            # The 'shape' parameter should correspond to original landmark data
            final_shape = average_shape  # For now, just return average shape
            print(f"Note: Using average shape due to dimension mismatch ({unrotated_shape.shape[1]}D vs {average_shape.shape[1]}D)")
        else:
            final_shape = average_shape + unrotated_shape
        #print("final shape", final_shape.shape,final_shape)


        return final_shape



class DatasetAnalysisDialog(QDialog):
    def __init__(self,parent,dataset):
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
        #self.setGeometry(QRect(100, 100, 1400, 800))
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
        self.shape_vsplitter.setSizes([800,20])
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
        self.plot_widget2 = FigureCanvas(Figure(figsize=(20, 16),dpi=100))
        self.fig2 = self.plot_widget2.figure
        self.ax2 = self.fig2.add_subplot()
        self.toolbar2 = NavigationToolbar(self.plot_widget2, self)
        self.plot_widget3 = FigureCanvas(Figure(figsize=(20, 16),dpi=100))
        self.fig3 = self.plot_widget3.figure
        self.ax3 = self.fig3.add_subplot(projection='3d')
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
        #self.plot_layout.addWidget(self.toolbar2)
        #self.plot_layout.addWidget(self.plot_widget2)
        #self.plot_layout.addWidget(self.toolbar3)
        #self.plot_layout.addWidget(self.plot_widget3)
        self.plot_layout.addWidget(self.plot_control_widget1)
        self.plot_layout.addWidget(self.plot_control_widget2)
        self.plot_layout.addWidget(self.btnChartOptions)

        self.plot_all_widget = QWidget()
        self.plot_all_widget.setLayout(self.plot_layout)

        # set value 1 to 10 for axis
        for i in range(1,11):
            self.comboAxis1.addItem("PC"+str(i))
            self.comboAxis2.addItem("PC"+str(i))
            self.comboAxis3.addItem("PC"+str(i))
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

        self.main_hsplitter.setSizes([400,200,400])
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
        #print("set dataset result: ", set_result)
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
            self.color_list[i] = self.m_app.settings.value("DataPointColor/"+str(i), self.default_color_list[i])
        for i in range(len(self.marker_list)):
            self.marker_list[i] = self.m_app.settings.value("DataPointMarker/"+str(i), self.marker_list[i])

        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/DatasetAnalysisWindow", QRect(100, 100, 1400, 800)))
        else:
            self.setGeometry(QRect(100, 100, 1400, 800))
            self.move(self.parent.pos()+QPoint(50,50))

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

        for i in range(1,11):
            self.comboAxis1.addItem(header+str(i))
            self.comboAxis2.addItem(header+str(i))
            self.comboAxis3.addItem(header+str(i))
        self.comboAxis1.setCurrentIndex(axis1)
        self.comboAxis2.setCurrentIndex(axis2)
        self.comboAxis3.setCurrentIndex(axis3)
        #self.reset_tableView()
        #self.load_object()
        #self.on_btn_analysis_clicked()
        
    def select_all(self):
        pass
    def select_none(self):
        pass
    def select_invert(self):
        pass

    def chart_options_clicked(self):
        self.show_chart_options = not self.show_chart_options
        if self.show_chart_options:
            #self.gbChartOptions.show()
            self.plot_control_widget1.show()
            self.plot_control_widget2.show()
        else:
            #self.gbChartOptions.hide()
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
        #print("dataset:", dataset)
        self.dataset = dataset
        prev_lm_count = -1
        for obj in dataset.object_list:
            obj.unpack_landmark()
            obj.unpack_variable()
            #print("property:", obj.variable_list)
            lm_count = len(obj.landmark_list)
            #print("prev_lm_count:", prev_lm_count, "lm_count:", lm_count)
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
                #self.comboAxis2.addItem(propertyname)
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
        #self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        #self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        #self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        #self.cbxShowAverage.stateChanged.connect(self.show_average_state_changed)
        #self.cbxAutoRotate.stateChanged.connect(self.auto_rotate_state_changed)
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
        #print("on_btnAnalyze_clicked")
        self.selected_object_id_list = []
        self.ds_ops.selected_object_id_list = self.selected_object_id_list
        self.load_object()
        self.on_object_selection_changed([],[])
        self.show_analysis_result()
        self.show_object_shape()
        
    def on_btnSaveResults_clicked(self):
        today = datetime. datetime. now()
        date_str = today. strftime("%Y%m%d_%H%M%S")

        filename_candidate = '{}_analysis_{}.xlsx'.format(self.ds_ops.dataset_name, date_str)
        filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
        #print("filepath:", filepath)
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Save File As"), filepath, "Excel format (*.xlsx)")
        if filename:
            #print("filename:", filename)
            doc = xlsxwriter.Workbook(filename)
            
            # PCA result
            property_count = len(self.ds_ops.variablename_list)
            header = [ "object_name", * self.ds_ops.variablename_list ]
            header.extend( [self.analysis_type[:2]+str(i+1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))] )
            header.extend("CSize")
            worksheet = doc.add_worksheet("Result coordinates")
            row_index = 0
            column_index = 0

            for colname in header:
                worksheet.write(row_index, column_index, colname )
                column_index+=1
            
            new_coords = self.analysis_result.rotated_matrix.tolist()
            for i, obj in enumerate(self.ds_ops.object_list):
                worksheet.write(i+1, 0, obj.object_name )
                #print(obj.variable_list)
                for j in range(property_count):
                #for j, property in enumerate(obj.variable_list):
                    worksheet.write(i+1, j+1, obj.variable_list[j] )

                for k, val in enumerate(new_coords[i]):
                    worksheet.write(i+1, k+property_count+1, val )
                    #self.plot_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))
                obj = MdObject.get_by_id(obj.id)
                worksheet.write(i+1, k+property_count+2, obj.get_centroid_size(True))
                

            worksheet = doc.add_worksheet("Rotation matrix")
            row_index = 0
            column_index = 0
            rotation_matrix = self.analysis_result.rotation_matrix.tolist()
            #print("rotation_matrix[0][0]", [0][0], len(self.pca_result.rotation_matrix[0][0]))
            for i, row in enumerate(rotation_matrix):
                for j, val in enumerate(row):
                    worksheet.write(i, j, val )                  

            worksheet = doc.add_worksheet("Eigenvalues")
            for i, val in enumerate(self.analysis_result.raw_eigen_values):
                val2 = self.analysis_result.eigen_value_percentages[i]
                worksheet.write(i, 0, val )
                worksheet.write(i, 1, val2 )


            # PCA result
            #header = [ "object_name", *self.ds_ops.variablename_list ]
            #header.extend( [self.analysis_type[:2]+str(i+1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))] )
            worksheet = doc.add_worksheet("Shapes")
            row_index = 0
            column_index = 0
            for i, colname in enumerate(self.shape_column_header_list):
                worksheet.write(row_index, i, colname )
                #column_index+=1

            for i, shape in enumerate(self.shape_list.tolist()):
                worksheet.write(i+1, 0, self.shape_name_list[i])
                for j, val in enumerate(shape):
                    worksheet.write(i+1, j+1, val)
                    #self.shapes_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))

            doc.close()

        #print("on_btnSaveResults_clicked")
        
    def show_index_state_changed(self):
        if self.cbxShowIndex.isChecked():
            self.lblShape.show_index = True
            #print("show index CHECKED!")
        else:
            self.lblShape.show_index = False
            #print("show index UNCHECKED!")
        self.lblShape.update()

    def show_average_state_changed(self):
        if self.cbxShowAverage.isChecked():
            self.lblShape.show_average = True
            #print("show index CHECKED!")
        else:
            self.lblShape.show_average = False
            #print("show index UNCHECKED!")
        self.lblShape.update()

    def auto_rotate_state_changed(self):
        #print("auto_rotate_state_changed", self.cbxAutoRotate.isChecked())
        if self.cbxAutoRotate.isChecked():
            self.lblShape.auto_rotate = True
            #print("auto rotate CHECKED!")
        else:
            self.lblShape.auto_rotate = False
            #print("auto rotate UNCHECKED!")
        self.lblShape.update()

    def show_wireframe_state_changed(self):
        if self.cbxShowWireframe.isChecked():
            self.lblShape.show_wireframe = True
            #print("show index CHECKED!")
        else:
            self.lblShape.show_wireframe = False
            #print("show index UNCHECKED!")
        self.lblShape.update()

    def show_baseline_state_changed(self):
        if self.cbxShowBaseline.isChecked():
            self.lblShape.show_baseline = True
            #print("show index CHECKED!")
        else:
            self.lblShape.show_baseline = False
            #print("show index UNCHECKED!")
        self.lblShape.update()

        #connect 
        #self.lblShape.sigPain

    def show_object_shape(self):
        self.lblShape.set_ds_ops(self.ds_ops)
        self.lblShape.repaint()

    def on_btn_analysis_clicked(self):
        #print("pca button clicked")
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

        #print("pca_result.nVariable:",pca_result.nVariable)
        #with open('pca_result.txt', 'w') as f:
        #    for obj in ds_ops.object_list:
        #        f.write(obj.object_name + "\t" + "\t".join([str(x) for x in obj.pca_result]) + "\n")

    def show_analysis_result(self):
        #self.plot_widget.clear()

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
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0
        flip_axis3 = -1.0 if self.cbxFlipAxis3.isChecked() == True else 1.0

        symbol_candidate = ['o','s','^','x','+','d','v','<','>','p','h']
        color_candidate = ['blue','green','black','cyan','magenta','yellow','gray','red']
        color_candidate = self.color_list[:]
        symbol_candidate = self.marker_list[:]
        self.propertyname_index = self.comboPropertyName.currentIndex() -1
        self.scatter_data = {}
        self.scatter_result = {}
        SCATTER_SMALL_SIZE = 30
        SCATTER_MEDIUM_SIZE = 50
        SCATTER_LARGE_SIZE = 60
        if self.plot_size.lower() == 'small':
            scatter_size = SCATTER_SMALL_SIZE
        elif self.plot_size.lower() == 'medium':
            scatter_size = SCATTER_MEDIUM_SIZE
        elif self.plot_size.lower() == 'large':
            scatter_size = SCATTER_LARGE_SIZE

        key_list = []
        key_list.append('__default__')
        self.scatter_data['__default__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':color_candidate[0], 'size':scatter_size}
        if len(self.selected_object_id_list) > 0:
            self.scatter_data['__selected__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':'red', 'size':SCATTER_LARGE_SIZE}
            key_list.append('__selected__')

        for obj in self.ds_ops.object_list:
            key_name = '__default__'

            if obj.id in self.selected_object_id_list:
                key_name = '__selected__'
            elif self.propertyname_index > -1 and self.propertyname_index < len(obj.variable_list):
                key_name = obj.variable_list[self.propertyname_index]

            if key_name not in self.scatter_data.keys():
                self.scatter_data[key_name] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'property':key_name, 'symbol':'', 'color':'', 'size':scatter_size}
            if axis1 == 10:
                mdobject = MdObject.get_by_id(obj.id)
                csize = mdobject.get_centroid_size(True)
                #print("obj:", mdobject.id, "csize:", csize)
                self.scatter_data[key_name]['x_val'].append(flip_axis1 * mdobject.get_centroid_size(True))
            else:
                self.scatter_data[key_name]['x_val'].append(flip_axis1 * obj.analysis_result[axis1])
            self.scatter_data[key_name]['y_val'].append(flip_axis2 * obj.analysis_result[axis2])
            self.scatter_data[key_name]['z_val'].append(flip_axis3 * obj.analysis_result[axis3])
            self.scatter_data[key_name]['data'].append(obj)
            #group_hash[key_name]['text'].append(obj.object_name)
            #group_hash[key_name]['hoverinfo'].append(obj.id)

        # remove empty group
        if len(self.scatter_data['__default__']['x_val']) == 0:
            del self.scatter_data['__default__']

        # assign color and symbol
        sc_idx = 0
        for key_name in self.scatter_data.keys():
            if self.scatter_data[key_name]['color'] == '':
                self.scatter_data[key_name]['color'] = color_candidate[sc_idx % len(color_candidate)]
                self.scatter_data[key_name]['symbol'] = symbol_candidate[sc_idx % len(symbol_candidate)]
                sc_idx += 1

        if self.rb2DChartDim.isChecked():
            self.ax2.clear()
            for name in self.scatter_data.keys():
                #print("name", name, "len(group_hash[name]['x_val'])", len(group_hash[name]['x_val']), group_hash[name]['symbol'])
                group = self.scatter_data[name]
                if len(group['x_val']) > 0:
                    self.scatter_result[name] = self.ax2.scatter(group['x_val'], group['y_val'], s=group['size'], marker=group['symbol'], color=group['color'], data=group['data'], picker=True, pickradius=5)
                    #print("ret", ret)
                if name == '__selected__':
                    for idx, obj in enumerate(group['data']):
                        self.ax2.annotate(obj.object_name, (group['x_val'][idx], group['y_val'][idx]))
            if show_legend:
                values = []
                keys = []
                for key in self.scatter_result.keys():
                    #print("key", key)
                    if key[0] == '_':
                        continue
                    else:
                        keys.append(key)
                        values.append(self.scatter_result[key])
                self.ax2.legend(values, keys, loc='upper right', bbox_to_anchor=(1.05, 1))
            if show_axis_label:
                self.ax2.set_xlabel(axis1_title)
                self.ax2.set_ylabel(axis2_title)
            self.fig2.tight_layout()
            self.fig2.canvas.draw()
            self.fig2.canvas.flush_events()
            self.fig2.canvas.mpl_connect('pick_event',self.on_pick)
            self.fig2.canvas.mpl_connect('button_press_event', self.on_canvas_button_press)
            self.fig2.canvas.mpl_connect('button_release_event', self.on_canvas_button_release)
        else:
            self.ax3.clear()
            for name in self.scatter_data.keys():
                group = self.scatter_data[name]
                #print("name", name, "len(group_hash[name]['x_val'])", len(group['x_val']), group['symbol'])
                if len(self.scatter_data[name]['x_val']) > 0:
                    self.scatter_result[name] = self.ax3.scatter(group['x_val'], group['y_val'], group['z_val'], s=group['size'], marker=group['symbol'], color=group['color'], data=group['data'],depthshade=depth_shade, picker=True, pickradius=5)
                if name == '__selected__':
                    for idx, obj in enumerate(group['data']):
                        self.ax3.text(group['x_val'][idx], group['y_val'][idx], group['z_val'][idx],obj.object_name)
                    #print("ret", ret)
            if show_legend:
                values = []
                keys = []
                for key in self.scatter_result.keys():
                    #print("key", key)
                    if key[0] == '_':
                        continue
                    else:
                        keys.append(key)
                        values.append(self.scatter_result[key])
                self.ax3.legend(values, keys, loc='upper left', bbox_to_anchor=(1.05, 1))
            #if show_legend:
            #    self.ax3.legend(self.scatter_result.values(), self.scatter_result.keys(), loc='upper left', bbox_to_anchor=(1.05, 1))
            if show_axis_label:
                self.ax3.set_xlabel(axis1_title)
                self.ax3.set_ylabel(axis2_title)
                self.ax3.set_zlabel(axis3_title)
            self.fig3.tight_layout()
            self.fig3.canvas.draw()
            self.fig3.canvas.flush_events()
            self.fig3.canvas.mpl_connect('pick_event',self.on_pick)
            self.fig3.canvas.mpl_connect('button_press_event', self.on_canvas_button_press)
            self.fig3.canvas.mpl_connect('button_release_event', self.on_canvas_button_release)

    def show_result_table(self):
        
        self.plot_data.clear()
        self.rotation_matrix_data.clear()

        # PCA data
        # set header as "PC1", "PC2", "PC3", ... "PCn
        if self.rbCVA.isChecked():
            header = ["CV"+str(i+1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))]
        else:
            header = ["PC"+str(i+1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))]
        header.append("CSize")
        #print("header", header)
        self.plot_data.setColumnCount(len(header)+1)
        self.plot_data.setHorizontalHeaderLabels(["Name"] + header)

        new_coords = self.analysis_result.rotated_matrix.tolist()
        self.plot_data.setColumnCount(len(new_coords[0])+2)
        for i, obj in enumerate(self.ds_ops.object_list):
            self.plot_data.insertRow(i)
            self.plot_data.setItem(i, 0, QTableWidgetItem(obj.object_name))
            for j, val in enumerate(new_coords[i]):
                self.plot_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))
            mdobject = MdObject.get_by_id(obj.id)
            csize = mdobject.get_centroid_size(True)
            #print("obj:", mdobject.id, "csize:", csize)
            self.plot_data.setItem(i, len(new_coords[0])+1, QTableWidgetItem(str(int(csize*10000)/10000.0)))

        # rotation matrix
        rotation_matrix = self.analysis_result.rotation_matrix.tolist()
        #print("rotation_matrix[0][0]", [0][0], len(self.pca_result.rotation_matrix[0][0]))
        self.rotation_matrix_data.setColumnCount(len(rotation_matrix[0]))
        for i, row in enumerate(rotation_matrix):
            self.rotation_matrix_data.insertRow(i)
            for j, val in enumerate(row):
                self.rotation_matrix_data.setItem(i, j, QTableWidgetItem(str(int(val*10000)/10000.0)))
        
        #self.analysis_result.rotated_matrix

        # eigen values
        self.eigenvalue_data.setColumnCount(2)
        for i, val in enumerate(self.analysis_result.raw_eigen_values):
            val2 = self.analysis_result.eigen_value_percentages[i]
            self.eigenvalue_data.insertRow(i)
            self.eigenvalue_data.setItem(i, 0, QTableWidgetItem(str(int(val*10000)/10000.0)))
            self.eigenvalue_data.setItem(i, 1, QTableWidgetItem(str(int(val2*10000)/10000.0)))

        # shapes tab
        min_vector = self.analysis_result.rotated_matrix.min(axis=0)
        max_vector = self.analysis_result.rotated_matrix.max(axis=0)
        avg_vector = self.analysis_result.rotated_matrix.mean(axis=0)
        # combine 3 vectors to 1 matrix
        shapes = np.vstack((min_vector, avg_vector, max_vector))
        self.shapes_data.clear()
        self.shapes_data.setColumnCount(len(new_coords[0])+1)
        axis1 = self.comboAxis1.currentIndex()
        axis2 = self.comboAxis2.currentIndex()
        axis3 = self.comboAxis3.currentIndex()
        axis1_title = self.comboAxis1.currentText()
        axis2_title = self.comboAxis2.currentText()
        axis3_title = self.comboAxis3.currentText()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0
        flip_axis3 = -1.0 if self.cbxFlipAxis3.isChecked() == True else 1.0
        new_coords = self.analysis_result.rotated_matrix.tolist()
        for i, obj in enumerate(self.ds_ops.object_list):
            obj.analysis_result = new_coords[i]

        #print("shapes", shapes.shape)
        row_header_list = []
        dimension = self.ds_ops.dimension
        vector_length = len(self.analysis_result.rotated_matrix.tolist()[0])
        if dimension == 2:
            axis_label = [ 'x', 'y' ]
        elif dimension == 3:
            axis_label = [ 'x', 'y', 'z' ]
        
        column_header_list = ["name"]
        for i in range(vector_length):
            column_header_list.append(axis_label[i%dimension] + str(int(i/dimension)+1))
        #column_header_list.append("CSize")

        '''
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
        '''


    def on_canvas_button_press(self, evt):
        #print("button_press", evt)
        self.canvas_down_xy = (evt.x, evt.y)
        #self.tableView.selectionModel().clearSelection()

    def on_canvas_button_release(self, evt):
        #print("button_release", evt)
        if self.onpick_happened == True:
            self.onpick_happened = False
            return
        self.canvas_up_xy = (evt.x, evt.y)
        if self.canvas_down_xy == self.canvas_up_xy:
            self.tableView1.selectionModel().clearSelection()


    def on_pick(self,evt):
        #print("onpick", evt)
        self.onpick_happened = True
        #print("evt", evt, evt.ind, evt.artist )
        selected_object_id_list = []
        for key_name in self.scatter_data.keys():
            if evt.artist == self.scatter_result[key_name]:
                #print("key_name", key_name)
                for idx in evt.ind:
                    obj = self.scatter_data[key_name]['data'][idx]
                    #print("obj", obj)
                    selected_object_id_list.append(obj.id)
                    #self.ds_ops.select_object(obj.id)

        #print("selected_object_id_list", selected_object_id_list)
        # select rows in tableView
        #self.tableView.clearSelection()
        #selectionModel = self.tableView.selectionModel()

        #print("selected_object_id_list", selected_object_id_list)
        self.selection_changed_off = True
        for id in selected_object_id_list:
            #item = self.object_model.findItems(str(id), Qt.MatchExactly, 0)
            item = self.object_hash[id]
            self.tableView1.selectionModel().select(item.index(),QItemSelectionModel.Rows | QItemSelectionModel.Select)
        self.selection_changed_off = False
        self.on_object_selection_changed([],[])

        #for row in range(self.object_model.rowCount()):
        #    if int(self.object_model.item(row,0).text()) in selected_object_id_list:
        #        self.tableView.selectionModel().select(self.object_model.item(row,0).index(),QItemSelectionModel.Rows | QItemSelectionModel.Select)


    def on_mouse_clicked(self, event):
        #print("mouse clicked:",event)
        #if event.double():
        #    print("double clicked")
        #else:
        #    print("single clicked")
        p = self.plot_widget.plotItem.vb.mapSceneToView(event.scenePos()) 
        self.status_bar.showMessage("scene pos:" + str(event.scenePos()) + ", data pos:" + str(p))

    def on_mouse_moved(self, pos):
        p = self.plot_widget.plotItem.vb.mapSceneToView(pos)       
        #print("plot widget:",self.plot_widget, "plotItem:",self.plot_widget.plotItem, "vb:",self.plot_widget.plotItem.vb, "mapSceneToView:",self.plot_widget.plotItem.vb.mapSceneToView(pos)) 
        #print("pos:",pos, pos.x(), pos.y(), "p:",p, p.x(), p.y())

        self.status_bar.showMessage("x: %d, y: %d, x2: %f, y2: %f" % (pos.x(), pos.y(), p.x(), p.y()))

    def on_scatter_item_clicked(self, plot, points):
        #print("scatter item clicked:",plot,points)
        self.selected_object_id_list = []
        for pt in points:
            #print("points:",str(pt.data()))
            self.selected_object_id_list.append(pt.data().id)
        # select rows in tableView
        for obj_id in self.selected_object_id_list:
            for row in range(self.object_model.rowCount()):
                if int(self.object_model.item(row,0).text()) == obj_id:
                    self.tableView1.selectRow(row)
                    #break
            
    def PerformCVA(self,dataset_ops):
        cva = MdCanonicalVariate()

        property_index = self.comboPropertyName.currentIndex() -1
        #print("property_index:",property_index)
        if property_index < 0:
            QMessageBox.information(self, "Information", "Please select a property.")
            return
        datamatrix = []
        category_list = []
        #obj = dataset_ops.object_list[0]
        #print(obj, obj.variable_list, property_index)
        for obj in dataset_ops.object_list:
            datum = []
            for lm in obj.landmark_list:
                datum.extend(lm)
            datamatrix.append(datum)
            category_list.append(obj.variable_list[property_index])

        cva.SetData(datamatrix)
        cva.SetCategory(category_list)
        cva.Analyze()

        number_of_axes = min(cva.nObservation, cva.nVariable)
        cva_done = True

        return cva

    def PerformPCA(self,dataset_ops):

        pca = MdPrincipalComponent()
        datamatrix = []
        for obj in dataset_ops.object_list:
            datum = []
            for lm in obj.landmark_list:
                datum.extend( lm )
            datamatrix.append(datum)

        pca.SetData(datamatrix)
        pca.Analyze()

        number_of_axes = min(pca.nObservation, pca.nVariable)
        pca_done = True

        return pca

    def load_object(self):
        # load objects into tableView
        #for object in self.dataset.object_list:
        self.object_model.clear()
        self.property_model.clear()
        self.reset_tableView()
        if self.dataset is None:
            return
        #objects = self.selected_dataset.objects
        self.object_hash = {}

        self.propertyname_index = self.comboPropertyName.currentIndex() -1
        self.propertyname = self.comboPropertyName.currentText()

        self.variable_list = []
        for obj in self.dataset.object_list:
            item0 = QStandardItem()
            item0.setCheckable(True)
            item0.setCheckState(Qt.Checked)
            item0.setData(obj.id,Qt.DisplayRole)

            item1 = QStandardItem()
            item1.setData(obj.id,Qt.DisplayRole)
            item2 = QStandardItem(obj.object_name)
            self.object_hash[obj.id] = item1
            if self.propertyname_index >= 0:
                obj.unpack_variable()
                #print(obj.variable_list)
                item3 = QStandardItem(obj.variable_list[self.propertyname_index])
                if obj.variable_list[self.propertyname_index] not in self.variable_list:
                    self.variable_list.append(obj.variable_list[self.propertyname_index])
                    p_item0 = QStandardItem()
                    p_item0.setCheckable(True)
                    p_item0.setCheckState(Qt.Checked)
                    p_item1 = QStandardItem()
                    p_item1.setCheckable(True)
                    p_item1.setCheckState(Qt.Checked)
                    self.property_model.appendRow([p_item0,p_item1,QStandardItem(obj.variable_list[self.propertyname_index])])
                #self.variable_list.append(obj.variable_list[self.propertyname_index])
                self.object_model.appendRow([item0,item1,item2,item3] )
            else:
                self.object_model.appendRow([item0,item1,item2] )
        

    def reset_tableView(self):
        self.property_model = QStandardItemModel()
        self.property_model.setColumnCount(3)
        self.property_model.setHorizontalHeaderLabels(["Show","Avg","Group"])
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
        self.propertyname_index = self.comboPropertyName.currentIndex() -1
        self.propertyname = self.comboPropertyName.currentText()
        self.object_model.setColumnCount(3)
        self.object_model.setHorizontalHeaderLabels(["", "ID", "Name"])
        self.tableView1.setModel(self.proxy_model)
        #self.tableView.setModel(self.object_model)
        self.tableView1.setColumnWidth(0, 20)
        self.tableView1.setColumnWidth(1, 50)
        self.tableView1.setColumnWidth(2, 150)
        self.tableView1.verticalHeader().setDefaultSectionSize(20)
        self.tableView1.verticalHeader().setVisible(False)
        self.tableView1.setSelectionBehavior(QTableView.SelectRows)
        #self.tableView.clicked.connect(self.on_tableView_clicked)
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
        
        self.tableView1.setStyleSheet("QTreeView::item:selected{background-color: palette(highlight); color: palette(highlightedText);};")

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
        if hasattr(model, 'mapToSource'):
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
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Export"))
        self.parent = parent
        #print(self.parent.pos())
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
        #self.rbMorphologika.setEnabled(False)
        #self.rbMorphologika.setChecked(False)

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
        self.form_layout.addWidget(self.lblDatasetName,0,0)
        self.form_layout.addWidget(self.edtDatasetName,0,1,1,2)
        self.form_layout.addWidget(self.lblObjectList,1,0)
        self.form_layout.addWidget(self.lstObjectList,2,0,2,1)
        self.form_layout.addWidget(self.btnMoveRight,2,1)
        self.form_layout.addWidget(self.btnMoveLeft,3,1)
        self.form_layout.addWidget(self.lblExportList,1,2)
        self.form_layout.addWidget(self.lstExportList,2,2,2,1)
        
        self.button_layout1 = QHBoxLayout()
        self.button_layout1.addWidget(self.btnExport)
        self.button_layout1.addWidget(self.btnCancel)

        self.button_layout2 = QHBoxLayout()
        self.button_layout2.addWidget(self.lblExport)
        self.button_layout2.addWidget(self.rbTPS)
        self.button_layout2.addWidget(self.rbX1Y1)
        self.button_layout2.addWidget(self.rbMorphologika)
        self.button_group2 = QButtonGroup()
        self.button_group2.addButton(self.rbTPS)
        self.button_group2.addButton(self.rbX1Y1)
        self.button_group2.addButton(self.rbMorphologika)

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
            self.move(self.parent.pos()+QPoint(50,50))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/ExportDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def set_dataset(self,dataset):

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
        #for i in range(self.lstExportList.count()):
        ##    item = self.lstExportList.item(i)
        #    export_list.append(item.text())
        if self.rbProcrustes.isChecked():
            self.ds_ops.procrustes_superimposition()
        object_list = self.ds_ops.object_list
        today = datetime.datetime.now()
        date_str = today.strftime("%Y%m%d_%H%M%S")

        if self.rbTPS.isChecked():
            filename_candidate = '{}_{}.tps'.format(self.ds_ops.dataset_name, date_str)
            filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
            filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filepath, "TPS format (*.tps)")
            if filename:
                # open text file
                with open(filename, 'w') as f:
                    for object in object_list:
                        f.write('LM={}\n'.format(len(object.landmark_list)))
                        for lm in object.landmark_list:
                            if self.ds_ops.dimension == 2:
                                f.write('{}\t{}\n'.format(*lm))
                            else:
                                f.write('{}\t{}\t{}\n'.format(*lm))
                        #if object.has_image():
                        #    f.write('IMAGE={}\n'.format(object.image_filename))
                        f.write('ID={}\n'.format(object.object_name))

        elif self.rbMorphologika.isChecked():
            filename_candidate = '{}_{}.txt'.format(self.ds_ops.dataset_name, date_str)
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
                    label_values += '\t'.join(mo.variable_list).strip() + NEWLINE
                    name_values += mo.object_name + NEWLINE
                    #print mo.objname
                    rawpoint_values += "'#" + mo.object_name + NEWLINE
                    for lm in mo.landmark_list:
                        rawpoint_values += '\t'.join([str(c) for c in lm])
                        rawpoint_values += NEWLINE
                #print name_values
                result_str += name_values + label_values + rawpoint_values
                if len(self.dataset.edge_list) > 0:
                    result_str += "[wireframe]" + NEWLINE
                    self.dataset.unpack_wireframe()
                    for edge in self.dataset.edge_list:
                        #print edge
                        result_str += '\t'.join([str(v) for v in edge]) + NEWLINE
                if len(self.dataset.polygon_list) > 0:
                    result_str += "[polygons]" + NEWLINE
                    self.dataset.unpack_polygons()
                    for polygon in self.dataset.polygon_list:
                        #print edge
                        result_str += '\t'.join([str(v) for v in polygon]) + NEWLINE
                for obj_ops in self.ds_ops.object_list:
                    obj = MdObject.get_by_id(obj_ops.id)
                    if obj.has_image():
                        img = obj.get_image()
                        image_values += obj.get_name() + "." + img.get_file_path().split(".")[-1] + NEWLINE
                        old_filepath = img.get_file_path()
                        # get filepath from filename
                        new_image_path = os.path.join(os.path.dirname(filename), obj.get_name() + "." + img.get_file_path().split(".")[-1])
                        shutil.copyfile(old_filepath, new_image_path)

                    else:
                        image_values = "" + NEWLINE
                    if obj.pixels_per_mm is not None and obj.pixels_per_mm > 0:
                        ppmm_values += str(obj.pixels_per_mm) + NEWLINE
                    else:
                        ppmm_values = "" + NEWLINE

                result_str += image_values
                result_str += ppmm_values
                #print("filename:", filename)
                # open text file
                with open(filename, 'w') as f:
                    f.write(result_str)
        self.close()

class ImportDatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Import"))
        self.parent = parent
        #print(self.parent.pos())
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        #self.setGeometry(QRect(100, 100, 600, 400))
        #self.move(self.parent.pos()+QPoint(100,100))

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
        #self.rbnX1Y1.setDisabled(True)
        #self.rbnMorphologika.setDisabled(True)
        self.chkFileType.addButton(self.rbnTPS)
        self.chkFileType.addButton(self.rbnNTS)
        self.chkFileType.addButton(self.rbnX1Y1)
        self.chkFileType.addButton(self.rbnMorphologika)
        self.chkFileType.buttonClicked.connect(self.file_type_changed)
        self.chkFileType.setExclusive(True)
        # add qgroupbox for file type
        self.gbxFileType = QGroupBox()
        self.gbxFileType.setLayout(QHBoxLayout())
        self.gbxFileType.layout().addWidget(self.rbnTPS)
        self.gbxFileType.layout().addWidget(self.rbnNTS)
        self.gbxFileType.layout().addWidget(self.rbnX1Y1)
        self.gbxFileType.layout().addWidget(self.rbnMorphologika)
        self.gbxFileType.layout().addStretch(1)
        self.gbxFileType.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gbxFileType.setMaximumHeight(50)
        self.gbxFileType.setMinimumHeight(50)
        #self.gbxFileType.setTitle("File Type")

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
        #self.main_layout.addRow("File Type", self.cbxFileType)
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
            self.move(self.parent.pos()+QPoint(50,50))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/ImportDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def open_file2(self, filename):
        self.edtFilename.setText(filename)
        self.btnImport.setEnabled(True)
        self.edtDatasetName.setText(Path(filename).stem)
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
        else:
            self.rbnTPS.setChecked(False)
            self.rbnNTS.setChecked(False)
            self.rbnX1Y1.setChecked(False)
            self.rbnMorphologika.setChecked(False)
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
      
            
            #else:
    
    def file_type_changed(self):
        pass

    def import_file(self):

        filename = self.edtFilename.text()
        filetype = self.chkFileType.checkedButton().text()
        datasetname = self.edtDatasetName.text()
        objectcount = self.edtObjectCount.text()
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

        if import_data is None:
            return

        self.btnImport.setEnabled(False)
        self.prgImport.setValue(0)
        self.prgImport.setFormat(self.tr("Importing..."))
        self.prgImport.update()
        self.prgImport.repaint()

        self.edtObjectCount.setText(str(import_data.nobjects))
        #print("objects:", tps.nobjects,tps.nlandmarks,tps.object_name_list)
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
            #dataset.pack_edge_str()
        dataset.save()
        # add objects
        for i in range(import_data.nobjects):
            object = MdObject()
            object.object_name = import_data.object_name_list[i]
            # see if import_data.ppmm_list exist
            if hasattr(import_data, 'ppmm_list') and len(import_data.ppmm_list) > 0:
                if mu.is_numeric(import_data.ppmm_list[i]):
                    object.pixels_per_mm = float(import_data.ppmm_list[i])
                else:
                    object.pixels_per_mm = None
            #print("object:", object.object_name)
            object.dataset = dataset
            object.landmark_str = ""
            landmark_list = []
            #print("object_name", object.object_name, import_data.landmark_data.keys())
            #if object.object_name in import_data.landmark_data.keys():
            #    print("key exist")
            #else:
            #    print("key not exist")
            for landmark in import_data.landmark_data[object.object_name]:
                landmark_list.append("\t".join([ str(x) for x in landmark]))
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
                    new_filepath = new_image.get_file_path( self.m_app.storage_directory)
                    if not os.path.exists(os.path.dirname(new_filepath)):
                        os.makedirs(os.path.dirname(new_filepath))
                    shutil.copyfile(file_name, new_filepath)
                    new_image.save()

            val = int( (float(i+1)*100.0 / float(import_data.nobjects)) )
            #print("progress:", i+1, tps.nobjects, val)
            self.update_progress(val)
            #progress = int( (i / float(tps.nobjects)) * 100)

        #print("tps import done")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText(self.tr("Finished importing a {} file.".format(filetype)))
        msg.setStandardButtons(QMessageBox.Ok)
            
        retval = msg.exec_()
        self.close()
        # add dataset to project
        #self.parent.parent.project.datasets.append(dataset)
        #self.parent.parent.project.current_dataset = dataset

    def update_progress(self, value):
        self.prgImport.setValue(value)
        self.prgImport.setFormat(self.tr("Importing...{}%".format(value)))
        self.prgImport.update()
        self.prgImport.repaint()
        QApplication.processEvents()

class PreferencesDialog(QDialog):
    '''
    PreferencesDialog shows preferences.

    Args:
        None

    Attributes:
        well..
    '''
    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        self.m_app = QApplication.instance()

        self.m_app.remember_geometry = True
        self.toolbar_icon_small = False
        self.toolbar_icon_medium = False
        self.toolbar_icon_large = False
        self.m_app.plot_size = "medium"

        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        #['blue','green','black','cyan','magenta','yellow','gray','red']
        self.m_app.color_list = self.default_color_list[:]
        self.m_app.marker_list = mu.MARKER_LIST[:]

        self.m_app.landmark_pref = {'2D':{'size':1,'color':'#0000FF'},'3D':{'size':1,'color':'#0000FF'}}
        self.m_app.wireframe_pref = {'2D':{'thickness':1,'color':'#FFFF00'},'3D':{'thickness':1,'color':'#FFFF00'}}
        self.m_app.index_pref = {'2D':{'size':1,'color':'#FFFFFF'},'3D':{'size':1,'color':'#FFFFFF'}}
        self.m_app.bgcolor = '#AAAAAA'
        #print("landmark_pref:", self.landmark_pref)
        #print("wireframe_pref:", self.wireframe_pref)

        
        self.setWindowTitle("Preferences")
        #self.lbl_main_view.setMinimumSize(400, 300)
        #print("landmark_pref:", self.landmark_pref)
        #print("wireframe_pref:", self.wireframe_pref)

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
        self.combo2DLandmarkSize.addItems([self.tr("Small"),self.tr("Medium"),self.tr("Large")])
        self.combo2DLandmarkSize.setCurrentIndex(int(self.m_app.landmark_pref['2D']['size']))
        self.lbl2DLandmarkColor = QPushButton()
        self.lbl2DLandmarkColor.setMinimumSize(20,20)
        self.lbl2DLandmarkColor.setStyleSheet("background-color: " + self.m_app.landmark_pref['2D']['color'])
        self.lbl2DLandmarkColor.setToolTip(self.m_app.landmark_pref['2D']['color'])
        self.lbl2DLandmarkColor.setCursor(Qt.PointingHandCursor)
        self.lbl2DLandmarkColor.mousePressEvent = lambda event, dim='2D': self.on_lblLmColor_clicked(event, '2D')
        self.combo2DLandmarkSize.currentIndexChanged.connect(lambda event, dim='2D': self.on_comboLmSize_currentIndexChanged(event, '2D'))

        self.gb2DLandmarkPref.layout().addWidget(self.combo2DLandmarkSize)
        self.gb2DLandmarkPref.layout().addWidget(self.lbl2DLandmarkColor)

        self.gb3DLandmarkPref = QGroupBox()
        self.gb3DLandmarkPref.setLayout(QHBoxLayout())
        self.gb3DLandmarkPref.setTitle(self.tr("3D"))
        self.combo3DLandmarkSize = QComboBox()
        self.combo3DLandmarkSize.addItems([self.tr("Small"),self.tr("Medium"),self.tr("Large")])
        self.combo3DLandmarkSize.setCurrentIndex(int(self.m_app.landmark_pref['3D']['size']))
        self.lbl3DLandmarkColor = QPushButton()
        self.lbl3DLandmarkColor.setMinimumSize(20,20)
        self.lbl3DLandmarkColor.setStyleSheet("background-color: " + self.m_app.landmark_pref['3D']['color'])
        self.lbl3DLandmarkColor.setToolTip(self.m_app.landmark_pref['3D']['color'])
        self.lbl3DLandmarkColor.setCursor(Qt.PointingHandCursor)
        self.lbl3DLandmarkColor.mousePressEvent = lambda event, dim='3D': self.on_lblLmColor_clicked(event, '3D')
        self.combo3DLandmarkSize.currentIndexChanged.connect(lambda event, dim='3D': self.on_comboLmSize_currentIndexChanged(event, '3D'))

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
        self.combo2DWireframeThickness.addItems([self.tr("Thin"),self.tr("Medium"),self.tr("Thick")])
        self.combo2DWireframeThickness.setCurrentIndex(int(self.m_app.wireframe_pref['2D']['thickness']))
        self.lbl2DWireframeColor = QPushButton()
        self.lbl2DWireframeColor.setMinimumSize(20,20)
        self.lbl2DWireframeColor.setStyleSheet("background-color: " + self.m_app.wireframe_pref['2D']['color'])
        self.lbl2DWireframeColor.setToolTip(self.m_app.wireframe_pref['2D']['color'])
        self.lbl2DWireframeColor.setCursor(Qt.PointingHandCursor)
        self.lbl2DWireframeColor.mousePressEvent = lambda event, dim='2D': self.on_lblWireframeColor_clicked(event, '2D')
        self.combo2DWireframeThickness.currentIndexChanged.connect(lambda event, dim='2D': self.on_comboWireframeThickness_currentIndexChanged(event, '2D'))

        self.gb2DWireframePref.layout().addWidget(self.combo2DWireframeThickness)
        self.gb2DWireframePref.layout().addWidget(self.lbl2DWireframeColor)

        self.gb3DWireframePref = QGroupBox()
        self.gb3DWireframePref.setLayout(QHBoxLayout())
        self.gb3DWireframePref.setTitle(self.tr("3D"))
        self.combo3DWireframeThickness = QComboBox()
        self.combo3DWireframeThickness.addItems([self.tr("Thin"),self.tr("Medium"),self.tr("Thick")])
        self.combo3DWireframeThickness.setCurrentIndex(int(self.m_app.wireframe_pref['3D']['thickness']))
        self.lbl3DWireframeColor = QPushButton()
        self.lbl3DWireframeColor.setMinimumSize(20,20)
        self.lbl3DWireframeColor.setStyleSheet("background-color: " + self.m_app.wireframe_pref['3D']['color'])
        self.lbl3DWireframeColor.setToolTip(self.m_app.wireframe_pref['3D']['color'])
        self.lbl3DWireframeColor.setCursor(Qt.PointingHandCursor)
        self.lbl3DWireframeColor.mousePressEvent = lambda event, dim='3D': self.on_lblWireframeColor_clicked(event, '3D')
        self.combo3DWireframeThickness.currentIndexChanged.connect(lambda event, dim='3D': self.on_comboWireframeThickness_currentIndexChanged(event, '3D'))

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
        self.combo2DIndexSize.addItems([self.tr("Small"),self.tr("Medium"),self.tr("Large")])
        self.combo2DIndexSize.setCurrentIndex(int(self.m_app.index_pref['2D']['size']))
        self.lbl2DIndexColor = QPushButton()
        self.lbl2DIndexColor.setMinimumSize(20,20)
        self.lbl2DIndexColor.setStyleSheet("background-color: " + self.m_app.index_pref['2D']['color'])
        self.lbl2DIndexColor.setToolTip(self.m_app.index_pref['2D']['color'])
        self.lbl2DIndexColor.setCursor(Qt.PointingHandCursor)
        self.lbl2DIndexColor.mousePressEvent = lambda event, dim='2D': self.on_lblIndexColor_clicked(event, '2D')
        self.combo2DIndexSize.currentIndexChanged.connect(lambda event, dim='2D': self.on_comboIndexSize_currentIndexChanged(event, '2D'))

        self.gb2DIndexPref.layout().addWidget(self.combo2DIndexSize)
        self.gb2DIndexPref.layout().addWidget(self.lbl2DIndexColor)

        self.gb3DIndexPref = QGroupBox()
        self.gb3DIndexPref.setLayout(QHBoxLayout())
        self.gb3DIndexPref.setTitle(self.tr("3D"))
        self.combo3DIndexSize = QComboBox()
        self.combo3DIndexSize.addItems([self.tr("Small"),self.tr("Medium"),self.tr("Large")])
        self.combo3DIndexSize.setCurrentIndex(int(self.m_app.index_pref['3D']['size']))
        self.lbl3DIndexColor = QPushButton()
        self.lbl3DIndexColor.setMinimumSize(20,20)
        self.lbl3DIndexColor.setStyleSheet("background-color: " + self.m_app.index_pref['3D']['color'])
        self.lbl3DIndexColor.setToolTip(self.m_app.index_pref['3D']['color'])
        self.lbl3DIndexColor.setCursor(Qt.PointingHandCursor)
        self.lbl3DIndexColor.mousePressEvent = lambda event, dim='3D': self.on_lblIndexColor_clicked(event, '3D')
        self.combo3DIndexSize.currentIndexChanged.connect(lambda event, dim='3D': self.on_comboIndexSize_currentIndexChanged(event, '3D'))

        self.gb3DIndexPref.layout().addWidget(self.combo3DIndexSize)
        self.gb3DIndexPref.layout().addWidget(self.lbl3DIndexColor)

        self.index_layout = QHBoxLayout()
        self.index_layout.addWidget(self.gb2DIndexPref)
        self.index_layout.addWidget(self.gb3DIndexPref)
        self.index_widget = QWidget()
        self.index_widget.setLayout(self.index_layout)

        self.lblBgcolor = QPushButton()
        self.lblBgcolor.setMinimumSize(20,20)
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
        #symbol_candidate = ['o','s','^','x','+','d','v','<','>','p','h']

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
        self.btnResetMarkers.setMinimumSize(60,20)
        self.btnResetMarkers.setMaximumSize(100,20)

        self.comboMarker_list = []
        for i in range(len(self.m_app.marker_list)):
            self.comboMarker_list.append(QComboBox())
            self.comboMarker_list[i].addItems(mu.MARKER_LIST)
            self.comboMarker_list[i].setCurrentIndex(mu.MARKER_LIST.index(self.m_app.marker_list[i]))
            self.comboMarker_list[i].currentIndexChanged.connect(lambda event, index=i: self.on_comboMarker_currentIndexChanged(event, index))
            self.gbPlotMarkers.layout().addWidget(self.comboMarker_list[i])
        self.gbPlotMarkers.layout().addWidget(self.btnResetMarkers)

        self.btnResetVivid = QPushButton()
        self.btnResetVivid.setText(self.tr("Vivid"))
        self.btnResetVivid.clicked.connect(self.on_btnResetVivid_clicked)
        self.btnResetVivid.setMinimumSize(60,20)
        self.btnResetVivid.setMaximumSize(100,20)
        self.btnResetPastel = QPushButton()
        self.btnResetPastel.setText(self.tr("Pastel"))
        self.btnResetPastel.clicked.connect(self.on_btnResetPastel_clicked)
        self.btnResetPastel.setMinimumSize(60,20)
        self.btnResetPastel.setMaximumSize(100,20)

        self.lblColor_list = []
        for i in range(len(self.m_app.color_list)):
            self.lblColor_list.append(QPushButton())
            self.lblColor_list[i].setMinimumSize(20,20)
            #self.lblColor_list[i].setMaximumSize(20,20)
            self.lblColor_list[i].setStyleSheet("background-color: " + self.m_app.color_list[i])
            self.lblColor_list[i].setToolTip(self.m_app.color_list[i])
            self.lblColor_list[i].setCursor(Qt.PointingHandCursor)
            self.lblColor_list[i].setText(str(i+1))
            #self.lblColor_list[i].mousePressEvent = self.on_lblColor_clicked
            self.lblColor_list[i].mousePressEvent = lambda event, index=i: self.on_lblColor_clicked(event, index)
            #self.gbPlotColors.layout().addWidget(self.lblColor_list[i])
            # put into layout in two rows
            self.gbPlotColors.layout().addWidget(self.lblColor_list[i], i//10, i%10)

        #self.gbPlotColors.layout().addWidget(self.rbToolbarIconSmall)
        self.gbPlotColors.layout().addWidget(self.btnResetVivid,0,10)
        self.gbPlotColors.layout().addWidget(self.btnResetPastel,1,10)

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
            #print("removed translator")
            self.m_app.translator = None
        else:
            pass
        translator = QTranslator()
        translator_path = mu.resource_path("translations/Modan2_{}.qm".format(self.m_app.language))
        if os.path.exists(translator_path):
            translator.load(translator_path)
            self.m_app.installTranslator(translator)
            self.m_app.translator = translator
        else:
            pass

        self.update_language()


    def on_comboMarker_currentIndexChanged(self, event, index):
        self.current_lblMarker = self.comboMarker_list[index]
        self.m_app.marker_list[self.comboMarker_list.index(self.current_lblMarker)] = self.current_lblMarker.currentText()
        #print(self.marker_list)

    def on_lblColor_clicked(self,event, index):
        self.current_lblColor = self.lblColor_list[index]
        #dialog = ColorPickerDialog(color=QColor(self.current_lblColor.toolTip()))
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.current_lblColor.toolTip())) # return type is QColor
        #print("color: ", color)
        if color is not None:
            self.current_lblColor.setStyleSheet("background-color: " + color.name())
            self.current_lblColor.setToolTip(color.name())
            self.m_app.color_list[self.lblColor_list.index(self.current_lblColor)] = color.name()
            #print(self.color_list)

    def on_lblBgcolor_clicked(self,event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.m_app.bgcolor))
        if color is not None:
            self.m_app.bgcolor = color.name()
            self.lblBgcolor.setStyleSheet("background-color: " + self.m_app.bgcolor)
            self.lblBgcolor.setToolTip(self.m_app.bgcolor)
        self.parent.update_settings()

    def on_comboLmSize_currentIndexChanged(self, event, dim):
        if dim == '2D':
            self.current_comboLmSize = self.combo2DLandmarkSize
        elif dim == '3D':
            self.current_comboLmSize = self.combo3DLandmarkSize
        self.m_app.landmark_pref[dim]['size'] = self.current_comboLmSize.currentIndex()
        self.parent.update_settings()

    def on_lblLmColor_clicked(self,event, dim):
        if dim == '2D':
            self.current_lblLmColor = self.lbl2DLandmarkColor
        elif dim == '3D':
            self.current_lblLmColor = self.lbl3DLandmarkColor
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.current_lblLmColor.toolTip()))
        if color is not None:
            self.current_lblLmColor.setStyleSheet("background-color: " + color.name())
            self.current_lblLmColor.setToolTip(color.name())
            self.m_app.landmark_pref[dim]['color'] = color.name()
        self.parent.update_settings()

    def on_comboIndexSize_currentIndexChanged(self, event, dim):
        if dim == '2D':
            self.current_comboIndexSize = self.combo2DIndexSize
        elif dim == '3D':
            self.current_comboIndexSize = self.combo3DIndexSize
        self.m_app.index_pref[dim]['size'] = self.current_comboIndexSize.currentIndex()
        self.parent.update_settings()

    def on_lblIndexColor_clicked(self,event, dim):
        if dim == '2D':
            self.current_lblIndexColor = self.lbl2DIndexColor
        elif dim == '3D':
            self.current_lblIndexColor = self.lbl3DIndexColor
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.current_lblIndexColor.toolTip()))
        if color is not None:
            self.current_lblIndexColor.setStyleSheet("background-color: " + color.name())
            self.current_lblIndexColor.setToolTip(color.name())
            self.m_app.index_pref[dim]['color'] = color.name()
        self.parent.update_settings()

    def on_comboWireframeThickness_currentIndexChanged(self, event, dim):
        if dim == '2D':
            self.current_comboWireframeThickness = self.combo2DWireframeThickness
        elif dim == '3D':
            self.current_comboWireframeThickness = self.combo3DWireframeThickness
        self.m_app.wireframe_pref[dim]['thickness'] = self.current_comboWireframeThickness.currentIndex()
        self.parent.update_settings()

    def on_lblWireframeColor_clicked(self,event, dim):
        if dim == '2D':
            self.current_lblWireframeColor = self.lbl2DWireframeColor
        elif dim == '3D':
            self.current_lblWireframeColor = self.lbl3DWireframeColor
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.current_lblWireframeColor.toolTip()))
        if color is not None:
            self.current_lblWireframeColor.setStyleSheet("background-color: " + color.name())
            self.current_lblWireframeColor.setToolTip(color.name())
            self.m_app.wireframe_pref[dim]['color'] = color.name()
        self.parent.update_settings()

    def read_settings(self):
        self.m_app.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        self.m_app.toolbar_icon_size = self.m_app.settings.value("ToolbarIconSize", "Medium")
        #print("toolbar_icon_size:", self.m_app.toolbar_icon_size)
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
            self.m_app.color_list[i] = self.m_app.settings.value("DataPointColor/"+str(i), self.default_color_list[i])

        for i in range(len(self.m_app.marker_list)):
            self.m_app.marker_list[i] = self.m_app.settings.value("DataPointMarker/"+str(i), self.m_app.marker_list[i])
        self.m_app.plot_size = self.m_app.settings.value("PlotSize", self.m_app.plot_size)

        self.m_app.landmark_pref['2D']['size'] = self.m_app.settings.value("LandmarkSize/2D", self.m_app.landmark_pref['2D']['size'])
        self.m_app.landmark_pref['2D']['color'] = self.m_app.settings.value("LandmarkColor/2D", self.m_app.landmark_pref['2D']['color'])
        self.m_app.landmark_pref['3D']['size'] = self.m_app.settings.value("LandmarkSize/3D", self.m_app.landmark_pref['3D']['size'])
        self.m_app.landmark_pref['3D']['color'] = self.m_app.settings.value("LandmarkColor/3D", self.m_app.landmark_pref['3D']['color'])
        self.m_app.wireframe_pref['2D']['thickness'] = self.m_app.settings.value("WireframeThickness/2D", self.m_app.wireframe_pref['2D']['thickness'])
        self.m_app.wireframe_pref['2D']['color'] = self.m_app.settings.value("WireframeColor/2D", self.m_app.wireframe_pref['2D']['color'])
        self.m_app.wireframe_pref['3D']['thickness'] = self.m_app.settings.value("WireframeThickness/3D", self.m_app.wireframe_pref['3D']['thickness'])
        self.m_app.wireframe_pref['3D']['color'] = self.m_app.settings.value("WireframeColor/3D", self.m_app.wireframe_pref['3D']['color'])
        self.m_app.index_pref['2D']['size'] = self.m_app.settings.value("IndexSize/2D", self.m_app.index_pref['2D']['size'])
        self.m_app.index_pref['2D']['color'] = self.m_app.settings.value("IndexColor/2D", self.m_app.index_pref['2D']['color'])
        self.m_app.index_pref['3D']['size'] = self.m_app.settings.value("IndexSize/3D", self.m_app.index_pref['3D']['size'])
        self.m_app.index_pref['3D']['color'] = self.m_app.settings.value("IndexColor/3D", self.m_app.index_pref['3D']['color'])
        self.m_app.bgcolor = self.m_app.settings.value("BackgroundColor", self.m_app.bgcolor)
        self.m_app.language = self.m_app.settings.value("Language", "en")
        #print("read language:", self.m_app.language)
        self.update_language()

        if self.m_app.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/PreferencesDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos()+QPoint(100,100))

    def write_settings(self):
        self.m_app.settings.setValue("ToolbarIconSize", self.m_app.toolbar_icon_size)
        self.m_app.settings.setValue("PlotSize", self.m_app.plot_size)
        self.m_app.settings.setValue("WindowGeometry/RememberGeometry", self.m_app.remember_geometry)
        #print(self.color_list)
        for i in range(len(self.m_app.marker_list)):
            self.m_app.settings.setValue("DataPointMarker/"+str(i), self.m_app.marker_list[i])

        for i in range(len(self.m_app.color_list)):
            self.m_app.settings.setValue("DataPointColor/"+str(i), self.m_app.color_list[i])

        if self.m_app.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/PreferencesDialog", self.geometry())

        self.m_app.settings.setValue("LandmarkSize/2D", self.m_app.landmark_pref['2D']['size'])
        self.m_app.settings.setValue("LandmarkColor/2D", self.m_app.landmark_pref['2D']['color'])
        self.m_app.settings.setValue("LandmarkSize/3D", self.m_app.landmark_pref['3D']['size'])
        self.m_app.settings.setValue("LandmarkColor/3D", self.m_app.landmark_pref['3D']['color'])
        self.m_app.settings.setValue("WireframeThickness/2D", self.m_app.wireframe_pref['2D']['thickness'])
        self.m_app.settings.setValue("WireframeColor/2D", self.m_app.wireframe_pref['2D']['color'])
        self.m_app.settings.setValue("WireframeThickness/3D", self.m_app.wireframe_pref['3D']['thickness'])
        self.m_app.settings.setValue("WireframeColor/3D", self.m_app.wireframe_pref['3D']['color'])
        self.m_app.settings.setValue("BackgroundColor", self.m_app.bgcolor)
        self.m_app.settings.setValue("IndexSize/2D", self.m_app.index_pref['2D']['size'])
        self.m_app.settings.setValue("IndexColor/2D", self.m_app.index_pref['2D']['color'])
        self.m_app.settings.setValue("IndexSize/3D", self.m_app.index_pref['3D']['size'])
        self.m_app.settings.setValue("IndexColor/3D", self.m_app.index_pref['3D']['color'])
        self.m_app.settings.setValue("Language", self.m_app.language)
        #print("write language:", self.m_app.language)

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

        item_list = [ (self.tr("Small"), "Small" ), (self.tr("Medium"), "Medium"), (self.tr("Large"), "Large")]
        for item in item_list:
            self.combo2DLandmarkSize.addItem(item[0], item[1])
            self.combo3DLandmarkSize.addItem(item[0], item[1])
            self.combo2DIndexSize.addItem(item[0], item[1])
            self.combo3DIndexSize.addItem(item[0], item[1])

        item_list = [ (self.tr("Thin"), "Thin" ), (self.tr("Medium"), "Medium"), (self.tr("Thick"), "Thick")]
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
