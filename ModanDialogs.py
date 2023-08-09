from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, QStatusBar,\
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QAction, QMenu, QSizePolicy, \
                            QTableWidget, QBoxLayout, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox, QOpenGLWidget, \
                            QTabWidget, QListWidget, QColorDialog

from PyQt5 import QtGui, uic
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem,\
                        QPainterPath, QFont, QImageReader, QPainter, QBrush, QMouseEvent, QWheelEvent, QDrag, QDoubleValidator
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QEvent, QRegExp, QSize, QPoint,\
                         pyqtSignal, QThread, QMimeData, pyqtSlot, QItemSelectionModel, QTimer

import pyqtgraph as pg
#import pyqtgraph.opengl as gl
from OBJFileLoader import OBJ

import OpenGL.GL as gl
from OpenGL import GLU as glu
from OpenGL import GLUT as glut
from PyQt5.QtOpenGL import *
import sys
#import scipy as sp

import random
import struct
import xlsxwriter

import math, re, os
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import shutil
#import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from MdModel import *
import MdUtils as mu

from MdStatistics import MdPrincipalComponent, MdCanonicalVariate
import numpy as np
from OpenGL.arrays import vbo
import copy
#from pyqt_color_picker import ColorPickerWidget, ColorPickerDialog

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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

LANDMARK_RADIUS = 2
DISTANCE_THRESHOLD = LANDMARK_RADIUS * 3

IMAGE_EXTENSION_LIST = ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']
MODEL_EXTENSION_LIST = ['obj', 'ply', 'stl']

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
ICON['landmark'] = resource_path('icons/M2Landmark_2.png')
ICON['landmark_hover'] = resource_path('icons/M2Landmark_2_hover.png')
ICON['landmark_down'] = resource_path('icons/M2Landmark_2_down.png')
ICON['landmark_disabled'] = resource_path('icons/M2Landmark_2_disabled.png')
ICON['wireframe'] = resource_path('icons/M2Wireframe_2.png')
ICON['wireframe_hover'] = resource_path('icons/M2Wireframe_2_hover.png')
ICON['wireframe_down'] = resource_path('icons/M2Wireframe_2_down.png')
ICON['calibration'] = resource_path('icons/M2Calibration_2.png')
ICON['calibration_hover'] = resource_path('icons/M2Calibration_2_hover.png')
ICON['calibration_down'] = resource_path('icons/M2Calibration_2_down.png')
ICON['calibration_disabled'] = resource_path('icons/M2Calibration_2_disabled.png')

NEWLINE = '\n'


def as_qt_color(color):
    return QColor( *[ int(x*255) for x in color ] )

class ObjectViewer2D(QLabel):
    def __init__(self, widget):
        super(ObjectViewer2D, self).__init__(widget)
        self.setMinimumSize(400,300)
        self.object_dialog = None
        self.object = None
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.scale = 1.0
        self.fullpath = None
        self.pan_mode = MODE['NONE']
        self.edit_mode = MODE['NONE']

        self.show_index = True
        self.show_wireframe = True
        self.show_baseline = False  
        self.read_only = False
        self.show_model = False

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
            #QApplication.setOverrideCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
        elif self.edit_mode == MODE['READY_MOVE_LANDMARK']:
            self.setCursor(Qt.SizeAllCursor)
            #QApplication.setOverrideCursor(Qt.SizeAllCursor)
            self.show_message("Click on landmark to move")
        elif self.edit_mode == MODE['MOVE_LANDMARK']:
            #QApplication.setOverrideCursor(Qt.SizeAllCursor)
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Move landmark")
        elif self.edit_mode == MODE['CALIBRATION']:
            #QApplication.setOverrideCursor(Qt.CrossCursor)
            self.setCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
        else:
            self.setCursor(Qt.ArrowCursor)
            #QApplication.setOverrideCursor(Qt.ArrowCursor)

    def get_landmark_index_within_threshold(self, curr_pos, threshold=DISTANCE_THRESHOLD):
        for index, landmark in enumerate(self.landmark_list):
            lm_can_pos = [self._2canx(landmark[0]),self._2cany(landmark[1])]
            dist = self.get_distance(curr_pos, lm_can_pos)
            #print(curr_pos, "lm_can_pos", lm_can_pos, "dist:", dist, "idx:", index)
            if dist < threshold:
                return index
        return -1
    
    def get_edge_index_within_threshold(self, curr_pos, threshold=DISTANCE_THRESHOLD):
        if len(self.edge_list) == 0:
            return -1

        landmark_list = self.landmark_list
        for index, wire in enumerate(self.edge_list):
            if wire[0] >= len(self.landmark_list) or wire[1] >= len(self.landmark_list):
                continue

            wire_start = [self._2canx(float(self.landmark_list[wire[0]][0])),self._2cany(float(self.landmark_list[wire[0]][1]))]
            wire_end = [self._2canx(float(self.landmark_list[wire[1]][0])),self._2cany(float(self.landmark_list[wire[1]][1]))]
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
        #print("self.edit_mode", self.edit_mode, "curr pos:", curr_pos)
    
        if self.pan_mode == MODE['PAN']:
            self.temp_pan_x = int(self.mouse_curr_x - self.mouse_down_x)
            self.temp_pan_y = int(self.mouse_curr_y - self.mouse_down_y)

        elif self.edit_mode == MODE['EDIT_LANDMARK']:
            near_idx = self.get_landmark_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
            if near_idx >= 0:
                #self.setCursor(Qt.SizeAllCursor)                
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
            #if self.object_dialog is None:
            #    return
            if self.edit_mode == MODE['EDIT_LANDMARK']:
                img_x = self._2imgx(self.mouse_curr_x)
                img_y = self._2imgy(self.mouse_curr_y)
                if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                    return
                self.object_dialog.add_landmark(img_x, img_y)
                #self.update_landmark_list()
                #print(self.cursor_on_vertex, x,y,z, self.landmark_list[0], self.obj_ops.landmark_list[0])
                #self.calculate_resize()
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
                #if self.
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
            else:
                self.pan_mode = MODE['PAN']
                self.mouse_down_x = me.x()
                self.mouse_down_y = me.y()
        elif me.button() == Qt.MidButton:
            print("middle button clicked")

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

        return super().mouseReleaseEvent(ev)    

    def wheelEvent(self, event):
        #if self.orig_pixmap is None:
        #    return
        we = QWheelEvent(event)
        scale_delta = 0
        if we.angleDelta().y() > 0:
            scale_delta = 0.1
        else:
            scale_delta = -0.1
        if self.scale <= 0.8 and scale_delta < 0:
            return
        if self.scale > 1:
            scale_delta *= math.floor(self.scale)
        
        prev_scale = self.scale
        self.scale += scale_delta
        self.scale = round(self.scale * 10) / 10
        scale_proportion = self.scale / prev_scale
        if self.orig_pixmap is not None:
            self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_pixmap.width() * self.scale / self.image_canvas_ratio), int(self.orig_pixmap.height() * self.scale / self.image_canvas_ratio))

        self.pan_x = int( we.pos().x() - (we.pos().x() - self.pan_x) * scale_proportion )
        self.pan_y = int( we.pos().y() - (we.pos().y() - self.pan_y) * scale_proportion )

        self.repaint()

        QLabel.wheelEvent(self, event)

    def dragEnterEvent(self, event):
        if self.object_dialog is None:
            return
        file_name = event.mimeData().text()
        if file_name.split('.')[-1].lower() in IMAGE_EXTENSION_LIST:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self.object_dialog is None:
            return

        file_path = event.mimeData().text()
        file_path = re.sub('file:///', '', file_path)
        self.set_image(file_path)
        self.calculate_resize()
        if self.object_dialog is not None:
            self.object_dialog.set_object_name(Path(file_path).stem)

    def paintEvent(self, event):
        # fill background with dark gray

        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(as_qt_color(COLOR['BACKGROUND'])))
        if self.object is None:
            return
        if self.curr_pixmap is not None:
            #print("paintEvent", self.curr_pixmap.width(), self.curr_pixmap.height())
            painter.drawPixmap(self.pan_x+self.temp_pan_x, self.pan_y+self.temp_pan_y,self.curr_pixmap)
            #print("paintEvent", self.pan_x+self.temp_pan_x, self.pan_y+self.temp_pan_y,self.curr_pixmap.width(), self.curr_pixmap.height())
            #print("pan_x", self.pan_x, "pan_y", self.pan_y, "temp_pan_x", self.temp_pan_x, "temp_pan_y", self.temp_pan_y)

        if self.show_wireframe == True:
            painter.setPen(QPen(as_qt_color(COLOR['WIREFRAME']), 2))
            painter.setBrush(QBrush(as_qt_color(COLOR['WIREFRAME'])))

            for wire in self.edge_list:
                if wire[0] >= len(self.landmark_list) or wire[1] >= len(self.landmark_list):
                    continue
                [ from_x, from_y ] = self.landmark_list[wire[0]]
                [ to_x, to_y ] = self.landmark_list[wire[1]]
                painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))
                #painter.drawLine(self.landmark_list[wire[0]][0], self.landmark_list[wire[0]][1], self.landmark_list[wire[1]][0], self.landmark_list[wire[1]][1])
            if self.selected_edge_index >= 0:
                edge = self.edge_list[self.selected_edge_index]
                painter.setPen(QPen(as_qt_color(COLOR['SELECTED_EDGE']), 2))
                if edge[0] >= len(self.landmark_list) or edge[1] >= len(self.landmark_list):
                    pass
                else:
                    [ from_x, from_y ] = self.landmark_list[edge[0]]
                    [ to_x, to_y ] = self.landmark_list[edge[1]]
                    painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))

        radius = LANDMARK_RADIUS
        painter.setPen(QPen(Qt.blue, 2))
        painter.setBrush(QBrush(Qt.blue))
        if self.edit_mode == MODE['CALIBRATION']:
            if self.calibration_from_img_x >= 0 and self.calibration_from_img_y >= 0:
                x1 = int(self._2canx(self.calibration_from_img_x))
                y1 = int(self._2cany(self.calibration_from_img_y))
                x2 = self.mouse_curr_x
                y2 = self.mouse_curr_y
                painter.setPen(QPen(as_qt_color(COLOR['SELECTED_LANDMARK']), 2))
                painter.drawLine(x1,y1,x2,y2)

        painter.setFont(QFont('Helvetica', 10))
        for idx, landmark in enumerate(self.landmark_list):
            if idx == self.wire_hover_index:
                painter.setPen(QPen(as_qt_color(COLOR['SELECTED_LANDMARK']), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR['SELECTED_LANDMARK'])))
            elif idx == self.wire_start_index or idx == self.wire_end_index:
                painter.setPen(QPen(as_qt_color(COLOR['SELECTED_LANDMARK']), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR['SELECTED_LANDMARK'])))
            elif idx == self.selected_landmark_index:
                painter.setPen(QPen(as_qt_color(COLOR['SELECTED_LANDMARK']), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR['SELECTED_LANDMARK'])))
            else:
                painter.setPen(QPen(as_qt_color(COLOR['NORMAL_SHAPE']), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR['NORMAL_SHAPE'])))
            painter.drawEllipse(int(self._2canx(landmark[0])-radius), int(self._2cany(landmark[1]))-radius, radius*2, radius*2)
            if self.show_index == True:
                painter.setPen(QPen(as_qt_color(COLOR['NORMAL_TEXT']), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR['NORMAL_TEXT'])))
                painter.drawText(int(self._2canx(landmark[0])+10), int(self._2cany(landmark[1]))+10, str(idx+1))

        # draw wireframe being edited
        if self.wire_start_index >= 0:
            painter.setPen(QPen(as_qt_color(COLOR['WIREFRAME']), 2))
            painter.setBrush(QBrush(as_qt_color(COLOR['WIREFRAME'])))
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

    def update_landmark_list(self):
        return

    def calculate_resize(self):
        #print("objectviewer calculate resize", self, self.object, self.object.landmark_list, self.landmark_list)
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
            #print("min_x:", min_x, "max_x:", max_x, "min_y:", min_y, "max_y:", max_y)
            width = max_x - min_x
            height = max_y - min_y
            w_scale = ( self.width() * 1.0 ) / ( width * 1.5 )
            h_scale = ( self.height() * 1.0 ) / ( height * 1.5 )
            self.scale = min(w_scale, h_scale)
            self.pan_x = int( -min_x * self.scale + (self.width() - width * self.scale) / 2.0 )
            self.pan_y = int( -min_y * self.scale + (self.height() - height * self.scale) / 2.0 )
            #print("scale:", self.scale, "pan_x:", self.pan_x, "pan_y:", self.pan_y, "image_canvas_ratio:", self.image_canvas_ratio)
        self.repaint()

    def resizeEvent(self, event):
        self.calculate_resize()
        QLabel.resizeEvent(self, event)

    def set_object(self, object):
        #print("set object", object, object.pixels_per_mm)
        m_app = QApplication.instance()
        self.object = object
        dataset = object.dataset

        if self.object.pixels_per_mm is not None and self.object.pixels_per_mm > 0:
            self.pixels_per_mm = self.object.pixels_per_mm
        if object.image.count() > 0:
            self.set_image(object.image[0].get_file_path(m_app.storage_directory))

        object.unpack_landmark()
        object.dataset.unpack_wireframe()
        self.landmark_list = object.landmark_list
        self.edge_list = object.dataset.edge_list
        self.calculate_resize()

    def set_image(self,file_path):
        self.fullpath = file_path
        self.curr_pixmap = self.orig_pixmap = QPixmap(file_path)
        self.setPixmap(self.curr_pixmap)


    def clear_object(self):
        self.landmark_list = []
        self.edge_list = []
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.object = None
        self.pan_x = 0
        self.pan_y = 0
        self.temp_pan_x = 0
        self.temp_pan_y = 0
        self.scale = 1.0
        self.image_canvas_ratio = 1.0
        self.update()

    def add_edge(self,wire_start_index, wire_end_index):
        if wire_start_index == wire_end_index:
            return
        if wire_start_index > wire_end_index:
            wire_start_index, wire_end_index = wire_end_index, wire_start_index
        dataset = self.object.dataset
        for wire in dataset.edge_list:
            if wire[0] == wire_start_index and wire[1] == wire_end_index:
                return
        dataset.edge_list.append([wire_start_index, wire_end_index])
        dataset.pack_wireframe()
        dataset.save()
        self.repaint()
        
    def delete_edge(self, edge_index):
        dataset = self.object.dataset
        dataset.edge_list.pop(edge_index)
        dataset.pack_wireframe()
        dataset.save()
        self.repaint()

