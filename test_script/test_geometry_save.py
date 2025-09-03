#!/usr/bin/env python
"""
Test script to verify main window geometry saving.
"""
import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRect, QTimer

sys.path.insert(0, str(Path(__file__).parent))

def test_geometry_saving():
    """Test main window geometry saving functionality."""
    
    config_path = Path.home() / '.modan2' / 'config.json'
    
    # Read current config
    print("Reading current config...")
    if config_path.exists():
        with open(config_path, 'r') as f:
            initial_config = json.load(f)
        print(f"Initial main window geometry: {initial_config.get('ui', {}).get('window_geometry', {}).get('main_window', 'Not found')}")
    else:
        print("No config file exists yet")
        initial_config = {}
    
    app = QApplication(sys.argv)
    
    try:
        # Create main window with test config
        from Modan2 import ModanMainWindow
        
        test_config = {
            "ui": {
                "remember_geometry": True,
                "window_geometry": {
                    "main_window": [100, 100, 800, 600]  # Initial position
                }
            },
            "language": "en"
        }
        
        print("\nCreating main window...")
        main_window = ModanMainWindow(test_config)
        
        # Show window
        main_window.show()
        app.processEvents()
        
        print(f"Initial window geometry: {main_window.geometry()}")
        
        # Change window geometry
        new_geometry = QRect(200, 150, 1000, 700)
        main_window.setGeometry(new_geometry)
        app.processEvents()
        
        print(f"Changed window geometry: {main_window.geometry()}")
        
        # Test write_settings manually
        print("\nTesting write_settings...")
        main_window.write_settings()
        
        # Check if settings were written
        if config_path.exists():
            with open(config_path, 'r') as f:
                updated_config = json.load(f)
            
            main_window_geom = updated_config.get('ui', {}).get('window_geometry', {}).get('main_window')
            print(f"Saved geometry in config: {main_window_geom}")
            
            if main_window_geom:
                print("✓ Geometry saving works!")
                expected_geom = [200, 150, 1000, 700]
                if main_window_geom == expected_geom:
                    print("✓ Geometry values are correct!")
                else:
                    print(f"❌ Geometry mismatch. Expected: {expected_geom}, Got: {main_window_geom}")
            else:
                print("❌ Geometry not found in config")
        else:
            print("❌ Config file not created")
        
        # Test closeEvent
        print("\nTesting closeEvent (should also call write_settings)...")
        main_window.close()
        
        # Final config check
        if config_path.exists():
            with open(config_path, 'r') as f:
                final_config = json.load(f)
            
            final_geom = final_config.get('ui', {}).get('window_geometry', {}).get('main_window')
            print(f"Final saved geometry: {final_geom}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if app:
            app.quit()

if __name__ == "__main__":
    success = test_geometry_saving()
    sys.exit(0 if success else 1)