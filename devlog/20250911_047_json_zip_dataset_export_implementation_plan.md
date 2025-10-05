# JSON+ZIP Dataset Export Implementation Plan

**Date**: 2025-09-11
**Issue**: #047
**Status**: Planning Phase
**Priority**: Medium

## Overview

Implement a comprehensive dataset export functionality that packages all dataset information (landmarks, variables, metadata) along with associated files (images, 3D models) into a single ZIP archive with JSON metadata format.

## Current State Analysis

### Existing Export Functionality
- **TPS Export**: Only landmarks and specimen IDs (no variables, no files)
- **Morphologika Export**: Landmarks + variables + images (no 3D models)
- **NTS/CSV Export**: Basic landmark data only
- **File Storage**: Images and 3D models copied to internal storage (`~/PaleoBytes/Modan2/data/`)

### Current Limitations
1. No unified export format that includes all data types
2. 3D models never exported with datasets
3. Fragmented export options (different formats support different features)
4. No complete dataset backup/sharing capability

## Proposed Solution

### JSON+ZIP Package Format

**Archive Structure:**
```
dataset_export.zip
├── dataset.json          # Complete dataset metadata and landmark data
├── images/              # Image files referenced by objects
│   ├── specimen_001.jpg
│   ├── specimen_002.png
│   └── ...
└── models/              # 3D model files referenced by objects
    ├── specimen_001.obj
    ├── specimen_002.ply
    └── ...
```

### JSON Schema Design

```json
{
  "format_version": "1.0",
  "export_info": {
    "exported_by": "Modan2 v0.1.4",
    "export_date": "2025-09-11T10:30:00Z",
    "export_format": "JSON+ZIP",
    "include_files": true
  },
  "dataset": {
    "id": 123,
    "name": "My Research Dataset",
    "description": "Morphometric analysis of specimens",
    "dimension": 2,
    "created_date": "2025-01-15",
    "modified_date": "2025-09-11",
    "variables": ["Sex", "Age", "Species", "Location"],
    "landmark_count": 15,
    "object_count": 50
  },
  "objects": [
    {
      "id": 456,
      "name": "specimen_001",
      "created_date": "2025-01-15",
      "landmarks": [
        [234.5, 123.6],
        [345.7, 234.8],
        [456.8, 345.9]
      ],
      "variables": {
        "Sex": "Male",
        "Age": "Adult",
        "Species": "Homo sapiens",
        "Location": "Site A"
      },
      "files": {
        "image": {
          "path": "images/specimen_001.jpg",
          "original_filename": "IMG_0001.jpg",
          "size": 2048576,
          "md5hash": "abcd1234..."
        },
        "model": {
          "path": "models/specimen_001.obj",
          "original_filename": "model_001.obj",
          "size": 1024000,
          "md5hash": "efgh5678..."
        }
      }
    }
  ]
}
```

## Implementation Plan

### Phase 1: Core JSON Serialization

**Target Files:**
- `MdUtils.py` - Add JSON serialization functions
- `MdModel.py` - Add export methods to database models

**Tasks:**
1. Create `serialize_dataset_to_json()` function
2. Implement dataset metadata extraction
3. Implement object data extraction with landmarks and variables
4. Handle file reference collection
5. Add proper error handling and validation

**Key Functions to Implement:**
```python
def serialize_dataset_to_json(dataset_id: int, include_files: bool = True) -> dict
def collect_dataset_files(dataset_id: int) -> tuple[list, list]  # images, models
def validate_json_schema(data: dict) -> bool
```

### Phase 2: ZIP Packaging

**Target Files:**
- `MdUtils.py` - Add ZIP packaging functions

**Tasks:**
1. Create temporary directory for package assembly
2. Generate JSON file
3. Copy image files to `images/` subdirectory
4. Copy 3D model files to `models/` subdirectory
5. Create ZIP archive
6. Clean up temporary files
7. Progress reporting for large datasets

**Key Functions to Implement:**
```python
def create_zip_package(dataset_id: int, output_path: str, progress_callback=None) -> bool
def copy_files_to_package(file_list: list, target_dir: str) -> None
def cleanup_temp_directory(temp_dir: str) -> None
```

### Phase 3: Export Dialog Integration

**Target Files:**
- `ModanDialogs.py` - Modify `ExportDatasetDialog`

