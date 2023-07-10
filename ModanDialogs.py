from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, QStatusBar,\
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QAction, QMenu, QSizePolicy, \
                            QTableWidget, QBoxLayout, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox 

from PyQt5 import QtGui, uic
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem,\
                        QPainterPath, QFont, QImageReader, QPainter, QBrush, QMouseEvent, QWheelEvent, QDrag
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QEvent, QRegExp, QSize, QPoint,\
                         pyqtSignal, QThread, QMimeData, pyqtSlot

import pyqtgraph as pg
import pyqtgraph.opengl as gl

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
MODE_NONE = 0
MODE_PAN = 12
MODE_EDIT_LANDMARK = 1
MODE_WIREFRAME = 2
MODE_READY_MOVE_LANDMARK = 3
MODE_MOVE_LANDMARK = 4
MODE_PRE_WIRE_FROM = 5


LANDMARK_RADIUS = 3
DISTANCE_THRESHOLD = LANDMARK_RADIUS * 3

IMAGE_EXTENSION_LIST = ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']

class LandmarkEditor(QLabel):
    #clicked = pyqtSignal()
    def __init__(self, widget):
        super(LandmarkEditor, self).__init__(widget)
        self.object_dialog = None
        self.setAcceptDrops(True)
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.scale = 1.0
        self.fullpath = None
        self.temp_pan_x = 0
        self.temp_pan_y = 0
        self.mouse_down_x = 0
        self.mouse_down_y = 0
        self.pan_x = 0
        self.pan_y = 0
        self.setMouseTracking(True)
        self.pan_mode = MODE_NONE
        self.set_mode(MODE_EDIT_LANDMARK)
        #self.edit_mode = MODE_ADD_LANDMARK
        self.first_resize = True
        self.curr_mouse_x = 0
        self.curr_mouse_y = 0
        self.image_canvas_ratio = 1.0
        self.setMinimumSize(640,480)
        self.show_index = True
        self.show_wireframe = True
        self.show_baseline = False  
        self.edit_mode = MODE_NONE
        self.selected_landmark_index = -1
        self.landmark_list = []
        self.wire_hover_index = -1
        self.wire_start_index = -1
        self.wire_end_index = -1
        self.selected_edge_index = -1
        
        #self.repaint()

