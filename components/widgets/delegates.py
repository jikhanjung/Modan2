"""
MdSequenceDelegate - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from PyQt5.QtGui import (
    QIntValidator,
)
from PyQt5.QtWidgets import (
    QLineEdit,
    QStyledItemDelegate,
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


logger = logging.getLogger(__name__)


class MdSequenceDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() == 1:  # Check if it's the sequence column
            editor = QLineEdit(parent)
            editor.setValidator(QIntValidator())
            return editor
        else:
            return super().createEditor(parent, option, index)
