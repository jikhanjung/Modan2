import sys

from PyQt5.QtCore import QMimeData, Qt
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


class CustomDrag(QDrag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.copy_cursor = QCursor(Qt.DragCopyCursor)
        self.move_cursor = QCursor(Qt.DragMoveCursor)

    def exec_(self, supportedActions, defaultAction=Qt.IgnoreAction):
        result = super().exec_(supportedActions, defaultAction)
        QApplication.restoreOverrideCursor()  # Ensure cursor is restored after drag
        return result


class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            drag = CustomDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.currentIndex().data())
            drag.setMimeData(mime_data)

            # Set up the drag to change cursor based on modifiers
            def update_cursor(action):
                modifiers = QApplication.keyboardModifiers()
                if modifiers & Qt.ControlModifier:
                    drag.setDragCursor(drag.copy_cursor.pixmap(), Qt.CopyAction)
                else:
                    drag.setDragCursor(drag.move_cursor.pixmap(), Qt.MoveAction)

            drag.actionChanged.connect(update_cursor)

            # Initial cursor setup
            update_cursor(Qt.MoveAction)

            drag.exec_(Qt.CopyAction | Qt.MoveAction)
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
