from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QCheckBox, QColorDialog, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, QStatusBar, QMessageBox, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QSizePolicy, \
                            QTableWidget, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox, QInputDialog,\
                            QTabWidget, QListWidget, QSpinBox, QPlainTextEdit, QSlider, QScrollArea, QStyledItemDelegate, \
                            QAction, QShortcut, QMenu
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem, QImage,\
                        QFont, QPainter, QBrush, QMouseEvent, QWheelEvent, QIntValidator, QIcon, QCursor,\
                        QFontMetrics, QKeySequence, QDrag
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSize, QPoint, QAbstractTableModel, QTranslator, \
                         pyqtSlot, pyqtSignal, QItemSelectionModel, QTimer, QEvent, QModelIndex, QObject, QPointF

import logging

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
from OBJFileLoader import OBJ
from MdModel import *
from scipy.spatial.distance import cdist
import OpenGL.GL as gl
from OpenGL import GLU as glu
# Removed GLUT import to prevent Windows compatibility issues
from PyQt5.QtOpenGL import *
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
MODE_GROWTH_TRAJECTORY = 2
MODE_AVERAGE = 3
MODE_COMPARISON = 4
MODE_COMPARISON2 = 5
#MODE_GRID = 6

BASE_LANDMARK_RADIUS = 2
DISTANCE_THRESHOLD = BASE_LANDMARK_RADIUS * 3
CENTROID_SIZE_VALUE = 99
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


