import glfw
from OpenGL.GL import *
import numpy as np
import math

width, height = 800, 600
rotationX, rotationY = 0.0, 0.0
prevMouseX, prevMouseY = 0, 0
rotationMatrix = np.identity(4)

vertex_shader = """
#version 330 core

layout (location = 0) in vec3 aPos;
uniform mat4 transform;

void main()
{
    gl_Position = transform * vec4(aPos, 1.0);
}
"""

fragment_shader = """
#version 330 core

out vec4 FragColor;

void main()
{
    FragColor = vec4(1.0, 0.5, 0.2, 1.0);
}
"""

def create_shader(shader_type, shader_source):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, shader_source)
    glCompileShader(shader)

    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        raise RuntimeError("Shader compilation failed: " + glGetShaderInfoLog(shader).decode("utf-8"))

    return shader

def create_program(vertex_shader_source, fragment_shader_source):
    vertex_shader = create_shader(GL_VERTEX_SHADER, vertex_shader_source)
    fragment_shader = create_shader(GL_FRAGMENT_SHADER, fragment_shader_source)

    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)

    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        raise RuntimeError("Program linking failed: " + glGetProgramInfoLog(program).decode("utf-8"))

    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return program

def create_cube_vao():
    vertices = np.array([
        -0.5, -0.5, -0.5,
         0.5, -0.5, -0.5,
         0.5,  0.5, -0.5,
        -0.5,  0.5, -0.5,
        -0.5, -0.5,  0.5,
         0.5, -0.5,  0.5,
         0.5,  0.5,  0.5,
        -0.5,  0.5,  0.5,
    ], dtype=np.float32)

    indices = np.array([
        0, 1, 2, 2, 3, 0,
        1, 5, 6, 6, 2, 1,
        7, 6, 5, 5, 4, 7,
        4, 0, 3, 3, 7, 4,
        4, 5, 1, 1, 0, 4,
        3, 2, 6, 6, 7, 3,
    ], dtype=np.uint32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    ebo = glGenBuffers(1)

    glBindVertexArray(vao)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, None)
    glEnableVertexAttribArray(0)

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)

    return vao

def display():
    global rotationMatrix

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    transform_location = glGetUniformLocation(shader_program, "transform")

    glUseProgram(shader_program)
    glUniformMatrix4fv(transform_location, 1, GL_FALSE, rotationMatrix)

    glBindVertexArray(cube_vao)
    glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_INT, None)
    glBindVertexArray(0)

    glUseProgram(0)

    glfw.swap_buffers(window)

def mouse(button, action, mods):
    global prevMouseX, prevMouseY
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        prevMouseX, prevMouseY = glfw.get_cursor_pos(window)

def motion(x, y):
    global prevMouseX, prevMouseY, rotationX, rotationY, rotationMatrix

    deltaX = x - prevMouseX
    deltaY = y - prevMouseY

    rotationY += deltaX * 0.5
    rotationX += deltaY * 0.5

    rotationX = max(-90.0, min(90.0, rotationX))

    rotationX_rad = math.radians(rotationX)
    rotationY_rad = math.radians(rotationY)

    rotationXMatrix = np.array([
        [1, 0, 0, 0],
        [0, np.cos(rotationX_rad), -np.sin(rotationX_rad), 0],
        [0, np.sin(rotationX_rad), np.cos(rotationX_rad), 0],
        [0, 0, 0, 1]
    ])

    rotationYMatrix = np.array([
        [np.cos(rotationY_rad), 0, np.sin(rotationY_rad), 0],
        [0, 1, 0, 0],
        [-np.sin(rotationY_rad), 0, np.cos(rotationY_rad), 0],
        [0, 0, 0, 1]
    ])

    rotationMatrix = np.dot(rotationYMatrix, rotationXMatrix)

    prevMouseX, prevMouseY = x, y

def key_callback(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)

def main():
    global width, height, shader_program, cube_vao, rotationMatrix, window

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
    glfw.set_mouse_button_callback(window, mouse)
    glfw.set_cursor_pos_callback(window, motion)
    glfw.set_key_callback(window, key_callback)

    glEnable(GL_DEPTH_TEST)

    shader_program = create_program(vertex_shader, fragment_shader)
    cube_vao = create_cube_vao()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        display()