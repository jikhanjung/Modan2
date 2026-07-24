"""
MdTreeView - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtWidgets import (
    QTreeView,
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


class MdTreeView(QTreeView):
    """Custom TreeView that clears selection when clicking on empty space"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        """Override mouse press to clear selection on empty space click"""
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.pos())
            if not index.isValid():
                # Clicked on empty space, clear selection
                self.clearSelection()
                if self.selectionModel():
                    self.selectionModel().clearSelection()

        # Call parent implementation for normal behavior
        super().mousePressEvent(event)
