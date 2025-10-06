"""
Morphologika - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas

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
import os
import re

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


class Morphologika:
    def __init__(self, filename, datasetname, invertY=False):
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
        f = open(self.filename)
        morphologika_data = f.read()
        f.close()

        object_count = -1
        landmark_count = -1
        data_lines = [l.strip() for l in morphologika_data.split("\n")]
        dsl = ""
        dimension = 2
        raw_data = {}
        for line in data_lines:
            line = line.strip()
            if line == "":
                continue
            if line[0] == "'":
                """comment"""
                continue
            elif line[0] == "[":
                dsl = re.search(r"(\w+)", line).group(0).lower()
                raw_data[dsl] = []
                continue
            else:
                raw_data[dsl].append(line)
                if dsl == "individuals":
                    object_count = int(line)
                if dsl == "landmarks":
                    landmark_count = int(line)
                if dsl == "dimensions":
                    dimension = int(line)

        if object_count < 0 or landmark_count < 0:
            return False

        self.raw_data = raw_data
        self.nlandmarks = landmark_count
        self.dimension = dimension
        self.object_name_list = self.raw_data["names"]
        self.nobjects = len(self.object_name_list)
        self.nobjects = object_count

        objects = {}
        for i, name in enumerate(self.object_name_list):
            begin = i * self.nlandmarks
            count = self.nlandmarks
            objects[name] = []
            for point in self.raw_data["rawpoints"][begin : begin + count]:
                coords = re.split(r"\s+", point)[:dimension]
                objects[name].append(coords)

        self.landmark_data = objects
        self.edge_list = []
        self.image_list = []
        self.polygon_list = []
        self.variablename_list = []
        self.property_list_list = []

        if self.dimension == 2 and self.invertY:
            for key in objects.keys():
                for idx in range(len(objects[key])):
                    objects[key][idx][1] = -1.0 * float(objects[key][idx][1])

        if "labels" in self.raw_data.keys():
            for line in self.raw_data["labels"]:
                labels = re.split(r"\s+", line)
                for label in labels:
                    self.variablename_list.append(label)

        if "labelvalues" in self.raw_data.keys():
            for line in self.raw_data["labelvalues"]:
                property_list = re.split(r"\s+", line)
                self.property_list_list.append(property_list)

        if "wireframe" in self.raw_data.keys():
            for line in self.raw_data["wireframe"]:
                edge = [int(v) for v in re.split(r"\s+", line)]
                edge.sort()
                self.edge_list.append(edge)

        if "polygons" in self.raw_data.keys():
            for line in self.raw_data["polygons"]:
                poly = [int(v) for v in re.split(r"\s+", line)]
                poly.sort()
                self.polygon_list.append(poly)

        if "images" in self.raw_data.keys():
            for idx, line in enumerate(self.raw_data["images"]):
                object_name = self.object_name_list[idx]
                self.object_images[object_name] = line

        if "pixelspermm" in self.raw_data.keys():
            for idx, line in enumerate(self.raw_data["pixelspermm"]):
                self.ppmm_list.append(line)

        self.edge_list.sort()
        self.polygon_list.sort()
        return
