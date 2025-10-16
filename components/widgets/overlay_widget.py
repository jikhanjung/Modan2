"""
ResizableOverlayWidget - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from PyQt5.QtCore import (
    QPoint,
    QRect,
    Qt,
)
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPen,
)
from PyQt5.QtWidgets import (
    QWidget,
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


class ResizableOverlayWidget(QWidget):
    """Custom widget with resize handles for overlay functionality"""

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window  # Store reference to main window for callbacks
        self.setMinimumSize(200, 150)
        self.resize_margin = 20  # Margin for resize area (increased for easier grabbing)
        self.header_height = 30  # Height of draggable header area
        self.close_button_size = 20  # Size of close button
        self.resizing = False
        self.dragging = False
        self.resize_direction = None
        self.setMouseTracking(True)  # Enable mouse tracking for cursor changes

        # Track which edges/corners are being resized
        self.RESIZE_NONE = 0
        self.RESIZE_TOP_LEFT = 1
        self.RESIZE_TOP_RIGHT = 2
        self.RESIZE_BOTTOM_LEFT = 3
        self.RESIZE_BOTTOM_RIGHT = 4

        # Track current corner position (default: bottom-right)
        self.current_corner = "bottom_right"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check resize first (higher priority)
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction != self.RESIZE_NONE:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_size = self.size()
                self.resize_start_geometry = self.geometry()
            elif self.is_header_area(event.pos()):
                # Start dragging only from header area if not resizing
                self.dragging = True
                self.drag_start_pos = event.globalPos()
                self.drag_start_geometry = self.geometry()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            self.handle_resize(event.globalPos())
        elif self.dragging:
            self.handle_dragging(event.globalPos())
        else:
            # Update cursor based on position - check close button first
            if self.is_close_button_area(event.pos()):
                self.setCursor(Qt.ArrowCursor)
            else:
                direction = self.get_resize_direction(event.pos())
                if direction != self.RESIZE_NONE:
                    self.update_cursor(direction)
                elif self.is_header_area(event.pos()):
                    self.setCursor(Qt.OpenHandCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dragging:
                # Snap to corner for easier positioning
                self.snap_to_corner()
                self.dragging = False
                # Notify main window that overlay was moved
                if self.main_window and hasattr(self.main_window, "on_overlay_moved"):
                    self.main_window.on_overlay_moved()
            self.resizing = False
            self.resize_direction = self.RESIZE_NONE
        super().mouseReleaseEvent(event)

    def is_header_area(self, pos):
        """Check if position is in draggable header area (excluding close button)"""
        if pos.y() > self.header_height:
            return False

        # Exclude close button area
        if self.is_close_button_area(pos):
            return False

        return True

    def is_close_button_area(self, pos):
        """Check if position is in close button area"""
        close_button_area = QRect(
            self.width() - self.close_button_size - 5,  # 5px margin from right edge
            5,  # 5px margin from top edge
            self.close_button_size,
            self.close_button_size,
        )
        return close_button_area.contains(pos)

    def get_resize_direction(self, pos):
        """Determine resize direction based on current corner position"""
        rect = self.rect()
        margin = self.resize_margin

        left_edge = pos.x() <= margin
        right_edge = pos.x() >= rect.width() - margin
        top_edge = pos.y() <= margin
        bottom_edge = pos.y() >= rect.height() - margin

        # Return appropriate resize direction based on current corner
        if self.current_corner == "top_left":
            if right_edge and bottom_edge:
                return self.RESIZE_BOTTOM_RIGHT
        elif self.current_corner == "top_right":
            if left_edge and bottom_edge:
                return self.RESIZE_BOTTOM_LEFT
        elif self.current_corner == "bottom_left":
            if right_edge and top_edge:
                return self.RESIZE_TOP_RIGHT
        elif self.current_corner == "bottom_right":
            if left_edge and top_edge:
                return self.RESIZE_TOP_LEFT

        return self.RESIZE_NONE

    def update_cursor(self, direction):
        """Update cursor based on resize direction"""
        if direction in [self.RESIZE_TOP_LEFT, self.RESIZE_BOTTOM_RIGHT]:
            self.setCursor(Qt.SizeFDiagCursor)
        elif direction in [self.RESIZE_TOP_RIGHT, self.RESIZE_BOTTOM_LEFT]:
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def handle_resize(self, global_pos):
        """Handle the resizing operation based on current corner position"""
        if self.resize_direction == self.RESIZE_NONE:
            return

        delta = global_pos - self.resize_start_pos
        original_geometry = self.resize_start_geometry

        if self.resize_direction == self.RESIZE_TOP_LEFT:
            # Resize from top-left corner
            new_width = max(self.minimumWidth(), original_geometry.width() - delta.x())
            new_height = max(self.minimumHeight(), original_geometry.height() - delta.y())
            new_x = original_geometry.x() + original_geometry.width() - new_width
            new_y = original_geometry.y() + original_geometry.height() - new_height
            self.setGeometry(new_x, new_y, new_width, new_height)

        elif self.resize_direction == self.RESIZE_TOP_RIGHT:
            # Resize from top-right corner
            new_width = max(self.minimumWidth(), original_geometry.width() + delta.x())
            new_height = max(self.minimumHeight(), original_geometry.height() - delta.y())
            new_x = original_geometry.x()
            new_y = original_geometry.y() + original_geometry.height() - new_height
            self.setGeometry(new_x, new_y, new_width, new_height)

        elif self.resize_direction == self.RESIZE_BOTTOM_LEFT:
            # Resize from bottom-left corner
            new_width = max(self.minimumWidth(), original_geometry.width() - delta.x())
            new_height = max(self.minimumHeight(), original_geometry.height() + delta.y())
            new_x = original_geometry.x() + original_geometry.width() - new_width
            new_y = original_geometry.y()
            self.setGeometry(new_x, new_y, new_width, new_height)

        elif self.resize_direction == self.RESIZE_BOTTOM_RIGHT:
            # Resize from bottom-right corner
            new_width = max(self.minimumWidth(), original_geometry.width() + delta.x())
            new_height = max(self.minimumSize().height(), original_geometry.height() + delta.y())
            new_x = original_geometry.x()
            new_y = original_geometry.y()
            self.setGeometry(new_x, new_y, new_width, new_height)

    def handle_dragging(self, global_pos):
        """Handle dragging of the overlay widget"""
        if not self.dragging:
            return

        delta = global_pos - self.drag_start_pos
        new_geometry = QRect(self.drag_start_geometry)
        new_geometry.translate(delta.x(), delta.y())

        # Move the widget to follow the mouse
        self.setGeometry(new_geometry)

    def snap_to_corner(self):
        """Snap the overlay to the nearest corner based on center position relative to parent center"""
        if not self.parent():
            return False

        parent_rect = self.parent().rect()
        current_rect = self.geometry()

        # Calculate corner positions
        corners = {
            "top_left": QPoint(0, 0),
            "top_right": QPoint(parent_rect.width() - current_rect.width(), 0),
            "bottom_left": QPoint(0, parent_rect.height() - current_rect.height()),
            "bottom_right": QPoint(
                parent_rect.width() - current_rect.width(), parent_rect.height() - current_rect.height()
            ),
        }

        # Get centers for comparison
        parent_center = parent_rect.center()
        current_center = current_rect.center()

        # Determine target corner based on which quadrant the center is in
        is_right = current_center.x() > parent_center.x()
        is_bottom = current_center.y() > parent_center.y()

        if is_right and is_bottom:
            target_corner = "bottom_right"
        elif is_right and not is_bottom:
            target_corner = "top_right"
        elif not is_right and is_bottom:
            target_corner = "bottom_left"
        else:
            target_corner = "top_left"

        # Snap to the determined corner
        self.current_corner = target_corner
        target_pos = corners[target_corner]
        self.move(target_pos)

        # Update parent to trigger resize handle repositioning if needed
        if hasattr(self.parent(), "update_overlay_position"):
            self.parent().update_overlay_position()
        return True

    def paintEvent(self, event):
        """Override paint event to draw background and border"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # Draw background
        painter.fillRect(rect, QColor(255, 255, 255))  # White background

        # Draw border
        painter.setPen(QPen(QColor(102, 102, 102), 2))  # Gray border, 2px thick
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)  # Adjust for border thickness

        # Don't call super() - we're handling everything ourselves
