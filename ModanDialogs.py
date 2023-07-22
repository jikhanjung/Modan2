from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, QStatusBar,\
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QAction, QMenu, QSizePolicy, \
                            QTableWidget, QBoxLayout, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox, QOpenGLWidget, \
                            QTabWidget, QListWidget

from PyQt5 import QtGui, uic
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem,\
                        QPainterPath, QFont, QImageReader, QPainter, QBrush, QMouseEvent, QWheelEvent, QDrag, QDoubleValidator
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QEvent, QRegExp, QSize, QPoint,\
                         pyqtSignal, QThread, QMimeData, pyqtSlot, QItemSelectionModel, QTimer

import pyqtgraph as pg
#import pyqtgraph.opengl as gl

import OpenGL.GL as gl
from OpenGL import GLU as glu
from OpenGL import GLUT as glut
from PyQt5.QtOpenGL import *
import sys

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
from MdStatistics import MdPrincipalComponent
import numpy as np
from OpenGL.arrays import vbo

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


MODE_NONE = 0
MODE_PAN = 12
MODE_EDIT_LANDMARK = 1
MODE_WIREFRAME = 2
MODE_READY_MOVE_LANDMARK = 3
MODE_MOVE_LANDMARK = 4
MODE_PRE_WIRE_FROM = 5
MODE_CALIBRATION = 6


LANDMARK_RADIUS = 3
DISTANCE_THRESHOLD = LANDMARK_RADIUS * 3

IMAGE_EXTENSION_LIST = ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']

# glview modes
OBJECT_MODE = 1
DATASET_MODE = 2
VIEW_MODE = 1
PAN_MODE = 2
ROTATE_MODE = 3
ZOOM_MODE = 4
LANDMARK_MODE = 1
WIREFRAME_MODE = 2

COLOR_RED = ( 1, 0, 0 )
COLOR_GREEN = ( 0, 1, 0 )
COLOR_BLUE = ( 0, 0, 1 )
COLOR_YELLOW = ( 1, 1, 0 )
COLOR_CYAN = ( 0, 1, 1 )
COLOR_MAGENTA = ( 1, 0, 1 )
COLOR_WHITE = ( 1, 1, 1 )
COLOR_LIGHT_GRAY = ( 0.8, 0.8, 0.8 )
COLOR_BLACK = (0,0,0)

COLOR_SINGLE_SHAPE = COLOR_GREEN
COLOR_AVERAGE_SHAPE = COLOR_LIGHT_GRAY
COLOR_NORMAL_SHAPE = COLOR_BLUE
COLOR_NORMAL_TEXT = COLOR_WHITE
COLOR_SELECTED_SHAPE = COLOR_RED
COLOR_SELECTED_TEXT = COLOR_RED
COLOR_SELECTED_LANDMARK = COLOR_RED
COLOR_WIREFRAME = COLOR_YELLOW
COLOR_SELECTED_EDGE = COLOR_RED
COLOR_BACKGROUND = COLOR_BLACK

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
        self.pan_mode = MODE_NONE
        self.edit_mode = MODE_NONE

        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.set_mode(MODE_EDIT_LANDMARK)

        self.show_index = True
        self.show_wireframe = True
        self.show_baseline = False  

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
        if self.edit_mode == MODE_EDIT_LANDMARK:
            self.setCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
        elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Click on landmark to move")
        elif self.edit_mode == MODE_MOVE_LANDMARK:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Move landmark")
        if self.edit_mode == MODE_CALIBRATION:
            self.setCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
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
        if self.orig_pixmap is None or self.object_dialog is None:
            return
        me = QMouseEvent(event)
        self.mouse_curr_x = me.x()
        self.mouse_curr_y = me.y()
        curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
    
        if self.pan_mode == MODE_PAN:
            self.temp_pan_x = self.mouse_curr_x - self.mouse_down_x
            self.temp_pan_y = self.mouse_curr_y - self.mouse_down_y

        elif self.edit_mode == MODE_EDIT_LANDMARK:
            near_idx = self.get_landmark_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
            if near_idx >= 0:
                self.setCursor(Qt.SizeAllCursor)
                self.set_mode(MODE_READY_MOVE_LANDMARK)
                self.selected_landmark_index = near_idx

        elif self.edit_mode == MODE_WIREFRAME:
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

        elif self.edit_mode == MODE_MOVE_LANDMARK:
            if self.selected_landmark_index >= 0:
                self.landmark_list[self.selected_landmark_index] = [self._2imgx(self.mouse_curr_x), self._2imgy(self.mouse_curr_y)]
                if self.object_dialog is not None:
                    self.object_dialog.update_landmark(self.selected_landmark_index, *self.landmark_list[self.selected_landmark_index])

        elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
            curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
            ready_landmark = self.landmark_list[self.selected_landmark_index]
            lm_can_pos = [self._2canx(ready_landmark[0]),self._2cany(ready_landmark[1])]
            if self.get_distance(curr_pos, lm_can_pos) > DISTANCE_THRESHOLD:
                self.set_mode(MODE_EDIT_LANDMARK)
                self.selected_landmark_index = -1
            
        self.repaint()
        QLabel.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        if self.orig_pixmap is None or self.object_dialog is None:
            return

        me = QMouseEvent(event)
        if me.button() == Qt.LeftButton:
            if self.edit_mode == MODE_EDIT_LANDMARK:
                img_x = self._2imgx(self.mouse_curr_x)
                img_y = self._2imgy(self.mouse_curr_y)
                if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                    return
                self.object_dialog.add_landmark(img_x, img_y)
            elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
                self.set_mode(MODE_MOVE_LANDMARK)
            elif self.edit_mode == MODE_WIREFRAME:
                if self.wire_hover_index >= 0:
                    if self.wire_start_index < 0:
                        self.wire_start_index = self.wire_hover_index
                        self.wire_hover_index = -1
            elif self.edit_mode == MODE_CALIBRATION:
                self.calibration_from_img_x = self._2imgx(self.mouse_curr_x)
                self.calibration_from_img_y = self._2imgy(self.mouse_curr_y)

        elif me.button() == Qt.RightButton:
            if self.edit_mode == MODE_WIREFRAME:
                #if self.
                if self.wire_start_index >= 0:
                    self.wire_start_index = -1
                    self.wire_hover_index = -1
                elif self.selected_edge_index >= 0:
                    self.delete_edge(self.selected_edge_index)                    
                    self.selected_edge_index = -1
            elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
                if self.selected_landmark_index >= 0:
                    self.object_dialog.delete_landmark(self.selected_landmark_index)
                    self.selected_landmark_index = -1
            else:
                self.pan_mode = MODE_PAN
                self.mouse_down_x = me.x()
                self.mouse_down_y = me.y()
        elif me.button() == Qt.MidButton:
            print("middle button clicked")

        self.repaint()

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        me = QMouseEvent(ev)
        if self.pan_mode == MODE_PAN:
            self.pan_mode = MODE_NONE
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
            self.repaint()
        elif self.edit_mode == MODE_MOVE_LANDMARK:
            self.set_mode(MODE_EDIT_LANDMARK)
            self.selected_landmark_index = -1
        elif self.edit_mode == MODE_WIREFRAME:
            if self.wire_start_index >= 0 and self.wire_hover_index >= 0:
                self.add_edge(self.wire_start_index, self.wire_hover_index)
                self.wire_start_index = -1
                self.wire_hover_index = -1
                self.wire_end_index = -1
        elif self.edit_mode == MODE_CALIBRATION:
            diff_x = self._2imgx(self.mouse_curr_x) - self.calibration_from_img_x
            diff_y = self._2imgy(self.mouse_curr_y) - self.calibration_from_img_y
            dist = math.sqrt(diff_x * diff_x + diff_y * diff_y)
            self.object_dialog.calibrate(dist)
            self.calibration_from_img_x = -1
            self.calibration_from_img_y = -1

        return super().mouseReleaseEvent(ev)    

    def wheelEvent(self, event):
        if self.orig_pixmap is None:
            return
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
        if self.object is None:
            return

        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(as_qt_color(COLOR_BACKGROUND)))

        #if self.orig_pixmap is None:
        #    return
        
        if self.curr_pixmap is not None:                
            painter.drawPixmap(self.pan_x+self.temp_pan_x, self.pan_y+self.temp_pan_y,self.curr_pixmap)

        #print("paintEvent", self.landmark_list, self.edge_list)
        # draw wireframe
        if self.show_wireframe == True:
            painter.setPen(QPen(as_qt_color(COLOR_WIREFRAME), 2))
            painter.setBrush(QBrush(as_qt_color(COLOR_WIREFRAME)))

            #print("wireframe 2", dataset.edge_list, dataset.wireframe)
            for wire in self.edge_list:
                if wire[0] >= len(self.landmark_list) or wire[1] >= len(self.landmark_list):
                    continue
                [ from_x, from_y ] = self.landmark_list[wire[0]]
                [ to_x, to_y ] = self.landmark_list[wire[1]]
                painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))
                #painter.drawLine(self.landmark_list[wire[0]][0], self.landmark_list[wire[0]][1], self.landmark_list[wire[1]][0], self.landmark_list[wire[1]][1])
            if self.selected_edge_index >= 0:
                edge = self.edge_list[self.selected_edge_index]
                painter.setPen(QPen(as_qt_color(COLOR_SELECTED_EDGE), 2))
                [ from_x, from_y ] = self.landmark_list[edge[0]]
                [ to_x, to_y ] = self.landmark_list[edge[1]]
                painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))

        radius = LANDMARK_RADIUS
        painter.setPen(QPen(Qt.blue, 2))
        painter.setBrush(QBrush(Qt.blue))
        if self.edit_mode == MODE_CALIBRATION:
            if self.calibration_from_img_x >= 0 and self.calibration_from_img_y >= 0:
                x1 = int(self._2canx(self.calibration_from_img_x))
                y1 = int(self._2cany(self.calibration_from_img_y))
                x2 = self.mouse_curr_x
                y2 = self.mouse_curr_y
                painter.setPen(QPen(as_qt_color(COLOR_SELECTED_LANDMARK), 2))
                painter.drawLine(x1,y1,x2,y2)

        painter.setFont(QFont('Arial', 14))
        for idx, landmark in enumerate(self.landmark_list):
            if idx == self.wire_hover_index:
                painter.setPen(QPen(as_qt_color(COLOR_SELECTED_LANDMARK), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR_SELECTED_LANDMARK)))
            elif idx == self.wire_start_index or idx == self.wire_end_index:
                painter.setPen(QPen(as_qt_color(COLOR_SELECTED_LANDMARK), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR_SELECTED_LANDMARK)))
            else:
                painter.setPen(QPen(as_qt_color(COLOR_NORMAL_SHAPE), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR_NORMAL_SHAPE)))
            painter.drawEllipse(int(self._2canx(landmark[0])-radius), int(self._2cany(landmark[1]))-radius, radius*2, radius*2)
            if self.show_index == True:
                painter.drawText(int(self._2canx(landmark[0])+10), int(self._2cany(landmark[1]))+10, str(idx+1))


        # draw wireframe being edited
        if self.wire_start_index >= 0:
            painter.setPen(QPen(as_qt_color(COLOR_WIREFRAME), 2))
            painter.setBrush(QBrush(as_qt_color(COLOR_WIREFRAME)))
            start_lm = self.landmark_list[self.wire_start_index]
            painter.drawLine(self._2canx(int(start_lm[0])), self._2cany(int(start_lm[1])), self.mouse_curr_x, self.mouse_curr_y)


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
            painter.setFont(QFont('Arial', 10))
            painter.drawText(x + int(math.floor(float(bar_width) / 2.0 + 0.5)) - len(length_text) * 4, y - 5, length_text)

    def calculate_resize(self):
        #print("objectviewer calculate resize", self.object.landmark_list, self.landmark_list)
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
            self.pan_x = -min_x * self.scale + (self.width() - width * self.scale) / 2.0
            self.pan_y = -min_y * self.scale + (self.height() - height * self.scale) / 2.0
            #print("scale:", self.scale, "pan_x:", self.pan_x, "pan_y:", self.pan_y)
        self.repaint()

    def resizeEvent(self, event):
        #if self.orig_pixmap is not None:
        #print("resize")
        self.calculate_resize()
        #if self.curr_pixmap is not None:                
        #    pass
        QLabel.resizeEvent(self, event)
        #

    def set_object(self, object):
        #print("set object", object, object.pixels_per_mm)
        m_app = QApplication.instance()
        self.object = object

        if self.object.pixels_per_mm is not None and self.object.pixels_per_mm > 0:
            self.pixels_per_mm = self.object.pixels_per_mm

        if object.image.count() > 0:
            self.set_image(object.image[0].get_image_path(m_app.storage_directory))
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

