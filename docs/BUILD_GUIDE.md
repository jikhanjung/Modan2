# Modan2 Build Guide

**Version**: 0.1.5-alpha.1
**Last Updated**: 2025-10-08

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Build Process](#build-process)
4. [Platform-Specific Instructions](#platform-specific-instructions)
5. [Troubleshooting](#troubleshooting)
6. [Build Verification](#build-verification)

---

## Overview

This guide explains how to build Modan2 executables and installers from source code.

### Build Outputs

**Automated by `build.py`**:
1. **One-File Executable**: Single portable executable
   - Windows: `Modan2_v{VERSION}_build{BUILD}.exe`
   - Linux: `Modan2_v{VERSION}_build{BUILD}_linux`
   - macOS: `Modan2_v{VERSION}_build{BUILD}_macos`

2. **One-Directory Bundle**: Folder with executable and dependencies
   - All platforms: `dist/Modan2/`
   - Contains main executable + libraries

3. **Windows Installer** (Windows only):
   - Created with InnoSetup
   - Output: `Output/Modan2-Setup-{VERSION}.exe`

---

## Prerequisites

### All Platforms

**Required**:
- Python 3.10 or later
- Git
- All requirements from `requirements.txt`

```bash
pip install -r requirements.txt
```

**Additional Build Tools**:
```bash
pip install pyinstaller semver
```

### Windows-Specific

**Required**:
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (for installer creation)
- Add ISCC.exe to PATH or use full path

**Installation**:
1. Download Inno Setup installer
2. Run installer (default location: `C:\Program Files (x86)\Inno Setup 6\`)
3. Add to PATH:
   - System Properties → Environment Variables
   - Add `C:\Program Files (x86)\Inno Setup 6\` to PATH

### Linux-Specific

**System Packages**:
```bash
sudo apt-get install -y \
  python3-dev \
  libxcb-xinerama0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libqt5gui5 \
  libqt5widgets5 \
  python3-pyqt5 \
  libglut-dev \
  python3-opengl
```

### macOS-Specific

**Required**:
- Xcode Command Line Tools
- Homebrew (recommended)

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.12

# Install Qt5
brew install qt@5
```

---

## Build Process

### Quick Build

**Automated Build** (recommended):
```bash
# From project root
python build.py
```

This will:
1. Create build info JSON
2. Build one-file executable
3. Build one-directory bundle
4. Copy example dataset
5. Run InnoSetup (Windows only)

### Manual Build Steps

If you need more control:

```bash
# 1. Create build info
python -c "import json; json.dump({'version': '0.1.5-alpha.1', 'build_number': 'manual'}, open('build_info.json', 'w'))"

# 2. Run PyInstaller
pyinstaller --name=Modan2 \
  --onefile \
  --noconsole \
  --add-data="icons/*.png:icons" \
  --add-data="translations/*.qm:translations" \
  --add-data="migrations/*:migrations" \
  --add-data="build_info.json:." \
  --icon=icons/Modan2_2.png \
  --noupx \
  --clean \
  main.py
```

### Build Configuration

**Version** is read from `version.py`:
```python
__version__ = "0.1.5-alpha.1"
```

**Build Number**:
- Local builds: `"local"`
- CI/CD builds: `BUILD_NUMBER` environment variable

---

## Platform-Specific Instructions

### Building on Windows

**Step 1**: Ensure prerequisites installed
```cmd
python --version   # Should be 3.10+
pip --version
ISCC.exe /?        # InnoSetup compiler
```

**Step 2**: Build
```cmd
cd Modan2
python build.py
```

**Expected Output**:
```
Building Modan2 version 0.1.5-alpha.1
Build number: local
Build date: 20251008
Created build_info.json
PyInstaller completed successfully
Executable created: dist\Modan2_v0.1.5-alpha.1_buildlocal.exe
PyInstaller completed successfully
Executable created: dist\Modan2\Modan2.exe
Copied ExampleDataset to dist/ExampleDataset
Installer created with version 0.1.5-alpha.1
Build completed for version 0.1.5-alpha.1
```

**Build Artifacts**:
- `dist/Modan2_v0.1.5-alpha.1_buildlocal.exe` - Portable executable
- `dist/Modan2/` - Directory bundle
- `Output/Modan2-Setup-0.1.5-alpha.1.exe` - Installer

**Testing**:
```cmd
# Test one-file executable
dist\Modan2_v0.1.5-alpha.1_buildlocal.exe

# Test installer
Output\Modan2-Setup-0.1.5-alpha.1.exe
```

### Building on Linux

**Step 1**: Install dependencies
```bash
# System packages
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip python3-pyqt5 \
  libxcb-xinerama0 libqt5gui5 libglut-dev python3-opengl

# Python packages
pip3 install -r requirements.txt
pip3 install pyinstaller semver
```

**Step 2**: Build
```bash
cd Modan2
python3 build.py
```

**Expected Output**:
```
Building Modan2 version 0.1.5-alpha.1
Build number: local
Build date: 20251008
Created build_info.json
PyInstaller completed successfully
Executable created: dist/Modan2_v0.1.5-alpha.1_buildlocal_linux
PyInstaller completed successfully
Executable created: dist/Modan2/Modan2
Inno Setup is Windows-only, skipping...
Build completed for version 0.1.5-alpha.1
```

**Build Artifacts**:
- `dist/Modan2_v0.1.5-alpha.1_buildlocal_linux` - Portable executable
- `dist/Modan2/` - Directory bundle

**Testing**:
```bash
# Make executable
chmod +x dist/Modan2_v0.1.5-alpha.1_buildlocal_linux

# Test
./dist/Modan2_v0.1.5-alpha.1_buildlocal_linux

# Or test directory bundle
./dist/Modan2/Modan2
```

**Packaging** (optional):
Create a simple installation script:

```bash
# Create install script
cat > install.sh << 'EOF'
#!/bin/bash
# Modan2 Installation Script

echo "Installing Modan2..."

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pyqt5 libqt5gui5 libglut3.12

# Copy executable
sudo cp Modan2 /usr/local/bin/
sudo chmod +x /usr/local/bin/Modan2

# Create desktop entry
cat > ~/.local/share/applications/modan2.desktop << 'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=Modan2
Comment=Geometric Morphometrics Analysis
Exec=/usr/local/bin/Modan2
Icon=modan2
Terminal=false
Categories=Science;Education;
DESKTOP

echo "Installation complete!"
echo "Launch Modan2 from applications menu or run: Modan2"
EOF

chmod +x install.sh
```

### Building on macOS

**Step 1**: Install prerequisites
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Qt
brew install python@3.12 qt@5

# Install Python packages
pip3 install -r requirements.txt
pip3 install pyinstaller semver
```

**Step 2**: Build
```bash
cd Modan2
python3 build.py
```

**Expected Output**:
```
Building Modan2 version 0.1.5-alpha.1
Build number: local
Build date: 20251008
Created build_info.json
PyInstaller completed successfully
Executable created: dist/Modan2_v0.1.5-alpha.1_buildlocal_macos
PyInstaller completed successfully
Executable created: dist/Modan2/Modan2
Inno Setup is Windows-only, skipping...
Build completed for version 0.1.5-alpha.1
```

**Build Artifacts**:
- `dist/Modan2_v0.1.5-alpha.1_buildlocal_macos` - Portable executable
- `dist/Modan2/` - Directory bundle

**Testing**:
```bash
# Make executable
chmod +x dist/Modan2_v0.1.5-alpha.1_buildlocal_macos

# Test
./dist/Modan2_v0.1.5-alpha.1_buildlocal_macos
```

**Creating DMG** (optional):

```bash
# Create DMG (requires create-dmg)
brew install create-dmg

create-dmg \
  --volname "Modan2 Installer" \
  --volicon "icons/Modan2_2.png" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "Modan2.app" 200 190 \
  --hide-extension "Modan2.app" \
  --app-drop-link 600 185 \
  "Modan2-0.1.5-alpha.1.dmg" \
  "dist/"
```

---

## Troubleshooting

### PyInstaller Issues

**Error**: `ModuleNotFoundError` during build
```
Solution: Add missing module to hidden imports
pyinstaller --hidden-import=module_name ...
```

**Error**: `FileNotFoundError: icons/*.png`
```
Solution: Verify icons directory exists and contains PNG files
ls icons/*.png
```

**Error**: Executable too large (> 100MB)
```
Solution: This is normal for PyQt5 applications
- One-file mode includes Python + Qt + all dependencies
- Typical size: 80-150MB
- Directory mode distributes size across multiple files
```

### Windows-Specific Issues

**Error**: `ISCC.exe not found`
```
Solution:
1. Install Inno Setup from https://jrsoftware.org/isdl.php
2. Add to PATH or use full path in build.py
3. Or skip installer creation (only affects installer, not executable)
```

**Warning**: Windows Defender flags executable
```
Cause: PyInstaller executables sometimes trigger false positives
Solutions:
1. Add exception in Windows Defender
2. Submit to Microsoft for analysis
3. Code signing (future - requires certificate)
```

### Linux-Specific Issues

**Error**: `ImportError: libQt5Core.so.5: cannot open shared object file`
```
Solution: Install Qt5 libraries
sudo apt-get install libqt5core5a libqt5gui5 libqt5widgets5
```

**Error**: `Could not load Qt platform plugin "xcb"`
```
Solution: Install XCB libraries
sudo apt-get install libxcb-xinerama0 libxcb-icccm4
```

**Error**: Qt plugin conflicts (WSL)
```
Solution: Use fix_qt_import.py
python3 fix_qt_import.py
```

### macOS-Specific Issues

**Error**: `"Modan2" cannot be opened because it is from an unidentified developer`
```
Solution: Allow in Security & Privacy
1. System Preferences → Security & Privacy
2. Click "Open Anyway"
Or: Right-click → Open → Open
```

**Error**: Code signing required
```
Note: macOS 10.15+ requires notarization for distribution
For testing: Right-click → Open
For distribution: Requires Apple Developer account
```

---

## Build Verification

### Smoke Test Checklist

After building, verify the executable works:

```bash
# 1. Executable launches
./Modan2  # or Modan2.exe

# 2. Main window appears
# Visual check: Main window with menu bar and panels

# 3. Basic functionality
# - Create new dataset
# - Import sample TPS file
# - View object
# - Run PCA
# - Export dataset
```

### Automated Testing

```bash
# Run pytest on source (before build)
pytest

# Check build output exists
ls -lh dist/
```

### File Size Expectations

| Platform | One-File | One-Dir (total) |
|----------|----------|-----------------|
| Windows | 80-120MB | 100-150MB |
| Linux | 70-100MB | 90-120MB |
| macOS | 80-120MB | 100-150MB |

**Large size is normal** due to:
- Python interpreter
- PyQt5 framework
- NumPy, SciPy, OpenCV libraries
- All dependencies bundled

### Build Artifacts Checklist

**After successful build, you should have**:

**Windows**:
- [ ] `dist/Modan2_v{VERSION}_build{BUILD}.exe` (one-file)
- [ ] `dist/Modan2/Modan2.exe` (directory bundle)
- [ ] `dist/Modan2/` contains DLLs and data files
- [ ] `Output/Modan2-Setup-{VERSION}.exe` (installer)
- [ ] `build_info.json` created

**Linux**:
- [ ] `dist/Modan2_v{VERSION}_build{BUILD}_linux` (one-file)
- [ ] `dist/Modan2/Modan2` (directory bundle)
- [ ] `dist/Modan2/` contains libraries and data files
- [ ] `build_info.json` created

**macOS**:
- [ ] `dist/Modan2_v{VERSION}_build{BUILD}_macos` (one-file)
- [ ] `dist/Modan2/Modan2` (directory bundle)
- [ ] `dist/Modan2/` contains frameworks and data files
- [ ] `build_info.json` created

---

## Advanced Topics

### CI/CD Build

For automated builds in GitHub Actions or similar:

```yaml
name: Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest, macos-latest]

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller semver

    - name: Build
      run: python build.py
      env:
        BUILD_NUMBER: ${{ github.run_number }}

    - name: Upload artifacts
      uses: actions/upload-artifact@v2
      with:
        name: Modan2-${{ matrix.os }}
        path: dist/
```

### Custom Build Configuration

Edit `build.py` to customize:

```python
# Change application name
NAME = "MyMorphometrics"

# Add hidden imports
hidden_imports = [
    'sklearn.utils._typedefs',
    'sklearn.neighbors._partition_nodes',
]

# Modify PyInstaller args
onefile_args = [
    f"--name={NAME}",
    "--onefile",
    "--noconsole",
    f"--hidden-import={','.join(hidden_imports)}",
    # ... rest of args
]
```

### Reducing Executable Size

**Techniques**:

1. **Use one-directory mode** (distributes size)
2. **Exclude unused libraries**:
   ```python
   --exclude-module=matplotlib  # if not needed
   ```
3. **Use UPX compression** (risky - may trigger antivirus):
   ```python
   # Remove --noupx from build.py
   ```
4. **External data files** (don't bundle large files):
   ```python
   # Don't add-data large example datasets
   ```

---

## Support

**Build Issues**:
- Check [Troubleshooting](#troubleshooting) section
- Search [PyInstaller documentation](https://pyinstaller.org/)
- Report on [GitHub Issues](https://github.com/yourusername/Modan2/issues)

**Platform-Specific Help**:
- Windows: Check Inno Setup logs
- Linux: Check terminal output for missing libraries
- macOS: Check Console.app for errors

---

## Appendix

### Build Script Details

**build.py** performs:

1. **Version Detection**: Reads from `version.py`
2. **Build Info**: Creates `build_info.json` with version, date, platform
3. **PyInstaller (One-File)**: Creates portable single executable
4. **PyInstaller (One-Directory)**: Creates folder with executable + libs
5. **Example Data**: Copies ExampleDataset to dist/
6. **InnoSetup** (Windows): Creates installer

**Key Files**:
- `build.py` - Main build script
- `version.py` - Version source of truth
- `build_info.json` - Generated build metadata
- `InnoSetup/Modan2.iss` - Installer configuration (Windows)
- `build/file_version_info.txt` - Windows version resource template

### Version Management

**Updating Version**:

Edit `version.py`:
```python
__version__ = "0.2.0"
```

Build automatically uses this version:
```bash
python build.py
# Output: Building Modan2 version 0.2.0
```

**Semantic Versioning**:
- Major.Minor.Patch (e.g., 1.2.3)
- Pre-release: 1.0.0-alpha, 1.0.0-beta
- Build metadata: 1.0.0+20251008

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**For Modan2 Version**: 0.1.5-alpha.1