#function _2canx( coord ) { return Math.round(( coord / gImageCanvasRatio ) * gScale) + gPanX + gTempPanX; }
#function _2cany( coord ) { return Math.round(( coord / gImageCanvasRatio ) * gScale) + gPanY + gTempPanY; }
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
        self.curr_mouse_x = me.x()
        self.curr_mouse_y = me.y()
        curr_pos = [self.curr_mouse_x, self.curr_mouse_y]
    
        #print("mouse move event", me, me.pos(), self.curr_mouse_x, self.curr_mouse_y, self._2imgx(self.curr_mouse_x), self._2imgy(self.curr_mouse_y))
        if self.pan_mode == MODE_PAN:
            self.temp_pan_x = self.curr_mouse_x - self.mouse_down_x
            self.temp_pan_y = self.curr_mouse_y - self.mouse_down_y
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
                self.landmark_list[self.selected_landmark_index] = [self._2imgx(self.curr_mouse_x), self._2imgy(self.curr_mouse_y)]
                if self.object_dialog is not None:
                    self.object_dialog.update_landmark(self.selected_landmark_index, *self.landmark_list[self.selected_landmark_index])
                #self.repaint()
                #print("landmark list", self.landmark_list)
        elif self.edit_mode == MODE_READY_MOVE_LANDMARK:
            curr_pos = [self.curr_mouse_x, self.curr_mouse_y]
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
                img_x = self._2imgx(self.curr_mouse_x)
                img_y = self._2imgy(self.curr_mouse_y)
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
        painter.fillRect(self.rect(), QBrush(QColor(100,100,100)))

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
            painter.setPen(QPen(Qt.blue, 2))
            painter.setBrush(QBrush(Qt.white))

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
                painter.setPen(QPen(Qt.yellow, 2))
                [ from_x, from_y ] = self.landmark_list[edge[0]]
                [ to_x, to_y ] = self.landmark_list[edge[1]]
                painter.drawLine(int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y)))



        radius = LANDMARK_RADIUS
        painter.setPen(QPen(Qt.red, 2))
        painter.setBrush(QBrush(Qt.white))
        if self.edit_mode == MODE_EDIT_LANDMARK:
            img_x = self._2imgx(self.curr_mouse_x)
            img_y = self._2imgy(self.curr_mouse_y)
            if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                pass
            else:
                pass
                #painter.drawEllipse(self.curr_mouse_x-radius, self.curr_mouse_y-radius, radius*2, radius*2)

        #print(landmark_list)

        #print("font:", painter.font().family(), painter.font().pointSize(), painter.font().pixelSize())
        painter.setFont(QFont('Arial', 14))
        for idx, landmark in enumerate(self.landmark_list):
            if idx == self.wire_hover_index:
                painter.setPen(QPen(Qt.blue, 2))
                painter.setBrush(QBrush(Qt.yellow))
                print("wire hover idx", idx)
            elif idx == self.wire_start_index or idx == self.wire_end_index:
                painter.setPen(QPen(Qt.blue, 2))
                painter.setBrush(QBrush(Qt.blue))
                print("wire start/end idx", idx)
            else:
                painter.setPen(QPen(Qt.red, 2))
                painter.setBrush(QBrush(Qt.white))
            painter.drawEllipse(self._2canx(int(landmark[0]))-radius, self._2cany(int(landmark[1]))-radius, radius*2, radius*2)
            if self.show_index == True:
                painter.drawText(self._2canx(int(landmark[0]))+10, self._2cany(int(landmark[1]))+10, str(idx+1))


        # draw wireframe being edited
        if self.wire_start_index >= 0:
            painter.setPen(QPen(Qt.blue, 2))
            painter.setBrush(QBrush(Qt.blue))
            start_lm = self.landmark_list[self.wire_start_index]
            #painter.drawEllipse(self._2canx(int(start_lm[0]))-radius*2, self._2cany(int(start_lm[1]))-radius, radius*2, radius*2)
            # draw line from start to mouse
            painter.drawLine(self._2canx(int(start_lm[0])), self._2cany(int(start_lm[1])), self.curr_mouse_x, self.curr_mouse_y)


        #r = QRect(0, self.height() - 20, self.width(), 20)
        #painter.fillRect(r, QBrush(Qt.blue))
        #pen = QPen(QColor("red"), 10)
        #painter.setPen(pen)
        #painter.drawRect(self.rect())
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
            self.first_resize = False
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
        #print("set_object", object.object_name)
        m_app = QApplication.instance()
        self.object = object
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
        self.landmark_list = []
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.update()    

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

        self.image_label = LandmarkEditor(self)
        self.image_label.object_dialog = self
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        #self.image_label.clicked.connect(self.on_image_clicked)

        self.pixmap = QPixmap(1024,768)
        self.image_label.setPixmap(self.pixmap)

        self.form_layout = QFormLayout()
        self.form_layout.addRow("Dataset Name", self.lblDataset)
        self.form_layout.addRow("Object Name", self.edtObjectName)
        self.form_layout.addRow("Object Desc", self.edtObjectDesc)
        self.form_layout.addRow("Landmarks", self.edtLandmarkStr)
        self.form_layout.addRow("", self.inputCoords)

        self.btnGroup = QButtonGroup() 
        self.btnLandmark = PicButton(QPixmap("icon/landmark.png"), QPixmap("icon/landmark_hover.png"), QPixmap("icon/landmark_down.png"))
        self.btnWireframe = PicButton(QPixmap("icon/wireframe.png"), QPixmap("icon/wireframe_hover.png"), QPixmap("icon/wireframe_down.png"))
        self.btnGroup.addButton(self.btnLandmark, 0)
        self.btnGroup.addButton(self.btnLandmark, 0)
        self.btnLandmark.setCheckable(True)
        self.btnWireframe.setCheckable(True)
        self.btnLandmark.setChecked(True)
        self.btnWireframe.setChecked(False)
        self.btnLandmark.setAutoExclusive(True)
        self.btnWireframe.setAutoExclusive(True)
        self.btnLandmark.clicked.connect(self.btnLandmark_clicked)
        self.btnWireframe.clicked.connect(self.btnWireframe_clicked)
        self.btnLandmark.setFixedSize(32,32)
        self.btnWireframe.setFixedSize(32,32)
        self.btn_layout2 = QGridLayout()
        self.btn_layout2.addWidget(self.btnLandmark,0,0)
        self.btn_layout2.addWidget(self.btnWireframe,0,1)

        self.cbxShowIndex = QCheckBox()
        self.cbxShowIndex.setText("Index")
        self.cbxShowIndex.setChecked(True)
        self.cbxShowWireframe = QCheckBox()
        self.cbxShowWireframe.setText("Wireframe")
        self.cbxShowWireframe.setChecked(True)
        self.cbxShowBaseline = QCheckBox()
        self.cbxShowBaseline.setText("Baseline")
        self.cbxShowBaseline.setChecked(True)

        self.left_widget = QWidget()
        self.left_widget.setLayout(self.form_layout)

        self.right_top_widget = QWidget()
        self.right_top_widget.setLayout(self.btn_layout2)
        self.right_middle_widget = QWidget()
        self.right_middle_layout = QVBoxLayout()
        self.right_middle_layout.addWidget(self.cbxShowIndex)
        self.right_middle_layout.addWidget(self.cbxShowWireframe)
        self.right_middle_layout.addWidget(self.cbxShowBaseline)
        self.right_middle_widget.setLayout(self.right_middle_layout)
        self.right_bottom_widget = QWidget()
        self.vsplitter.addWidget(self.right_top_widget)
        self.vsplitter.addWidget(self.right_middle_widget)
        self.vsplitter.addWidget(self.right_bottom_widget)
        self.vsplitter.setSizes([50,50,400])
        self.vsplitter.setStretchFactor(0, 0)
        self.vsplitter.setStretchFactor(1, 0)
        self.vsplitter.setStretchFactor(2, 1)

        self.hsplitter.addWidget(self.left_widget)
        self.hsplitter.addWidget(self.image_label)
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


        #self.main_layout.addLayout(self.sub_layout)
        self.main_layout.addWidget(self.hsplitter)
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.status_bar)

        self.dataset = None
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.m_app = QApplication.instance()
        self.btnLandmark_clicked()

        self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)

    def show_index_state_changed(self, int):
        if self.cbxShowIndex.isChecked():
            self.image_label.show_index = True
            #print("show index CHECKED!")
        else:
            self.image_label.show_index = False
            #print("show index UNCHECKED!")
        self.image_label.update()

    def show_baseline_state_changed(self, int):
        if self.cbxShowBaseline.isChecked():
            self.image_label.show_baseline = True
            #print("show index CHECKED!")
        else:
            self.image_label.show_baseline = False
            #print("show index UNCHECKED!")
        self.image_label.update()

    def show_wireframe_state_changed(self, int):
        if self.cbxShowWireframe.isChecked():
            self.image_label.show_wireframe = True
            #print("show index CHECKED!")
        else:
            self.image_label.show_wireframe = False
            #print("show index UNCHECKED!")
        self.image_label.update()

        #self.edtDataFolder.setText(str(self.data_folder.resolve()))
        #self.edtServerAddress.setText(self.server_address)
        #self.edtServerPort.setText(self.server_port)

    '''
    @pyqtSlot()
    def on_image_clicked(self,event):
        print("clicked")
        print(event.pos())
        #pass
    '''

    def btnLandmark_clicked(self):
        #self.edit_mode = MODE_ADD_LANDMARK
        self.image_label.set_mode(MODE_EDIT_LANDMARK)
        self.image_label.update()
        self.btnLandmark.setDown(True)
        self.btnLandmark.setChecked(True)
        self.btnWireframe.setDown(False)
        self.btnWireframe.setChecked(False)

    def btnWireframe_clicked(self):
        #self.edit_mode = MODE_ADD_LANDMARK
        self.image_label.set_mode(MODE_WIREFRAME)
        self.image_label.update()
        self.btnWireframe.setDown(True)
        self.btnWireframe.setChecked(True)
        self.btnLandmark.setDown(False)
        self.btnLandmark.setChecked(False)

    def set_object_name(self, name):
        #print("set_object_name", self.edtObjectName.text(), name)

        if self.edtObjectName.text() == "":
            self.edtObjectName.setText(name)

    def set_dataset(self, dataset):
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
            self.inputZ.hide()
            input_width = 80
        elif self.dataset.dimension == 3:
            self.edtLandmarkStr.setColumnCount(3)
            self.edtLandmarkStr.setHorizontalHeaderLabels(["X","Y","Z"])
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            self.inputZ.show()
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
            self.landmark_list.append([x,y])
        elif self.dataset.dimension == 3:
            self.landmark_list.append([x,y,z])
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

    def show_landmarks(self):
        self.edtLandmarkStr.setRowCount(len(self.landmark_list))
        for idx, lm in enumerate(self.landmark_list):

            item_x = QTableWidgetItem(str(float(lm[0]*1.0)))
            item_x.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            self.edtLandmarkStr.setItem(idx, 0, item_x)

            item_y = QTableWidgetItem(str(float(lm[1]*1.0)))
            item_y.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            self.edtLandmarkStr.setItem(idx, 1, item_y)

            if self.dataset.dimension == 3:
                item_z = QTableWidgetItem(str(float(lm[2]*1.0)))
                item_z.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                self.edtLandmarkStr.setItem(idx, 2, item_z)

    def set_object(self, object):
        #print("set_object", self.image_label.size())
        self.object = object
        self.edtObjectName.setText(object.object_name)
        self.edtObjectDesc.setText(object.object_desc)
        #self.edtLandmarkStr.setText(object.landmark_str)
        self.landmark_list = object.unpack_landmark()
        #for lm in self.landmark_list:
        #    self.show_landmark(*lm)
        self.show_landmarks()

        if len(self.dataset.propertyname_list) >0:
            self.object.unpack_property()
            self.dataset.unpack_propertyname_str()
            for idx, propertyname in enumerate(self.dataset.propertyname_list):
                if idx < len(object.property_list):
                    self.edtPropertyList[idx].setText(object.property_list[idx])

        if object.image is not None and len(object.image) > 0:
            img = object.image[0]
            image_path = img.get_image_path(self.m_app.storage_directory)
            #check if image_path exists
            if os.path.exists(image_path):
                self.image_label.set_image(image_path)
                self.image_label.set_object(object)
                self.image_label.landmark_list = self.landmark_list
        #self.set_dataset(object.dataset)

    def save_object(self):

        if self.object is None:
            self.object = MdObject()
        self.object.dataset_id = self.dataset.id
        self.object.object_name = self.edtObjectName.text()
        self.object.object_desc = self.edtObjectDesc.toPlainText()
        #self.object.landmark_str = self.edtLandmarkStr.text()
        self.object.landmark_str = self.make_landmark_str()
        if self.dataset.propertyname_str is not None and self.dataset.propertyname_str != "":
            self.object.property_str = ",".join([ edt.text() for edt in self.edtPropertyList ])

        self.object.save()
        if self.image_label.fullpath is not None and self.object.image.count() == 0:
            md_image = MdImage()
            md_image.object_id = self.object.id
            md_image.load_file_info(self.image_label.fullpath)
            new_filepath = md_image.get_image_path( self.m_app.storage_directory)
            if not os.path.exists(os.path.dirname(new_filepath)):
                os.makedirs(os.path.dirname(new_filepath))
            #print("save object new filepath:", new_filepath)
            shutil.copyfile(self.image_label.fullpath, new_filepath)
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
        painter.fillRect(self.rect(), QBrush(QColor(100,100,100)))

        if self.ds_ops is None:
            return

        if self.show_wireframe == True:
            painter.setPen(QPen(Qt.blue, 2))
            painter.setBrush(QBrush(Qt.white))

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
                painter.setPen(QPen(Qt.yellow, 2))
                painter.setBrush(QBrush(Qt.yellow))
            else:
                painter.setPen(QPen(Qt.red, 2))
                painter.setBrush(QBrush(Qt.white))
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
                painter.setPen(QPen(Qt.blue, 2))
                painter.setBrush(QBrush(Qt.white))
                x = self._2canx(landmark[0])
                y = self._2cany(landmark[1])
                painter.drawEllipse(x-radius, y-radius, radius*2, radius*2)
                if self.show_index:
                    painter.drawText(x+10, y+10, str(idx+1))

    def _2canx(self, x):
        return int(x*self.scale + self.pan_x)
    def _2cany(self, y):
        return int(y*self.scale + self.pan_y)
