"""
NTS - Extracted from ModanComponents.py
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
import re

from ._encoding import open_text

logger = logging.getLogger(__name__)


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

    def _parse_header(self, headerline):
        """Parse the NTS header line.

        Sets ``self.dimension`` and returns ``(total_object_count,
        variable_count, layout)``; ``layout`` records where the row / column
        names live.
        """
        total_object_count = int(headerline.group(3))
        variable_count = int(headerline.group(6))
        self.dimension = int(headerline.group(14))
        if headerline.group(13).lower() == "dim":
            self.dimension = int(headerline.group(14))

        row_flag = headerline.group(4).lower()
        layout = {
            "row_names_separate_line": row_flag == "l",
            "row_names_at_beginning": row_flag == "b",
            "row_names_at_ending": row_flag == "e",
            "column_names_exist": headerline.group(7).lower() == "l",
        }
        return total_object_count, variable_count, layout

    def _row_name(self, data_list, layout, row_names_list, index):
        """Take this row's object name per the header layout.

        Names given at the row's start/end are popped out of ``data_list`` so
        only coordinates remain. Falls back to a generated name when the file
        supplies fewer names than rows (rather than raising IndexError).
        """
        if layout["row_names_at_beginning"]:
            return data_list.pop(0)
        if layout["row_names_at_ending"]:
            return data_list.pop(-1)
        if index < len(row_names_list):
            return row_names_list[index]
        return f"{self.datasetname}_{index + 1}"

    def read(self):
        with open_text(self.filename) as f:
            nts_lines = f.readlines()

        dataset = {}
        total_object_count = -1
        landmark_count = 0
        objects = {}
        object_name_list = []
        row_names_list = []
        comments = ""
        layout = None  # set once the header line is seen
        row_names_read = False
        column_names_read = False

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
                total_object_count, variable_count, layout = self._parse_header(headerline)
                # Landmarks per object. This used a stale local `dimension` that
                # was never updated (only self.dimension was), so the condition
                # was always false and nlandmarks stayed 0 for every NTS file.
                if variable_count > 0 and self.dimension > 0:
                    landmark_count = int(variable_count / self.dimension)
                continue

            if layout is None:
                continue  # data before the header line; ignore it

            if layout["row_names_separate_line"] and not row_names_read:
                row_names_list = re.split(r"\s+", line)
                row_names_read = True
                continue

            if layout["column_names_exist"] and not column_names_read:
                column_names_read = True  # column names are parsed but unused
                continue

            data_list = re.split(r"\s+", line)
            row_name = self._row_name(data_list, layout, row_names_list, len(object_name_list))
            coords = [float(x) for x in data_list]
            objects[row_name] = [coords[i : i + self.dimension] for i in range(0, len(coords), self.dimension)]
            object_name_list.append(row_name)

        if total_object_count == 0 and landmark_count == 0:
            return None

        self.nobjects = len(object_name_list)
        self.nlandmarks = landmark_count
        self.landmark_data = objects
        self.object_name_list = object_name_list
        self.description = comments

        if self.dimension == 2 and self.invertY:
            for coords in objects.values():
                for point in coords:
                    point[1] = -1 * point[1]

        return dataset
