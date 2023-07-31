# https://github.com/yarolig/OBJFileLoader

import os
#import pygame
from OpenGL.GL import *
from OpenGL import GLUT as glut
import math
import numpy as np

class OBJ:
    generate_on_init = True
    @classmethod
    def loadTexture(cls, imagefile):
        return None
        surf = pygame.image.load(imagefile)
        image = pygame.image.tostring(surf, 'RGBA', 1)
        ix, iy = surf.get_rect().size
        texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        return texid

    @classmethod
    def loadMaterial(cls, filename):
        return None
        contents = {}
        mtl = None
        dirname = os.path.dirname(filename)

        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'newmtl':
                mtl = contents[values[1]] = {}
            elif mtl is None:
                raise ValueError("mtl file doesn't start with newmtl stmt")
            elif values[0] == 'map_Kd':
                # load the texture referred to by this declaration
                mtl[values[0]] = values[1]
                imagefile = os.path.join(dirname, mtl['map_Kd'])
                mtl['texture_Kd'] = cls.loadTexture(imagefile)
            else:
                mtl[values[0]] = list(map(float, values[1:]))
        return contents

    def __init__(self, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.original_vertices = []
        self.normals = []
        self.original_normals = []
        self.texcoords = []
        self.faces = []
        self.landmark_list = []
        self.gl_list = 0
        self.rotation_matrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
        ])
        self.max_x = -9999999
        self.min_x = 9999999
        self.max_y = -9999999
        self.min_y = 9999999
        self.max_z = -9999999
        self.min_z = 9999999
        dirname = os.path.dirname(filename)

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
                self.original_vertices.append(v)
            elif values[0] == 'vn':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
                self.original_normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(list(map(float, values[1:3])))
            elif values[0] in ('usemtl', 'usemat'):
                #pass
                material = values[1]
            elif values[0] == 'mtllib':
                pass
                #self.mtl = self.loadMaterial(os.path.join(dirname, values[1]))
            elif values[0] == 'f':
                face = []
                #texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    #if len(w) >= 2 and len(w[1]) > 0:
                    #    texcoords.append(int(w[1]))
                    #else:
                    #    texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms))#, texcoords, material))
        self.max_x = max(self.vertices, key=lambda x: x[0])[0]
        self.min_x = min(self.vertices, key=lambda x: x[0])[0]
        self.max_y = max(self.vertices, key=lambda x: x[1])[1]
        self.min_y = min(self.vertices, key=lambda x: x[1])[1]
        self.max_z = max(self.vertices, key=lambda x: x[2])[2]
        self.min_z = min(self.vertices, key=lambda x: x[2])[2]
        self.center_x = (self.max_x + self.min_x) / 2
        self.center_y = (self.max_y + self.min_y) / 2
        self.center_z = (self.max_z + self.min_z) / 2
        # center vertices
        vertices = np.array(self.vertices)
        vertices[:, 0] -= self.center_x
        vertices[:, 1] -= self.center_y
        vertices[:, 2] -= self.center_z
        self.centered_vertices = vertices.tolist()
        
        if self.generate_on_init:
            self.generate()

    def generate(self):
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        glFrontFace(GL_CCW)
        for face in self.faces:
            vertices, normals = face #, texture_coords, material = face

            #mtl = self.mtl[material]
            if False: #'texture_Kd' in mtl:
                # use diffuse texmap
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
            else:
                # just use diffuse colour
                #glColor(*mtl['Kd'])
                glColor(0.8, 0.8, 0.8, 1)

            glBegin(GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                #if texture_coords[i] > 0:
                #    glTexCoord2fv(self.texcoords[texture_coords[i] - 1])
                glVertex3fv(self.vertices[vertices[i] - 1])
            glEnd()
        glEndList()

    def render(self):
        glCallList(self.gl_list)
        return
        #import datetime
        #print("1:",datetime.datetime.now())
        glFrontFace(GL_CCW)
        for face in self.faces:
            vertices, normals, texture_coords, material = face
            glColor(0.8, 0.8, 0.8, 1)

            glBegin(GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                glVertex3fv(self.vertices[vertices[i] - 1])
            glEnd()
        #print("2:",datetime.datetime.now())

    def free(self):
        glDeleteLists([self.gl_list])

    def rotate(self, rotationX_rad, rotationY_rad):
        #print(rotationX_rad, rotationY_rad)
        rotationXMatrix = np.array([
            [1, 0, 0, 0],
            [0, np.cos(rotationY_rad), -np.sin(rotationY_rad), 0],
            [0, np.sin(rotationY_rad), np.cos(rotationY_rad), 0],
            [0, 0, 0, 1]
        ])

        rotationYMatrix = np.array([
            [np.cos(rotationX_rad), 0, np.sin(rotationX_rad), 0],
            [0, 1, 0, 0],
            [-np.sin(rotationX_rad), 0, np.cos(rotationX_rad), 0],
            [0, 0, 0, 1]
        ])
        #print(rotationXMatrix)
        #print(rotationYMatrix)
        new_rotation_matrix = np.dot(rotationXMatrix, rotationYMatrix)
        self.rotation_matrix = np.dot(new_rotation_matrix, self.rotation_matrix)

        # Create a column of 1's with the same number of rows as vertices
        ones_column = np.ones((np.array(self.centered_vertices).shape[0], 1))

        # Use numpy.hstack() to concatenate the vertices with the ones column
        vertices_with_ones = np.hstack((self.centered_vertices, ones_column))
        new_vertices = np.dot(vertices_with_ones, self.rotation_matrix.T)
        self.vertices = new_vertices[:, 0:3]

        normals_with_ones = np.hstack((self.original_normals, ones_column))
        new_normals = np.dot(normals_with_ones, self.rotation_matrix.T)
        self.normals = new_normals[:, 0:3]

        #self.normals = np.dot(self.normals, self.rotation_matrix)
        #self.generate()


    def rotate_3d(self, theta, axis):
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        r_mx = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        if ( axis == 'Z' ):
            r_mx[0][0] = cos_theta
            r_mx[0][1] = sin_theta
            r_mx[1][0] = -1 * sin_theta
            r_mx[1][1] = cos_theta
        elif ( axis == 'Y' ):
            r_mx[0][0] = cos_theta
            r_mx[0][2] = sin_theta
            r_mx[2][0] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        elif ( axis == 'X' ):
            r_mx[1][1] = cos_theta
            r_mx[1][2] = sin_theta
            r_mx[2][1] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        # print "rotation matrix", r_mx

        for i, lm in enumerate(self.vertices):
            coords = [0,0,0]
            #print("vertex", i, lm)
            x, y, z = lm
            #for j in range(len(self.vertices)):
            #    coords[j] = self.vertices[j]
            x_rotated = x * r_mx[0][0] + y * r_mx[1][0] + z * r_mx[2][0]
            y_rotated = x * r_mx[0][1] + y * r_mx[1][1] + z * r_mx[2][1]
            z_rotated = x * r_mx[0][2] + y * r_mx[1][2] + z * r_mx[2][2]
            self.vertices[i] = x_rotated, y_rotated, z_rotated
            #print("rotated", self.vertices[i])
        for i, normal in enumerate(self.normals):
            coords = [0,0,0]
            #print("vertex", i, lm)
            x, y, z = normal
            #for j in range(len(self.vertices)):
            #    coords[j] = self.vertices[j]
            x_rotated = x * r_mx[0][0] + y * r_mx[1][0] + z * r_mx[2][0]
            y_rotated = x * r_mx[0][1] + y * r_mx[1][1] + z * r_mx[2][1]
            z_rotated = x * r_mx[0][2] + y * r_mx[1][2] + z * r_mx[2][2]
            self.normals[i] = x_rotated, y_rotated, z_rotated
            