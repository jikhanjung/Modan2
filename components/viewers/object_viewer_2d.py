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
    QImage,
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

import MdLiveWire
import MdUtils as mu

logger = logging.getLogger(__name__)

from MdConstants import BASE_LANDMARK_RADIUS, COLOR, DATASET_MODE, DISTANCE_THRESHOLD, MODE, OBJECT_MODE

# Cap on the scaled render pixmap's longer side. adjust_scale allocates a
# pixmap proportional to the zoom scale, and the scale itself grows
# near-exponentially under repeated zoom-in (scale += floor(scale) * ratio), so
# without a cap a burst of wheel events could request a multi-GB allocation and
# take the process down (kernel OOM — devlog 220). 8192 px on the longer side
# (~256 MB RGBA worst case) is far beyond any useful landmarking zoom.
MAX_SCALED_PIXMAP_DIM = 8192


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
        # Optional full-resolution render source ("Show Original"): sharpens
        # what curr_pixmap is resampled from, while orig_pixmap (the stored
        # working copy) keeps defining the landmark coordinate space.
        self.fullres_pixmap = None
        self.scale = 1.0
        self.prev_scale = 1.0
        self.fullpath = None
        self.image_changed = False
        self.pan_mode = MODE["NONE"]
        self.edit_mode = MODE["NONE"]
        self.data_mode = OBJECT_MODE

        self.show_index = False
        # Draw the dataset landmark name/abbreviation instead of the index number.
        self.show_landmark_name = False
        self.show_wireframe = True
        self.show_polygon = True
        # Toggle the raw traced curves and the derived semi-landmarks (both are
        # display-only in the merge-at-analysis model).
        self.show_curve = True
        self.show_semi_landmark = True
        # Show expected positions of not-yet-placed landmarks while digitizing (2D).
        self.show_expected = False
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
        # Raw points of the curve currently being traced in EDIT_CURVE mode
        # (image coordinates). Committed to semi-landmarks on double-click.
        self.current_curve_points = []
        # The sparse points actually clicked during an edge-snapped trace (the
        # dense path lives in current_curve_points). Stored with the finished
        # curve so it can later be edited by its clicks and re-snapped.
        self.current_curve_anchors = []
        # When a curve is selected (from the object dialog's curve table) its raw
        # trace points become editable instead of tracing a new curve.
        self.selected_curve_id = None
        self.moving_curve_point_index = -1
        self.hover_curve_point_index = -1
        # Curve currently under the cursor (highlighted like a selection) in
        # landmark or curve mode.
        self.hover_curve_id = None
        # Live-wire (intelligent scissors) curve auto-detection. When enabled,
        # tracing snaps to the strongest image edge between clicks. The LiveWire
        # is built lazily from the current image and rebuilt when it changes;
        # livewire_preview holds the snapped path from the last point to the
        # cursor for painting.
        self.livewire_enabled = False
        # Smooth the snapped trace (remove the live-wire pixel staircase) before
        # it becomes semi-landmarks. Endpoints/anchors stay pinned.
        self.smooth_curves = True
        self._livewire = None
        self._livewire_path = None
        self.livewire_preview = []
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
        # Accept keyboard focus on click so curve mode can handle Enter (accept)
        # and Esc (cancel); QLabel takes no focus by default.
        self.setFocusPolicy(Qt.ClickFocus)
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
        if mode != MODE["EDIT_CURVE"]:
            # Leaving curve editing clears the selected curve and its edit state.
            self.selected_curve_id = None
            self.moving_curve_point_index = -1
            self.hover_curve_point_index = -1
            self.livewire_preview = []
            self.current_curve_anchors = []
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
        elif self.edit_mode == MODE["EDIT_CURVE"]:
            self.setCursor(Qt.CrossCursor)
            self.current_curve_points = []
            self.current_curve_anchors = []
            self.show_message(self._curve_hint())
        else:
            self.setCursor(Qt.ArrowCursor)

    def _curve_hint(self):
        """Status-bar guidance for curve tracing, tailored to the snap toggle."""
        if self.livewire_enabled:
            return self.tr("Snap on: click along the edge; Enter/double-click to accept, Esc/right-click to cancel")
        return self.tr("Click to trace a curve; Enter/double-click to accept, Esc/right-click to cancel")

    def set_livewire_enabled(self, enabled):
        """Toggle live-wire snapping for curve tracing.

        Enabling it lazily builds the cost map from the current image the first
        time a snap is needed. Disabling drops any in-progress preview.
        """
        self.livewire_enabled = bool(enabled)
        if not self.livewire_enabled:
            self.livewire_preview = []
        if self.edit_mode == MODE["EDIT_CURVE"]:
            self.show_message(self._curve_hint())
        self.repaint()

    def set_smooth_curves(self, enabled):
        """Toggle smoothing of snapped traces; re-snap the selected curve so the
        change shows immediately."""
        self.smooth_curves = bool(enabled)
        if self.selected_curve_id is not None:
            self._resnap_selected_curve()
            self._notify_curve_edited()
        self.repaint()

    def _reset_livewire(self):
        """Forget the cached cost map (e.g. after the image changes)."""
        self._livewire = None
        self._livewire_path = None
        self.livewire_preview = []

    def _pixmap_to_gray(self, pixmap):
        """A QPixmap as a 2D uint8 grayscale numpy array (rows=y, cols=x)."""
        image = pixmap.toImage().convertToFormat(QImage.Format_Grayscale8)
        w, h = image.width(), image.height()
        if w == 0 or h == 0:
            return None
        ptr = image.constBits()
        ptr.setsize(image.sizeInBytes())
        # Rows are padded to a 4-byte boundary; slice off the padding.
        stride = image.bytesPerLine()
        buf = np.frombuffer(ptr, dtype=np.uint8).reshape(h, stride)
        return buf[:, :w].copy()

    def _ensure_livewire(self):
        """Build the live-wire cost map from orig_pixmap on first use; cache it.

        The cost map lives in orig_pixmap pixel space, which is exactly the
        coordinate space of the traced curve points (via _2imgx/_2imgy), so no
        extra transform is needed. Returns the LiveWire or None if unavailable.
        """
        if self._livewire is not None:
            return self._livewire
        if self.orig_pixmap is None or self.orig_pixmap.isNull():
            return None
        gray = self._pixmap_to_gray(self.orig_pixmap)
        if gray is None:
            return None
        self._livewire = MdLiveWire.build_livewire(gray)
        return self._livewire

    def _maybe_smooth(self, path):
        """Smooth a snapped path (pinning its endpoints) when smoothing is on."""
        if self.smooth_curves and len(path) >= 3:
            return mu.smooth_polyline(path)
        return path

    def _livewire_segment(self, start_img, end_img):
        """Snapped path between two image-space points, endpoints included.

        Falls back to a straight two-point segment when live-wire is unavailable.
        """
        wire = self._ensure_livewire()
        if wire is None:
            return [list(start_img), list(end_img)]
        return self._maybe_smooth(wire.find_path(start_img, end_img))

    def _curve_raw_map(self):
        """The object's raw curve traces (id -> polyline).

        Prefer the live map being edited in the object dialog, falling back to
        the object's saved traces for read-only viewing. The dialog is the
        authority whenever it holds the map -- even when empty (every curve
        deleted), so a just-deleted curve does not reappear from the saved copy.
        """
        dlg = getattr(self, "object_dialog", None)
        if dlg is not None and hasattr(dlg, "curve_raw_map"):
            return dlg.curve_raw_map
        if self.object is not None:
            return self.object.get_curve_raw()
        return {}

    def _landmark_names(self):
        """Dataset-wide per-landmark names, preferring the dialog's dataset."""
        dlg = getattr(self, "object_dialog", None)
        dataset = getattr(dlg, "dataset", None) if dlg is not None else None
        if dataset is None:
            dataset = getattr(self, "dataset", None)
        return dataset.get_landmark_names() if dataset is not None else []

    def _landmark_label(self, idx, names):
        """Text drawn by a landmark: its name when enabled and set, else index."""
        if self.show_landmark_name and idx < len(names):
            name = names[idx].get("name")
            if name:
                return name
        return str(idx + 1)

    def _update_landmark_tooltip(self, curr_pos, global_pos):
        """Show a hovered landmark's description (or name) as a tooltip."""
        from PyQt5.QtWidgets import QToolTip

        near = self.get_landmark_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
        names = self._landmark_names()
        if 0 <= near < len(names):
            entry = names[near]
            text = entry.get("desc") or entry.get("name")
            if text:
                QToolTip.showText(global_pos, text, self)
                return
        # Fall back to a curve description/name when hovering a curve.
        curve_id = self._curve_at_position(curr_pos)
        if curve_id is not None:
            for curve in self._curve_config():
                if curve.get("id") == curve_id:
                    text = curve.get("desc") or curve.get("name")
                    if text:
                        QToolTip.showText(global_pos, text, self)
                        return
                    break
        QToolTip.hideText()

    def _curve_config(self):
        """Curve scheme, preferring the object dialog's in-memory copy.

        While the object dialog is open it is the single source of truth for the
        (unsaved) curve scheme; reading it here keeps display in sync with edits
        that have not been written to the database yet.
        """
        dlg = getattr(self, "object_dialog", None)
        if dlg is not None and hasattr(dlg, "curve_config"):
            return dlg.curve_config
        dataset = getattr(self, "dataset", None)
        return dataset.get_curve_config() if dataset is not None else []

    def _derived_semi_landmarks(self):
        """Semi-landmarks resampled from the raw curve traces for display.

        These are never stored on the object (merge-at-analysis model); they are
        derived from the raw traces and the curve scheme each paint.
        """
        raw_map = self._curve_raw_map()
        semis = []
        for curve in self._curve_config():
            raw = raw_map.get(curve.get("id"))
            if raw and len(raw) >= 2:
                try:
                    semis.extend(mu.resample_polyline(raw, curve.get("n", 0)))
                except ValueError:
                    pass
        return semis

    def _curve_anchor_map(self):
        """The object's snap anchors (id -> clicked points), from the dialog."""
        dlg = getattr(self, "object_dialog", None)
        return getattr(dlg, "curve_anchor_map", {}) if dlg is not None else {}

    def _curve_editpoints(self, curve_id):
        """Points the user manipulates for a curve: the sparse snap anchors if it
        has any, else its raw trace (whose points are the clicks for hand-traced
        curves). This is what edit hit-tests, drags, inserts and handles use."""
        if curve_id is None:
            return None
        anchors = self._curve_anchor_map().get(curve_id)
        if anchors:
            return anchors
        return self._curve_raw_map().get(curve_id)

    def _selected_curve_raw(self):
        """Editable points of the selected curve (anchors if snapped, else raw).

        Kept named ``_selected_curve_raw`` because every editing path (hit-test,
        drag, insert, delete) manipulates these points; for snap curves they are
        the anchors, and a re-snap rebuilds the dense trace afterwards.
        """
        return self._curve_editpoints(self.selected_curve_id)

    def _snap_segment(self, a, b, seed_a=True):
        """Snapped path a->b, seeding whichever endpoint is fixed during a drag.

        The live-wire caches predecessor trees per seed, so seeding the stationary
        endpoint keeps re-snapping cheap while the other end is dragged. Falls
        back to a straight segment when no image is available.
        """
        wire = self._ensure_livewire()
        if wire is None:
            return [list(a), list(b)]
        if seed_a:
            path = wire.find_path(a, b)
        else:
            path = wire.find_path(b, a)
            path.reverse()
        return self._maybe_smooth(path)

    def _resnap_selected_curve(self, moving_index=None):
        """Rebuild the selected snap-curve's dense trace from its edited anchors.

        No-op for a hand-traced curve (no anchors -- its raw points were edited
        directly). Snaps between consecutive anchors when an image is available,
        falling back to straight segments otherwise, and writes the result back
        to the dialog's raw map so resampling and rendering stay in sync.
        ``moving_index`` (the anchor being dragged) seeds each segment from its
        fixed endpoint so live re-snapping stays responsive.
        """
        curve_id = self.selected_curve_id
        anchors = self._curve_anchor_map().get(curve_id)
        dlg = getattr(self, "object_dialog", None)
        if not anchors or dlg is None:
            return
        if len(anchors) < 2:
            dlg.curve_raw_map[curve_id] = [list(p) for p in anchors]
            return
        dense = [list(anchors[0])]
        for i in range(len(anchors) - 1):
            # Seed the endpoint that is not the one being dragged.
            seed_a = i != moving_index
            dense.extend(self._snap_segment(anchors[i], anchors[i + 1], seed_a=seed_a)[1:])
        dlg.curve_raw_map[curve_id] = dense

    def _point_on_polyline_index(self, pos, polyline, threshold=DISTANCE_THRESHOLD):
        """Index i of a polyline segment (i, i+1) under screen ``pos``, or -1."""
        for i in range(len(polyline) - 1):
            a = [self._2canx(polyline[i][0]), self._2cany(polyline[i][1])]
            b = [self._2canx(polyline[i + 1][0]), self._2cany(polyline[i + 1][1])]
            if self._point_segment_distance(pos, a, b) <= threshold:
                return i
        return -1

    def _anchor_insert_index(self, dense, anchors, img_point):
        """Ordinal slot among ``anchors`` for a new point clicked on ``dense``.

        Anchors sit on the dense trace, so ordering by nearest dense vertex keeps
        the anchor list in curve order when a new one is inserted mid-curve.
        """

        def nearest(pt):
            best_i, best_d = 0, None
            for i, q in enumerate(dense):
                d = (q[0] - pt[0]) ** 2 + (q[1] - pt[1]) ** 2
                if best_d is None or d < best_d:
                    best_d, best_i = d, i
            return best_i

        click_at = nearest(img_point)
        return sum(1 for a in anchors if nearest(a) < click_at)

    def _insert_editpoint_near(self, pos):
        """Insert a new edit point where the user clicked on the selected curve.

        For a snap curve the click is tested against the *visible dense trace*
        (not the sparse anchor chord) and the new anchor is slotted into the
        anchor list by its position along that trace. For a hand-traced curve it
        falls back to the raw-segment hit-test. Returns the new point's index in
        the edit list, or -1 if the click missed the curve.
        """
        edit = self._selected_curve_raw()
        if not edit:
            return -1
        img_point = [self._2imgx(self.mouse_curr_x), self._2imgy(self.mouse_curr_y)]
        anchors = self._curve_anchor_map().get(self.selected_curve_id)
        if anchors:
            dense = self._curve_raw_map().get(self.selected_curve_id)
            if not dense or self._point_on_polyline_index(pos, dense) < 0:
                return -1
            idx = self._anchor_insert_index(dense, anchors, img_point)
            anchors.insert(idx, img_point)
            return idx
        seg_idx = self._curve_segment_within_threshold(pos)
        if seg_idx < 0:
            return -1
        edit.insert(seg_idx + 1, img_point)
        return seg_idx + 1

    def _show_curve_context_menu(self, global_pos):
        """Right-click menu in curve mode: delete a point and/or the curve."""
        from PyQt5.QtWidgets import QMenu

        curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
        target_id = self._curve_at_position(curr_pos) or self.selected_curve_id
        if target_id is None:
            return

        point_idx = self._curve_point_within_threshold(curr_pos) if target_id == self.selected_curve_id else -1
        menu = QMenu(self)
        del_point_action = menu.addAction(self.tr("Delete Point")) if point_idx >= 0 else None
        del_curve_action = menu.addAction(self.tr("Delete Curve"))
        action = menu.exec_(global_pos)
        if action is None:
            return
        if action is del_point_action:
            raw = self._selected_curve_raw()
            if raw is not None and len(raw) > 2:
                raw.pop(point_idx)
                self._resnap_selected_curve()
                self._notify_curve_edited()
        elif action is del_curve_action:
            if self.object_dialog is not None and hasattr(self.object_dialog, "delete_curve"):
                self.object_dialog.delete_curve(target_id)
        self.repaint()

    def _notify_curve_edited(self):
        """Tell the object dialog a curve's raw trace changed (refresh + persist)."""
        dlg = getattr(self, "object_dialog", None)
        if dlg is None:
            return
        if hasattr(dlg, "curve_trace_changed"):
            dlg.curve_trace_changed()
        elif hasattr(dlg, "show_curves"):
            dlg.show_curves()

    def _curve_point_within_threshold(self, pos, threshold=DISTANCE_THRESHOLD):
        """Index of the selected curve's raw point under ``pos`` (screen), or -1."""
        raw = self._selected_curve_raw()
        if not raw:
            return -1
        for i, pt in enumerate(raw):
            if self.get_distance(pos, [self._2canx(pt[0]), self._2cany(pt[1])]) <= threshold:
                return i
        return -1

    def _curve_segment_within_threshold(self, pos, threshold=DISTANCE_THRESHOLD):
        """Index i of the selected curve's segment (i, i+1) under ``pos``, or -1."""
        raw = self._selected_curve_raw()
        if not raw or len(raw) < 2:
            return -1
        for i in range(len(raw) - 1):
            a = [self._2canx(raw[i][0]), self._2cany(raw[i][1])]
            b = [self._2canx(raw[i + 1][0]), self._2cany(raw[i + 1][1])]
            if self._point_segment_distance(pos, a, b) <= threshold:
                return i
        return -1

    def _curve_at_position(self, pos, threshold=DISTANCE_THRESHOLD):
        """Id of a curve whose raw trace passes near ``pos`` (screen), or None."""
        raw_map = self._curve_raw_map()
        for curve in self._curve_config():
            raw = raw_map.get(curve.get("id"))
            if not raw:
                continue
            for pt in raw:
                if self.get_distance(pos, [self._2canx(pt[0]), self._2cany(pt[1])]) <= threshold:
                    return curve.get("id")
            for i in range(len(raw) - 1):
                a = [self._2canx(raw[i][0]), self._2cany(raw[i][1])]
                b = [self._2canx(raw[i + 1][0]), self._2cany(raw[i + 1][1])]
                if self._point_segment_distance(pos, a, b) <= threshold:
                    return curve.get("id")
        return None

    @staticmethod
    def _point_segment_distance(p, a, b):
        """Distance from screen point ``p`` to the segment a-b."""
        ax, ay = a
        bx, by = b
        px, py = p
        dx, dy = bx - ax, by - ay
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

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
        self._update_landmark_tooltip(curr_pos, me.globalPos())

        if self.pan_mode == MODE["PAN"]:
            self.temp_pan_x = int(self.mouse_curr_x - self.mouse_down_x)
            self.temp_pan_y = int(self.mouse_curr_y - self.mouse_down_y)

        elif self.edit_mode == MODE["EDIT_LANDMARK"]:
            near_idx = self.get_landmark_index_within_threshold(curr_pos, DISTANCE_THRESHOLD)
            if near_idx >= 0:
                self.set_mode(MODE["READY_MOVE_LANDMARK"])
                self.selected_landmark_index = near_idx
                self.hover_curve_id = None
            else:
                # Highlight a curve under the cursor (a click would select it).
                self.hover_curve_id = self._curve_at_position(curr_pos)

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

        elif self.edit_mode == MODE["EDIT_CURVE"]:
            self.hover_curve_id = self._curve_at_position(curr_pos)
            if self.selected_curve_id is not None:
                raw = self._selected_curve_raw()
                if raw is not None and self.moving_curve_point_index >= 0:
                    # Drag the grabbed point (an anchor for a snap curve). Re-snap
                    # live so the dense trace follows the anchor as it moves.
                    raw[self.moving_curve_point_index] = [
                        self._2imgx(self.mouse_curr_x),
                        self._2imgy(self.mouse_curr_y),
                    ]
                    self._resnap_selected_curve(moving_index=self.moving_curve_point_index)
                elif raw is not None:
                    # Hover highlight for the point under the cursor.
                    self.hover_curve_point_index = self._curve_point_within_threshold(curr_pos)
            elif self.livewire_enabled and self.current_curve_points:
                # Live preview: snap the last point to the cursor along edges.
                self.livewire_preview = self._livewire_segment(
                    self.current_curve_points[-1],
                    [self._2imgx(self.mouse_curr_x), self._2imgy(self.mouse_curr_y)],
                )

        self.repaint()
        QLabel.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        me = QMouseEvent(event)
        if me.button() == Qt.LeftButton:
            if self.edit_mode == MODE["EDIT_LANDMARK"]:
                if self.orig_pixmap is None:
                    return
                # A click near an existing curve selects it and switches to curve
                # mode, instead of placing a landmark.
                near_id = self._curve_at_position([self.mouse_curr_x, self.mouse_curr_y])
                if (
                    near_id is not None
                    and self.object_dialog is not None
                    and hasattr(self.object_dialog, "enter_curve_mode")
                ):
                    self.object_dialog.enter_curve_mode(near_id)
                    self.repaint()
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
            elif self.edit_mode == MODE["EDIT_CURVE"]:
                if self.orig_pixmap is None:
                    return
                curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
                # 1) Editing the selected curve: grab a point or insert one.
                if self.selected_curve_id is not None:
                    pt_idx = self._curve_point_within_threshold(curr_pos)
                    if pt_idx >= 0:
                        self.moving_curve_point_index = pt_idx
                        self.repaint()
                        return
                    ins_idx = self._insert_editpoint_near(curr_pos)
                    if ins_idx >= 0:
                        self.moving_curve_point_index = ins_idx
                        # For a snap curve the inserted point is a new anchor;
                        # re-snap so the dense trace runs through it (a following
                        # drag re-snaps live).
                        self._resnap_selected_curve()
                        self.repaint()
                        return
                # 2) A click near any curve selects it (unless mid-trace).
                if not self.current_curve_points:
                    near_id = self._curve_at_position(curr_pos)
                    if near_id is not None:
                        if self.object_dialog is not None and hasattr(self.object_dialog, "select_curve_row"):
                            self.object_dialog.select_curve_row(near_id)
                        else:
                            self.selected_curve_id = near_id
                        self.repaint()
                        return
                # 3) Otherwise, with no curve selected, add a point to the trace.
                if self.selected_curve_id is None:
                    img_x = self._2imgx(self.mouse_curr_x)
                    img_y = self._2imgy(self.mouse_curr_y)
                    if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                        return
                    if self.livewire_enabled:
                        # Snap from the last point to the click along the strongest
                        # edge, appending the intermediate points (skip index 0,
                        # which repeats the point already in the trace). Remember
                        # the click itself as an anchor so the curve stays
                        # editable by its clicks.
                        if self.current_curve_points:
                            segment = self._livewire_segment(self.current_curve_points[-1], [img_x, img_y])
                            self.current_curve_points.extend(segment[1:])
                        else:
                            self.current_curve_points.append([img_x, img_y])
                        self.current_curve_anchors.append([img_x, img_y])
                    else:
                        self.current_curve_points.append([img_x, img_y])
                    self.livewire_preview = []

        elif me.button() == Qt.RightButton:
            if self.edit_mode == MODE["EDIT_CURVE"]:
                if self.current_curve_points:
                    # Cancel the curve being traced.
                    self.current_curve_points = []
                    self.current_curve_anchors = []
                    self.livewire_preview = []
                elif self._curve_at_position([self.mouse_curr_x, self.mouse_curr_y]) is not None:
                    # Near a curve: context menu (delete point / curve).
                    self._show_curve_context_menu(me.globalPos())
                else:
                    # Empty space: right-drag pans, like the other modes.
                    self.pan_mode = MODE["PAN"]
                    self.mouse_down_x = me.x()
                    self.mouse_down_y = me.y()
            elif self.edit_mode == MODE["WIREFRAME"]:
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
            elif (
                self.edit_mode == MODE["EDIT_LANDMARK"]
                and self._curve_at_position([self.mouse_curr_x, self.mouse_curr_y]) is not None
            ):
                # Right-click a highlighted curve in landmark mode: offer to delete
                # it (no curve is selected here, so only "Delete Curve" shows).
                self._show_curve_context_menu(me.globalPos())
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
        elif self.edit_mode == MODE["EDIT_CURVE"] and self.moving_curve_point_index >= 0:
            # Finished dragging (or inserting) a curve point. For a snap curve the
            # dragged point is an anchor, so re-snap the dense trace to it.
            self.moving_curve_point_index = -1
            self._resnap_selected_curve()
            self._notify_curve_edited()

        self.repaint()
        return super().mouseReleaseEvent(ev)

    def _accept_current_curve(self):
        """Commit the in-progress trace as semi-landmarks (double-click / Enter).

        Returns True if a trace was accepted, so callers can swallow the event.
        """
        if self.edit_mode != MODE["EDIT_CURVE"] or self.selected_curve_id is not None:
            return False
        if self.object_dialog is None:
            return False
        points = self.current_curve_points
        anchors = self.current_curve_anchors
        self.current_curve_points = []
        self.current_curve_anchors = []
        self.livewire_preview = []
        if len(points) >= 2:
            self.object_dialog.finish_curve(points, anchors or None)
        self.repaint()
        return True

    def _cancel_current_curve(self):
        """Discard the in-progress trace (right-click / Esc). Returns True if any."""
        if self.edit_mode != MODE["EDIT_CURVE"] or not self.current_curve_points:
            return False
        self.current_curve_points = []
        self.current_curve_anchors = []
        self.livewire_preview = []
        self.repaint()
        return True

    def mouseDoubleClickEvent(self, event):
        # Finish tracing a curve: the double-click's first press already added the
        # end point, so commit the collected points as semi-landmarks.
        if self._accept_current_curve():
            return
        return super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        # In curve mode, Enter accepts the current trace and Esc cancels it,
        # mirroring double-click / right-click for keyboard users.
        if self.edit_mode == MODE["EDIT_CURVE"] and self.selected_curve_id is None:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if self._accept_current_curve():
                    return
            elif event.key() == Qt.Key_Escape:
                if self._cancel_current_curve():
                    return
        return super().keyPressEvent(event)

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
            longer_side = max(self.orig_pixmap.width(), self.orig_pixmap.height())
            if longer_side > 0 and self.image_canvas_ratio > 0:
                max_scale = MAX_SCALED_PIXMAP_DIM * self.image_canvas_ratio / longer_side
                # Keep the 0.1 rounding grid; never clamp below fit-to-canvas.
                max_scale = max(1.0, math.floor(max_scale * 10) / 10)
                if self.scale > max_scale:
                    self.scale = max_scale
            self.curr_pixmap = self._render_source().scaled(
                int(self.orig_pixmap.width() * self.scale / self.image_canvas_ratio),
                int(self.orig_pixmap.height() * self.scale / self.image_canvas_ratio),
                Qt.IgnoreAspectRatio,  # the target box already carries the source's aspect
                Qt.SmoothTransformation,
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
        landmark_names = self._landmark_names() if self.show_landmark_name else []
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
                painter.drawText(
                    int(self._2canx(landmark[0]) + 10),
                    int(self._2cany(landmark[1])) + 10,
                    self._landmark_label(idx, landmark_names),
                )

        # draw expected positions of the not-yet-placed landmarks (digitizing aid)
        if self.show_expected and self.object_dialog is not None:
            expected = getattr(self.object_dialog, "expected_landmark_list", None)
            if expected is not None:
                for idx in range(len(self.landmark_list), len(expected)):
                    lm = expected[idx]
                    if lm and lm[0] is not None and lm[1] is not None:
                        self.draw_estimated_landmark(painter, lm[0], lm[1], idx)

        # draw wireframe being edited
        if self.wire_start_index >= 0:
            painter.setPen(QPen(mu.as_qt_color(COLOR["WIREFRAME"]), 2))
            painter.setBrush(QBrush(mu.as_qt_color(COLOR["WIREFRAME"])))
            start_lm = self.landmark_list[self.wire_start_index]
            painter.drawLine(
                int(self._2canx(start_lm[0])), int(self._2cany(start_lm[1])), self.mouse_curr_x, self.mouse_curr_y
            )

        # draw each curve: its raw trace (polyline), the derived semi-landmarks
        # (labelled C<curve>-<semi-landmark> when indices are shown), and, for the
        # selected curve, editable point handles
        raw_map = self._curve_raw_map()
        if raw_map:
            semi_color = mu.as_qt_color(COLOR["SEMI_LANDMARK"])
            for num, curve in enumerate(self._curve_config(), start=1):
                raw = raw_map.get(curve.get("id"))
                if not raw:
                    continue
                canvas_pts = [(int(self._2canx(p[0])), int(self._2cany(p[1]))) for p in raw]
                if self.show_curve:
                    # Draw the selected curve's line thicker so it stands out.
                    line_width = 3 if curve.get("id") == self.selected_curve_id else 1
                    painter.setPen(QPen(mu.as_qt_color(COLOR["CURVE"]), line_width))
                    painter.setBrush(Qt.NoBrush)
                    for j in range(len(canvas_pts) - 1):
                        painter.drawLine(*canvas_pts[j], *canvas_pts[j + 1])
                if self.show_semi_landmark and len(raw) >= 2:
                    try:
                        semis = mu.resample_polyline(raw, curve.get("n", 0))
                    except ValueError:
                        semis = []
                    for i, pt in enumerate(semis, start=1):
                        sx, sy = int(self._2canx(pt[0])), int(self._2cany(pt[1]))
                        painter.setPen(QPen(semi_color, 2))
                        painter.setBrush(QBrush(semi_color))
                        painter.drawEllipse(sx - radius, sy - radius, radius * 2, radius * 2)
                        if self.show_index:
                            painter.drawText(sx + 6, sy, f"C{num}-{i}")
                if curve.get("id") in (self.selected_curve_id, self.hover_curve_id):
                    # Editable handles sit on the manipulated points -- the sparse
                    # snap anchors, or the raw points for a hand-traced curve --
                    # not every dense point of a snapped trace.
                    edit_pts = self._curve_editpoints(curve.get("id")) or raw
                    handle_pts = [(int(self._2canx(p[0])), int(self._2cany(p[1]))) for p in edit_pts]
                    for j, (cx, cy) in enumerate(handle_pts):
                        is_selected = curve.get("id") == self.selected_curve_id
                        if is_selected and j in (self.hover_curve_point_index, self.moving_curve_point_index):
                            painter.setPen(QPen(mu.as_qt_color(COLOR["SELECTED_LANDMARK"]), 2))
                            painter.setBrush(QBrush(mu.as_qt_color(COLOR["SELECTED_LANDMARK"])))
                        else:
                            painter.setPen(QPen(mu.as_qt_color(COLOR["CURVE"]), 2))
                            painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(cx - 3, cy - 3, 6, 6)

        # draw the curve currently being traced (EDIT_CURVE mode)
        if self.current_curve_points:
            painter.setPen(QPen(mu.as_qt_color(COLOR["CURVE"]), 2))
            painter.setBrush(QBrush(mu.as_qt_color(COLOR["CURVE"])))
            prev = None
            for pt in self.current_curve_points:
                cx, cy = int(self._2canx(pt[0])), int(self._2cany(pt[1]))
                painter.drawEllipse(cx - 2, cy - 2, 4, 4)
                if prev is not None:
                    painter.drawLine(prev[0], prev[1], cx, cy)
                prev = (cx, cy)
            if self.livewire_enabled and self.livewire_preview:
                # Snapped rubber-band: draw the live-wire path to the cursor.
                pen = QPen(mu.as_qt_color(COLOR["CURVE"]), 2, Qt.DashLine)
                painter.setPen(pen)
                pv_prev = prev
                for pt in self.livewire_preview:
                    px, py = int(self._2canx(pt[0])), int(self._2cany(pt[1]))
                    painter.drawLine(pv_prev[0], pv_prev[1], px, py)
                    pv_prev = (px, py)
            else:
                # Straight rubber-band segment from the last point to the cursor.
                painter.drawLine(prev[0], prev[1], self.mouse_curr_x, self.mouse_curr_y)

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
            self.curr_pixmap = self._render_source().scaled(
                int(self.orig_width * self.scale / self.image_canvas_ratio),
                int(self.orig_width * self.scale / self.image_canvas_ratio),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
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
        self.fullres_pixmap = None
        self._reset_livewire()
        self.curr_pixmap = self.orig_pixmap = QPixmap(file_path)
        if self.curr_pixmap.isNull():
            # QPixmap fails silently on a missing/corrupt/unsupported image,
            # leaving the viewer blank with no hint why. Log it at least.
            logger.warning(f"set_image: could not load image (blank pixmap): {file_path}")
        self.setPixmap(self.curr_pixmap)

    def set_fullres_source(self, file_path):
        """Render from a full-resolution image without changing coordinates.

        The working copy loaded via set_image stays the coordinate reference
        (orig_pixmap's dimensions keep driving image_canvas_ratio and all
        landmark math); only the source that curr_pixmap is resampled from
        changes, so zooming shows the original's detail. Pass None to go back
        to rendering from the working copy.
        """
        if file_path is None:
            self.fullres_pixmap = None
        else:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                logger.warning(f"set_fullres_source: could not load image: {file_path}")
                self.fullres_pixmap = None
            else:
                self.fullres_pixmap = pixmap
        self.calculate_resize()
        self.repaint()

    def _render_source(self):
        """Pixmap to resample curr_pixmap from (never defines coordinates)."""
        return self.fullres_pixmap if self.fullres_pixmap is not None else self.orig_pixmap

    def clear_object(self):
        # print("object view clear object")
        self.landmark_list = []
        self.edge_list = []
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.fullres_pixmap = None
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
