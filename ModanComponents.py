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


logger = logging.getLogger(__name__)

# Constants and mode definitions
# Import all components from modular structure
from components import (
    MISSING_COUNT_ROLE,
    NTS,
    TPS,
    X1Y1,
    AnalysisInfoWidget,
    CustomDrag,
    DatasetOpsViewer,
    DragEventFilter,
    MdDrag,
    MdLandmarkCountDelegate,
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
from MdConstants import (
    BASE_LANDMARK_RADIUS,
    COLOR,
    DATASET_MODE,
    DISTANCE_THRESHOLD,
    MODE,
    OBJECT_MODE,
    PAN_MODE,
    ROTATE_MODE,
    VIEW_MODE,
    WIREFRAME_MODE,
    ZOOM_MODE,
)

# Re-export for backward compatibility
__all__ = [
    # Constants
    "MODE",
    "BASE_LANDMARK_RADIUS",
    "DISTANCE_THRESHOLD",
    "OBJECT_MODE",
    "DATASET_MODE",
    "VIEW_MODE",
    "PAN_MODE",
    "ROTATE_MODE",
    "ZOOM_MODE",
    "WIREFRAME_MODE",
    "COLOR",
    "GLUT_AVAILABLE",
    "GLUT_INITIALIZED",
    "glut",
    # Viewers
    "ObjectViewer2D",
    "ObjectViewer3D",
    # Widgets
    "AnalysisInfoWidget",
    "DatasetOpsViewer",
    "MISSING_COUNT_ROLE",
    "MdLandmarkCountDelegate",
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