class ObjectViewer3D(QGLWidget):
    def __init__(self, parent):
        #print("MyGLWidget init")
        QGLWidget.__init__(self,parent)
        self.parent = parent
        self.setMinimumSize(400,300)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.object_dialog = None
        self.ds_ops = None
        self.obj_ops = None
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.temp_pan_x = 0
        self.temp_pan_y = 0
        self.rotate_x = 0
        self.rotate_y = 0
        self.temp_rotate_x = 0
        self.temp_rotate_y = 0
        self.show_index = True
        self.show_wireframe = True
        self.show_baseline = False
        self.show_average = True
        self.show_model = True
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
        #self.setMinimumSize(400,400)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.timeout)
        self.timer.start()
        self.frustum_args = {'width': 1.0, 'height': 1.0, 'znear': 0.1, 'zfar': 1000.0}
        self.color_to_lm_idx = {}
        self.lm_idx_to_color = {}
        self.picker_buffer = None
        self.gl_list = None
        #self.no_drawing = False
        self.wireframe_from_idx = -1
        self.wireframe_to_idx = -1
        self.selected_landmark_idx = -1
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

    def show_message(self, msg):
        if self.object_dialog is not None:
            self.object_dialog.status_bar.showMessage(msg) 

    def set_mode(self, mode):
        self.edit_mode = mode  
        if self.edit_mode == MODE['EDIT_LANDMARK']:
            self.setCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
        elif self.edit_mode == MODE['READY_MOVE_LANDMARK']:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Click on landmark to move")
        elif self.edit_mode == MODE['MOVE_LANDMARK']:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Move landmark")
        elif self.edit_mode == MODE['WIREFRAME']:
            #print("self.obj_ops:", self.obj_ops)
            self.initialize_colors()
            self.setCursor(Qt.ArrowCursor)
            self.show_message("Wireframe mode")
        else:
            self.setCursor(Qt.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        # left button: rotate
        # right button: zoom
        # middle button: pan

        self.down_x = event.x()
        self.down_y = event.y()
        #print("down_x:", self.down_x, "down_y:", self.down_y)
        if event.buttons() == Qt.LeftButton:
            if self.edit_mode == MODE['WIREFRAME'] and self.selected_landmark_idx > -1:
                self.wireframe_from_idx = self.selected_landmark_idx
                #self.edit_mode = MODE_ADD_WIRE
            elif self.edit_mode == MODE['EDIT_LANDMARK'] and self.cursor_on_vertex > -1:
                pass
            else:                
                self.view_mode = ROTATE_MODE
        elif event.buttons() == Qt.RightButton:
            if self.edit_mode == MODE['EDIT_LANDMARK'] and self.cursor_on_vertex > -1:
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
        #print("curr_x:", self.curr_x, "curr_y:", self.curr_y)
        if event.button() == Qt.LeftButton:
            if self.edit_mode == MODE['WIREFRAME'] and self.wireframe_from_idx > -1 and self.selected_landmark_idx > -1 and self.selected_landmark_idx != self.wireframe_from_idx:
                self.wireframe_to_idx = self.selected_landmark_idx
                self.add_wire(self.wireframe_from_idx, self.wireframe_to_idx)
                self.wireframe_from_idx = -1
                self.wireframe_to_idx = -1
                self.update()
            elif self.edit_mode == MODE['EDIT_LANDMARK'] and self.cursor_on_vertex > -1 and self.curr_x == self.down_x and self.curr_y == self.down_y:
                #self.threed_model.landmark_list.append(self.cursor_on_vertex)
                x, y, z = self.threed_model.original_vertices[self.cursor_on_vertex]
                #print(self.cursor_on_vertex, x,y,z, self.landmark_list[0], self.obj_ops.landmark_list[0], self.object_dialog.landmark_list[0])
                self.object_dialog.add_landmark(x,y,z)
                self.update_landmark_list()
                self.calculate_resize()
            else:
                self.rotate_x += self.temp_rotate_x
                self.rotate_y += self.temp_rotate_y
                if self.data_mode == OBJECT_MODE and self.obj_ops is not None:
                    #print("x rotate:", self.rotate_x, "y rotate:", self.rotate_y)
                    #print( "test_obj vert 1 before rotation:", self.test_obj.vertices[0])
                    #self.obj_ops.rotate(math.radians(-1*self.rotate_x),math.radians(self.rotate_y))
                    self.obj_ops.rotate_3d(math.radians(-1*self.rotate_x),'Y')
                    self.obj_ops.rotate_3d(math.radians(self.rotate_y),'X')
                    if self.threed_model is not None:
                        #print("rotate_x:", self.rotate_x, "rotate_y:", self.rotate_y)
                        #print("1:",datetime.datetime.now())
                        if self.show_model == True:
                            apply_rotation_to_vertex = True
                        else:
                            apply_rotation_to_vertex = False
                        self.threed_model.rotate(math.radians(self.rotate_x),math.radians(self.rotate_y),apply_rotation_to_vertex)
                        #print("2:",datetime.datetime.now())
                        #self.threed_model.rotate_3d(math.radians(-1*self.rotate_x),'Y')
                        #self.threed_model.rotate_3d(math.radians(self.rotate_y),'X')
                        if self.show_model == True:
                            self.threed_model.generate()
                        #print("3:",datetime.datetime.now())
                    #print( "test_obj vert 1 after rotation:", self.test_obj.vertices[0])
                    self.rotate_x = 0
                    self.rotate_y = 0
                    #self.obj
                elif self.data_mode == DATASET_MODE and self.ds_ops is not None:
                    #self.ds_ops.average_shape.rotate_3d(math.radians(-1*self.rotate_x),'Y')
                    #self.ds_ops.average_shape.rotate_3d(math.radians(self.rotate_y),'X')
                    for obj in self.ds_ops.object_list:
                        obj.rotate_3d(math.radians(-1*self.rotate_x),'Y')
                        obj.rotate_3d(math.radians(self.rotate_y),'X')
                    self.rotate_x = 0
                    self.rotate_y = 0
                self.temp_rotate_x = 0
                self.temp_rotate_y = 0
        elif event.button() == Qt.RightButton:
            if self.edit_mode == MODE['EDIT_LANDMARK'] and self.cursor_on_vertex > -1 and self.curr_x == self.down_x and self.curr_y == self.down_y:
                print("delete landmark")
            else:
                self.dolly += self.temp_dolly 
                self.temp_dolly = 0
        elif event.button() == Qt.MiddleButton:
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
        self.view_mode = VIEW_MODE
        self.updateGL()
        #self.parent.update_status()

    def mouseMoveEvent(self, event):
        #@print("mouse move event",event)
        self.curr_x = event.x()
        self.curr_y = event.y()
        #print("curr_x:", self.curr_x, "curr_y:", self.curr_y)
        if self.edit_mode == WIREFRAME_MODE:
            #print("wireframe mode. about to do hit_test")

            hit, lm_idx = self.hit_test(self.curr_x, self.curr_y)
            if hit:
                self.selected_landmark_idx = lm_idx
                self.no_hit_count = 0
            elif self.selected_landmark_idx > -1:
                self.no_hit_count += 1
                if self.no_hit_count > 5:
                    self.selected_landmark_idx = -1
                    self.no_hit_count = 0

        if event.buttons() == Qt.LeftButton and self.view_mode == ROTATE_MODE:
            self.is_dragging = True
            self.temp_rotate_x = self.curr_x - self.down_x
            self.temp_rotate_y = self.curr_y - self.down_y
        elif event.buttons() == Qt.RightButton and self.view_mode == ZOOM_MODE:
            self.is_dragging = True
            self.temp_dolly = ( self.curr_y - self.down_y ) / 100.0
        elif event.buttons() == Qt.MiddleButton and self.view_mode == PAN_MODE:
            self.is_dragging = True
            self.temp_pan_x = self.curr_x - self.down_x
            self.temp_pan_y = self.curr_y - self.down_y
        elif self.edit_mode == MODE['EDIT_LANDMARK']:
            #print("edit 3d landmark mode")
            ## call unproject_mouse
            if self.show_model == True:
                on_background = self.hit_background_test(self.curr_x, self.curr_y)
                #print("on_background:", on_background)
                if on_background == True:
                    self.cursor_on_vertex = -1
                else:
                    closest_element = self.pick_element(self.curr_x, self.curr_y)
                    if closest_element is not None:
                        self.cursor_on_vertex = closest_element
                    else:
                        self.cursor_on_vertex = -1
            #if closest_element is not None:
                #print("closest element:", closest_element)

            #near, ray_direction = self.unproject_mouse(self.curr_x, self.curr_y)
           
            # call hit_test
            # if hit, set selected_landmark_idx
            # if selected_landmark_idx > -1, call update_landmark

        self.updateGL()

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
        dataset.edge_list.append([wire_start_index, wire_end_index])
        #print("wireframe", dataset.edge_list)
        dataset.pack_wireframe()
        self.edge_list = dataset.edge_list
        #print("wireframe", dataset.wireframe)
        dataset.save()
        

    def wheelEvent(self, event):
        #print("wheel event", event.angleDelta().y())
        self.dolly -= event.angleDelta().y() / 240.0
        self.updateGL()

    def set_ds_ops(self, ds_ops):
        #print("set_ds_ops")
        self.ds_ops = ds_ops
        #self.calculate_scale_and_pan()
        self.data_mode = DATASET_MODE
        average_shape = self.ds_ops.get_average_shape()
        scale = self.get_scale_from_object(average_shape)
        average_shape.rescale(scale)
        for obj in self.ds_ops.object_list:
            obj.rescale(scale)
            #obj.translate(-average_shape.get_centroid())
        self.edge_list = ds_ops.edge_list

    def set_object(self, object):
        #print("set_object 1",type(object))
        #object.unpack_landmark()
        #self.landmark_list = object.landmark_
        m_app = QApplication.instance()
        if isinstance(object, MdObject):
            self.object = object
            obj_ops = MdObjectOps(object)
        elif object is None:
            self.object = MdObject()
            obj_ops = MdObjectOps(self.object)
            #print("object is not MdObject")
        else:
            pass
        #print("set_object 2",type(obj_ops))
        self.dataset = object.dataset
        self.obj_ops = obj_ops
        #self.landmark_list = object.landmark_
        self.data_mode = OBJECT_MODE
        self.pan_x = self.pan_y = 0
        self.rotate_x = self.rotate_y = 0
        self.edge_list = self.dataset.unpack_wireframe()
        #print("edge_list:", self.edge_list)
        #self.landmark_list = object.landmark_list

        if object.threed_model.count() > 0:
            #print("object has 3d model", self, self.object, self.threed_model)
            #print("and no 3d model in view yet", self )
            filepath = object.threed_model[0].get_file_path(m_app.storage_directory)
            #print("3d model from:", filepath)
            self.set_threed_model(filepath)
        else:
            self.threed_model = None
        self.calculate_resize()
        self.updateGL()
        #print("data_mode:", self.data_mode)

    def get_scale_from_object(self, obj_ops):
        if len(obj_ops.landmark_list) == 0:
            return 1.0
        centroid_size = obj_ops.get_centroid_size()
        min_x, max_x = min( [ lm[0] for lm in obj_ops.landmark_list] ), max( [ lm[0] for lm in obj_ops.landmark_list] )
        min_y, max_y = min( [ lm[1] for lm in obj_ops.landmark_list] ), max( [ lm[1] for lm in obj_ops.landmark_list] )
        min_z, max_z = min( [ lm[2] for lm in obj_ops.landmark_list] ), max( [ lm[2] for lm in obj_ops.landmark_list] )
        #obj_ops.rescale(5)
        width = max_x - min_x
        if width == 0:
            width = 1
        height = max_y - min_y
        if height == 0:
            height = 1
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
        if file_name.split('.')[-1].lower() in MODEL_EXTENSION_LIST:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self.object_dialog is None:
            return

        file_path = event.mimeData().text()
        file_path = re.sub('file:///', '', file_path)
        self.set_threed_model(file_path)
        self.calculate_resize()
        if self.object_dialog is not None:
            self.object_dialog.set_object_name(Path(file_path).stem)
            self.object_dialog.enable_landmark_edit()

    def set_threed_model(self, file_path):
        if file_path.split('.')[-1].lower() == 'obj':
            #self.test_obj = OBJ('Estaingia_simulation_base_20221125.obj')
            self.threed_model = OBJ(file_path)
            self.fullpath = file_path
        self.updateGL()

    def initialize_frame_buffer(self, frame_buffer_id=0):
        #print("initialize_frame_buffer")
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, frame_buffer_id)
        gl.glClearDepth(1.0)
        gl.glDepthFunc(gl.GL_LESS)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_COLOR_MATERIAL)
        gl.glShadeModel(gl.GL_SMOOTH)

        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect_ratio = self.width() / self.height()
        glu.gluPerspective(45.0,aspect_ratio,0.1, 100.0) # 시야각, 종횡비, 근거리 클리핑, 원거리 클리핑
        gl.glMatrixMode(gl.GL_MODELVIEW)
        glut.glutInit(sys.argv)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def initializeGL(self):
        #print("initializeGL")
        self.initialize_frame_buffer()
        self.picker_buffer = self.create_picker_buffer()
        self.initialize_frame_buffer(self.picker_buffer)
        self.initialized = True
        if self.initialized == True and self.threed_model is not None and self.threed_model.generated == False:
            self.threed_model.generate()

        #self.test_obj = OBJ('Estaingia_simulation_base_20221125.obj')

    def paintGL(self):
        #print("paintGL")
        if self.edit_mode == WIREFRAME_MODE:
            self.draw_picker_buffer()

        self.draw_all()

    def draw_all(self):
        #print("draw_all")
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45.0, self.aspect, 0.1, 100.0)
        gl.glTranslatef(0, 0, -5.0 + self.dolly + self.temp_dolly)   # x, y, z 
        gl.glTranslatef((self.pan_x + self.temp_pan_x)/100.0, (self.pan_y + self.temp_pan_y)/-100.0, 0.0)
        gl.glRotatef(self.rotate_y + self.temp_rotate_y, 1.0, 0.0, 0.0)
        gl.glRotatef(self.rotate_x + self.temp_rotate_x, 0.0, 1.0, 0.0)
        #gl.glLoadIdentity()

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glClearColor(*COLOR['BACKGROUND'], 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        gl.glEnable(gl.GL_POINT_SMOOTH)
        if self.ds_ops is None and self.obj_ops is None:
            return
        
        # pan, rotate, dolly

        if self.data_mode == OBJECT_MODE:
            self.draw_object(self.obj_ops)
        else:
            self.draw_dataset(self.ds_ops)
        gl.glFlush()

    def draw_dataset(self, ds_ops):
        
        for obj in ds_ops.object_list:
            if obj.id in ds_ops.selected_object_id_list:
                object_color = COLOR['SELECTED_SHAPE']
            else:
                object_color = COLOR['NORMAL_SHAPE']
            self.draw_object(obj, landmark_as_sphere=False, color=object_color)
        if self.show_average:
            object_color = COLOR['AVERAGE_SHAPE']
            self.draw_object(ds_ops.get_average_shape(), landmark_as_sphere=True, color=object_color)

    def draw_object(self,object,landmark_as_sphere=True,color=COLOR['NORMAL_SHAPE']):
        #print("draw object", object, self.edge_list)
        current_buffer = gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)
        if landmark_as_sphere:
            if self.show_wireframe and len(self.edge_list) > 0:
                #print("draw wireframe",self.edge_list)
                for edge in self.edge_list:
                    #gl.glDisable(gl.GL_LIGHTING)
                    gl.glColor3f( *COLOR['WIREFRAME'])
                    gl.glBegin(gl.GL_LINE_STRIP)
                    #print(self.down_x, self.down_y, self.curr_x, self.curr_y)
                    for lm_idx in edge:
                        if lm_idx < len(object.landmark_list):
                            lm = object.landmark_list[lm_idx]
                            gl.glVertex3f(*lm)
                    gl.glEnd()

            lm_count = len(object.landmark_list)
            for i, lm in enumerate(object.landmark_list):
                gl.glPushMatrix()
                gl.glTranslate(*lm)
                #print("color: yellow")
                gl.glColor3f( *color )
                if i in [ self.selected_landmark_idx, self.wireframe_from_idx, self.wireframe_to_idx ]:
                    gl.glColor3f( *COLOR['SELECTED_LANDMARK'] )

                if current_buffer == self.picker_buffer and self.object_dialog is not None:
                    gl.glDisable(gl.GL_LIGHTING)
                    #print("color:",*self.lm_idx_to_color[i])
                    key = "lm_"+str(i)
                    #print("i:",i,"key:",key, "color:",self.lm_idx_to_color[key], "current_buffer:",current_buffer, "picker_buffer:",self.picker_buffer)
                    color = self.lm_idx_to_color[key]
                    #print(self.lm_idx_to_color, i, current_buffer)
                    gl.glColor3f( *[ c * 1.0 / 255 for c in color] )
                glut.glutSolidSphere(0.03, 10, 10)
                if current_buffer == self.picker_buffer:
                    gl.glEnable(gl.GL_LIGHTING)
                gl.glPopMatrix()

                if self.show_index:
                    gl.glDisable(gl.GL_LIGHTING)
                    gl.glColor3f( *COLOR['NORMAL_TEXT'] )
                    gl.glRasterPos3f(lm[0] + 0.05, lm[1] + 0.05, lm[2])
                    for letter in list(str(i+1)):
                        glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_12, ord(letter))
                    gl.glEnable(gl.GL_LIGHTING)

        else:
            gl.glPointSize(5)
            gl.glDisable(gl.GL_LIGHTING)
            gl.glColor3f( *color )
            gl.glBegin(gl.GL_POINTS)
            #gl.glColor3f( 1.0, 1.0, 0.0 )
            for lm in object.landmark_list:
                gl.glVertex3f(lm[0], lm[1], lm[2])
            gl.glEnd()
            gl.glEnable(gl.GL_LIGHTING)

        '''
        import pywavefront
        from pywavefront import visualization

        #[create a window and set up your OpenGl context]
        obj = pywavefront.Wavefront('Estaingia_simulation_base_20221125.obj')

        ##[inside your drawing loop]
        #visualization.draw(obj)
        '''

        # https://github.com/yarolig/OBJFileLoader
        #gl.glPushMatrix()
        #gl.glColor3f( *COLOR['RED'] )
        #gl.glTranslatef(box_x, box_y, box_z)
        if self.threed_model is not None and self.show_model is True:
            #print("view has threed_model", self.object_dialog, self, self.threed_model, self.threed_model.gl_list)
            self.threed_model.render()

            if self.cursor_on_vertex > -1:
                lm = self.threed_model.vertices[self.cursor_on_vertex]
                gl.glPushMatrix()
                gl.glTranslate(*lm)
                #print("color: yellow")
                gl.glColor3f( *COLOR['SELECTED_LANDMARK'] )
                glut.glutSolidSphere(0.03, 10, 10)
                gl.glPopMatrix()

            return
            if len(self.threed_model.landmark_list ) > 0:
                print("printing landmark:", self.threed_model.landmark_list, COLOR['NORMAL_SHAPE'])
                for idx in self.threed_model.landmark_list:
                    lm = self.threed_model.vertices[idx]
                    gl.glPushMatrix()
                    gl.glTranslate(*lm)
                    gl.glColor3f( *COLOR['NORMAL_SHAPE'] )
                    glut.glutSolidSphere(0.03, 10, 10)
                    gl.glPopMatrix()


        #gl.glPopMatrix()

    def create_picker_buffer(self):
        #print("create_picker_buffer")
        # Create a new framebuffer
        picker_buffer = gl.glGenFramebuffers(1)
        #print("picker_buffer:", self.picker_buffer)
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
        #print("draw_picker_buffer")
        # Now you can render to this framebuffer instead of the default one
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.picker_buffer)
        gl.glViewport(0, 0, self.width(), self.height())

        # Render your scene...
        #self.
        self.draw_all()

        # Don't forget to unbind the framebuffer when you're done to revert back to the default framebuffer
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def delete_picker_buffer(self):
        #gl.glDeleteFramebuffers(1, self.picker_buffer)
        gl.glDeleteTextures([self.texture_buffer])
        gl.glDeleteRenderbuffers([self.render_buffer])
        gl.glDeleteFramebuffers([self.picker_buffer])
        self.picker_buffer = None

    def resizeGL(self, width, height):
        #print("resizeGL")
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        self.aspect = width / float(height)
        glu.gluPerspective(45.0, self.aspect, 0.1, 100.0)
        #gl.glTranslatef(0, 0, 2.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

        if self.picker_buffer is not None and self.edit_mode == WIREFRAME_MODE:
            #print("resize picker buffer", width, height)

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

    def timeout(self):
        #print("timeout, auto_rotate:", self.auto_rotate)
        if self.auto_rotate == False:
            #print "no rotate"
            return
        if self.is_dragging:
            #print "dragging"
            return

        self.rotate_x += 0.5
        self.updateGL()

    def clear_object(self):
        #print("clear object")
        #print("clear oject")
        self.obj_ops = None
        self.object = None
        self.landmark_list = []
        #print("current buffer:", gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING))
        #gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        #gl.glFlush()
        self.updateGL()
        #self.data_mode = DATASET_MODE

    def hit_background_test(self, x, y):
        pixels = gl.glReadPixels(x, self.height()-y, 1, 1, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
#        print(pixels)
        r, g, b = struct.unpack('BBB', pixels)
        rgb_list = [r, g, b]
        bg_color = [int(255* c) for c in COLOR['BACKGROUND']]
        #print( bg_color, rgb_list)
        if bg_color == rgb_list:
            return True
        else:
            return False
        #print("hit test", x, y, rgb_tuple)


    def hit_test(self, x, y):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.picker_buffer)
        #gl.glReadBuffer(gl.GL_BACK)
        pixels = gl.glReadPixels(x, self.height()-y, 1, 1, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
#        print(pixels)
        r, g, b = struct.unpack('BBB', pixels)
        rgb_tuple = (r, g, b)
        #print("hit test", x, y, rgb_tuple)

        if rgb_tuple in self.color_to_lm_idx.keys():
            lm_idx = self.color_to_lm_idx[rgb_tuple]
            #print("hit test", x, y, rgb_tuple, lm_idx)
            #text, idx = lm_idx.split("_")
            return True, int(lm_idx)
        else:
            return False,-1

    def draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        for obj in self.objects:
            gl.glColor3ub(*self.object_to_color[obj.id])
            obj.draw()

    def initialize_colors(self):
        if self.obj_ops is None:
            pass
        self.color_to_lm_idx = {}
        self.lm_idx_to_color = {}
        for i in range(len(self.obj_ops.landmark_list)):
            while True:
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                if color not in self.color_to_lm_idx.keys():
                    break
            self.color_to_lm_idx[color] = str(i)
            self.lm_idx_to_color["lm_"+str(i)] = color

    def update_landmark_list(self):
        #self.landmark_list = copy.deepcopy(self.object_dialog.landmark_list)
        self.obj_ops.landmark_list = copy.deepcopy(self.landmark_list)
        return

        self.obj_ops.landmark_list = []
        for lm in self.landmark_list:
            x, y, z = lm[0], lm[1], lm[2]
            self.obj_ops.landmark_list.append([float(x),float(y),float(z)])

    def calculate_resize(self):
        #print("obj_ops:", self.obj_ops)
        #if len(self.landmark_list) == 0:
        #    return
        if self.threed_model is not None:
            #print("calculate resize, has threed_model")
            if self.initialized == True and self.threed_model.generated == False:
                self.threed_model.generate()
            #if len(self.landmark_list) > 0:
            #    print("are they the same?", self.landmark_list is self.obj_ops.landmark_list)
            #    print("calculate resize: self 1:", id(self.landmark_list), self.landmark_list[0] )
            #print("calculate resize: obj_ops 1:", id(self.obj_ops.landmark_list), self.obj_ops.landmark_list[0])
            #print("model center:", self.threed_model.center_x, self.threed_model.center_y, self.threed_model.center_z)
            self.obj_ops.move(-1 * self.threed_model.center_x, -1 * self.threed_model.center_y, -1 * self.threed_model.center_z)
            #if len(self.landmark_list) > 0:
            #    print("calculate resize: self 2:", id(self.landmark_list), self.landmark_list[0] )
            #print("calculate resize: obj_ops 2:", id(self.obj_ops.landmark_list), self.obj_ops.landmark_list[0])
            self.obj_ops.rescale(self.threed_model.scale)
            self.obj_ops.apply_rotation_matrix(self.threed_model.rotation_matrix)
            #print("calculate resize: obj_ops 3:", id(self.obj_ops.landmark_list), self.obj_ops.landmark_list[0])
            #pass
        else:
            self.obj_ops.landmark_list = copy.deepcopy(self.landmark_list)
            self.obj_ops.move_to_center()
            centroid_size = self.obj_ops.get_centroid_size()
            self.obj_ops.rescale_to_unitsize()
            scale = self.get_scale_from_object(self.obj_ops)
            self.obj_ops.rescale(scale)
            #self.auto_rotate = True
        self.updateGL()
        return

    def rotate(self, rotationX_rad, rotationY_rad, vertices ):
        #print(rotationX_rad, rotationY_rad)
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
        #print(rotationXMatrix)
        #print(rotationYMatrix)
        new_rotation_matrix = np.dot(rotationXMatrix, rotationYMatrix)
        self.rotation_matrix = np.dot(new_rotation_matrix, self.rotation_matrix)

        # Create a column of 1's with the same number of rows as vertices
        ones_column = np.ones((np.array(vertices).shape[0], 1))

        # Use numpy.hstack() to concatenate the vertices with the ones column
        vertices_with_ones = np.hstack(( vertices, ones_column))
        new_vertices_with_ones = np.dot(vertices_with_ones, self.rotation_matrix.T)
        new_vertices = new_vertices_with_ones[:, 0:3]

        return new_vertices

    def unproject_mouse(self, x, y):
        # Get the view and projection matrices from your OpenGL code
        modelview = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
        projection = gl.glGetDoublev(gl.GL_PROJECTION_MATRIX)
        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        # Unproject the mouse coordinates to get the 3D ray
        near = glu.gluUnProject(x, viewport[3] - y, 0.0, modelview, projection, viewport)
        far = glu.gluUnProject(x, viewport[3] - y, 1.0, modelview, projection, viewport)
        ray_direction = np.array(far) - np.array(near)
        ray_direction /= np.linalg.norm(ray_direction)
        return near, ray_direction

    def pick_element(self, x, y):
        near, ray_direction = self.unproject_mouse(x, y)
        
        # Initialize variables to keep track of the closest intersection
        closest_distance = float('inf')
        closest_element = None
        vert_is_closest = False

        faces = self.threed_model.faces
        vertices = self.threed_model.vertices
        # Iterate over the faces of the 3D object and check for ray-triangle intersection
        '''
        for face_entity in faces:
            #print(face)
            face = face_entity[0]
            #print("face:", face)
            v0, v1, v2 = np.array(vertices[face[0]-1]), np.array(vertices[face[1]-1]), np.array(vertices[face[2]-1])
            intersection_point, distance = self.ray_triangle_intersection(near, ray_direction, v0, v1, v2)

            # Check if there's a valid intersection and if it's closer than the current closest
            if intersection_point is not None and distance < closest_distance:
                closest_distance = distance
                closest_element = face
                #print("closest face:", closest_element)
        '''

        # Iterate over the vertices of the 3D object and check for distance to ray
        for i, vertex in enumerate(vertices):
            distance = self.distance_to_ray(near, ray_direction, np.array(vertex))

            # Check if the distance is within a threshold (pick radius) and if it's closer than the current closest
            pick_radius = 0.1  # Adjust this value according to your needs
            if distance is not None and distance < closest_distance and distance < pick_radius:
                closest_distance = distance
                closest_element = i
                vert_is_closest = True
                #print("closest vert:", closest_element)

        #if vert_is_closest:
        #    self.cursor_on_vertex = closest_element
        #else:
        #    self.cursor_on_vertex = -1

        return closest_element

    def ray_triangle_intersection(self, ray_origin, ray_direction, v0, v1, v2):
        # Compute the triangle's normal
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        normal /= np.linalg.norm(normal)

        # Check if the ray is parallel to the triangle (dot product of the ray direction and normal)
        epsilon = 1e-6
        if abs(np.dot(ray_direction, normal)) < epsilon:
            return None, None  # No intersection

        # Compute the distance from the ray origin to the plane containing the triangle
        d = np.dot(v0 - ray_origin, normal) / np.dot(ray_direction, normal)

        # Check if the intersection point is behind the ray origin
        if d < 0:
            return None, None  # No intersection

        # Compute the intersection point
        intersection_point = ray_origin + d * ray_direction

        # Check if the intersection point is inside the triangle
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
            # Intersection point is inside the triangle
            return intersection_point, d
        else:
            return None, None  # No intersection

    def distance_to_ray(self, ray_origin, ray_direction, point):
        # Calculate the vector from the ray origin to the point
        point_vector = point - ray_origin

        # Calculate the projection of point_vector onto the ray direction
        projection = np.dot(point_vector, ray_direction)

        # Check if the projection is negative (point is behind the ray origin)
        if projection < 0:
            return None

        # Calculate the distance to the ray
        distance = np.linalg.norm(point_vector - projection * ray_direction)

        return distance

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
        painter.fillRect(self.rect(), QBrush(as_qt_color(COLOR['BACKGROUND'])))

        if self.ds_ops is None:
            return

        if self.show_wireframe == True:
            painter.setPen(QPen(as_qt_color(COLOR['WIREFRAME']), 2))
            painter.setBrush(QBrush(as_qt_color(COLOR['WIREFRAME'])))

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
                painter.setPen(QPen(as_qt_color(COLOR['SELECTED_SHAPE']), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR['SELECTED_SHAPE'])))
            else:
                painter.setPen(QPen(as_qt_color(COLOR['NORMAL_SHAPE']), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR['NORMAL_SHAPE'])))
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
                painter.setPen(QPen(as_qt_color(COLOR['AVERAGE_SHAPE']), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR['AVERAGE_SHAPE'])))
                x = self._2canx(landmark[0])
                y = self._2cany(landmark[1])
                painter.drawEllipse(x-radius, y-radius, radius*2, radius*2)
                if self.show_index:
                    painter.drawText(x+10, y+10, str(idx+1))

    def _2canx(self, x):
        return int(x*self.scale + self.pan_x)
    def _2cany(self, y):
        return int(y*self.scale + self.pan_y)