class ObjectViewer2D(QLabel):
    def __init__(self, parent=None, transparent=False):
        if transparent:
            super(ObjectViewer2D, self).__init__(parent)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowTransparentForInput | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_NoSystemBackground, True)
        else:
            super(ObjectViewer2D, self).__init__(parent)
        self.transparent = transparent
        self.parent = parent
        logger.info("object viewer 2d init")
        self.setMinimumSize(300,200)

        self.debug = False
        self.landmark_size = 1
        self.landmark_color = "#0000FF"
        self.wireframe_thickness = 1
        self.wireframe_color = "#FFFF00"
        self.index_size = 1
        self.index_color = "#FFFFFF"
        self.bgcolor = "#AAAAAA"
        self.m_app = QApplication.instance()
        self.read_settings()

        self.object_dialog = None
        self.object = None
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.scale = 1.0
        self.prev_scale = 1.0
        self.fullpath = None
        self.image_changed = False
        self.pan_mode = MODE['NONE']
        self.edit_mode = MODE['NONE']
        self.data_mode = OBJECT_MODE

        self.show_index = True
        self.show_wireframe = True
        self.show_polygon = True
        self.show_baseline = False  
        self.read_only = False
        self.show_model = False
        self.show_arrow = False
        self.show_average = False

        self.pan_x = 0
        self.pan_y = 0
        self.temp_pan_x = 0
        self.temp_pan_y = 0
        self.mouse_down_x = 0
        self.mouse_down_y = 0
        self.mouse_curr_x = 0
        self.mouse_curr_y = 0

        self.landmark_list = []
        self.edge_list = []
        self.image_canvas_ratio = 1.0
        self.selected_landmark_index = -1
        self.selected_edge_index = -1
        self.wire_hover_index = -1
        self.wire_start_index = -1
        self.wire_end_index = -1
        self.calibration_from_img_x = -1
        self.calibration_from_img_y = -1
        self.pixels_per_mm = -1
        self.orig_width = -1
        self.orig_height = -1

        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.set_mode(MODE['EDIT_LANDMARK'])
        self.comparison_data = {}
        self.source_preference = None
        self.target_preference = None
        self.ds_ops = None

    def set_source_shape_preference(self, pref):
        self.source_preference = pref
        if self.ds_ops is not None and len(self.ds_ops.object_list) > 0:
            obj = self.ds_ops.object_list[0]
            obj.visible = pref['visible']
            obj.show_landmark = pref['show_landmark']
            obj.show_wireframe = pref['show_wireframe']
            obj.show_polygon = pref['show_polygon']
            obj.opacity = pref['opacity']
            obj.polygon_color = pref['polygon_color']
            obj.edge_color = pref['edge_color']
            obj.landmark_color = pref['landmark_color']
    
    def set_target_shape_preference(self, pref):
        self.target_preference = pref
        if self.ds_ops is not None and len(self.ds_ops.object_list) > 1:
            obj = self.ds_ops.object_list[1]
            obj.visible = pref['visible']
            obj.show_landmark = pref['show_landmark']
            obj.show_wireframe = pref['show_wireframe']
            obj.show_polygon = pref['show_polygon']
            obj.opacity = pref['opacity']
            obj.polygon_color = pref['polygon_color']
            obj.edge_color = pref['edge_color']
            obj.landmark_color = pref['landmark_color']

    def set_source_shape_color(self, color):
        self.source_shape_color = color

    def set_target_shape_color(self, color):
        self.target_shape_color = color

    def set_source_shape(self, object):
        self.comparison_data['source_shape'] = object

    def set_target_shape(self, object):
        self.comparison_data['target_shape'] = object

    def set_intermediate_shape(self, object):
        self.comparison_data['intermediate_shape'] = object

    def generate_reference_shape(self):
        shape_list = []
        ds = MdDataset()
        ds.dimension = self.dataset.dimension
        ds.baseline = self.dataset.baseline
        ds.wireframe = self.dataset.wireframe
        ds.edge_list = self.dataset.edge_list
        ds.polygon_list = self.dataset.polygon_list
        ds_ops = MdDatasetOps(ds)

        if 'source_shape' in self.comparison_data:
            shape_list.append(self.comparison_data['source_shape'])
            source = self.comparison_data['source_shape']
            source_ops = MdObjectOps(source)
            ds_ops.object_list.append(source_ops)
        if 'target_shape' in self.comparison_data:
            shape_list.append(self.comparison_data['target_shape'])
            target = self.comparison_data['target_shape']
            target_ops = MdObjectOps(target)
            ds_ops.object_list.append(target_ops)

        ret = ds_ops.procrustes_superimposition()
        if ret == False:
            logger = logging.getLogger(__name__)
            logger.error("procrustes failed")
            return
        self.comparison_data['ds_ops'] = ds_ops
        self.comparison_data['average_shape'] = ds_ops.get_average_shape()
        self.set_ds_ops(ds_ops)
        
        self.data_mode = DATASET_MODE
        if self.source_preference is not None:
            self.set_source_shape_preference(self.source_preference)
        if self.target_preference is not None:
            self.set_target_shape_preference(self.target_preference)
            
        self.update_tps_grid()

    def set_ds_ops(self, ds_ops):
        self.ds_ops = ds_ops
        self.data_mode = DATASET_MODE
        average_shape = self.ds_ops.get_average_shape()
        self.landmark_list = average_shape.landmark_list
        #self.set_object(average_shape)
        self.calculate_resize()
        self.align_object()
        #scale = self.get_scale_from_object(average_shape)
        #average_shape.rescale(scale)
        #for obj in self.ds_ops.object_list:
        #    obj.rescale(scale)
        self.edge_list = ds_ops.edge_list

    def set_shape_preference(self, object_preference):
        self.shape_preference = object_preference
        if self.obj_ops is not None :
            obj = self.obj_ops
            if 'visible' in object_preference:
                obj.visible = object_preference['visible']
            if 'show_landmark' in object_preference:
                obj.show_landmark = object_preference['show_landmark']
            if 'show_wireframe' in object_preference:
                obj.show_wireframe = object_preference['show_wireframe']
            if 'show_polygon' in object_preference:
                obj.show_polygon = object_preference['show_polygon']
            if 'opacity' in object_preference:
                obj.opacity = object_preference['opacity']
            if 'polygon_color' in object_preference:
                obj.polygon_color = object_preference['polygon_color']
            if 'edge_color' in object_preference:
                obj.edge_color = object_preference['edge_color']
            if 'landmark_color' in object_preference:
                obj.landmark_color = object_preference['landmark_color']
        return

    def apply_rotation(self, angle):
        return

    def set_object_name(self, name):
        self.object_name = name

    def align_object(self):
        if self.orig_pixmap is not None:
            return
        if len(self.landmark_list) == 0:
            return
        if self.data_mode == OBJECT_MODE:
            if self.obj_ops is None:
                return
            self.obj_ops.align(self.dataset.baseline_point_list)
            self.landmark_list = self.obj_ops.landmark_list
        elif self.data_mode == DATASET_MODE:
            for obj_ops in self.ds_ops.object_list:
                obj_ops.align(self.ds_ops.baseline_point_list)

    def set_landmark_pref(self,lm_pref,wf_pref,bgcolor):
        self.landmark_size = lm_pref['size']
        self.landmark_color = lm_pref['color']
        self.wireframe_thickness = wf_pref['thickness']
        self.wireframe_color = wf_pref['color']
        self.bgcolor = bgcolor

    def read_settings(self):
        self.landmark_size = self.m_app.settings.value("LandmarkSize/2D", self.landmark_size)
        self.landmark_color = self.m_app.settings.value("LandmarkColor/2D", self.landmark_color)
        self.wireframe_thickness = self.m_app.settings.value("WireframeThickness/2D", self.wireframe_thickness)
        self.wireframe_color = self.m_app.settings.value("WireframeColor/2D", self.wireframe_color)
        self.index_size = self.m_app.settings.value("IndexSize/2D", self.index_size)
        self.index_color = self.m_app.settings.value("IndexColor/2D", self.index_color)
        self.bgcolor = self.m_app.settings.value("BackgroundColor", self.bgcolor)

    def _2canx(self, coord):
        return round((float(coord) / self.image_canvas_ratio) * self.scale) + self.pan_x + self.temp_pan_x
    def _2cany(self, coord):
        return round((float(coord) / self.image_canvas_ratio) * self.scale) + self.pan_y + self.temp_pan_y
    def _2imgx(self, coord):
        return round(((float(coord) - self.pan_x) / self.scale) * self.image_canvas_ratio)
    def _2imgy(self, coord):
        return round(((float(coord) - self.pan_y) / self.scale) * self.image_canvas_ratio)

    def show_message(self, msg):
        if self.object_dialog is not None:
            self.object_dialog.status_bar.showMessage(msg) 

    def set_mode(self, mode):
        self.edit_mode = mode
        if self.edit_mode == MODE['EDIT_LANDMARK']:
            self.setCursor(Qt.CrossCursor)
            self.show_message(self.tr("Click on image to add landmark"))
        elif self.edit_mode == MODE['READY_MOVE_LANDMARK']:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message(self.tr("Click on landmark to move"))
        elif self.edit_mode == MODE['MOVE_LANDMARK']:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message(self.tr("Move landmark"))
        elif self.edit_mode == MODE['CALIBRATION']:
            self.setCursor(Qt.CrossCursor)
            self.show_message(self.tr("Click on image to calibrate"))
        else:
            self.setCursor(Qt.ArrowCursor)

    def get_landmark_index_within_threshold(self, curr_pos, threshold=DISTANCE_THRESHOLD):
        for index, landmark in enumerate(self.landmark_list):
            lm_can_pos = [self._2canx(landmark[0]),self._2cany(landmark[1])]
            dist = self.get_distance(curr_pos, lm_can_pos)
            if dist < threshold:
                return index
        return -1
    
    def get_edge_index_within_threshold(self, curr_pos, threshold=DISTANCE_THRESHOLD):
        if len(self.edge_list) == 0:
            return -1

        landmark_list = self.landmark_list
        for index, wire in enumerate(self.edge_list):
            from_lm_idx = wire[0]-1
            to_lm_idx = wire[1]-1
            if from_lm_idx >= len(self.landmark_list) or to_lm_idx >= len(self.landmark_list):
                continue

            wire_start = [self._2canx(float(self.landmark_list[from_lm_idx][0])),self._2cany(float(self.landmark_list[from_lm_idx][1]))]
            wire_end = [self._2canx(float(self.landmark_list[to_lm_idx][0])),self._2cany(float(self.landmark_list[to_lm_idx][1]))]
            dist = self.get_distance_to_line(curr_pos, wire_start, wire_end)
            if dist < threshold and dist > 0:
                return index
        return -1
    
    def get_distance_to_line(self, curr_pos, line_start, line_end):
        x1 = line_start[0]
        y1 = line_start[1]
        x2 = line_end[0]
        y2 = line_end[1]
        max_x = max(x1,x2)
        min_x = min(x1,x2)
        max_y = max(y1,y2)
        min_y = min(y1,y2)
        if curr_pos[0] > max_x or curr_pos[0] < min_x or curr_pos[1] > max_y or curr_pos[1] < min_y:
            return -1
        x0 = curr_pos[0]
        y0 = curr_pos[1]
        numerator = abs((y2-y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1)
        denominator = math.sqrt(math.pow(y2-y1,2) + math.pow(x2-x1,2))
        return numerator/denominator

    def get_distance(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def mouseMoveEvent(self, event):
        if self.object_dialog is None:
            return
        me = QMouseEvent(event)
        self.mouse_curr_x = me.x()
        self.mouse_curr_y = me.y()
        curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
    
        if self.pan_mode == MODE['PAN']:
            self.temp_pan_x = int(self.mouse_curr_x - self.mouse_down_x)
            self.temp_pan_y = int(self.mouse_curr_y - self.mouse_down_y)

        elif self.edit_mode == MODE['EDIT_LANDMARK']:
            near_idx = self.get_landmark_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
            if near_idx >= 0:
                self.set_mode(MODE['READY_MOVE_LANDMARK'])
                self.selected_landmark_index = near_idx

        elif self.edit_mode == MODE['WIREFRAME']:
            near_idx = self.get_landmark_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
            if near_idx >= 0:
                self.selected_edge_index = -1
                if self.wire_hover_index < 0:
                    self.wire_hover_index = near_idx
                else:
                    pass
            elif self.wire_start_index >= 0:
                self.wire_hover_index = -1
            else:
                self.wire_hover_index = -1
                near_wire_idx = self.get_edge_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
                if near_wire_idx >= 0:
                    edge = self.edge_list[near_wire_idx]
                    self.selected_edge_index = near_wire_idx
                else:
                    self.selected_edge_index = -1

        elif self.edit_mode == MODE['MOVE_LANDMARK']:
            if self.selected_landmark_index >= 0:
                self.landmark_list[self.selected_landmark_index] = [self._2imgx(self.mouse_curr_x), self._2imgy(self.mouse_curr_y)]
                if self.object_dialog is not None:
                    self.object_dialog.update_landmark(self.selected_landmark_index, *self.landmark_list[self.selected_landmark_index])

        elif self.edit_mode == MODE['READY_MOVE_LANDMARK']:
            curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
            ready_landmark = self.landmark_list[self.selected_landmark_index]
            lm_can_pos = [self._2canx(ready_landmark[0]),self._2cany(ready_landmark[1])]
            if self.get_distance(curr_pos, lm_can_pos) > DISTANCE_THRESHOLD:
                self.set_mode(MODE['EDIT_LANDMARK'])
                self.selected_landmark_index = -1
            
        self.repaint()
        QLabel.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        me = QMouseEvent(event)
        if me.button() == Qt.LeftButton:
            if self.edit_mode == MODE['EDIT_LANDMARK']:
                if self.orig_pixmap is None:
                    return
                img_x = self._2imgx(self.mouse_curr_x)
                img_y = self._2imgy(self.mouse_curr_y)
                if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                    return
                self.object_dialog.add_landmark(img_x, img_y)
            elif self.edit_mode == MODE['READY_MOVE_LANDMARK']:
                self.set_mode(MODE['MOVE_LANDMARK'])
            elif self.edit_mode == MODE['WIREFRAME']:
                if self.wire_hover_index >= 0:
                    if self.wire_start_index < 0:
                        self.wire_start_index = self.wire_hover_index
                        self.wire_hover_index = -1
            elif self.edit_mode == MODE['CALIBRATION']:
                self.calibration_from_img_x = self._2imgx(self.mouse_curr_x)
                self.calibration_from_img_y = self._2imgy(self.mouse_curr_y)

        elif me.button() == Qt.RightButton:
            if self.edit_mode == MODE['WIREFRAME']:
                if self.wire_start_index >= 0:
                    self.wire_start_index = -1
                    self.wire_hover_index = -1
                elif self.selected_edge_index >= 0:
                    self.delete_edge(self.selected_edge_index)                    
                    self.selected_edge_index = -1
            elif self.edit_mode == MODE['READY_MOVE_LANDMARK']:
                if self.selected_landmark_index >= 0:
                    self.object_dialog.delete_landmark(self.selected_landmark_index)
                    self.selected_landmark_index = -1
                    self.set_mode(MODE['EDIT_LANDMARK'])
            else:
                self.pan_mode = MODE['PAN']
                self.mouse_down_x = me.x()
                self.mouse_down_y = me.y()

        self.repaint()

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        if self.object_dialog is None:
            return
        me = QMouseEvent(ev)
        if self.pan_mode == MODE['PAN']:
            self.pan_mode = MODE['NONE']
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
            self.repaint()
        elif self.edit_mode == MODE['MOVE_LANDMARK']:
            self.set_mode(MODE['EDIT_LANDMARK'])
            self.selected_landmark_index = -1
        elif self.edit_mode == MODE['WIREFRAME']:
            if self.wire_start_index >= 0 and self.wire_hover_index >= 0:
                #print("wire start:", self.wire_start_index, "wire hover:", self.wire_hover_index)
                self.add_edge(self.wire_start_index, self.wire_hover_index)
                self.wire_start_index = -1
                self.wire_hover_index = -1
                self.wire_end_index = -1
        elif self.edit_mode == MODE['CALIBRATION']:
            diff_x = self._2imgx(self.mouse_curr_x) - self.calibration_from_img_x
            diff_y = self._2imgy(self.mouse_curr_y) - self.calibration_from_img_y
            dist = math.sqrt(diff_x * diff_x + diff_y * diff_y)
            self.object_dialog.calibrate(dist)
            self.calibration_from_img_x = -1
            self.calibration_from_img_y = -1

        self.repaint()
        return super().mouseReleaseEvent(ev)    

    def wheelEvent(self, event):
        we = QWheelEvent(event)
        scale_delta_ratio = 0
        if we.angleDelta().y() > 0:
            scale_delta_ratio = 0.1
        else:
            scale_delta_ratio = -0.1
        if self.scale <= 0.8 and scale_delta_ratio < 0:
            return

        self.prev_scale = self.scale
        self.adjust_scale(scale_delta_ratio)
        scale_proportion = self.scale / self.prev_scale
        self.pan_x = round( we.pos().x() - (we.pos().x() - self.pan_x) * scale_proportion )
        self.pan_y = round( we.pos().y() - (we.pos().y() - self.pan_y) * scale_proportion )

        QLabel.wheelEvent(self, event)
        self.repaint()
        event.accept()

    def adjust_scale(self, scale_delta_ratio, recurse = True):
        if self.parent != None and callable(getattr(self.parent, 'sync_zoom', None)) and recurse == True:
            self.parent.sync_zoom(self, scale_delta_ratio)

        if self.scale > 1:
            scale_delta = math.floor(self.scale) * scale_delta_ratio
        else:
            scale_delta = scale_delta_ratio

        self.scale += scale_delta
        self.scale = round(self.scale * 10) / 10

        if self.orig_pixmap is not None:
            self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_pixmap.width() * self.scale / self.image_canvas_ratio), int(self.orig_pixmap.height() * self.scale / self.image_canvas_ratio))

        self.repaint()

    def reset_pose(self):
        self.calculate_resize()

    def dragEnterEvent(self, event):
        if self.object_dialog is None:
            return
        file_name = event.mimeData().text()
        if file_name.split('.')[-1].lower() in mu.IMAGE_EXTENSION_LIST:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self.object_dialog is None:
            return

        file_path = event.mimeData().text()
        file_path = mu.process_dropped_file_name(file_path)

        self.set_image(file_path)
        
        self.calculate_resize()
        if self.object_dialog is not None:
            self.object_dialog.set_object_name(Path(file_path).stem)
            self.object_dialog.btnLandmark_clicked()    
            self.object_dialog.btnLandmark.setDown(True)
            self.object_dialog.btnLandmark.setEnabled(True)

    def draw_dataset(self, painter):
        ds_ops = self.ds_ops
        logger = logging.getLogger(__name__)
        logger.debug(f"draw dataset: {ds_ops}, objects: {ds_ops.object_list}")
        if self.show_arrow and len(ds_ops.object_list) > 1:
            self.draw_arrow(painter, 0, 1)

        for idx, obj in enumerate(ds_ops.object_list):
            logger.debug(f"draw object: {obj}, landmarks: {obj.landmark_list}")
            if obj.visible == False:
                continue
            if obj.id in ds_ops.selected_object_id_list:
                object_color = COLOR['SELECTED_SHAPE']
            else:
                if obj.landmark_color is not None:
                    object_color = mu.as_gl_color(obj.landmark_color)
                else:
                    object_color = mu.as_gl_color(self.landmark_color) #COLOR['NORMAL_SHAPE']
            edge_color=self.wireframe_color
            if obj.edge_color is not None:
                edge_color = obj.edge_color
            polygon_color=self.wireframe_color
            if obj.polygon_color is not None:
                polygon_color = obj.polygon_color

            self.draw_object(painter, obj, landmark_as_sphere=False, color=object_color, edge_color=edge_color,polygon_color=polygon_color)

        if self.show_average:
            object_color = COLOR['AVERAGE_SHAPE']
            self.draw_object(ds_ops.get_average_shape(), landmark_as_sphere=True, color=object_color)

    def draw_dataset(self, painter):
        ds_ops = self.ds_ops
        
        # Generate TPS grid if not already generated
        if not hasattr(self, 'grid_lines_transformed'):
            self.generate_tps_grid()
        
        # Draw TPS grid
        if hasattr(self, 'grid_lines_transformed'):
            pen = QPen(QColor(235, 235, 235, 70))  # Light blue, semi-transparent
            pen.setWidth(2)
            painter.setPen(pen)
            
            # Draw transformed grid lines
            for direction, line in self.grid_lines_transformed:
                points = [QPointF(self._2canx(p[0]), self._2cany(p[1])) for p in line]
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
        
        # Draw shapes
        if self.show_arrow and len(ds_ops.object_list) > 1:
            self.draw_arrow(painter, 0, 1)

        for idx, obj in enumerate(ds_ops.object_list):
            if obj.visible == False:
                continue
            if obj.id in ds_ops.selected_object_id_list:
                object_color = COLOR['SELECTED_SHAPE']
            else:
                if obj.landmark_color is not None:
                    object_color = mu.as_gl_color(obj.landmark_color)
                else:
                    object_color = mu.as_gl_color(self.landmark_color)
            edge_color = self.wireframe_color
            if obj.edge_color is not None:
                edge_color = obj.edge_color
            polygon_color = self.wireframe_color
            if obj.polygon_color is not None:
                polygon_color = obj.polygon_color

            self.draw_object(painter, obj, landmark_as_sphere=False, 
                            color=object_color, edge_color=edge_color,
                            polygon_color=polygon_color)

        if self.show_average:
            object_color = COLOR['AVERAGE_SHAPE']
            self.draw_object(ds_ops.get_average_shape(), landmark_as_sphere=True, 
                            color=object_color)


    def draw_arrow(self, painter, start_idx, end_idx):
        from_obj = self.ds_ops.object_list[start_idx]
        to_obj = self.ds_ops.object_list[end_idx]
        for idx, from_lm in enumerate(from_obj.landmark_list):
            to_lm = to_obj.landmark_list[idx]
            from_x = from_lm[0]
            from_y = from_lm[1]
            to_x = to_lm[0]
            to_y = to_lm[1]
            self.draw_line( painter, from_x, from_y, to_x, to_y, COLOR['RED'])
    
    def draw_object(self, painter, obj, landmark_as_sphere=False, color=COLOR['NORMAL_SHAPE'], edge_color=COLOR['WIREFRAME'], polygon_color=COLOR['WIREFRAME']):
        if obj.show_landmark:
            for idx, landmark in enumerate(obj.landmark_list):
                self.draw_landmark(painter, landmark[0], landmark[1], color)
        if obj.show_wireframe:
            for edge in self.ds_ops.edge_list:
                from_lm_idx = edge[0]-1
                to_lm_idx = edge[1]-1
                if from_lm_idx >= len(obj.landmark_list) or to_lm_idx >= len(obj.landmark_list):
                    continue
                from_lm = obj.landmark_list[from_lm_idx]
                to_lm = obj.landmark_list[to_lm_idx]
                self.draw_line(painter, from_lm[0], from_lm[1], to_lm[0], to_lm[1], edge_color)
        return
        if obj.show_polygon:
            for polygon in obj.polygon_list:
                polygon_points = []
                for idx in polygon:
                    if idx >= len(obj.landmark_list):
                        continue
                    landmark = obj.landmark_list[idx]
                    polygon_points.append(landmark)
                self.draw_polygon(polygon_points, polygon_color)
       
    def draw_line(self, painter, from_x, from_y, to_x, to_y, color):
        #print("color:", color)
        painter.setPen(QPen(mu.as_qt_color(color), 2))
        painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))

    def draw_landmark(self, painter, x, y, color):
        radius = BASE_LANDMARK_RADIUS * (int(self.landmark_size) + 1) 
        painter.setPen(QPen(mu.as_qt_color(color), 2))
        painter.setBrush(QBrush(mu.as_qt_color(color)))
        painter.drawEllipse(int(self._2canx(x)-radius), int(self._2cany(y))-radius, radius*2, radius*2)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.transparent == False:
            painter.fillRect(self.rect(), QBrush(QColor(self.bgcolor)))
        if self.object is None:
            #print("no object")
            if self.ds_ops is not None:
                self.draw_dataset(painter)
            return
        if self.curr_pixmap is not None:
            painter.drawPixmap(self.pan_x+self.temp_pan_x, self.pan_y+self.temp_pan_y,self.curr_pixmap)

        if self.show_wireframe == True:
            if self.obj_ops.edge_color:
                color = QColor(self.obj_ops.edge_color)
            else:
                color = QColor(self.wireframe_color)
            painter.setPen(QPen(color, int(self.wireframe_thickness)+1))
            painter.setBrush(QBrush(color))                

            for wire in self.edge_list:
                from_lm_idx = wire[0]-1
                to_lm_idx = wire[1]-1
                if from_lm_idx >= len(self.landmark_list) or to_lm_idx >= len(self.landmark_list):
                    continue
                [ from_x, from_y ] = self.landmark_list[from_lm_idx]
                [ to_x, to_y ] = self.landmark_list[to_lm_idx]
                painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))
            if self.selected_edge_index >= 0:
                edge = self.edge_list[self.selected_edge_index]
                from_lm_idx = edge[0]-1
                to_lm_idx = edge[1]-1
                painter.setPen(QPen(mu.as_qt_color(COLOR['SELECTED_EDGE']), 2))
                if from_lm_idx >= len(self.landmark_list) or to_lm_idx >= len(self.landmark_list):
                    pass
                else:
                    [ from_x, from_y ] = self.landmark_list[from_lm_idx]
                    [ to_x, to_y ] = self.landmark_list[to_lm_idx]
                    painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))

        radius = BASE_LANDMARK_RADIUS * (int(self.landmark_size) + 1) 
        painter.setPen(QPen(Qt.blue, 2))
        painter.setBrush(QBrush(Qt.blue))
        if self.edit_mode == MODE['CALIBRATION']:
            if self.calibration_from_img_x >= 0 and self.calibration_from_img_y >= 0:
                x1 = int(self._2canx(self.calibration_from_img_x))
                y1 = int(self._2cany(self.calibration_from_img_y))
                x2 = self.mouse_curr_x
                y2 = self.mouse_curr_y
                painter.setPen(QPen(mu.as_qt_color(COLOR['SELECTED_LANDMARK']), 2))
                painter.drawLine(x1,y1,x2,y2)

        painter.setFont(QFont('Helvetica', 10 + int(self.index_size) * 3))
        for idx, landmark in enumerate(self.landmark_list):
            if idx == self.wire_hover_index:
                painter.setPen(QPen(mu.as_qt_color(COLOR['SELECTED_LANDMARK']), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR['SELECTED_LANDMARK'])))
            elif idx == self.wire_start_index or idx == self.wire_end_index:
                painter.setPen(QPen(mu.as_qt_color(COLOR['SELECTED_LANDMARK']), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR['SELECTED_LANDMARK'])))
            elif idx == self.selected_landmark_index:
                painter.setPen(QPen(mu.as_qt_color(COLOR['SELECTED_LANDMARK']), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR['SELECTED_LANDMARK'])))
            else:
                if self.obj_ops.landmark_color:
                    color = QColor(self.obj_ops.landmark_color)
                else:
                    color = QColor(self.landmark_color)
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(color))                
            painter.drawEllipse(int(self._2canx(landmark[0])-radius), int(self._2cany(landmark[1]))-radius, radius*2, radius*2)
            if self.show_index == True:
                idx_color = QColor(self.index_color)
                painter.setPen(QPen(idx_color, 2 ))
                painter.setBrush(QBrush(idx_color))
                painter.drawText(int(self._2canx(landmark[0])+10), int(self._2cany(landmark[1]))+10, str(idx+1))

        # draw wireframe being edited
        if self.wire_start_index >= 0:
            painter.setPen(QPen(mu.as_qt_color(COLOR['WIREFRAME']), 2))
            painter.setBrush(QBrush(mu.as_qt_color(COLOR['WIREFRAME'])))
            start_lm = self.landmark_list[self.wire_start_index]
            painter.drawLine(int(self._2canx(start_lm[0])), int(self._2cany(start_lm[1])), self.mouse_curr_x, self.mouse_curr_y)

        if self.object.pixels_per_mm is not None and self.object.pixels_per_mm > 0:
            pixels_per_mm = self.object.pixels_per_mm
            max_scalebar_size = 120
            bar_width = ( float(pixels_per_mm) / self.image_canvas_ratio ) * self.scale
            actual_length = 1.0
            while bar_width > max_scalebar_size:
                bar_width /= 10.0
                actual_length /= 10.0
            if bar_width * 10.0 < max_scalebar_size:
                bar_width *= 10.0
                actual_length *= 10.0
            elif bar_width * 5.0 < max_scalebar_size:
                bar_width *= 5.0
                actual_length *= 5.0
            elif bar_width * 2.0 < max_scalebar_size:
                bar_width *= 2.0
                actual_length *= 2.0

            bar_width = int(math.floor(bar_width + 0.5))
            x = self.width() - 15 - ( bar_width + 20 )
            y = self.height() - 15 - 35

            painter.setPen(QPen(Qt.white, 1))
            painter.setBrush(QBrush(Qt.white))
            painter.drawRect(x, y, bar_width + 20, 30)
            x += 10
            y += 20
            painter.setPen(QPen(Qt.black, 1))
            painter.drawLine(x, y, x + bar_width, y)
            painter.drawLine(x, y - 5, x, y + 5)
            painter.drawLine(x + bar_width, y - 5, x + bar_width, y + 5)
            if actual_length >= 1000:
                length_text = str(int(actual_length / 1000.0)) + " m"
            elif actual_length >= 10:
                length_text = str(int(actual_length /10)) + " cm"
            elif actual_length >= 1:
                length_text = str(int(actual_length)) + " mm"
            elif actual_length >= 0.001:
                length_text = str(int(actual_length * 1000.0)) + " um"
            else:
                length_text = str(round(actual_length * 1000000.0 *1000)/1000) + " nm"
            painter.setPen(QPen(Qt.black, 1))
            painter.setFont(QFont('Helvetica', 10))
            painter.drawText(x + int(math.floor(float(bar_width) / 2.0 + 0.5)) - len(length_text) * 4, y - 5, length_text)
        
        if self.debug:
            painter.setPen(QPen(Qt.black, 1))
            painter.setFont(QFont('Helvetica', 10))
            painter.drawText( 10, 20, f"Scale: {self.scale} prev_scale: {self.prev_scale} image_to_canvas_ratio: {self.image_canvas_ratio}, pan: {self.pan_x}, {self.pan_y}" )

    def update_landmark_list(self):
        return

    def calculate_resize(self):
        if self.orig_pixmap is not None:
            self.orig_width = self.orig_pixmap.width()
            self.orig_height = self.orig_pixmap.height()
            image_wh_ratio = self.orig_width / self.orig_height
            label_wh_ratio = self.width() / self.height()
            if image_wh_ratio > label_wh_ratio:
                self.image_canvas_ratio = self.orig_width / self.width()
            else:
                self.image_canvas_ratio = self.orig_height / self.height()
            self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_width*self.scale/self.image_canvas_ratio),int(self.orig_width*self.scale/self.image_canvas_ratio), Qt.KeepAspectRatio)
        else:
            if len(self.landmark_list) < 2:
                return
            # no image landmark showing
            min_x = 999999999
            max_x = -999999999
            min_y = 999999999
            max_y = -999999999
            for idx, landmark in enumerate(self.landmark_list):
                if landmark[0] < min_x:
                    min_x = landmark[0]
                if landmark[0] > max_x:
                    max_x = landmark[0]
                if landmark[1] < min_y:
                    min_y = landmark[1]
                if landmark[1] > max_y:
                    max_y = landmark[1]
            width = max_x - min_x
            height = max_y - min_y
            w_scale = ( self.width() * 1.0 ) / ( width * 1.5 )
            h_scale = ( self.height() * 1.0 ) / ( height * 1.5 )
            self.scale = min(w_scale, h_scale)
            self.pan_x = int( -min_x * self.scale + (self.width() - width * self.scale) / 2.0 )
            self.pan_y = int( -min_y * self.scale + (self.height() - height * self.scale) / 2.0 )

    def resizeEvent(self, event):
        self.calculate_resize()
        QLabel.resizeEvent(self, event)

    def set_object(self, object):
        m_app = QApplication.instance()
        self.object = object
        self.dataset = object.dataset

        if self.object.pixels_per_mm is not None and self.object.pixels_per_mm > 0:
            self.pixels_per_mm = self.object.pixels_per_mm
        if object.image.count() > 0:
            image_path = object.image[0].get_file_path(m_app.storage_directory)
            if image_path is not None and os.path.exists(image_path):
                self.set_image(image_path)
            else:
                self.clear_object()

        object.unpack_landmark()
        object.dataset.unpack_wireframe()

        if isinstance(object, MdObject):
            self.object = object
            obj_ops = MdObjectOps(object)
        elif object is None:
            self.object = MdObject()
            obj_ops = MdObjectOps(self.object)

        self.ds_ops = MdDatasetOps(self.dataset)
        self.obj_ops = obj_ops
        self.data_mode = OBJECT_MODE
        self.pan_x = self.pan_y = 0
        self.rotate_x = self.rotate_y = 0
        self.edge_list = self.dataset.unpack_wireframe()


        self.landmark_list = object.landmark_list
        self.edge_list = object.dataset.edge_list
        self.calculate_resize()
        if self.dataset.baseline is not None:
            self.dataset.unpack_baseline()
            self.align_object()

    def set_image(self,file_path):
        if self.fullpath is not None:
            self.image_changed = True
        
        self.fullpath = file_path
        self.curr_pixmap = self.orig_pixmap = QPixmap(file_path)
        self.setPixmap(self.curr_pixmap)

    def clear_object(self):
        #print("object view clear object")
        self.landmark_list = []
        self.edge_list = []
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.object = None
        self.ds_ops = None
        self.pan_x = 0
        self.pan_y = 0
        self.temp_pan_x = 0
        self.temp_pan_y = 0
        self.scale = 1.0
        self.image_canvas_ratio = 1.0
        self.update()

    def add_edge(self,wire_start_index, wire_end_index):
        #print("add edge")
        if wire_start_index == wire_end_index:
            return
        if wire_start_index > wire_end_index:
            wire_start_index, wire_end_index = wire_end_index, wire_start_index
        dataset = self.object.dataset
        #print("edge list 1:", dataset.edge_list)
        for wire in dataset.edge_list:
            if wire[0] == wire_start_index+1 and wire[1] == wire_end_index+1:
                return
        dataset.edge_list.append([wire_start_index+1, wire_end_index+1])
        #print("edge list 2:", dataset.edge_list)
        dataset.pack_wireframe()
        dataset.save()
        
    def delete_edge(self, edge_index):
        dataset = self.object.dataset
        dataset.edge_list.pop(edge_index)
        dataset.pack_wireframe()
        dataset.save()

    def generate_tps_grid(self):
        """Generate TPS grid for visualization"""
        if self.ds_ops is None or len(self.ds_ops.object_list) < 2:
            return
        
        # Get source and target points
        source_obj = self.ds_ops.object_list[0]
        target_obj = self.ds_ops.object_list[1]
        
        source_points = np.array(source_obj.landmark_list)
        target_points = np.array(target_obj.landmark_list)
        
        # Add boundary points around the shape
        def create_boundary_points(points, n_points=24):
            # Calculate shape bounds
            center = np.mean(points, axis=0)
            points_centered = points - center
            
            # Calculate radius based on shape size
            max_dist = np.max(np.sqrt(np.sum(points_centered**2, axis=1)))
            radius = max_dist * 1.2  # Make boundary slightly larger than shape
            
            # Generate boundary points in a circle
            angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
            boundary = np.column_stack((
                center[0] + radius * np.cos(angles),
                center[1] + radius * np.sin(angles)
            ))
            return boundary
        
        # Add boundary points
        boundary_source = create_boundary_points(source_points)
        boundary_target = create_boundary_points(target_points)
        
        # Combine with landmark points
        self.source_with_boundary = np.vstack([source_points, boundary_source])
        self.target_with_boundary = np.vstack([target_points, boundary_target])
        
        # Create rectangular grid that encloses the shape
        padding = 0.1
        x_min = np.min(source_points[:, 0]) - padding
        x_max = np.max(source_points[:, 0]) + padding
        y_min = np.min(source_points[:, 1]) - padding
        y_max = np.max(source_points[:, 1]) + padding
        
        # Generate grid points
        n_grid = 20  # Number of grid lines
        x = np.linspace(x_min, x_max, n_grid)
        y = np.linspace(y_min, y_max, n_grid)
        
        # Create vertical and horizontal lines
        self.grid_lines_orig = []
        
        # Vertical lines
        for i in range(n_grid):
            line_points = np.array([(x[i], y_) for y_ in y])
            self.grid_lines_orig.append(('v', line_points))
        
        # Horizontal lines
        for i in range(n_grid):
            line_points = np.array([(x_, y[i]) for x_ in x])
            self.grid_lines_orig.append(('h', line_points))
        
        # Calculate TPS parameters
        self.tps_weights, self.tps_affine = self.calculate_tps_params(
            self.source_with_boundary, 
            self.target_with_boundary
        )
        
        # Transform grid lines
        self.grid_lines_transformed = []
        for direction, line in self.grid_lines_orig:
            transformed_line = np.array([
                self.transform_point(p, self.source_with_boundary, self.tps_weights, self.tps_affine)
                for p in line
            ])
            self.grid_lines_transformed.append((direction, transformed_line))

    def calculate_tps_params(self, control_points, target_points):
        """Calculate TPS transformation parameters"""
        def U(r):
            return (r**2) * np.log(r + np.finfo(float).eps)
        
        n = control_points.shape[0]
        K = cdist(control_points, control_points)
        K = U(K)
        P = np.hstack([np.ones((n, 1)), control_points])
        L = np.vstack([
            np.hstack([K, P]),
            np.hstack([P.T, np.zeros((3, 3))])
        ])
        Y = np.vstack([target_points, np.zeros((3, 2))])
        params = np.linalg.solve(L, Y)
        return params[:-3], params[-3:]

    def transform_point(self, point, control_points, weights, affine):
        """Transform a single point using TPS"""
        def U(r):
            return (r**2) * np.log(r + np.finfo(float).eps)
        
        k = cdist(point.reshape(1, -1), control_points)
        k = U(k)
        wx = weights[:, 0]
        wy = weights[:, 1]
        px = np.sum(k * wx) + affine[0, 0] + affine[1, 0] * point[0] + affine[2, 0] * point[1]
        py = np.sum(k * wy) + affine[0, 1] + affine[1, 1] * point[0] + affine[2, 1] * point[1]
        return np.array([px, py])

    def update_tps_grid(self):
        """Update TPS grid after shape changes"""
        if hasattr(self, 'grid_lines_transformed'):
            delattr(self, 'grid_lines_transformed')
        self.generate_tps_grid()
        self.update()

