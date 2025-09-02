#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat
from OpenGL import GL as gl
from OpenGL import GLUT as glut
from OpenGL import GLU as glu

# 1) GLUT은 한 번만 초기화
print("Initializing GLUT...")
glut.glutInit(sys.argv)
print("GLUT initialized successfully")

# 2) Core 대신 Compatibility 프로파일로 강제
fmt = QSurfaceFormat()
fmt.setVersion(3, 3)  # 또는 (2, 1)
fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
QSurfaceFormat.setDefaultFormat(fmt)
print("OpenGL format set to Compatibility profile")

class TestGLUTWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.glut_ok = True

    def initializeGL(self):
        print("=== Testing GLUT in PyQt6 OpenGL Context ===")
        print(f"OpenGL Version: {gl.glGetString(gl.GL_VERSION).decode()}")
        print(f"OpenGL Renderer: {gl.glGetString(gl.GL_RENDERER).decode()}")
        
        gl.glClearColor(0.2, 0.2, 0.2, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        # 조명 파라미터는 파이썬 리스트로도 OK
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (1.0, 1.0, 1.0, 0.0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT,  (0.2, 0.2, 0.2, 1.0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE,  (0.8, 0.8, 0.8, 1.0))

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        if not self.glut_ok:
            return
        gl.glLoadIdentity()
        gl.glTranslatef(0, 0, -5)

        try:
            for i in range(5):
                gl.glPushMatrix()
                gl.glTranslatef(i * 0.5 - 1, 0, 0)
                gl.glColor3f(1.0, 0.5, 0.0)
                # GLUT 도형 호출 (Compatibility 컨텍스트에서만 안전)
                glut.glutSolidSphere(0.3, 16, 16)
                gl.glPopMatrix()
            print("✅ Multiple glutSolidSphere calls: SUCCESS")
        except Exception as e:
            print(f"❌ glutSolidSphere: FAILED - {e}")
            self.glut_ok = False

    def resizeGL(self, w, h):
        if h == 0:
            h = 1
        gl.glViewport(0, 0, w, h)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45.0, w / h, 0.1, 100.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 + GLUT Compatibility Profile Test")
        self.resize(600, 400)
        self.gl_widget = TestGLUTWidget()
        self.setCentralWidget(self.gl_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = TestWindow()
    w.show()
    print("Window shown, testing GLUT with Compatibility profile...")
    sys.exit(app.exec())