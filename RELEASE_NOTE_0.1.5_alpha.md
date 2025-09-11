# Modan2 v0.1.5 Alpha Release Note

**⚠️ Alpha Version Notice: This version is provided for testing purposes. Thorough validation is recommended before using in actual research.**

## Major New Features

### 📦 JSON+ZIP Dataset Packaging System
Introducing a revolutionary export/import system for complete dataset backup and sharing.

**Key Features:**
- **Complete Data Preservation**: Includes landmarks, variables, wireframes, polygons, baselines, images, and 3D models
- **Structured Packaging**: Organized folder structure within ZIP (dataset.json, images/, models/)
- **Lossless Roundtrip**: Perfect data preservation through Export → Import workflow
- **Secure Import**: Zip Slip attack prevention and transaction-based rollback
- **Progress Tracking**: Real-time progress indicators and size estimation for large datasets

**File Structure Example:**
```
my_dataset.zip
├── dataset.json          # Complete metadata + landmarks + variables
├── images/              # Image files
│   ├── 123.jpg
│   └── 456.png  
└── models/              # 3D model files
    ├── 123.obj
    └── 456.ply
```

**Comparison with Existing Formats:**
- **TPS/NTS**: Landmarks only → **JSON+ZIP**: All data + files
- **Morphologika**: Landmarks + variables + images → **JSON+ZIP**: + 3D models + geometric structures
- **CSV/Excel**: Basic data only → **JSON+ZIP**: Complete dataset archive

### 🛡️ Enhanced Security & Reliability
- **Zip Slip Defense**: System protection against malicious ZIP files
- **Atomic Transactions**: Automatic database rollback on import failure
- **File Integrity Verification**: MD5 checksum validation
- **Conflict Resolution**: Automatic numbering for duplicate dataset names (e.g., "Dataset (1)")

### 🎯 Improved User Experience
- **Extended Export Dialog**: "JSON+ZIP Package" option added to existing dialog
- **File Inclusion Toggle**: Choose whether to include images/3D models
- **Size Estimation**: Display estimated file size before export
- **Import Preview**: Preview ZIP contents (object count, dimensions, etc.)

## Technical Improvements

### 📋 New API Functions (MdUtils.py)
- `serialize_dataset_to_json()`: Serialize dataset to JSON structure
- `create_zip_package()`: File collection and ZIP packaging
- `import_dataset_from_zip()`: Secure ZIP-based dataset import
- `collect_dataset_files()`: Dataset-related file path collection
- `safe_extract_zip()`: Security-verified ZIP extraction
- `validate_json_schema()`: JSON schema validation and error reporting

### 🏗️ JSON Schema v1.1
Extended schema including complete dataset metadata:
```json
{
  "format_version": "1.1",
  "dataset": {
    "wireframe": [[1,2], [2,3], ...],    // Wireframe information
    "polygons": [[1,2,3], ...],          // Polygon information  
    "baseline": [1,2],                   // Baseline (2 or 3 points)
    "variables": ["Sex", "Age", ...]     // Variable list
  },
  "objects": [
    {
      "landmarks": [[x,y], [null,y], ...], // Null coordinate support
      "pixels_per_mm": 3.2,                // Scale information
      "sequence": 1,                       // Object order
      "files": {                           // Attached file metadata
        "image": {...},
        "model": {...}
      }
    }
  ]
}
```

### 💾 Cross-Platform Compatibility
- UTF-8 encoding for Korean filename support
- Unified Windows, macOS, Linux path handling
- File system safety validation

## 📚 Documentation
- **Implementation Plan**: `devlog/20250911_047_json_zip_dataset_export_implementation_plan.md`
- **Revised Plan**: `devlog/20250911_048_json_zip_dataset_export_implementation_plan_revised.md`
- Detailed API documentation and usage examples

## Downloads

**⚠️ Warning: Alpha version is for testing purposes only.**

Download the appropriate version for your platform from the [Releases page](https://github.com/jikhanjung/Modan2/releases):

- **Windows**: `Modan2-Windows-Installer-v0.1.5-alpha-build*.zip`
- **macOS**: `Modan2-macOS-Installer-v0.1.5-alpha-build*.dmg`
- **Linux**: `Modan2-Linux-v0.1.5-alpha-build*.AppImage`

## System Requirements
- Python 3.11 or higher
- NumPy 2.0+
- PyQt5
- Adequate disk space (for large dataset Export/Import)

## Usage

### Dataset Export
1. Menu: **Dataset > Export Dataset**
2. Select **"JSON+ZIP Package (Complete Dataset)"**
3. Check **"Include image and model files"** (if needed)
4. Choose save location and Export

### Dataset Import  
1. Menu: **Dataset > Import Dataset**
2. Select **"JSON+ZIP"** format
3. Select ZIP file and Import

## Known Limitations
- Very large datasets (1GB+) may increase memory usage
- Performance degradation possible on network drives during import
- Some antivirus software may cause delays due to ZIP file scanning

## Feedback and Issue Reporting
Please report any issues or improvements found while using this alpha version:
- **GitHub Issues**: [https://github.com/jikhanjung/Modan2/issues](https://github.com/jikhanjung/Modan2/issues)
- **Email**: honestjung@gmail.com

## Upcoming Plans (v0.1.5 Stable)
- User feedback integration and bug fixes
- Performance optimization (large file handling)
- Additional validation testing and documentation
- Batch export functionality (multiple datasets simultaneously)

---

**Note**: The new JSON+ZIP format in this version is fully compatible with existing TPS, Morphologika, and NTS formats. Existing formats continue to be supported, and JSON+ZIP serves as an additional option for complete backup and sharing.