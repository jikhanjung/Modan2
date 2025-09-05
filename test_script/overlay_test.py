# overlay_modern_gl.py
# PyQt5 + Modern OpenGL(Shaders/VBO/VAO) + Transparent Top-Level Overlay Window
import sys
import math
import ctypes
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QOpenGLWidget, QLabel, QVBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QSurfaceFormat, QGuiApplication
from PyQt5.QtCore import QCoreApplication

from OpenGL.GL import *


# ---------------------------
# Utilities (shader helpers)
# ---------------------------
def compile_shader(source: str, shader_type) -> int:
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    status = glGetShaderiv(shader, GL_COMPILE_STATUS)
    if status != GL_TRUE:
        log = glGetShaderInfoLog(shader).decode("utf-8", "ignore")
        typ = "VERTEX" if shader_type == GL_VERTEX_SHADER else "FRAGMENT"
        raise RuntimeError(f"[{typ} SHADER COMPILE ERROR]\n{log}\nSource:\n{source}")
    return shader


def link_program(vs: int, fs: int) -> int:
    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    glLinkProgram(prog)
    status = glGetProgramiv(prog, GL_LINK_STATUS)
    if status != GL_TRUE:
        log = glGetProgramInfoLog(prog).decode("utf-8", "ignore")
        raise RuntimeError(f"[PROGRAM LINK ERROR]\n{log}")
    # shaders can be deleted after linking
    glDetachShader(prog, vs)
    glDetachShader(prog, fs)
    glDeleteShader(vs)
    glDeleteShader(fs)
    return prog


