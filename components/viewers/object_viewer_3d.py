"""
ObjectViewer3D - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

import OpenGL.GL as gl
from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from OpenGL import GLU as glu
from PyQt5.QtCore import (
    Qt,
    QTimer,
)
from PyQt5.QtGui import (
    QColor,
)
from PyQt5.QtWidgets import (
    QApplication,
)

from MdModel import MdDataset, MdDatasetOps, MdObject, MdObjectOps
from OBJFileLoader import OBJ

# GLUT import conditional - causes crashes on Windows builds
GLUT_AVAILABLE = False
GLUT_INITIALIZED = False
glut = None

try:
    from OpenGL import GLUT as glut

    GLUT_AVAILABLE = True
except ImportError as e:
    GLUT_AVAILABLE = False
    print(f"Warning: GLUT not available ({e}), using fallback rendering")
    glut = None

# Initialize GLUT once at module level if available
if GLUT_AVAILABLE and glut:
    try:
        glut.glutInit(sys.argv)
        GLUT_INITIALIZED = True
    except Exception as e:
        print(f"Warning: Failed to initialize GLUT ({e}), using fallback rendering")
        GLUT_AVAILABLE = False
        GLUT_INITIALIZED = False
import copy
import math
import random
import struct
from pathlib import Path

import numpy as np
from PyQt5.QtOpenGL import QGLFormat, QGLWidget

import MdUtils as mu

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
MODE_GROWTH_TRAJECTORY = 2
MODE_AVERAGE = 3
MODE_COMPARISON = 4
MODE_COMPARISON2 = 5
# MODE_GRID = 6

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


class ObjectViewer3D(QGLWidget):
    def __init__(self, parent=None, transparent=False):
        if transparent:
            fmt = QGLFormat()
            fmt.setAlpha(True)  # Ensure the format includes an alpha channel
            super().__init__(fmt, parent)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowTransparentForInput | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_NoSystemBackground, True)
        else:
            QGLWidget.__init__(self, parent)
        self.transparent = transparent
        self.parent = parent
        self.setMinimumSize(120, 90)
        self.landmark_size = 1
        self.landmark_color = "#0000FF"
        self.wireframe_thickness = 1
        self.wireframe_color = "#FFFF00"
        self.index_size = 1
        self.index_color = "#FFFFFF"
        self.bgcolor = "#AAAAAA"
        self.arrow_color = "#FFFF00"
        self.m_app = QApplication.instance()
        self.read_settings()
        self.object_name = ""
        self.source_preference = None
        self.target_preference = None

        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.object_dialog = None
        self.ds_ops = None
        self.ds_ops_comp = None
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
        self.show_index = False
        self.show_wireframe = True
        self.show_polygon = True
        self.show_baseline = False
        self.show_average = True
        self.show_model = True
        self.show_arrow = False

        self.curr_x = 0
        self.curr_y = 0
        self.down_x = 0
        self.down_y = 0
        self.temp_dolly = 0
        self.dolly = 0
        self.data_mode = OBJECT_MODE
        self.view_mode = VIEW_MODE
        self.edit_mode = MODE["NONE"]
        self.auto_rotate = False
        self.is_dragging = False
        # self.setMinimumSize(400,400)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.timeout)
        self.timer.start()
        self.frustum_args = {"width": 1.0, "height": 1.0, "znear": 0.1, "zfar": 1000.0}
        self.color_to_lm_idx = {}
        self.lm_idx_to_color = {}
        self.picker_buffer = None
        self.gl_list = None
        self.temp_edge = []
        self.object = None
        self.polygon_list = []
        self.comparison_data = {}

        # self.no_drawing = False
        self.wireframe_from_idx = -1
        self.wireframe_to_idx = -1
        self.selected_landmark_idx = -1
        self.selected_edge_index = -1
        self.no_hit_count = 0
        self.threed_model = None
        self.cursor_on_vertex = -1
        self.rotation_matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        self.initialized = False
        self.fullpath = None
        self.edge_list = []
        self.landmark_list = []

    def set_object_name(self, object_name):
        self.object_name = object_name

    def set_landmark_pref(self, lm_pref, wf_pref):
        self.landmark_size = lm_pref["size"]
        self.landmark_color = lm_pref["color"]
        self.wireframe_thickness = wf_pref["thickness"]
        self.wireframe_color = wf_pref["color"]

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
        if self.edit_mode == MODE["EDIT_LANDMARK"]:
            # print("edit landmark")
            self.initialize_colors()
            self.setCursor(Qt.CrossCursor)
            self.show_message("Click on image to add landmark")
        elif self.edit_mode == MODE["READY_MOVE_LANDMARK"]:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Click on landmark to move")
        elif self.edit_mode == MODE["MOVE_LANDMARK"]:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message("Move landmark")
        elif self.edit_mode == MODE["WIREFRAME"]:
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
            if self.edit_mode == MODE["WIREFRAME"] and self.selected_landmark_idx > -1:
                self.wireframe_from_idx = self.selected_landmark_idx
                self.temp_edge = [
                    self.obj_ops.landmark_list[self.wireframe_from_idx][:],
                    self.obj_ops.landmark_list[self.wireframe_from_idx][:],
                ]
            elif self.edit_mode == MODE["EDIT_LANDMARK"] and self.selected_landmark_idx > -1:
                self.set_mode(MODE["MOVE_LANDMARK"])
                self.stored_landmark = {
                    "index": self.selected_landmark_idx,
                    "coords": self.threed_model.original_vertices[self.selected_landmark_idx],
                }
            else:
                self.view_mode = ROTATE_MODE
        elif event.buttons() == Qt.RightButton:
            if self.edit_mode == MODE["WIREFRAME"] and self.selected_edge_index > -1:
                self.delete_wire(self.selected_edge_index)
            elif self.edit_mode == MODE["EDIT_LANDMARK"] and self.cursor_on_vertex > -1:
                pass
            else:
                self.view_mode = ZOOM_MODE
        elif event.buttons() == Qt.MiddleButton:
            self.view_mode = PAN_MODE

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.curr_x = event.x()
        self.curr_y = event.y()
        if event.button() == Qt.LeftButton:
            if self.edit_mode == MODE["WIREFRAME"] and self.wireframe_from_idx > -1:
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

            elif (
                self.edit_mode == MODE["EDIT_LANDMARK"]
                and self.cursor_on_vertex > -1
                and self.curr_x == self.down_x
                and self.curr_y == self.down_y
            ):
                x, y, z = self.threed_model.original_vertices[self.cursor_on_vertex]
                self.object_dialog.add_landmark(x, y, z)
                self.update_landmark_list()
                self.initialize_colors()
                self.calculate_resize()
            elif (
                self.edit_mode == MODE["MOVE_LANDMARK"]
                and self.selected_landmark_idx > -1
                and self.cursor_on_vertex > -1
            ):
                self.update_landmark_list()
                self.initialize_colors()
                self.calculate_resize()
                self.selected_landmark_idx = -1
                self.cursor_on_vertex = -1
                self.set_mode(MODE["EDIT_LANDMARK"])
            else:
                if self.data_mode == OBJECT_MODE and self.obj_ops is not None:
                    if self.parent is not None and callable(getattr(self.parent, "sync_rotation", None)):
                        self.parent.sync_rotation()
                    else:
                        self.sync_rotation()
                elif self.data_mode == DATASET_MODE and self.ds_ops is not None:
                    if self.parent is not None and callable(getattr(self.parent, "sync_rotation", None)):
                        # if self.parent != None and self.parent.sync_rotation is not None:
                        self.parent.sync_rotation()
                    else:
                        self.sync_rotation()
                self.temp_rotate_x = 0
                self.temp_rotate_y = 0
        elif event.button() == Qt.RightButton:
            if (
                self.edit_mode == MODE["EDIT_LANDMARK"]
                and self.selected_landmark_idx > -1
                and self.curr_x == self.down_x
                and self.curr_y == self.down_y
            ):
                self.object_dialog.delete_landmark(self.selected_landmark_idx)
                self.update_landmark_list()
                self.initialize_colors()
                self.calculate_resize()
            else:
                self.dolly += self.temp_dolly
                self.temp_dolly = 0
                if self.parent is not None and callable(getattr(self.parent, "sync_zoom", None)):
                    self.parent.sync_zoom(self, self.dolly)
                if self.parent is not None and callable(getattr(self.parent, "sync_temp_zoom", None)):
                    self.parent.sync_temp_zoom(self, self.temp_dolly)

        elif event.button() == Qt.MiddleButton:
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
            if self.parent is not None and callable(getattr(self.parent, "sync_temp_pan", None)):
                self.parent.sync_temp_pan(self, self.temp_pan_x, self.temp_pan_y)
            if self.parent is not None and callable(getattr(self.parent, "sync_pan", None)):
                self.parent.sync_pan(self, self.pan_x, self.pan_y)

        self.view_mode = VIEW_MODE
        self.updateGL()

    def mouseMoveEvent(self, event):
        self.curr_x = event.x()
        self.curr_y = event.y()
        if self.edit_mode == MODE["WIREFRAME"]:
            kind, idx = self.hit_test(self.curr_x, self.curr_y)
            if kind == "Landmark":
                lm_idx = idx

                if lm_idx > -1:
                    self.selected_landmark_idx = lm_idx
                    self.no_hit_count = 0
                elif self.selected_landmark_idx > -1:
                    self.no_hit_count += 1
                    if self.no_hit_count > 5:
                        self.selected_landmark_idx = -1
                        self.no_hit_count = 0
            elif kind == "Edge":
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
            if self.parent is not None and callable(getattr(self.parent, "sync_temp_rotation", None)):
                self.parent.sync_temp_rotation(self, self.temp_rotate_x, self.temp_rotate_y)

        elif event.buttons() == Qt.RightButton and self.view_mode == ZOOM_MODE:
            self.is_dragging = True
            self.temp_dolly = (self.curr_y - self.down_y) / 100.0
            if self.parent is not None and callable(getattr(self.parent, "sync_temp_zoom", None)):
                self.parent.sync_temp_zoom(self, self.temp_dolly)

        elif event.buttons() == Qt.MiddleButton and self.view_mode == PAN_MODE:
            self.is_dragging = True
            self.temp_pan_x = self.curr_x - self.down_x
            self.temp_pan_y = self.curr_y - self.down_y
            if self.parent is not None and callable(getattr(self.parent, "sync_temp_pan", None)):
                self.parent.sync_temp_pan(self, self.temp_pan_x, self.temp_pan_y)
        elif self.edit_mode == MODE["EDIT_LANDMARK"]:
            hit_type, hit_idx = self.hit_test(self.curr_x, self.curr_y)
            if hit_type == "Landmark":
                self.selected_landmark_idx = hit_idx
                self.no_hit_count = 0
            else:
                self.selected_landmark_idx = -1

            if self.show_model:
                on_background = self.hit_background_test(self.curr_x, self.curr_y)
                if on_background:
                    self.cursor_on_vertex = -1
                else:
                    closest_element = self.pick_element(self.curr_x, self.curr_y)
                    if closest_element is not None:
                        self.cursor_on_vertex = closest_element
                    else:
                        self.cursor_on_vertex = -1
        elif self.edit_mode == MODE["MOVE_LANDMARK"]:
            if self.show_model:
                on_background = self.hit_background_test(self.curr_x, self.curr_y)
                if on_background:
                    self.cursor_on_vertex = -1
                    self.landmark_list[self.selected_landmark_idx] = self.stored_landmark["coords"]
                    self.selected_landmark_idx = -1
                    self.set_mode(MODE["EDIT_LANDMARK"])
                else:
                    closest_element = self.pick_element(self.curr_x, self.curr_y)
                    if closest_element is not None:
                        self.cursor_on_vertex = closest_element
                        if self.selected_landmark_idx >= 0:
                            self.landmark_list[self.selected_landmark_idx] = self.threed_model.original_vertices[
                                closest_element
                            ]
                            if self.object_dialog is not None:
                                self.object_dialog.update_landmark(
                                    self.selected_landmark_idx, *self.landmark_list[self.selected_landmark_idx]
                                )
                                self.update_landmark_list()
                                self.initialize_colors()
                                self.calculate_resize()
                    else:
                        self.cursor_on_vertex = -1

        self.updateGL()

    def wheelEvent(self, event):
        self.dolly -= event.angleDelta().y() / 240.0
        if self.parent is not None and callable(getattr(self.parent, "sync_zoom", None)):
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
        dataset.edge_list.append([wire_start_index + 1, wire_end_index + 1])
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
        if self.obj_ops is not None:
            obj = self.obj_ops
            if "visible" in object_preference:
                obj.visible = object_preference["visible"]
            if "show_landmark" in object_preference:
                obj.show_landmark = object_preference["show_landmark"]
            if "show_wireframe" in object_preference:
                obj.show_wireframe = object_preference["show_wireframe"]
            if "show_polygon" in object_preference:
                obj.show_polygon = object_preference["show_polygon"]
            if "opacity" in object_preference:
                obj.opacity = object_preference["opacity"]
            if "polygon_color" in object_preference:
                obj.polygon_color = object_preference["polygon_color"]
            if "edge_color" in object_preference:
                obj.edge_color = object_preference["edge_color"]
            if "landmark_color" in object_preference:
                obj.landmark_color = object_preference["landmark_color"]

    def set_source_shape_preference(self, pref):
        self.source_preference = pref
        if self.ds_ops is not None and len(self.ds_ops.object_list) > 0:
            obj = self.ds_ops.object_list[0]
            obj.visible = pref["visible"]
            obj.show_landmark = pref["show_landmark"]
            obj.show_wireframe = pref["show_wireframe"]
            obj.show_polygon = pref["show_polygon"]
            obj.opacity = pref["opacity"]
            obj.polygon_color = pref["polygon_color"]
            obj.edge_color = pref["edge_color"]
            obj.landmark_color = pref["landmark_color"]

    def set_target_shape_preference(self, pref):
        self.target_preference = pref
        if self.ds_ops is not None and len(self.ds_ops.object_list) > 1:
            obj = self.ds_ops.object_list[1]
            obj.visible = pref["visible"]
            obj.show_landmark = pref["show_landmark"]
            obj.show_wireframe = pref["show_wireframe"]
            obj.show_polygon = pref["show_polygon"]
            obj.opacity = pref["opacity"]
            obj.polygon_color = pref["polygon_color"]
            obj.edge_color = pref["edge_color"]
            obj.landmark_color = pref["landmark_color"]

    def set_source_shape_color(self, color):
        self.source_shape_color = color

    def set_target_shape_color(self, color):
        self.target_shape_color = color

    def set_source_shape(self, object):
        self.comparison_data["source_shape"] = object

    def set_target_shape(self, object):
        self.comparison_data["target_shape"] = object

    def set_intermediate_shape(self, object):
        self.comparison_data["intermediate_shape"] = object

    def generate_reference_shape(self):
        shape_list = []
        ds = MdDataset()
        ds.dimension = self.dataset.dimension
        ds.baseline = self.dataset.baseline
        ds.wireframe = self.dataset.wireframe
        ds.edge_list = self.dataset.edge_list
        ds.polygon_list = self.dataset.polygon_list
        ds_ops = MdDatasetOps(ds)

        if "source_shape" in self.comparison_data:
            shape_list.append(self.comparison_data["source_shape"])
            source = self.comparison_data["source_shape"]
            source_ops = MdObjectOps(source)
            ds_ops.object_list.append(source_ops)
        if "target_shape" in self.comparison_data:
            shape_list.append(self.comparison_data["target_shape"])
            target = self.comparison_data["target_shape"]
            target_ops = MdObjectOps(target)
            ds_ops.object_list.append(target_ops)

        ret = ds_ops.procrustes_superimposition()
        if not ret:
            logger = logging.getLogger(__name__)
            logger.error("procrustes failed")
            return
        self.comparison_data["ds_ops"] = ds_ops
        self.comparison_data["average_shape"] = ds_ops.get_average_shape()
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
        obj_ops.get_centroid_size()
        min_x, max_x = min([lm[0] for lm in obj_ops.landmark_list]), max([lm[0] for lm in obj_ops.landmark_list])
        min_y, max_y = min([lm[1] for lm in obj_ops.landmark_list]), max([lm[1] for lm in obj_ops.landmark_list])
        width = max_x - min_x
        if width == 0:
            width = 1
        height = max_y - min_y
        if height == 0:
            height = 1

        if len(obj_ops.landmark_list[0]) > 2:
            min_z, max_z = min([lm[2] for lm in obj_ops.landmark_list]), max([lm[2] for lm in obj_ops.landmark_list])
            # obj_ops.rescale(5)
            max_z - min_z
        _3D_SCREEN_WIDTH = 5
        _3D_SCREEN_HEIGHT = 5
        scale = min(_3D_SCREEN_WIDTH / width, _3D_SCREEN_HEIGHT / height)
        # print("scale:", scale)
        return scale * 0.5

    def dragEnterEvent(self, event):
        if self.object_dialog is None:
            return
        file_name = event.mimeData().text()
        if file_name.split(".")[-1].lower() in mu.MODEL_EXTENSION_LIST:
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
        if file_path.split(".")[-1].lower() == "obj":
            self.threed_model = OBJ(file_path)
            self.fullpath = file_path
        self.updateGL()

    def initializeGL(self):
        self.initialize_frame_buffer()
        self.picker_buffer = self.create_picker_buffer()
        self.initialize_frame_buffer(self.picker_buffer)
        self.initialized = True
        if self.initialized and self.threed_model is not None and not self.threed_model.generated:
            self.threed_model.generate()

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
        glu.gluPerspective(45.0, aspect_ratio, 0.1, 100.0)  # 시야각, 종횡비, 근거리 클리핑, 원거리 클리핑
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def paintGL(self):
        if self.edit_mode == MODE["WIREFRAME"] or self.edit_mode == MODE["EDIT_LANDMARK"]:
            self.draw_picker_buffer()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        gl.glPushMatrix()
        self.draw_all()
        gl.glPopMatrix()
        return

    def draw_all(self):
        gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45.0, self.aspect, 0.1, 100.0)
        light_position = [1.0, 1.0, 1.0, 0.0]  # x, y, z, w (w=0 for directional light)
        diffuse_intensity = (1.0, 1.0, 1.0, 1.0)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, light_position)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, diffuse_intensity)
        gl.glTranslatef(0, 0, -5.0 + self.dolly + self.temp_dolly)  # x, y, z
        gl.glTranslatef((self.pan_x + self.temp_pan_x) / 100.0, (self.pan_y + self.temp_pan_y) / -100.0, 0.0)
        gl.glRotatef(self.rotate_y + self.temp_rotate_y, 1.0, 0.0, 0.0)
        gl.glRotatef(self.rotate_x + self.temp_rotate_x, 0.0, 1.0, 0.0)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        bg_color = mu.as_gl_color(self.bgcolor)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)  # Standard alpha blending
        if self.transparent:
            gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        else:
            gl.glClearColor(*bg_color, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        gl.glEnable(gl.GL_POINT_SMOOTH)
        if self.ds_ops is None and self.obj_ops is None:
            return

        # pan, rotate, dolly
        if self.data_mode == OBJECT_MODE:
            if self.obj_ops and hasattr(self.obj_ops, "landmark_color") and self.obj_ops.landmark_color is not None:
                object_color = mu.as_gl_color(self.obj_ops.landmark_color)
            else:
                object_color = mu.as_gl_color(self.landmark_color)  # COLOR['NORMAL_SHAPE']
            self.draw_object(self.obj_ops, color=object_color)
        else:
            self.draw_dataset(self.ds_ops)
        gl.glDisable(gl.GL_BLEND)
        gl.glFlush()

    def draw_dataset(self, ds_ops):
        if self.show_arrow:
            self.draw_arrow(0, 1)

        for _idx, obj in enumerate(ds_ops.object_list):
            if not obj.visible:
                continue
            if obj.id in ds_ops.selected_object_id_list:
                object_color = COLOR["SELECTED_SHAPE"]
            else:
                if obj.landmark_color is not None:
                    object_color = mu.as_gl_color(obj.landmark_color)
                else:
                    object_color = mu.as_gl_color(self.landmark_color)  # COLOR['NORMAL_SHAPE']
            edge_color = self.wireframe_color
            if obj.edge_color is not None:
                edge_color = obj.edge_color
            polygon_color = self.wireframe_color
            if obj.polygon_color is not None:
                polygon_color = obj.polygon_color

            self.draw_object(
                obj, landmark_as_sphere=False, color=object_color, edge_color=edge_color, polygon_color=polygon_color
            )

        if self.show_average:
            object_color = COLOR["AVERAGE_SHAPE"]
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
            direction = [x / length for x in direction]

            # Rotation axis using cross product
            up_direction = [0, 0, 1]  # Cone should point upwards along Z
            axis = np.cross(direction, up_direction)

            # Calculate angle
            angle = math.degrees(math.acos(np.dot(direction, up_direction))) * -1

            # draw rod instead of GL_LINES
            arrow_color = mu.as_gl_color(self.arrow_color)
            gl.glColor3f(*arrow_color)
            gl.glPushMatrix()
            gl.glTranslatef(*((np.array(start_lm) + np.array(end_lm)) / 2))
            gl.glTranslatef(*[x * -0.015 for x in direction])
            gl.glRotatef(angle, *axis)
            gl.glScalef(0.005, 0.005, length - 0.03)
            if GLUT_AVAILABLE and GLUT_INITIALIZED and glut:
                try:
                    glut.glutSolidCube(1)
                except (OSError, AttributeError):
                    # Fallback to drawing a cube manually
                    pass
            else:
                # Fallback: draw wireframe cube
                self.draw_wireframe_cube()
            gl.glPopMatrix()

            if True:
                gl.glPushMatrix()
                gl.glTranslatef(*end_lm)
                gl.glTranslatef(*[x * -0.03 for x in direction])
                gl.glRotatef(angle, *axis)
                if GLUT_AVAILABLE and GLUT_INITIALIZED and glut:
                    try:
                        glut.glutSolidCone(0.02, 0.03, 10, 10)
                    except (OSError, AttributeError):
                        # Fallback if GLUT call fails
                        pass
                else:
                    # Fallback: draw simple cone
                    self.draw_simple_cone()
                gl.glPopMatrix()

    def draw_object(
        self,
        object,
        landmark_as_sphere=True,
        color=COLOR["NORMAL_SHAPE"],
        edge_color=COLOR["NORMAL_SHAPE"],
        polygon_color=COLOR["NORMAL_SHAPE"],
    ):
        if object is None:
            return
        current_buffer = gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)

        if self.show_wireframe and len(self.temp_edge) == 2 and object.show_wireframe:
            if object.edge_color:
                wf_color = mu.as_gl_color(object.edge_color)
            else:
                wf_color = mu.as_gl_color(self.wireframe_color)
            gl.glColor3f(*wf_color)  # *COLOR['WIREFRAME'])
            gl.glLineWidth(int(self.wireframe_thickness) + 1)
            gl.glBegin(gl.GL_LINE_STRIP)
            for v in self.temp_edge:
                gl.glVertex3f(*v)
            gl.glEnd()

        if self.show_wireframe and len(self.edge_list) > 0 and object.show_wireframe:
            for i, edge in enumerate(self.edge_list):
                if current_buffer == self.picker_buffer and self.object_dialog is not None:
                    gl.glDisable(gl.GL_LIGHTING)
                    key = "edge_" + str(i)
                    color = self.edge_idx_to_color[key]
                    gl.glColor3f(*[c * 1.0 / 255 for c in color])
                    line_width = 3 * (int(self.wireframe_thickness) + 1)
                    gl.glLineWidth(line_width)
                else:
                    if i == self.selected_edge_index:
                        gl.glColor3f(*COLOR["SELECTED_EDGE"])
                    else:
                        if object.edge_color:
                            wf_color = mu.as_gl_color(object.edge_color)
                        else:
                            wf_color = mu.as_gl_color(self.wireframe_color)
                        gl.glColor3f(*wf_color)
                    line_width = 1 * (int(self.wireframe_thickness) + 1)
                    gl.glLineWidth(line_width)
                gl.glBegin(gl.GL_LINE_STRIP)
                valid_edge = True
                for lm_idx in edge:
                    if lm_idx <= len(object.landmark_list):
                        lm = object.landmark_list[lm_idx - 1]
                        # Check if landmark is missing
                        if len(lm) < 3 or lm[0] is None or lm[1] is None or lm[2] is None:
                            valid_edge = False
                            break
                # Only draw edge if all landmarks are valid
                if valid_edge:
                    for lm_idx in edge:
                        if lm_idx <= len(object.landmark_list):
                            lm = object.landmark_list[lm_idx - 1]
                            gl.glVertex3f(*lm)
                gl.glEnd()
                if current_buffer == self.picker_buffer and self.object_dialog is not None:
                    gl.glEnable(gl.GL_LIGHTING)

        if self.show_polygon and len(self.polygon_list) > 0 and object.show_polygon:
            self.calculate_normal_list(object, self.polygon_list)
            for i, polygon in enumerate(self.polygon_list):
                normal = self.calculate_normal(object, polygon)
                gl.glEnable(gl.GL_LIGHTING)
                if object.polygon_color:
                    pg_color = mu.as_gl_color(object.polygon_color)
                elif isinstance(polygon_color, QColor):
                    pg_color = mu.as_gl_color(polygon_color)
                elif len(polygon_color) == 3:
                    pg_color = polygon_color
                else:
                    pg_color = mu.as_gl_color(polygon_color)
                gl.glColor4f(*pg_color, object.opacity)
                gl.glNormal3f(*normal)
                gl.glBegin(gl.GL_POLYGON)
                for lm_idx in polygon:
                    if lm_idx <= len(object.landmark_list):
                        lm = object.landmark_list[lm_idx - 1]
                        gl.glVertex3f(*lm)
                gl.glEnd()

        if landmark_as_sphere and object.show_landmark:
            len(object.landmark_list)
            for i, lm in enumerate(object.landmark_list):
                # Skip missing landmarks in 3D view
                if len(lm) < 3 or lm[0] is None or lm[1] is None or lm[2] is None:
                    continue
                gl.glPushMatrix()
                gl.glTranslate(*lm)
                gl.glColor3f(*color)
                if i in [self.selected_landmark_idx, self.wireframe_from_idx, self.wireframe_to_idx]:
                    gl.glColor3f(*COLOR["SELECTED_LANDMARK"])

                if current_buffer == self.picker_buffer and self.object_dialog is not None:
                    gl.glDisable(gl.GL_LIGHTING)
                    key = "lm_" + str(i)
                    color = self.lm_idx_to_color[key]
                    gl.glColor3f(*[c * 1.0 / 255 for c in color])
                if GLUT_AVAILABLE and GLUT_INITIALIZED and glut:
                    try:
                        glut.glutSolidSphere(0.02 * (int(self.landmark_size) + 1), 10, 10)
                    except (OSError, AttributeError):
                        # Fallback if GLUT call fails
                        self.draw_sphere(0.02 * (int(self.landmark_size) + 1))
                else:
                    # Fallback: use GLU sphere or point
                    self.draw_sphere(0.02 * (int(self.landmark_size) + 1))
                if current_buffer == self.picker_buffer and self.object_dialog is not None:
                    gl.glEnable(gl.GL_LIGHTING)
                gl.glPopMatrix()

                if self.show_index:
                    gl.glDisable(gl.GL_LIGHTING)
                    index_color = mu.as_gl_color(self.index_color)
                    gl.glColor3f(*index_color)
                    gl.glRasterPos3f(lm[0] + 0.05, lm[1] + 0.05, lm[2])
                    font_size_list = [
                        glut.GLUT_BITMAP_HELVETICA_10,
                        glut.GLUT_BITMAP_HELVETICA_12,
                        glut.GLUT_BITMAP_HELVETICA_18,
                    ]
                    if GLUT_AVAILABLE and GLUT_INITIALIZED and glut:
                        try:
                            for letter in list(str(i + 1)):
                                glut.glutBitmapCharacter(font_size_list[int(self.index_size)], ord(letter))
                        except (OSError, AttributeError):
                            # Fallback if GLUT text rendering fails
                            pass
                    gl.glEnable(gl.GL_LIGHTING)

        elif object.show_landmark:
            gl.glPointSize(5)
            gl.glDisable(gl.GL_LIGHTING)
            gl.glColor3f(*color)
            gl.glBegin(gl.GL_POINTS)
            # gl.glColor3f( 1.0, 1.0, 0.0 )
            for lm in object.landmark_list:
                # Skip missing landmarks
                if len(lm) < 3 or lm[0] is None or lm[1] is None or lm[2] is None:
                    continue
                gl.glVertex3f(lm[0], lm[1], lm[2])
            gl.glEnd()
            gl.glEnable(gl.GL_LIGHTING)

        if self.threed_model is not None and self.show_model is True:
            self.threed_model.render()

            if self.cursor_on_vertex > -1:
                lm = self.threed_model.vertices[self.cursor_on_vertex]
                gl.glPushMatrix()
                gl.glTranslate(*lm)
                gl.glColor3f(*COLOR["SELECTED_LANDMARK"])
                if GLUT_AVAILABLE and GLUT_INITIALIZED and glut:
                    try:
                        glut.glutSolidSphere(0.03, 10, 10)
                    except (OSError, AttributeError):
                        # Fallback if GLUT call fails
                        self.draw_sphere(0.03)
                else:
                    # Fallback: use GLU sphere or point
                    self.draw_sphere(0.03)
                gl.glPopMatrix()
            return

    def calculate_normal(self, obj_ops, polygon):
        p1 = obj_ops.landmark_list[polygon[0] - 1]
        p2 = obj_ops.landmark_list[polygon[1] - 1]
        p3 = obj_ops.landmark_list[polygon[2] - 1]
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
                length = math.sqrt(
                    face_normal[0] * face_normal[0] + face_normal[1] * face_normal[1] + face_normal[2] * face_normal[2]
                )
                face_normals.append([f / length for f in face_normal])
        return face_normals

    def calculate_normal_list(self, obj_ops, polygon_list):
        normal_dict = {}
        for polygon in polygon_list:
            lm_idx_list = [i - 1 for i in polygon]
            landmark_list = [obj_ops.landmark_list[i] for i in lm_idx_list]
            v1 = np.array(landmark_list[1]) - np.array(landmark_list[0])
            v2 = np.array(landmark_list[2]) - np.array(landmark_list[0])
            normal = -1.0 * np.cross(v1, v2)
            for i in lm_idx_list:
                if i in normal_dict:
                    normal_dict[i]["normal"] += normal
                    normal_dict[i]["count"] += 1
                else:
                    normal_dict[i] = {"normal": normal, "count": 1}
        normal_list = []
        for i in range(len(obj_ops.landmark_list)):
            if i in normal_dict:
                normal = normal_dict[i]["normal"] / normal_dict[i]["count"]
            else:
                normal = np.array([0, 0, 0])
            normal_list.append(normal)
        return normal_list

    def create_picker_buffer(self):
        picker_buffer = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, picker_buffer)

        # Create a texture to hold the color buffer
        self.texture_buffer = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_buffer)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.width(), self.height(), 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None
        )
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
        if not self.auto_rotate:
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
        pixels = gl.glReadPixels(x, self.height() - y, 1, 1, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        r, g, b = struct.unpack("BBB", pixels)
        rgb_list = [r, g, b]
        bg_color = [int(255 * c) for c in COLOR["BACKGROUND"]]
        if bg_color == rgb_list:
            return True
        else:
            return False

    def hit_test(self, x, y):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.picker_buffer)
        pixels = gl.glReadPixels(x, self.height() - y, 1, 1, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        r, g, b = struct.unpack("BBB", pixels)
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
            self.lm_idx_to_color["lm_" + str(i)] = color

        self.color_to_edge_idx = {}
        self.edge_idx_to_color = {}
        for i in range(len(self.edge_list)):
            while True:
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                if color not in self.color_to_lm_idx.keys() and color not in self.color_to_edge_idx.keys():
                    break
            self.color_to_edge_idx[color] = str(i)
            self.edge_idx_to_color["edge_" + str(i)] = color

    def update_landmark_list(self):
        self.obj_ops.landmark_list = copy.deepcopy(self.landmark_list)
        return

    def calculate_resize(self):
        if self.threed_model is not None:
            if self.initialized and not self.threed_model.generated:
                self.threed_model.generate()
            self.obj_ops.move(
                -1 * self.threed_model.center_x, -1 * self.threed_model.center_y, -1 * self.threed_model.center_z
            )
            self.obj_ops.rescale(self.threed_model.scale)
            self.obj_ops.apply_rotation_matrix(self.threed_model.rotation_matrix)
        else:
            self.obj_ops.landmark_list = copy.deepcopy(self.landmark_list)
            self.obj_ops.move_to_center()
            self.obj_ops.get_centroid_size()
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
        closest_distance = float("inf")
        closest_element = None
        vertices = self.threed_model.vertices

        for i, vertex in enumerate(vertices):
            distance = self.distance_to_ray(near, ray_direction, np.array(vertex))

            pick_radius = 0.1
            if distance is not None and distance < closest_distance and distance < pick_radius:
                closest_distance = distance
                closest_element = i
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
        intersection_point - v2
        dot00 = np.dot(edge0, edge0)
        dot01 = np.dot(edge0, edge1)
        np.dot(edge0, edge2)
        dot11 = np.dot(edge1, edge1)
        np.dot(edge1, edge2)
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

    def rotate(self, rotationX_rad, rotationY_rad, vertices):
        rotationXMatrix = np.array(
            [
                [1, 0, 0, 0],
                [0, np.cos(rotationY_rad), -np.sin(rotationY_rad), 0],
                [0, np.sin(rotationY_rad), np.cos(rotationY_rad), 0],
                [0, 0, 0, 1],
            ]
        )

        rotationYMatrix = np.array(
            [
                [np.cos(rotationX_rad), 0, np.sin(rotationX_rad), 0],
                [0, 1, 0, 0],
                [-np.sin(rotationX_rad), 0, np.cos(rotationX_rad), 0],
                [0, 0, 0, 1],
            ]
        )

        new_rotation_matrix = np.dot(rotationXMatrix, rotationYMatrix)
        self.rotation_matrix = np.dot(new_rotation_matrix, self.rotation_matrix)
        ones_column = np.ones((np.array(vertices).shape[0], 1))
        vertices_with_ones = np.hstack((vertices, ones_column))
        new_vertices_with_ones = np.dot(vertices_with_ones, self.rotation_matrix.T)
        new_vertices = new_vertices_with_ones[:, 0:3]

        return new_vertices

    def reset_pose(self):
        # Reset transient/view state
        self.temp_rotate_x = 0
        self.temp_rotate_y = 0
        self.rotate_x = 0
        self.rotate_y = 0
        self.pan_x = 0
        self.pan_y = 0
        self.dolly = 0
        self.temp_dolly = 0
        self.temp_pan_x = 0
        self.temp_pan_y = 0

        # Reset rotation matrix to identity for any consumers relying on it
        self.rotation_matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])

        # Restore underlying geometry to its original (pre-rotation) state.
        # In OBJECT_MODE we can safely rebuild ops from the backing MdObject.
        try:
            if self.data_mode == OBJECT_MODE and getattr(self, "object", None) is not None:
                # Re-initialize ops/geometry from source object
                self.set_object(self.object)
            else:
                # In DATASET_MODE, align all shapes to the dataset baseline which
                # restores a canonical orientation without reconstructing ds_ops.
                self.align_object()
        except Exception:
            # Fallback to alignment if reconstruction is unavailable
            self.align_object()

        # Invalidate any cached GL display lists
        if hasattr(self, "gl_list") and self.gl_list is not None:
            gl.glDeleteLists(self.gl_list, 1)
            self.gl_list = None

        # Ensure immediate GL redraw
        self.updateGL()

    def sync_rotation(self):
        self.rotate_x += self.temp_rotate_x
        self.rotate_y += self.temp_rotate_y
        self.temp_rotate_x = 0
        self.temp_rotate_y = 0

        if self.data_mode == OBJECT_MODE:
            if self.obj_ops is None:
                return

            self.obj_ops.rotate_3d(math.radians(-1 * self.rotate_x), "Y")
            self.obj_ops.rotate_3d(math.radians(self.rotate_y), "X")
            if self.threed_model is not None:
                if self.show_model:
                    apply_rotation_to_vertex = True
                else:
                    apply_rotation_to_vertex = False
                self.threed_model.rotate(
                    math.radians(self.rotate_x), math.radians(self.rotate_y), apply_rotation_to_vertex
                )
                if self.show_model:
                    self.threed_model.generate()

        elif self.data_mode == DATASET_MODE:
            if self.ds_ops is None:
                return
            for obj in self.ds_ops.object_list:
                obj.rotate_3d(math.radians(-1 * self.rotate_x), "Y")
                obj.rotate_3d(math.radians(self.rotate_y), "X")

        self.rotate_x = 0
        self.rotate_y = 0

    # Fallback rendering functions for when GLUT is not available
    def draw_wireframe_cube(self):
        """Draw a simple wireframe cube as fallback for glutSolidCube."""
        size = 0.5
        gl.glBegin(gl.GL_LINES)
        # Front face
        gl.glVertex3f(-size, -size, size)
        gl.glVertex3f(size, -size, size)
        gl.glVertex3f(size, -size, size)
        gl.glVertex3f(size, size, size)
        gl.glVertex3f(size, size, size)
        gl.glVertex3f(-size, size, size)
        gl.glVertex3f(-size, size, size)
        gl.glVertex3f(-size, -size, size)
        # Back face
        gl.glVertex3f(-size, -size, -size)
        gl.glVertex3f(size, -size, -size)
        gl.glVertex3f(size, -size, -size)
        gl.glVertex3f(size, size, -size)
        gl.glVertex3f(size, size, -size)
        gl.glVertex3f(-size, size, -size)
        gl.glVertex3f(-size, size, -size)
        gl.glVertex3f(-size, -size, -size)
        # Connecting lines
        gl.glVertex3f(-size, -size, size)
        gl.glVertex3f(-size, -size, -size)
        gl.glVertex3f(size, -size, size)
        gl.glVertex3f(size, -size, -size)
        gl.glVertex3f(size, size, size)
        gl.glVertex3f(size, size, -size)
        gl.glVertex3f(-size, size, size)
        gl.glVertex3f(-size, size, -size)
        gl.glEnd()

    def draw_simple_cone(self):
        """Draw a simple cone as fallback for glutSolidCone."""
        # Use a simple pyramid shape
        gl.glBegin(gl.GL_TRIANGLES)
        # Base triangles
        for i in range(8):
            angle1 = 2.0 * math.pi * i / 8
            angle2 = 2.0 * math.pi * (i + 1) / 8
            gl.glVertex3f(0, 0, 0.03)  # Tip
            gl.glVertex3f(0.02 * math.cos(angle1), 0.02 * math.sin(angle1), 0)
            gl.glVertex3f(0.02 * math.cos(angle2), 0.02 * math.sin(angle2), 0)
        gl.glEnd()

    def draw_sphere(self, radius):
        """Draw a sphere using GLU as fallback for glutSolidSphere."""
        if not hasattr(self, "glu_quadric"):
            self.glu_quadric = glu.gluNewQuadric()

        if self.glu_quadric:
            glu.gluSphere(self.glu_quadric, radius, 10, 10)
        else:
            # Ultimate fallback: draw a point
            gl.glPointSize(radius * 100)
            gl.glBegin(gl.GL_POINTS)
            gl.glVertex3f(0, 0, 0)
            gl.glEnd()