class MyGLViewWidget(gl.GLViewWidget):
    def __init__(self, widget):
        super(MyGLViewWidget, self).__init__(widget)
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


class DatasetAnalysisDialog(QDialog):
    def __init__(self,parent,dataset):
        super().__init__()
        self.setWindowTitle("Assorted Analyses")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 1200, 800))
        self.move(self.parent.pos()+QPoint(100,100))
        #print("dataset:",dataset.dataset_name)
        self.ds_ops = None
        
        self.hsplitter = QSplitter(Qt.Horizontal)

        self.lblShape2 = DatasetOpsViewer(self)
        self.lblShape2.setAlignment(Qt.AlignCenter)
        self.lblShape2.setMinimumWidth(400)
        #self.lblShape.setMaximumWidth(200)
        self.lblShape2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.lblGraph = QLabel("Graph")
        self.lblGraph.setAlignment(Qt.AlignCenter)
        self.lblGraph.setMinimumWidth(400)
        #self.lblGraph.setMaximumWidth(200)
        self.lblGraph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.tableView = QTableView()
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        #self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableView.setSortingEnabled(True)
        #self.tableView.setAlternatingRowColors(True)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.tableView.customContextMenuRequested.connect(self.show_context_menu)
        self.tableView.setSortingEnabled(True)

        #self.plot_widget = pg.PlotWidget()
        #self.plot_widget.setBackground('w')

        self.plot_widget2 = FigureCanvas(Figure(figsize=(20, 16),dpi=100))
        self.plot_widget3 = FigureCanvas(Figure(figsize=(20, 16),dpi=100))
        self.fig2 = self.plot_widget2.figure
        self.ax2 = self.fig2.add_subplot()
        self.fig3 = self.plot_widget3.figure
        self.ax3 = self.fig3.add_subplot(projection='3d')

        #sc = MplCanvas(self, width=5, height=4, dpi=100)
        #sc.axes.plot([0,1,2,3,4], [10,1,20,3,40])

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        self.toolbar2 = NavigationToolbar(self.plot_widget2, self)
        self.toolbar3 = NavigationToolbar(self.plot_widget3, self)        

        #fig = plt.figure()
        
        #self.ax.set_axis_off()
        #self.ax.set_xticks([])
        #self.ax.set_yticks([])
        #self.ax.set_zticks([])
        #self.ax.grid(False)


        #self.plot_widget = pg.useOpenGL.GLViewWidget()        

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
        self.checkbox_layout = QHBoxLayout()
        self.checkbox_layout.addWidget(self.cbxShowIndex)
        self.checkbox_layout.addWidget(self.cbxShowWireframe)
        self.checkbox_layout.addWidget(self.cbxShowBaseline)
        self.checkbox_layout.addWidget(self.cbxShowAverage)
        self.cbx_widget = QWidget()
        self.cbx_widget.setLayout(self.checkbox_layout)


        self.svsplitter = QSplitter(Qt.Vertical)

        # try adding a 3d plot
        self.lblShape3 = MyGLViewWidget(self)
        z = pg.gaussianFilter(numpy.random.normal(size=(50,50)), (1,1))
        p13d = gl.GLSurfacePlotItem(z=z, shader='shaded', color=(0.5, 0.5, 1, 1))
        self.lblShape3.addItem(p13d)

        if dataset.dimension == 3:
            self.lblShape2.hide()
            self.lblShape = self.lblShape3
        else:
            self.lblShape3.hide()
            self.lblShape = self.lblShape2

        self.svsplitter.addWidget(self.lblShape)

        self.svsplitter.addWidget(self.cbx_widget)
        self.svsplitter.setSizes([800,20])
        self.svsplitter.setStretchFactor(0, 1)
        self.svsplitter.setStretchFactor(1, 0)

        self.plot_layout = QVBoxLayout()
        self.plot_control_layout = QHBoxLayout()
        self.plot_control_layout2 = QHBoxLayout()
        self.plot_control_widget = QWidget()
        self.plot_control_widget2 = QWidget()
        self.plot_control_widget.setMaximumHeight(70)
        self.plot_control_widget.setLayout(self.plot_control_layout)
        self.plot_control_widget2.setMaximumHeight(70)
        self.plot_control_widget2.setLayout(self.plot_control_layout2)

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
        #self.gbAxis1.layout().addWidget(self.lblAxis1)
        self.gbAxis1.layout().addWidget(self.comboAxis1)
        self.gbAxis1.layout().addWidget(self.cbxFlipAxis1)
        self.gbAxis2 = QGroupBox()
        self.gbAxis2.setTitle("Axis 2")
        self.gbAxis2.setLayout(QHBoxLayout())
        #self.gbAxis2.layout().addWidget(self.lblAxis2)
        self.gbAxis2.layout().addWidget(self.comboAxis2)
        self.gbAxis2.layout().addWidget(self.cbxFlipAxis2)
        self.gbAxis3 = QGroupBox()
        self.gbAxis3.setTitle("Axis 3")
        self.gbAxis3.setLayout(QHBoxLayout())
        #self.gbAxis3.layout().addWidget(self.lblAxis3)
        self.gbAxis3.layout().addWidget(self.comboAxis3)
        self.gbAxis3.layout().addWidget(self.cbxFlipAxis3)


        self.plot_control_layout.addWidget(self.gbChartDim)
        self.plot_control_layout.addWidget(self.gbAxis1)
        self.plot_control_layout.addWidget(self.gbAxis2)
        self.plot_control_layout.addWidget(self.gbAxis3)
        # connect checkboxes
        self.cbxFlipAxis1.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis2.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis3.stateChanged.connect(self.flip_axis_changed)

        '''
        self.plot_control_layout.addWidget(self.rb2DChartDim)
        self.plot_control_layout.addWidget(self.rb3DChartDim)
        self.plot_control_layout.addWidget(self.lblAxis1)
        self.plot_control_layout.addWidget(self.comboAxis1)
        self.plot_control_layout.addWidget(self.cbxFlipAxis1)
        self.plot_control_layout.addWidget(self.lblAxis2)
        self.plot_control_layout.addWidget(self.comboAxis2)
        self.plot_control_layout.addWidget(self.cbxFlipAxis2)
        self.plot_control_layout.addWidget(self.lblAxis3)
        self.plot_control_layout.addWidget(self.comboAxis3)
        self.plot_control_layout.addWidget(self.cbxFlipAxis3)
        '''

        self.gbGroupBy = QGroupBox()
        self.gbGroupBy.setTitle("Group By")
        self.gbGroupBy.setLayout(QHBoxLayout())
        self.comboPropertyName = QComboBox()
        self.gbGroupBy.layout().addWidget(self.comboPropertyName)

        self.plot_control_layout2.addWidget(self.gbChartDim)
        self.plot_control_layout2.addWidget(self.gbGroupBy)

        #self.comboPropertyName..connect(self.propertyname_changed)
        #connect comboPropertyname change to plot
        self.comboPropertyName.setCurrentIndex(-1)
        self.comboPropertyName.currentIndexChanged.connect(self.propertyname_changed)
        self.btnChartOptions = QPushButton("Chart Options")
        self.btnChartOptions.clicked.connect(self.chart_options_clicked)

        self.plot_layout.addWidget(self.toolbar2)
        self.plot_layout.addWidget(self.plot_widget2)
        self.plot_layout.addWidget(self.toolbar3)
        self.plot_layout.addWidget(self.plot_widget3)
        self.plot_layout.addWidget(self.plot_control_widget)
        self.plot_layout.addWidget(self.plot_control_widget2)
        self.plot_layout.addWidget(self.btnChartOptions)

        #self.comboDim.addItem("2D")
        #self.comboDim.addItem("3D")
        #self.comboDim.currentIndexChanged.connect(self.on_comboDim_changed)


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
        
        # add event to comboaxic
        self.comboAxis1.currentIndexChanged.connect(self.axis_changed)
        self.comboAxis2.currentIndexChanged.connect(self.axis_changed)
        self.comboAxis3.currentIndexChanged.connect(self.axis_changed)

        self.hsplitter.addWidget(self.svsplitter)
        self.hsplitter.addWidget(self.tableView)
        self.hsplitter.addWidget(self.plot_all_widget)

        self.main_layout = QVBoxLayout()
        self.sub_layout = QHBoxLayout()

        #self.hsplitter.addWidget(self.right_widget)
        self.hsplitter.setSizes([400,200,400])
        self.hsplitter.setStretchFactor(0, 1)
        self.hsplitter.setStretchFactor(1, 0)
        self.hsplitter.setStretchFactor(2, 1)

        self.left_bottom_layout = QVBoxLayout()
        self.middle_bottom_layout = QVBoxLayout()
        self.right_bottom_layout = QVBoxLayout()

        rbbox_height = 50

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
        #self.gbSuperimposition.layout().setContentsMargins(0, 0, 0, 0)
        #self.gbSuperimposition.layout().addWidget(self.btnSuperimpose)
        '''
        self.lb1_layout = QVBoxLayout()
        self.lb1_layout.addWidget(self.rbProcrustes)
        self.lb1_layout.addWidget(self.rbBookstein)
        self.lb1_layout.addWidget(self.rbResistantFit)
        self.lb1_widget = QWidget()
        self.lb1_widget.setMinimumHeight(rbbox_height)
        self.lb1_widget.setMaximumHeight(rbbox_height)
        self.lb1_widget.setLayout(self.lb1_layout)'''
        #self.lb1_layout.setMinimumHeight(60)
        self.left_bottom_layout.addWidget(self.gbSuperimposition)
        self.left_bottom_layout.addWidget(self.btnSuperimpose)

        self.rbPCA = QRadioButton("PCA")
        self.rbCVA = QRadioButton("CVA")
        self.rbPCA.setChecked(True)
        self.rbCVA.setEnabled(False)
        self.gbAnalysis = QGroupBox()
        self.gbAnalysis.setTitle("Method")
        self.gbAnalysis.setLayout(QHBoxLayout())
        #self.gbAnalysis.layout().setContentsMargins(0, 0, 0, 0)
        self.gbAnalysis.layout().addWidget(self.rbPCA)
        self.gbAnalysis.layout().addWidget(self.rbCVA)
        self.gbAnalysis.setMaximumHeight(rbbox_height)


        '''
        #self.mb1_layout = QVBoxLayout()
        #self.mb1_layout.addWidget(self.rbPCA)
        #self.mb1_layout.addWidget(self.rbCVA)
        self.mb1_widget = QWidget()
        self.mb1_widget.setMinimumHeight(rbbox_height)
        self.mb1_widget.setMaximumHeight(rbbox_height)
        self.mb1_widget.setLayout(self.mb1_layout)
        '''
        
        #self.mb1_layout.setMinimumHeight(60)
        self.btnAnalyze = QPushButton("Perform Analysis")
        self.btnAnalyze.clicked.connect(self.on_btnAnalyze_clicked)
        self.middle_bottom_layout.addWidget(self.gbAnalysis)
        self.middle_bottom_layout.addWidget(self.btnAnalyze)

        self.empty_widget = QWidget()
        #self.empty_widget.setMinimumHeight(60)
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
        #self.rb1_layout.addWidget(self.btnSaveResults)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addLayout(self.left_bottom_layout)
        self.bottom_layout.addLayout(self.middle_bottom_layout)
        self.bottom_layout.addLayout(self.right_bottom_layout)

        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        #print("c")
        self.set_dataset(dataset)

        #print("d")
        self.reset_tableView()
        self.load_object()
        self.pca_result = None
        self.selected_object_list = []
        self.selected_object_id_list = []

        self.status_bar = QStatusBar()
        self.status_bar.setMaximumHeight(20)
        #self.setStatusBar(self.status_bar)
        self.main_layout.addWidget(self.hsplitter)
        self.main_layout.addLayout(self.bottom_layout)
        self.main_layout.addWidget(self.status_bar)
        self.setLayout(self.main_layout)

        self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        self.cbxShowAverage.stateChanged.connect(self.show_average_state_changed)

        self.show_chart_options = True
        self.chart_options_clicked()

        #self.comboDim.setCurrentIndex(1)
        self.rb3DChartDim.setChecked(True)
        self.on_chart_dim_changed()
        self.on_btnPCA_clicked()
        self.btnSaveResults.setFocus()

    def chart_options_clicked(self):
        self.show_chart_options = not self.show_chart_options
        if self.show_chart_options:
            #self.gbChartOptions.show()
            self.plot_control_widget.show()
            self.plot_control_widget2.show()
        else:
            #self.gbChartOptions.hide()
            self.plot_control_widget.hide()
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
        self.dataset = dataset
        self.comboPropertyName.clear()
        self.comboPropertyName.addItem("Select Property")
        if len(self.dataset.propertyname_list) > 0:
            for propertyname in self.dataset.propertyname_list:
                self.comboPropertyName.addItem(propertyname)
                #self.comboAxis2.addItem(propertyname)
        self.comboPropertyName.setCurrentIndex(0)
        self.comboPropertyName.currentIndexChanged.connect(self.propertyname_changed)

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
        print("on_btnSaveResults_clicked")
        
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
        group_hash = {}

        key_list = []
        key_list.append('__default__')
        group_hash['__default__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':'blue', 'size':50}
        if len(self.selected_object_id_list) > 0:
            group_hash['__selected__'] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'hoverinfo':[], 'text':[], 'property':'', 'symbol':'o', 'color':'red', 'size':100}
            key_list.append('__selected__')

        for obj in self.ds_ops.object_list:
            key_name = '__default__'

            if obj.id in self.selected_object_id_list:
                key_name = '__selected__'
            elif self.propertyname_index > -1 and self.propertyname_index < len(obj.property_list):
                key_name = obj.property_list[self.propertyname_index]

            if key_name not in group_hash.keys():
                group_hash[key_name] = { 'x_val':[], 'y_val':[], 'z_val':[], 'data':[], 'property':key_name, 'symbol':'', 'color':'', 'size':50}

            group_hash[key_name]['x_val'].append(flip_axis1 * obj.pca_result[axis1])
            group_hash[key_name]['y_val'].append(flip_axis2 * obj.pca_result[axis2])
            group_hash[key_name]['z_val'].append(flip_axis3 * obj.pca_result[axis3])
            #group_hash[key_name]['data'].append(obj)
            #group_hash[key_name]['text'].append(obj.object_name)
            #group_hash[key_name]['hoverinfo'].append(obj.id)

        # remove empty group
        if len(group_hash['__default__']['x_val']) == 0:
            del group_hash['__default__']

        # assign color and symbol
        sc_idx = 0
        for key_name in group_hash.keys():
            if group_hash[key_name]['color'] == '':
                group_hash[key_name]['color'] = color_candidate[sc_idx % len(color_candidate)]
                group_hash[key_name]['symbol'] = symbol_candidate[sc_idx % len(symbol_candidate)]
                sc_idx += 1

        if self.rb2DChartDim.isChecked():
            self.ax2.clear()
            for name in group_hash.keys():
                #print("name", name, "len(group_hash[name]['x_val'])", len(group_hash[name]['x_val']), group_hash[name]['symbol'])
                group = group_hash[name]
                if len(group['x_val']) > 0:
                    ret = self.ax2.scatter(group['x_val'], group['y_val'], s=group['size'], marker=group['symbol'], color=group['color'], data=group['data'], picker=True, pickradius=5)
                    print("ret", ret)
            self.fig2.tight_layout()
            self.fig2.canvas.draw()
            self.fig2.canvas.flush_events()
            self.fig2.canvas.mpl_connect('pick_event',self.onpick)

        else:
            self.ax3.clear()
            for name in group_hash.keys():
                #print("name", name, "len(group_hash[name]['x_val'])", len(group_hash[name]['x_val']), group_hash[name]['symbol'])
                group = group_hash[name]
                if len(group_hash[name]['x_val']) > 0:
                    ret = self.ax3.scatter(group['x_val'], group['y_val'], group['z_val'], s=group['size'], marker=group['symbol'], color=group['color'], data=group['data'],depthshade=depth_shade)
                    print("ret", ret)
            self.fig3.tight_layout()
            self.fig3.canvas.draw()
            self.fig3.canvas.flush_events()

    def onpick(self,evt):
        print("evt", evt, evt.ind, evt.artist )

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
        for obj in self.dataset.object_list:
            item1 = QStandardItem()
            item1.setData(obj.id,Qt.DisplayRole)
            item2 = QStandardItem(obj.object_name)
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
        self.import_thread = ImportThread(self)
        self.import_thread.start()
        self.import_thread.finished.connect(self.import_finished)
        self.import_thread.progress.connect(self.import_progress)

    def import_finished(self):
        self.btnImport.setEnabled(True)
        self.prgImport.setValue(100)
        self.prgImport.setFormat("Import Finished")
        self.prgImport.update()
        self.prgImport.repaint()
        self.import_thread.quit()
        self.import_thread.wait()

    def import_progress(self, value):
        self.prgImport.setValue(value)
        self.prgImport.update()
        self.prgImport.repaint()