class LandmarkEditor(QLabel):
    #clicked = pyqtSignal()
    def __init__(self, widget):
        super(LandmarkEditor, self).__init__(widget)
        self.setMinimumSize(400,300)
        self.object_dialog = None
        self.setAcceptDrops(True)
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.scale = 1.0
        self.fullpath = None
        self.setMouseTracking(True)
        self.set_mode(MODE_EDIT_LANDMARK)
        self.pan_mode = MODE_NONE
        self.edit_mode = MODE_NONE

        self.show_index = True
        self.show_wireframe = True
        self.show_baseline = False  

        self.pan_x = 0
        self.pan_y = 0
        self.temp_pan_x = 0
        self.temp_pan_y = 0
        self.mouse_down_x = 0
        self.mouse_down_y = 0
        self.mouse_curr_x = 0
        self.mouse_curr_y = 0

        self.landmark_list = []
        self.image_canvas_ratio = 1.0
        self.selected_landmark_index = -1
        self.selected_edge_index = -1
        self.wire_hover_index = -1
        self.wire_start_index = -1
        self.wire_end_index = -1
        self.calibration_from_img_x = -1
        self.calibration_from_img_y = -1
        self.pixels_per_mm = -1
        
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
        if self.edit_mode == MODE_EDIT_LANDMARK:
            self.setCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
        elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Click on landmark to move")
        elif self.edit_mode == MODE_MOVE_LANDMARK:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Move landmark")
        if self.edit_mode == MODE_CALIBRATION:
            self.setCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
        else:
            self.setCursor(Qt.ArrowCursor)

    def get_index_within_threshold(self, curr_pos, threshold):

        for index, landmark in enumerate(self.landmark_list):
            lm_can_pos = [self._2canx(landmark[0]),self._2cany(landmark[1])]
            dist = self.get_distance(curr_pos, lm_can_pos)
            if dist < DISTANCE_THRESHOLD:
                return index
        return -1
    
    def get_edge_index_within_threshold(self, curr_pos, threshold):
        if len(self.edge_list) == 0:
            return -1

        landmark_list = self.landmark_list
        for index, wire in enumerate(self.edge_list):
            #print("index", index, "wire:", wire)
            if wire[0] >= len(self.landmark_list) or wire[1] >= len(self.landmark_list):
                continue

            wire_start = [self._2canx(float(self.landmark_list[wire[0]][0])),self._2cany(float(self.landmark_list[wire[0]][1]))]
            wire_end = [self._2canx(float(self.landmark_list[wire[1]][0])),self._2cany(float(self.landmark_list[wire[1]][1]))]
            dist = self.get_distance_to_line(curr_pos, wire_start, wire_end)
            if dist < DISTANCE_THRESHOLD and dist > 0:
                #print("dist:", dist, "threshold:", threshold, wire_start, wire_end)
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
    

    def mouseMoveEvent(self, event):
        if self.orig_pixmap is None or self.object_dialog is None:
            return
        me = QMouseEvent(event)
        self.mouse_curr_x = me.x()
        self.mouse_curr_y = me.y()
        curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
    
        #print("mouse move event", me, me.pos(), self.curr_mouse_x, self.curr_mouse_y, self._2imgx(self.curr_mouse_x), self._2imgy(self.curr_mouse_y))
        if self.pan_mode == MODE_PAN:
            self.temp_pan_x = self.mouse_curr_x - self.mouse_down_x
            self.temp_pan_y = self.mouse_curr_y - self.mouse_down_y
            #print("pan", self.pan_x, self.pan_y, self.temp_pan_x, self.temp_pan_y)
            #self.downX = me.x()
            #self.downY = me.y()
        elif self.edit_mode == MODE_EDIT_LANDMARK:
            near_idx = self.get_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
            if near_idx >= 0:
                #print("close to landmark", landmark, curr_pos, lm_can_pos, dist, DISTANCE_THRESHOLD)
                self.setCursor(Qt.SizeAllCursor)
                self.set_mode(MODE_READY_MOVE_LANDMARK)
                self.selected_landmark_index = near_idx

        elif self.edit_mode == MODE_WIREFRAME:
            #if self.wire_hover_index < 0:
            near_idx = self.get_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
            #print("close to landmark", self.landmark_list[near_idx], curr_pos, near_idx, DISTANCE_THRESHOLD)
            #print("start/end index", self.wire_start_index, self.wire_end_index)
            if near_idx >= 0:
                self.selected_edge_index = -1
                if self.wire_hover_index < 0:
                    self.wire_hover_index = near_idx
                    #print("hover wire idx", near_idx, self.landmark_list[near_idx])
                    #self.repaint()
                else:
                    pass
            elif self.wire_start_index >= 0:
                self.wire_hover_index = -1
                #pass
            else:
                self.wire_hover_index = -1
                #self.repaint()
            
                near_wire_idx = self.get_edge_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
                if near_wire_idx >= 0:
                    edge = self.edge_list[near_wire_idx]
                    self.selected_edge_index = near_wire_idx
                    #print("near wire idx", near_wire_idx, edge, self.landmark_list[edge[0]], self.landmark_list[edge[1]])
                else:
                    self.selected_edge_index = -1

        elif self.edit_mode == MODE_MOVE_LANDMARK:
            #print("move landmark", self.selected_landmark_index)
            if self.selected_landmark_index >= 0:
                #print("move landmark", self.selected_landmark_index)
                self.landmark_list[self.selected_landmark_index] = [self._2imgx(self.mouse_curr_x), self._2imgy(self.mouse_curr_y)]
                if self.object_dialog is not None:
                    self.object_dialog.update_landmark(self.selected_landmark_index, *self.landmark_list[self.selected_landmark_index])
                #self.repaint()
                #print("landmark list", self.landmark_list)
        elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
            curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
            ready_landmark = self.landmark_list[self.selected_landmark_index]
            lm_can_pos = [self._2canx(ready_landmark[0]),self._2cany(ready_landmark[1])]
            if self.get_distance(curr_pos, lm_can_pos) > DISTANCE_THRESHOLD:
                self.set_mode(MODE_EDIT_LANDMARK)
                self.selected_landmark_index = -1
            
        self.repaint()
        QLabel.mouseMoveEvent(self, event)

    def get_distance(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def mousePressEvent(self, event):
        if self.orig_pixmap is None or self.object_dialog is None:
            return
        #print("mouse press event")
        #self.clicked.emit()
        me = QMouseEvent(event)
        #print("event and pos", event, me.pos())
        if me.button() == Qt.LeftButton:

            #print("left button clicked", me.pos())
            if self.edit_mode == MODE_EDIT_LANDMARK:
                #print("add landmark")
                #print(self.object_dialog)
                img_x = self._2imgx(self.mouse_curr_x)
                img_y = self._2imgy(self.mouse_curr_y)
                if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                    return
                #print("add landmark", img_x, img_y)
                #print("landmark list 0", self.landmark_list)
                self.object_dialog.add_landmark(img_x, img_y)
                #print("landmark list 1", self.landmark_list)
                #self.landmark_list.append([img_x, img_y])
                #print("landmark list 2", self.landmark_list)
            elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
                self.set_mode(MODE_MOVE_LANDMARK)
            elif self.edit_mode == MODE_WIREFRAME:
                if self.wire_hover_index >= 0:
                    if self.wire_start_index < 0:
                        self.wire_start_index = self.wire_hover_index
                        self.wire_hover_index = -1
                        #self.edit_mode = MODE_DRAW_WIREFRAME
            elif self.edit_mode == MODE_CALIBRATION:
                self.calibration_from_img_x = self._2imgx(self.mouse_curr_x)
                self.calibration_from_img_y = self._2imgy(self.mouse_curr_y)

        elif me.button() == Qt.RightButton:
            if self.edit_mode == MODE_WIREFRAME:
                #if self.
                if self.wire_start_index >= 0:
                    self.wire_start_index = -1
                    self.wire_hover_index = -1
                elif self.selected_edge_index >= 0:
                    self.delete_edge(self.selected_edge_index)                    
                    self.selected_edge_index = -1
            elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
            #elif self.edit_mode == MODE_EDIT_LANDMARK:
                if self.selected_landmark_index >= 0:
                    #self.landmark_list.pop(self.selected_landmark_index)
                    self.object_dialog.delete_landmark(self.selected_landmark_index)
                    self.selected_landmark_index = -1
                    #self.object_dialog.show_landmarks()
            else:
                self.pan_mode = MODE_PAN
                self.mouse_down_x = me.x()
                self.mouse_down_y = me.y()
                #print("right button clicked")
            #print("right button clicked")
        elif me.button() == Qt.MidButton:
            print("middle button clicked")

        self.repaint()
        #QLabel.mousePressEvent(self, event)

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        me = QMouseEvent(ev)
        #print("mouse release event", me, me.pos())
        if self.pan_mode == MODE_PAN:
            self.pan_mode = MODE_NONE
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
            self.repaint()
            #print("right button released")
        elif self.edit_mode == MODE_MOVE_LANDMARK:
            self.set_mode(MODE_EDIT_LANDMARK)
            self.selected_landmark_index = -1
            #print("move landmark", self.selected_landmark_index)
        elif self.edit_mode == MODE_WIREFRAME:
            if self.wire_start_index >= 0 and self.wire_hover_index >= 0:
                self.add_wire(self.wire_start_index, self.wire_hover_index)
                self.wire_start_index = -1
                self.wire_hover_index = -1
                #self.edit_mode = MODE_EDIT_WIREFRAME
                self.wire_end_index = -1
                #self.repaint()
        elif self.edit_mode == MODE_CALIBRATION:

            diff_x = self._2imgx(self.mouse_curr_x) - self.calibration_from_img_x
            diff_y = self._2imgy(self.mouse_curr_y) - self.calibration_from_img_y
            dist = math.sqrt(diff_x * diff_x + diff_y * diff_y)
            self.object_dialog.calibrate(dist)
            self.calibration_from_img_x = -1
            self.calibration_from_img_y = -1

        return super().mouseReleaseEvent(ev)    

    def add_wire(self,wire_start_index, wire_end_index):
        if wire_start_index == wire_end_index:
            return
        if wire_start_index > wire_end_index:
            wire_start_index, wire_end_index = wire_end_index, wire_start_index
        dataset = self.object.dataset
        for wire in dataset.edge_list:
            if wire[0] == wire_start_index and wire[1] == wire_end_index:
                return
        dataset.edge_list.append([wire_start_index, wire_end_index])
        #print("wireframe", dataset.edge_list)
        dataset.pack_wireframe()
        #print("wireframe", dataset.wireframe)
        dataset.save()
        #print("dataset:", dataset)
        self.repaint()
        
    def delete_edge(self, edge_index):
        dataset = self.object.dataset
        dataset.edge_list.pop(edge_index)
        dataset.pack_wireframe()
        dataset.save()
        self.repaint()

    def wheelEvent(self, event):
        if self.orig_pixmap is None:
            return
        we = QWheelEvent(event)
        scale_delta = 0
        #print(we.angleDelta())
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
        self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_pixmap.width() * self.scale / self.image_canvas_ratio), int(self.orig_pixmap.height() * self.scale / self.image_canvas_ratio))

        self.pan_x = int( we.pos().x() - (we.pos().x() - self.pan_x) * scale_proportion )
        self.pan_y = int( we.pos().y() - (we.pos().y() - self.pan_y) * scale_proportion )

        self.repaint()

        #print("wheel event", we, we.angleDelta())
        QLabel.wheelEvent(self, event)

    def set_image(self,file_path):
        self.fullpath = file_path
        self.curr_pixmap = self.orig_pixmap = QPixmap(file_path)
        self.setPixmap(self.curr_pixmap)

        #self.setScaledContents(True)
        #print( self.curr_pixmap.width(), self.curr_pixmap.height(), self.orig_pixmap.width(), self.orig_pixmap.height())

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
        #print(file_path)
        #self.setScaledContents(True)
        self.set_image(file_path)
        #filename_stem = Path(file_path).stem
        # resize self
        self.calculate_resize()
        self.object_dialog.set_object_name(Path(file_path).stem)
        #self.resize(self.width(), self.height())

    def paintEvent(self, event):
        #self.pixmap
        #return super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(as_qt_color(COLOR_BACKGROUND)))

        if self.orig_pixmap is None:
            return
        # fill background with dark gray
        
        #height = self.progress * self.height()
        #if self.orig_pixmap is not None:
            #painter.drawPixmap(self.rect(), self.orig_pixmap)
        if self.curr_pixmap is not None:                
            #self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_width/self.image_canvas_ratio),int(self.orig_width/self.image_canvas_ratio), Qt.KeepAspectRatio)            
            painter.drawPixmap(self.pan_x+self.temp_pan_x, self.pan_y+self.temp_pan_y,self.curr_pixmap)

        # if edit_mode = MODE_ADD_LANDMARK draw a circle at the mouse position
        #painter.setBrush(QBrush(Qt.red))
        # draw wireframe
        if self.show_wireframe == True:
            painter.setPen(QPen(as_qt_color(COLOR_WIREFRAME), 2))
            painter.setBrush(QBrush(as_qt_color(COLOR_WIREFRAME)))

            #print("wireframe 2", dataset.edge_list, dataset.wireframe)
            for wire in self.edge_list:
                if wire[0] >= len(self.landmark_list) or wire[1] >= len(self.landmark_list):
                    continue
                [ from_x, from_y ] = self.landmark_list[wire[0]]
                [ to_x, to_y ] = self.landmark_list[wire[1]]
                painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))
                #painter.drawLine(self.landmark_list[wire[0]][0], self.landmark_list[wire[0]][1], self.landmark_list[wire[1]][0], self.landmark_list[wire[1]][1])
            if self.selected_edge_index >= 0:
                edge = self.edge_list[self.selected_edge_index]
                painter.setPen(QPen(as_qt_color(COLOR_SELECTED_EDGE), 2))
                [ from_x, from_y ] = self.landmark_list[edge[0]]
                [ to_x, to_y ] = self.landmark_list[edge[1]]
                painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))



        radius = LANDMARK_RADIUS
        painter.setPen(QPen(Qt.blue, 2))
        painter.setBrush(QBrush(Qt.blue))
        if self.edit_mode == MODE_EDIT_LANDMARK:
            img_x = self._2imgx(self.mouse_curr_x)
            img_y = self._2imgy(self.mouse_curr_y)
            if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                pass
            else:
                pass
                #painter.drawEllipse(self.curr_mouse_x-radius, self.curr_mouse_y-radius, radius*2, radius*2)
        elif self.edit_mode == MODE_CALIBRATION:
            if self.calibration_from_img_x >= 0 and self.calibration_from_img_y >= 0:
                x1 = int(self._2canx(self.calibration_from_img_x))
                y1 = int(self._2cany(self.calibration_from_img_y))
                x2 = self.mouse_curr_x
                y2 = self.mouse_curr_y
                #print("calibration", x1, y1, x2, y2)

                painter.setPen(QPen(Qt.red, 2))
                painter.drawLine(x1,y1,x2,y2)
        #print(landmark_list)

        #print("font:", painter.font().family(), painter.font().pointSize(), painter.font().pixelSize())
        painter.setFont(QFont('Arial', 14))
        for idx, landmark in enumerate(self.landmark_list):
            if idx == self.wire_hover_index:
                painter.setPen(QPen(as_qt_color(COLOR_SELECTED_LANDMARK), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR_SELECTED_LANDMARK)))
                #print("wire hover idx", idx)
            elif idx == self.wire_start_index or idx == self.wire_end_index:
                painter.setPen(QPen(as_qt_color(COLOR_SELECTED_LANDMARK), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR_SELECTED_LANDMARK)))
                #print("wire start/end idx", idx)
            else:
                painter.setPen(QPen(as_qt_color(COLOR_NORMAL_SHAPE), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR_NORMAL_SHAPE)))
            painter.drawEllipse(self._2canx(int(landmark[0]))-radius, self._2cany(int(landmark[1]))-radius, radius*2, radius*2)
            if self.show_index == True:
                painter.drawText(self._2canx(int(landmark[0]))+10, self._2cany(int(landmark[1]))+10, str(idx+1))


        # draw wireframe being edited
        if self.wire_start_index >= 0:
            painter.setPen(QPen(as_qt_color(COLOR_WIREFRAME), 2))
            painter.setBrush(QBrush(as_qt_color(COLOR_WIREFRAME)))
            start_lm = self.landmark_list[self.wire_start_index]
            #painter.drawEllipse(self._2canx(int(start_lm[0]))-radius*2, self._2cany(int(start_lm[1]))-radius, radius*2, radius*2)
            # draw line from start to mouse
            painter.drawLine(self._2canx(int(start_lm[0])), self._2cany(int(start_lm[1])), self.mouse_curr_x, self.mouse_curr_y)


        if self.object.pixels_per_mm is not None and self.object.pixels_per_mm > 0:
            pixels_per_mm = self.object.pixels_per_mm
            max_scalebar_size = 120
            #print("scalebar", self.pixels_per_mm, self.scale, max_scalebar_size)

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
            #length_text = str(actual_length) + " mm"
            #print( length_text, len( length_text ) )
            painter.setPen(QPen(Qt.black, 1))
            #painter.setBrush(QBrush(Qt.black))
            painter.setFont(QFont('Arial', 10))
            painter.drawText(x + int(math.floor(float(bar_width) / 2.0 + 0.5)) - len(length_text) * 4, y - 5, length_text)

    def calculate_resize(self):
        self.orig_width = self.orig_pixmap.width()
        self.orig_height = self.orig_pixmap.height()
        image_wh_ratio = self.orig_width / self.orig_height
        label_wh_ratio = self.width() / self.height()
        if image_wh_ratio > label_wh_ratio:
            self.image_canvas_ratio = self.orig_width / self.width()
        else:
            self.image_canvas_ratio = self.orig_height / self.height()
        self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_width*self.scale/self.image_canvas_ratio),int(self.orig_width*self.scale/self.image_canvas_ratio), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        if self.orig_pixmap is not None:
            self.calculate_resize()
            #print("image_wh_ratio", image_wh_ratio, "label_wh_ratio", label_wh_ratio, "image_canvas_ratio", self.image_canvas_ratio)

        #print("resize",self.size())
        # print size
        #print(event.size())
        #print(self.size())
        if self.curr_pixmap is not None:                
            #self.curr_pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
            #print( self.curr_pixmap.width(), self.curr_pixmap.height(), self.orig_pixmap.width(), self.orig_pixmap.height())
            pass
        QLabel.resizeEvent(self, event)

    def set_object(self, object):
        #print("Landmark Editor set_object", object.object_name)
        m_app = QApplication.instance()
        self.object = object

        if self.object.pixels_per_mm is not None and self.object.pixels_per_mm > 0:
            self.pixels_per_mm = self.object.pixels_per_mm

        if object.image.count() > 0:
            #print("set_object", object.image[0].get_image_path(m_app.storage_directory))
            self.set_image(object.image[0].get_image_path(m_app.storage_directory))
            object.unpack_landmark()
            object.dataset.unpack_wireframe()
            self.landmark_list = object.landmark_list
            self.edge_list = object.dataset.edge_list
            #print("edge_list", self.edge_list)
            #print("landmark_list", object.landmark_str)
            self.calculate_resize()

    def clear_object(self):
        #print("Landmark Editor clear_object")
        self.landmark_list = []
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.update()    

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

class ObjectDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Object")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 1024, 600))
        self.move(self.parent.pos()+QPoint(100,100))
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

        self.object_view_3d = MyGLWidget(self)
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
        self.btnLandmark = PicButton(QPixmap(resource_path("icons/landmark.png")), QPixmap(resource_path("icons/landmark_hover.png")), QPixmap(resource_path("icons/landmark_down.png")))
        self.btnWireframe = PicButton(QPixmap(resource_path("icons/wireframe.png")), QPixmap(resource_path("icons/wireframe_hover.png")), QPixmap(resource_path("icons/wireframe_down.png")))
        self.btnCalibration = PicButton(QPixmap(resource_path("icons/caliper.png")), QPixmap(resource_path("icons/caliper_hover.png")), QPixmap(resource_path("icons/caliper_down.png")))
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
        self.btnLandmark.setFixedSize(32,32)
        self.btnWireframe.setFixedSize(32,32)
        self.btnCalibration.setFixedSize(32,32)
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
        self.cbxAutoRotate = QCheckBox()
        self.cbxAutoRotate.setText("Rotate")
        self.cbxAutoRotate.setChecked(True)
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
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.m_app = QApplication.instance()
        #self.btnLandmark_clicked()

        self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        self.cbxAutoRotate.stateChanged.connect(self.auto_rotate_state_changed)

        #self.calibration
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
        self.object_view.set_mode(MODE_EDIT_LANDMARK)
        self.object_view.update()
        self.btnLandmark.setDown(True)
        self.btnLandmark.setChecked(True)
        self.btnWireframe.setDown(False)
        self.btnWireframe.setChecked(False)
        self.btnCalibration.setDown(False)
        self.btnCalibration.setChecked(False)

    def btnCalibration_clicked(self):
        #self.edit_mode = MODE_ADD_LANDMARK
        self.object_view_2d.set_mode(MODE_CALIBRATION)
        self.object_view_2d.update()
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
        self.object_view.set_mode(MODE_WIREFRAME)
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
            self.btnCalibration.show()
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
            self.btnCalibration.hide()
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
        #print("adding landmark", x, y, z)
        if self.dataset.dimension == 2:
            self.landmark_list.append([float(x),float(y)])
        elif self.dataset.dimension == 3:
            self.landmark_list.append([float(x),float(y),float(z)])
        self.show_landmarks()

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

    def set_object(self, object):
        #print("set_object", object.object_name, object.dataset.dimension)
        self.object = object
        self.edtObjectName.setText(object.object_name)
        self.edtObjectDesc.setText(object.object_desc)
        #self.edtLandmarkStr.setText(object.landmark_str)
        self.landmark_list = object.unpack_landmark()
        self.edge_list = object.dataset.unpack_wireframe()
        #for lm in self.landmark_list:
        #    self.show_landmark(*lm)
        self.show_landmarks()

        if object.dataset.dimension == 3:
            #print("set_object 3d")
            self.object_view = self.object_view_3d
            self.object_view.auto_rotate = True
            #obj_ops = MdObjectOps(object)
            self.object_view.set_object(object)
            #self.object_view.set_dataset(object.dataset)
            self.cbxAutoRotate.show()
        else:
            #print("set_object 2d")
            self.object_view = self.object_view_2d
            self.cbxAutoRotate.hide()
            if object.image is not None and len(object.image) > 0:
                img = object.image[0]
                image_path = img.get_image_path(self.m_app.storage_directory)
                #check if image_path exists
                if os.path.exists(image_path):
                    self.object_view.set_image(image_path)
                    self.object_view.set_object(object)
                    self.object_view.landmark_list = self.landmark_list
            elif len(self.landmark_list) > 0:
                self.object_view.set_object(object)
                self.object_view.landmark_list = self.landmark_list

        if len(self.dataset.propertyname_list) >0:
            self.object.unpack_property()
            self.dataset.unpack_propertyname_str()
            for idx, propertyname in enumerate(self.dataset.propertyname_list):
                if idx < len(object.property_list):
                    self.edtPropertyList[idx].setText(object.property_list[idx])

            #self.object_view_3d.landmark_list = self.landmark_list
        #self.set_dataset(object.dataset)

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
            new_filepath = md_image.get_image_path( self.m_app.storage_directory)
            if not os.path.exists(os.path.dirname(new_filepath)):
                os.makedirs(os.path.dirname(new_filepath))
            #print("save object new filepath:", new_filepath)
            shutil.copyfile(self.object_view_2d.fullpath, new_filepath)
            md_image.save()

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
                image_path = self.object.image[0].get_image_path(self.m_app.storage_directory)
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
        painter.fillRect(self.rect(), QBrush(as_qt_color(COLOR_BACKGROUND)))

        if self.ds_ops is None:
            return

        if self.show_wireframe == True:
            painter.setPen(QPen(as_qt_color(COLOR_WIREFRAME), 2))
            painter.setBrush(QBrush(as_qt_color(COLOR_WIREFRAME)))

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
        painter.setFont(QFont('Arial', 14))
        for obj in self.ds_ops.object_list:
            #print("obj:", obj.id)
            if obj.id in self.ds_ops.selected_object_id_list:
                painter.setPen(QPen(as_qt_color(COLOR_SELECTED_SHAPE), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR_SELECTED_SHAPE)))
            else:
                painter.setPen(QPen(as_qt_color(COLOR_NORMAL_SHAPE), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR_NORMAL_SHAPE)))
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
                painter.setPen(QPen(as_qt_color(COLOR_AVERAGE_SHAPE), 2))
                painter.setBrush(QBrush(as_qt_color(COLOR_AVERAGE_SHAPE)))
                x = self._2canx(landmark[0])
                y = self._2cany(landmark[1])
                painter.drawEllipse(x-radius, y-radius, radius*2, radius*2)
                if self.show_index:
                    painter.drawText(x+10, y+10, str(idx+1))

    def _2canx(self, x):
        return int(x*self.scale + self.pan_x)
    def _2cany(self, y):
        return int(y*self.scale + self.pan_y)