class ObjectViewer3D(QGLWidget):
    def __init__(self, parent=None, transparent=False):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=== ObjectViewer3D.__init__ started ===")
        
        logger.info(f"ObjectViewer3D init params - parent: {type(parent) if parent else None}, transparent: {transparent}")
        
        try:
            if transparent:
                logger.info("ObjectViewer3D: Using transparent mode")
                logger.info("ObjectViewer3D: Creating QGLFormat...")
                fmt = QGLFormat()
                logger.info("ObjectViewer3D: Setting alpha channel...")
                fmt.setAlpha(True)  # Ensure the format includes an alpha channel
                logger.info("ObjectViewer3D: Calling super().__init__ with format...")
                super(ObjectViewer3D, self).__init__(fmt, parent)
                logger.info("ObjectViewer3D: QGLWidget constructor complete (transparent mode)")
                
                logger.info("ObjectViewer3D: Setting window flags...")
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowTransparentForInput | Qt.Tool)
                logger.info("ObjectViewer3D: Setting attributes...")
                self.setAttribute(Qt.WA_TranslucentBackground)
                self.setAttribute(Qt.WA_NoSystemBackground, True)
                logger.info("ObjectViewer3D: Transparent mode setup complete")
            else:
                logger.info("ObjectViewer3D: Using standard mode")
                logger.info("ObjectViewer3D: Calling QGLWidget.__init__...")
                QGLWidget.__init__(self,parent)
                logger.info("ObjectViever3D: QGLWidget constructor complete (standard mode)")
                
        except Exception as e:
            logger.error(f"ObjectViewer3D: QGLWidget construction FAILED: {e}")
            import traceback
            logger.error("ObjectViewer3D constructor traceback:")
            for line in traceback.format_exc().splitlines():
                logger.error(f"  {line}")
            raise
        logger.info("ObjectViewer3D: Setting up member variables...")
        self.transparent = transparent
        self.parent = parent
        
        logger.info("ObjectViewer3D: Setting minimum size...")
        self.setMinimumSize(120,90)
        logger.info("ObjectViewer3D: Setting default colors and sizes...")
        self.landmark_size = 1
        self.landmark_color = "#0000FF"
        self.wireframe_thickness = 1
        self.wireframe_color = "#FFFF00"
        self.index_size = 1
        self.index_color = "#FFFFFF"
        self.bgcolor = "#AAAAAA"
        self.arrow_color = "#FFFF00"
        
        logger.info("ObjectViewer3D: Getting QApplication instance...")
        self.m_app = QApplication.instance()
        logger.info(f"ObjectViewer3D: QApplication instance: {self.m_app}")
        
        logger.info("ObjectViewer3D: Reading settings...")
        self.read_settings()
        logger.info("ObjectViewer3D: Settings read complete")
        logger.info("ObjectViewer3D: Setting object properties...")
        self.object_name = ""
        self.source_preference = None
        self.target_preference = None

        logger.info("ObjectViewer3D: Configuring widget behavior...")
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        logger.info("ObjectViewer3D: Widget behavior configured")
        logger.info("ObjectViewer3D: Initializing state variables...")
        self.object_dialog = None
        self.ds_ops = None
        self.ds_ops_comp = None
        self.obj_ops = None
        
        logger.info("ObjectViewer3D: Setting up transformation variables...")
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.temp_pan_x = 0
        self.temp_pan_y = 0
        self.rotate_x = 0
        self.rotate_y = 0
        self.temp_rotate_x = 0
        self.temp_rotate_y = 0
        
        logger.info("ObjectViewer3D: Setting display flags...")
        self.show_index = False
        self.show_wireframe = True
        self.show_polygon = True
        self.show_baseline = False
        self.show_average = True
        self.show_model = True
        self.show_arrow = False

        logger.info("ObjectViewer3D: Setting up interaction variables...")
        self.curr_x = 0
        self.curr_y = 0
        self.down_x = 0
        self.down_y = 0
        self.temp_dolly = 0
        self.dolly = 0
        self.data_mode = OBJECT_MODE
        self.view_mode = VIEW_MODE
        self.edit_mode = MODE['NONE']
        self.auto_rotate = False
        self.is_dragging = False
        
        logger.info("ObjectViewer3D: Setting up timer...")
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.timeout)
        logger.info("ObjectViewer3D: Starting timer...")
        self.timer.start()
        logger.info("ObjectViewer3D: Timer started successfully")
        
        logger.info("ObjectViewer3D: Setting up rendering variables...")
        self.frustum_args = {'width': 1.0, 'height': 1.0, 'znear': 0.1, 'zfar': 1000.0}
        self.color_to_lm_idx = {}
        self.lm_idx_to_color = {}
        
        logger.info("ObjectViewer3D: Finalizing initialization...")
        self.picker_buffer = None
        self.gl_list = None
        self.temp_edge = []
        self.object = None
        
        # Initialize aspect ratio with safe default value to prevent paintGL crashes
        self.aspect = 1.0  # Safe default aspect ratio
        logger.info("ObjectViewer3D: Set default aspect ratio to 1.0")
        
        logger.info("=== ObjectViewer3D.__init__ completed successfully ===")
        self.polygon_list = []
        self.comparison_data = {}

        #self.no_drawing = False
        self.wireframe_from_idx = -1
        self.wireframe_to_idx = -1
        self.selected_landmark_idx = -1
        self.selected_edge_index = -1
        self.no_hit_count = 0
        self.threed_model = None
        self.cursor_on_vertex = -1
        self.rotation_matrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
        ])
        self.initialized = False
        self.fullpath = None
        self.edge_list = []
        self.landmark_list = []

    def set_object_name (self, object_name):
        self.object_name = object_name

    def set_landmark_pref(self,lm_pref,wf_pref):
        self.landmark_size = lm_pref['size']
        self.landmark_color = lm_pref['color']
        self.wireframe_thickness = wf_pref['thickness']
        self.wireframe_color = wf_pref['color']

    def read_settings(self):
        self.landmark_size = self.m_app.settings.value("LandmarkSize/3D", self.landmark_size)
        self.landmark_color = self.m_app.settings.value("LandmarkColor/3D", self.landmark_color)
        self.wireframe_thickness = self.m_app.settings.value("WireframeThickness/3D", self.wireframe_thickness)
        self.wireframe_color = self.m_app.settings.value("WireframeColor/3D", self.wireframe_color)
        self.index_size = self.m_app.settings.value("IndexSize/3D", self.index_size)
        self.index_color = self.m_app.settings.value("IndexColor/3D", self.index_color)
        self.bgcolor = self.m_app.settings.value("BackgroundColor", self.bgcolor)

    def show_message(self, msg):
        if self.object_dialog is not None:
            self.object_dialog.status_bar.showMessage(msg) 

    def set_mode(self, mode):
        self.edit_mode = mode  
        if self.edit_mode == MODE['EDIT_LANDMARK']:
            #print("edit landmark")
            self.initialize_colors()
            self.setCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
        elif self.edit_mode == MODE['READY_MOVE_LANDMARK']:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Click on landmark to move")
        elif self.edit_mode == MODE['MOVE_LANDMARK']:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Move landmark")
        elif self.edit_mode == MODE['WIREFRAME']:
            self.initialize_colors()
            self.setCursor(Qt.ArrowCursor)
            self.show_message("Wireframe mode")
        else:
            self.setCursor(Qt.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        self.down_x = event.x()
        self.down_y = event.y()
        if event.buttons() == Qt.LeftButton:
            if self.edit_mode == MODE['WIREFRAME'] and self.selected_landmark_idx > -1:
                self.wireframe_from_idx = self.selected_landmark_idx
                self.temp_edge = [ self.obj_ops.landmark_list[self.wireframe_from_idx][:], self.obj_ops.landmark_list[self.wireframe_from_idx][:]]
            elif self.edit_mode == MODE['EDIT_LANDMARK'] and self.selected_landmark_idx > -1:
                self.set_mode(MODE['MOVE_LANDMARK'])
                self.stored_landmark = { 'index': self.selected_landmark_idx, 'coords': self.threed_model.original_vertices[self.selected_landmark_idx] }
            else:                
                self.view_mode = ROTATE_MODE
        elif event.buttons() == Qt.RightButton:
            if self.edit_mode == MODE['WIREFRAME'] and self.selected_edge_index > -1:
                self.delete_wire(self.selected_edge_index)
            elif self.edit_mode == MODE['EDIT_LANDMARK'] and self.cursor_on_vertex > -1:
                pass
            else:
                self.view_mode = ZOOM_MODE
        elif event.buttons() == Qt.MiddleButton:
            self.view_mode = PAN_MODE

    def mouseReleaseEvent(self, event):
        import datetime
        self.is_dragging = False
        self.curr_x = event.x()
        self.curr_y = event.y()
        if event.button() == Qt.LeftButton:
            if self.edit_mode == MODE['WIREFRAME'] and self.wireframe_from_idx > -1:
                if self.selected_landmark_idx > -1 and self.selected_landmark_idx != self.wireframe_from_idx:
                    self.wireframe_to_idx = self.selected_landmark_idx
                    self.add_wire(self.wireframe_from_idx, self.wireframe_to_idx)
                    self.wireframe_from_idx = -1
                    self.wireframe_to_idx = -1
                    self.update()
                else:
                    self.wireframe_from_idx = -1
                    self.wireframe_to_idx = -1
                    self.update()
                self.temp_edge = []

            elif self.edit_mode == MODE['EDIT_LANDMARK'] and self.cursor_on_vertex > -1 and self.curr_x == self.down_x and self.curr_y == self.down_y:
                x, y, z = self.threed_model.original_vertices[self.cursor_on_vertex]
                self.object_dialog.add_landmark(x,y,z)
                self.update_landmark_list()
                self.initialize_colors()
                self.calculate_resize()
            elif self.edit_mode == MODE['MOVE_LANDMARK'] and self.selected_landmark_idx > -1 and self.cursor_on_vertex > -1:
                self.update_landmark_list()
                self.initialize_colors()
                self.calculate_resize()
                self.selected_landmark_idx = -1
                self.cursor_on_vertex = -1
                self.set_mode(MODE['EDIT_LANDMARK'])
            else:
                if self.data_mode == OBJECT_MODE and self.obj_ops is not None:
                    if self.parent != None and callable(getattr(self.parent, 'sync_rotation', None)):
                        self.parent.sync_rotation()
                    else:
                        self.sync_rotation()
                elif self.data_mode == DATASET_MODE and self.ds_ops is not None:
                    if self.parent != None and callable(getattr(self.parent, 'sync_rotation', None)):
                    #if self.parent != None and self.parent.sync_rotation is not None:
                        self.parent.sync_rotation()
                    else:
                        self.sync_rotation()
                self.temp_rotate_x = 0
                self.temp_rotate_y = 0
        elif event.button() == Qt.RightButton:
            if self.edit_mode == MODE['EDIT_LANDMARK'] and self.selected_landmark_idx > -1 and self.curr_x == self.down_x and self.curr_y == self.down_y:
                self.object_dialog.delete_landmark(self.selected_landmark_idx)
                self.update_landmark_list()
                self.initialize_colors()
                self.calculate_resize()
            else:
                self.dolly += self.temp_dolly 
                self.temp_dolly = 0
                if self.parent != None and callable(getattr(self.parent, 'sync_zoom', None)):
                    self.parent.sync_zoom(self, self.dolly)
                if self.parent != None and callable(getattr(self.parent, 'sync_temp_zoom', None)):
                    self.parent.sync_temp_zoom(self, self.temp_dolly)

        elif event.button() == Qt.MiddleButton:
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
            if self.parent != None and callable(getattr(self.parent, 'sync_temp_pan', None)):
                self.parent.sync_temp_pan(self, self.temp_pan_x, self.temp_pan_y)
            if self.parent != None and callable(getattr(self.parent, 'sync_pan', None)):
                self.parent.sync_pan(self, self.pan_x, self.pan_y)

        self.view_mode = VIEW_MODE
        self.updateGL()

    def mouseMoveEvent(self, event):
        self.curr_x = event.x()
        self.curr_y = event.y()
        if self.edit_mode == MODE["WIREFRAME"]:
            kind, idx = self.hit_test(self.curr_x, self.curr_y)
            if kind == 'Landmark':
                lm_idx = idx
            
                if lm_idx > -1:
                    self.selected_landmark_idx = lm_idx
                    self.no_hit_count = 0
                elif self.selected_landmark_idx > -1:
                    self.no_hit_count += 1
                    if self.no_hit_count > 5:
                        self.selected_landmark_idx = -1
                        self.no_hit_count = 0
            elif kind == 'Edge':
                self.selected_edge_index = idx
                self.selected_landmark_idx = -1
            else:
                self.selected_landmark_idx = -1
                self.selected_edge_index = -1

            if self.wireframe_from_idx > -1:
                near, ray_direction = self.unproject_mouse(self.curr_x, self.curr_y)
                self.temp_edge[1] = near

        if event.buttons() == Qt.LeftButton and self.view_mode == ROTATE_MODE:
            self.is_dragging = True
            self.temp_rotate_x = self.curr_x - self.down_x
            self.temp_rotate_y = self.curr_y - self.down_y
            if self.parent != None and callable(getattr(self.parent, 'sync_temp_rotation', None)):
                self.parent.sync_temp_rotation(self, self.temp_rotate_x, self.temp_rotate_y)

        elif event.buttons() == Qt.RightButton and self.view_mode == ZOOM_MODE:
            self.is_dragging = True
            self.temp_dolly = ( self.curr_y - self.down_y ) / 100.0
            if self.parent != None and callable(getattr(self.parent, 'sync_temp_zoom', None)):
                self.parent.sync_temp_zoom(self, self.temp_dolly)

        elif event.buttons() == Qt.MiddleButton and self.view_mode == PAN_MODE:
            self.is_dragging = True
            self.temp_pan_x = self.curr_x - self.down_x
            self.temp_pan_y = self.curr_y - self.down_y
            if self.parent != None and callable(getattr(self.parent, 'sync_temp_pan', None)):
                self.parent.sync_temp_pan(self, self.temp_pan_x, self.temp_pan_y)
        elif self.edit_mode == MODE['EDIT_LANDMARK']:
            hit_type, hit_idx = self.hit_test(self.curr_x, self.curr_y)
            if hit_type == 'Landmark':
                self.selected_landmark_idx = hit_idx
                self.no_hit_count = 0
            else:
                self.selected_landmark_idx = -1

            if self.show_model == True:
                on_background = self.hit_background_test(self.curr_x, self.curr_y)
                if on_background == True:
                    self.cursor_on_vertex = -1
                else:
                    closest_element = self.pick_element(self.curr_x, self.curr_y)
                    if closest_element is not None:
                        self.cursor_on_vertex = closest_element
                    else:
                        self.cursor_on_vertex = -1
        elif self.edit_mode == MODE['MOVE_LANDMARK']:
            if self.show_model == True:
                on_background = self.hit_background_test(self.curr_x, self.curr_y)
                if on_background == True:
                    self.cursor_on_vertex = -1
                    self.landmark_list[self.selected_landmark_idx] = self.stored_landmark['coords']
                    self.selected_landmark_idx = -1
                    self.set_mode(MODE['EDIT_LANDMARK'])
                else:
                    closest_element = self.pick_element(self.curr_x, self.curr_y)
                    if closest_element is not None:
                        self.cursor_on_vertex = closest_element
                        if self.selected_landmark_idx >= 0:
                            self.landmark_list[self.selected_landmark_idx] = self.threed_model.original_vertices[closest_element]
                            if self.object_dialog is not None:
                                self.object_dialog.update_landmark(self.selected_landmark_idx, *self.landmark_list[self.selected_landmark_idx])
                                self.update_landmark_list()
                                self.initialize_colors()
                                self.calculate_resize()
                    else:
                        self.cursor_on_vertex = -1

        self.updateGL()

    def wheelEvent(self, event):
        self.dolly -= event.angleDelta().y() / 240.0
        if self.parent != None and callable(getattr(self.parent, 'sync_zoom', None)):
            self.parent.sync_zoom(self, self.dolly)

        self.updateGL()
        event.accept()

    def add_wire(self, wire_start_index, wire_end_index):
        if wire_start_index == wire_end_index:
            return
        if wire_start_index > wire_end_index:
            wire_start_index, wire_end_index = wire_end_index, wire_start_index
        dataset = self.object.dataset
        if len(dataset.edge_list) == 0 and dataset.wireframe is not None and dataset.wireframe != "":
            dataset.unpack_wireframe()
        for wire in dataset.edge_list:
            if wire[0] == wire_start_index and wire[1] == wire_end_index:
                return
        dataset.edge_list.append([wire_start_index+1, wire_end_index+1])
        dataset.pack_wireframe()
        self.edge_list = dataset.edge_list
        dataset.save()
        self.initialize_colors()        

    def delete_wire(self, selected_edge_index):
        if selected_edge_index >= len(self.edge_list):
            return

        dataset = self.object.dataset
        if len(dataset.edge_list) == 0 and dataset.wireframe is not None and dataset.wireframe != "":
            dataset.unpack_wireframe()
        dataset.edge_list.pop(selected_edge_index)
        self.selected_edge_index = -1
        dataset.pack_wireframe()
        self.edge_list = dataset.edge_list
        dataset.save()
        self.initialize_colors()        

    def set_ds_ops(self, ds_ops):
        self.ds_ops = ds_ops
        self.data_mode = DATASET_MODE
        average_shape = self.ds_ops.get_average_shape()
        scale = self.get_scale_from_object(average_shape)
        average_shape.rescale(scale)
        for obj in self.ds_ops.object_list:
            obj.rescale(scale)
        self.edge_list = ds_ops.edge_list

    def set_shape_preference(self, object_preference):
        self.shape_preference = object_preference
        if self.obj_ops is not None :
            obj = self.obj_ops
            if 'visible' in object_preference:
                obj.visible = object_preference['visible']
            if 'show_landmark' in object_preference:
                obj.show_landmark = object_preference['show_landmark']
            if 'show_wireframe' in object_preference:
                obj.show_wireframe = object_preference['show_wireframe']
            if 'show_polygon' in object_preference:
                obj.show_polygon = object_preference['show_polygon']
            if 'opacity' in object_preference:
                obj.opacity = object_preference['opacity']
            if 'polygon_color' in object_preference:
                obj.polygon_color = object_preference['polygon_color']
            if 'edge_color' in object_preference:
                obj.edge_color = object_preference['edge_color']
            if 'landmark_color' in object_preference:
                obj.landmark_color = object_preference['landmark_color']

    def set_source_shape_preference(self, pref):
        self.source_preference = pref
        if self.ds_ops is not None and len(self.ds_ops.object_list) > 0:
            obj = self.ds_ops.object_list[0]
            obj.visible = pref['visible']
            obj.show_landmark = pref['show_landmark']
            obj.show_wireframe = pref['show_wireframe']
            obj.show_polygon = pref['show_polygon']
            obj.opacity = pref['opacity']
            obj.polygon_color = pref['polygon_color']
            obj.edge_color = pref['edge_color']
            obj.landmark_color = pref['landmark_color']
    
    def set_target_shape_preference(self, pref):
        self.target_preference = pref
        if self.ds_ops is not None and len(self.ds_ops.object_list) > 1:
            obj = self.ds_ops.object_list[1]
            obj.visible = pref['visible']
            obj.show_landmark = pref['show_landmark']
            obj.show_wireframe = pref['show_wireframe']
            obj.show_polygon = pref['show_polygon']
            obj.opacity = pref['opacity']
            obj.polygon_color = pref['polygon_color']
            obj.edge_color = pref['edge_color']
            obj.landmark_color = pref['landmark_color']

    def set_source_shape_color(self, color):
        self.source_shape_color = color

    def set_target_shape_color(self, color):
        self.target_shape_color = color

    def set_source_shape(self, object):
        self.comparison_data['source_shape'] = object
    
    def set_target_shape(self, object):
        self.comparison_data['target_shape'] = object
    
    def set_intermediate_shape(self, object):
        self.comparison_data['intermediate_shape'] = object

    def generate_reference_shape(self):
        shape_list = []
        ds = MdDataset()
        ds.dimension = self.dataset.dimension
        ds.baseline = self.dataset.baseline
        ds.wireframe = self.dataset.wireframe
        ds.edge_list = self.dataset.edge_list
        ds.polygon_list = self.dataset.polygon_list
        ds_ops = MdDatasetOps(ds)

        if 'source_shape' in self.comparison_data:
            shape_list.append(self.comparison_data['source_shape'])
            source = self.comparison_data['source_shape']
            source_ops = MdObjectOps(source)
            ds_ops.object_list.append(source_ops)
        if 'target_shape' in self.comparison_data:
            shape_list.append(self.comparison_data['target_shape'])
            target = self.comparison_data['target_shape']
            target_ops = MdObjectOps(target)
            ds_ops.object_list.append(target_ops)

        ret = ds_ops.procrustes_superimposition()
        if ret == False:
            logger = logging.getLogger(__name__)
            logger.error("procrustes failed")
            return
        self.comparison_data['ds_ops'] = ds_ops
        self.comparison_data['average_shape'] = ds_ops.get_average_shape()
        self.set_ds_ops(ds_ops)
        
        self.data_mode = DATASET_MODE
        if self.source_preference is not None:
            self.set_source_shape_preference(self.source_preference)
        if self.target_preference is not None:
            self.set_target_shape_preference(self.target_preference)

    def set_object(self, object, idx=-1):
        self.show()
        self.landmark_list = copy.deepcopy(object.landmark_list)
        m_app = QApplication.instance()
        if isinstance(object, MdObject):
            self.object = object
            obj_ops = MdObjectOps(object)
        elif object is None:
            self.object = MdObject()
            obj_ops = MdObjectOps(self.object)
        else:
            pass
        self.dataset = object.dataset
        if self.dataset.baseline is not None:
            self.dataset.unpack_baseline()
        self.ds_ops = MdDatasetOps(self.dataset)

        self.obj_ops = obj_ops
        self.data_mode = OBJECT_MODE
        self.pan_x = self.pan_y = 0
        self.rotate_x = self.rotate_y = 0
        self.edge_list = self.dataset.unpack_wireframe()
        self.polygon_list = self.dataset.unpack_polygons()
        if object.threed_model.count() > 0:
            filepath = object.threed_model[0].get_file_path(m_app.storage_directory)
            self.set_threed_model(filepath)
        else:
            self.threed_model = None
        self.calculate_resize()

        if self.dataset.baseline is not None:
            self.align_object()

    def update_object(self, object):
        return
        self.object = object
        self.landmark_list = object.landmark_list
        self.edge_list = object.dataset.edge_list
        self.calculate_resize()
        self.updateGL()

    def align_object(self):
        if self.data_mode == OBJECT_MODE:
            if self.obj_ops is None:
                return
            self.obj_ops.align(self.ds_ops.baseline_point_list)
        elif self.data_mode == DATASET_MODE:
            for obj_ops in self.ds_ops.object_list:
                obj_ops.align(self.ds_ops.baseline_point_list)

    def get_scale_from_object(self, obj_ops):
        if len(obj_ops.landmark_list) == 0:
            return 1.0
        centroid_size = obj_ops.get_centroid_size()
        min_x, max_x = min( [ lm[0] for lm in obj_ops.landmark_list] ), max( [ lm[0] for lm in obj_ops.landmark_list] )
        min_y, max_y = min( [ lm[1] for lm in obj_ops.landmark_list] ), max( [ lm[1] for lm in obj_ops.landmark_list] )
        width = max_x - min_x
        if width == 0:
            width = 1
        height = max_y - min_y
        if height == 0:
            height = 1

        if len(obj_ops.landmark_list[0])>2:
            min_z, max_z = min( [ lm[2] for lm in obj_ops.landmark_list] ), max( [ lm[2] for lm in obj_ops.landmark_list] )
            #obj_ops.rescale(5)
            depth = max_z - min_z
        _3D_SCREEN_WIDTH = 5
        _3D_SCREEN_HEIGHT = 5
        scale = min( _3D_SCREEN_WIDTH / width, _3D_SCREEN_HEIGHT / height )
        #print("scale:", scale)
        return scale*0.5

    def dragEnterEvent(self, event):
        if self.object_dialog is None:
            return
        file_name = event.mimeData().text()
        if file_name.split('.')[-1].lower() in mu.MODEL_EXTENSION_LIST:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self.object_dialog is None:
            return

        file_path = event.mimeData().text()
        file_path = mu.process_dropped_file_name(file_path)
        file_path = mu.process_3d_file(file_path)

        self.set_threed_model(file_path)
        self.calculate_resize()
        if self.object_dialog is not None:
            self.object_dialog.set_object_name(Path(file_path).stem)
            self.object_dialog.enable_landmark_edit()

    def set_threed_model(self, file_path):
        if file_path.split('.')[-1].lower() == 'obj':
            self.threed_model = OBJ(file_path)
            self.fullpath = file_path
        self.updateGL()


    def initializeGL(self):
        self.initialize_frame_buffer()
        self.picker_buffer = self.create_picker_buffer()
        self.initialize_frame_buffer(self.picker_buffer)
        self.initialized = True
        if self.initialized == True and self.threed_model is not None and self.threed_model.generated == False:
            self.threed_model.generate()

    def initialize_frame_buffer(self, frame_buffer_id=0):
        # GLU 쿼드릭 초기화 (GLUT 대신)
        if not hasattr(self, 'glu_quadric'):
            self.glu_quadric = glu.gluNewQuadric()
            glu.gluQuadricNormals(self.glu_quadric, glu.GLU_SMOOTH)  # 조명용 노멀
            logger.debug("GLU quadric initialized for sphere rendering")
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, frame_buffer_id)
        gl.glClearDepth(1.0)
        gl.glDepthFunc(gl.GL_LESS)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_COLOR_MATERIAL)
        gl.glShadeModel(gl.GL_SMOOTH)

        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        
        # Set up lighting parameters
        light_position = [1.0, 1.0, 1.0, 0.0]  # Directional light
        light_ambient = [0.2, 0.2, 0.2, 1.0]   # Ambient light
        light_diffuse = [0.8, 0.8, 0.8, 1.0]   # Diffuse light
        light_specular = [1.0, 1.0, 1.0, 1.0]  # Specular light
        
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, light_position)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, light_ambient)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, light_diffuse)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, light_specular)
        
        # Set material properties for better lighting
        gl.glEnable(gl.GL_COLOR_MATERIAL)
        gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        # Calculate and store aspect ratio with zero-height protection
        h = max(1, self.height())
        w = max(1, self.width())
        self.aspect = w / float(h)  # Update self.aspect for draw_all() usage
        glu.gluPerspective(45.0, self.aspect, 0.1, 100.0) # 시야각, 종횡비, 근거리 클리핑, 원거리 클리핑
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def paintGL(self):
        # Guard against early paint events when widget has no valid size
        if self.width() <= 0 or self.height() <= 0:
            return  # Skip rendering for invalid/hidden widget sizes
            
        if self.edit_mode == MODE['WIREFRAME'] or self.edit_mode == MODE['EDIT_LANDMARK']:
            self.draw_picker_buffer()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # Clear landmark positions for this frame
        if hasattr(self, 'landmark_screen_positions'):
            self.landmark_screen_positions.clear()
        
        gl.glPushMatrix() 
        self.draw_all()
        gl.glPopMatrix()
        return

    def draw_wireframe_cube(self):
        """Draw a simple wireframe cube to replace GLUT cube."""
        gl.glBegin(gl.GL_LINES)
        # Bottom face
        gl.glVertex3f(-0.5, -0.5, -0.5); gl.glVertex3f(0.5, -0.5, -0.5)
        gl.glVertex3f(0.5, -0.5, -0.5); gl.glVertex3f(0.5, -0.5, 0.5)
        gl.glVertex3f(0.5, -0.5, 0.5); gl.glVertex3f(-0.5, -0.5, 0.5)
        gl.glVertex3f(-0.5, -0.5, 0.5); gl.glVertex3f(-0.5, -0.5, -0.5)
        # Top face
        gl.glVertex3f(-0.5, 0.5, -0.5); gl.glVertex3f(0.5, 0.5, -0.5)
        gl.glVertex3f(0.5, 0.5, -0.5); gl.glVertex3f(0.5, 0.5, 0.5)
        gl.glVertex3f(0.5, 0.5, 0.5); gl.glVertex3f(-0.5, 0.5, 0.5)
        gl.glVertex3f(-0.5, 0.5, 0.5); gl.glVertex3f(-0.5, 0.5, -0.5)
        # Vertical edges
        gl.glVertex3f(-0.5, -0.5, -0.5); gl.glVertex3f(-0.5, 0.5, -0.5)
        gl.glVertex3f(0.5, -0.5, -0.5); gl.glVertex3f(0.5, 0.5, -0.5)
        gl.glVertex3f(0.5, -0.5, 0.5); gl.glVertex3f(0.5, 0.5, 0.5)
        gl.glVertex3f(-0.5, -0.5, 0.5); gl.glVertex3f(-0.5, 0.5, 0.5)
        gl.glEnd()

    def draw_simple_cone(self):
        """Draw a simple cone shape to replace GLUT cone."""
        gl.glBegin(gl.GL_TRIANGLES)
        # Simple triangle-based cone
        for i in range(8):
            angle1 = i * 2 * 3.14159 / 8
            angle2 = (i + 1) * 2 * 3.14159 / 8
            x1, y1 = 0.5 * np.cos(angle1), 0.5 * np.sin(angle1)
            x2, y2 = 0.5 * np.cos(angle2), 0.5 * np.sin(angle2)
            # Side face
            gl.glVertex3f(0, 0, 1)    # Tip
            gl.glVertex3f(x1, y1, 0)  # Base edge 1
            gl.glVertex3f(x2, y2, 0)  # Base edge 2
        gl.glEnd()

    def draw_all(self):
        # Safety check for aspect ratio - prevent crashes on early paint events
        aspect = getattr(self, "aspect", None)
        if not aspect or aspect <= 0:
            # Widget hasn't been properly laid out/resized yet - calculate safe fallback
            w = max(1, self.width())
            h = max(1, self.height())
            aspect = w / float(h)
            self.aspect = aspect  # Update for next time
        else:
            aspect = self.aspect
            
        current_buffer = gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45.0, aspect, 0.1, 100.0)
        
        # Ensure lighting is properly set up for each frame
        if current_buffer == 0:  # Only for main render buffer, not picker buffer
            gl.glEnable(gl.GL_LIGHTING)
            gl.glEnable(gl.GL_LIGHT0)
            
            light_position = [1.0, 1.0, 1.0, 0.0]  # Directional light
            light_ambient = [0.2, 0.2, 0.2, 1.0]   # Ambient light
            light_diffuse = [0.8, 0.8, 0.8, 1.0]   # Diffuse light
            
            gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, light_position)
            gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, light_ambient)
            gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, light_diffuse) 
        gl.glTranslatef(0, 0, -5.0 + self.dolly + self.temp_dolly)   # x, y, z 
        gl.glTranslatef((self.pan_x + self.temp_pan_x)/100.0, (self.pan_y + self.temp_pan_y)/-100.0, 0.0)
        gl.glRotatef(self.rotate_y + self.temp_rotate_y, 1.0, 0.0, 0.0)
        gl.glRotatef(self.rotate_x + self.temp_rotate_x, 0.0, 1.0, 0.0)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        bg_color = mu.as_gl_color(self.bgcolor)
        
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)  # Standard alpha blending
        if self.transparent:
            gl.glClearColor(0.0,0.0,0.0, 0.0)
        else:
            gl.glClearColor(*bg_color, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        gl.glEnable(gl.GL_POINT_SMOOTH)
        if self.ds_ops is None and self.obj_ops is None:
            return
        
        # pan, rotate, dolly
        if self.data_mode == OBJECT_MODE:
            if self.obj_ops and hasattr(self.obj_ops, 'landmark_color') and self.obj_ops.landmark_color is not None:
                object_color = mu.as_gl_color(self.obj_ops.landmark_color)
            else:
                object_color = mu.as_gl_color(self.landmark_color) #COLOR['NORMAL_SHAPE']
            self.draw_object(self.obj_ops,color=object_color)
        else:
            self.draw_dataset(self.ds_ops)
        gl.glDisable(gl.GL_BLEND)
        gl.glFlush()

    def draw_dataset(self, ds_ops):
        if self.show_arrow:
            self.draw_arrow(0, 1)

        for idx, obj in enumerate(ds_ops.object_list):
            if obj.visible == False:
                continue
            if obj.id in ds_ops.selected_object_id_list:
                object_color = COLOR['SELECTED_SHAPE']
            else:
                if obj.landmark_color is not None:
                    object_color = mu.as_gl_color(obj.landmark_color)
                else:
                    object_color = mu.as_gl_color(self.landmark_color) #COLOR['NORMAL_SHAPE']
            edge_color=self.wireframe_color
            if obj.edge_color is not None:
                edge_color = obj.edge_color
            polygon_color=self.wireframe_color
            if obj.polygon_color is not None:
                polygon_color = obj.polygon_color

            self.draw_object(obj, landmark_as_sphere=False, color=object_color, edge_color=edge_color,polygon_color=polygon_color)

        if self.show_average:
            object_color = COLOR['AVERAGE_SHAPE']
            self.draw_object(ds_ops.get_average_shape(), landmark_as_sphere=True, color=object_color)


    def draw_arrow(self, start_idx, end_idx):
        if self.data_mode == OBJECT_MODE:
            return
        if self.ds_ops is None:
            return
        if start_idx >= len(self.ds_ops.object_list) or end_idx >= len(self.ds_ops.object_list):
            return
        start_obj = self.ds_ops.object_list[start_idx]
        end_obj = self.ds_ops.object_list[end_idx]
        for i in range(len(start_obj.landmark_list)):
            start_lm = start_obj.landmark_list[i]
            end_lm = end_obj.landmark_list[i]

            direction = [end_lm[0] - start_lm[0], end_lm[1] - start_lm[1], end_lm[2] - start_lm[2]]
            length = math.sqrt(sum(x**2 for x in direction))  # More concise length calculation
            direction = [x/length for x in direction]

            # Rotation axis using cross product
            up_direction = [0, 0, 1]  # Cone should point upwards along Z
            axis = np.cross(direction, up_direction)

            # Calculate angle
            angle = math.degrees(math.acos(np.dot(direction, up_direction))) * -1
            
            # draw rod instead of GL_LINES
            arrow_color = mu.as_gl_color(self.arrow_color)
            gl.glColor3f(*arrow_color)
            gl.glPushMatrix()
            gl.glTranslatef(*((np.array(start_lm)+np.array(end_lm))/2))
            gl.glTranslatef(*[x*-0.015 for x in direction])
            gl.glRotatef(angle, *axis)
            gl.glScalef(0.005, 0.005, length-0.03)
            # Replace GLUT cube with simple wireframe
            self.draw_wireframe_cube()
            gl.glPopMatrix()

            if True:
                gl.glPushMatrix()
                gl.glTranslatef(*end_lm)
                gl.glTranslatef(*[x*-0.03 for x in direction])
                gl.glRotatef(angle, *axis)
                # Replace GLUT cone with simple triangle
                self.draw_simple_cone()
                gl.glPopMatrix()

    def draw_object(self,object,landmark_as_sphere=True,color=COLOR['NORMAL_SHAPE'],edge_color=COLOR['NORMAL_SHAPE'],polygon_color=COLOR['NORMAL_SHAPE']):
        if object is None:
            return
        current_buffer = gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)

        if self.show_wireframe and len(self.temp_edge) == 2 and object.show_wireframe:
            if object.edge_color:
                wf_color = mu.as_gl_color(object.edge_color)
            else:
                wf_color = mu.as_gl_color(self.wireframe_color)
            gl.glColor3f( *wf_color ) #*COLOR['WIREFRAME'])
            gl.glLineWidth(int(self.wireframe_thickness)+1)
            gl.glBegin(gl.GL_LINE_STRIP)
            for v in self.temp_edge:
                gl.glVertex3f(*v)
            gl.glEnd()

        if self.show_wireframe and len(self.edge_list) > 0 and object.show_wireframe:
            for i, edge in enumerate(self.edge_list):
                if current_buffer == self.picker_buffer and self.object_dialog is not None:
                    gl.glDisable(gl.GL_LIGHTING)
                    key = "edge_"+str(i)
                    color = self.edge_idx_to_color[key]
                    gl.glColor3f( *[ c * 1.0 / 255 for c in color] )
                    line_width = 3*(int(self.wireframe_thickness)+1)
                    gl.glLineWidth(line_width)
                else:
                    if i == self.selected_edge_index:
                        gl.glColor3f( *COLOR['SELECTED_EDGE'] )
                    else:
                        if object.edge_color:
                            wf_color = mu.as_gl_color(object.edge_color)
                        else:
                            wf_color = mu.as_gl_color(self.wireframe_color)
                        gl.glColor3f( *wf_color )
                    line_width = 1*(int(self.wireframe_thickness)+1)
                    gl.glLineWidth(line_width)                        
                gl.glBegin(gl.GL_LINE_STRIP)
                for lm_idx in edge:
                    if lm_idx <= len(object.landmark_list):
                        lm = object.landmark_list[lm_idx-1]
                        gl.glVertex3f(*lm)
                gl.glEnd()
                if current_buffer == self.picker_buffer and self.object_dialog is not None:
                    gl.glEnable(gl.GL_LIGHTING)


        if self.show_polygon and len(self.polygon_list) > 0 and object.show_polygon:
            normal_list = self.calculate_normal_list(object,self.polygon_list)
            for i, polygon in enumerate(self.polygon_list):
                normal = self.calculate_normal(object,polygon)
                gl.glEnable(gl.GL_LIGHTING)
                if object.polygon_color:
                    pg_color = mu.as_gl_color(object.polygon_color)
                elif isinstance(polygon_color,QColor):
                    pg_color = mu.as_gl_color(polygon_color)
                elif len(polygon_color) == 3:
                    pg_color = polygon_color
                else:
                    pg_color = mu.as_gl_color(polygon_color)
                gl.glColor4f( *pg_color, object.opacity )
                gl.glNormal3f(*normal)
                gl.glBegin(gl.GL_POLYGON)
                for lm_idx in polygon:
                    if lm_idx <= len(object.landmark_list):
                        lm = object.landmark_list[lm_idx-1]
                        gl.glVertex3f(*lm)
                gl.glEnd()

        if landmark_as_sphere and object.show_landmark:
            lm_count = len(object.landmark_list)
            for i, lm in enumerate(object.landmark_list):
                gl.glPushMatrix()
                gl.glTranslate(*lm)
                gl.glColor3f( *color )
                if i in [ self.selected_landmark_idx, self.wireframe_from_idx, self.wireframe_to_idx ]:
                    gl.glColor3f( *COLOR['SELECTED_LANDMARK'] )

                if current_buffer == self.picker_buffer and self.object_dialog is not None:
                    gl.glDisable(gl.GL_LIGHTING)
                    key = "lm_"+str(i)
                    color = self.lm_idx_to_color[key]
                    gl.glColor3f( *[ c * 1.0 / 255 for c in color] )
                # Use GLU sphere (stable, fast, lighting-compatible)
                radius = 0.02 * ( int(self.landmark_size) + 1 )
                try:
                    if hasattr(self, 'glu_quadric'):
                        glu.gluSphere(self.glu_quadric, radius, 12, 12)
                    else:
                        logger.warning("GLU quadric not initialized, using point fallback")
                        raise Exception("GLU quadric not available")
                except Exception as e:
                    logger.debug(f"GLU sphere rendering failed: {e}")
                    # Fallback: draw a simple point
                    gl.glPointSize(float(self.landmark_size) * 3 + 3)
                    gl.glBegin(gl.GL_POINTS)
                    gl.glVertex3f(0, 0, 0)
                    gl.glEnd()
                if current_buffer == self.picker_buffer and self.object_dialog is not None:
                    gl.glEnable(gl.GL_LIGHTING)
                gl.glPopMatrix()

                if self.show_index:
                    # TODO: Add landmark index display (text or other visual indicator)
                    pass

        elif object.show_landmark:
            
            gl.glPointSize(5)
            gl.glDisable(gl.GL_LIGHTING)
            gl.glColor3f( *color )
            gl.glBegin(gl.GL_POINTS)
            #gl.glColor3f( 1.0, 1.0, 0.0 )
            for lm in object.landmark_list:
                gl.glVertex3f(lm[0], lm[1], lm[2])
            gl.glEnd()
            gl.glEnable(gl.GL_LIGHTING)

        if self.threed_model is not None and self.show_model is True:
            self.threed_model.render()

            if self.cursor_on_vertex > -1:
                lm = self.threed_model.vertices[self.cursor_on_vertex]
                gl.glPushMatrix()
                gl.glTranslate(*lm)
                gl.glColor3f( *COLOR['SELECTED_LANDMARK'] )
                # Use GLU sphere instead of GLUT
                if hasattr(self, 'glu_quadric'):
                    glu.gluSphere(self.glu_quadric, 0.03, 10, 10)
                else:
                    # Fallback: draw a point
                    gl.glPointSize(8)
                    gl.glBegin(gl.GL_POINTS)
                    gl.glVertex3f(0, 0, 0)
                    gl.glEnd()
                gl.glPopMatrix()
            return

    def calculate_normal(self, obj_ops, polygon):
        p1 = obj_ops.landmark_list[polygon[0]-1]
        p2 = obj_ops.landmark_list[polygon[1]-1]
        p3 = obj_ops.landmark_list[polygon[2]-1]
        v1 = np.array(p2) - np.array(p1)
        v2 = np.array(p3) - np.array(p1)
        normal = -1.0 * np.cross(v1, v2)
        normal = normal / np.linalg.norm(normal)
        return normal

    def calculate_face_normals(self, polygon_list):
        face_normals = []
        for polygon in polygon_list:
            # Calculate the average normal of the polygon's vertices
            face_normal = [0.0, 0.0, 0.0]
            for lm_idx in polygon:
                face_normal[0] += self.normal_list[lm_idx - 1][0]
                face_normal[1] += self.normal_list[lm_idx - 1][1]
                face_normal[2] += self.normal_list[lm_idx - 1][2]
                # Normalize the face normal
                length = math.sqrt(face_normal[0] * face_normal[0] + face_normal[1] * face_normal[1] + face_normal[2] * face_normal[2])
                face_normals.append([f / length for f in face_normal])
        return face_normals

    def calculate_normal_list(self, obj_ops, polygon_list):
        normal_dict = {}
        for polygon in polygon_list:
            lm_idx_list = [i-1 for i in polygon]
            landmark_list = [obj_ops.landmark_list[i] for i in lm_idx_list]
            v1 = np.array(landmark_list[1]) - np.array(landmark_list[0])
            v2 = np.array(landmark_list[2]) - np.array(landmark_list[0])
            normal = -1.0 * np.cross(v1, v2)
            for i in lm_idx_list:
                if i in normal_dict:
                    normal_dict[i]['normal'] += normal
                    normal_dict[i]['count'] += 1
                else:
                    normal_dict[i] = { 'normal': normal, 'count': 1 }
        normal_list = []
        for i in range(len(obj_ops.landmark_list)):
            if i in normal_dict:
                normal = normal_dict[i]['normal'] / normal_dict[i]['count']
            else:
                normal = np.array([0,0,0])
            normal_list.append(normal)
        return normal_list

    def create_picker_buffer(self):
        picker_buffer = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, picker_buffer)

        # Create a texture to hold the color buffer
        self.texture_buffer = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_buffer)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.width(), self.height(), 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        # Attach the texture to the framebuffer
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.texture_buffer, 0)

        # Create a renderbuffer for the depth buffer
        self.render_buffer = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.render_buffer)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, self.width(), self.height())

        # Attach the renderbuffer to the framebuffer
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.render_buffer)

        # Check that the framebuffer is complete
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            raise Exception("Failed to create framebuffer")
        return picker_buffer

    def draw_picker_buffer(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.picker_buffer)
        gl.glViewport(0, 0, self.width(), self.height())
        # Render your scene...
        self.draw_all()

        # Don't forget to unbind the framebuffer when you're done to revert back to the default framebuffer
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def delete_picker_buffer(self):
        gl.glDeleteTextures([self.texture_buffer])
        gl.glDeleteRenderbuffers([self.render_buffer])
        gl.glDeleteFramebuffers([self.picker_buffer])
        self.picker_buffer = None

    def resizeGL(self, width, height):
        # Protect against zero height to prevent division by zero
        height = max(1, height)
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        self.aspect = width / float(height)
        glu.gluPerspective(45.0, self.aspect, 0.1, 100.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

        if self.picker_buffer is not None and self.edit_mode == WIREFRAME_MODE:
            # Resize the renderbuffer
            gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.render_buffer)
            gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, width, height)
            
            # Don't forget to update the size of your texture if you have one attached to the FBO
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_buffer)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
            
            # Unbind the renderbuffer
            gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)            

            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.picker_buffer)
            gl.glViewport(0, 0, width, height)
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            aspect = width / float(height)
            glu.gluPerspective(45.0, aspect, 0.1, 100.0)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def closeEvent(self, event):
        pass

    def timeout(self):
        if self.auto_rotate == False:
            return
        if self.is_dragging:
            return
        self.rotate_x += 0.5
        self.updateGL()

    def clear_object(self):
        self.obj_ops = None
        self.object = None
        self.landmark_list = []
        self.updateGL()

    def hit_background_test(self, x, y):
        pixels = gl.glReadPixels(x, self.height()-y, 1, 1, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        r, g, b = struct.unpack('BBB', pixels)
        rgb_list = [r, g, b]
        bg_color = [int(255* c) for c in COLOR['BACKGROUND']]
        if bg_color == rgb_list:
            return True
        else:
            return False

    def hit_test(self, x, y):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.picker_buffer)
        pixels = gl.glReadPixels(x, self.height()-y, 1, 1, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        r, g, b = struct.unpack('BBB', pixels)
        rgb_tuple = (r, g, b)

        if rgb_tuple in self.color_to_lm_idx.keys():
            lm_idx = self.color_to_lm_idx[rgb_tuple]
            return "Landmark", int(lm_idx)
        elif rgb_tuple in self.color_to_edge_idx.keys():
            edge_idx = self.color_to_edge_idx[rgb_tuple]
            return "Edge", int(edge_idx)
        return "", -1

    def initialize_colors(self):
        self.color_to_lm_idx = {}
        self.lm_idx_to_color = {}
        for i in range(len(self.landmark_list)):
            while True:
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                if color not in self.color_to_lm_idx.keys():
                    break
            self.color_to_lm_idx[color] = str(i)
            self.lm_idx_to_color["lm_"+str(i)] = color

        self.color_to_edge_idx = {}
        self.edge_idx_to_color = {}
        for i in range(len(self.edge_list)):
            while True:
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                if color not in self.color_to_lm_idx.keys() and color not in self.color_to_edge_idx.keys():
                    break
            self.color_to_edge_idx[color] = str(i)
            self.edge_idx_to_color["edge_"+str(i)] = color

    def update_landmark_list(self):
        self.obj_ops.landmark_list = copy.deepcopy(self.landmark_list)
        return

    def calculate_resize(self):
        if self.threed_model is not None:
            if self.initialized == True and self.threed_model.generated == False:
                self.threed_model.generate()
            self.obj_ops.move(-1 * self.threed_model.center_x, -1 * self.threed_model.center_y, -1 * self.threed_model.center_z)
            self.obj_ops.rescale(self.threed_model.scale)
            self.obj_ops.apply_rotation_matrix(self.threed_model.rotation_matrix)
        else:
            self.obj_ops.landmark_list = copy.deepcopy(self.landmark_list)
            self.obj_ops.move_to_center()
            centroid_size = self.obj_ops.get_centroid_size()
            self.obj_ops.rescale_to_unitsize()
            scale = self.get_scale_from_object(self.obj_ops)
            self.obj_ops.rescale(scale)
        return

    def unproject_mouse(self, x, y):
        modelview = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
        projection = gl.glGetDoublev(gl.GL_PROJECTION_MATRIX)
        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        near = glu.gluUnProject(x, viewport[3] - y, 0.0, modelview, projection, viewport)
        far = glu.gluUnProject(x, viewport[3] - y, 1.0, modelview, projection, viewport)
        ray_direction = np.array(far) - np.array(near)
        ray_direction /= np.linalg.norm(ray_direction)
        return near, ray_direction

    def pick_element(self, x, y):
        near, ray_direction = self.unproject_mouse(x, y)
        closest_distance = float('inf')
        closest_element = None
        vert_is_closest = False
        faces = self.threed_model.faces
        vertices = self.threed_model.vertices

        for i, vertex in enumerate(vertices):
            distance = self.distance_to_ray(near, ray_direction, np.array(vertex))

            pick_radius = 0.1
            if distance is not None and distance < closest_distance and distance < pick_radius:
                closest_distance = distance
                closest_element = i
                vert_is_closest = True
        return closest_element

    def ray_triangle_intersection(self, ray_origin, ray_direction, v0, v1, v2):
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        normal /= np.linalg.norm(normal)

        epsilon = 1e-6
        if abs(np.dot(ray_direction, normal)) < epsilon:
            return None, None  # No intersection
        d = np.dot(v0 - ray_origin, normal) / np.dot(ray_direction, normal)
        if d < 0:
            return None, None  # No intersection

        intersection_point = ray_origin + d * ray_direction
        edge0 = v0 - v2
        C0 = intersection_point - v0
        C1 = intersection_point - v1
        C2 = intersection_point - v2
        dot00 = np.dot(edge0, edge0)
        dot01 = np.dot(edge0, edge1)
        dot02 = np.dot(edge0, edge2)
        dot11 = np.dot(edge1, edge1)
        dot12 = np.dot(edge1, edge2)
        inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01)
        u = (dot11 * np.dot(C0, edge0) - dot01 * np.dot(C0, edge1)) * inv_denom
        v = (dot00 * np.dot(C1, edge1) - dot01 * np.dot(C1, edge0)) * inv_denom

        if (u >= 0) and (v >= 0) and (u + v <= 1):
            return intersection_point, d
        else:
            return None, None  # No intersection

    def distance_to_ray(self, ray_origin, ray_direction, point):
        point_vector = point - ray_origin
        projection = np.dot(point_vector, ray_direction)
        if projection < 0:
            return None

        distance = np.linalg.norm(point_vector - projection * ray_direction)
        return distance

    def apply_rotation(self, rotation_matrix):
        if self.data_mode == OBJECT_MODE:
            self.obj_ops.apply_rotation_matrix(rotation_matrix)
        elif self.data_mode == DATASET_MODE:
            self.ds_ops.apply_rotation_matrix(rotation_matrix)

    def rotate(self, rotationX_rad, rotationY_rad, vertices ):
        rotationXMatrix = np.array([
            [1, 0, 0, 0],
            [0, np.cos(rotationY_rad), -np.sin(rotationY_rad), 0],
            [0, np.sin(rotationY_rad), np.cos(rotationY_rad), 0],
            [0, 0, 0, 1]
        ])

        rotationYMatrix = np.array([
            [np.cos(rotationX_rad), 0, np.sin(rotationX_rad), 0],
            [0, 1, 0, 0],
            [-np.sin(rotationX_rad), 0, np.cos(rotationX_rad), 0],
            [0, 0, 0, 1]
        ])

        new_rotation_matrix = np.dot(rotationXMatrix, rotationYMatrix)
        self.rotation_matrix = np.dot(new_rotation_matrix, self.rotation_matrix)
        ones_column = np.ones((np.array(vertices).shape[0], 1))
        vertices_with_ones = np.hstack(( vertices, ones_column))
        new_vertices_with_ones = np.dot(vertices_with_ones, self.rotation_matrix.T)
        new_vertices = new_vertices_with_ones[:, 0:3]

        return new_vertices

    def reset_pose(self):
        self.temp_rotate_x = 0
        self.temp_rotate_y = 0
        self.rotate_x = 0
        self.rotate_y = 0
        self.pan_x = 0
        self.pan_y = 0
        self.dolly = 0
        self.temp_dolly = 0
        self.align_object()

    def sync_rotation(self):
        self.rotate_x += self.temp_rotate_x
        self.rotate_y += self.temp_rotate_y
        self.temp_rotate_x = 0
        self.temp_rotate_y = 0

        if self.data_mode == OBJECT_MODE:
            if self.obj_ops is None:
                return

            self.obj_ops.rotate_3d(math.radians(-1*self.rotate_x),'Y')
            self.obj_ops.rotate_3d(math.radians(self.rotate_y),'X')
            if self.threed_model is not None:
                if self.show_model == True:
                    apply_rotation_to_vertex = True
                else:
                    apply_rotation_to_vertex = False
                self.threed_model.rotate(math.radians(self.rotate_x),math.radians(self.rotate_y),apply_rotation_to_vertex)
                if self.show_model == True:
                    self.threed_model.generate()

        elif self.data_mode == DATASET_MODE:
            if self.ds_ops is None:
                return
            for obj in self.ds_ops.object_list:
                obj.rotate_3d(math.radians(-1*self.rotate_x),'Y')
                obj.rotate_3d(math.radians(self.rotate_y),'X')

        self.rotate_x = 0
        self.rotate_y = 0        


