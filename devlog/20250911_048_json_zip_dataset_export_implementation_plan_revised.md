# JSON+ZIP Dataset Export/Import — Revised Plan

Date: 2025-09-11
Issue: #048
Status: Planning (Revised)
Priority: Medium

## Overview

Add a unified JSON+ZIP format that preserves complete datasets (landmarks, variables, wireframe/polygons/baseline, per-object metadata, attached images and 3D models) for reliable backup and sharing. This revision incorporates schema expansion, safer import, better UI integration, and performance safeguards aligned with the current codebase.

## Current State & Gaps

- Existing exports: TPS (LM+ID), Morphologika (LM+vars+images), NTS/CSV (basic LMs). No 3D models in exports; fragmented options; no complete dataset backup.
- Storage: Images/3D stored under `mu.DEFAULT_STORAGE_DIRECTORY` using `MdImage.get_file_path(base)`/`MdThreeDModel.get_file_path(base)`.
- Gaps to address:
  - Include dataset-wide geometry: `wireframe`, `polygons`, `baseline`.
  - Include object fields: `pixels_per_mm`, `sequence`.
  - Allow null landmark coordinates (parser may produce `None`).
  - Safer ZIP extraction (Zip Slip defense), transactional import, clear ID policy.
  - UI: extend existing Import/Export dialogs instead of introducing parallel dialogs.

## Package Layout

```
dataset_export.zip
├── dataset.json                 # Complete metadata + data
├── images/                      # Optional image files
│   ├── <object_id>.<ext>
│   └── ...
└── models/                      # Optional 3D model files
    ├── <object_id>.<ext>
    └── ...
```

- JSON stores relative paths (e.g., `images/123.jpg`) and original filenames in metadata.
- Internal filenames use stable `<object_id>.<ext>` to avoid collisions and simplify import mapping.

## JSON Schema (v1.1)

```jsonc
{
  "format_version": "1.1",
  "export_info": {
    "exported_by": "Modan2 <version>",        // from version.py or MdUtils.BUILD_INFO
    "export_date": "<ISO-8601>",
    "export_format": "JSON+ZIP",
    "include_files": true
  },
  "dataset": {
    "id": 123,                                 // informational only
    "name": "Dataset Name",
    "description": "...",
    "dimension": 2,
    "created_date": "YYYY-MM-DD",
    "modified_date": "YYYY-MM-DD",
    "variables": ["Sex", "Age", ...],
    "landmark_count": 15,
    "object_count": 50,
    "wireframe": [[1,2], [2,3], ...],         // optional
    "polygons": [[1,2,3], ...],               // optional
    "baseline": [1,2]                         // optional (or 3 points)
  },
  "objects": [
    {
      "id": 456,                               // informational only
      "name": "specimen_001",
      "sequence": 1,
      "created_date": "YYYY-MM-DD",
      "pixels_per_mm": 3.2,                    // optional
      "landmarks": [                           // allow nulls per coordinate
        [234.5, 123.6],
        [null, 234.8],
        [456.8, 345.9]
      ],
      "variables": {                           // keys match dataset.variables
        "Sex": "Male",
        "Age": "Adult"
      },
      "files": {
        "image": {
          "path": "images/456.jpg",          // relative in ZIP
          "original_filename": "IMG_0001.jpg",
          "size": 2048576,
          "md5hash": "abcd...",
          "last_modified": "<ISO-8601>"
        },
        "model": {
          "path": "models/456.obj",
          "original_filename": "model_001.obj",
          "size": 1024000,
          "md5hash": "efgh...",
          "last_modified": "<ISO-8601>"
        }
      }
    }
  ]
}
```

ID policy: `dataset.id` and `object.id` are exported for reference only; new IDs are assigned on import. Object file paths in ZIP use exported object ids; importer maps by array index/object name when reconstructing.

## Implementation Plan

### Phase 1 — Core Serialization (JSON)

Target: `MdUtils.py` (new helpers), `MdModel.py` (optional to_dict helpers)

Tasks:
1. Build dataset dictionary from DB, including `wireframe`, `polygons`, `baseline`, `variables`.
2. Build objects with `sequence`, `pixels_per_mm`, `landmarks` (with `None` allowed), `variables` dict, and optional `files` metadata.
3. Collect file references using existing `MdImage.get_file_path(base)` and `MdThreeDModel.get_file_path(base)` relative to `m_app.storage_directory`.
4. Use version from `version.__version__` or `MdUtils.BUILD_INFO`.
5. Optional schema validation step (lightweight type checks, presence of keys).

APIs:
```python
def serialize_dataset_to_json(dataset_id: int, include_files: bool = True, storage_dir: str | None = None) -> dict
def collect_dataset_files(dataset_id: int, storage_dir: str | None = None) -> tuple[list[str], list[str]]  # (images, models)
def validate_json_schema(data: dict) -> tuple[bool, list[str]]  # ok, errors
```

Notes:
- `storage_dir` defaults to `QApplication.instance().storage_directory` or `mu.DEFAULT_STORAGE_DIRECTORY`.
- Variables mapping: object `property_str` is unpacked and paired with `dataset.variablename_list`.

### Phase 2 — ZIP Packaging

Target: `MdUtils.py`

