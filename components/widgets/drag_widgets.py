"""
MdDrag, DragEventFilter, CustomDrag - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

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


logger = logging.getLogger(__name__)


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