# ---------------------------
# OpenGL Overlay Widget
# ---------------------------
class OverlayGL(QOpenGLWidget):
    """Transparent background OpenGL overlay. Renders a rotating triangle with alpha."""
    def __init__(self, parent=None):
        super().__init__(parent)

        # Request alpha buffer for transparency + core profile is OK (ES도 문제없음)
        fmt = QSurfaceFormat()
        fmt.setRenderableType(QSurfaceFormat.OpenGL)
        # Core/Compatibility 모두 셰이더 기반이라 상관 없지만 명시적으로 Core:
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setVersion(3, 3)
        fmt.setAlphaBufferSize(8)   # ✨ important for transparent background
        fmt.setSamples(4)           # optional MSAA for smoother edges
        self.setFormat(fmt)

        # 타이머로 간단 회전 애니메이션
        self._theta = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60 FPS

        # GL objects
        self._prog = None
        self._vao = None
        self._vbo = None
        self._u_rotation = None
        self._u_color = None

    def _tick(self):
        self._theta += 1.2  # deg/frame
        if self._theta > 360.0:
            self._theta -= 360.0
        self.update()  # schedule repaint

    # ---------- OpenGL lifecycle ----------
    def initializeGL(self):
        # Debug: print context info
        fmt = self.context().format()
        print(f"[GL] Profile: {fmt.profile()} (0=NoProfile,1=Core,2=Compatibility)")
        print(f"[GL] Version: {fmt.majorVersion()}.{fmt.minorVersion()}")

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)  # overlay HUD 용이라면 보통 끔

        # --- build shader program ---
        vert_src = """
        #version 330 core
        layout(location=0) in vec2 pos;
        uniform float u_rotation;   // radians
        void main(){
            float c = cos(u_rotation);
            float s = sin(u_rotation);
            mat2 R = mat2(c, -s, s, c);
            vec2 p = R * pos;
            gl_Position = vec4(p, 0.0, 1.0);
        }
        """
        frag_src = """
        #version 330 core
        out vec4 outColor;
        uniform vec4 u_color;
        void main(){
            outColor = u_color;   // RGBA, 알파 포함
        }
        """
        vs = compile_shader(vert_src, GL_VERTEX_SHADER)
        fs = compile_shader(frag_src, GL_FRAGMENT_SHADER)
        self._prog = link_program(vs, fs)

        # uniform locations
        self._u_rotation = glGetUniformLocation(self._prog, "u_rotation")
        self._u_color    = glGetUniformLocation(self._prog, "u_color")

        # --- geometry (triangle) ---
        tri = np.array([
            -0.5, -0.5,
             0.5, -0.5,
             0.0,  0.5
        ], dtype=np.float32)

        self._vao = glGenVertexArrays(1)
        self._vbo = glGenBuffers(1)

        glBindVertexArray(self._vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, tri.nbytes, tri, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def resizeGL(self, w, h):
        # HiDPI 고려 (자동로직이 대부분 해주지만 직접 맞추고 싶다면:)
        dpr = self.devicePixelRatio()
        glViewport(0, 0, int(w * dpr), int(h * dpr))

    def paintGL(self):
        # ✨ 완전 투명 배경 (아래 위젯이 그대로 보임)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(self._prog)

        # 회전값(rad) 업데이트
        rad = math.radians(self._theta)
        glUniform1f(self._u_rotation, rad)

        # 반투명 흰색(알파 0.9)
        glUniform4f(self._u_color, 1.0, 1.0, 1.0, 0.9)

        glBindVertexArray(self._vao)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        glBindVertexArray(0)

        glUseProgram(0)

    def deleteGL(self):
        # 리소스 정리
        try:
            if self._vbo:
                glDeleteBuffers(1, [self._vbo])
                self._vbo = None
            if self._vao:
                glDeleteVertexArrays(1, [self._vao])
                self._vao = None
            if self._prog:
                glDeleteProgram(self._prog)
                self._prog = None
        except Exception:
            pass

    def closeEvent(self, e):
        self.makeCurrent()
        self.deleteGL()
        self.doneCurrent()
        super().closeEvent(e)


# ---------------------------
# Transparent Top-Level Overlay Window
# ---------------------------
class OverlayWindow(QWidget):
    """
    - Frameless, translucent top-level window that follows the anchor window.
    - Mouse events pass through by default (so 아래 위젯과 상호작용 가능).
    """
    def __init__(self, anchor_window: QMainWindow, pass_mouse=True):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)         # ✨ window transparency
        self.setAttribute(Qt.WA_AlwaysStackOnTop, True)
        if pass_mouse:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True) # 클릭 통과

        self.anchor = anchor_window
        self.anchor.installEventFilter(self)

        self.gl = OverlayGL(self)
        self.gl.setGeometry(self.rect())

        self.sync_to_anchor()
        self.show()

    def eventFilter(self, obj, ev):
        if obj is self.anchor and ev.type() in (
            QEvent.Move, QEvent.Resize, QEvent.WindowStateChange, QEvent.Show, QEvent.Hide
        ):
            self.sync_to_anchor()
        return super().eventFilter(obj, ev)

    def resizeEvent(self, e):
        self.gl.setGeometry(self.rect())
        super().resizeEvent(e)

    def sync_to_anchor(self):
        if not self.anchor.isVisible():
            self.hide()
            return
        # 앵커의 프레임 지오메트리(스크린 좌표)에 맞추어 위치/크기 동기화
        g = self.anchor.frameGeometry()
        self.setGeometry(g)
        self.show()


# ---------------------------
# Example Main Window (Anchor)
# ---------------------------
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anchor Window (PyQt5 + Modern GL Overlay)")
        self.setGeometry(200, 200, 900, 600)

        # 내용물은 그냥 예시 UI
        center = QWidget(self)
        lay = QVBoxLayout(center)
        label = QLabel("아래는 일반 위젯 UI입니다.\n오버레이 창에 그려진 삼각형이 위에 떠 있습니다.", center)
        label.setAlignment(Qt.AlignCenter)
        btn = QPushButton("오버레이 토글", center)
        btn.clicked.connect(self.toggle_overlay)
        lay.addWidget(label)
        lay.addWidget(btn)
        self.setCentralWidget(center)

        # 오버레이 켜기
        self.overlay = OverlayWindow(self, pass_mouse=True)

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.sync_to_anchor()
            self.overlay.show()


if __name__ == "__main__":
    # (선택) ANGLE 대신 데스크탑 OpenGL을 선호한다면 **QApplication 생성 전** 설정
    # 일부 환경에서는 불필요하지만, 드라이버 이슈 회피에 도움이 될 수 있음.
    QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL, True)

    app = QApplication(sys.argv)

    # HiDPI를 좀 더 예쁘게 (선택)
    QGuiApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    w = Main()
    w.show()
    sys.exit(app.exec_())
