"""
NTS - Extracted from ModanComponents.py
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


class NTS:
    def __init__(self, filename, datasetname, invertY=False):
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

    def isNumber(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def read(self):
        with open(self.filename) as f:
            nts_lines = f.readlines()

            dataset = {}

            total_object_count = 0
            landmark_count = 0
            object_name_list = []
            objects = {}
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
                if line == "":
                    continue
                if line.startswith('"') or line.startswith("'"):
                    comments += line
                    continue
                #                          1    2     3   4    5     6    7   8    9    10   11   12   13    14
                headerline = re.search(
                    r"^(\d+)(\s+)(\d+)(\w*)(\s+)(\d+)(\w*)(\s+)(\d+)(\s+)(\d*)(\s*)(\w+)=(\d+)(.*)", line
                )
                if headerline is not None:
                    headerline.group(1)
                    total_object_count = int(headerline.group(3))
                    variable_count = int(headerline.group(6))
                    self.dimension = int(headerline.group(14))
                    if variable_count > 0 and dimension > 0:
                        landmark_count = int(float(variable_count) / float(dimension))
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

                if headerline_processed and row_names_exist_in_separate_line and not row_names_read:
                    row_names_list = re.split(r"\s+", line)
                    row_names_read = True
                    continue

                if headerline_processed and column_names_exist and not column_names_read:
                    re.split(r"\s+", line)
                    column_names_read = True
                    continue

                if headerline_processed:
                    data_list = re.split(r"\s+", line)
                    if row_names_exist_at_row_beginning:
                        row_name = data_list.pop(0)
                    elif row_names_exist_at_row_ending:
                        row_name = data_list.pop(-1)
                    elif len(row_names_list) > 0:
                        row_name = row_names_list[current_object_count]
                    else:
                        row_name = self.datasetname + "_" + str(current_object_count + 1)
                    data_list = [float(x) for x in data_list]
                    objects[row_name] = []
                    for idx in range(0, len(data_list), self.dimension):
                        objects[row_name].append(data_list[idx : idx + self.dimension])
                    object_name_list.append(row_name)
                    current_object_count += 1

            if total_object_count == 0 and landmark_count == 0:
                return None

            self.nobjects = len(object_name_list)
            self.nlandmarks = landmark_count
            self.landmark_data = objects
            self.object_name_list = object_name_list
            self.description = comments

            if self.dimension == 2 and self.invertY:
                for key in objects.keys():
                    for idx in range(len(objects[key])):
                        objects[key][idx][1] = -1 * objects[key][idx][1]

            return dataset
