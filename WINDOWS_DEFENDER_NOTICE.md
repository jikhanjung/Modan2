# Windows Defender False Positive Notice

## Issue
Windows Defender may incorrectly flag Modan2 executables as containing a trojan. This is a **false positive** common with PyInstaller-built applications.

## Why This Happens
1. **Unsigned executable**: The application is not digitally signed with a code signing certificate
2. **PyInstaller packing**: PyInstaller bundles Python runtime and libraries in a way that can trigger heuristic detection
3. **Low reputation**: New executables without established reputation are more likely to be flagged

## Solutions

### For Users

#### Option 1: Add Exclusion (Recommended for Developers)
1. Open Windows Security
2. Go to "Virus & threat protection"
3. Click "Manage settings" under "Virus & threat protection settings"
4. Scroll to "Exclusions" and click "Add or remove exclusions"
5. Add the Modan2 folder or executable

#### Option 2: Restore from Quarantine
1. Open Windows Security
2. Go to "Virus & threat protection"
3. Click "Protection history"
4. Find the Modan2 entry and click "Actions"
5. Select "Restore" and confirm

#### Option 3: Use Portable Version
Instead of the installer, use the portable zip version which may have fewer issues.

### For Developers

#### Build Improvements (Already Implemented)
- Added `--noupx` flag to avoid UPX compression
- Added `--clean` flag to ensure clean builds
- Using one-directory builds instead of one-file when possible

#### Future Improvements
1. **Code Signing Certificate**: Purchase and use a code signing certificate ($200-500/year)
2. **Submit to Microsoft**: Submit false positive report to Microsoft
3. **Build Reputation**: Once more users download and use the application, reputation will improve

## Verification
You can verify the safety of the executable by:
1. Checking the source code on GitHub
2. Building from source yourself
3. Scanning with multiple antivirus engines on VirusTotal

## Report False Positive
Help improve detection by reporting this false positive to Microsoft:
https://www.microsoft.com/en-us/wdsi/submission

## Alternative Installation Methods
1. Build from source: `python build.py`
2. Run directly with Python: `python Modan2.py`
3. Use the Linux AppImage or macOS DMG versions if available
