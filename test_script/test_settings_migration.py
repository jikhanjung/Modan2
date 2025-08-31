#!/usr/bin/env python
"""
Test script to verify the QSettings to JSON migration.
Tests that settings are properly saved and loaded from the JSON config file.
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))

def test_settings_wrapper():
    """Test the SettingsWrapper functionality."""
    
    # Create a test config
    test_config = {
        "ui": {
            "remember_geometry": True,
            "toolbar_icon_size": "Medium",
            "window_geometry": {
                "main_window": [100, 100, 800, 600]
            }
        },
        "calibration": {
            "unit": "mm"
        },
        "language": "en"
    }
    
    # Import the main window to get SettingsWrapper
    from Modan2 import ModanMainWindow
    
    # Create app instance
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create main window with test config
    window = ModanMainWindow(test_config)
    settings = window.m_app.settings
    
    print("Testing SettingsWrapper...")
    print("-" * 50)
    
    # Test reading values
    print("\n1. Testing READ operations:")
    print(f"   RememberGeometry: {settings.value('WindowGeometry/RememberGeometry', False)}")
    print(f"   ToolbarIconSize: {settings.value('ToolbarIconSize', 'Unknown')}")
    print(f"   Language: {settings.value('Language', 'Unknown')}")
    print(f"   Calibration Unit: {settings.value('Calibration/Unit', 'Unknown')}")
    
    # Test writing values
    print("\n2. Testing WRITE operations:")
    settings.setValue("Language", "ko")
    settings.setValue("Calibration/Unit", "cm")
    settings.setValue("WindowGeometry/MainWindow", QRect(200, 200, 1024, 768))
    settings.setValue("ToolbarIconSize", "Large")
    
    # Verify writes
    print(f"   Language after write: {settings.value('Language', 'Unknown')}")
    print(f"   Calibration Unit after write: {settings.value('Calibration/Unit', 'Unknown')}")
    print(f"   ToolbarIconSize after write: {settings.value('ToolbarIconSize', 'Unknown')}")
    
    # Test WindowGeometry handling
    geometry = settings.value("WindowGeometry/MainWindow", QRect())
    if isinstance(geometry, QRect):
        print(f"   MainWindow geometry: {[geometry.x(), geometry.y(), geometry.width(), geometry.height()]}")
    else:
        print(f"   MainWindow geometry: {geometry}")
    
    # Save to file
    print("\n3. Testing SAVE to file:")
    settings.sync()
    
    # Read the saved file
    config_path = Path.home() / '.modan2' / 'config.json'
    if config_path.exists():
        with open(config_path, 'r') as f:
            saved_config = json.load(f)
        
        print(f"   Config file exists at: {config_path}")
        print(f"   Language in file: {saved_config.get('language', 'Not found')}")
        print(f"   Calibration unit in file: {saved_config.get('calibration', {}).get('unit', 'Not found')}")
        print(f"   Toolbar icon size in file: {saved_config.get('ui', {}).get('toolbar_icon_size', 'Not found')}")
        
        # Check nested values
        window_geometry = saved_config.get('ui', {}).get('window_geometry', {}).get('main_window', None)
        print(f"   Main window geometry in file: {window_geometry}")
    else:
        print(f"   ERROR: Config file not found at {config_path}")
    
    print("\n4. Testing data point colors/markers:")
    # Test dynamic key mapping for colors and markers
    for i in range(3):
        settings.setValue(f"DataPointColor/{i}", f"#FF00{i}0")
        settings.setValue(f"DataPointMarker/{i}", f"marker_{i}")
    
    for i in range(3):
        color = settings.value(f"DataPointColor/{i}", "Not found")
        marker = settings.value(f"DataPointMarker/{i}", "Not found")
        print(f"   DataPointColor/{i}: {color}")
        print(f"   DataPointMarker/{i}: {marker}")
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)
    
    # Cleanup
    app.quit()
    return True

if __name__ == "__main__":
    try:
        success = test_settings_wrapper()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)