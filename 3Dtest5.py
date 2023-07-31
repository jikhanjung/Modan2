import glfw
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import numpy as np

width, height = 800, 600
rotationX, rotationY = 0.0, 0.0
prevMouseX, prevMouseY = 0, 0
rotationMatrix = np.identity(4)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glMultMatrixf(rotationMatrix)
    # Draw your object here
    glutSolidCube(1.0)
    glutSwapBuffers()

def mouse(button, state, x, y):
    global prevMouseX, prevMouseY, rotationX, rotationY
    if button == GLFW_MOUSE_BUTTON_LEFT and state == GLFW_PRESS:
        prevMouseX, prevMouseY = x, y

def motion(x, y):
    global prevMouseX, prevMouseY, rotationX, rotationY, rotationMatrix
    deltaX = x - prevMouseX
    deltaY = y - prevMouseY

    rotationY += deltaX
    rotationX += deltaY

    rotationXMatrix = np.array([[1, 0, 0, 0],
                                [0, np.cos(np.radians(rotationX)), -np.sin(np.radians(rotationX)), 0],
                                [0, np.sin(np.radians(rotationX)), np.cos(np.radians(rotationX)), 0],
                                [0, 0, 0, 1]])

    rotationYMatrix = np.array([[np.cos(np.radians(rotationY)), 0, np.sin(np.radians(rotationY)), 0],
                                [0, 1, 0, 0],
                                [-np.sin(np.radians(rotationY)), 0, np.cos(np.radians(rotationY)), 0],
                                [0, 0, 0, 1]])

    rotationMatrix = np.matmul(rotationYMatrix, rotationXMatrix)

    prevMouseX, prevMouseY = x, y

    glutPostRedisplay()

def main():
    global width, height
    if not glfw.init():
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(width, height, "OpenGL Mouse Rotation", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)


    glClearDepth(1.0)
    glDepthFunc(GL_LESS)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glShadeModel(GL_SMOOTH)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0,(width/height),0.1, 100.0) # 시야각, 종횡비, 근거리 클리핑, 원거리 클리핑
    glMatrixMode(GL_MODELVIEW)
    glutInit(sys.argv)

    glTranslatef(0.0, 0.0, -5)

    glfw.set_mouse_button_callback(window, mouse)
    glfw.set_cursor_pos_callback(window, motion)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        display()

    glfw.terminate()

if __name__ == "__main__":
    main()