"""
TPS - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

# GLUT import conditional - causes crashes on Windows builds
GLUT_AVAILABLE = False
GLUT_INITIALIZED = False
glut = None

try:
    from OpenGL import GLUT as glut  # type: ignore[no-redef]

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
import os
import re

from ._encoding import open_text

logger = logging.getLogger(__name__)


class _TPSObjectState:
    """Accumulation state for the TPS object currently being read.

    A TPS object is a ``LM=<n>`` header, its coordinate lines, optional
    ``KEY=VALUE`` lines (ID/IMAGE/COMMENT), and optionally ``CURVES=<k>`` then
    k x (``POINTS=<m>`` + m coordinate lines). Holding that in one object keeps
    the line loop readable and lets the per-line handlers be separate methods.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.data = []
        self.object_id = ""
        self.image_path = ""
        self.comment_1 = ""
        self.comment_2 = ""
        self.curves = []
        self.current_curve = []
        self.points_remaining = 0
        self.reading_curves = False


class TPS:
    def __init__(self, filename, datasetname, invertY=False):
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
        # Per-object semi-landmark curves parsed from CURVES=/POINTS= blocks:
        # object key -> list of curves, each a list of [x, y(, z)] points. Empty
        # for the common landmark-only TPS file.
        self.curve_data = {}
        self.invertY = invertY
        self.read()

    def isNumber(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _store_object(self, state, object_count):
        """Store the accumulated object into the result collections.

        Extracted so the two flush points -- on a new ``LM=`` header and at
        end-of-file -- share one implementation instead of duplicating the
        key-selection + storage logic.
        """
        comment_1 = state.comment_1
        if state.object_id != "":
            key = state.object_id
        elif comment_1 != "":
            key = comment_1
            comment_1 = ""  # used as the name; don't repeat it in the comment
        else:
            key = self.datasetname + "_" + str(object_count + 1)
        self.landmark_data[key] = state.data
        self.object_name_list.append(key)
        self.object_comment[key] = " ".join([comment_1, state.comment_2]).strip()
        if state.image_path != "":
            self.object_images[key] = state.image_path
        if state.curves:
            self.curve_data[key] = state.curves

    @staticmethod
    def _apply_keyword(state, key, value):
        """Apply one ``KEY=VALUE`` line to the object being accumulated."""
        key = key.lower()
        if key == "image":
            state.image_path = value
        elif key == "comment":
            state.comment_2 = value
        elif key == "id":
            state.object_id = value
        elif key == "curves":
            state.reading_curves = True
        elif key == "points":
            state.points_remaining = int(value)
            state.current_curve = []

    @staticmethod
    def _apply_coordinates(state, point):
        """Route a coordinate line to the curve being read, or to the landmarks.

        Curve coordinate lines must not land in ``data`` -- that would corrupt
        the landmark list.
        """
        if state.reading_curves and state.points_remaining > 0:
            state.current_curve.append(point)
            state.points_remaining -= 1
            if state.points_remaining == 0:
                state.curves.append(state.current_curve)
                state.current_curve = []
        elif len(point) > 1:
            state.data.append(point)

    def read(self):
        with open_text(self.filename) as f:
            tps_lines = f.readlines()

        dataset = {}
        object_count = 0
        landmark_count = 0
        threed = 0
        twod = 0
        self.landmark_data = {}
        self.object_name_list = []
        self.object_comment = {}
        self.object_images = {}
        self.curve_data = {}
        currently_in_data_section = False
        state = _TPSObjectState()

        for line in tps_lines:
            line = line.strip()
            if line == "" or line.startswith(("#", '"', "'")):
                continue

            headerline = re.search(r"^\s*LM\s*=\s*(\d+)\s*(.*)", line, re.IGNORECASE)
            if headerline is not None:
                if currently_in_data_section:
                    if len(state.data) > 0:
                        self._store_object(state, object_count)
                        state.reset()
                    object_count += 1
                currently_in_data_section = True
                landmark_count = int(headerline.group(1))
                state.comment_1 = headerline.group(2).strip()
                continue

            dataline = re.search(r"^\s*(\w+)\s*=(.+)", line)
            if dataline is None:
                point = [float(x) for x in re.split(r"\s+", line)]
                if len(point) > 2 and self.isNumber(point[2]):
                    threed += 1
                else:
                    twod += 1
                self._apply_coordinates(state, point)
            else:
                self._apply_keyword(state, dataline.group(1), dataline.group(2))

        # An empty / non-TPS file (no LM header, no landmarks): discard before
        # storing anything, matching the pre-refactor behavior.
        if object_count == 0 and landmark_count == 0:
            return None

        if len(state.data) > 0:
            self._store_object(state, object_count)

        self.dimension = 3 if threed > twod else 2

        if self.dimension == 2 and self.invertY:
            for coords in self.landmark_data.values():
                for point in coords:
                    point[1] = -1 * point[1]
            for curve in (c for curves in self.curve_data.values() for c in curves):
                for point in curve:
                    point[1] = -1 * point[1]

        self.nobjects = len(self.object_name_list)
        self.nlandmarks = landmark_count
        return dataset