class ShapePreference(QWidget):
    shape_preference_changed = pyqtSignal(dict)
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.visible = True
        self.show_landmark = True
        self.show_wireframe = True
        self.show_polygon = True
        self.transparency = 0
        self.opacity = 1 - self.transparency
        self.ignore_change = False
        self.index = -1
        self.edge_color = "red"
        self.landmark_color = "red"
        self.polygon_color = "red"
        self.name = ""

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.lblTitle = QLabel("Name")
        self.edtTitle = QLineEdit()
        self.cbxShow = QCheckBox("Show")
        self.cbxShow.setChecked(self.visible)
        self.cbxShowLandmark = QCheckBox("")
        self.cbxShowLandmark.setChecked(self.show_landmark)
        self.cbxShowWireframe = QCheckBox("")
        self.cbxShowWireframe.setChecked(self.show_wireframe)
        self.cbxShowPolygon = QCheckBox("")
        self.cbxShowPolygon.setChecked(self.show_polygon)
        self.sliderTransparency = QSlider(Qt.Horizontal)
        self.sliderTransparency.setMinimum(0)
        self.sliderTransparency.setMaximum(100)
        self.sliderTransparency.setValue(0)

        self.btnLMColor = QPushButton("LM")
        self.btnLMColor.setMinimumSize(20,20)
        self.btnLMColor.setStyleSheet("background-color: red")
        self.btnLMColor.setToolTip("red")
        self.btnLMColor.setCursor(Qt.PointingHandCursor)
        #self.btnLMColor.mousePressEvent = lambda event, type='LM': self.on_btnColor_clicked(event, 'LM')
        self.btnLMColor.clicked.connect(self.on_btnLMColor_clicked)

        self.btnEdgeColor = QPushButton("Edge")
        self.btnEdgeColor.setMinimumSize(20,20)
        self.btnEdgeColor.setStyleSheet("background-color: red")
        self.btnEdgeColor.setToolTip("red")
        self.btnEdgeColor.setCursor(Qt.PointingHandCursor)
        self.btnEdgeColor.clicked.connect(self.on_btnEdgeColor_clicked)

        self.btnFaceColor = QPushButton("Face")
        self.btnFaceColor.setMinimumSize(20,20)
        self.btnFaceColor.setStyleSheet("background-color: red")
        self.btnFaceColor.setToolTip("red")
        self.btnFaceColor.setCursor(Qt.PointingHandCursor)
        self.btnFaceColor.clicked.connect(self.on_btnFaceColor_clicked)        

        self.layout.addWidget(self.lblTitle)
        self.layout.addWidget(self.edtTitle)
        self.layout.addWidget(self.cbxShow)
        self.layout.addWidget(self.cbxShowLandmark)
        self.layout.addWidget(self.btnLMColor)
        self.layout.addWidget(self.cbxShowWireframe)
        self.layout.addWidget(self.btnEdgeColor)
        self.layout.addWidget(self.cbxShowPolygon)
        self.layout.addWidget(self.btnFaceColor)
        self.layout.addWidget(self.sliderTransparency)

        self.cbxShow.stateChanged.connect(self.cbxShow_stateChanged)
        self.cbxShowLandmark.stateChanged.connect(self.cbxShowLandmark_stateChanged)
        self.cbxShowWireframe.stateChanged.connect(self.cbxShowWireframe_stateChanged)
        self.cbxShowPolygon.stateChanged.connect(self.cbxShowPolygon_stateChanged)
        self.edtTitle.textChanged.connect(self.edtTitle_textChanged)
        self.sliderTransparency.valueChanged.connect(self.sliderTransparency_valueChanged)

    def hide_title(self):
        self.lblTitle.hide()

    def hide_name(self):
        self.edtTitle.hide()
    
    def hide_cbxShow(self):
        self.cbxShow.hide()

    def on_btnLMColor_clicked(self,event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.btnLMColor.toolTip()))
        if color is not None:
            self.btnLMColor.setStyleSheet("background-color: " + color.name())
            self.btnLMColor.setToolTip(color.name())
            self.landmark_color = color.name()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def on_btnEdgeColor_clicked(self,event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.btnEdgeColor.toolTip()))
        if color is not None:
            self.btnEdgeColor.setStyleSheet("background-color: " + color.name())
            self.btnEdgeColor.setToolTip(color.name())
            self.edge_color = color.name()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def on_btnFaceColor_clicked(self,event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.btnFaceColor.toolTip()))
        if color is not None:
            self.btnFaceColor.setStyleSheet("background-color: " + color.name())
            self.btnFaceColor.setToolTip(color.name())
            self.polygon_color = color.name()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def edtTitle_textChanged(self, text):
        self.name = text
        if self.ignore_change is False:
            self.emit_changed_signal()

    def emit_changed_signal(self):
        pref = {'name': self.name, 'index': self.index, 'visible': self.visible, 
                'show_landmark': self.show_landmark, 'show_wireframe': self.show_wireframe, 'show_polygon': self.show_polygon, 'opacity': self.opacity,
                'landmark_color': self.landmark_color, 'edge_color': self.edge_color, 'polygon_color': self.polygon_color}
        self.shape_preference_changed.emit(pref)

    def get_preference(self):
        pref = {'name': self.name, 'index': self.index, 'visible': self.visible,
                'show_landmark': self.show_landmark, 'show_wireframe': self.show_wireframe, 'show_polygon': self.show_polygon, 'opacity': self.opacity,
                'landmark_color': self.landmark_color, 'edge_color': self.edge_color, 'polygon_color': self.polygon_color}
        return pref

    def set_color(self, color):
        self.btnLMColor.setStyleSheet("background-color: " + color)
        self.landmark_color = color
        self.btnEdgeColor.setStyleSheet("background-color: " + color)
        self.edge_color = color
        self.btnFaceColor.setStyleSheet("background-color: " + color)
        self.polygon_color = color

    def set_opacity(self, opacity):
        self.opacity = opacity
        self.transparency = 1 - opacity
        self.sliderTransparency.setValue(int(self.transparency * 100))

    def set_title(self, title):
        self.lblTitle.setText(title)        

    def set_name(self, name):
        self.name = name
        self.ignore_change = True
        self.edtTitle.setText(name)
        self.ignore_change = False

    def set_index(self, index):
        self.index = index

    def btnColor_clicked(self):
        pass

    def cbxShow_stateChanged(self, int):
        self.visible = self.cbxShow.isChecked()
        if self.ignore_change is False:
            self.emit_changed_signal()
    
    def cbxShowLandmark_stateChanged(self, int):
        self.show_landmark = self.cbxShowLandmark.isChecked()
        if self.ignore_change is False:
            self.emit_changed_signal()
    
    def cbxShowWireframe_stateChanged(self, int):
        self.show_wireframe = self.cbxShowWireframe.isChecked()
        if self.ignore_change is False:
            self.emit_changed_signal()
    
    def cbxShowPolygon_stateChanged(self, int):
        self.show_polygon = self.cbxShowPolygon.isChecked()
        if self.ignore_change is False:
            self.emit_changed_signal()
    
    def sliderTransparency_valueChanged(self, int):
        self.transparency = self.sliderTransparency.value() / 100.0
        self.opacity = 1 - self.transparency
        if self.ignore_change is False:
            self.emit_changed_signal()

