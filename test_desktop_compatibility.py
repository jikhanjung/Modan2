#!/usr/bin/env python3
import os, sys
# 1) ANGLE(ES) 말고 데스크탑 OpenGL 강제
os.environ["QT_OPENGL"] = "desktop"   # <= 중요: 반드시 QApplication 생성 전

from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL import GL as gl, GLUT as glut, GLU as glu

# 2) 디폴트 포맷: 2.1 + Compatibility (QApplication 이전)
fmt = QSurfaceFormat()
fmt.setVersion(2, 1)  # 3.x에서 잡히는 Core 분쟁 피하려고 2.1 추천
fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
QSurfaceFormat.setDefaultFormat(fmt)

# 3) GLU 사용하므로 GLUT 초기화 불필요
# glut.glutInit(sys.argv)  # 제거됨

class W(QOpenGLWidget):
    def initializeGL(self):
        ctx = self.context()
        f = ctx.format()
        print("Profile:", f.profile(), "(2=Compatibility)")
        print("Version:", f.majorVersion(), f.minorVersion())
        print("Is OpenGLES:", ctx.isOpenGLES())

        gl.glClearColor(0.2, 0.2, 0.2, 1)
        gl.glEnable(gl.GL_DEPTH_TEST)

        # Compatibility 컨텍스트에서만 유효
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (1.0, 1.0, 1.0, 0.0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT,  (0.2, 0.2, 0.2, 1.0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE,  (0.8, 0.8, 0.8, 1.0))
        
        # GLU 쿼드릭 초기화 (GLUT 대신)
        self.quad = glu.gluNewQuadric()
        glu.gluQuadricNormals(self.quad, glu.GLU_SMOOTH)  # 조명용 노멀
        print("GLU quadric initialized successfully")

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        gl.glTranslatef(0, 0, -5)
        
        try:
            for i in range(5):
                gl.glPushMatrix()
                gl.glTranslatef(i * 0.5 - 1, 0, 0)
                gl.glColor3f(1.0, 0.5, 0.0)
                # GLU 구체 (GLUT 대신) - DLL 충돌 없음
                glu.gluSphere(self.quad, 0.3, 16, 16)
                gl.glPopMatrix()
            print("✅ GLU sphere rendering: SUCCESS")
        except Exception as e:
            print(f"❌ GLU sphere: FAILED - {e}")

    def resizeGL(self, w, h):
        if h == 0: h = 1
        gl.glViewport(0, 0, w, h)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45.0, w / h, 0.1, 100.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setCentralWidget(W())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Main(); win.resize(600, 400); win.show()
    sys.exit(app.exec())
