#!/usr/bin/env python3

import sys

print("=== OpenGL Environment Check ===")

# Check numpy
try:
    import numpy
    print(f"numpy: {numpy.__version__}")
except Exception as e:
    print(f"numpy: ERROR - {e}")

# Check PyOpenGL
try:
    import OpenGL
    print(f"PyOpenGL: {OpenGL.__version__}")
except Exception as e:
    print(f"PyOpenGL: ERROR - {e}")

# Check PyOpenGL-accelerate
try:
    import OpenGL_accelerate
    print("PyOpenGL-accelerate: available")
    
    # Try specific GLUT functions
    from OpenGL import GL as gl
    from OpenGL import GLUT as glut
    
    print("GLUT import: OK")
    
    # Test GLUT initialization
    try:
        glut.glutInit(sys.argv)
        print("GLUT init: OK")
    except Exception as e:
        print(f"GLUT init: ERROR - {e}")
        
except Exception as e:
    print(f"PyOpenGL-accelerate: ERROR - {e}")

# Check installation method
try:
    import pkg_resources
    opengl_dist = pkg_resources.get_distribution('PyOpenGL')
    accelerate_dist = pkg_resources.get_distribution('PyOpenGL-accelerate')
    print(f"PyOpenGL location: {opengl_dist.location}")
    print(f"PyOpenGL-accelerate location: {accelerate_dist.location}")
except Exception as e:
    print(f"Package info: ERROR - {e}")