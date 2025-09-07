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

# Create a .desktop file for the AppImage
# This is a minimal example, you might want to customize it further
cat << EOF > "${APP_DIR}/Modan2.desktop"
[Desktop Entry]
Name=Modan2
Exec=AppRun
Icon=Modan2
Type=Application
Categories=Science;Education;
EOF

# Copy icon (assuming it's in icons/Modan2.png)
# You might need to adjust the path to your icon
cp icons/Modan2.png "${APP_DIR}/Modan2.png"

# Run linuxdeploy
# --appdir: Path to the AppDir (PyInstaller bundle)
# --output appimage: Specify AppImage output format
# --desktop-file: Path to the .desktop file
# --icon-file: Path to the icon file (Corrected from --icon)
# --output: Output filename (optional, linuxdeploy can name it)
linuxdeploy \
  --appdir "$APP_DIR" \
  --output appimage \
  --desktop-file "${APP_DIR}/Modan2.desktop" \
  --icon-file "${APP_DIR}/Modan2.png" \
  --output "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
  echo "Successfully created AppImage: $OUTPUT_FILE"
else
  echo "Failed to create AppImage."
  exit 1
fi