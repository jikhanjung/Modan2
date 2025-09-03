import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QListWidget, QListWidgetItem, QTextEdit)
from PyQt6.QtGui import QDrag, QCursor, QPixmap
from PyQt6.QtCore import Qt, QMimeData, QObject, QEvent

class DragEventFilter(QObject):
    def __init__(self, drag_object):
        super().__init__()
        self.drag_object = drag_object

    def eventFilter(self, obj, event):
        if event.type() in [QEvent.Type.KeyPress, QEvent.Type.KeyRelease]:
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self.drag_object.setDragCursor(self.drag_object.copy_cursor.pixmap(), Qt.DropAction.CopyAction)
                print("Set Copy Cursor")
            else:
                self.drag_object.setDragCursor(self.drag_object.move_cursor.pixmap(), Qt.DropAction.MoveAction)
                print("Set Move Cursor")
        return False

class CustomDrag(QDrag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.copy_cursor = QCursor(Qt.CursorShape.DragCopyCursor)
        self.move_cursor = QCursor(Qt.CursorShape.DragMoveCursor)

    def exec_(self, supportedActions, defaultAction=Qt.DropAction.IgnoreAction):
        event_filter = DragEventFilter(self)
        QApplication.instance().installEventFilter(event_filter)
        
        # Set initial cursor
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.setDragCursor(self.copy_cursor.pixmap(), Qt.DropAction.CopyAction)
        else:
            self.setDragCursor(self.move_cursor.pixmap(), Qt.DropAction.MoveAction)
        
        result = super().exec_(supportedActions, defaultAction)
        
        QApplication.instance().removeEventFilter(event_filter)
        return result

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            item = self.currentItem()
            if item:
                drag = CustomDrag(self)
                mimeData = QMimeData()
                mimeData.setText(item.text())
                drag.setMimeData(mimeData)

                # Optional: Set a pixmap for the drag operation
                #pixmap = QPixmap(self.viewport().size())
                #self.viewport().render(pixmap)
                #drag.setPixmap(pixmap)

                result = drag.exec_(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
                
                if result == Qt.DropAction.MoveAction:
                    self.takeItem(self.row(item))

class DropTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.insertPlainText(event.mimeData().text() + '\n')
        event.acceptProposedAction()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag and Drop with Custom Cursor")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        self.list_widget = DraggableListWidget()
        self.text_edit = DropTextEdit()

        layout.addWidget(self.list_widget)
        layout.addWidget(self.text_edit)

        # Populate the list widget
        for i in range(10):
            self.list_widget.addItem(QListWidgetItem(f"Item {i+1}"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())