class TPS:
    def __init__(self, filename, datasetname):
        self.filename = filename
        self.datasetname = datasetname
        self.dimension = 0
        self.nobjects = 0
        self.object_name_list = []
        self.landmark_str_list = []
        self.edge_list = []
        self.polygon_list = []
        self.propertyname_list = []
        self.property_list_list = []
        self.object_comment = {}
        self.landmark_data = {}
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

                # regular expression that finds the line "LM=xx comment", ignore case
                headerline = re.search('^\s*LM\s*=\s*(\d+)\s*(.*)', line, re.IGNORECASE)

                #headerline = re.search('^\s*[LM]+\s*=\s*(\d+)\s*(.*)', line)
                if headerline is not None:
                    #print("headerline:", headerline.group(1), headerline.group(2))
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
                            #print("data:", data)
                            data = []
                            object_id = ''
                            object_comment_1 = ''
                            object_comment_2 = ''
                            object_image_path = ''
                        landmark_count, object_comment_1 = int(headerline.group(1)), headerline.group(2).strip()
                        #print("landmark_count:", landmark_count, "object_count:", object_count, "comment:", comment)
                        object_count += 1
                    else:
                        currently_in_data_section = True
                        landmark_count, object_comment_1 = int(headerline.group(1)), headerline.group(2).strip()
                else:
                    dataline = re.search('^\s*(\w+)\s*=(.+)', line)
                    #print(line)
                    if dataline is None:
                        #print("actual data:", line)
                        point = [ float(x) for x in re.split('\s+', line)]
                        if len(point) > 2 and self.isNumber(point[2]):
                            threed += 1
                        else:
                            twod += 1
                        #print("point:", point)
                        if len(point)>1:
                            data.append(point)
                    elif dataline.group(1).lower() == "image":
                        #print("image:", dataline.group(2))
                        object_image_path = dataline.group(2)
                    elif dataline.group(1).lower() == "comment":
                        #print("comment:", dataline.group(2))
                        object_comment_2 = dataline.group(2)
                    elif dataline.group(1).lower() == "id":
                        #print("id:", dataline.group(2))
                        #object_id = dataline.group(2)
                        pass

            #print("aa")

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

            #print("bb", object_count, landmark_count)

            if object_count == 0 and landmark_count == 0:
                return None

            if threed > twod:
                self.dimension = 3
            else:
                self.dimension = 2
            
            #print ("dimension:", self.dimension)
            #print("object_count:", object_count)
            #print("landmark_count:", landmark_count)
            #print("object_name_list:", object_name_list)
            #print("object_comment:", object_comment)
            #print("objects:", objects)

            self.nobjects = len(object_name_list)
            self.nlandmarks = landmark_count
            self.landmark_data = objects
            self.object_name_list = object_name_list
            self.object_comment = object_comment
            #print(self.landmark_data.keys(), self.object_name_list)

            return dataset

