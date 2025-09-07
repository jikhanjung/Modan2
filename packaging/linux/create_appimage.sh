#!/bin/bash

# This script uses linuxdeploy and appimagetool to create a Linux AppImage
# Usage: ./create_appimage.sh <version_string>

VERSION=$1
if [ -z "$VERSION" ]; then
  echo "Usage: ./create_appimage.sh <version_string>"
  exit 1
fi

APP_DIR="dist/Modan2" # PyInstaller one-dir bundle
OUTPUT_DIR="build_linux"
OUTPUT_FILE="${OUTPUT_DIR}/Modan2-Linux-${VERSION}.AppImage"

# Ensure output directory exists
mkdir -p "$APP_DIR"

# Check if linuxdeploy and appimagetool are available
if ! command -v linuxdeploy &> /dev/null
then
    echo "Error: 'linuxdeploy' command not found. Please install it."
    exit 1
fi

if ! command -v appimagetool &> /dev/null
then
    echo "Error: 'appimagetool' command not found. Please install it."
    exit 1
fi

echo "Creating Linux AppImage for Modan2 v${VERSION}..."

# Create AppRun script
cat << 'EOF' > "${APP_DIR}/AppRun"
#!/bin/bash
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR"
exec "./Modan2" "$@"
EOF
chmod +x "${APP_DIR}/AppRun"

# Create a .desktop file for the AppImage
cat << EOF > "${APP_DIR}/Modan2.desktop"
[Desktop Entry]
Name=Modan2
Exec=AppRun
Icon=Modan2
Type=Application
Categories=Science;Education;
Comment=Morphometric analysis application
EOF

# Copy icon (assuming it's in icons/Modan2.png or use a default)
if [ -f "icons/Modan2.png" ]; then
    cp icons/Modan2.png "${APP_DIR}/Modan2.png"
elif [ -f "icons/Modan2_2.png" ]; then
    cp icons/Modan2_2.png "${APP_DIR}/Modan2.png"
else
    # Create a simple placeholder icon if none exists
    echo "Warning: No icon found, creating placeholder"
    touch "${APP_DIR}/Modan2.png"
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Run linuxdeploy
# --appdir: Path to the AppDir (PyInstaller bundle)
# --output appimage: Specify AppImage output format
# --desktop-file: Path to the .desktop file
# --icon-file: Path to the icon file
linuxdeploy \
  --appdir "$APP_DIR" \
  --output appimage \
  --desktop-file "${APP_DIR}/Modan2.desktop" \
  --icon-file "${APP_DIR}/Modan2.png"

# Check if AppImage was created and rename it
if [ -f "Modan2-x86_64.AppImage" ]; then
  mv "Modan2-x86_64.AppImage" "$OUTPUT_FILE"
  echo "Successfully created AppImage: $OUTPUT_FILE"
else
  echo "Failed to create AppImage."
  exit 1
fi