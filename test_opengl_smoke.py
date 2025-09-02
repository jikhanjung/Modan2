#!/usr/bin/env python3
"""
OpenGL smoke test for CI/CD pipeline
Tests basic OpenGL functionality without requiring a display
"""

import sys
import os

def test_opengl_import():
    """Test that OpenGL modules can be imported"""
    print("Testing OpenGL module imports...")
    try:
        import OpenGL
        print(f"✓ OpenGL version: {OpenGL.__version__}")
    except ImportError as e:
        print(f"✗ Failed to import OpenGL: {e}")
        return False
    
    try:
        import numpy
        print(f"✓ NumPy version: {numpy.__version__}")
    except ImportError as e:
        print(f"✗ Failed to import numpy: {e}")
        return False
    
    try:
        from OpenGL import GL
        print("✓ OpenGL.GL imported")
    except ImportError as e:
        print(f"✗ Failed to import OpenGL.GL: {e}")
        return False
    
    try:
        from OpenGL import GLU
        print("✓ OpenGL.GLU imported")
    except ImportError as e:
        print(f"✗ Failed to import OpenGL.GLU: {e}")
        return False
    
    return True

def test_pyqt5_import():
    """Test that PyQt5 modules can be imported"""
    print("\nTesting PyQt5 module imports...")
    try:
        from PyQt5 import QtCore
        print(f"✓ PyQt5.QtCore version: {QtCore.QT_VERSION_STR}")
    except ImportError as e:
        print(f"✗ Failed to import PyQt5.QtCore: {e}")
        return False
    
    try:
        from PyQt5.QtWidgets import QApplication
        print("✓ PyQt5.QtWidgets.QApplication imported")
    except ImportError as e:
        print(f"✗ Failed to import PyQt5.QtWidgets.QApplication: {e}")
        return False
    
    try:
        from PyQt5.QtOpenGL import QGLWidget
        print("✓ PyQt5.QtOpenGL.QGLWidget imported (legacy)")
    except ImportError as e:
        print(f"⚠ Could not import QGLWidget (legacy): {e}")
    
    try:
        from PyQt5.QtWidgets import QOpenGLWidget
        print("✓ PyQt5.QtWidgets.QOpenGLWidget imported")
    except ImportError as e:
        print(f"✗ Failed to import QOpenGLWidget: {e}")
        return False
    
    return True

def test_offscreen_context():
    """Test creating an offscreen OpenGL context"""
    print("\nTesting offscreen OpenGL context creation...")
    
    # Set up offscreen rendering
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QSurfaceFormat, QOpenGLContext, QOffscreenSurface
        
        # Create application (required for Qt)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("✓ QApplication created")
        
        # Set up surface format
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)  # OpenGL 2.1
        fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
        fmt.setDepthBufferSize(24)
        fmt.setStencilBufferSize(8)
        fmt.setSamples(4)
        QSurfaceFormat.setDefaultFormat(fmt)
        print("✓ Surface format configured")
        
        # Create context
        ctx = QOpenGLContext()
        ctx.setFormat(fmt)
        if not ctx.create():
            print("✗ Failed to create OpenGL context")
            return False
        print("✓ OpenGL context created")
        
        # Create offscreen surface
        surf = QOffscreenSurface()
        surf.setFormat(fmt)
        surf.create()
        if not surf.isValid():
            print("✗ Offscreen surface is not valid")
            return False
        print("✓ Offscreen surface created")
        
        # Make context current
        if not ctx.makeCurrent(surf):
            print("✗ Failed to make context current")
            return False
        print("✓ Context made current")
        
        # Test OpenGL calls
        from OpenGL.GL import glGetString, GL_VERSION, GL_VENDOR, GL_RENDERER
        
        version = glGetString(GL_VERSION)
        vendor = glGetString(GL_VENDOR)
        renderer = glGetString(GL_RENDERER)
        
        if version:
            print(f"✓ OpenGL Version: {version.decode('utf-8', errors='ignore')}")
        if vendor:
            print(f"✓ OpenGL Vendor: {vendor.decode('utf-8', errors='ignore')}")
        if renderer:
            print(f"✓ OpenGL Renderer: {renderer.decode('utf-8', errors='ignore')}")
        
        ctx.doneCurrent()
        print("✓ Context released")
        
        return True
        
    except Exception as e:
        print(f"✗ Offscreen context test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("OpenGL Smoke Test for CI/CD")
    print("=" * 60)
    
    all_passed = True
    
    # Test imports
    if not test_opengl_import():
        all_passed = False
    
    if not test_pyqt5_import():
        all_passed = False
    
    # Test offscreen context (may not work in all CI environments)
    if not test_offscreen_context():
        print("⚠ Offscreen context test failed (this is expected in some CI environments)")
        # Don't fail the whole test for this
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All critical tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())