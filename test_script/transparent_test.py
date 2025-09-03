from PyQt6.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QCheckBox, QColorDialog, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, QStatusBar, QMessageBox, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QSizePolicy, \
                            QTableWidget, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox, \
                            QTabWidget, QListWidget, QSpinBox, QPlainTextEdit
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem, QImage,\
                        QFont, QPainter, QBrush, QMouseEvent, QWheelEvent, QDoubleValidator, QIcon, QCursor
from PyQt6.QtCore import Qt, QRect, QSortFilterProxyModel, QSize, QPoint,\
                         pyqtSlot, QItemSelectionModel, QTimer

from PyQt6 import QtCore


import OpenGL.GL as gl
from OpenGL.GL import *
from OpenGL import GLU as glu
from OpenGL import GLUT as glut
from PyQt6.QtOpenGL import *

class TransparentGLWidget(QGLWidget):
    def __init__(self, parent=None):
        fmt = QGLFormat()
        fmt.setAlpha(True)  # Ensure the format includes an alpha channel
        super(TransparentGLWidget, self).__init__(fmt, parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowTransparentForInput)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)

    def initializeGL(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Clear the background with transparent alpha

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Example: Draw a semi-transparent red triangle
        glColor4f(1.0, 0.0, 0.0, 0.5)
        glBegin(GL_TRIANGLES)
        glVertex3f(-0.5, -0.5, 0)
        glVertex3f(0.5, -0.5, 0)
        glVertex3f(0.0, 0.5, 0)
        glEnd()

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

import sys

if __name__ == "__main__":
    #QApplication : 프로그램을 실행시켜주는 클래스
    #with open('log.txt', 'w') as f:
    #    f.write("hello\n")
    #    # current directory
    #    f.write("current directory 1:" + os.getcwd() + "\n")
    #    f.write("current directory 2:" + os.path.abspath(".") + "\n")
    app = QApplication(sys.argv)

    #app.settings = 
    #app.preferences = QSettings("Modan", "Modan2")

    #WindowClass의 인스턴스 생성
    myWindow = TransparentGLWidget()

    #프로그램 화면을 보여주는 코드
    myWindow.show()
    #myWindow.activateWindow()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec()