class NTS:
    def __init__(self, filename, datasetname):
        self.filename = filename
        self.datasetname = datasetname
        self.dimension = 0
        self.nobjects = 0
        self.object_name_list = []
        self.landmark_str_list = []
        self.edge_list = []
        self.polygon_list = []
        self.propertyname_list = []
        self.property_list_list = []
        self.object_comment = {}
        self.landmark_data = {}
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
                headerline = re.search('^(\d+)(\s+)(\d+)(\w*)(\s+)(\d+)(\w*)(\s+)(\d+)(\s+)(\d*)(\s*)(\w+)=(\d+)(.*)', line)
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
                        #print("dim:", headerline.group(14))
                        self.dimension = int(headerline.group(14))
                    
                    headerline_processed = True
                    #print(headerline_processed, headerline.group(6), headerline.group(7), column_names_exist, column_names_read)
                    continue

                if headerline_processed == True and row_names_exist_in_separate_line == True and row_names_read == False:
                    row_names_list = re.split('\s+', line)
                    row_names_read = True
                    continue

                if headerline_processed == True and column_names_exist == True and column_names_read == False:
                    column_names_list = re.split('\s+', line)
                    column_names_read = True
                    continue

                if headerline_processed == True:
                    data_list = re.split('\s+', line)
                    if row_names_exist_at_row_beginning == True:
                        row_name = data_list.pop(0)
                    elif row_names_exist_at_row_ending == True:
                        row_name = data_list.pop(-1)
                    elif len(row_names_list) > 0:
                        row_name = row_names_list[current_object_count]
                    else:
                        row_name = self.datasetname + "_" + str(current_object_count+1)
                    # turn data_list into coordinates of landmarks based on dimension
                    data_list = [ float(x) for x in data_list ]
                    #print(data_list, len(data_list), self.dimension)
                    objects[row_name] = []
                    for idx in range(0,len(data_list),self.dimension):
                        #print point
                        #print("idx:", idx, "dimension:", self.dimension, "lm:", data_list[idx:idx+self.dimension])
                        objects[row_name].append(data_list[idx:idx+self.dimension])

                    #print(objects[row_name])
                    #objects[row_name] = data_list
                    object_name_list.append(row_name)
                    current_object_count += 1

            if total_object_count == 0 and landmark_count == 0:
                return None

            self.nobjects = len(object_name_list)
            self.nlandmarks = landmark_count
            self.landmark_data = objects
            self.object_name_list = object_name_list
            self.description = comments

            return dataset

