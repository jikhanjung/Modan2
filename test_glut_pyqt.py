#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGL import QGLWidget
from OpenGL import GL as gl
from OpenGL import GLUT as glut
from OpenGL import GLU as glu

class TestGLUTWidget(QGLWidget):
    def __init__(self):
        super().__init__()
        self.glut_initialized = False

    def initializeGL(self):
        print("=== Testing GLUT in PyQt6 OpenGL Context ===")
        
        # Test GLUT initialization
        try:
            print("Attempting GLUT initialization...")
            glut.glutInit(sys.argv)
            self.glut_initialized = True
            print("✅ GLUT initialization: SUCCESS")
        except Exception as e:
            print(f"❌ GLUT initialization: FAILED - {e}")
            return

        # Setup basic OpenGL
        gl.glClearColor(0.2, 0.2, 0.2, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        if not self.glut_initialized:
            return
            
        gl.glLoadIdentity()
        gl.glTranslatef(0, 0, -5)
        
        # Test glutSolidSphere
        try:
            gl.glColor3f(1.0, 0.0, 0.0)
            glut.glutSolidSphere(1.0, 20, 20)
            print("✅ glutSolidSphere: SUCCESS")
        except Exception as e:
            print(f"❌ glutSolidSphere: FAILED - {e}")
            
    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45, width/height, 0.1, 100)
        gl.glMatrixMode(gl.GL_MODELVIEW)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GLUT + PyQt6 Test")
        self.resize(400, 300)
        
        self.gl_widget = TestGLUTWidget()
        self.setCentralWidget(self.gl_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("Window shown, GLUT test should run in paintGL...")
    
    # Force a paint event
    window.gl_widget.update()
    
    sys.exit(app.exec())