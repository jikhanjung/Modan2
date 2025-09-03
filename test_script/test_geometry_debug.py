#!/usr/bin/env python
"""
Debug script to test geometry reading/writing with logs.
"""
import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRect, QTimer

sys.path.insert(0, str(Path(__file__).parent))

def test_geometry_debug():
    """Test geometry with debug logs."""
    
    config_path = Path.home() / '.modan2' / 'config.json'
    
    print("=" * 60)
    print("CURRENT CONFIG FILE CONTENT:")
    print("=" * 60)
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            current_config = json.load(f)
        print(json.dumps(current_config, indent=2))
    else:
        print("No config file exists")
    
    print("\n" + "=" * 60)
    print("STARTING APPLICATION WITH DEBUG LOGS:")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    try:
        from Modan2 import ModanMainWindow
        
        # Create main window (this will trigger read_settings)
        main_window = ModanMainWindow()
        main_window.show()
        app.processEvents()
        
        print(f"\nActual window geometry after show: {main_window.geometry()}")
        print(f"Actual maximized state: {main_window.isMaximized()}")
        
        # Change to small window for testing
        print("\n" + "=" * 60)
        print("CHANGING TO SMALL WINDOW:")
        print("=" * 60)
        
        main_window.showNormal()  # Ensure not maximized
        app.processEvents()
        
        small_geometry = QRect(100, 100, 600, 400)  # Small window on first monitor
        main_window.setGeometry(small_geometry)
        app.processEvents()
        
        print(f"Set small geometry: {small_geometry}")
        print(f"Actual geometry after change: {main_window.geometry()}")
        print(f"Is maximized after change: {main_window.isMaximized()}")
        
        # Save settings
        print("\n" + "=" * 60)
        print("CALLING WRITE_SETTINGS:")
        print("=" * 60)
        
        main_window.write_settings()
        
        print("\n" + "=" * 60)
        print("CONFIG FILE AFTER SAVE:")
        print("=" * 60)
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
            print(json.dumps(saved_config, indent=2))
        
        main_window.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        app.quit()

if __name__ == "__main__":
    test_geometry_debug()