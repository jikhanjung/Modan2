"""
ObjectViewer2D - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from PyQt5.QtCore import (
    QPointF,
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
)
from scipy.spatial.distance import cdist

from MdModel import MdDataset, MdDatasetOps, MdObject, MdObjectOps

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
import math
import os
from pathlib import Path

import numpy as np

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


class ObjectViewer2D(QLabel):
    def __init__(self, parent=None, transparent=False):
        if transparent:
            super().__init__(parent)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowTransparentForInput | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_NoSystemBackground, True)
        else:
            super().__init__(parent)
        self.transparent = transparent
        self.parent = parent
        logger.info("object viewer 2d init")
        self.setMinimumSize(300, 200)

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
        self.pan_mode = MODE["NONE"]
        self.edit_mode = MODE["NONE"]
        self.data_mode = OBJECT_MODE

        self.show_index = False
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
        self.set_mode(MODE["EDIT_LANDMARK"])
        self.comparison_data = {}
        self.source_preference = None
        self.target_preference = None
        self.ds_ops = None

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

        self.update_tps_grid()

    def set_ds_ops(self, ds_ops):
        self.ds_ops = ds_ops
        self.data_mode = DATASET_MODE
        average_shape = self.ds_ops.get_average_shape()
        self.landmark_list = average_shape.landmark_list
        # self.set_object(average_shape)
        self.calculate_resize()
        self.align_object()
        # scale = self.get_scale_from_object(average_shape)
        # average_shape.rescale(scale)
        # for obj in self.ds_ops.object_list:
        #    obj.rescale(scale)
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

    def set_landmark_pref(self, lm_pref, wf_pref, bgcolor):
        self.landmark_size = lm_pref["size"]
        self.landmark_color = lm_pref["color"]
        self.wireframe_thickness = wf_pref["thickness"]
        self.wireframe_color = wf_pref["color"]
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
        if coord is None:
            return 0  # Return safe default value
        return round((float(coord) / self.image_canvas_ratio) * self.scale) + self.pan_x + self.temp_pan_x

    def _2cany(self, coord):
        if coord is None:
            return 0  # Return safe default value
        return round((float(coord) / self.image_canvas_ratio) * self.scale) + self.pan_y + self.temp_pan_y

    def _2imgx(self, coord):
        if coord is None:
            return 0  # Return safe default value
        return round(((float(coord) - self.pan_x) / self.scale) * self.image_canvas_ratio)

    def _2imgy(self, coord):
        if coord is None:
            return 0  # Return safe default value
        return round(((float(coord) - self.pan_y) / self.scale) * self.image_canvas_ratio)

    def show_message(self, msg):
        if self.object_dialog is not None:
            self.object_dialog.status_bar.showMessage(msg)

    def set_mode(self, mode):
        self.edit_mode = mode
        if self.edit_mode == MODE["EDIT_LANDMARK"]:
            self.setCursor(Qt.CrossCursor)
            self.show_message(self.tr("Click on image to add landmark"))
        elif self.edit_mode == MODE["READY_MOVE_LANDMARK"]:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message(self.tr("Click on landmark to move"))
        elif self.edit_mode == MODE["MOVE_LANDMARK"]:
            self.setCursor(Qt.SizeAllCursor)
            self.show_message(self.tr("Move landmark"))
        elif self.edit_mode == MODE["CALIBRATION"]:
            self.setCursor(Qt.CrossCursor)
            self.show_message(self.tr("Click on image to calibrate"))
        else:
            self.setCursor(Qt.ArrowCursor)

    def get_landmark_index_within_threshold(self, curr_pos, threshold=DISTANCE_THRESHOLD):
        for index, landmark in enumerate(self.landmark_list):
            # Skip missing landmarks
            if landmark[0] is None or landmark[1] is None:
                continue
            lm_can_pos = [self._2canx(landmark[0]), self._2cany(landmark[1])]
            dist = self.get_distance(curr_pos, lm_can_pos)
            if dist < threshold:
                return index
        return -1

    def get_edge_index_within_threshold(self, curr_pos, threshold=DISTANCE_THRESHOLD):
        if len(self.edge_list) == 0:
            return -1

        for index, wire in enumerate(self.edge_list):
            from_lm_idx = wire[0] - 1
            to_lm_idx = wire[1] - 1
            if from_lm_idx >= len(self.landmark_list) or to_lm_idx >= len(self.landmark_list):
                continue

            # Skip edges with missing landmarks
            from_lm = self.landmark_list[from_lm_idx]
            to_lm = self.landmark_list[to_lm_idx]
            if from_lm[0] is None or from_lm[1] is None or to_lm[0] is None or to_lm[1] is None:
                continue

            wire_start = [self._2canx(float(from_lm[0])), self._2cany(float(from_lm[1]))]
            wire_end = [self._2canx(float(to_lm[0])), self._2cany(float(to_lm[1]))]
            dist = self.get_distance_to_line(curr_pos, wire_start, wire_end)
            if dist < threshold and dist > 0:
                return index
        return -1

    def get_distance_to_line(self, curr_pos, line_start, line_end):
        x1 = line_start[0]
        y1 = line_start[1]
        x2 = line_end[0]
        y2 = line_end[1]
        max_x = max(x1, x2)
        min_x = min(x1, x2)
        max_y = max(y1, y2)
        min_y = min(y1, y2)
        if curr_pos[0] > max_x or curr_pos[0] < min_x or curr_pos[1] > max_y or curr_pos[1] < min_y:
            return -1
        x0 = curr_pos[0]
        y0 = curr_pos[1]
        numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        denominator = math.sqrt(math.pow(y2 - y1, 2) + math.pow(x2 - x1, 2))
        return numerator / denominator

    def get_distance(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    def mouseMoveEvent(self, event):
        if self.object_dialog is None:
            return
        me = QMouseEvent(event)
        self.mouse_curr_x = me.x()
        self.mouse_curr_y = me.y()
        curr_pos = [self.mouse_curr_x, self.mouse_curr_y]

        if self.pan_mode == MODE["PAN"]:
            self.temp_pan_x = int(self.mouse_curr_x - self.mouse_down_x)
            self.temp_pan_y = int(self.mouse_curr_y - self.mouse_down_y)

        elif self.edit_mode == MODE["EDIT_LANDMARK"]:
            near_idx = self.get_landmark_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
            if near_idx >= 0:
                self.set_mode(MODE["READY_MOVE_LANDMARK"])
                self.selected_landmark_index = near_idx

        elif self.edit_mode == MODE["WIREFRAME"]:
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
                    self.edge_list[near_wire_idx]
                    self.selected_edge_index = near_wire_idx
                else:
                    self.selected_edge_index = -1

        elif self.edit_mode == MODE["MOVE_LANDMARK"]:
            if self.selected_landmark_index >= 0:
                self.landmark_list[self.selected_landmark_index] = [
                    self._2imgx(self.mouse_curr_x),
                    self._2imgy(self.mouse_curr_y),
                ]
                if self.object_dialog is not None:
                    self.object_dialog.update_landmark(
                        self.selected_landmark_index, *self.landmark_list[self.selected_landmark_index]
                    )

        elif self.edit_mode == MODE["READY_MOVE_LANDMARK"]:
            curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
            ready_landmark = self.landmark_list[self.selected_landmark_index]
            # Don't try to move missing landmarks
            if ready_landmark[0] is None or ready_landmark[1] is None:
                return
            lm_can_pos = [self._2canx(ready_landmark[0]), self._2cany(ready_landmark[1])]
            if self.get_distance(curr_pos, lm_can_pos) > DISTANCE_THRESHOLD:
                self.set_mode(MODE["EDIT_LANDMARK"])
                self.selected_landmark_index = -1

        self.repaint()
        QLabel.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        me = QMouseEvent(event)
        if me.button() == Qt.LeftButton:
            if self.edit_mode == MODE["EDIT_LANDMARK"]:
                if self.orig_pixmap is None:
                    return
                img_x = self._2imgx(self.mouse_curr_x)
                img_y = self._2imgy(self.mouse_curr_y)
                if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                    return
                self.object_dialog.add_landmark(img_x, img_y)
            elif self.edit_mode == MODE["READY_MOVE_LANDMARK"]:
                self.set_mode(MODE["MOVE_LANDMARK"])
            elif self.edit_mode == MODE["WIREFRAME"]:
                if self.wire_hover_index >= 0:
                    if self.wire_start_index < 0:
                        self.wire_start_index = self.wire_hover_index
                        self.wire_hover_index = -1
            elif self.edit_mode == MODE["CALIBRATION"]:
                self.calibration_from_img_x = self._2imgx(self.mouse_curr_x)
                self.calibration_from_img_y = self._2imgy(self.mouse_curr_y)

        elif me.button() == Qt.RightButton:
            if self.edit_mode == MODE["WIREFRAME"]:
                if self.wire_start_index >= 0:
                    self.wire_start_index = -1
                    self.wire_hover_index = -1
                elif self.selected_edge_index >= 0:
                    self.delete_edge(self.selected_edge_index)
                    self.selected_edge_index = -1
            elif self.edit_mode == MODE["READY_MOVE_LANDMARK"]:
                if self.selected_landmark_index >= 0:
                    self.object_dialog.delete_landmark(self.selected_landmark_index)
                    self.selected_landmark_index = -1
                    self.set_mode(MODE["EDIT_LANDMARK"])
            else:
                self.pan_mode = MODE["PAN"]
                self.mouse_down_x = me.x()
                self.mouse_down_y = me.y()

        self.repaint()

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        if self.object_dialog is None:
            return
        QMouseEvent(ev)
        if self.pan_mode == MODE["PAN"]:
            self.pan_mode = MODE["NONE"]
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
            self.repaint()
        elif self.edit_mode == MODE["MOVE_LANDMARK"]:
            self.set_mode(MODE["EDIT_LANDMARK"])
            self.selected_landmark_index = -1
        elif self.edit_mode == MODE["WIREFRAME"]:
            if self.wire_start_index >= 0 and self.wire_hover_index >= 0:
                # print("wire start:", self.wire_start_index, "wire hover:", self.wire_hover_index)
                self.add_edge(self.wire_start_index, self.wire_hover_index)
                self.wire_start_index = -1
                self.wire_hover_index = -1
                self.wire_end_index = -1
        elif self.edit_mode == MODE["CALIBRATION"]:
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
        self.pan_x = round(we.pos().x() - (we.pos().x() - self.pan_x) * scale_proportion)
        self.pan_y = round(we.pos().y() - (we.pos().y() - self.pan_y) * scale_proportion)

        QLabel.wheelEvent(self, event)
        self.repaint()
        event.accept()

    def adjust_scale(self, scale_delta_ratio, recurse=True):
        if self.parent is not None and callable(getattr(self.parent, "sync_zoom", None)) and recurse:
            self.parent.sync_zoom(self, scale_delta_ratio)

        if self.scale > 1:
            scale_delta = math.floor(self.scale) * scale_delta_ratio
        else:
            scale_delta = scale_delta_ratio

        self.scale += scale_delta
        self.scale = round(self.scale * 10) / 10

        if self.orig_pixmap is not None:
            self.curr_pixmap = self.orig_pixmap.scaled(
                int(self.orig_pixmap.width() * self.scale / self.image_canvas_ratio),
                int(self.orig_pixmap.height() * self.scale / self.image_canvas_ratio),
            )

        self.repaint()

    def reset_pose(self):
        self.calculate_resize()

    def dragEnterEvent(self, event):
        if self.object_dialog is None:
            return
        file_name = event.mimeData().text()
        if file_name.split(".")[-1].lower() in mu.IMAGE_EXTENSION_LIST:
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

        for _idx, obj in enumerate(ds_ops.object_list):
            logger.debug(f"draw object: {obj}, landmarks: {obj.landmark_list}")
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
                painter,
                obj,
                landmark_as_sphere=False,
                color=object_color,
                edge_color=edge_color,
                polygon_color=polygon_color,
            )

        if self.show_average:
            object_color = COLOR["AVERAGE_SHAPE"]
            self.draw_object(ds_ops.get_average_shape(), landmark_as_sphere=True, color=object_color)

    def draw_dataset(self, painter):
        ds_ops = self.ds_ops

        # Generate TPS grid if not already generated
        if not hasattr(self, "grid_lines_transformed"):
            self.generate_tps_grid()

        # Draw TPS grid
        if hasattr(self, "grid_lines_transformed"):
            pen = QPen(QColor(235, 235, 235, 70))  # Light blue, semi-transparent
            pen.setWidth(2)
            painter.setPen(pen)

            # Draw transformed grid lines
            for _direction, line in self.grid_lines_transformed:
                # Skip lines with None values
                valid_line = all(p[0] is not None and p[1] is not None for p in line)
                if not valid_line:
                    continue
                points = [QPointF(self._2canx(p[0]), self._2cany(p[1])) for p in line]
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])

        # Draw shapes
        if self.show_arrow and len(ds_ops.object_list) > 1:
            self.draw_arrow(painter, 0, 1)

        for _idx, obj in enumerate(ds_ops.object_list):
            if not obj.visible:
                continue
            if obj.id in ds_ops.selected_object_id_list:
                object_color = COLOR["SELECTED_SHAPE"]
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

            self.draw_object(
                painter,
                obj,
                landmark_as_sphere=False,
                color=object_color,
                edge_color=edge_color,
                polygon_color=polygon_color,
            )

        if self.show_average:
            object_color = COLOR["AVERAGE_SHAPE"]
            self.draw_object(ds_ops.get_average_shape(), landmark_as_sphere=True, color=object_color)

    def draw_arrow(self, painter, start_idx, end_idx):
        from_obj = self.ds_ops.object_list[start_idx]
        to_obj = self.ds_ops.object_list[end_idx]
        for idx, from_lm in enumerate(from_obj.landmark_list):
            to_lm = to_obj.landmark_list[idx]
            from_x = from_lm[0]
            from_y = from_lm[1]
            to_x = to_lm[0]
            to_y = to_lm[1]
            self.draw_line(painter, from_x, from_y, to_x, to_y, COLOR["RED"])

    def draw_object(
        self,
        painter,
        obj,
        landmark_as_sphere=False,
        color=COLOR["NORMAL_SHAPE"],
        edge_color=COLOR["WIREFRAME"],
        polygon_color=COLOR["WIREFRAME"],
    ):
        if obj.show_landmark:
            for idx, landmark in enumerate(obj.landmark_list):
                # Check for missing landmarks
                if landmark[0] is None or landmark[1] is None:
                    # Skip missing landmarks in dataset view
                    # (they are properly displayed in Object Dialog with estimation)
                    continue
                else:
                    self.draw_landmark(painter, landmark[0], landmark[1], color)
        if obj.show_wireframe:
            for edge in self.ds_ops.edge_list:
                from_lm_idx = edge[0] - 1
                to_lm_idx = edge[1] - 1
                if from_lm_idx >= len(obj.landmark_list) or to_lm_idx >= len(obj.landmark_list):
                    continue
                from_lm = obj.landmark_list[from_lm_idx]
                to_lm = obj.landmark_list[to_lm_idx]
                # Skip edges with missing landmarks
                if from_lm[0] is None or from_lm[1] is None or to_lm[0] is None or to_lm[1] is None:
                    continue
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
        # print("color:", color)
        painter.setPen(QPen(mu.as_qt_color(color), 2))
        painter.drawLine(
            int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y))
        )

    def draw_landmark(self, painter, x, y, color):
        radius = BASE_LANDMARK_RADIUS * (int(self.landmark_size) + 1)
        painter.setPen(QPen(mu.as_qt_color(color), 2))
        painter.setBrush(QBrush(mu.as_qt_color(color)))
        painter.drawEllipse(int(self._2canx(x) - radius), int(self._2cany(y)) - radius, radius * 2, radius * 2)

    def draw_estimated_landmark(self, painter, x, y, idx):
        """Draw an estimated landmark position with distinctive visual style"""
        radius = BASE_LANDMARK_RADIUS * (int(self.landmark_size) + 1)

        # Convert to screen coordinates
        screen_x = int(self._2canx(x))
        screen_y = int(self._2cany(y))

        # Use same color as normal landmarks
        if self.obj_ops and self.obj_ops.landmark_color:
            color = QColor(self.obj_ops.landmark_color)
        else:
            color = QColor(self.landmark_color)

        # Draw unfilled circle (hollow) with solid line
        painter.setPen(QPen(color, 2, Qt.SolidLine))
        painter.setBrush(Qt.NoBrush)  # No fill
        painter.drawEllipse(screen_x - radius, screen_y - radius, radius * 2, radius * 2)

        # Draw index with question mark if enabled
        if self.show_index:
            idx_color = QColor(self.index_color)
            painter.setFont(QFont("Helvetica", 10 + int(self.index_size) * 3))
            painter.setPen(QPen(idx_color, 2))
            # Draw index number followed by question mark
            painter.drawText(screen_x + 10, screen_y + 10, f"{idx + 1}?")

    def draw_missing_landmark(self, painter, idx, total_landmarks):
        """Draw an indicator for missing landmarks - shows as an X mark"""
        # Try to position the X mark based on the index
        # This is a rough approximation - ideally would be based on nearby landmarks
        radius = BASE_LANDMARK_RADIUS * (int(self.landmark_size) + 1) + 2

        # Calculate an approximate position (will be improved in future)
        # For now, just draw at origin or calculated from index
        x = self.width() / 2
        y = self.height() / 2
        if total_landmarks > 0:
            # Simple linear arrangement for visualization
            # Ensure X mark stays within bounds with padding
            padding = radius + 10
            x = padding + (self.width() - 2 * padding) * (idx / max(1, total_landmarks - 1))
            y = self.height() * 0.5

        # Draw X mark in red with dashed lines
        painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
        x_pos = int(x)
        y_pos = int(y)
        # Draw X with slightly larger size to be more visible
        x_size = radius
        painter.drawLine(x_pos - x_size, y_pos - x_size, x_pos + x_size, y_pos + x_size)
        painter.drawLine(x_pos - x_size, y_pos + x_size, x_pos + x_size, y_pos - x_size)

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.transparent:
            painter.fillRect(self.rect(), QBrush(QColor(self.bgcolor)))
        if self.object is None:
            # print("no object")
            if self.ds_ops is not None:
                self.draw_dataset(painter)
            return
        if self.curr_pixmap is not None:
            painter.drawPixmap(self.pan_x + self.temp_pan_x, self.pan_y + self.temp_pan_y, self.curr_pixmap)

        if self.show_wireframe:
            if self.obj_ops.edge_color:
                color = QColor(self.obj_ops.edge_color)
            else:
                color = QColor(self.wireframe_color)
            painter.setPen(QPen(color, int(self.wireframe_thickness) + 1))
            painter.setBrush(QBrush(color))

            for wire in self.edge_list:
                from_lm_idx = wire[0] - 1
                to_lm_idx = wire[1] - 1
                if from_lm_idx >= len(self.landmark_list) or to_lm_idx >= len(self.landmark_list):
                    continue
                from_lm = self.landmark_list[from_lm_idx]
                to_lm = self.landmark_list[to_lm_idx]
                # Skip edges with missing landmarks
                if from_lm[0] is None or from_lm[1] is None or to_lm[0] is None or to_lm[1] is None:
                    continue
                [from_x, from_y] = from_lm
                [to_x, to_y] = to_lm
                painter.drawLine(
                    int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y))
                )
            if self.selected_edge_index >= 0:
                edge = self.edge_list[self.selected_edge_index]
                from_lm_idx = edge[0] - 1
                to_lm_idx = edge[1] - 1
                painter.setPen(QPen(mu.as_qt_color(COLOR["SELECTED_EDGE"]), 2))
                if from_lm_idx >= len(self.landmark_list) or to_lm_idx >= len(self.landmark_list):
                    pass
                else:
                    [from_x, from_y] = self.landmark_list[from_lm_idx]
                    [to_x, to_y] = self.landmark_list[to_lm_idx]
                    painter.drawLine(
                        int(self._2canx(from_x)),
                        int(self._2cany(from_y)),
                        int(self._2canx(to_x)),
                        int(self._2cany(to_y)),
                    )

        radius = BASE_LANDMARK_RADIUS * (int(self.landmark_size) + 1)
        painter.setPen(QPen(Qt.blue, 2))
        painter.setBrush(QBrush(Qt.blue))
        if self.edit_mode == MODE["CALIBRATION"]:
            if self.calibration_from_img_x >= 0 and self.calibration_from_img_y >= 0:
                x1 = int(self._2canx(self.calibration_from_img_x))
                y1 = int(self._2cany(self.calibration_from_img_y))
                x2 = self.mouse_curr_x
                y2 = self.mouse_curr_y
                painter.setPen(QPen(mu.as_qt_color(COLOR["SELECTED_LANDMARK"]), 2))
                painter.drawLine(x1, y1, x2, y2)

        painter.setFont(QFont("Helvetica", 10 + int(self.index_size) * 3))
        for idx, landmark in enumerate(self.landmark_list):
            # Check for missing landmarks
            if landmark[0] is None or landmark[1] is None:
                # Check if we have an estimated position from object_dialog
                if hasattr(self, "object_dialog") and self.object_dialog:
                    if (
                        hasattr(self.object_dialog, "estimated_landmark_list")
                        and self.object_dialog.estimated_landmark_list is not None
                        and idx < len(self.object_dialog.estimated_landmark_list)
                    ):
                        est_lm = self.object_dialog.estimated_landmark_list[idx]
                        if est_lm[0] is not None and est_lm[1] is not None:
                            # Draw estimated landmark with distinctive style
                            self.draw_estimated_landmark(painter, est_lm[0], est_lm[1], idx)
                            continue
                # Skip missing landmarks (no estimation available or not in object_dialog)
                # Missing landmarks should only be shown with proper estimation in Object Dialog
                continue

            if idx == self.wire_hover_index:
                painter.setPen(QPen(mu.as_qt_color(COLOR["SELECTED_LANDMARK"]), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR["SELECTED_LANDMARK"])))
            elif idx == self.wire_start_index or idx == self.wire_end_index:
                painter.setPen(QPen(mu.as_qt_color(COLOR["SELECTED_LANDMARK"]), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR["SELECTED_LANDMARK"])))
            elif idx == self.selected_landmark_index:
                painter.setPen(QPen(mu.as_qt_color(COLOR["SELECTED_LANDMARK"]), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR["SELECTED_LANDMARK"])))
            else:
                if self.obj_ops.landmark_color:
                    color = QColor(self.obj_ops.landmark_color)
                else:
                    color = QColor(self.landmark_color)
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(color))
            painter.drawEllipse(
                int(self._2canx(landmark[0]) - radius), int(self._2cany(landmark[1])) - radius, radius * 2, radius * 2
            )
            if self.show_index:
                idx_color = QColor(self.index_color)
                painter.setPen(QPen(idx_color, 2))
                painter.setBrush(QBrush(idx_color))
                painter.drawText(int(self._2canx(landmark[0]) + 10), int(self._2cany(landmark[1])) + 10, str(idx + 1))

        # draw wireframe being edited
        if self.wire_start_index >= 0:
            painter.setPen(QPen(mu.as_qt_color(COLOR["WIREFRAME"]), 2))
            painter.setBrush(QBrush(mu.as_qt_color(COLOR["WIREFRAME"])))
            start_lm = self.landmark_list[self.wire_start_index]
            painter.drawLine(
                int(self._2canx(start_lm[0])), int(self._2cany(start_lm[1])), self.mouse_curr_x, self.mouse_curr_y
            )

        if self.object.pixels_per_mm is not None and self.object.pixels_per_mm > 0:
            pixels_per_mm = self.object.pixels_per_mm
            max_scalebar_size = 120
            bar_width = (float(pixels_per_mm) / self.image_canvas_ratio) * self.scale
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
            x = self.width() - 15 - (bar_width + 20)
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
                length_text = str(int(actual_length / 10)) + " cm"
            elif actual_length >= 1:
                length_text = str(int(actual_length)) + " mm"
            elif actual_length >= 0.001:
                length_text = str(int(actual_length * 1000.0)) + " um"
            else:
                length_text = str(round(actual_length * 1000000.0 * 1000) / 1000) + " nm"
            painter.setPen(QPen(Qt.black, 1))
            painter.setFont(QFont("Helvetica", 10))
            painter.drawText(
                x + int(math.floor(float(bar_width) / 2.0 + 0.5)) - len(length_text) * 4, y - 5, length_text
            )

        if self.debug:
            painter.setPen(QPen(Qt.black, 1))
            painter.setFont(QFont("Helvetica", 10))
            painter.drawText(
                10,
                20,
                f"Scale: {self.scale} prev_scale: {self.prev_scale} image_to_canvas_ratio: {self.image_canvas_ratio}, pan: {self.pan_x}, {self.pan_y}",
            )

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
            self.curr_pixmap = self.orig_pixmap.scaled(
                int(self.orig_width * self.scale / self.image_canvas_ratio),
                int(self.orig_width * self.scale / self.image_canvas_ratio),
                Qt.KeepAspectRatio,
            )
        else:
            if len(self.landmark_list) < 2:
                return
            # no image landmark showing
            min_x = 999999999
            max_x = -999999999
            min_y = 999999999
            max_y = -999999999
            for _idx, landmark in enumerate(self.landmark_list):
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
            w_scale = (self.width() * 1.0) / (width * 1.5)
            h_scale = (self.height() * 1.0) / (height * 1.5)
            self.scale = min(w_scale, h_scale)
            self.pan_x = int(-min_x * self.scale + (self.width() - width * self.scale) / 2.0)
            self.pan_y = int(-min_y * self.scale + (self.height() - height * self.scale) / 2.0)

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

    def set_image(self, file_path):
        if self.fullpath is not None:
            self.image_changed = True

        self.fullpath = file_path
        self.curr_pixmap = self.orig_pixmap = QPixmap(file_path)
        self.setPixmap(self.curr_pixmap)

    def clear_object(self):
        # print("object view clear object")
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

    def add_edge(self, wire_start_index, wire_end_index):
        # print("add edge")
        if wire_start_index == wire_end_index:
            return
        if wire_start_index > wire_end_index:
            wire_start_index, wire_end_index = wire_end_index, wire_start_index
        dataset = self.object.dataset
        # print("edge list 1:", dataset.edge_list)
        for wire in dataset.edge_list:
            if wire[0] == wire_start_index + 1 and wire[1] == wire_end_index + 1:
                return
        dataset.edge_list.append([wire_start_index + 1, wire_end_index + 1])
        # print("edge list 2:", dataset.edge_list)
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
            angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
            boundary = np.column_stack((center[0] + radius * np.cos(angles), center[1] + radius * np.sin(angles)))
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
            self.grid_lines_orig.append(("v", line_points))

        # Horizontal lines
        for i in range(n_grid):
            line_points = np.array([(x_, y[i]) for x_ in x])
            self.grid_lines_orig.append(("h", line_points))

        # Calculate TPS parameters
        self.tps_weights, self.tps_affine = self.calculate_tps_params(
            self.source_with_boundary, self.target_with_boundary
        )

        # Transform grid lines
        self.grid_lines_transformed = []
        for direction, line in self.grid_lines_orig:
            transformed_line = np.array(
                [self.transform_point(p, self.source_with_boundary, self.tps_weights, self.tps_affine) for p in line]
            )
            self.grid_lines_transformed.append((direction, transformed_line))

    def calculate_tps_params(self, control_points, target_points):
        """Calculate TPS transformation parameters"""

        def U(r):
            return (r**2) * np.log(r + np.finfo(float).eps)

        n = control_points.shape[0]
        K = cdist(control_points, control_points)
        K = U(K)
        P = np.hstack([np.ones((n, 1)), control_points])
        L = np.vstack([np.hstack([K, P]), np.hstack([P.T, np.zeros((3, 3))])])
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
        if hasattr(self, "grid_lines_transformed"):
            delattr(self, "grid_lines_transformed")
        self.generate_tps_grid()
        self.update()
