"""
ModanComponents - Modular refactoring

This file now imports from the components/ package and re-exports everything
for backward compatibility. All actual implementations have been moved to
components/ subdirectories.

Original file: 4,852 lines
Refactored structure:
  - components/viewers/: 2D and 3D object viewers (2,517 lines)
  - components/widgets/: Custom PyQt5 widgets (1,734 lines)
  - components/formats/: File format handlers (462 lines)
  - Shared imports and constants: 179 lines

For new code, prefer importing from components/ directly:
  from components.viewers import ObjectViewer2D
  from components.widgets import MdTableView
  from components.formats import TPS

For backward compatibility, old imports still work:
  from ModanComponents import ObjectViewer2D  # Still works
"""

# Import all shared modules and initialize GLUT (needed by components)
import logging
import sys

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

# Constants and mode definitions
from MdConstants import MODE

MODE_EXPLORATION = 0
MODE_REGRESSION = 1
MODE_GROWTH_TRAJECTORY = 2
MODE_AVERAGE = 3
MODE_COMPARISON = 4
MODE_COMPARISON2 = 5

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

# Import all components from modular structure
from components import (
    NTS,
    TPS,
    X1Y1,
    AnalysisInfoWidget,
    CustomDrag,
    DatasetOpsViewer,
    DragEventFilter,
    MdDrag,
    MdSequenceDelegate,
    MdTableModel,
    MdTableView,
    MdTreeView,
    Morphologika,
    ObjectViewer2D,
    ObjectViewer3D,
    PicButton,
    ResizableOverlayWidget,
    ShapePreference,
)

# Re-export for backward compatibility
__all__ = [
    # Constants
    "MODE",
    "MODE_EXPLORATION",
    "MODE_REGRESSION",
    "MODE_GROWTH_TRAJECTORY",
    "MODE_AVERAGE",
    "MODE_COMPARISON",
    "MODE_COMPARISON2",
    "BASE_LANDMARK_RADIUS",
    "DISTANCE_THRESHOLD",
    "CENTROID_SIZE_VALUE",
    "CENTROID_SIZE_TEXT",
    "OBJECT_MODE",
    "DATASET_MODE",
    "VIEW_MODE",
    "PAN_MODE",
    "ROTATE_MODE",
    "ZOOM_MODE",
    "LANDMARK_MODE",
    "WIREFRAME_MODE",
    "COLOR",
    "ICON",
    "NEWLINE",
    "GLUT_AVAILABLE",
    "GLUT_INITIALIZED",
    "glut",
    # Viewers
    "ObjectViewer2D",
    "ObjectViewer3D",
    # Widgets
    "AnalysisInfoWidget",
    "DatasetOpsViewer",
    "MdSequenceDelegate",
    "CustomDrag",
    "DragEventFilter",
    "MdDrag",
    "PicButton",
    "ResizableOverlayWidget",
    "ShapePreference",
    "MdTableModel",
    "MdTableView",
    "MdTreeView",
    # Formats
    "Morphologika",
    "NTS",
    "TPS",
    "X1Y1",
]
