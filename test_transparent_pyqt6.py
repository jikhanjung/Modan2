#!/usr/bin/env python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtCore import Qt
import OpenGL.GL as gl

class TransparentGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        # Set up format before widget creation
        fmt = QSurfaceFormat()
        fmt.setAlphaBufferSize(8)
        fmt.setSamples(0)
        fmt.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
        QSurfaceFormat.setDefaultFormat(fmt)
        
        super().__init__(parent)
        
        # Enable transparency
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
    def initializeGL(self):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
    def paintGL(self):
        # Clear with transparent background
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Draw a semi-transparent red triangle
        gl.glColor4f(1.0, 0.0, 0.0, 0.5)
        gl.glBegin(gl.GL_TRIANGLES)
        gl.glVertex3f(-0.5, -0.5, 0)
        gl.glVertex3f(0.5, -0.5, 0)
        gl.glVertex3f(0.0, 0.5, 0)
        gl.glEnd()
        
    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transparent OpenGL Test")
        
        # Make main window also support transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        self.gl_widget = TransparentGLWidget(self)
        self.setCentralWidget(self.gl_widget)
        self.resize(400, 400)

if __name__ == "__main__":
    # Set format before creating application
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    fmt.setSamples(0)
    QSurfaceFormat.setDefaultFormat(fmt)
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())