"""
X1Y1 - Extracted from ModanComponents.py
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

from ._encoding import open_text

logger = logging.getLogger(__name__)


class X1Y1:
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
        with open_text(self.filename) as f:
            lines = f.readlines()
            dataset = {}
            landmark_count = 0
            data = []
            object_name_list = []
            objects = {}
            header = ""
            y_flip = 1.0
            if self.invertY:
                y_flip = -1.0

            if not lines:
                raise ValueError(f"Empty or unreadable X1Y1 file: {self.filename}")
            header = lines[0].strip().split("\t")
            xyz_header_list = header[1:]
            if len(xyz_header_list) < 3:
                raise ValueError(
                    f"Malformed X1Y1 header (need a name column plus at least 3 coordinate columns): {self.filename}"
                )
            if xyz_header_list[2].lower()[0] == "x":
                self.dimension = 2
            else:
                self.dimension = 3
            int(len(xyz_header_list) / self.dimension)
            lines = lines[1:]

            for line in lines:
                line = line.strip()
                if line == "":
                    continue
                if line.startswith("#"):
                    continue
                if line.startswith('"') or line.startswith("'"):
                    continue

                data = []
                fields_list = line.split("\t")
                object_name = fields_list[0]
                object_name_list.append(object_name)
                landmark_list = fields_list[1:]
                if len(landmark_list) > 0:
                    if self.dimension == 2:
                        for idx in range(0, len(landmark_list), 2):
                            data.append([float(landmark_list[idx]), y_flip * float(landmark_list[idx + 1])])
                    elif self.dimension == 3:
                        for idx in range(0, len(landmark_list), 3):
                            data.append(
                                [
                                    float(landmark_list[idx]),
                                    float(landmark_list[idx + 1]),
                                    float(landmark_list[idx + 2]),
                                ]
                            )
                objects[object_name] = data
            self.nobjects = len(object_name_list)
            self.nlandmarks = landmark_count
            self.landmark_data = objects
            self.object_name_list = object_name_list
            return dataset