class Morphologika:
    def __init__(self, filename, datasetname):
        self.filename = filename
        self.datasetname = datasetname
        self.dimension = 0
        self.nobjects = 0
        self.object_name_list = []
        self.landmark_str_list = []
        self.edge_list = []
        self.polygon_list = []
        self.propertyname_list = []
        self.property_list_list = []
        self.object_comment = {}
        self.landmark_data = {}
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
                dsl = re.search('(\w+)', line).group(0).lower()
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

        # abc
        objects = {}
        #object_landmark_list = []
        for i, name in enumerate(self.object_name_list):
            begin = i * self.nlandmarks
            count = self.nlandmarks
            # print begin, begin + count
            objects[name] = []
            for point in self.raw_data['rawpoints'][begin:begin + count]:
                #print point
                coords = re.split('\s+', point)
                objects[name].append(coords)

        self.landmark_data = objects

        self.edge_list = []
        self.polygon_list = []
        self.propertyname_list = []
        self.property_list_list = []

        if 'labels' in self.raw_data.keys():
            for line in self.raw_data['labels']:
                labels = re.split('\s+', line)
                for label in labels:
                    self.propertyname_list.append( label )
                    
        if 'labelvalues' in self.raw_data.keys():
            for line in self.raw_data['labelvalues']:
                property_list = re.split('\s+', line)
                self.property_list_list.append(property_list)

        if 'wireframe' in self.raw_data.keys():
            for line in self.raw_data['wireframe']:
                edge = [int(v) for v in re.split('\s+', line)]
                edge.sort()
                self.edge_list.append(edge)

        if 'polygons' in self.raw_data.keys():
            for line in self.raw_data['polygons']:
                poly = [int(v) for v in re.split('\s+', line)]
                poly.sort()
                self.polygon_list.append(poly)

        self.edge_list.sort()
        self.polygon_list.sort()
        return

class PicButton(QAbstractButton):
    def __init__(self, pixmap, pixmap_hover, pixmap_pressed, pixmap_disabled=None, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap
        self.pixmap_hover = pixmap_hover
        self.pixmap_pressed = pixmap_pressed
        if pixmap_disabled is None:
            result = pixmap_hover.copy()
            image = QtGui.QPixmap.toImage(result)
            grayscale = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
            pixmap_disabled = QtGui.QPixmap.fromImage(grayscale)
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
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 320, 180))
        self.move(self.parent.pos()+QPoint(100,100))
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
        if dist is not None:
            self.set_pixel_number(dist)

    def set_pixel_number(self, pixel_number):
        self.pixel_number = pixel_number
        # show number of pixel in calibration text 
        self.lblText1.setText("Enter the unit length in metric scale.")
        self.lblText2.setText("%d pixels are equivalent to:" % self.pixel_number)
        
    def btnOK_clicked(self):
        #self.parent.calibration_length = float(self.edtLength.text())
        #self.parent.calibration_unit = self.cbxUnit.currentText()
        self.parent.set_object_calibration( self.pixel_number, float(self.edtLength.text()),self.comboUnit.currentText())
        self.close()
    
    def btnCancel_clicked(self):
        self.close()

class DatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Modan2 - Dataset Information")
        self.parent = parent
        #print(self.parent.pos())
        #self.setGeometry(QRect(100, 100, 600, 400))
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        #self.move(self.parent.pos()+QPoint(100,100))

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
        #self.edtPolygons = QTextEdit()
        self.edtPropertyNameStr = QTextEdit()

        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addRow("Parent", self.cbxParent)
        self.main_layout.addRow("Dataset Name", self.edtDatasetName)
        self.main_layout.addRow("Description", self.edtDatasetDesc)
        self.main_layout.addRow("Dimension", dim_layout)
        self.main_layout.addRow("Wireframe", self.edtWireframe)
        self.main_layout.addRow("Baseline", self.edtBaseline)
        #self.main_layout.addRow("Polygons", self.edtPolygons)
        self.main_layout.addRow("Property Names", self.edtPropertyNameStr)


        self.btnOkay = QPushButton()
        self.btnOkay.setText("Save")
        self.btnOkay.clicked.connect(self.Okay)

        self.btnDelete = QPushButton()
        self.btnDelete.setText("Delete")
        self.btnDelete.clicked.connect(self.Delete)

        self.btnCancel = QPushButton()
        self.btnCancel.setText("Cancel")
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
        #self.edtPolygons.setText(dataset.polygons)
        self.edtPropertyNameStr.setText(dataset.propertyname_str)
    
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

    def Okay(self):
        if self.dataset is None:
            self.dataset = MdDataset()
        self.dataset.parent_id = self.cbxParent.currentData()
        self.dataset.dataset_name = self.edtDatasetName.text()
        self.dataset.dataset_desc = self.edtDatasetDesc.text()
        if self.rbtn2D.isChecked():
            self.dataset.dimension = 2
        elif self.rbtn3D.isChecked():
            self.dataset.dimension = 3
        self.dataset.wireframe = self.edtWireframe.toPlainText()
        self.dataset.baseline = self.edtBaseline.text()
        #self.dataset.polygons = self.edtPolygons.toPlainText()
        self.dataset.propertyname_str = self.edtPropertyNameStr.toPlainText()

        #self.data
        #print(self.dataset.dataset_desc, self.dataset.dataset_name)
        self.dataset.save()
        self.accept()

    def Delete(self):
        ret = QMessageBox.question(self, "", "Are you sure to delete this dataset?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
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
        self.setWindowTitle("Modan2 - Object Information")
        self.parent = parent
        #print(self.parent.pos())
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        #self.move(self.parent.pos()+QPoint(50,50))

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
        self.btnAddInput.setText("Add")
        self.inputLayout.addWidget(self.btnAddInput)
        self.inputX.returnPressed.connect(self.input_coords_process)
        self.inputY.returnPressed.connect(self.input_coords_process)
        self.inputZ.returnPressed.connect(self.input_coords_process)
        self.inputX.textChanged[str].connect(self.x_changed)
        self.btnAddInput.clicked.connect(self.input_coords_process)

        self.edtObjectName = QLineEdit()
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

        self.object_view_2d = ObjectViewer2D(self)
        self.object_view_2d.object_dialog = self
        self.object_view_2d.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        #self.image_label.clicked.connect(self.on_image_clicked)

        self.pixmap = QPixmap(1024,768)
        self.object_view_2d.setPixmap(self.pixmap)

        self.form_layout = QFormLayout()
        self.form_layout.addRow("Dataset Name", self.lblDataset)
        self.form_layout.addRow("Object Name", self.edtObjectName)
        self.form_layout.addRow("Object Desc", self.edtObjectDesc)
        self.form_layout.addRow("Landmarks", self.edtLandmarkStr)
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
        self.cbxShowIndex.setText("Index")
        self.cbxShowIndex.setChecked(True)
        self.cbxShowWireframe = QCheckBox()
        self.cbxShowWireframe.setText("Wireframe")
        self.cbxShowWireframe.setChecked(True)
        self.cbxShowBaseline = QCheckBox()
        self.cbxShowBaseline.setText("Baseline")
        self.cbxShowBaseline.setChecked(True)
        self.cbxShowBaseline.hide()
        self.cbxAutoRotate = QCheckBox()
        self.cbxAutoRotate.setText("Rotate")
        self.cbxAutoRotate.setChecked(False)
        self.cbxShowModel = QCheckBox()
        self.cbxShowModel.setText("3D Model")
        self.cbxShowModel.setChecked(True)
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
        self.right_middle_layout.addWidget(self.cbxShowBaseline)
        self.right_middle_layout.addWidget(self.cbxShowModel)
        self.right_middle_layout.addWidget(self.cbxAutoRotate)
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

        self.btnOkay = QPushButton()
        self.btnOkay.setText("Save")
        self.btnOkay.clicked.connect(self.Okay)
        self.btnDelete = QPushButton()
        self.btnDelete.setText("Delete")
        self.btnDelete.clicked.connect(self.Delete)
        self.btnCancel = QPushButton()
        self.btnCancel.setText("Cancel")
        self.btnCancel.clicked.connect(self.Cancel)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnOkay)
        btn_layout.addWidget(self.btnDelete)
        btn_layout.addWidget(self.btnCancel)

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
        self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        self.cbxAutoRotate.stateChanged.connect(self.auto_rotate_state_changed)
        self.cbxShowModel.stateChanged.connect(self.show_model_state_changed)

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

    def show_index_state_changed(self, int):
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
        self.calibrate_dlg = CalibrationDialog(self, dist)
        self.calibrate_dlg.setModal(True)
        self.calibrate_dlg.exec_()

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
            self.dataset.unpack_propertyname_str()
            for propertyname in self.dataset.propertyname_list:
                self.edtPropertyList.append( QLineEdit() )
                self.form_layout.addRow(propertyname, self.edtPropertyList[-1])
        #self.inputX.setFixedWidth(input_width)
        #self.inputY.setFixedWidth(input_width)
        #self.inputZ.setFixedWidth(input_width)
        #self.btnAddInput.setFixedWidth(input_width)

    def set_object(self, object):
        #print("set_object", object.object_name, object.dataset.dimension)
        if object is not None:
            self.object = object
            self.edtObjectName.setText(object.object_name)
            self.edtObjectDesc.setText(object.object_desc)
            #self.edtLandmarkStr.setText(object.landmark_str)
            object.unpack_landmark()
            self.landmark_list = copy.deepcopy(object.landmark_list)
            self.edge_list = object.dataset.unpack_wireframe()
            #for lm in self.landmark_list:
            #    self.show_landmark(*lm)
            #self.show_landmarks()

        if self.dataset.dimension == 3:
            #print("set_object 3d")
            self.object_view = self.object_view_3d
            self.object_view.auto_rotate = False
            #obj_ops = MdObjectOps(object)
            #self.object_view.set_dataset(object.dataset)
            #self.btnLandmark.setDisabled(True)
            self.btnCalibration.setDisabled(True)
            self.cbxAutoRotate.show()
            if object is not None:
                if object.threed_model is not None and len(object.threed_model) > 0:
                    self.enable_landmark_edit()
                else:
                    self.disable_landmark_edit()
                #print("object dialog self.landmark_list in set object 3d", self.landmark_list)
                self.object_view.set_object(object)
                self.object_view.landmark_list = self.landmark_list
                self.object_view.update_landmark_list()
                self.object_view.calculate_resize()
                #self.object_view.landmark_list = self.landmark_list
        else:
            #print("set_object 2d")
            self.object_view = self.object_view_2d
            self.cbxAutoRotate.hide()
            if object is not None:
                if object.image is not None and len(object.image) > 0:
                    img = object.image[0]
                    image_path = img.get_file_path(self.m_app.storage_directory)
                    #check if image_path exists
                    if os.path.exists(image_path):
                        self.object_view.set_image(image_path)
                    self.btnCalibration.setEnabled(True)
                    self.enable_landmark_edit()
                else:
                    self.btnCalibration.setDisabled(True)
                    self.disable_landmark_edit()
                #elif len(self.landmark_list) > 0:
                #print("objectdialog self.landmark_list in set object 2d", self.landmark_list)
                self.object_view.set_object(object)
                self.object_view.landmark_list = self.landmark_list
                self.object_view.update_landmark_list()
                self.object_view.calculate_resize()

        if len(self.dataset.propertyname_list) >0:
            self.object.unpack_property()
            self.dataset.unpack_propertyname_str()
            for idx, propertyname in enumerate(self.dataset.propertyname_list):
                if idx < len(object.property_list):
                    self.edtPropertyList[idx].setText(object.property_list[idx])

            #self.object_view_3d.landmark_list = self.landmark_list
        #self.set_dataset(object.dataset)
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

        if self.object is None:
            self.object = MdObject()
        self.object.dataset_id = self.dataset.id
        self.object.object_name = self.edtObjectName.text()
        self.object.object_desc = self.edtObjectDesc.toPlainText()
        #self.object.landmark_str = self.edtLandmarkStr.text()
        self.object.landmark_str = self.make_landmark_str()
        #print("scale:", self.object.pixels_per_mm)
        if self.dataset.propertyname_str is not None and self.dataset.propertyname_str != "":
            self.object.property_str = ",".join([ edt.text() for edt in self.edtPropertyList ])

        self.object.save()
        if self.object_view_2d.fullpath is not None and self.object.image.count() == 0:
            md_image = MdImage()
            md_image.object_id = self.object.id
            md_image.load_file_info(self.object_view_2d.fullpath)
            new_filepath = md_image.get_file_path( self.m_app.storage_directory)
            if not os.path.exists(os.path.dirname(new_filepath)):
                os.makedirs(os.path.dirname(new_filepath))
            #print("save object new filepath:", new_filepath)
            shutil.copyfile(self.object_view_2d.fullpath, new_filepath)
            md_image.save()
        elif self.object_view_3d.fullpath is not None and self.object.threed_model.count() == 0:
            md_3dmodel = MdThreeDModel()
            md_3dmodel.object_id = self.object.id
            md_3dmodel.load_file_info(self.object_view_3d.fullpath)
            new_filepath = md_3dmodel.get_file_path( self.m_app.storage_directory)
            if not os.path.exists(os.path.dirname(new_filepath)):
                os.makedirs(os.path.dirname(new_filepath))
            #print("save object new filepath:", new_filepath)
            shutil.copyfile(self.object_view_3d.fullpath, new_filepath)
            md_3dmodel.save()

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

    def Delete(self):
        ret = QMessageBox.question(self, "", "Are you sure to delete this object?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            if self.object.image.count() > 0:
                image_path = self.object.image[0].get_file_path(self.m_app.storage_directory)
                if os.path.exists(image_path):
                    os.remove(image_path)
            self.object.delete_instance()
        #self.delete_dataset()
        self.accept()

    def Okay(self):
        self.save_object()
        self.accept()

    def Cancel(self):
        self.reject()

    def resizeEvent(self, event):
        #print("Window has been resized",self.image_label.width(), self.image_label.height())
        #self.pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        #self.edtObjectDesc.resize(self.edtObjectDesc.height(),300)
        #self.image_label.setPixmap(self.pixmap)
        QDialog.resizeEvent(self, event)

class DatasetAnalysisDialog(QDialog):
    def __init__(self,parent,dataset):
        super().__init__()
        self.setWindowTitle("Modan2 - Dataset Analysis")
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.parent = parent
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        self.color_list = self.default_color_list[:]
        self.read_settings()
        #self.setGeometry(QRect(100, 100, 1400, 800))
        
        self.ds_ops = None
        self.object_hash = {}
        
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
        self.cbxShowIndex.setText("Index")
        self.cbxShowIndex.setChecked(True)
        self.cbxShowWireframe = QCheckBox()
        self.cbxShowWireframe.setText("Wireframe")
        self.cbxShowWireframe.setChecked(False)
        self.cbxShowBaseline = QCheckBox()
        self.cbxShowBaseline.setText("Baseline")
        self.cbxShowBaseline.setChecked(False)
        self.cbxShowAverage = QCheckBox()
        self.cbxShowAverage.setText("Average")
        self.cbxShowAverage.setChecked(True)
        self.cbxAutoRotate = QCheckBox()
        self.cbxAutoRotate.setText("Rotate")
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

        self.table_tab.addTab(self.tableView1, "Objects")
        self.table_tab.addTab(self.tableView2, "Groups")
        self.table_layout.addWidget(self.table_tab)

        self.table_control_widget = QWidget()
        self.table_control_layout = QHBoxLayout()
        self.table_control_widget.setLayout(self.table_control_layout)
        self.btnSelectAll = QPushButton()
        self.btnSelectAll.setText("All")
        self.btnSelectAll.clicked.connect(self.select_all)
        self.btnSelectNone = QPushButton()
        self.btnSelectNone.setText("None")
        self.btnSelectNone.clicked.connect(self.select_none)
        self.btnSelectInvert = QPushButton()
        self.btnSelectInvert.setText("Invert")
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
        self.cbxDepthShade.setText("Depth Shade")
        self.cbxDepthShade.setChecked(False)
        self.cbxDepthShade.toggled.connect(self.on_chart_dim_changed)
        self.cbxLegend = QCheckBox()
        self.cbxLegend.setText("Legend")
        self.cbxLegend.setChecked(False)
        self.cbxLegend.toggled.connect(self.on_chart_dim_changed)
        self.cbxAxisLabel = QCheckBox()
        self.cbxAxisLabel.setText("Axis")
        self.cbxAxisLabel.setChecked(True)
        self.cbxAxisLabel.toggled.connect(self.on_chart_dim_changed)
        self.gbChartDim = QGroupBox()
        self.gbChartDim.setTitle("Chart")
        self.gbChartDim.setLayout(QHBoxLayout())
        self.gbChartDim.layout().addWidget(self.rb2DChartDim)
        self.gbChartDim.layout().addWidget(self.rb3DChartDim)
        self.gbChartDim.layout().addWidget(self.cbxDepthShade)
        self.gbChartDim.layout().addWidget(self.cbxLegend)
        self.gbChartDim.layout().addWidget(self.cbxAxisLabel)
        self.gbGroupBy = QGroupBox()
        self.gbGroupBy.setTitle("Group By")
        self.gbGroupBy.setLayout(QHBoxLayout())
        self.comboPropertyName = QComboBox()
        self.comboPropertyName.setCurrentIndex(-1)
        self.comboPropertyName.currentIndexChanged.connect(self.propertyname_changed)
        self.gbGroupBy.layout().addWidget(self.comboPropertyName)

        self.plot_control_layout2.addWidget(self.gbChartDim)
        self.plot_control_layout2.addWidget(self.gbGroupBy)

        self.btnChartOptions = QPushButton("Chart Options")
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

        self.plot_tab.addTab(self.plot_data, "Result table")
        self.plot_tab.addTab(self.rotation_matrix_data, "Rotation matrix")
        self.plot_tab.addTab(self.eigenvalue_data, "Eigenvalues")


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
        self.btnSuperimpose = QPushButton("Superimpose")
        self.btnSuperimpose.clicked.connect(self.on_btnSuperimpose_clicked)
        self.gbSuperimposition = QGroupBox()
        self.gbSuperimposition.setTitle("Superimposition")
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
        self.btnAnalyze = QPushButton("Perform Analysis")
        self.btnAnalyze.clicked.connect(self.on_btn_analysis_clicked)
        self.middle_bottom_layout.addWidget(self.gbAnalysis)
        self.middle_bottom_layout.addWidget(self.btnAnalyze)

        self.empty_widget = QWidget()
        self.btnSaveResults = QPushButton("Save Results")
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
        for i in range(len(self.color_list)):
            self.color_list[i] = self.m_app.settings.value("DataPointColor/"+str(i), self.default_color_list[i])

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
            obj.unpack_property()
            #print("property:", obj.property_list)
            lm_count = len(obj.landmark_list)
            #print("prev_lm_count:", prev_lm_count, "lm_count:", lm_count)
            if prev_lm_count != lm_count and prev_lm_count != -1:
                # show messagebox and close the window
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Error: landmark count is not consistent")
                msg.setWindowTitle("Error")
                msg.exec_()
                self.close()
                return False
            prev_lm_count = lm_count

        self.comboPropertyName.clear()
        self.comboPropertyName.addItem("Select Property")
        if len(self.dataset.propertyname_list) > 0:
            for propertyname in self.dataset.propertyname_list:
                self.comboPropertyName.addItem(propertyname)
                #self.comboAxis2.addItem(propertyname)
        self.comboPropertyName.setCurrentIndex(0)
        self.comboPropertyName.currentIndexChanged.connect(self.propertyname_changed)
        if self.dataset.dimension == 3:
            self.cbxAutoRotate.show()
        else:
            self.cbxAutoRotate.hide()

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
        print("on_btnSuperimpose_clicked")

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
        filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filename_candidate, "Excel format (*.xlsx)")
        if filename:
            #print("filename:", filename)
            doc = xlsxwriter.Workbook(filename)
            
            # PCA result
            header = [ "object_name", *self.ds_ops.propertyname_list ]
            header.extend( [self.analysis_type[:2]+str(i+1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))] )
            worksheet = doc.add_worksheet("Result coordinates")
            row_index = 0
            column_index = 0

            for colname in header:
                worksheet.write(row_index, column_index, colname )
                column_index+=1
            
            new_coords = self.analysis_result.rotated_matrix.tolist()
            for i, obj in enumerate(self.ds_ops.object_list):
                worksheet.write(i+1, 0, obj.object_name )
                #print(obj.property_list)
                for j, property in enumerate(obj.property_list):
                    worksheet.write(i+1, j+1, property )

                for k, val in enumerate(new_coords[i]):
                    worksheet.write(i+1, k+len(obj.property_list)+1, val )
                    #self.plot_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))

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

            doc.close()
        #print("on_btnSaveResults_clicked")
        
    def show_index_state_changed(self, int):
        if self.cbxShowIndex.isChecked():
            self.lblShape.show_index = True
            #print("show index CHECKED!")
        else:
            self.lblShape.show_index = False
            #print("show index UNCHECKED!")
        self.lblShape.update()

    def show_average_state_changed(self, int):
        if self.cbxShowAverage.isChecked():
            self.lblShape.show_average = True
            #print("show index CHECKED!")
        else:
            self.lblShape.show_average = False
            #print("show index UNCHECKED!")
        self.lblShape.update()

    def auto_rotate_state_changed(self, int):
        #print("auto_rotate_state_changed", self.cbxAutoRotate.isChecked())
        if self.cbxAutoRotate.isChecked():
            self.lblShape.auto_rotate = True
            #print("auto rotate CHECKED!")
        else:
            self.lblShape.auto_rotate = False
            #print("auto rotate UNCHECKED!")
        self.lblShape.update()

    def show_wireframe_state_changed(self, int):
        if self.cbxShowWireframe.isChecked():
            self.lblShape.show_wireframe = True
            #print("show index CHECKED!")
        else:
            self.lblShape.show_wireframe = False
            #print("show index UNCHECKED!")
        self.lblShape.update()

    def show_baseline_state_changed(self, int):
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
            print("procrustes superimposition failed")
            return
        self.show_object_shape()

        if self.dataset.object_list is None or len(self.dataset.object_list) < 5:
            print("too small number of objects for PCA analysis")            
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
        self.propertyname_index = self.comboPropertyName.currentIndex() -1
        self.scatter_data = {}
        self.scatter_result = {}
        SCATTER_SMALL_SIZE = 30
        SCATTER_LARGE_SIZE = 60

        key_list = []
        key_list.append('__default__')
        self.scatter_data['__default__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':'blue', 'size':SCATTER_SMALL_SIZE}
        if len(self.selected_object_id_list) > 0:
            self.scatter_data['__selected__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':'red', 'size':SCATTER_LARGE_SIZE}
            key_list.append('__selected__')

        for obj in self.ds_ops.object_list:
            key_name = '__default__'

            if obj.id in self.selected_object_id_list:
                key_name = '__selected__'
            elif self.propertyname_index > -1 and self.propertyname_index < len(obj.property_list):
                key_name = obj.property_list[self.propertyname_index]

            if key_name not in self.scatter_data.keys():
                self.scatter_data[key_name] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'property':key_name, 'symbol':'', 'color':'', 'size':SCATTER_SMALL_SIZE}

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
            if show_legend:
                self.ax2.legend(self.scatter_result.values(), self.scatter_result.keys(), loc='upper left', bbox_to_anchor=(1.05, 1))
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
                    #print("ret", ret)
            if show_legend:
                self.ax3.legend(self.scatter_result.values(), self.scatter_result.keys(), loc='upper left', bbox_to_anchor=(1.05, 1))
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
        #print("header", header)
        self.plot_data.setColumnCount(len(header)+1)
        self.plot_data.setHorizontalHeaderLabels(["Name"] + header)

        new_coords = self.analysis_result.rotated_matrix.tolist()
        self.plot_data.setColumnCount(len(new_coords[0])+1)
        for i, obj in enumerate(self.ds_ops.object_list):
            self.plot_data.insertRow(i)
            self.plot_data.setItem(i, 0, QTableWidgetItem(obj.object_name))
            for j, val in enumerate(new_coords[i]):
                self.plot_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))

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


    def show_pca_result_pyqtgraph(self):
        self.plot_widget.clear()

        x_val = []
        y_val = []
        data = []
        symbol = []
        pen = []

        # get axis1 and axis2 value from comboAxis1 and 2 index
        axis1 = self.comboAxis1.currentIndex() +1
        axis2 = self.comboAxis2.currentIndex() +1
        #print("axis1: ", axis1) +1
        #print("axis2: ", axis2)
        flip_axis1 = self.cbxFlipAxis1.isChecked()
        if flip_axis1:
            flip_axis1 = -1.0
        else:
            flip_axis1 = 1.0

        flip_axis2 = self.cbxFlipAxis2.isChecked()
        if flip_axis2:
            flip_axis2 = -1.0
        else:
            flip_axis2 = 1.0

        symbol_candidate = ['o','x','+','s','d','v','^','<','>','p','h']
        color_candidate = ['r','b','c','m','y','k','w','g']
        prop_list = []
        symbol_list = []
        self.propertyname_index = self.comboPropertyName.currentIndex()

        for obj in self.ds_ops.object_list:
            x_val.append( flip_axis1 * obj.pca_result[axis1])
            y_val.append( flip_axis2 * obj.pca_result[axis2])
            data.append(obj)
            curr_symbol = ''
            curr_color = ''
            #print("property_index:",self.property_index,"len(obj.property_list):",len(obj.property_list),"obj.property_list:",obj.property_list)
            if self.propertyname_index > -1:
                if self.propertyname_index < len(obj.property_list):
                    prop = obj.property_list[self.propertyname_index]
                    if prop not in prop_list:
                        prop_list.append(prop)
                    index = prop_list.index(prop)
                    curr_symbol = symbol_candidate[index]
                    curr_color = color_candidate[index]
            else:
                curr_symbol = symbol_candidate[0]
                curr_color = color_candidate[0]


            #print("obj.id:",obj.id,"self.selected_object_id_list:",self.selected_object_id_list)
            if obj.id in self.selected_object_id_list:
                curr_symbol = 'o'
                pen.append(pg.mkPen(color='b', width=1))
            else:
                if curr_symbol == '':
                    curr_symbol = 'x'
                pen.append(pg.mkPen(color=curr_color, width=1))
            symbol_list.append(curr_symbol)

        #scatter = MyPlotItem(size=10, brush=pg.mkBrush(255, 255, 255, 120),hoverable=True,hoverPen=pg.mkPen(color='r', width=2))
        self.scatter_item = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(255, 255, 255, 120),hoverable=True,hoverPen=pg.mkPen(color='r', width=2))
        self.scatter_item.addPoints(x=x_val, y=y_val, data=data, symbol=symbol_list, pen=pen)

        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("PCA Result")
        self.plot_widget.setLabel("left", "PC2")
        self.plot_widget.setLabel("bottom", "PC1")
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)
        ret = self.plot_widget.addItem(self.scatter_item)
        self.scatter_item.sigClicked.connect(self.on_scatter_item_clicked)
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.plot_widget.scene().sigMouseClicked.connect(self.on_mouse_clicked)
        #print("ret:",ret)
        #self.plot_widget.plot(x=x_val, y=y_val, pen=pg.mkPen(width=2, color='r'), name="plot1")

        '''
        https://stackoverflow.com/questions/48687464/how-to-set-equal-scale-for-axes-in-pyqtgraph-plot

        1)
        import pyqtgraph as pg
        y = range(0, 100)
        x = range(0, 100)
        plt = pg.plot(x, y, pen='r')
        plt.setFixedSize(1000, 1000)
        plt.showGrid(x=True, y=True)

        2)
        import pyqtgraph as pg
        import numpy as np
        a = np.linspace(0,2*np.pi)
        x =  2+np.cos(a)
        y = -1+np.sin(a)
        plt = pg.plot(x, y, pen='r')
        plt.setAspectLocked()
        plt.showGrid(x=True, y=True)
        pg.QtGui.QApplication.exec_()
        '''


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
        #print(obj, obj.property_list, property_index)
        for obj in dataset_ops.object_list:
            datum = []
            for lm in obj.landmark_list:
                datum.extend(lm)
            datamatrix.append(datum)
            category_list.append(obj.property_list[property_index])

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

        self.property_list = []
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
                obj.unpack_property()
                #print(obj.property_list)
                item3 = QStandardItem(obj.property_list[self.propertyname_index])
                if obj.property_list[self.propertyname_index] not in self.property_list:
                    self.property_list.append(obj.property_list[self.propertyname_index])
                    p_item0 = QStandardItem()
                    p_item0.setCheckable(True)
                    p_item0.setCheckState(Qt.Checked)
                    self.property_model.appendRow([p_item0,QStandardItem(obj.property_list[self.propertyname_index])])
                #self.property_list.append(obj.property_list[self.propertyname_index])
                self.object_model.appendRow([item0,item1,item2,item3] )
            else:
                self.object_model.appendRow([item0,item1,item2] )
        

    def reset_tableView(self):
        self.property_model = QStandardItemModel()
        self.property_model.setColumnCount(2)
        self.property_model.setHorizontalHeaderLabels(["", "Group"])
        self.tableView2.setModel(self.property_model)

        self.tableView2.setColumnWidth(0, 20)
        self.tableView2.setColumnWidth(1, 200)
        header2 = self.tableView2.horizontalHeader()
        header2.setSectionResizeMode(0, QHeaderView.Fixed)
        header2.setSectionResizeMode(1, QHeaderView.Stretch)


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

        if self.propertyname_index >= 0:
            self.object_model.setColumnCount(4)
            self.object_model.setHorizontalHeaderLabels(["", "ID", "Name", self.propertyname])
            self.tableView1.setColumnWidth(3, 150)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            self.property_model.setHorizontalHeaderLabels(["", self.propertyname])
        
        self.tableView1.setStyleSheet("QTreeView::item:selected{background-color: palette(highlight); color: palette(highlightedText);};")

    '''
    def on_tableView_clicked(self, index):
        self.selected_object_id_list = self.get_selected_object_id_list()
        #if len(self.selected_object_id_list) == 0:
        #    return
    '''

    def on_object_selection_changed(self, selected, deselected):
        if self.selection_changed_off:
            pass
        else:
            self.selected_object_id_list = self.get_selected_object_id_list()
            #if len(self.selected_object_id_list) == 0:
            #    return
            #print("object_id:",object_id, type(object_id))
            #for 
            #for object_id in self.selected_object_id_list:
                #print("selected object id:",object_id)
            #object_id = selected_object_list[0].id
            self.show_analysis_result()
            self.ds_ops.selected_object_id_list = self.selected_object_id_list
            self.show_object_shape()

        
        #self.selected_object = MdObject.get_by_id(object_id)
        #print("selected_object:",self.selected_object)
        #self.show_object(self.selected_object)

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
        self.setWindowTitle("Modan2 - Export")
        self.parent = parent
        #print(self.parent.pos())
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()

        self.lblDatasetName = QLabel("Dataset Name")
        self.lblDatasetName.setMaximumHeight(20)
        self.edtDatasetName = QLineEdit()
        self.edtDatasetName.setMaximumHeight(20)
        self.lblObjectList = QLabel("Object List")
        self.lblExportList = QLabel("Export List")
        self.lblObjectList.setMaximumHeight(20)
        self.lblExportList.setMaximumHeight(20)
        self.lstObjectList = QListWidget()
        self.lstExportList = QListWidget()
        self.lstObjectList.setMinimumHeight(400)
        self.lstExportList.setMinimumHeight(400)
        self.btnExport = QPushButton("Export")
        self.btnExport.clicked.connect(self.export_dataset)
        self.btnCancel = QPushButton("Cancel")
        self.btnCancel.clicked.connect(self.close)
        self.btnMoveRight = QPushButton(">")
        self.btnMoveRight.clicked.connect(self.move_right)
        self.btnMoveLeft = QPushButton("<")
        self.btnMoveLeft.clicked.connect(self.move_left)

        self.lblExport = QLabel("Export Format")
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

        self.lblSuperimposition = QLabel("Superimposition")
        self.rbProcrustes = QRadioButton("Procrustes")
        self.rbProcrustes.clicked.connect(self.on_rbProcrustes_clicked)
        self.rbProcrustes.setEnabled(True)
        self.rbProcrustes.setChecked(True)
        self.rbBookstein = QRadioButton("Bookstein")
        self.rbBookstein.clicked.connect(self.on_rbBookstein_clicked)
        self.rbBookstein.setEnabled(False)
        self.rbBookstein.setChecked(False)
        self.rbRFTRA = QRadioButton("RFTRA")
        self.rbRFTRA.clicked.connect(self.on_rbRFTRA_clicked)
        self.rbRFTRA.setEnabled(False)
        self.rbRFTRA.setChecked(False)
        self.rbNone = QRadioButton("None")
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

            filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filename_candidate, "TPS format (*.tps)")
            if filename:
                # open text file
                with open(filename, 'w') as f:
                    for object in object_list:
                        f.write('LM={}\t{}\n'.format(len(object.landmark_list),object.object_name))
                        for lm in object.landmark_list:
                            if self.ds_ops.dimension == 2:
                                f.write('{}\t{}\n'.format(*lm))
                            else:
                                f.write('{}\t{}\t{}\n'.format(*lm))

        elif self.rbMorphologika.isChecked():
            filename_candidate = '{}_{}.txt'.format(self.ds_ops.dataset_name, date_str)
            filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filename_candidate, "Morphologika format (*.txt)")
            if filename:
                result_str = ""
                result_str += "[individuals]" + NEWLINE + str(len(self.ds_ops.object_list)) + NEWLINE
                result_str += "[landmarks]" + NEWLINE + str(len(self.ds_ops.object_list[0].landmark_list)) + NEWLINE
                result_str += "[Dimensions]" + NEWLINE + str(self.ds_ops.dimension) + NEWLINE
                label_values = "[labels]" + NEWLINE + "\t".join(self.dataset.propertyname_list) + NEWLINE
                label_values += "[labelvalues]" + NEWLINE
                rawpoint_values = "[rawpoints]" + NEWLINE
                name_values = "[names]" + NEWLINE
                for mo in self.ds_ops.object_list:
                    label_values += '\t'.join(mo.property_list).strip() + NEWLINE
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

                # open text file
                with open(filename, 'w') as f:
                    f.write(result_str)
        self.close()

class ImportDatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Modan2 - Import")
        self.parent = parent
        #print(self.parent.pos())
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        #self.setGeometry(QRect(100, 100, 600, 400))
        #self.move(self.parent.pos()+QPoint(100,100))

        # add file open dialog
        self.btnOpenFile = QPushButton("Open File")
        self.btnOpenFile.clicked.connect(self.open_file)
        self.edtFilename = QLineEdit()
        self.edtFilename.setReadOnly(True)
        self.edtFilename.setText("")
        self.edtFilename.setPlaceholderText("Select a file to import")
        self.edtFilename.setMinimumWidth(400)
        self.edtFilename.setMaximumWidth(400)
        self.edtFilename.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # add file type checkbox group with TPS, X1Y1, Morphologika.
        self.chkFileType = QButtonGroup()
        self.rbnTPS = QRadioButton("TPS")
        self.rbnNTS = QRadioButton("NTS")
        self.rbnX1Y1 = QRadioButton("X1Y1")
        self.rbnMorphologika = QRadioButton("Morphologika")
        self.rbnX1Y1.setDisabled(True)
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

        # add dataset name edit
        self.edtDatasetName = QLineEdit()
        self.edtDatasetName.setText("")
        self.edtDatasetName.setPlaceholderText("Dataset Name")
        self.edtDatasetName.setMinimumWidth(400)
        self.edtDatasetName.setMaximumWidth(400)
        self.edtDatasetName.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                
        # add object count edit
        self.edtObjectCount = QLineEdit()
        self.edtObjectCount.setReadOnly(True)
        self.edtObjectCount.setText("")
        self.edtObjectCount.setPlaceholderText("Object Count")
        self.edtObjectCount.setMinimumWidth(100)
        self.edtObjectCount.setMaximumWidth(100)
        self.edtObjectCount.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.btnImport = QPushButton("Excute Import")
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
        self.main_layout.addRow("File", self.btnOpenFile)
        #self.main_layout.addRow("File Type", self.cbxFileType)
        self.main_layout.addRow("File Type", self.gbxFileType)
        self.main_layout.addRow("Dataset Name", self.edtDatasetName)
        self.main_layout.addRow("Object Count", self.edtObjectCount)
        self.main_layout.addRow("Import", self.btnImport)
        self.main_layout.addRow("Progress", self.prgImport)

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/ImportDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos()+QPoint(50,50))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/ImportDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.*)")
        if filename:
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
            elif self.file_ext.lower() == ".nts":
                self.rbnNTS.setChecked(True)
                self.edtObjectCount.setText("")
                self.file_type_changed()
            elif self.file_ext.lower() == ".x1y1":
                self.rbnX1Y1.setChecked(True)
                self.file_type_changed()
            elif self.file_ext.lower() == ".txt":
                self.rbnMorphologika.setChecked(True)
                self.file_type_changed()
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
                QMessageBox.warning(self, "Warning", "File type not supported.")
                return
            #else:
    
    def file_type_changed(self):
        pass

    def import_file(self):

        filename = self.edtFilename.text()
        filetype = self.chkFileType.checkedButton().text()
        datasetname = self.edtDatasetName.text()
        objectcount = self.edtObjectCount.text()
        import_data = None
        if filetype == "TPS":
            import_data = TPS(filename, datasetname)
        elif filetype == "NTS":
            import_data = NTS(filename, datasetname)
        elif filetype == "Morphologika":
            import_data = Morphologika(filename, datasetname)

        if import_data is None:
            return

        self.btnImport.setEnabled(False)
        self.prgImport.setValue(0)
        self.prgImport.setFormat("Importing...")
        self.prgImport.update()
        self.prgImport.repaint()

        self.edtObjectCount.setText(str(import_data.nobjects))
        #print("objects:", tps.nobjects,tps.nlandmarks,tps.object_name_list)
        # create dataset
        dataset = MdDataset()
        dataset.dataset_name = datasetname
        dataset.dimension = import_data.dimension
        if len(import_data.propertyname_list) > 0:
            dataset.propertyname_list = import_data.propertyname_list
            dataset.pack_propertyname_str()
        dataset.save()
        # add objects
        for i in range(import_data.nobjects):
            object = MdObject()
            object.object_name = import_data.object_name_list[i]
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
            if len(import_data.propertyname_list) > 0:
                object.property_list = import_data.property_list_list[i]
                object.pack_property()
            if object.object_name in import_data.object_comment.keys():
                object.object_desc = import_data.object_comment[import_data.object_name_list[i]]

            object.save()
            val = int( (float(i+1)*100.0 / float(import_data.nobjects)) )
            #print("progress:", i+1, tps.nobjects, val)
            self.update_progress(val)
            #progress = int( (i / float(tps.nobjects)) * 100)

        #print("tps import done")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("Finished importing a " + filetype + " file.")
        msg.setStandardButtons(QMessageBox.Ok)
            
        retval = msg.exec_()
        self.close()
        # add dataset to project
        #self.parent.parent.project.datasets.append(dataset)
        #self.parent.parent.project.current_dataset = dataset

    def update_progress(self, value):
        self.prgImport.setValue(value)
        self.prgImport.setFormat("Importing...{}%".format(value))
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
        self.remember_geometry = True

        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        #['blue','green','black','cyan','magenta','yellow','gray','red']
        self.color_list = self.default_color_list[:]

        self.m_app = QApplication.instance()
        self.read_settings()
        self.setWindowTitle("Preferences")
        #self.lbl_main_view.setMinimumSize(400, 300)

        self.rbRememberGeometryYes = QRadioButton("Yes")
        self.rbRememberGeometryYes.setChecked(self.remember_geometry)
        self.rbRememberGeometryYes.clicked.connect(self.on_rbRememberGeometryYes_clicked)
        self.rbRememberGeometryNo = QRadioButton("No")
        self.rbRememberGeometryNo.setChecked(not self.remember_geometry)
        self.rbRememberGeometryNo.clicked.connect(self.on_rbRememberGeometryNo_clicked)

        self.gbRememberGeomegry = QGroupBox()
        self.gbRememberGeomegry.setLayout(QHBoxLayout())
        self.gbRememberGeomegry.layout().addWidget(self.rbRememberGeometryYes)
        self.gbRememberGeomegry.layout().addWidget(self.rbRememberGeometryNo)

        
        self.toolbar_icon_large = True if self.toolbar_icon_size.lower() == "large" else False
        self.rbToolbarIconLarge = QRadioButton("Large")
        self.rbToolbarIconLarge.setChecked(self.toolbar_icon_large)
        self.rbToolbarIconLarge.clicked.connect(self.on_rbToolbarIconLarge_clicked)
        self.rbToolbarIconSmall = QRadioButton("Small")
        self.rbToolbarIconSmall.setChecked(not self.toolbar_icon_large)
        self.rbToolbarIconSmall.clicked.connect(self.on_rbToolbarIconSmall_clicked)

        self.gbToolbarIconSize = QGroupBox()
        self.gbToolbarIconSize.setLayout(QHBoxLayout())
        self.gbToolbarIconSize.layout().addWidget(self.rbToolbarIconLarge)
        self.gbToolbarIconSize.layout().addWidget(self.rbToolbarIconSmall)


        self.gbPlotColors = QGroupBox()
        self.gbPlotColors.setLayout(QGridLayout())
        #symbol_candidate = ['o','s','^','x','+','d','v','<','>','p','h']
        self.btnResetVivid = QPushButton()
        self.btnResetVivid.setText("Vivid")
        self.btnResetVivid.clicked.connect(self.on_btnResetVivid_clicked)
        self.btnResetVivid.setMinimumSize(60,20)
        self.btnResetVivid.setMaximumSize(100,20)
        self.btnResetPastel = QPushButton()
        self.btnResetPastel.setText("Pastel")
        self.btnResetPastel.clicked.connect(self.on_btnResetPastel_clicked)
        self.btnResetPastel.setMinimumSize(60,20)
        self.btnResetPastel.setMaximumSize(100,20)
        

        self.lblColor_list = []
        for i in range(len(self.color_list)):
            self.lblColor_list.append(QPushButton())
            self.lblColor_list[i].setMinimumSize(20,20)
            #self.lblColor_list[i].setMaximumSize(20,20)
            self.lblColor_list[i].setStyleSheet("background-color: " + self.color_list[i])
            self.lblColor_list[i].setToolTip(self.color_list[i])
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

        self.btnOkay = QPushButton()
        self.btnOkay.setText("Close")
        self.btnOkay.clicked.connect(self.Okay)

        self.btnCancel = QPushButton()
        self.btnCancel.setText("Cancel")
        self.btnCancel.clicked.connect(self.Cancel)

        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addRow("Remember Geometry", self.gbRememberGeomegry)
        self.main_layout.addRow("Toolbar Icon Size", self.gbToolbarIconSize)
        self.main_layout.addRow("Data point colors", self.gbPlotColors)
        self.main_layout.addRow("", self.btnOkay)

        self.read_settings()

    def on_btnResetPastel_clicked(self):
        self.color_list = mu.PASTEL_COLOR_LIST[:]
        for i in range(len(self.color_list)):
            self.lblColor_list[i].setStyleSheet("background-color: " + self.color_list[i])
            self.lblColor_list[i].setToolTip(self.color_list[i])
    def on_btnResetVivid_clicked(self):
        self.color_list = mu.VIVID_COLOR_LIST[:]
        for i in range(len(self.color_list)):
            self.lblColor_list[i].setStyleSheet("background-color: " + self.color_list[i])
            self.lblColor_list[i].setToolTip(self.color_list[i])

    def on_lblColor_clicked(self,event, index):
        self.current_lblColor = self.lblColor_list[index]
        #dialog = ColorPickerDialog(color=QColor(self.current_lblColor.toolTip()))
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.current_lblColor.toolTip())) # return type is QColor
        #print("color: ", color)
        if color is not None:
            self.current_lblColor.setStyleSheet("background-color: " + color.name())
            self.current_lblColor.setToolTip(color.name())
            self.color_list[self.lblColor_list.index(self.current_lblColor)] = color.name()
            #print(self.color_list)

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        self.toolbar_icon_size = self.m_app.settings.value("ToolbarIconSize", "Small")
        for i in range(len(self.color_list)):
            self.color_list[i] = self.m_app.settings.value("DataPointColor/"+str(i), self.default_color_list[i])
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/PreferencesDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos()+QPoint(100,100))

    def write_settings(self):
        self.m_app.settings.setValue("ToolbarIconSize", self.toolbar_icon_size)
        self.m_app.settings.setValue("WindowGeometry/RememberGeometry", self.remember_geometry)
        #print(self.color_list)
        for i in range(len(self.color_list)):
            self.m_app.settings.setValue("DataPointColor/"+str(i), self.color_list[i])




        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/PreferencesDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def on_rbToolbarIconLarge_clicked(self):
        self.toolbar_icon_large = True
        self.toolbar_icon_size = "Large"
        self.parent.set_toolbar_icon_size( self.toolbar_icon_size )

    def on_rbToolbarIconSmall_clicked(self):
        self.toolbar_icon_large = False
        self.toolbar_icon_size = "Small"
        self.parent.set_toolbar_icon_size( self.toolbar_icon_size )

    def on_rbRememberGeometryYes_clicked(self):
        self.remember_geometry = True

    def on_rbRememberGeometryNo_clicked(self):
        self.remember_geometry = False        

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














