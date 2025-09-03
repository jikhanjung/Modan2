import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTreeView, QTableView, QHeaderView)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QDrag, QCursor
from PyQt6.QtCore import Qt, QMimeData, QObject, QEvent

class DragEventFilter(QObject):
    def __init__(self, drag_object):
        super().__init__()
        self.drag_object = drag_object
        self.copy_cursor = QCursor(Qt.CursorShape.DragCopyCursor)
        self.move_cursor = QCursor(Qt.CursorShape.DragMoveCursor)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress or event.type() == QEvent.KeyRelease:
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self.drag_object.setDragCursor(self.copy_cursor.pixmap(), Qt.DropAction.CopyAction)
            else:
                self.drag_object.setDragCursor(self.move_cursor.pixmap(), Qt.DropAction.MoveAction)
        return False

class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.currentIndex().data())
            drag.setMimeData(mime_data)

            # Create and install the event filter
            event_filter = DragEventFilter(drag)
            QApplication.instance().installEventFilter(event_filter)

            # Set initial cursor
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                drag.setDragCursor(event_filter.copy_cursor.pixmap(), Qt.DropAction.CopyAction)
            else:
                drag.setDragCursor(event_filter.move_cursor.pixmap(), Qt.DropAction.MoveAction)

            # Execute drag operation
            result = drag.exec_(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)

            # Remove the event filter after drag operation
            QApplication.instance().removeEventFilter(event_filter)

        super().mouseMoveEvent(event)

class CustomTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        text = event.mimeData().text()
        row_count = self.model().rowCount()
        self.model().insertRow(row_count)
        self.model().setData(self.model().index(row_count, 0), text)
        event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag and Drop Example")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        self.tree_view = CustomTreeView()
        self.table_view = CustomTableView()

        layout.addWidget(self.tree_view)
        layout.addWidget(self.table_view)

        self.setup_tree_model()
        self.setup_table_model()

    def setup_tree_model(self):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Items'])
        root = model.invisibleRootItem()
        for i in range(5):
            item = QStandardItem(f"Item {i+1}")
            root.appendRow(item)
            for j in range(3):
                child = QStandardItem(f"Child {i+1}.{j+1}")
                item.appendRow(child)
        self.tree_view.setModel(model)
        self.tree_view.expandAll()

    def setup_table_model(self):
        model = QStandardItemModel(0, 1)
        model.setHorizontalHeaderLabels(['Dropped Items'])
        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())