Tasks:
1. Create temp directory (`tempfile.TemporaryDirectory`).
2. Write `dataset.json` using UTF-8.
3. Copy files into `images/` and `models/` using streaming and stable `<object_id>.<ext>` naming.
4. Create ZIP with compression (`zipfile.ZIP_DEFLATED`).
5. Cleanup via context manager.
6. Progress callbacks for large sets (integrate with `ProgressDialog`).

APIs:
```python
def create_zip_package(dataset_id: int, output_path: str, include_files: bool = True, progress_callback=None) -> bool
def copy_files_to_package(file_list: list[str], target_dir: str, progress_callback=None) -> None
def estimate_package_size(dataset_id: int, include_files: bool = True) -> int  # bytes
```

### Phase 3 — UI Integration

Target: `ModanDialogs.py` (extend existing dialogs)

Export — `ExportDatasetDialog` (~5556):
- Add radio: "JSON+ZIP Package (Complete Dataset)".
- Add checkbox: "Include image and model files" (enabled only when JSON+ZIP selected).
- Add estimated size label and reuse existing `ProgressDialog` during packaging.
- On confirm, call `create_zip_package(...)`.

Import — `ImportDatasetDialog`:
- Add radio: "JSON+ZIP" to file type group.
- When selected, open `.zip`, read `dataset.json`, and preview counts/dimension.
- On import, call new import functions (Phase 4) with progress.

Internationalization: Wrap new labels with `self.tr("...")` and include in `translations` on next update.

### Phase 4 — Import (ZIP → DB)

Target: `MdUtils.py` (ZIP/JSON I/O), `ModanDialogs.py` (wiring), `MdModel.py` (constructors)

Tasks:
1. Safe extraction with Zip Slip prevention.
2. Parse and validate `dataset.json` (schema v1.1).
3. Open Peewee transaction: create dataset, then objects; rollback on any failure.
4. Rebuild `wireframe`, `polygons`, `baseline`, variables, and `landmark_str`.
5. Copy files from extracted `images/`/`models/` into `m_app.storage_directory` using `MdImage/MdThreeDModel` helpers.
6. Handle filename collisions by deterministic naming (handled by `<object_id>.<ext>` convention), verify md5 if present.
7. Progress updates via callback.

APIs:
```python
def safe_extract_zip(zip_path: str, dest_dir: str) -> str  # returns extraction root
def read_json_from_zip(zip_path: str) -> dict
def import_dataset_from_zip(zip_path: str, progress_callback=None) -> int  # returns new dataset id
```

Safety:
- Reject entries with absolute paths or `..` sequences.
- Enforce extraction under `dest_dir` only.
- Use Peewee transaction for atomic import.

### Phase 5 — Testing & Validation

Unit Tests (`tests/`, pytest markers):
- `serialize_dataset_to_json` with objects having null coords and variables.
- `collect_dataset_files` with image/model presence/absence.
- `safe_extract_zip` Zip Slip defense cases.

Integration Tests:
- Small dataset export/import (no files).
- Medium dataset with images only.
- Large dataset with images + 3D models (mark `@slow`).
- Roundtrip fidelity: landmarks, variables, wireframe/polygons/baseline, `pixels_per_mm` preserved.
- Corrupted ZIP/invalid JSON handling; graceful errors and no partial DB writes.

## Technical Notes

Versioning:
- Use `version.__version__` or `MdUtils.BUILD_INFO` fields (`PROGRAM_VERSION`, `PROGRAM_BUILD_NUMBER`). Avoid hardcoded strings.

Paths & Filenames:
- JSON paths are relative (`images/...`, `models/...`).
- Internal filenames in ZIP: `<object_id>.<ext>` to avoid collisions.
- On import, actual storage path comes from `MdImage.get_file_path(m_app.storage_directory)` / `MdThreeDModel.get_file_path(...)`.

Performance:
- Use `zipfile` with file path arguments (streaming) instead of loading bytes into memory.
- Progress via callbacks; run heavy work in `QThread`/`QtConcurrent` to keep UI responsive.

Error Handling:
- Validate schema minimally prior to import; collect errors with precise messages.
- If referenced file missing in ZIP, log warning and continue (or configurable policy); keep dataset usable.

Cross-Platform:
- Use `pathlib`/`os.path` for joins; ensure UTF-8 JSON. Test on Windows/macOS/Linux.

Security:
- Strict Zip Slip checks; do not overwrite files outside temp dir during extraction.

## Success Criteria

1. Single ZIP faithfully represents dataset and optional files.
2. Roundtrip preserves all geometry, attributes, and file attachments.
3. Handles 100+ objects / ~1GB attachments with progress and without UI freeze.
4. Clear errors and no partial imports (transactional).
5. Works on Windows/macOS/Linux.

## Future Enhancements

- Batch export (multi-dataset), selective export, compression level options.
- Cloud export backends, schema evolution (v2), checksums verification on import.

## Timeline (Estimate)

- Phase 1–2: 2–3 days
- Phase 3: 1 day
- Phase 4: 2 days
- Phase 5: 1–2 days

Total: 6–8 days

## Next Steps

1. Implement `serialize_dataset_to_json` and `collect_dataset_files` in `MdUtils.py` with tests.
2. Wire up `ExportDatasetDialog` option and call `create_zip_package` with `ProgressDialog`.
3. Implement `safe_extract_zip` and importer, add integration tests for roundtrip.
4. Document usage in README and CHANGELOG.
