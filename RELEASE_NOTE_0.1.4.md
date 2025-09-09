# Modan2 v0.1.4 Release Note

## Major Improvements

### 🚀 Automation System
- Built CI/CD pipeline with GitHub Actions
- Cross-platform automatic builds for Windows, Linux, and macOS
- pytest-based automated testing (229 tests)

### 🎨 UI/UX Enhancements
- Added overlay dragging and corner snapping
- Improved splash screen with build information
- Restored 3D landmark index display
- Significantly improved Korean translation

### 🔧 Technical Improvements
- Code modularization (Controller, Helpers, Constants, Widgets separation)
- Support for NumPy 2.0+ and Python 3.12
- Enhanced error handling and logging system
- Migrated to JSON-based settings management

### 🐛 Bug Fixes
- Resolved PCA analysis consistency issues
- Fixed Reset Pose functionality
- Solved Linux/WSL Qt compatibility problems
- Mitigated Windows Defender false positives

### 📚 Documentation
- Added Korean README
- Created development guides (CLAUDE.md, GEMINI.md)
- Added comprehensive development logs

## Downloads

Download the appropriate version for your platform from the [Releases page](https://github.com/jikhanjung/Modan2/releases):

- **Windows**: `Modan2-Windows-Installer-v0.1.4-build*.zip`
- **macOS**: `Modan2-macOS-Installer-v0.1.4-build*.dmg`
- **Linux**: `Modan2-Linux-v0.1.4-build*.AppImage`

For detailed installation instructions, please refer to the [README](https://github.com/jikhanjung/Modan2#installation).

## System Requirements
- Python 3.11 or higher
- NumPy 2.0+
- PyQt5

## Known Issues
- Thumbnail sync delay in WSL environment
- Increased memory usage with large datasets

## Next Version Plans
- Consider PyQt6 migration
- Performance optimization
- Additional file format support