class MyGLWidget(QGLWidget):
    def __init__(self, parent):
        QGLWidget.__init__(self,parent)
        self.parent = parent
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
        self.show_wireframe = False
        self.show_baseline = False
        self.show_average = True
        self.curr_x = 0
        self.curr_y = 0
        self.down_x = 0
        self.down_y = 0
        self.temp_dolly = 0
        self.dolly = 0
        self.data_mode = OBJECT_MODE
        self.view_mode = VIEW_MODE
        self.edit_mode = MODE_NONE
        self.auto_rotate = False
        self.is_dragging = False
        self.setMinimumSize(400,400)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.timeout)
        self.timer.start()
        self.frustum_args = {'width': 1.0, 'height': 1.0, 'znear': 0.1, 'zfar': 1000.0}
        self.color_to_lm_idx = {}
        self.lm_idx_to_color = {}
        self.picker_buffer = None
        #self.no_drawing = False
        self.wireframe_from_idx = -1
        self.wireframe_to_idx = -1
        self.selected_landmark_idx = -1
        self.no_hit_count = 0
        self.edge_list = []


    def show_message(self, msg):
        if self.object_dialog is not None:
            self.object_dialog.status_bar.showMessage(msg) 

    def set_mode(self, mode):
        self.edit_mode = mode  
        if self.edit_mode == MODE_EDIT_LANDMARK:
            self.setCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
        elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Click on landmark to move")
        elif self.edit_mode == MODE_MOVE_LANDMARK:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Move landmark")
        elif self.edit_mode == MODE_WIREFRAME:
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
            if self.edit_mode == MODE_WIREFRAME and self.selected_landmark_idx > -1:
                self.wireframe_from_idx = self.selected_landmark_idx
                #self.edit_mode = MODE_ADD_WIRE
            else:                
                self.view_mode = ROTATE_MODE
        elif event.buttons() == Qt.RightButton:
            self.view_mode = ZOOM_MODE
        elif event.buttons() == Qt.MiddleButton:
            self.view_mode = PAN_MODE

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.curr_x = event.x()
        self.curr_y = event.y()
        #print("curr_x:", self.curr_x, "curr_y:", self.curr_y)
        if event.button() == Qt.LeftButton:
            if self.edit_mode == MODE_WIREFRAME and self.wireframe_from_idx > -1 and self.selected_landmark_idx > -1 and self.selected_landmark_idx != self.wireframe_from_idx:
                self.wireframe_to_idx = self.selected_landmark_idx
                self.add_wire(self.wireframe_from_idx, self.wireframe_to_idx)
                self.wireframe_from_idx = -1
                self.wireframe_to_idx = -1
                self.update()
            else:
                self.rotate_x += self.temp_rotate_x
                self.rotate_y += self.temp_rotate_y
                if self.data_mode == OBJECT_MODE:
                    #print("x rotate:", self.rotate_x, "y rotate:", self.rotate_y)
                    self.obj_ops.rotate_3d(math.radians(-1*self.rotate_x),'Y')
                    self.obj_ops.rotate_3d(math.radians(self.rotate_y),'X')
                    self.rotate_x = 0
                    self.rotate_y = 0
                else:
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


            #print("hit_test result:",hit, lm_idx)
            #print( "cursor on landmark", self.curr_x, self.curr_y, hit, lm_idx)
            #if hit:
            #    self.parent.update_status("cursor on landmark %d" % lm_idx)

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
        #print("wireframe", dataset.wireframe)
        dataset.save()
        

    def wheelEvent(self, event):
        #print("wheel event", event.angleDelta().y())
        self.dolly -= event.angleDelta().y() / 240.0
        self.updateGL()

    def set_ds_ops(self, ds_ops):
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
        #print("set_object 1",type(obj_ops))
        if isinstance(object, MdObject):
            self.object = object
            obj_ops = MdObjectOps(object)
        else:
            print("object is not MdObject")
        #print("set_object 2",type(obj_ops))
        obj_ops.move_to_center()
        centroid_size = obj_ops.get_centroid_size()
        obj_ops.rescale_to_unitsize()
        scale = self.get_scale_from_object(obj_ops)
        obj_ops.rescale(scale)
        self.obj_ops = obj_ops
        self.data_mode = OBJECT_MODE
        self.pan_x = self.pan_y = 0
        self.rotate_x = self.rotate_y = 0
        #self.auto_rotate = True
        self.dataset = object.dataset
        self.edge_list = self.dataset.unpack_wireframe()
        self.updateGL()
        #print("data_mode:", self.data_mode)

    def get_scale_from_object(self, obj_ops):
        centroid_size = obj_ops.get_centroid_size()
        min_x, max_x = min( [ lm[0] for lm in obj_ops.landmark_list] ), max( [ lm[0] for lm in obj_ops.landmark_list] )
        min_y, max_y = min( [ lm[1] for lm in obj_ops.landmark_list] ), max( [ lm[1] for lm in obj_ops.landmark_list] )
        min_z, max_z = min( [ lm[2] for lm in obj_ops.landmark_list] ), max( [ lm[2] for lm in obj_ops.landmark_list] )
        #obj_ops.rescale(5)
        width = max_x - min_x
        height = max_y - min_y
        depth = max_z - min_z
        _3D_SCREEN_WIDTH = 5
        _3D_SCREEN_HEIGHT = 5
        scale = min( _3D_SCREEN_WIDTH / width, _3D_SCREEN_HEIGHT / height )
        #print("scale:", scale)
        return scale*0.5

    def initialize_frame_buffer(self, frame_buffer_id=0):
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
        self.initialize_frame_buffer()
        self.picker_buffer = self.create_picker_buffer()
        self.initialize_frame_buffer(self.picker_buffer)

    def paintGL(self):
        if self.edit_mode == WIREFRAME_MODE:
            self.draw_picker_buffer()

        self.draw_all()

    def draw_all(self):
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45.0, self.aspect, 0.1, 100.0)
        gl.glTranslatef(0, 0, -5.0 + self.dolly + self.temp_dolly)   # x, y, z 
        gl.glTranslatef((self.pan_x + self.temp_pan_x)/100.0, (self.pan_y + self.temp_pan_y)/-100.0, 0.0)
        gl.glRotatef(self.rotate_y + self.temp_rotate_y, 1.0, 0.0, 0.0)
        gl.glRotatef(self.rotate_x + self.temp_rotate_x, 0.0, 1.0, 0.0)
        #gl.glLoadIdentity()

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glClearColor(*COLOR_BACKGROUND, 1)
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
                object_color = COLOR_SELECTED_SHAPE
            else:
                object_color = COLOR_NORMAL_SHAPE
            self.draw_object(obj, landmark_as_sphere=False, color=object_color)
        if self.show_average:
            object_color = COLOR_AVERAGE_SHAPE
            self.draw_object(ds_ops.get_average_shape(), landmark_as_sphere=True, color=object_color)

    def draw_object(self,object,landmark_as_sphere=True,color=COLOR_NORMAL_SHAPE):
        current_buffer = gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)
        if landmark_as_sphere:
            if self.show_wireframe and len(self.edge_list) > 0:
                #print("draw wireframe",self.edge_list)
                for edge in self.edge_list:
                    #gl.glDisable(gl.GL_LIGHTING)
                    gl.glColor3f( *COLOR_WIREFRAME )
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
                    gl.glColor3f( *COLOR_SELECTED_LANDMARK )

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
                    gl.glColor3f( *COLOR_NORMAL_TEXT )
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
        
        # https://github.com/yarolig/OBJFileLoader
        #from OBJFileLoader import OBJ
        #box = OBJ('box.obj')
        #gl.glPushMatrix()
        #gl.glColor3f( *COLOR_RED )
        #gl.glTranslatef(box_x, box_y, box_z)
        #box.render()
        #gl.glPopMatrix()

    def create_picker_buffer(self):
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
        self.obj_ops = None
        #gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        #gl.glFlush()
        #self.data_mode = DATASET_MODE

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
        #print("color_to_lm_idx", self.color_to_lm_idx)
        #print("lm_idx_to_color", self.lm_idx_to_color)

    def __hit_test(self, x, y):

        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glSelectBuffer(512)
        gl.glRenderMode(gl.GL_SELECT)
        gl.glLoadIdentity()
        
        #glu.gluPickMatrix(event.x(), viewport[3] - event.y(), 4, 4, viewport)

        aspect = viewport[2] / viewport[3]
        glu.gluPerspective(60, aspect, 1.0, 400)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        self.paintGL()
        gl.glMatrixMode(gl.GL_PROJECTION)
        #if right == False:
        #    parseLeftButtonNameStack(gl.glRenderMode(gl.GL_RENDER))
        #else:
        #    parseRightButtonNameStack(gl.glRenderMode(gl.GL_RENDER))
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)        

    def _hit_test(self, x, y):
        print( 'is cursor on landmark')

        SIZE = 1024
        select_buffer = np.array([0] * SIZE,dtype=np.uint32)
        select_buffer = [0] * SIZE
        #a = np.array([127, 128, 129], dtype=np.int8)
        select_buffer = gl.glSelectBuffer(SIZE)  # allocate a selection buffer of SIZE elements
        print("select buffer", SIZE, select_buffer)

        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        print("viewport:", viewport)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()

        gl.glRenderMode(gl.GL_SELECT)
        print("render mode:")
        self.render_mode = gl.GL_SELECT

        gl.glLoadIdentity()
        glu.gluPickMatrix(x, (viewport[3] - y), 10, 10, viewport)
        gl.glFrustum(self.frustum_args['width'] * -1.0, self.frustum_args['width'], self.frustum_args['height'] * -1.0,
                     self.frustum_args['height'], self.frustum_args['znear'], self.frustum_args['zfar'])
        glu.gluLookAt(0.0, 0.0, self.offset * -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        self.draw_all()

        buffer = gl.glRenderMode(gl.GL_RENDER)
        self.render_mode = gl.GL_RENDER

        hit = False
        top_lmidx = -1

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)

        for hit_record in buffer:
            min_depth, max_depth, names = hit_record  
            if names[0] > 1000:
                pass  #print "wire " + self.wirename[names[0]]
            else:
                #print "you hit point #" + str( names[0] )
                lmidx = names[0]
                if not hit:
                    hit = True
                    top_lmidx = lmidx
                    return hit, lmidx

        for hit_record in buffer:
            min_depth, max_depth, names = hit_record  # do something with the record
            if names[0] > 1000:
                hit = True
                idx = names[0]
                return hit, idx

            #self.object.landmarks[lmidx].selected = True
            #self.Refresh(False)
            #glMatrixMode( GL_MODELVIEW )

            #    print "a"
        self.updateGL()
        return hit, top_lmidx