class X1Y1:
    def __init__(self, filename, datasetname, invertY = False):
        #
        self.dirname = os.path.dirname(filename) 
        self.filename = filename
        self.datasetname = datasetname
        self.dimension = 0
        self.nobjects = 0
        self.object_name_list = []
        self.landmark_str_list = []
        self.edge_list = []
        self.polygon_list = []
        self.variablename_list = []
        self.property_list_list = []
        self.object_comment = {}
        self.landmark_data = {}
        self.object_images = {}
        self.invertY = invertY
        self.read()

    def isNumber(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def read(self):
        with open(self.filename, 'r') as f:
            lines = f.readlines()
            dataset = {}
            object_count = 0
            landmark_count = 0
            data = []
            object_name_list = []
            threed = 0
            twod = 0
            objects = {}
            object_comment = {}
            object_images = {}
            header = ''
            comment = ''
            image_count = 0
            currently_in_data_section = False
            object_id = ''
            object_image_path = ''
            object_comment_1 = ''
            object_comment_2 = ''
            y_flip = 1.0
            if self.invertY:
                y_flip = -1.0

            header = lines[0].strip().split("\t")
            xyz_header_list = header[1:]
            if xyz_header_list[2].lower()[0] == "x":
                self.dimension = 2
            else:
                self.dimension = 3
            lendmark_count = int(len(xyz_header_list) / self.dimension)
            lines = lines[1:]
            
            for line in lines:
                line = line.strip()
                if line == '':
                    continue
                if line.startswith("#"):
                    continue
                if line.startswith('"') or line.startswith("'"):
                    continue

                data = []
                fields_list = line.split("\t")
                object_name = fields_list[0]
                object_name_list.append(object_name)
                landmark_list = fields_list[1:]
                if len(landmark_list) > 0:
                    if self.dimension == 2:
                        for idx in range(0, len(landmark_list), 2):
                            data.append([float(landmark_list[idx]), y_flip * float(landmark_list[idx+1])])
                    elif self.dimension == 3:
                        for idx in range(0, len(landmark_list), 3):
                            data.append([float(landmark_list[idx]), float(landmark_list[idx+1]), float(landmark_list[idx+2])])
                objects[object_name] = data
            self.nobjects = len(object_name_list)
            self.nlandmarks = landmark_count
            self.landmark_data = objects
            self.object_name_list = object_name_list
            return dataset

class TPS:
    def __init__(self, filename, datasetname, invertY = False):
        #
        self.dirname = os.path.dirname(filename) 
        self.filename = filename
        self.datasetname = datasetname
        self.dimension = 0
        self.nobjects = 0
        self.object_name_list = []
        self.landmark_str_list = []
        self.edge_list = []
        self.polygon_list = []
        self.variablename_list = []
        self.property_list_list = []
        self.object_comment = {}
        self.landmark_data = {}
        self.invertY = invertY
        self.read()

    def isNumber(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def read(self):
        with open(self.filename, 'r') as f:
            tps_lines = f.readlines()
            dataset = {}
            object_count = 0
            landmark_count = 0
            data = []
            object_name_list = []
            threed = 0
            twod = 0
            objects = {}
            object_comment = {}
            object_images = {}
            header = ''
            comment = ''
            image_count = 0
            currently_in_data_section = False
            object_id = ''
            object_image_path = ''
            object_comment_1 = ''
            object_comment_2 = ''
            
            for line in tps_lines:
                line = line.strip()
                if line == '':
                    continue
                if line.startswith("#"):
                    continue
                if line.startswith('"') or line.startswith("'"):
                    continue
                headerline = re.search(r'^\s*LM\s*=\s*(\d+)\s*(.*)', line, re.IGNORECASE)

                if headerline is not None:
                    if currently_in_data_section == True:
                        if len(data) > 0:
                            if object_id != '':
                                key = object_id
                            elif object_comment_1 != '':
                                key = object_comment_1
                                object_comment_1 = ''
                            else:
                                key = self.datasetname + "_" + str(object_count+1)
                            objects[key] = data
                            object_name_list.append(key)
                            object_comment[key] = " ".join( [ object_comment_1, object_comment_2 ] ).strip()
                            if object_image_path != '':
                                object_images[key] = object_image_path
                            #print("data:", data)
                            data = []
                            object_id = ''
                            object_comment_1 = ''
                            object_comment_2 = ''
                            object_image_path = ''
                        landmark_count, object_comment_1 = int(headerline.group(1)), headerline.group(2).strip()
                        object_count += 1
                    else:
                        currently_in_data_section = True
                        landmark_count, object_comment_1 = int(headerline.group(1)), headerline.group(2).strip()
                else:
                    dataline = re.search(r'^\s*(\w+)\s*=(.+)', line)
                    if dataline is None:
                        point = [ float(x) for x in re.split(r'\s+', line)]
                        if len(point) > 2 and self.isNumber(point[2]):
                            threed += 1
                        else:
                            twod += 1
                        if len(point)>1:
                            data.append(point)
                    elif dataline.group(1).lower() == "image":
                        object_image_path = dataline.group(2)
                    elif dataline.group(1).lower() == "comment":
                        object_comment_2 = dataline.group(2)
                    elif dataline.group(1).lower() == "id":
                        object_id = dataline.group(2)
                        pass

            if len(data) > 0:
                if object_id != '':
                    key = object_id
                elif object_comment_1 != '':
                    key = object_comment_1
                    object_comment_1 = ''
                else:
                    key = self.datasetname + "_" + str(object_count+1)
                objects[key] = data
                object_name_list.append(key)
                object_comment[key] = " ".join( [ object_comment_1, object_comment_2 ] ).strip()
                if object_image_path != '':
                    object_images[key] = object_image_path

            if object_count == 0 and landmark_count == 0:
                return None

            if threed > twod:
                self.dimension = 3
            else:
                self.dimension = 2
            
            if self.dimension == 2 and self.invertY:
                for key in objects.keys():
                    for idx in range(len(objects[key])):
                        objects[key][idx][1] = -1 * objects[key][idx][1]
            
            self.nobjects = len(object_name_list)
            self.nlandmarks = landmark_count
            self.landmark_data = objects
            self.object_name_list = object_name_list
            self.object_comment = object_comment
            self.object_images = object_images
            return dataset

class NTS:
    def __init__(self, filename, datasetname, invertY = False):
        self.filename = filename
        self.datasetname = datasetname
        self.dimension = 0
        self.nobjects = 0
        self.object_name_list = []
        self.landmark_str_list = []
        self.edge_list = []
        self.polygon_list = []
        self.variablename_list = []
        self.property_list_list = []
        self.object_comment = {}
        self.landmark_data = {}
        self.object_images = {}
        self.invertY = invertY
        self.read()

    def isNumber(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def read(self):
        with open(self.filename, 'r') as f:
            nts_lines = f.readlines()

            dataset = {}

            total_object_count = 0
            landmark_count = 0
            data = []
            object_name_list = []
            threed = 0
            twod = 0
            objects = {}
            header = ''
            comment = ''
            image_count = 0
            matrix_type = -1
            total_object_count = -1
            variable_count = -1
            dimension = -1
            headerline_processed = False
            column_names_exist = False
            column_names_read = False
            row_names_read = False
            row_names_exist_at_row_beginning = False
            row_names_exist_at_row_ending = False
            row_names_exist_in_separate_line = False

            current_object_count = 0
            comments = ""

            for line in nts_lines:
                line = line.strip()
                if line == '':
                    continue
                if line.startswith('"') or line.startswith("'"):
                    comments += line
                    continue
                #                          1    2     3   4    5     6    7   8    9    10   11   12   13    14
                headerline = re.search(r'^(\d+)(\s+)(\d+)(\w*)(\s+)(\d+)(\w*)(\s+)(\d+)(\s+)(\d*)(\s*)(\w+)=(\d+)(.*)', line)
                if headerline is not None:
                    matrix_type = headerline.group(1)
                    total_object_count = int(headerline.group(3))
                    variable_count = int(headerline.group(6))
                    self.dimension = int(headerline.group(14))
                    if variable_count > 0 and dimension > 0:
                        landmark_count = int( float(variable_count) / float(dimension) )
                    if headerline.group(4).lower() == "l":
                        row_names_exist_in_separate_line = True
                    elif headerline.group(4).lower() == "b":
                        row_names_exist_at_row_beginning = True
                    elif headerline.group(4).lower() == "e":
                        row_names_exist_at_row_ending = True
                    if headerline.group(7).lower() == "l":
                        column_names_exist = True
                    if headerline.group(13).lower() == "dim":
                        self.dimension = int(headerline.group(14))
                    headerline_processed = True
                    continue

                if headerline_processed == True and row_names_exist_in_separate_line == True and row_names_read == False:
                    row_names_list = re.split(r'\s+', line)
                    row_names_read = True
                    continue

                if headerline_processed == True and column_names_exist == True and column_names_read == False:
                    column_names_list = re.split(r'\s+', line)
                    column_names_read = True
                    continue

                if headerline_processed == True:
                    data_list = re.split(r'\s+', line)
                    if row_names_exist_at_row_beginning == True:
                        row_name = data_list.pop(0)
                    elif row_names_exist_at_row_ending == True:
                        row_name = data_list.pop(-1)
                    elif len(row_names_list) > 0:
                        row_name = row_names_list[current_object_count]
                    else:
                        row_name = self.datasetname + "_" + str(current_object_count+1)
                    data_list = [ float(x) for x in data_list ]
                    objects[row_name] = []
                    for idx in range(0,len(data_list),self.dimension):
                        objects[row_name].append(data_list[idx:idx+self.dimension])
                    object_name_list.append(row_name)
                    current_object_count += 1

            if total_object_count == 0 and landmark_count == 0:
                return None

            self.nobjects = len(object_name_list)
            self.nlandmarks = landmark_count
            self.landmark_data = objects
            self.object_name_list = object_name_list
            self.description = comments

            if self.dimension == 2 and self.invertY == True:
                for key in objects.keys():
                    for idx in range(len(objects[key])):
                        objects[key][idx][1] = -1 * objects[key][idx][1]

            return dataset

class Morphologika:
    def __init__(self, filename, datasetname, invertY = False):
        self.dirname = os.path.dirname(filename) 
        self.filename = filename
        self.datasetname = datasetname
        self.dimension = 0
        self.nobjects = 0
        self.object_name_list = []
        self.landmark_str_list = []
        self.edge_list = []
        self.polygon_list = []
        self.ppmm_list = []
        self.variablename_list = []
        self.property_list_list = []
        self.object_comment = {}
        self.landmark_data = {}
        self.object_images = {}
        self.invertY = invertY
        self.read()

    def read(self):
        f = open(self.filename, 'r')
        morphologika_data = f.read()
        f.close()

        object_count = -1
        landmark_count = -1
        data_lines = [l.strip() for l in morphologika_data.split('\n')]
        found = False
        dsl = ''
        dimension = 2
        raw_data = {}
        for line in data_lines:
            line = line.strip()
            if line == "":
                continue
            if line[0] == "'":
                '''comment'''
                continue
            elif line[0] == '[':
                dsl = re.search(r'(\w+)', line).group(0).lower()
                raw_data[dsl] = []
                continue
            else:
                raw_data[dsl].append(line)
                if dsl == 'individuals':
                    object_count = int(line)
                if dsl == 'landmarks':
                    landmark_count = int(line)
                if dsl == 'dimensions':
                    dimension = int(line)

        if object_count < 0 or landmark_count < 0:
            return False

        self.raw_data = raw_data
        self.nlandmarks = landmark_count
        self.dimension = dimension
        self.object_name_list = self.raw_data['names']
        self.nobjects = len(self.object_name_list)
        self.nobjects = object_count

        objects = {}
        for i, name in enumerate(self.object_name_list):
            begin = i * self.nlandmarks
            count = self.nlandmarks
            objects[name] = []
            for point in self.raw_data['rawpoints'][begin:begin + count]:
                coords = re.split(r'\s+', point)[:dimension]
                objects[name].append(coords)

        self.landmark_data = objects
        self.edge_list = []
        self.image_list = []
        self.polygon_list = []
        self.variablename_list = []
        self.property_list_list = []

        if self.dimension == 2 and self.invertY == True:
            for key in objects.keys():
                for idx in range(len(objects[key])):
                    objects[key][idx][1] = -1.0 * float(objects[key][idx][1])

        if 'labels' in self.raw_data.keys():
            for line in self.raw_data['labels']:
                labels = re.split(r'\s+', line)
                for label in labels:
                    self.variablename_list.append( label )
                    
        if 'labelvalues' in self.raw_data.keys():
            for line in self.raw_data['labelvalues']:
                property_list = re.split(r'\s+', line)
                self.property_list_list.append(property_list)

        if 'wireframe' in self.raw_data.keys():
            for line in self.raw_data['wireframe']:
                edge = [int(v) for v in re.split(r'\s+', line)]
                edge.sort()
                self.edge_list.append(edge)

        if 'polygons' in self.raw_data.keys():
            for line in self.raw_data['polygons']:
                poly = [int(v) for v in re.split(r'\s+', line)]
                poly.sort()
                self.polygon_list.append(poly)

        if 'images' in self.raw_data.keys():
            for idx, line in enumerate(self.raw_data['images']):
                object_name = self.object_name_list[idx]
                self.object_images[object_name] = line

        if 'pixelspermm' in self.raw_data.keys():
            for idx, line in enumerate(self.raw_data['pixelspermm']):
                self.ppmm_list.append(line)

        self.edge_list.sort()
        self.polygon_list.sort()
        return

class MdSequenceDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() == 1:  # Check if it's the sequence column
            editor = QLineEdit(parent)
            editor.setValidator(QIntValidator())
            return editor
        else:
            return super().createEditor(parent, option, index)

class MdDrag(QDrag):
    #shiftStateChanged = Signal(bool)
    def __init__(self, parent):
        super().__init__(parent)
        logger = logging.getLogger(__name__)
        logger.debug("md drag init")
        self.shift_pressed = False
        self.copy_cursor = QPixmap(QCursor(Qt.DragCopyCursor).pixmap())
        self.move_cursor = QPixmap(QCursor(Qt.DragMoveCursor).pixmap())

    def updateCursor(self, event):
        self.shift_pressed = bool(event.modifiers() & Qt.ShiftModifier)
        if self.shift_pressed:
            self.setDragCursor(self.copy_cursor, Qt.CopyAction)
        else:
            self.setDragCursor(self.move_cursor, Qt.MoveAction)

    def dragEnterEvent(self, event):
        logger = logging.getLogger(__name__)
        logger.debug("md drag dragEnterEvent")
        self.updateCursor(event)
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        logger = logging.getLogger(__name__)
        logger.debug(f"drag move event: {event.pos()}")
        self.updateCursor(event)
        super().dragMoveEvent(event)

class DragEventFilter(QObject):
    def __init__(self, drag_object):
        super().__init__()
        self.drag_object = drag_object

    def eventFilter(self, obj, event):
        if event.type() in [QEvent.KeyPress, QEvent.KeyRelease]:
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.ControlModifier:
                self.drag_object.setDragCursor(self.drag_object.copy_cursor.pixmap(), Qt.CopyAction)
                logger.debug("Set Copy Cursor")
            else:
                self.drag_object.setDragCursor(self.drag_object.move_cursor.pixmap(), Qt.MoveAction)
                logger.debug("Set Move Cursor")
        return False

class CustomDrag(QDrag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.copy_cursor = QCursor(Qt.DragCopyCursor)
        self.move_cursor = QCursor(Qt.DragMoveCursor)

    def exec_(self, supportedActions, defaultAction=Qt.IgnoreAction):
        event_filter = DragEventFilter(self)
        QApplication.instance().installEventFilter(event_filter)
        
        # Set initial cursor
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ControlModifier:
            self.setDragCursor(self.copy_cursor.pixmap(), Qt.CopyAction)
        else:
            self.setDragCursor(self.move_cursor.pixmap(), Qt.MoveAction)
        
        result = super().exec_(supportedActions, defaultAction)
        
        QApplication.instance().removeEventFilter(event_filter)
        return result

class MdTableView(QTableView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.verticalHeader().hide()
        self.sort_later = False
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.copy_action = QAction(self.tr("Copy\tCtrl+C"), self)
        self.copy_action.triggered.connect(self.copy_selected_data)
        copy_shortcut = QShortcut(QKeySequence.Copy, self)
        copy_shortcut.activated.connect(self.copy_action.trigger)  # Connect to the action
        self.paste_action = QAction(self.tr("Paste\tCtrl+V"), self)
        self.paste_action.triggered.connect(self.paste_data)
        paste_shortcut = QShortcut(QKeySequence.Paste, self)
        paste_shortcut.activated.connect(self.paste_action.trigger)
        self.fill_sequence_action = QAction(self.tr("Fill sequence"), self)
        self.fill_sequence_action.triggered.connect(self.fill_sequence)
        logger = logging.getLogger(__name__)
        logger.debug("Fill sequence action created and connected")
        self.fill_action = QAction(self.tr("Fill value"), self) 
        self.fill_action.triggered.connect(self.fill_value)
        self.clear_cells_action = QAction(self.tr("Clear"), self)
        self.clear_cells_action.triggered.connect(self.clear_selected_cells)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.selection_mode = "Cells"
        self.drag_start_position = None
        self.is_dragging = False

    def set_cells_selection_mode(self):
        self.selection_mode = "Cells"
        self.setDragEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)

    def set_rows_selection_mode(self):
        self.selection_mode = "Rows"
        self.setDragEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            index = self.indexAt(event.pos())
            self.was_cell_selected = index in self.selectionModel().selectedIndexes()

            if self.selection_mode == "Rows" and self.was_cell_selected:
                self.startDrag(Qt.CopyAction)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            if event.modifiers() & Qt.ShiftModifier:
                QApplication.setOverrideCursor(Qt.DragCopyCursor)  # Copy cursor
            else:
                QApplication.setOverrideCursor(Qt.ClosedHandCursor)  # Move cursor (or Qt.SizeAllCursor)


        if self.selection_mode != "Rows":
            super().mouseMoveEvent(event)
            return
        
        if not (event.buttons() & Qt.LeftButton):
            return

        if self.selection_mode == "Rows" and not self.was_cell_selected:
            self.drag_start_position = event.pos()
            super().mouseMoveEvent(event)
            return

        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        table_rect = self.viewport().rect()
        if not table_rect.contains(event.pos()):
            logger = logging.getLogger(__name__)
            logger.debug("outside table, start drag")
            self.is_dragging = True
            self.startDrag()
        else:
            super().mouseMoveEvent(event)

    def startDrag(self, supportedActions=Qt.CopyAction):
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            return
        mimeData = self.model().mimeData(indexes)
        if not mimeData:
            return
        drag = CustomDrag(self)
        drag.setMimeData(mimeData)
        
        # Set initial cursor based on current Shift key state
        initial_action = Qt.CopyAction if QApplication.keyboardModifiers() & Qt.ShiftModifier else Qt.MoveAction
        dropAction = drag.exec_(Qt.CopyAction | Qt.MoveAction)
        self.is_dragging = False

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_dragging:
                # Select the row if a drag operation was started
                row = self.rowAt(event.pos().y())
                self.selectionModel().select(self.model().index(row, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)
                self.is_dragging = False
            else:
                super().mouseReleaseEvent(event)

    def show_context_menu(self, pos):
        logger = logging.getLogger(__name__)
        index = self.indexAt(pos)  # Get the index of the clicked cell
        column = index.column()  # Get the column index
        
        # Get column header text
        column_header = ""
        if self.model() and column >= 0:
            column_header = self.model().headerData(column, Qt.Horizontal, Qt.DisplayRole)
            if column_header is None:
                column_header = ""
        
        logger.debug(f"Context menu requested at pos: {pos}, index: {index}, column: {column}, header: '{column_header}'")
        
        selected_indices = self.selectionModel().selectedIndexes()
        logger.debug(f"Selected indices: {len(selected_indices)} items")
        
        # Check if this is a read-only column (name, count, csize)
        readonly_columns = ['name', 'count', 'csize']
        column_header_lower = str(column_header).lower().strip()
        is_readonly_column = column_header_lower in readonly_columns
        
        logger.debug(f"Column '{column_header}' (normalized: '{column_header_lower}') is read-only: {is_readonly_column}")

        menu = QMenu(self)
        menu.addAction(self.copy_action)
        
        # Only add paste and other actions if not a read-only column
        if not is_readonly_column:
            menu.addAction(self.paste_action)

        # For read-only columns, only show copy
        if not is_readonly_column:
            # Only show Fill Sequence if all selected cells are in column 1 (sequence column)
            show_fill_sequence = False
            if selected_indices:
                # Check if all selected cells are in column 1
                selected_columns = set(idx.column() for idx in selected_indices)
                if len(selected_columns) == 1 and 1 in selected_columns:
                    show_fill_sequence = True
                    logger.debug(f"All {len(selected_indices)} selected cells are in sequence column (column 1)")
                else:
                    logger.debug(f"Selected cells span multiple columns {selected_columns} or not in sequence column")
            elif column == 1:
                # No selection, but clicked on sequence column
                show_fill_sequence = True
                logger.debug("Clicked on sequence column, enabling Fill sequence")
            
            if show_fill_sequence:
                menu.addAction(self.fill_sequence_action)
                logger.debug("Added Fill sequence action")
            else:
                logger.debug("Fill sequence not available (only works when sequence column cells are selected)")
                
            menu.addAction(self.fill_action)
            menu.addAction(self.clear_cells_action)
        else:
            logger.debug(f"Read-only column '{column_header}': only showing copy action")
        
        actions_list = ["Copy"]
        if not is_readonly_column:
            actions_list.append("Paste")
            if 'show_fill_sequence' in locals() and show_fill_sequence:
                actions_list.append("Fill sequence")
            actions_list.extend(["Fill value", "Clear"])
        
        logger.debug(f"Context menu showing with actions: {', '.join(actions_list)}")
        logger.info(f"Context menu for column '{column_header}' ({'read-only' if is_readonly_column else 'editable'}): {', '.join(actions_list)}")
        
        menu.exec_(self.mapToGlobal(pos)) 

    def fill_value(self):
        #print("fill value")
        selected_indices = self.selectionModel().selectedIndexes()
        if len(selected_indices) == 0:
            return
        # get the first cell
        first_index = selected_indices[0]
        value = str(self.model().data(first_index, Qt.DisplayRole))
        # get user input
        value, ok = QInputDialog.getText(self, "Fill Values", "Enter value", text=value)
        if not ok:
            return
        # fill the values
        for index in selected_indices:
            self.model().setData(index, value, Qt.EditRole)

    def fill_sequence(self):
        logger = logging.getLogger(__name__)
        logger.info("Fill sequence action triggered")
        
        selected_cells = self.selectionModel().selectedIndexes()
        logger.debug(f"Selected cells: {len(selected_cells)}")
        
        if len(selected_cells) == 0:
            logger.warning("No cells selected for fill sequence")
            return
        selected_cells.sort(key=lambda x: (x.row(), x.column()))
        # make sure all the cells are in the column 1
        # get column number of all the cells
        column_numbers = [cell.column() for cell in selected_cells]
        logger.debug(f"Column numbers: {column_numbers}")
        
        if len(set(column_numbers)) > 1:
            logger.warning("Multiple columns selected, fill sequence only works on single column")
            return
        
        if column_numbers[0] != 1:
            logger.warning(f"Fill sequence only works on column 1 (sequence column), selected column: {column_numbers[0]}")
            return
        
        # get the first cell
        first_cell = selected_cells[0]
        first_row = first_cell.row()
        column_0_index = self.model().index(first_row, 0)
        object_id = self.model().data(column_0_index, Qt.DisplayRole)
        sequence = self.model().data(first_cell, Qt.DisplayRole)
        try:
            sequence = int(sequence)
        except:
            sequence = 1
        # get user input
        logger.debug(f"Showing input dialog for starting sequence, current value: {sequence}")
        sequence, ok = QInputDialog.getInt(self, "Fill Sequence", "Enter starting sequence number", sequence)
        if not ok:
            logger.info("User cancelled starting sequence input")
            return
            
        logger.debug(f"User entered starting sequence: {sequence}")
        # get increment
        increment, ok = QInputDialog.getInt(self, "Fill Sequence", "Enter increment", 1)
        if not ok:
            logger.info("User cancelled increment input")
            return
            
        logger.debug(f"User entered increment: {increment}")
        # fill the sequence
        logger.info(f"Filling sequence for {len(selected_cells)} cells, starting at {sequence} with increment {increment}")
        
        for i, cell in enumerate(selected_cells):
            row = cell.row()
            index = self.model().index(row, 1)
            logger.debug(f"Setting row {row}, column 1 to value {sequence}")
            
            result = self.model().setData(index, sequence, Qt.EditRole)
            if not result:
                logger.error(f"Failed to set data at row {row}, column 1")
            
            sequence += increment
            
        logger.info("Fill sequence completed successfully")

    def paste_data(self):
        current_index = self.currentIndex()
        if not current_index.isValid():
            return
        text = QApplication.clipboard().text()
        rows = text.split("\n")
        for row, row_text in enumerate(rows):
            columns = row_text.split("\t")
            for col, text in enumerate(columns):
                index = self.model().index(current_index.row() + row, current_index.column() + col)
                self.model().setData(index, text, Qt.EditRole)

    def copy_selected_data(self):
        selected_indexes = self.selectionModel().selectedIndexes()
        if selected_indexes:
            all_data = []
            data_row = []
            prev_index = None
            for index in selected_indexes:
                if prev_index is not None and index.row() != prev_index.row():
                    all_data.append("\t".join(data_row))
                    data_row = []
                data_row.append(str(self.model().data(index, Qt.DisplayRole)))
                prev_index = index
            all_data.append("\t".join(data_row))
            text = "\n".join(all_data)  # Tab-separated for multiple cells
            QApplication.clipboard().setText(text)

    def defer_sort(self, topLeft, bottomRight, roles):
        # Only defer if the sequence column was edited
        if topLeft.column() == 1: 
            self.sort_later = True        

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            #print("key return or enter")
            if not self.isPersistentEditorOpen(self.currentIndex()):
                self.edit(self.currentIndex())
        elif event.key() in [Qt.Key_Up, Qt.Key_Down]:
            #print("key up, key down")
            # Handle up/down arrow keys directly (e.g., move selection)
            current_index = self.currentIndex()
            new_row = current_index.row() + (-1 if event.key() == Qt.Key_Up else 1)
            new_index = self.model().index(new_row, current_index.column())
            if new_index.isValid():
                self.setCurrentIndex(new_index)
        elif event.key() == Qt.Key_Delete:  # Check if Delete key is pressed
            self.clear_selected_cells()
        else:
            super().keyPressEvent(event)


    def clear_selected_cells(self):
        indexes = self.selectionModel().selectedIndexes()
        if indexes:
            for index in indexes:
                # get source model 
                source_model = self.model().sourceModel()
                if index.column() not in source_model._uneditable_columns:
                    self.model().setData(index, "", Qt.EditRole)  # Set data to empty string

    def isPersistentEditorOpen(self, index):
        return self.indexWidget(index) is not None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        header = self.horizontalHeader()
        total_width = self.viewport().width()
        column_count = self.model().columnCount()
        self.setColumnHidden(0, True)

        # Define your desired column widths
        default_width = 60
        fixed_widths = {
            0: 50,   # First column 100 pixels
            1: 50,   # First column 100 pixels
            2: 300,   # Third column 150 pixels
        }

        # Calculate remaining width for flexible columns
        remaining_width = total_width - sum(fixed_widths.values())
        flexible_columns = column_count - len(fixed_widths)
        flexible_width = remaining_width // flexible_columns if flexible_columns > 0 else 0
        if flexible_width < default_width:
            flexible_width = default_width

        for i in range(column_count):
            if i in fixed_widths:
                header.resizeSection(i, fixed_widths[i])
            else:
                header.resizeSection(i, flexible_width)

        # Calculate maximum content width for each column
        content_widths = [0] * column_count
        for row in range(self.model().rowCount()):
            for col in range(column_count):
                index = self.model().index(row, col)
                text = str(self.model().data(index, Qt.DisplayRole))
                text_width = self.fontMetrics().horizontalAdvance(text)
                content_widths[col] = max(content_widths[col], text_width)

        # Adjust column widths based on content and fixed widths
        for i in range(column_count):
            if i in fixed_widths:
                header.resizeSection(i, fixed_widths[i])
            else:
                # Ensure a minimum width for flexible columns
                width = max(flexible_width, content_widths[i] + 20)  # Add some padding
                header.resizeSection(i, width)

class MdTableModel(QAbstractTableModel):
    dataChangedCustomSignal = pyqtSignal()
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []  # Initialize with provided data or an empty list
        self._vheader_data = []
        self._hheader_data = []
        self._uneditable_columns = [0,2,3,4]

    def set_columns_uneditable(self, columns):
        self._uneditable_columns = columns

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0]) if self._data else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        d = self._data[index.row()][index.column()]
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if isinstance(d, str):
                return d #self._data[index.row()][index.column()]
            elif isinstance(d, list):
                return " ".join(d)
            elif isinstance(d, dict) and 'value' in d:
                return d['value']
        if role == Qt.BackgroundRole:
            # if d is str or list, return default color
            if index.column() in self._uneditable_columns:
                return QColor(240, 240, 240)            
            if isinstance(d, (str, list)):
                return None
            elif isinstance(d, dict) and d.get('changed', False):
                return QColor('yellow')
        if role == Qt.ToolTipRole:
            return "Tooltip for cell ({}, {})".format(index.row(), index.column())
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter | Qt.AlignVCenter
        return None

    def setData(self, index, value, role=Qt.EditRole):
        old_data = self._data[index.row()][index.column()]
        if isinstance(old_data, dict) and old_data.get('value', None):
            old_data = old_data['value']
        if str(value) == str(old_data):
            return False

        if not index.isValid() or role != Qt.EditRole:
            return False
        if index.row() >= len(self._data) or index.column() >= len(self._data[0]):
            return False

        try:
            new_value = int(value) 
        except ValueError:
            try:
                new_value = float(value)
            except ValueError:
                new_value = str(value)

        self._data[index.row()][index.column()] = {'value': new_value, 'changed': True}
        self.dataChanged.emit(index, index, [role, Qt.BackgroundRole])
        self.dataChangedCustomSignal.emit()
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() in self._uneditable_columns:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return super().flags(index) | Qt.ItemIsEditable     

    def resetColors(self):
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                d = self._data[row][column]
                if isinstance(d, dict) and d.get('changed', False):
                    d['changed'] = False
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1), [Qt.BackgroundRole])

    def load_data(self, data):
        self.beginResetModel()
        self._data = data        
        self.endResetModel()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                # Return the header text for the given horizontal section
                return "{}".format(self._hheader_data[section])
                #return ""
            elif orientation == Qt.Vertical:
                # Return the header text for the given vertical section
                if len( self._vheader_data ) == 0:
                    return "{}".format(section+1)
                else:
                    return "{}".format(self._vheader_data[section])
        if role == Qt.ToolTipRole and orientation == Qt.Vertical:
            return ""

    def setVerticalHeader(self, header_data):
        self._vheader_data = header_data

    def setHorizontalHeader(self, header_data):
        self._hheader_data = header_data
        #print("header_data:", header_data)

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        try:  # Attempt to sort numerically
            self._data = sorted(
                self._data,
                key=lambda x: float(x[column]['value']), 
                reverse=(order == Qt.DescendingOrder)
            )
        except ValueError:  # Fallback to lexicographical sorting if not numeric
            self._data = sorted(
                self._data,
                key=lambda x: x[column]['value'],
                reverse=(order == Qt.DescendingOrder)
            )
        self.layoutChanged.emit()

    def clear(self):
        self.layoutAboutToBeChanged.emit()
        self._data = []  # Empty the underlying data
        self.layoutChanged.emit()

    def appendRows(self, rows):
        self.layoutAboutToBeChanged.emit()
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + len(rows) - 1)
        for row_data in rows:
            row = [{"value": col_data, "changed": False} for col_data in row_data]
            self._data.append(row)
        self.endInsertRows()
        self.layoutChanged.emit()

    def save_object_info(self):
        for row in self._data:
            #print(row)
            id = row[0]['value']
            obj = MdObject.get_by_id(id)
            ds = obj.dataset
            variablename_list = ds.get_variablename_list()
            property_list = []
            for idx, col in enumerate(row):
                if idx > max(self._uneditable_columns):
                    #print("idx:", idx, "col:", col['value'])
                    property_list.append(str(col['value']))
                elif idx == 1:
                    obj.sequence = col['value']
            obj.variable_list = property_list
            obj.pack_variable()
            obj.save()
        self.data_changed = False
        
class AnalysisInfoWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.m_app = QApplication.instance()
        self.default_color_list = mu.VIVID_COLOR_LIST[:]        
        self.color_list = self.default_color_list[:]
        #print("color_list", self.color_list)        
        self.marker_list = mu.MARKER_LIST[:]
        self.plot_size = "medium"
        #print("color_list", self.color_list)        
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.lblAnalysisName = QLabel(self.tr("Analysis Name"))
        self.edtAnalysisName = QLineEdit()
        self.lblSuperimposition = QLabel(self.tr("Superimposition"))
        self.edtSuperimposition = QLineEdit()
        self.edtSuperimposition.setEnabled(False)
        self.ignore_change = False
        self.PcaView = QWidget()
        self.pca_layout = QGridLayout()
        self.PcaView.setLayout(self.pca_layout)
        self.CvaView = QWidget()
        self.cva_layout = QGridLayout()
        self.CvaView.setLayout(self.cva_layout)
        self.ManovaView = QWidget()
        self.manova_layout = QGridLayout()
        self.ManovaView.setLayout(self.manova_layout)
        self.analysis_tab = QTabWidget()
        self.analysis_tab.addTab(self.PcaView, "PCA")
        self.analysis_tab.addTab(self.CvaView, "CVA")
        self.analysis_tab.addTab(self.ManovaView, "MANOVA")
        self.analysis_tab.currentChanged.connect(self.on_tab_changed)

        ''' PCA 3D plot '''
        self.lblPcaGroupBy = QLabel(self.tr("Grouping variable"))
        self.comboPcaGroupBy = QComboBox()
        self.comboPcaGroupBy.setEnabled(False)
        self.comboPcaGroupBy.currentIndexChanged.connect(self.comboPcaGroupBy_changed)
        self.pca_plot_widget3 = FigureCanvas(Figure(figsize=(20, 16),dpi=100))
        self.pca_fig3 = self.pca_plot_widget3.figure
        self.pca_ax3 = self.pca_fig3.add_subplot(projection='3d')
        self.pca_toolbar3 = NavigationToolbar(self.pca_plot_widget3, self)
        i = 0
        self.pca_layout.addWidget(self.pca_toolbar3, i, 0)
        self.pca_layout.addWidget(self.lblPcaGroupBy, i, 1)
        self.pca_layout.addWidget(self.comboPcaGroupBy, i, 2)
        i += 1
        self.pca_layout.addWidget(self.pca_plot_widget3, i, 0, 1, 2)
        self.pca_layout.setRowStretch(i, 1)

        ''' CVA 3D plot '''
        self.lblCvaGroupBy = QLabel("Grouping variable")
        self.comboCvaGroupBy = QComboBox()
        self.comboCvaGroupBy.setEnabled(False)
        self.comboCvaGroupBy.currentIndexChanged.connect(self.comboCvaGroupBy_changed)
        self.cva_plot_widget3 = FigureCanvas(Figure(figsize=(20, 16),dpi=100))
        self.cva_fig3 = self.cva_plot_widget3.figure
        self.cva_ax3 = self.cva_fig3.add_subplot(projection='3d')
        self.cva_toolbar3 = NavigationToolbar(self.cva_plot_widget3, self)
        i = 0
        self.cva_layout.addWidget(self.cva_toolbar3, i, 0)
        self.cva_layout.addWidget(self.lblCvaGroupBy, i, 1)
        self.cva_layout.addWidget(self.comboCvaGroupBy, i, 2)
        i += 1
        self.cva_layout.addWidget(self.cva_plot_widget3, i, 0, 1, 3)
        self.cva_layout.setRowStretch(i, 1)

        ''' MANOVA info '''
        self.lblManovaGroupBy = QLabel("Grouping variable")
        self.comboManovaGroupBy = QComboBox()
        self.comboManovaGroupBy.setEnabled(False)
        ''' manova output table '''
        self.tabManovaResult = QTableWidget()        
        self.comboManovaGroupBy.currentIndexChanged.connect(self.comboManovaGroupBy_changed)
        i = 0
        self.manova_layout.addWidget(self.lblManovaGroupBy, i, 0)
        self.manova_layout.addWidget(self.comboManovaGroupBy, i, 1)
        i += 1
        self.manova_layout.addWidget(self.tabManovaResult, i, 0, 1, 2)

        i = 0
        self.layout.addWidget(self.lblAnalysisName, i, 0)
        self.layout.addWidget(self.edtAnalysisName, i, 1)
        i += 1
        self.layout.addWidget(self.lblSuperimposition, i, 0)
        self.layout.addWidget(self.edtSuperimposition, i, 1)
        i += 1
        self.layout.addWidget(self.analysis_tab, i, 0, 1, 2)
        self.read_settings()

    def read_settings(self):
        self.plot_size = self.m_app.settings.value("PlotSize", self.plot_size)
        for i in range(len(self.color_list)):
            self.color_list[i] = self.m_app.settings.value("DataPointColor/"+str(i), self.default_color_list[i])
        for i in range(len(self.marker_list)):
            self.marker_list[i] = self.m_app.settings.value("DataPointMarker/"+str(i), self.marker_list[i])
        self.update_language()#self.m_app.settings.value("Language", "en"))

    def update_language(self):
        if False:
            if self.m_app.translator is not None:
                self.m_app.removeTranslator(self.m_app.translator)
                self.m_app.translator = None

            translator = QTranslator()
            translator_path = mu.resource_path("translations/Modan2_{}.qm".format(language))
            if os.path.exists(translator_path):
                translator.load(translator_path)
                self.m_app.installTranslator(translator)
                self.m_app.translator = translator

        self.lblAnalysisName.setText(self.tr("Analysis Name"))
        self.lblSuperimposition.setText(self.tr("Superimposition"))
        self.lblPcaGroupBy.setText(self.tr("Grouping variable"))
    
    def on_tab_changed(self, index):
        """Handle tab change event - enable buttons only for PCA tab"""
        # Enable Analysis Detail and Data Exploration buttons only for PCA tab (index 0)
        is_pca_tab = (index == 0)
        
        # Access parent's buttons (ModanMainWindow)
        if hasattr(self.parent, 'btnAnalysisDetail'):
            self.parent.btnAnalysisDetail.setEnabled(is_pca_tab)
        if hasattr(self.parent, 'btnDataExploration'):
            self.parent.btnDataExploration.setEnabled(is_pca_tab)

    def comboPcaGroupBy_changed(self):
        if self.ignore_change:
            return
        self.show_analysis_result()

    def comboCvaGroupBy_changed(self):
        if self.ignore_change:
            return
        self.show_analysis_result()

    def comboManovaGroupBy_changed(self):
        if self.ignore_change:
            return
        self.show_analysis_result()

    def set_analysis(self, analysis):        
        self.ignore_change = True
        self.analysis = analysis
        self.edtAnalysisName.setText(analysis.analysis_name)
        self.edtSuperimposition.setText(analysis.superimposition_method)
        for combo in [ self.comboPcaGroupBy, self.comboCvaGroupBy, self.comboManovaGroupBy ]:
            combo.clear()

            valid_property_index_list = analysis.dataset.get_grouping_variable_index_list()
            variablename_list = analysis.dataset.get_variablename_list()
            for idx in valid_property_index_list:
                property = variablename_list[idx]
                combo.addItem(property, idx)

        self.comboPcaGroupBy.setEnabled(True)
        self.comboCvaGroupBy.setEnabled(False)
        self.comboManovaGroupBy.setEnabled(False)
        
        self.comboPcaGroupBy.setCurrentIndex(0)

        if analysis.cva_group_by in analysis.dataset.get_variablename_list():
            self.comboCvaGroupBy.setCurrentText(analysis.cva_group_by)
        else:
            self.comboCvaGroupBy.setCurrentIndex(0)

        if analysis.manova_group_by in analysis.dataset.get_variablename_list():
            self.comboManovaGroupBy.setCurrentText(analysis.manova_group_by)
        else:
            self.comboManovaGroupBy.setCurrentIndex(0)
        self.ignore_change = False
        
        # Set tab to PCA by default
        self.analysis_tab.setCurrentIndex(0)
        
        # Set initial button state - enable only for PCA tab
        self.on_tab_changed(0)


    def show_analysis_result(self):
        logger = logging.getLogger(__name__)
        logger.info(f"show_analysis_result called for: {self.analysis.analysis_name}")
        
        # Handle legacy analysis data - if JSON is missing, show basic info
        if not self.analysis.object_info_json:
            logger.warning("No JSON data found - showing basic analysis info")
            # Show analysis name and details in a simple format
            self.edtAnalysisName.setText(self.analysis.analysis_name)
            self.edtSuperimposition.setText(self.analysis.superimposition_method or "Unknown")
            return
        
        # Continue with full analysis display if JSON data exists
        logger.info("Loading object_info_json")
        object_info_list = json.loads(self.analysis.object_info_json)
        for obj in object_info_list:
            if 'property_list' in obj.keys():
                obj['variable_list'] = obj['property_list']
            
        # Initialize result variables
        pca_analysis_result_list = None
        cva_analysis_result_list = None
        manova_result = None
        
        if self.analysis.pca_analysis_result_json:
            logger.info("Loading pca_analysis_result_json")
            pca_analysis_result_list = json.loads(self.analysis.pca_analysis_result_json)
            logger.info(f"PCA result loaded: type={type(pca_analysis_result_list)}, len={len(pca_analysis_result_list) if pca_analysis_result_list else 'None'}")
        
        logger.info(f"CVA JSON exists: {bool(self.analysis.cva_analysis_result_json)}")
        if self.analysis.cva_analysis_result_json:
            logger.info("Loading cva_analysis_result_json")
            cva_analysis_result_list = json.loads(self.analysis.cva_analysis_result_json)
            logger.info(f"CVA result loaded: type={type(cva_analysis_result_list)}, len={len(cva_analysis_result_list) if cva_analysis_result_list else 'None'}")
        else:
            logger.warning("CVA analysis_result_json is empty or None")
            
        if self.analysis.manova_analysis_result_json:
            logger.info("Loading manova_analysis_result_json")
            manova_result = json.loads(self.analysis.manova_analysis_result_json)
        
        # Handle MANOVA results
        self.tabManovaResult.clear()
        self.tabManovaResult.setRowCount(0)
        
        if manova_result:
            logger.debug(f"MANOVA result structure: {manova_result}")
            
            # Set up proper MANOVA table format
            # Columns: Statistic, Value, Num DF, Den DF, F Value, Pr>F
            column_headers = ["Statistic", "Value", "Num DF", "Den DF", "F Value", "Pr>F"]
            self.tabManovaResult.setColumnCount(len(column_headers))
            self.tabManovaResult.setHorizontalHeaderLabels(column_headers)
            
            # Check if MANOVA result contains multiple statistics or single values
            if 'stat_dict' in manova_result and isinstance(manova_result['stat_dict'], dict):
                # New stat_dict format (matches original Modan2)
                logger.info("MANOVA: Processing stat_dict format")
                stat_dict = manova_result['stat_dict']
                column_names = stat_dict.get('column_names', column_headers)
                
                for stat_name, stat_values in stat_dict.items():
                    if stat_name == 'column_names':
                        continue
                        
                    row = self.tabManovaResult.rowCount()
                    self.tabManovaResult.insertRow(row)
                    
                    # Set statistic name
                    self.tabManovaResult.setItem(row, 0, QTableWidgetItem(stat_name))
                    
                    # Set values from the list
                    if isinstance(stat_values, list) and len(stat_values) >= 5:
                        self.tabManovaResult.setItem(row, 1, QTableWidgetItem(f"{stat_values[0]:.6e}"))
                        self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(int(stat_values[1]))))
                        self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(int(stat_values[2]))))
                        self.tabManovaResult.setItem(row, 4, QTableWidgetItem(f"{stat_values[3]:.3f}"))
                        self.tabManovaResult.setItem(row, 5, QTableWidgetItem(f"{stat_values[4]:.3f}"))
                        
            elif 'statistics' in manova_result and isinstance(manova_result['statistics'], dict):
                # Multiple statistics format
                logger.info("MANOVA: Processing multiple statistics format")
                for stat_name, stat_data in manova_result['statistics'].items():
                    row = self.tabManovaResult.rowCount()
                    self.tabManovaResult.insertRow(row)
                    
                    # Set statistic name
                    self.tabManovaResult.setItem(row, 0, QTableWidgetItem(stat_name))
                    
                    # Set values if available
                    if isinstance(stat_data, dict):
                        self.tabManovaResult.setItem(row, 1, QTableWidgetItem(str(stat_data.get('value', 'N/A'))))
                        self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(stat_data.get('num_df', 'N/A'))))
                        self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(stat_data.get('den_df', 'N/A'))))
                        self.tabManovaResult.setItem(row, 4, QTableWidgetItem(str(stat_data.get('f_statistic', 'N/A'))))
                        self.tabManovaResult.setItem(row, 5, QTableWidgetItem(str(stat_data.get('p_value', 'N/A'))))
            else:
                # Single statistics - convert current format to table rows
                logger.info("MANOVA: Processing single statistics format")
                
                # Map common MANOVA statistics to display names
                stat_mapping = {
                    'wilks_lambda': "Wilks' Lambda",
                    'pillais_trace': "Pillai's Trace", 
                    'hotellings_trace': "Hotelling's Trace",
                    'roys_largest_root': "Roy's Largest Root",
                    'f_statistic': 'F Statistic',
                    'p_value': 'P Value'
                }
                
                for key, value in manova_result.items():
                    if key in ['analysis_type', 'degrees_of_freedom']:
                        continue  # Skip meta information
                        
                    row = self.tabManovaResult.rowCount()
                    self.tabManovaResult.insertRow(row)
                    
                    # Use mapped name if available, otherwise use key
                    display_name = stat_mapping.get(key, key.replace('_', ' ').title())
                    self.tabManovaResult.setItem(row, 0, QTableWidgetItem(display_name))
                    
                    # Set the value
                    self.tabManovaResult.setItem(row, 1, QTableWidgetItem(str(value)))
                    
                    # For degrees of freedom, try to extract if available
                    if key == 'degrees_of_freedom' and isinstance(value, (list, tuple)) and len(value) >= 2:
                        self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(value[0])))  # Num DF
                        self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(value[1])))  # Den DF
                    elif 'degrees_of_freedom' in manova_result and isinstance(manova_result['degrees_of_freedom'], (list, tuple)):
                        df = manova_result['degrees_of_freedom']
                        if len(df) >= 2:
                            self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(df[0])))
                            self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(df[1])))
            
            logger.info(f"MANOVA table final size: {self.tabManovaResult.rowCount()}x{self.tabManovaResult.columnCount()}")
        else:
            logger.warning("MANOVA result is empty or None")

        # Handle property names safely
        if self.analysis.propertyname_str:
            variablename_list = self.analysis.propertyname_str.split(",")
        else:
            # Fallback to dataset's variable names if analysis doesn't have them
            variablename_list = self.analysis.dataset.get_variablename_list()
            logger.info(f"Using dataset variable names: {variablename_list}")

        symbol_candidate = ['o','s','^','x','+','d','v','<','>','p','h']
        symbol_candidate = self.marker_list[:]
        color_candidate = ['blue','green','black','cyan','magenta','yellow','gray','red']
        color_candidate = self.color_list[:]

        SCATTER_SMALL_SIZE = 30
        SCATTER_MEDIUM_SIZE = 50
        SCATTER_LARGE_SIZE = 60
        scatter_size = SCATTER_MEDIUM_SIZE

        self.pca_ax3.clear()
        self.cva_ax3.clear()

        axis_prefix_list = [ "PC", "CV" ]
        combo_list = [ self.comboPcaGroupBy, self.comboCvaGroupBy ]
        plot_widget_list = [ self.pca_plot_widget3, self.cva_plot_widget3 ]
        fig_list = [ self.pca_fig3, self.cva_fig3 ]
        ax_list = [ self.pca_ax3, self.cva_ax3 ]
        propertyname_index_list = [ -1, -1 ]
        self.pca_scatter_data = {}
        self.cva_scatter_data = {}
        scatter_data_list = [ self.pca_scatter_data, self.cva_scatter_data ]
        self.pca_scatter_result = {}
        self.cva_scatter_result = {}
        scatter_result_list = [ self.pca_scatter_result, self.cva_scatter_result ]
        analysis_result_list_list = [ pca_analysis_result_list, cva_analysis_result_list ]
        
        # Debug logging for analysis results
        logger.info(f"Object count: {len(object_info_list)}")
        if pca_analysis_result_list:
            logger.info(f"PCA result count: {len(pca_analysis_result_list)}")
        else:
            logger.info("PCA result is None/empty")
        if cva_analysis_result_list:
            logger.info(f"CVA result count: {len(cva_analysis_result_list)}")
        else:
            logger.info("CVA result is None/empty")

        for idx, axis_prefix in enumerate(axis_prefix_list):
            logger.info(f"Processing analysis type idx={idx}, prefix='{axis_prefix}', has_data={analysis_result_list_list[idx] is not None}")
            
            # Skip processing if no data available for this analysis type
            if not analysis_result_list_list[idx]:
                logger.info(f"Skipping {axis_prefix} processing - no data available")
                continue
                
            depth_shade = False
            show_legend = False
            show_axis_label = True
            axis1 = 0
            axis2 = 1
            axis3 = 2
            axis1_title = axis_prefix + str(axis1+1)
            axis2_title = axis_prefix + str(axis2+1)
            axis3_title = axis_prefix + str(axis3+1)
            propertyname = combo_list[idx].currentText()
            propertyname_index_list[idx] = variablename_list.index(propertyname) if propertyname in variablename_list else -1
            logger.info(f"Grouping for {axis_prefix}: propertyname='{propertyname}', index={propertyname_index_list[idx]}")
            logger.info(f"Available variables: {variablename_list[:10]}")  # Show first 10 variables
            scatter_data_list[idx] = {}
            scatter_result_list[idx] = {}

            key_list = []
            key_list.append('__default__')
            scatter_data_list[idx]['__default__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':color_candidate[0], 'size':scatter_size}

            for idx2, obj in enumerate(object_info_list):
                key_name = '__default__'
                ''' get propertyname '''
                if idx2 < 3:  # Debug first 3 objects
                    logger.info(f"Object {idx2} keys: {list(obj.keys())}")
                    if 'variable_list' in obj.keys():
                        logger.info(f"Object {idx2} variable_list: {obj['variable_list'][:5] if len(obj['variable_list']) > 5 else obj['variable_list']}")
                
                if 'variable_list' in obj.keys():
                    if propertyname_index_list[idx] > -1 and propertyname_index_list[idx] < len(obj['variable_list']):
                        key_name = obj['variable_list'][propertyname_index_list[idx]]
                else:
                    if propertyname_index_list[idx] > -1 and propertyname_index_list[idx] < len(obj['property_list']):
                        key_name = obj['property_list'][propertyname_index_list[idx]]


                if key_name not in scatter_data_list[idx].keys():
                    scatter_data_list[idx][key_name] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'property':key_name, 'symbol':'', 'color':'', 'size':scatter_size}
                    if idx2 < 5:  # Only log first few objects
                        logger.info(f"Created new group '{key_name}' for object {idx2}")

                # Safety check for analysis result data
                if (analysis_result_list_list[idx] and 
                    idx2 < len(analysis_result_list_list[idx]) and 
                    analysis_result_list_list[idx][idx2] is not None and
                    len(analysis_result_list_list[idx][idx2]) > max(axis1, axis2, axis3)):
                    
                    scatter_data_list[idx][key_name]['x_val'].append(analysis_result_list_list[idx][idx2][axis1])
                    scatter_data_list[idx][key_name]['y_val'].append(analysis_result_list_list[idx][idx2][axis2])
                    scatter_data_list[idx][key_name]['z_val'].append(analysis_result_list_list[idx][idx2][axis3])
                    scatter_data_list[idx][key_name]['data'].append(obj)
                else:
                    # Debug detailed failure reason
                    failure_reasons = []
                    if not analysis_result_list_list[idx]:
                        failure_reasons.append("no analysis data")
                    elif idx2 >= len(analysis_result_list_list[idx]):
                        failure_reasons.append(f"idx2({idx2}) >= data_len({len(analysis_result_list_list[idx])})")
                    elif analysis_result_list_list[idx][idx2] is None:
                        failure_reasons.append("result is None")
                    elif len(analysis_result_list_list[idx][idx2]) <= max(axis1, axis2, axis3):
                        failure_reasons.append(f"result_len({len(analysis_result_list_list[idx][idx2])}) <= max_axis({max(axis1, axis2, axis3)})")
                    
                    logger.warning(f"Skipping invalid analysis result data for object {idx2}: {', '.join(failure_reasons)}")
                    # Add default values to maintain consistency
                    scatter_data_list[idx][key_name]['x_val'].append(0.0)
                    scatter_data_list[idx][key_name]['y_val'].append(0.0)
                    scatter_data_list[idx][key_name]['z_val'].append(0.0)
                    scatter_data_list[idx][key_name]['data'].append(obj)

            ''' remove empty group '''
            if len(scatter_data_list[idx]['__default__']['x_val']) == 0:
                del scatter_data_list[idx]['__default__']

            ''' assign color and symbol '''
            sc_idx = 0
            for key_name in scatter_data_list[idx].keys():
                if scatter_data_list[idx][key_name]['color'] == '':
                    scatter_data_list[idx][key_name]['color'] = color_candidate[sc_idx % len(color_candidate)]
                    scatter_data_list[idx][key_name]['symbol'] = symbol_candidate[sc_idx % len(symbol_candidate)]
                    sc_idx += 1

            if True:
                ax_list[idx].clear()
                for name in scatter_data_list[idx].keys():
                    group = scatter_data_list[idx][name]
                    if len(scatter_data_list[idx][name]['x_val']) > 0:
                        scatter_result_list[idx][name] = ax_list[idx].scatter(group['x_val'], group['y_val'], group['z_val'], s=group['size'], marker=group['symbol'], color=group['color'], data=group['data'],depthshade=depth_shade, picker=True, pickradius=5)

                if True:
                    if '__default__' in scatter_result_list[idx].keys():
                        del scatter_result_list[idx]['__default__']
                    ax_list[idx].legend(scatter_result_list[idx].values(), scatter_result_list[idx].keys(), loc='upper right', bbox_to_anchor=(1.05, 1))
                if True:
                    ax_list[idx].set_xlabel(axis1_title)
                    ax_list[idx].set_ylabel(axis2_title)
                    ax_list[idx].set_zlabel(axis3_title)
                fig_list[idx].tight_layout()
                fig_list[idx].canvas.draw()
                fig_list[idx].canvas.flush_events()