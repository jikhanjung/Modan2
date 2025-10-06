"""
MdDrag, DragEventFilter, CustomDrag - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from PyQt5.QtCore import (
    QEvent,
    QObject,
    Qt,
)
from PyQt5.QtGui import (
    QCursor,
    QDrag,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
)

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


class MdDrag(QDrag):
    # shiftStateChanged = Signal(bool)
    def __init__(self, parent):
        super().__init__(parent)
        logger = logging.getLogger(__name__)
        logger.debug("md drag init")
        self.shift_pressed = False
        self.copy_cursor = QPixmap(QCursor(Qt.DragCopyCursor).pixmap())
        self.move_cursor = QPixmap(QCursor(Qt.DragMoveCursor).pixmap())

    def updateCursor(self, event):
        self.shift_pressed = bool(event.modifiers() & Qt.ShiftModifier)
        if self.shift_pressed:
            self.setDragCursor(self.copy_cursor, Qt.CopyAction)
        else:
            self.setDragCursor(self.move_cursor, Qt.MoveAction)

    def dragEnterEvent(self, event):
        logger = logging.getLogger(__name__)
        logger.debug("md drag dragEnterEvent")
        self.updateCursor(event)
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        logger = logging.getLogger(__name__)
        logger.debug(f"drag move event: {event.pos()}")
        self.updateCursor(event)
        super().dragMoveEvent(event)


class DragEventFilter(QObject):
    def __init__(self, drag_object):
        super().__init__()
        self.drag_object = drag_object

    def eventFilter(self, obj, event):
        if event.type() in [QEvent.KeyPress, QEvent.KeyRelease]:
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.ControlModifier:
                self.drag_object.setDragCursor(self.drag_object.copy_cursor.pixmap(), Qt.CopyAction)
                logger.debug("Set Copy Cursor")
            else:
                self.drag_object.setDragCursor(self.drag_object.move_cursor.pixmap(), Qt.MoveAction)
                logger.debug("Set Move Cursor")
        return False


class CustomDrag(QDrag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.copy_cursor = QCursor(Qt.DragCopyCursor)
        self.move_cursor = QCursor(Qt.DragMoveCursor)

    def exec_(self, supportedActions, defaultAction=Qt.IgnoreAction):
        event_filter = DragEventFilter(self)
        QApplication.instance().installEventFilter(event_filter)

        # Set initial cursor
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ControlModifier:
            self.setDragCursor(self.copy_cursor.pixmap(), Qt.CopyAction)
        else:
            self.setDragCursor(self.move_cursor.pixmap(), Qt.MoveAction)

        result = super().exec_(supportedActions, defaultAction)

        QApplication.instance().removeEventFilter(event_filter)
        return result
