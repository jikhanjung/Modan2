#!/bin/bash
# Modan2 launcher script with Qt environment fixes

echo "=== Modan2 Launcher ==="

# Check if we're in WSL
if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
    echo "WSL environment detected"

    # Check if X server is running
    if ! xset q &>/dev/null; then
        echo "WARNING: X server not accessible"
        echo "Please ensure an X server (like VcXsrv) is running"
        echo "And DISPLAY is set correctly"
    fi
fi

# Set Qt environment variables
export QT_QPA_PLATFORM_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/qt5/plugins"
export QT_QPA_PLATFORM=xcb
export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_SCALE_FACTOR=1

# Alternative: try different Qt backends if xcb fails
echo "Attempting to run with XCB platform..."
python main.py "$@"

if [ $? -ne 0 ]; then
    echo "XCB failed, trying Wayland..."
    export QT_QPA_PLATFORM=wayland
    python main.py "$@"

    if [ $? -ne 0 ]; then
        echo "Wayland failed, trying minimal platform (no GUI)..."
        export QT_QPA_PLATFORM=minimal
        python main.py "$@"
    fi
fi
