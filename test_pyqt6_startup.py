#!/usr/bin/env python
"""Test PyQt6 startup - Quick test to see if app launches"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def test_startup():
    """Test if Modan2 can start with PyQt6"""
    try:
        # Import and create the main window
        from Modan2 import ModanMainWindow
        from MdAppSetup import ApplicationSetup
        
        app = QApplication(sys.argv)
        setup = ApplicationSetup()
        
        print("Creating main window...")
        window = ModanMainWindow(setup.get_config())
        
        print("SUCCESS: Main window created!")
        window.show()
        
        # Auto-close after 2 seconds
        QTimer.singleShot(2000, app.quit)
        
        return app.exec()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_startup())