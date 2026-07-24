"""
Morphologika - Extracted from ModanComponents.py
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
        with open_text(self.filename) as f:
            morphologika_data = f.read()

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
                # A "[" with no following word characters (e.g. a bare "[") is a
                # malformed section header; skip it rather than crashing on
                # re.search(...).group() of None.
                section = re.search(r"(\w+)", line)
                if section is None:
                    continue
                dsl = section.group(0).lower()
                raw_data[dsl] = []
                continue
            else:
                if dsl == "":
                    # Data appearing before any [section] header is malformed;
                    # ignore it rather than raising KeyError on raw_data[""].
                    continue
                raw_data[dsl].append(line)
                if dsl == "individuals":
                    object_count = int(line)
                if dsl == "landmarks":
                    landmark_count = int(line)
                if dsl == "dimensions":
                    dimension = int(line)

        if object_count < 0 or landmark_count < 0:
            return False

        # Required sections must exist before we index them below, otherwise a
        # file missing [names] or [rawpoints] raises a bare KeyError.
        missing = [s for s in ("names", "rawpoints") if s not in raw_data]
        if missing:
            raise ValueError(f"Malformed Morphologika file: missing required section(s) {missing}: {self.filename}")

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
