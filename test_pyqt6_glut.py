#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL import GL as gl
from OpenGL import GLUT as glut
from OpenGL import GLU as glu

class TestGLUTWidget(QOpenGLWidget):
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
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        
        # Set up lighting
        light_position = [1.0, 1.0, 1.0, 0.0]
        light_ambient = [0.2, 0.2, 0.2, 1.0]
        light_diffuse = [0.8, 0.8, 0.8, 1.0]
        
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, light_position)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, light_ambient)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, light_diffuse)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        if not self.glut_initialized:
            return
            
        gl.glLoadIdentity()
        gl.glTranslatef(0, 0, -5)
        
        # Test glutSolidSphere multiple times like in actual app
        try:
            for i in range(5):
                gl.glPushMatrix()
                gl.glTranslatef(i * 0.5 - 1, 0, 0)
                gl.glColor3f(1.0, 0.5, 0.0)
                glut.glutSolidSphere(0.3, 16, 16)
                gl.glPopMatrix()
            print("✅ Multiple glutSolidSphere calls: SUCCESS")
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
        self.setWindowTitle("PyQt6 + GLUT Test")
        self.resize(600, 400)
        
        self.gl_widget = TestGLUTWidget()
        self.setCentralWidget(self.gl_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("PyQt6 window shown, testing GLUT sphere rendering...")
    
    # Force a paint event
    window.gl_widget.update()
    
    sys.exit(app.exec())