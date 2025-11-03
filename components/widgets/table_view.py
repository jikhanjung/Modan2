"""
MdTableView, MdTableModel - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from PyQt5.QtCore import (
    QAbstractTableModel,
    QItemSelectionModel,
    QModelIndex,
    QRect,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QColor,
    QKeySequence,
    QPainter,
    QPen,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QInputDialog,
    QMenu,
    QShortcut,
    QTableView,
)

from MdModel import MdObject
from .drag_widgets import CustomDrag

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


class MdTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.verticalHeader().hide()
        self.sort_later = False
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Store the currently selected object row for custom drawing
        self.selected_object_row = -1

        self.copy_action = QAction(self.tr("Copy\tCtrl+C"), self)
        self.copy_action.triggered.connect(self.copy_selected_data)
        copy_shortcut = QShortcut(QKeySequence.Copy, self)
        copy_shortcut.activated.connect(self.copy_action.trigger)  # Connect to the action
        self.paste_action = QAction(self.tr("Paste\tCtrl+V"), self)
        self.paste_action.triggered.connect(self.paste_data)
        paste_shortcut = QShortcut(QKeySequence.Paste, self)
        paste_shortcut.activated.connect(self.paste_action.trigger)
        self.fill_sequence_action = QAction(self.tr("Fill sequence"), self)
        self.fill_sequence_action.triggered.connect(self.fill_sequence)
        logger = logging.getLogger(__name__)
        logger.debug("Fill sequence action created and connected")
        self.fill_action = QAction(self.tr("Fill value"), self)
        self.fill_action.triggered.connect(self.fill_value)
        self.clear_cells_action = QAction(self.tr("Clear"), self)
        self.clear_cells_action.triggered.connect(self.clear_selected_cells)
        self.edit_object_action = QAction(self.tr("Edit object"), self)
        self.edit_object_action.triggered.connect(self.edit_selected_object)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.selection_mode = "Cells"
        self.drag_start_position = None
        self.is_dragging = False
        self.drag_message_shown = False  # Flag to show status message only once

    def set_cells_selection_mode(self):
        self.selection_mode = "Cells"
        self.setDragEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)

    def set_rows_selection_mode(self):
        self.selection_mode = "Rows"
        self.setDragEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.drag_message_shown = False  # Reset flag on new press
            index = self.indexAt(event.pos())
            self.was_cell_selected = index in self.selectionModel().selectedIndexes()

            if self.selection_mode == "Rows" and self.was_cell_selected:
                self.startDrag(Qt.CopyAction)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            if event.modifiers() & Qt.ShiftModifier:
                QApplication.setOverrideCursor(Qt.DragCopyCursor)  # Copy cursor
            else:
                QApplication.setOverrideCursor(Qt.ClosedHandCursor)  # Move cursor (or Qt.SizeAllCursor)

        if self.selection_mode != "Rows":
            # Check if user is trying to drag in Cells mode
            if (event.buttons() & Qt.LeftButton) and self.drag_start_position is not None:
                if (event.pos() - self.drag_start_position).manhattanLength() >= QApplication.startDragDistance():
                    # User is trying to drag in cell mode - show message once
                    if not self.drag_message_shown:
                        self.show_status_message(
                            self.tr("Please switch to Row Selection mode to drag objects between datasets")
                        )
                        self.drag_message_shown = True
            super().mouseMoveEvent(event)
            return

        if not (event.buttons() & Qt.LeftButton):
            return

        if self.selection_mode == "Rows" and not self.was_cell_selected:
            self.drag_start_position = event.pos()
            super().mouseMoveEvent(event)
            return

        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        table_rect = self.viewport().rect()
        if not table_rect.contains(event.pos()):
            logger = logging.getLogger(__name__)
            logger.debug("outside table, start drag")
            self.is_dragging = True
            self.startDrag()
        else:
            super().mouseMoveEvent(event)

    def startDrag(self, supportedActions=Qt.CopyAction):
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            return
        mimeData = self.model().mimeData(indexes)
        if not mimeData:
            return
        drag = CustomDrag(self)
        drag.setMimeData(mimeData)

        # Set initial cursor based on current Shift key state
        Qt.CopyAction if QApplication.keyboardModifiers() & Qt.ShiftModifier else Qt.MoveAction
        drag.exec_(Qt.CopyAction | Qt.MoveAction)
        self.is_dragging = False

        # Restore cursor after drag ends
        while QApplication.overrideCursor():
            QApplication.restoreOverrideCursor()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_dragging:
                # Select the row if a drag operation was started
                row = self.rowAt(event.pos().y())
                self.selectionModel().select(
                    self.model().index(row, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows
                )
                self.is_dragging = False

                # Restore cursor after drag ends
                while QApplication.overrideCursor():
                    QApplication.restoreOverrideCursor()
            else:
                super().mouseReleaseEvent(event)

    def show_context_menu(self, pos):
        logger = logging.getLogger(__name__)
        index = self.indexAt(pos)  # Get the index of the clicked cell
        column = index.column()  # Get the column index

        # Get column header text
        column_header = ""
        if self.model() and column >= 0:
            column_header = self.model().headerData(column, Qt.Horizontal, Qt.DisplayRole)
            if column_header is None:
                column_header = ""

        logger.debug(
            f"Context menu requested at pos: {pos}, index: {index}, column: {column}, header: '{column_header}'"
        )

        selected_indices = self.selectionModel().selectedIndexes()
        logger.debug(f"Selected indices: {len(selected_indices)} items")

        # Check if this is a read-only column (name, count, csize)
        readonly_columns = ["name", "count", "csize"]
        column_header_lower = str(column_header).lower().strip()
        is_readonly_column = column_header_lower in readonly_columns

        logger.debug(
            f"Column '{column_header}' (normalized: '{column_header_lower}') is read-only: {is_readonly_column}"
        )

        menu = QMenu(self)

        # Add Edit object option at the top if a row is selected
        if selected_indices:
            menu.addAction(self.edit_object_action)
            menu.addSeparator()

        menu.addAction(self.copy_action)

        # Only add paste and other actions if not a read-only column
        if not is_readonly_column:
            menu.addAction(self.paste_action)

        # For read-only columns, only show copy
        if not is_readonly_column:
            # Only show Fill Sequence if all selected cells are in column 1 (sequence column)
            show_fill_sequence = False
            if selected_indices:
                # Check if all selected cells are in column 1
                selected_columns = {idx.column() for idx in selected_indices}
                if len(selected_columns) == 1 and 1 in selected_columns:
                    show_fill_sequence = True
                    logger.debug(f"All {len(selected_indices)} selected cells are in sequence column (column 1)")
                else:
                    logger.debug(f"Selected cells span multiple columns {selected_columns} or not in sequence column")
            elif column == 1:
                # No selection, but clicked on sequence column
                show_fill_sequence = True
                logger.debug("Clicked on sequence column, enabling Fill sequence")

            if show_fill_sequence:
                menu.addAction(self.fill_sequence_action)
                logger.debug("Added Fill sequence action")
            else:
                logger.debug("Fill sequence not available (only works when sequence column cells are selected)")

            menu.addAction(self.fill_action)
            menu.addAction(self.clear_cells_action)
        else:
            logger.debug(f"Read-only column '{column_header}': only showing copy action")

        actions_list = ["Copy"]
        if not is_readonly_column:
            actions_list.append("Paste")
            if "show_fill_sequence" in locals() and show_fill_sequence:
                actions_list.append("Fill sequence")
            actions_list.extend(["Fill value", "Clear"])

        logger.debug(f"Context menu showing with actions: {', '.join(actions_list)}")
        logger.info(
            f"Context menu for column '{column_header}' ({'read-only' if is_readonly_column else 'editable'}): {', '.join(actions_list)}"
        )

        menu.exec_(self.mapToGlobal(pos))

    def fill_value(self):
        # print("fill value")
        selected_indices = self.selectionModel().selectedIndexes()
        if len(selected_indices) == 0:
            return
        # get the first cell
        first_index = selected_indices[0]
        value = str(self.model().data(first_index, Qt.DisplayRole))
        # get user input
        value, ok = QInputDialog.getText(self, "Fill Values", "Enter value", text=value)
        if not ok:
            return
        # fill the values
        for index in selected_indices:
            self.model().setData(index, value, Qt.EditRole)

    def fill_sequence(self):
        logger = logging.getLogger(__name__)
        logger.info("Fill sequence action triggered")

        selected_cells = self.selectionModel().selectedIndexes()
        logger.debug(f"Selected cells: {len(selected_cells)}")

        if len(selected_cells) == 0:
            logger.warning("No cells selected for fill sequence")
            return
        selected_cells.sort(key=lambda x: (x.row(), x.column()))
        # make sure all the cells are in the column 1
        # get column number of all the cells
        column_numbers = [cell.column() for cell in selected_cells]
        logger.debug(f"Column numbers: {column_numbers}")

        if len(set(column_numbers)) > 1:
            logger.warning("Multiple columns selected, fill sequence only works on single column")
            return

        if column_numbers[0] != 1:
            logger.warning(
                f"Fill sequence only works on column 1 (sequence column), selected column: {column_numbers[0]}"
            )
            return

        # get the first cell
        first_cell = selected_cells[0]
        first_row = first_cell.row()
        column_0_index = self.model().index(first_row, 0)
        self.model().data(column_0_index, Qt.DisplayRole)
        sequence = self.model().data(first_cell, Qt.DisplayRole)
        try:
            sequence = int(sequence)
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not convert sequence value '{sequence}' to int: {e}. Using default value 1")
            sequence = 1
        # get user input
        logger.debug(f"Showing input dialog for starting sequence, current value: {sequence}")
        sequence, ok = QInputDialog.getInt(self, "Fill Sequence", "Enter starting sequence number", sequence)
        if not ok:
            logger.info("User cancelled starting sequence input")
            return

        logger.debug(f"User entered starting sequence: {sequence}")
        # get increment
        increment, ok = QInputDialog.getInt(self, "Fill Sequence", "Enter increment", 1)
        if not ok:
            logger.info("User cancelled increment input")
            return

        logger.debug(f"User entered increment: {increment}")
        # fill the sequence
        logger.info(
            f"Filling sequence for {len(selected_cells)} cells, starting at {sequence} with increment {increment}"
        )

        for _i, cell in enumerate(selected_cells):
            row = cell.row()
            index = self.model().index(row, 1)
            logger.debug(f"Setting row {row}, column 1 to value {sequence}")

            result = self.model().setData(index, sequence, Qt.EditRole)
            if not result:
                logger.error(f"Failed to set data at row {row}, column 1")

            sequence += increment

        logger.info("Fill sequence completed successfully")

    def paste_data(self):
        current_index = self.currentIndex()
        if not current_index.isValid():
            return
        text = QApplication.clipboard().text()
        rows = text.split("\n")
        for row, row_text in enumerate(rows):
            columns = row_text.split("\t")
            for col, text in enumerate(columns):
                index = self.model().index(current_index.row() + row, current_index.column() + col)
                self.model().setData(index, text, Qt.EditRole)

    def copy_selected_data(self):
        selected_indexes = self.selectionModel().selectedIndexes()
        if selected_indexes:
            all_data = []
            data_row = []
            prev_index = None
            for index in selected_indexes:
                if prev_index is not None and index.row() != prev_index.row():
                    all_data.append("\t".join(data_row))
                    data_row = []
                data_row.append(str(self.model().data(index, Qt.DisplayRole)))
                prev_index = index
            all_data.append("\t".join(data_row))
            text = "\n".join(all_data)  # Tab-separated for multiple cells
            QApplication.clipboard().setText(text)

    def defer_sort(self, topLeft, bottomRight, roles):
        # Only defer if the sequence column was edited
        if topLeft.column() == 1:
            self.sort_later = True

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            # print("key return or enter")
            if not self.isPersistentEditorOpen(self.currentIndex()):
                self.edit(self.currentIndex())
        elif event.key() in [Qt.Key_Up, Qt.Key_Down]:
            # print("key up, key down")
            # Handle up/down arrow keys directly (e.g., move selection)
            current_index = self.currentIndex()
            new_row = current_index.row() + (-1 if event.key() == Qt.Key_Up else 1)
            new_index = self.model().index(new_row, current_index.column())
            if new_index.isValid():
                self.setCurrentIndex(new_index)
        elif event.key() == Qt.Key_Delete:  # Check if Delete key is pressed
            self.clear_selected_cells()
        else:
            super().keyPressEvent(event)

    def clear_selected_cells(self):
        indexes = self.selectionModel().selectedIndexes()
        if indexes:
            for index in indexes:
                # get source model
                source_model = self.model().sourceModel()
                if index.column() not in source_model._uneditable_columns:
                    self.model().setData(index, "", Qt.EditRole)  # Set data to empty string

    def edit_selected_object(self):
        """Trigger the main window's edit object action"""
        # Find the parent MainWindow and trigger its edit object action
        parent = self.parent()
        while parent and not hasattr(parent, "actionEditObject"):
            parent = parent.parent()

        if parent and hasattr(parent, "actionEditObject"):
            parent.actionEditObject.trigger()

    def setSelectedObjectRow(self, row):
        """Set the currently selected object row for highlighting"""
        if self.selected_object_row != row:
            self.selected_object_row = row
            self.viewport().update()  # Trigger repaint

    def paintEvent(self, event):
        """Override paint event to draw row border for selected object"""
        super().paintEvent(event)

        if self.selected_object_row >= 0 and self.model():
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.Antialiasing)

            # Get the row geometry
            row_rect = QRect()
            for col in range(self.model().columnCount()):
                if not self.isColumnHidden(col):
                    cell_rect = self.visualRect(self.model().index(self.selected_object_row, col))
                    if row_rect.isNull():
                        row_rect = cell_rect
                    else:
                        row_rect = row_rect.united(cell_rect)

            if not row_rect.isNull():
                # Draw the border around the entire row
                painter.setPen(QPen(QColor(0, 120, 212), 3))  # Blue border, 3px thick
                painter.drawRect(row_rect.adjusted(1, 1, -1, -1))

        painter.end() if "painter" in locals() else None

    def isPersistentEditorOpen(self, index):
        return self.indexWidget(index) is not None

    def show_status_message(self, message, timeout=3000):
        """Show a message in the main window's status bar"""
        # Find the main window by traversing up the parent hierarchy
        parent = self.parent()
        while parent and not hasattr(parent, "statusBar"):
            parent = parent.parent()

        if parent and hasattr(parent, "statusBar"):
            parent.statusBar().showMessage(message, timeout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        header = self.horizontalHeader()
        total_width = self.viewport().width()
        column_count = self.model().columnCount()
        self.setColumnHidden(0, True)

        # Define your desired column widths
        default_width = 60
        fixed_widths = {
            0: 50,  # First column 100 pixels
            1: 50,  # First column 100 pixels
            2: 300,  # Third column 150 pixels
        }

        # Calculate remaining width for flexible columns
        remaining_width = total_width - sum(fixed_widths.values())
        flexible_columns = column_count - len(fixed_widths)
        flexible_width = remaining_width // flexible_columns if flexible_columns > 0 else 0
        if flexible_width < default_width:
            flexible_width = default_width

        for i in range(column_count):
            if i in fixed_widths:
                header.resizeSection(i, fixed_widths[i])
            else:
                header.resizeSection(i, flexible_width)

        # Calculate maximum content width for each column
        content_widths = [0] * column_count
        for row in range(self.model().rowCount()):
            for col in range(column_count):
                index = self.model().index(row, col)
                text = str(self.model().data(index, Qt.DisplayRole))
                text_width = self.fontMetrics().horizontalAdvance(text)
                content_widths[col] = max(content_widths[col], text_width)

        # Adjust column widths based on content and fixed widths
        for i in range(column_count):
            if i in fixed_widths:
                header.resizeSection(i, fixed_widths[i])
            else:
                # Ensure a minimum width for flexible columns
                width = max(flexible_width, content_widths[i] + 20)  # Add some padding
                header.resizeSection(i, width)


class MdTableModel(QAbstractTableModel):
    dataChangedCustomSignal = pyqtSignal()

    def __init__(self, data=None):
        super().__init__()
        self._data = data or []  # Initialize with provided data or an empty list
        self._vheader_data = []
        self._hheader_data = []
        self._uneditable_columns = [0, 2, 3, 4]

    def set_columns_uneditable(self, columns):
        self._uneditable_columns = columns

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0]) if self._data else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        d = self._data[index.row()][index.column()]
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if isinstance(d, str):
                return d  # self._data[index.row()][index.column()]
            elif isinstance(d, list):
                return " ".join(d)
            elif isinstance(d, dict) and "value" in d:
                return d["value"]
        if role == Qt.BackgroundRole:
            # if d is str or list, return default color
            if index.column() in self._uneditable_columns:
                return QColor(240, 240, 240)
            if isinstance(d, (str, list)):
                return None
            elif isinstance(d, dict) and d.get("changed", False):
                return QColor("yellow")
        if role == Qt.ToolTipRole:
            return f"Tooltip for cell ({index.row()}, {index.column()})"
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter | Qt.AlignVCenter
        return None

    def setData(self, index, value, role=Qt.EditRole):
        old_data = self._data[index.row()][index.column()]
        if isinstance(old_data, dict) and old_data.get("value", None):
            old_data = old_data["value"]
        if str(value) == str(old_data):
            return False

        if not index.isValid() or role != Qt.EditRole:
            return False
        if index.row() >= len(self._data) or index.column() >= len(self._data[0]):
            return False

        try:
            new_value = int(value)
        except ValueError:
            try:
                new_value = float(value)
            except ValueError:
                new_value = str(value)

        self._data[index.row()][index.column()] = {"value": new_value, "changed": True}
        self.dataChanged.emit(index, index, [role, Qt.BackgroundRole])
        self.dataChangedCustomSignal.emit()
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() in self._uneditable_columns:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return super().flags(index) | Qt.ItemIsEditable

    def resetColors(self):
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                d = self._data[row][column]
                if isinstance(d, dict) and d.get("changed", False):
                    d["changed"] = False
        self.dataChanged.emit(
            self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1), [Qt.BackgroundRole]
        )

    def load_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                # Return the header text for the given horizontal section
                return f"{self._hheader_data[section]}"
                # return ""
            elif orientation == Qt.Vertical:
                # Return the header text for the given vertical section
                if len(self._vheader_data) == 0:
                    return f"{section + 1}"
                else:
                    return f"{self._vheader_data[section]}"
        if role == Qt.ToolTipRole and orientation == Qt.Vertical:
            return ""

    def setVerticalHeader(self, header_data):
        self._vheader_data = header_data

    def setHorizontalHeader(self, header_data):
        self._hheader_data = header_data
        # print("header_data:", header_data)

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        try:  # Attempt to sort numerically
            self._data = sorted(
                self._data, key=lambda x: float(x[column]["value"]), reverse=(order == Qt.DescendingOrder)
            )
        except ValueError:  # Fallback to lexicographical sorting if not numeric
            self._data = sorted(self._data, key=lambda x: x[column]["value"], reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()

    def clear(self):
        self.layoutAboutToBeChanged.emit()
        self._data = []  # Empty the underlying data
        self.layoutChanged.emit()

    def appendRows(self, rows):
        self.layoutAboutToBeChanged.emit()
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + len(rows) - 1)
        for row_data in rows:
            row = [{"value": col_data, "changed": False} for col_data in row_data]
            self._data.append(row)
        self.endInsertRows()
        self.layoutChanged.emit()

    def save_object_info(self):
        for row in self._data:
            # print(row)
            id = row[0]["value"]
            obj = MdObject.get_by_id(id)
            ds = obj.dataset
            ds.get_variablename_list()
            property_list = []
            for idx, col in enumerate(row):
                if idx > max(self._uneditable_columns):
                    # print("idx:", idx, "col:", col['value'])
                    property_list.append(str(col["value"]))
                elif idx == 1:
                    obj.sequence = col["value"]
            obj.variable_list = property_list
            obj.pack_variable()
            obj.save()
        self.data_changed = False