class ImportThread(QThread):

    progress = pyqtSignal(int)
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def run(self):
        filename = self.parent.edtFilename.text()
        #filetype = self.parent.cbxFileType.currentText()
        filetype = self.parent.chkFileType.checkedButton().text()
        datasetname = self.parent.edtDatasetName.text()
        objectcount = self.parent.edtObjectCount.text()
        if filetype == "TPS":
            self.import_tps(filename, datasetname)
        elif filetype == "X1Y1":
            self.import_x1y1(filename, datasetname)
        elif filetype == "Morphologika":
            self.import_morphologika(filename, datasetname)
        else:
            self.progress.emit(0)
            return
        self.progress.emit(100)

    def import_tps(self, filename, datasetname):
        # read tps file
        tps = TPS(filename, datasetname)
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
            self.progress.emit(int( (i / float(tps.nobjects)) * 100))
            #progress = int( (i / float(tps.nobjects)) * 100)

        # add dataset to project
        #self.parent.parent.project.datasets.append(dataset)
        #self.parent.parent.project.current_dataset = dataset

    def import_x1y1(self, filename, datasetname):
        # read x1y1 file
        x1y1 = X1Y1(filename)
        # create dataset
        dataset = MdDataset()
        dataset.dataset_name = datasetname
        dataset.dimension = x1y1.dimension
        dataset.save()
        for i in range(x1y1.nobjects):
            object = MdObject()
            object.object_name = x1y1.object_name_list[i]
            #print("object:", object.object_name)
            object.dataset = dataset
            object.landmark_str = ""
            landmark_list = []
            for landmark in x1y1.landmark_data[x1y1.object_name_list[i]]:
                landmark_list.append("\t".join([ str(x) for x in landmark]))
            object.landmark_str = "\n".join(landmark_list)

            object.save()
            self.progress.emit(int( (i / float(x1y1.nobjects)) * 100))

class X1Y1:
    def __init__(self, filename):
        self.filename = filename
        self.nobjects = 0
        self.nlandmarks = 0
        self.objectnames = []
        self.landmarks = []
        self.read()

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
                            key = self.datasetname + "_" + str(object_count + 1)
                        objects[key] = data
                        object_name_list.append(key)
                        data = []
                    header = 'lm'
                    object_count += 1
                    landmark_count, comment = int(headerline.group(4)), headerline.group(5).strip()
                    print("landmark_count:", landmark_count)
                    # landmark_count_list.append( landmark_count )
                    # if not found:
                    #found = True
                elif headerline.group(1).lower() == "image":
                    image_count += 1

            if len(data) > 0:
                if comment != '':
                    key = comment
                else:
                    key = self.datasetname + "_" + str(object_count + 1)
                objects[key] = data
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