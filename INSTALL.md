# Modan2 Installation Guide

**Version**: 0.1.5-alpha.1
**Last Updated**: 2025-10-08

---

## Quick Install

### Windows

1. **Download** `Modan2-Setup.exe` from [Releases](https://github.com/yourusername/Modan2/releases)
2. **Run** the installer
3. **Launch** from Start Menu → Modan2

### macOS

1. **Download** `Modan2.dmg` from [Releases](https://github.com/yourusername/Modan2/releases)
2. **Open** the DMG file
3. **Drag** Modan2.app to Applications folder
4. **Launch** from Applications

### Linux (Ubuntu/Debian)

**Option 1: From Binary** (if available)
```bash
# Download executable
wget https://github.com/yourusername/Modan2/releases/download/v0.1.5-alpha.1/Modan2_linux

# Make executable
chmod +x Modan2_linux

# Run
./Modan2_linux
```

**Option 2: From Source** (recommended)
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-pyqt5 \
  libqt5gui5 libqt5widgets5 libglut3.12 python3-opengl

# Clone repository
git clone https://github.com/yourusername/Modan2.git
cd Modan2

# Install Python dependencies
pip3 install -r requirements.txt

# Run
python3 Modan2.py
```

---

## Detailed Installation

### Windows Installation

#### Method 1: Installer (Recommended)

**Step 1**: Download
- Go to [Releases](https://github.com/yourusername/Modan2/releases)
- Download `Modan2-Setup-{version}.exe`
- File size: ~80-100MB

**Step 2**: Run Installer
- Double-click `Modan2-Setup-{version}.exe`
- If Windows SmartScreen appears:
  - Click "More info"
  - Click "Run anyway"
- Follow installation wizard

**Step 3**: Installation Options
- Installation folder: Default is `C:\Program Files\Modan2`
- Create desktop shortcut: Recommended
- Start menu shortcut: Automatically created

**Step 4**: Launch
- Start Menu → Modan2, OR
- Desktop shortcut

#### Method 2: Portable Executable

**For users who prefer not to install**:

1. Download `Modan2_v{version}_build{build}.exe`
2. Place in desired folder (e.g., `C:\Programs\Modan2\`)
3. Double-click to run
4. No installation required
5. Can run from USB drive

**Note**: First launch may be slower (2-5 seconds)

#### Method 3: From Source

**Requirements**:
- Python 3.10 or later
- Git for Windows

**Steps**:
```cmd
# Clone repository
git clone https://github.com/yourusername/Modan2.git
cd Modan2

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python Modan2.py
```

---

### macOS Installation

#### Method 1: DMG (Recommended)

**Step 1**: Download
- Download `Modan2-{version}.dmg` from Releases
- File size: ~80-100MB

**Step 2**: Open DMG
- Double-click the DMG file
- DMG window appears with Modan2.app

**Step 3**: Install
- Drag Modan2.app to Applications folder
- Eject DMG

**Step 4**: First Launch
- Open Applications folder
- Right-click Modan2.app → Open (first time only)
- Click "Open" in security dialog
- Subsequent launches: Double-click normally

**Security Note**:
- macOS may show "unidentified developer" warning
- This is normal for unsigned applications
- Use Right-click → Open to bypass

#### Method 2: From Source

**Requirements**:
- macOS 10.14 or later
- Homebrew (recommended)
- Xcode Command Line Tools

**Steps**:
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.12

# Clone repository
git clone https://github.com/yourusername/Modan2.git
cd Modan2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python3 Modan2.py
```

---

### Linux Installation

#### Method 1: From Source (Recommended)

**Ubuntu/Debian**:
```bash
# 1. Install system dependencies
sudo apt-get update
sudo apt-get install -y \
  python3 \
  python3-pip \
  python3-venv \
  python3-pyqt5 \
  libqt5gui5 \
  libqt5widgets5 \
  libqt5core5a \
  libxcb-xinerama0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libglut3.12 \
  python3-opengl

# 2. Clone repository
git clone https://github.com/yourusername/Modan2.git
cd Modan2

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Run
python3 Modan2.py
```

**Fedora/RHEL**:
```bash
# System dependencies
sudo dnf install -y \
  python3 \
  python3-pip \
  python3-qt5 \
  qt5-qtbase \
  mesa-libGLU \
  freeglut

# Continue with clone, venv, pip install as above
```

**Arch Linux**:
```bash
# System dependencies
sudo pacman -S python python-pip python-pyqt5 qt5-base freeglut

# Continue with clone, venv, pip install as above
```

#### Method 2: Portable Binary (if available)

```bash
# Download
wget https://github.com/yourusername/Modan2/releases/download/v0.1.5-alpha.1/Modan2_linux

# Make executable
chmod +x Modan2_linux

# Run
./Modan2_linux
```

**Note**: Binary may have library conflicts on some distributions. Use source installation if issues occur.

#### Creating Desktop Entry

After installing from source, create desktop shortcut:

```bash
# Create desktop entry file
cat > ~/.local/share/applications/modan2.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Modan2
Comment=Geometric Morphometrics Analysis
Exec=/path/to/Modan2/venv/bin/python3 /path/to/Modan2/Modan2.py
Icon=/path/to/Modan2/icons/Modan2_2.png
Terminal=false
Categories=Science;Education;
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications
```

Replace `/path/to/Modan2` with actual path.

---

## Troubleshooting

### Windows Issues

**Issue**: Windows Defender blocks installation
```
Cause: PyInstaller executables sometimes flagged as false positive
Solution:
1. Click "More info" on SmartScreen
2. Click "Run anyway"
3. Or: Add exception in Windows Defender
```

**Issue**: Application won't launch (no error)
```
Solutions:
1. Run as administrator (right-click → Run as administrator)
2. Check if antivirus is blocking
3. Try portable executable instead of installer
```

**Issue**: Missing DLL errors
```
Solution: Install Visual C++ Redistributables
Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### macOS Issues

**Issue**: "Modan2 can't be opened because it is from an unidentified developer"
```
Solution:
1. Right-click Modan2.app → Open
2. Click "Open" in dialog
3. Or: System Preferences → Security & Privacy → "Open Anyway"
```

**Issue**: "Modan2 is damaged and can't be opened"
```
Cause: Gatekeeper quarantine attribute
Solution:
sudo xattr -rd com.apple.quarantine /Applications/Modan2.app
```

**Issue**: Application crashes on launch
```
Solution: Check Console.app for error messages
Look for Qt or Python errors
May need to install/update Qt5 via Homebrew
```

### Linux Issues

**Issue**: Qt platform plugin "xcb" error
```
Error: "Could not load the Qt platform plugin "xcb""
Solution:
# Install XCB libraries
sudo apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0

# Or use fix script
python3 fix_qt_import.py
```

**Issue**: OpenGL errors (3D viewer)
```
Solution: Install OpenGL libraries
sudo apt-get install -y libglut3.12 libglu1-mesa freeglut3
```

**Issue**: ImportError for Qt modules
```
Solution: Install PyQt5 system package
sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtopengl
```

**Issue**: Permission denied when running executable
```
Solution: Make file executable
chmod +x Modan2_linux
```

**WSL-Specific**:
```
Issue: Qt errors in WSL
Solution: Use fix_qt_import.py
python3 fix_qt_import.py
```

---

## Verification

### Post-Installation Checks

After installation, verify Modan2 works:

1. **Launch Application**
   - Modan2 window appears
   - No error dialogs

2. **Create Dataset**
   - Click "New Dataset" button
   - Dialog opens
   - Create test dataset

3. **Import Data**
   - File → Import → TPS (or other format)
   - Select sample file
   - Import succeeds

4. **Run Analysis**
   - Analysis → New Analysis
   - Select dataset
   - Run PCA
   - Results display

If all checks pass: ✅ Installation successful!

---

## Uninstallation

### Windows

**If installed with installer**:
1. Control Panel → Programs and Features
2. Find "Modan2"
3. Click Uninstall
4. Follow wizard

**If using portable executable**:
- Simply delete the executable file
- No registry entries or system changes

### macOS

1. Open Applications folder
2. Drag Modan2.app to Trash
3. Empty Trash

**Clean up (optional)**:
```bash
# Remove preferences
rm -rf ~/Library/Preferences/com.paleobytes.modan2*
rm -rf ~/Library/Application\ Support/Modan2
```

### Linux

**If installed from source**:
```bash
# Remove cloned directory
rm -rf /path/to/Modan2

# Remove desktop entry
rm ~/.local/share/applications/modan2.desktop

# Remove config files (optional)
rm -rf ~/.config/Modan2
rm -rf ~/.local/share/Modan2
```

**If using binary**:
```bash
# Remove executable
rm Modan2_linux
```

---

## System Requirements

### Minimum

- **OS**: Windows 10, macOS 10.14, Ubuntu 18.04 (or equivalent)
- **RAM**: 4GB
- **Storage**: 500MB free space
- **Display**: 1280x720

### Recommended

- **OS**: Windows 11, macOS 12+, Ubuntu 22.04+
- **RAM**: 8GB or more
- **Storage**: 2GB free space (for datasets)
- **Display**: 1920x1080 or higher
- **GPU**: Dedicated GPU for 3D models (OpenGL 3.3+)

### Tested Platforms

| Platform | Version | Status |
|----------|---------|--------|
| Windows 10 | 21H2+ | ✅ Tested |
| Windows 11 | 22H2+ | ✅ Tested |
| Ubuntu 20.04 LTS | - | ✅ Tested |
| Ubuntu 22.04 LTS | - | ✅ Tested |
| macOS 10.14 | Mojave | ⚠️ Limited testing |
| macOS 12+ | Monterey+ | ⚠️ Limited testing |

---

## Getting Help

**Installation Issues**:
- Check [Troubleshooting](#troubleshooting) section above
- See [User Guide](docs/USER_GUIDE.md) for detailed documentation
- Report issues on [GitHub](https://github.com/yourusername/Modan2/issues)

**Documentation**:
- [Quick Start Guide](docs/QUICK_START.md) - Get started in 10 minutes
- [User Guide](docs/USER_GUIDE.md) - Comprehensive guide
- [Build Guide](docs/BUILD_GUIDE.md) - Building from source

**Community**:
- GitHub Issues: Bug reports and feature requests
- Email: [your-email@example.com]

---

## Next Steps

After successful installation:

1. **Read** [Quick Start Guide](docs/QUICK_START.md) (10 minutes)
2. **Try** creating your first dataset
3. **Import** sample data (if provided)
4. **Run** basic analysis (PCA)
5. **Explore** features

**Need Help?** See [User Guide](docs/USER_GUIDE.md) for comprehensive documentation.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**For Modan2 Version**: 0.1.5-alpha.1
