import sys

from PyQt5.QtCore import QEvent, QMimeData, QObject, Qt
from PyQt5.QtGui import QCursor, QDrag, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QMainWindow,
    QTableView,
    QTreeView,
    QWidget,
)


class GlobalDragEventFilter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.copy_cursor = QCursor(Qt.DragCopyCursor)
        self.move_cursor = QCursor(Qt.DragMoveCursor)
        self.is_active = False

    def eventFilter(self, obj, event):
        if not self.is_active:
            return False

        if event.type() in [QEvent.KeyPress, QEvent.KeyRelease, QEvent.DragMove, QEvent.DragEnter]:
            modifiers = QApplication.queryKeyboardModifiers()  # Use queryKeyboardModifiers instead
            if modifiers & Qt.ControlModifier:
                QApplication.changeOverrideCursor(self.copy_cursor)
            else:
                QApplication.changeOverrideCursor(self.move_cursor)
        return False


class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.global_filter = GlobalDragEventFilter()
        QApplication.instance().installEventFilter(self.global_filter)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.currentIndex().data())
            drag.setMimeData(mime_data)

            # Activate the global filter
            self.global_filter.is_active = True

            # Set initial cursor
            modifiers = QApplication.keyboardModifiers()
            initial_cursor = (
                self.global_filter.copy_cursor if modifiers & Qt.ControlModifier else self.global_filter.move_cursor
            )
            QApplication.setOverrideCursor(initial_cursor)

            # Execute drag operation
            drag.exec_(Qt.CopyAction | Qt.MoveAction)

            # Deactivate the global filter and restore cursor
            self.global_filter.is_active = False
            QApplication.restoreOverrideCursor()

        super().mouseMoveEvent(event)


class CustomTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        QApplication.sendEvent(self, QEvent(QEvent.DragMove))
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
        model.setHorizontalHeaderLabels(["Items"])
        root = model.invisibleRootItem()
        for i in range(5):
            item = QStandardItem(f"Item {i + 1}")
            root.appendRow(item)
            for j in range(3):
                child = QStandardItem(f"Child {i + 1}.{j + 1}")
                item.appendRow(child)
        self.tree_view.setModel(model)
        self.tree_view.expandAll()

    def setup_table_model(self):
        model = QStandardItemModel(0, 1)
        model.setHorizontalHeaderLabels(["Dropped Items"])
        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