'''











class MyTreeView(QTreeView):
    def __init__(self):
        QTreeView.__init__(self)

    def dragEnterEvent(self, event):
        print("drag enter event")
        #if event.mimeData().hasUrls:
        event.accept()
        #else:
        #    event.ignore()

    def dragMoveEvent(self, event):
        print("drag move event from", event.source())
        #if event.mimeData().hasUrls:
        event.setDropAction(Qt.MoveAction)
        event.accept()
        #else:
        #    event.ignore()

    def dropEvent(self, event):
        print("drop event from", event.source(), event.source().currentIndex())
        #if event.mimeData().hasUrls:
        event.setDropAction(Qt.MoveAction)
        event.accept()
        # to get a list of files:
        drop_list = []
        for url in event.mimeData().urls():
            drop_list.append(str(url.toLocalFile()))
        # handle the list here
        #else:
        #    event.ignore()

class MyPlotWidget(pg.PlotWidget):

    def __init__(self, **kwargs):   
        super().__init__(**kwargs)

        # self.scene() is a pyqtgraph.GraphicsScene.GraphicsScene.GraphicsScene
        self.scene().sigMouseClicked.connect(self.mouse_clicked)    


    def mouse_clicked(self, mouseClickEvent):
        # mouseClickEvent is a pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        print('clicked plot 0x{:x}, event: {}, pos: {}, {}, {}'.format(id(self), mouseClickEvent, mouseClickEvent.pos(), mouseClickEvent.scenePos(), mouseClickEvent.screenPos()))
        plot_item = self.getPlotItem()
        print('plot_item: 0x{:x}'.format(id(plot_item)))

class MyPlotItem(pg.ScatterPlotItem):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.scene() is a pyqtgraph.GraphicsScene.GraphicsScene.GraphicsScene
        self.sigClicked.connect(self.clicked)


    def clicked(self, points, spotitem_list, ev):
        # mouseClickEvent is a pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        print('clicked plot 0x{:x}, points: {}, event: {}, xx:{}'.format(id(self), points, spotitem_list, ev))
        #plot_item = self.getPlotItem()
        #print('plot_item: 0x{:x}'.format(id(plot_item)))
        points = self.pointsAt(ev.pos())
        print("points:",points[0].data().object_name)        
'''        