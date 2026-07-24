"""
MdSequenceDelegate - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from PyQt5.QtGui import (
    QColor,
    QIntValidator,
    QPalette,
)
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
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


#: Colour of the missing-landmark count. Bright enough to read on the column's
#: grey (uneditable) background and on a selection highlight.
MISSING_COUNT_COLOR = QColor(200, 0, 0)


class MdLandmarkCountDelegate(QStyledItemDelegate):
    """Renders a landmark count as ``4 (1)``, the parenthesised part in red.

    The number itself counts *recorded* landmarks; the red suffix says how many
    positions are missing. The suffix is painted rather than folded into the
    display text so the cell's value stays an int and the column keeps sorting
    numerically.

    ``missing_count_role`` is passed in to avoid importing ``table_view`` here —
    that module already imports this one.
    """

    def __init__(self, missing_count_role, parent=None):
        super().__init__(parent)
        self._role = missing_count_role

    def _missing(self, index):
        try:
            return int(index.data(self._role) or 0)
        except (TypeError, ValueError):
            return 0

    def paint(self, painter, option, index):
        missing = self._missing(index)
        if missing <= 0:
            super().paint(painter, option, index)
            return

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        main_text = opt.text
        suffix = f" ({missing})"

        # Let the style draw the background/selection/focus, then take over the
        # text so the two halves can differ in colour.
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)

        painter.save()
        metrics = opt.fontMetrics
        main_width = metrics.horizontalAdvance(main_text)
        total_width = main_width + metrics.horizontalAdvance(suffix)

        rect = opt.rect
        # The column is centre-aligned; centre the pair, not just the number.
        x = rect.x() + max(0, (rect.width() - total_width) // 2)
        baseline = rect.y() + (rect.height() + metrics.ascent() - metrics.descent()) // 2

        selected = bool(opt.state & QStyle.State_Selected)
        painter.setPen(opt.palette.color(QPalette.HighlightedText if selected else QPalette.Text))
        painter.drawText(x, baseline, main_text)
        painter.setPen(MISSING_COUNT_COLOR)
        painter.drawText(x + main_width, baseline, suffix)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        missing = self._missing(index)
        if missing > 0:
            opt = QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            size.setWidth(size.width() + opt.fontMetrics.horizontalAdvance(f" ({missing})"))
        return size


class MdSequenceDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() == 1:  # Check if it's the sequence column
            editor = QLineEdit(parent)
            editor.setValidator(QIntValidator())
            return editor
        else:
            return super().createEditor(parent, option, index)