class DatasetAnalysisDialog(QDialog):
    def __init__(self,parent,dataset):
        super().__init__()
        self.setWindowTitle("Modan2 - Dataset Analyses")
        self.setWindowIcon(QIcon(resource_path('icons/modan.ico')))
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.parent = parent
        self.setGeometry(QRect(100, 100, 1400, 800))
        self.move(self.parent.pos()+QPoint(50,50))

        self.ds_ops = None
        self.object_hash = {}
        
        self.main_hsplitter = QSplitter(Qt.Horizontal)

        # 2d shape
        self.lblShape2 = DatasetOpsViewer(self)
        self.lblShape2.setAlignment(Qt.AlignCenter)
        self.lblShape2.setMinimumWidth(400)
        self.lblShape2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # 3d shape
        self.lblShape3 = MyGLWidget(self)
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

        self.tableView = QTableView()
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(True)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView.setSortingEnabled(True)

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
        self.gbChartDim = QGroupBox()
        self.gbChartDim.setTitle("Chart Dimension")
        self.gbChartDim.setLayout(QHBoxLayout())
        self.gbChartDim.layout().addWidget(self.rb2DChartDim)
        self.gbChartDim.layout().addWidget(self.rb3DChartDim)
        self.gbChartDim.layout().addWidget(self.cbxDepthShade)
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

        self.plot_tab.addTab(self.plot_data, "PCA result")
        self.plot_tab.addTab(self.rotation_matrix_data, "Rotation matrix")
        self.plot_tab.addTab(self.eigenvalue_data, "Eigen value")


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
        self.main_hsplitter.addWidget(self.tableView)
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
        self.rbCVA = QRadioButton("CVA")
        self.rbPCA.setChecked(True)
        self.rbCVA.setEnabled(False)
        self.gbAnalysis = QGroupBox()
        self.gbAnalysis.setTitle("Analysis")
        self.gbAnalysis.setLayout(QHBoxLayout())
        self.gbAnalysis.layout().addWidget(self.rbPCA)
        self.gbAnalysis.layout().addWidget(self.rbCVA)
        self.gbAnalysis.setMaximumHeight(rbbox_height)
        self.btnAnalyze = QPushButton("Perform Analysis")
        self.btnAnalyze.clicked.connect(self.on_btnAnalyze_clicked)
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
            self.on_btnPCA_clicked()

            self.btnSaveResults.setFocus()

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
            self.plot_widget2.show()
            self.plot_widget3.hide()
            self.toolbar2.show()
            self.toolbar3.hide()
            self.gbAxis3.hide()
            self.comboAxis3.hide()
            self.cbxFlipAxis3.hide()
            self.cbxDepthShade.hide()
        else:
            self.plot_widget3.show()
            self.plot_widget2.hide()
            self.toolbar2.hide()
            self.toolbar3.show()
            self.gbAxis3.show()
            self.comboAxis3.show()
            self.cbxFlipAxis3.show()
            self.cbxDepthShade.show()

        if self.ds_ops is not None:
            self.show_pca_result()

    def set_dataset(self, dataset):
        #print("dataset:", dataset)
        self.dataset = dataset
        prev_lm_count = -1
        for obj in dataset.object_list:
            obj.unpack_landmark()
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
        if self.ds_ops is not None:
            self.show_pca_result()

    def axis_changed(self):
        if self.ds_ops is not None:
            self.show_pca_result()

    def flip_axis_changed(self, int):
        if self.ds_ops is not None:
            self.show_pca_result()

    def on_btnSuperimpose_clicked(self):
        print("on_btnSuperimpose_clicked")

    def on_btnAnalyze_clicked(self):
        #print("on_btnAnalyze_clicked")
        self.selected_object_id_list = []
        self.ds_ops.selected_object_id_list = self.selected_object_id_list
        self.load_object()
        self.on_object_selection_changed([],[])
        self.show_pca_result()
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
            header = [ "object_name" ]
            header.extend( ["PC"+str(i+1) for i in range(len(self.pca_result.rotated_matrix.tolist()[0]))] )
            worksheet = doc.add_worksheet("PCA coordinates")
            row_index = 0
            column_index = 0

            for colname in header:
                worksheet.write(row_index, column_index, colname )
                column_index+=1
            
            new_coords = self.pca_result.rotated_matrix.tolist()
            for i, obj in enumerate(self.ds_ops.object_list):
                worksheet.write(i+1, 0, obj.object_name )
                for j, val in enumerate(new_coords[i]):
                    worksheet.write(i+1, j+1, val )
                    #self.plot_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))

            worksheet = doc.add_worksheet("Rotation matrix")
            row_index = 0
            column_index = 0
            rotation_matrix = self.pca_result.rotation_matrix.tolist()
            #print("rotation_matrix[0][0]", [0][0], len(self.pca_result.rotation_matrix[0][0]))
            for i, row in enumerate(rotation_matrix):
                for j, val in enumerate(row):
                    worksheet.write(i, j, val )                  

            worksheet = doc.add_worksheet("Eigenvalues")
            for i, val in enumerate(self.pca_result.raw_eigen_values):
                val2 = self.pca_result.eigen_value_percentages[i]
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

    def on_btnPCA_clicked(self):
        #print("pca button clicked")

        self.ds_ops = MdDatasetOps(self.dataset)

        self.ds_ops.procrustes_superimposition()
        self.show_object_shape()

        if self.dataset.object_list is None or len(self.dataset.object_list) < 5:
            print("too small number of objects for PCA analysis")            
            return

        self.pca_result = self.PerformPCA(self.ds_ops)
        new_coords = self.pca_result.rotated_matrix.tolist()
        for i, obj in enumerate(self.ds_ops.object_list):
            obj.pca_result = new_coords[i]

        self.show_pca_result()
        #print("pca_result.nVariable:",pca_result.nVariable)
        #with open('pca_result.txt', 'w') as f:
        #    for obj in ds_ops.object_list:
        #        f.write(obj.object_name + "\t" + "\t".join([str(x) for x in obj.pca_result]) + "\n")

    def show_pca_result(self):
        #self.plot_widget.clear()

        self.show_pca_table()
        # get axis1 and axis2 value from comboAxis1 and 2 index
        depth_shade = self.cbxDepthShade.isChecked()
        axis1 = self.comboAxis1.currentIndex() +1
        axis2 = self.comboAxis2.currentIndex() +1
        axis3 = self.comboAxis3.currentIndex() +1
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() == True else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() == True else 1.0
        flip_axis3 = -1.0 if self.cbxFlipAxis3.isChecked() == True else 1.0

        symbol_candidate = ['o','s','^','x','+','d','v','<','>','p','h']
        color_candidate = ['blue','green','black','cyan','magenta','yellow','white','gray','red']
        self.propertyname_index = self.comboPropertyName.currentIndex() -1
        self.scatter_data = {}
        self.scatter_result = {}

        key_list = []
        key_list.append('__default__')
        self.scatter_data['__default__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':'blue', 'size':50}
        if len(self.selected_object_id_list) > 0:
            self.scatter_data['__selected__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':'red', 'size':100}
            key_list.append('__selected__')

        for obj in self.ds_ops.object_list:
            key_name = '__default__'

            if obj.id in self.selected_object_id_list:
                key_name = '__selected__'
            elif self.propertyname_index > -1 and self.propertyname_index < len(obj.property_list):
                key_name = obj.property_list[self.propertyname_index]

            if key_name not in self.scatter_data.keys():
                self.scatter_data[key_name] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'property':key_name, 'symbol':'', 'color':'', 'size':50}

            self.scatter_data[key_name]['x_val'].append(flip_axis1 * obj.pca_result[axis1])
            self.scatter_data[key_name]['y_val'].append(flip_axis2 * obj.pca_result[axis2])
            self.scatter_data[key_name]['z_val'].append(flip_axis3 * obj.pca_result[axis3])
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
            self.fig3.tight_layout()
            self.fig3.canvas.draw()
            self.fig3.canvas.flush_events()
            self.fig3.canvas.mpl_connect('pick_event',self.on_pick)
            self.fig3.canvas.mpl_connect('button_press_event', self.on_canvas_button_press)
            self.fig3.canvas.mpl_connect('button_release_event', self.on_canvas_button_release)

    def show_pca_table(self):
        self.plot_data.clear()
        self.rotation_matrix_data.clear()

        # PCA data
        # set header as "PC1", "PC2", "PC3", ... "PCn
        header = ["PC"+str(i+1) for i in range(len(self.pca_result.rotated_matrix.tolist()[0]))]
        #print("header", header)
        self.plot_data.setColumnCount(len(header)+1)
        self.plot_data.setHorizontalHeaderLabels(["Name"] + header)

        new_coords = self.pca_result.rotated_matrix.tolist()
        self.plot_data.setColumnCount(len(new_coords[0])+1)
        for i, obj in enumerate(self.ds_ops.object_list):
            self.plot_data.insertRow(i)
            self.plot_data.setItem(i, 0, QTableWidgetItem(obj.object_name))
            for j, val in enumerate(new_coords[i]):
                self.plot_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))

        # rotation matrix
        rotation_matrix = self.pca_result.rotation_matrix.tolist()
        #print("rotation_matrix[0][0]", [0][0], len(self.pca_result.rotation_matrix[0][0]))
        self.rotation_matrix_data.setColumnCount(len(rotation_matrix[0]))
        for i, row in enumerate(rotation_matrix):
            self.rotation_matrix_data.insertRow(i)
            for j, val in enumerate(row):
                self.rotation_matrix_data.setItem(i, j, QTableWidgetItem(str(int(val*10000)/10000.0)))
        
        # eigen values
        self.eigenvalue_data.setColumnCount(2)
        for i, val in enumerate(self.pca_result.raw_eigen_values):
            val2 = self.pca_result.eigen_value_percentages[i]
            self.eigenvalue_data.insertRow(i)
            self.eigenvalue_data.setItem(i, 0, QTableWidgetItem(str(int(val*10000)/10000.0)))
            self.eigenvalue_data.setItem(i, 1, QTableWidgetItem(str(int(val2*10000)/10000.0)))


        #self.eigen_value_percentages.append(ss / sum)
        #self.raw_eigen_values = s
        #self.loading = v


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
            self.tableView.selectionModel().clearSelection()


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
            self.tableView.selectionModel().select(item.index(),QItemSelectionModel.Rows | QItemSelectionModel.Select)
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
                    self.tableView.selectRow(row)
                    #break
            

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
        self.reset_tableView()
        if self.dataset is None:
            return
        #objects = self.selected_dataset.objects
        self.object_hash = {}
        for obj in self.dataset.object_list:
            item1 = QStandardItem()
            item1.setData(obj.id,Qt.DisplayRole)
            item2 = QStandardItem(obj.object_name)
            self.object_hash[obj.id] = item1
            self.object_model.appendRow([item1,item2] )
        

    def reset_tableView(self):
        self.object_model = QStandardItemModel()
        self.object_model.setColumnCount(2)
        self.object_model.setHorizontalHeaderLabels(["", "Name"])
        self.tableView.setModel(self.object_model)
        self.tableView.setColumnWidth(0, 30)
        self.tableView.setColumnWidth(1, 200)
        self.tableView.verticalHeader().setDefaultSectionSize(20)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        #self.tableView.clicked.connect(self.on_tableView_clicked)
        self.object_selection_model = self.tableView.selectionModel()
        self.object_selection_model.selectionChanged.connect(self.on_object_selection_changed)
        self.tableView.setSortingEnabled(True)
        self.tableView.sortByColumn(0, Qt.AscendingOrder)
        self.object_model.setSortRole(Qt.UserRole)

        header = self.tableView.horizontalHeader()    
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableView.setStyleSheet("QTreeView::item:selected{background-color: palette(highlight); color: palette(highlightedText);};")

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
            self.show_pca_result()
            self.ds_ops.selected_object_id_list = self.selected_object_id_list
            self.show_object_shape()

        
        #self.selected_object = MdObject.get_by_id(object_id)
        #print("selected_object:",self.selected_object)
        #self.show_object(self.selected_object)

    def get_selected_object_id_list(self):
        selected_indexes = self.tableView.selectionModel().selectedRows()
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
        self.setWindowTitle("Export Dataset")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 600, 400))
        self.move(self.parent.pos()+QPoint(100,100))

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
        self.rbX1Y1 = QRadioButton("X1Y1")
        self.rbX1Y1.clicked.connect(self.on_rbX1Y1_clicked)
        self.rbX1Y1.setEnabled(True)
        self.rbX1Y1.setChecked(False)
        self.rbMorphologika = QRadioButton("Morphologika")
        self.rbMorphologika.clicked.connect(self.on_rbMorphologika_clicked)
        self.rbMorphologika.setEnabled(False)
        self.rbMorphologika.setChecked(False)

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

        if self.rbTPS.isChecked():
            today = datetime.datetime.now()
            date_str = today.strftime("%Y%m%d_%H%M%S")
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
                        #pass#
        self.close()

class ImportDatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Import Dataset")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 600, 400))
        self.move(self.parent.pos()+QPoint(100,100))

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
        self.rbnX1Y1 = QRadioButton("X1Y1")
        self.rbnMorphologika = QRadioButton("Morphologika")
        self.chkFileType.addButton(self.rbnTPS)
        self.chkFileType.addButton(self.rbnX1Y1)
        self.chkFileType.addButton(self.rbnMorphologika)
        self.chkFileType.buttonClicked.connect(self.file_type_changed)
        self.chkFileType.setExclusive(True)
        # add qgroupbox for file type
        self.gbxFileType = QGroupBox()
        self.gbxFileType.setLayout(QHBoxLayout())
        self.gbxFileType.layout().addWidget(self.rbnTPS)
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
            elif self.file_ext.lower() == ".x1y1":
                self.rbnX1Y1.setChecked(True)
                self.file_type_changed()
            elif self.file_ext.lower() == ".txt":
                self.rbnMorphologika.setChecked(True)
                self.file_type_changed()
            else:
                self.rbnTPS.setChecked(False)
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
        self.btnImport.setEnabled(False)
        self.prgImport.setValue(0)
        self.prgImport.setFormat("Importing...")
        self.prgImport.update()
        self.prgImport.repaint()

        filename = self.edtFilename.text()
        filetype = self.chkFileType.checkedButton().text()
        datasetname = self.edtDatasetName.text()
        objectcount = self.edtObjectCount.text()
        if filetype == "TPS":
            self.import_tps(filename, datasetname)            
        else:
            pass

    def import_tps(self, filename, datasetname):
        # read tps file
        tps = TPS(filename, datasetname)
        self.edtObjectCount.setText(str(tps.nobjects))
        #print("objects:", tps.nobjects,tps.nlandmarks,tps.object_name_list)
        # create dataset
        dataset = MdDataset()
        dataset.dataset_name = datasetname
        dataset.dimension = tps.dimension
        dataset.save()
        # add objects
        for i in range(tps.nobjects):
            object = MdObject()
            object.object_name = tps.object_name_list[i]
            #print("object:", object.object_name)
            object.dataset = dataset
            object.landmark_str = ""
            landmark_list = []
            for landmark in tps.landmark_data[tps.object_name_list[i]]:
                landmark_list.append("\t".join([ str(x) for x in landmark]))
            object.landmark_str = "\n".join(landmark_list)

            object.save()
            val = int( (float(i+1)*100.0 / float(tps.nobjects)) )
            #print("progress:", i+1, tps.nobjects, val)
            self.update_progress(val)
            #progress = int( (i / float(tps.nobjects)) * 100)

        #print("tps import done")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("Finished importing a TPS file.")
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

