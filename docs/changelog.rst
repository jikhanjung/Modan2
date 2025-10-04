Changelog
=========

All notable changes to Modan2 are documented here.

This project follows `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Version 0.1.5-alpha.1 (2025-09-11)
-----------------------------------

Added
~~~~~

**JSON+ZIP Dataset Packaging System**

- Complete dataset backup and sharing with new export/import format
- JSON schema v1.1 with extended metadata (wireframe, polygons, baseline, variables)
- ZIP packaging with support for images and 3D model files
- Structured file layout (dataset.json, images/, models/)
- Lossless round-trip data preservation

**Security and Stability Features**

- Zip Slip attack defense system
- Transaction-based import (automatic rollback on failure)
- File integrity verification (MD5 checksums)
- Safe ZIP extraction (``safe_extract_zip()``)
- JSON schema validation and error reporting

**New API Functions (MdUtils.py)**

- ``serialize_dataset_to_json()`` - Serialize dataset to JSON structure
- ``create_zip_package()`` - File collection and ZIP packaging
- ``import_dataset_from_zip()`` - Safe ZIP-based dataset import
- ``collect_dataset_files()`` - Collect dataset-related file paths
- ``estimate_package_size()`` - Estimate package size
- ``validate_json_schema()`` - JSON schema validation

**User Interface Improvements**

- "JSON+ZIP Package" option in Export Dialog
- "Include image and model files" toggle
- Real-time file size estimation display
- JSON+ZIP format support in Import Dialog
- Progress tracking with progress callbacks

Changed
~~~~~~~

**Existing Export Formats Maintained**

- TPS, NTS, Morphologika, CSV/Excel formats continue to be supported
- JSON+ZIP provided as additional option for complete backups

**Improved File Naming Conventions**

- Files inside ZIP use ``<object_id>.<ext>`` format to avoid conflicts
- Relative paths for platform independence

**Database Handling Improvements**

- Automatic duplicate dataset name resolution ("Dataset (1)", "Dataset (2)", etc.)
- Optimized variable mapping and landmark processing

Fixed
~~~~~

**Cross-Platform Compatibility**

- UTF-8 encoding for Korean filenames
- Unified path handling for Windows, macOS, Linux
- Added file system safety verification

**Memory and Performance Optimization**

- Streaming processing for large files
- Safe temporary file cleanup (context managers)
- Prevention of partial imports on error

Version 0.1.4 (2025-09-10)
---------------------------

Added
~~~~~

**CI/CD and Build System**

- GitHub Actions workflows (automatic build, test, release)
- Cross-platform build support (Windows, Linux, macOS)
- PyInstaller-based automated build script (``build.py``)
- Build number system and centralized version management (``version.py``)

**Testing Infrastructure**

- pytest-based automated test system (229 tests, 13 modules)
- Test categories: unit, integration, performance, GUI, workflow
- CI integration with automatic tests on PR
- Test coverage analysis tools

**UI/UX Features**

- Overlay drag and corner snap functionality
- Overlay title display
- Splash screen (build info and copyright)
- 3D landmark index display restored (using GLUT)
- Improved toolbar button state management
- TreeView usability improvements
- Read-only column context menus

**Documentation**

- Korean README (``README.ko.md``)
- Development guide documents (CLAUDE.md, GEMINI.md)
- Release guide and version management documents
- Windows Defender notice document
- Detailed development logs (devlog directory)

**Internationalization (i18n)**

- Significantly improved Korean translations
- Instant language setting application

**Project Management**

- Refined requirements.txt (tested and verified dependencies)
- Support for Python 3.11+
- OpenGL implementation improvements (font rendering)

Changed
~~~~~~~

**Code Refactoring**

- Modularized color constants (MdConstants.py)
- Unified icon path management
- Standardized logging system
- Optimized import statements

**Analysis System**

- PCA/CVA/MANOVA stability improvements
- Enhanced progress indicators during analysis
- Improved error handling and reporting

**UI Behavior**

- Consistent dialog behavior
- Auto-refresh after data changes
- More intuitive keyboard shortcuts

Fixed
~~~~~

**Critical Bugs**

- Dataset import/export encoding issues
- 3D viewer crashes
- TreeView update timing issues
- Analysis result caching problems

**Platform-Specific Issues**

- WSL/Linux Qt plugin errors (added fix_qt_import.py)
- OpenGL version compatibility
- Font rendering on different platforms

**Data Integrity**

- Landmark coordinate precision maintenance
- Wireframe/polygon data preservation
- Analysis result consistency

Previous Versions
-----------------

Version 0.1.3
~~~~~~~~~~~~~

- Initial public release
- Basic 2D/3D landmark support
- PCA, CVA, MANOVA analysis
- TPS/NTS file import
- SQLite database with Peewee ORM

Version 0.1.2
~~~~~~~~~~~~~

- Added 3D model support (OBJ, PLY, STL)
- Improved 2D/3D viewers
- Dataset hierarchy

Version 0.1.1
~~~~~~~~~~~~~

- Basic morphometric analysis
- Procrustes superimposition
- Simple data management

Version 0.1.0
~~~~~~~~~~~~~

- Initial development version
- Proof of concept

Upcoming Features
-----------------

Planned for Future Releases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Missing Landmark Support (Phase 3-5)**

- Advanced imputation methods (TPS warping, regression)
- Confidence intervals for estimated positions
- Multiple imputation for uncertainty quantification
- Missing-aware statistical methods (PPCA, EM-based CVA)

**Enhanced Analysis**

- Partial Least Squares (PLS)
- Phylogenetic comparative methods
- Disparity analysis
- Asymmetry analysis

**User Interface**

- Dark mode theme
- Customizable toolbar
- Advanced plot customization
- Interactive 3D landmark editing

**Performance**

- GPU-accelerated Procrustes
- Lazy loading for large datasets
- Caching improvements
- Parallel processing support

**Integration**

- R integration (export to geomorph, Morpho)
- Python API for scripting
- Command-line interface
- Plugin system

See the `GitHub Issues <https://github.com/jikhanjung/Modan2/issues>`_ page for full roadmap and feature requests.
