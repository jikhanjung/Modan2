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

logger = logging.getLogger(__name__)


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
