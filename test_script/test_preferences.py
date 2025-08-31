#!/usr/bin/env python
"""
Test script for the Preferences Dialog to check WindowGeometry handling.
"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_preferences_dialog():
    """Test the preferences dialog creation."""
    
    app = QApplication(sys.argv)
    
    try:
        # Import main window to initialize settings
        from Modan2 import ModanMainWindow
        
        # Create test config
        test_config = {
            "ui": {
                "remember_geometry": True,
                "toolbar_icon_size": "Medium",
                "preferences_dialog": [100, 100, 600, 400]  # This should be converted to QRect
            },
            "language": "en"
        }
        
        # Create main window with test config
        main_window = ModanMainWindow(test_config)
        
        print("Testing PreferencesDialog creation...")
        
        # Import and create PreferencesDialog
        from ModanDialogs import PreferencesDialog
        
        # This should not crash now
        prefs_dialog = PreferencesDialog(main_window)
        
        print("✓ PreferencesDialog created successfully!")
        print(f"✓ Dialog geometry: {prefs_dialog.geometry()}")
        
        # Test settings reading
        remember_geom = main_window.m_app.settings.value("WindowGeometry/RememberGeometry", True)
        prefs_geom = main_window.m_app.settings.value("WindowGeometry/PreferencesDialog", QRect(100, 100, 600, 400))
        
        print(f"✓ RememberGeometry setting: {remember_geom}")
        print(f"✓ PreferencesDialog geometry setting: {prefs_geom}")
        print(f"✓ Geometry type: {type(prefs_geom)}")
        
        # Test showing the dialog briefly
        prefs_dialog.show()
        app.processEvents()
        prefs_dialog.close()
        
        print("✓ Dialog show/hide test passed!")
        print("=" * 50)
        print("All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_preferences_dialog()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)