class TPS:
    def __init__(self, filename, datasetname):
        self.filename = filename
        self.datasetname = datasetname
        self.dimension = 0
        self.nobjects = 0
        self.object_name_list = []
        self.landmark_str_list = []
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
            header = ''
            comment = ''
            image_count = 0
            for line in tps_lines:
                line = line.strip()
                if line == '':
                    continue
                if line.startswith("#"):
                    continue
                headerline = re.search('^(\w+)(\s*)=(\s*)(\d+)(.*)', line)
                if headerline == None:
                    if header == 'lm':
                        point = [ float(x) for x in re.split('\s+', line)]
                        if len(point) > 2 and self.isNumber(point[2]):
                            threed += 1
                        else:
                            twod += 1

                        if len(point)>1:
                            data.append(point)
                    continue
                elif headerline.group(1).lower() == "lm":
                    if len(data) > 0:
                        if comment != '':
                            key = comment
                        else:
                            key = self.datasetname + "_" + str(object_count)
                        objects[key] = data
                        object_name_list.append(key)
                        data = []
                    header = 'lm'
                    landmark_count, comment = int(headerline.group(4)), headerline.group(5).strip()
                    #print("landmark_count:", landmark_count, "object_count:", object_count, "comment:", comment)
                    object_count += 1
                    # landmark_count_list.append( landmark_count )
                    # if not found:
                    #found = True
                elif headerline.group(1).lower() == "image":
                    image_count += 1

            if len(data) > 0:
                if comment != '':
                    key = comment
                else:
                    key = self.datasetname + "_" + str(object_count)
                #print("key:", key, "data:", data)
                objects[key] = data
                object_name_list.append(key)
                data = []

            if object_count == 0 and landmark_count == 0:
                return None

            if threed > twod:
                self.dimension = 3
            else:
                self.dimension = 2

            self.nobjects = len(object_name_list)
            self.nlandmarks = landmark_count
            self.landmark_data = objects
            self.object_name_list = object_name_list

            return dataset

class DatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Dataset")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 600, 400))
        self.move(self.parent.pos()+QPoint(100,100))

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
        self.edtPropertyNameStr = QTextEdit()

        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addRow("Parent", self.cbxParent)
        self.main_layout.addRow("Dataset Name", self.edtDatasetName)
        self.main_layout.addRow("Description", self.edtDatasetDesc)
        self.main_layout.addRow("Dimension", dim_layout)
        self.main_layout.addRow("Wireframe", self.edtWireframe)
        self.main_layout.addRow("Baseline", self.edtBaseline)
        self.main_layout.addRow("Polygons", self.edtPolygons)
        self.main_layout.addRow("Property Name List", self.edtPropertyNameStr)


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
        self.dataset.polygons = self.edtPolygons.toPlainText()
        self.dataset.propertyname_str = self.edtPropertyNameStr.toPlainText()

        #self.data
        #print(self.dataset.dataset_desc, self.dataset.dataset_name)
        self.dataset.save()
        self.accept()

    def Delete(self):
        ret = QMessageBox.question(self, "", "Are you sure to delete this dataset?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        print("ret:", ret)
        if ret == QMessageBox.Yes:
            self.dataset.delete_instance()
            self.parent.selected_dataset = None
            #self.dataset.delete_dataset()
        #self.delete_dataset()
        self.accept()

    def Cancel(self):
        self.reject()


class PicButton(QAbstractButton):
    def __init__(self, pixmap, pixmap_hover, pixmap_pressed, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap
        self.pixmap_hover = pixmap_hover
        self.pixmap_pressed = pixmap_pressed

        self.pressed.connect(self.update)
        self.released.connect(self.update)

    def paintEvent(self, event):
        pix = self.pixmap_hover if self.underMouse() else self.pixmap
        if self.isDown():
            pix = self.pixmap_pressed

        painter = QPainter(self)
        painter.drawPixmap(self.rect(), pix)

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()

    def sizeHint(self):
        return QSize(200, 200)

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
        self.setGeometry(QRect(0, 0, 400, 300))
        self.setWindowTitle("설정")
        #self.lbl_main_view.setMinimumSize(400, 300)

        self.lblServerAddress = QLabel()
        self.edtServerAddress = QLineEdit()
        self.edtServerPort = QLineEdit()
        self.lblDataFolder = QLabel()
        self.edtDataFolder = QLineEdit()

        self.edtServerPort.setFixedWidth(50)

        self.btnDataFolder = QPushButton()
        self.btnDataFolder.setText("선택")
        self.btnDataFolder.clicked.connect(self.select_folder)

        self.btnOkay = QPushButton()
        self.btnOkay.setText("확인")
        self.btnOkay.clicked.connect(self.Okay)

        self.btnCancel = QPushButton()
        self.btnCancel.setText("취소")
        self.btnCancel.clicked.connect(self.Cancel)


        self.layout = QVBoxLayout()
        self.layout1 = QHBoxLayout()
        self.layout1.addWidget(self.lblServerAddress)
        self.layout1.addWidget(self.edtServerAddress)
        self.layout1.addWidget(self.edtServerPort)
        self.layout3 = QHBoxLayout()
        self.layout3.addWidget(self.lblDataFolder)
        self.layout3.addWidget(self.edtDataFolder)
        self.layout3.addWidget(self.btnDataFolder)
        self.layout4 = QHBoxLayout()
        self.layout4.addWidget(self.btnOkay)
        self.layout4.addWidget(self.btnCancel)
        self.layout.addLayout(self.layout1)
        #self.layout.addLayout(self.layout2)
        self.layout.addLayout(self.layout3)
        self.layout.addLayout(self.layout4)
        self.setLayout(self.layout)
        self.server_address = ''
        self.server_port = ''
        self.data_folder = ''
        #print("pref dlg data_folder:", self.data_folder)
        self.read_settings()
        #print("pref dlg data_folder:", self.data_folder)
        self.lblServerAddress.setText("서버 주소")
        #self.lblServerPort.setText("Server Port")
        self.lblDataFolder.setText("사진 위치")

        #self.edtDataFolder.setText(str(self.data_folder.resolve()))
        self.edtServerAddress.setText(self.server_address)
        self.edtServerPort.setText(self.server_port)

    def write_settings(self):
        self.parent.server_address = self.edtServerAddress.text()
        self.parent.server_port = self.edtServerPort.text()
        self.parent.data_folder = Path(self.edtDataFolder.text())
        #print( self.parent.server_address,self.parent.server_port, self.parent.data_folder)

    def read_settings(self):
        self.server_address = self.parent.server_address
        self.server_port = self.parent.server_port
        self.data_folder = self.parent.data_folder.resolve()
        #print("pref dlg data folder:", self.data_folder)
        #print("pref dlg server address:", self.server_address)

    def Okay(self):
        self.write_settings()
        self.close()

    def Cancel(self):
        self.close()

    def select_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "폴더 선택", str(self.data_folder)))
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