#!/usr/bin/env python3
"""
Fix Qt import issues for WSL/Linux environments
This script sets up proper Qt environment variables and runs Modan2
"""

import os
import sys


def setup_qt_environment():
    """Setup Qt environment variables for WSL/Linux"""
    print("Setting up Qt environment...")

    # Set Qt platform plugin path
    qt_plugin_paths = [
        "/usr/lib/x86_64-linux-gnu/qt5/plugins",
        "/usr/lib/x86_64-linux-gnu/qt5/plugins/platforms",
        "/usr/lib/qt5/plugins",
        "/usr/lib/qt5/plugins/platforms",
    ]

    for path in qt_plugin_paths:
        if os.path.exists(path):
            os.environ["QT_PLUGIN_PATH"] = path
            print(f"Set QT_PLUGIN_PATH to: {path}")
            break

    # Set Qt platform
    os.environ["QT_QPA_PLATFORM"] = "xcb"

    # Disable Qt High DPI scaling issues
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"

    # Fix potential font issues
    os.environ["QT_QPA_FONTDIR"] = "/usr/share/fonts"

    # Enable debug output for Qt
    # os.environ['QT_DEBUG_PLUGINS'] = '1'

    print("Qt environment setup complete")


def check_display():
    """Check if DISPLAY is set for X11"""
    display = os.environ.get("DISPLAY")
    if not display:
        print("WARNING: DISPLAY environment variable not set")
        print("For WSL, you may need to:")
        print("1. Install an X server (like VcXsrv)")
        print("2. Set DISPLAY variable: export DISPLAY=:0")
        return False

    print(f"DISPLAY is set to: {display}")
    return True


def test_qt():
    """Test if Qt can initialize properly"""
    try:
        from PyQt5.QtCore import QT_VERSION_STR
        from PyQt5.QtWidgets import QApplication

        print(f"PyQt5 version: {QT_VERSION_STR}")

        # Try to create QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        print("Qt initialization successful")
        return True

    except Exception as e:
        print(f"Qt initialization failed: {e}")
        return False


def main():
    """Main function"""
    print("=== Modan2 Qt Environment Fix ===")

    # Check display
    if not check_display():
        print("Display check failed - GUI may not work properly")

    # Setup Qt environment
    setup_qt_environment()

    # Test Qt
    if not test_qt():
        print("Qt test failed - trying alternative setup...")

        # Alternative Qt platform
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        print("Set Qt platform to offscreen mode")

        if not test_qt():
            print("ERROR: Could not initialize Qt")
            sys.exit(1)

    # Run main application
    print("\n=== Starting Modan2 ===")
    try:
        import main

        main.main()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