**Tasks:**
1. Add "JSON+ZIP Package" radio button option
2. Add "Include Files" checkbox (enabled only for JSON+ZIP)
3. Update dialog layout and validation
4. Add file size estimation and progress bar
5. Integrate with ZIP packaging functionality

**UI Changes:**
```python
# Add to ExportDatasetDialog
self.rbJSONZip = QRadioButton("JSON+ZIP Package (Complete Dataset)")
self.chkIncludeFiles = QCheckBox("Include image and model files")
self.lblEstimatedSize = QLabel("Estimated size: calculating...")
self.progressBar = QProgressBar()
```

### Phase 4: Import Functionality

**Target Files:**
- `ModanDialogs.py` - Create `ImportJSONZipDialog`
- `ModanComponents.py` - Add JSON+ZIP reader class

**Tasks:**
1. Create ZIP extraction functionality
2. Parse and validate JSON schema
3. Create dataset and objects in database
4. Import files to internal storage
5. Handle conflicts and duplicates
6. Progress reporting for import process

### Phase 5: Testing and Validation

**Test Cases:**
1. Export small dataset (< 10 objects, no files)
2. Export medium dataset (50 objects, with images)
3. Export large dataset (200+ objects, images + 3D models)
4. Export/Import roundtrip validation
5. Error handling (corrupted ZIP, invalid JSON, missing files)
6. Cross-platform compatibility testing

## Technical Considerations

### File Path Handling
- Use relative paths in JSON (e.g., `images/specimen_001.jpg`)
- Handle file name conflicts (append numbers if needed)
- Preserve original file extensions
- Generate unique internal names if needed

### Performance Optimization
- Stream large files during ZIP creation
- Progress callbacks for long operations
- Memory-efficient processing for large datasets
- Background processing option

### Error Handling
- Validate JSON schema before import
- Handle missing files gracefully
- Provide detailed error messages
- Rollback capability for failed imports

### Cross-Platform Support
- Use `pathlib` for path handling
- Handle different file system encodings
- Test on Windows, macOS, Linux

## File Locations for Implementation

### Core Files to Modify:
1. **`/mnt/d/projects/Modan2/MdUtils.py`**
   - JSON serialization functions
   - ZIP packaging functions
   - File collection utilities

2. **`/mnt/d/projects/Modan2/ModanDialogs.py`**
   - Modify `ExportDatasetDialog` (lines ~5600-5800)
   - Add `ImportJSONZipDialog` class

3. **`/mnt/d/projects/Modan2/MdModel.py`**
   - Add export helper methods to database models
   - File path resolution methods

4. **`/mnt/d/projects/Modan2/Modan2.py`**
   - Add import menu item
   - Integration with main application

### Dependencies to Add:
- `zipfile` (built-in Python module)
- `json` (built-in Python module)
- `tempfile` (built-in Python module)
- `pathlib` (built-in Python module)

## Success Criteria

1. **Complete Export**: Single ZIP file contains all dataset information and files
2. **Roundtrip Fidelity**: Export → Import preserves all data exactly
3. **Performance**: Handle datasets with 100+ objects and 1GB+ files efficiently
4. **User Experience**: Clear progress indication and error messages
5. **Compatibility**: Works across Windows, macOS, Linux platforms

## Future Enhancements (Post-Implementation)

1. **Batch Export**: Export multiple datasets in one operation
2. **Selective Export**: Choose specific objects or variables to include
3. **Compression Options**: Different compression levels for ZIP files
4. **Cloud Integration**: Direct export to cloud storage services
5. **Format Versioning**: Support for different JSON schema versions

## Risk Assessment

**Medium Risk Items:**
- Large file handling (memory usage)
- Cross-platform file path compatibility
- Database transaction handling during import

**Low Risk Items:**
- JSON serialization (well-established libraries)
- ZIP file creation (standard Python functionality)
- UI integration (follows existing patterns)

## Timeline Estimate

- **Phase 1-2**: 2-3 days (Core functionality)
- **Phase 3**: 1 day (UI integration)
- **Phase 4**: 2 days (Import functionality)
- **Phase 5**: 1-2 days (Testing and refinement)

**Total Estimated Time**: 6-8 days of development work

---

**Next Steps:**
1. Begin Phase 1 implementation with JSON serialization
2. Create comprehensive test cases
3. Validate design with sample datasets
4. Iterative development and testing
