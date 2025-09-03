import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTreeView, QTableView, QHeaderView)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QDrag, QCursor
from PyQt6.QtCore import Qt, QMimeData, QObject, QEvent, QTimer

class GlobalDragEventFilter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.copy_cursor = QCursor(Qt.CursorShape.DragCopyCursor)
        self.move_cursor = QCursor(Qt.CursorShape.DragMoveCursor)
        self.is_active = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_modifiers)
        self.timer.setInterval(100)  # Check every 100 ms
        self.current_cursor_type = None

    def eventFilter(self, obj, event):
        if not self.is_active:
            return False

        if event.type() == QEvent.Type.DragEnter:
            self.timer.start()
            self.check_modifiers()  # Initial check
        elif event.type() == QEvent.Type.DragLeave or event.type() == QEvent.Type.Drop:
            self.timer.stop()
            self.current_cursor_type = None

        return False

    def check_modifiers(self):
        modifiers = QApplication.queryKeyboardModifiers()
        new_cursor_type = Qt.CursorShape.DragCopyCursor if modifiers & Qt.KeyboardModifier.ControlModifier else Qt.CursorShape.DragMoveCursor

        if new_cursor_type != self.current_cursor_type:
            self.current_cursor_type = new_cursor_type
            cursor = self.copy_cursor if new_cursor_type == Qt.CursorShape.DragCopyCursor else self.move_cursor
            QApplication.changeOverrideCursor(cursor)

class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.global_filter = GlobalDragEventFilter()
        QApplication.instance().installEventFilter(self.global_filter)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.currentIndex().data())
            drag.setMimeData(mime_data)

            self.global_filter.is_active = True
            self.global_filter.current_cursor_type = None  # Reset cursor type
            modifiers = QApplication.queryKeyboardModifiers()
            initial_cursor = self.global_filter.copy_cursor if modifiers & Qt.KeyboardModifier.ControlModifier else self.global_filter.move_cursor
            QApplication.setOverrideCursor(initial_cursor)

            result = drag.exec_(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)

            self.global_filter.is_active = False
            self.global_filter.timer.stop()
            self.global_filter.current_cursor_type = None
            QApplication.restoreOverrideCursor()

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