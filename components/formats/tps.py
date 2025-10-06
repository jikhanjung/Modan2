"""
TPS - Extracted from ModanComponents.py
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
            currently_in_data_section = False
            object_id = ""
            object_image_path = ""
            object_comment_1 = ""
            object_comment_2 = ""

            for line in tps_lines:
                line = line.strip()
                if line == "":
                    continue
                if line.startswith("#"):
                    continue
                if line.startswith('"') or line.startswith("'"):
                    continue
                headerline = re.search(r"^\s*LM\s*=\s*(\d+)\s*(.*)", line, re.IGNORECASE)

                if headerline is not None:
                    if currently_in_data_section:
                        if len(data) > 0:
                            if object_id != "":
                                key = object_id
                            elif object_comment_1 != "":
                                key = object_comment_1
                                object_comment_1 = ""
                            else:
                                key = self.datasetname + "_" + str(object_count + 1)
                            objects[key] = data
                            object_name_list.append(key)
                            object_comment[key] = " ".join([object_comment_1, object_comment_2]).strip()
                            if object_image_path != "":
                                object_images[key] = object_image_path
                            # print("data:", data)
                            data = []
                            object_id = ""
                            object_comment_1 = ""
                            object_comment_2 = ""
                            object_image_path = ""
                        landmark_count, object_comment_1 = int(headerline.group(1)), headerline.group(2).strip()
                        object_count += 1
                    else:
                        currently_in_data_section = True
                        landmark_count, object_comment_1 = int(headerline.group(1)), headerline.group(2).strip()
                else:
                    dataline = re.search(r"^\s*(\w+)\s*=(.+)", line)
                    if dataline is None:
                        point = [float(x) for x in re.split(r"\s+", line)]
                        if len(point) > 2 and self.isNumber(point[2]):
                            threed += 1
                        else:
                            twod += 1
                        if len(point) > 1:
                            data.append(point)
                    elif dataline.group(1).lower() == "image":
                        object_image_path = dataline.group(2)
                    elif dataline.group(1).lower() == "comment":
                        object_comment_2 = dataline.group(2)
                    elif dataline.group(1).lower() == "id":
                        object_id = dataline.group(2)
                        pass

            if len(data) > 0:
                if object_id != "":
                    key = object_id
                elif object_comment_1 != "":
                    key = object_comment_1
                    object_comment_1 = ""
                else:
                    key = self.datasetname + "_" + str(object_count + 1)
                objects[key] = data
                object_name_list.append(key)
                object_comment[key] = " ".join([object_comment_1, object_comment_2]).strip()
                if object_image_path != "":
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
