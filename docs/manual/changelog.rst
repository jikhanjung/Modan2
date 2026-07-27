Changelog
=========

All notable changes to Modan2 are documented here.

This project follows `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Version 0.2.0-alpha.2 (2026-07-24)
-----------------------------------

A hardening release for the 0.2 alpha: several data-loss and crash fixes found by
a file-I/O/security audit and by fuzzing, plus a large internal quality push
(cross-platform CI, type checking, and a complexity-refactoring campaign).

Fixed
~~~~~

- **Semi-landmark curves are no longer lost on ZIP export/import.** A dataset
  packaged to ``.zip`` and re-imported dropped its curve scheme and every traced
  curve; the package format now carries them (manifest schema 1.2, older packages
  still import).
- **Polygons are no longer dropped when importing a file** (a Morphologika file
  with a ``[polygons]`` block imported with no polygons).
- **Missing landmarks survive ZIP round-trips correctly**, stored with the app's
  "Missing" marker instead of the string ``None``.
- **NTS files now report the correct landmark count** (it was always 0).
- **Korean (and other non-Latin) chart text renders instead of showing boxes**,
  via a per-glyph font fallback built from the fonts installed on the machine.
- **Landmark file readers tolerate non-ASCII specimen names on any locale**
  (e.g. cp949 files on a UTF-8 system and vice-versa).
- **A malformed input file no longer crashes a reader** (fuzzing surfaced a
  Morphologika crash on a bare ``[``; parsers now fail with a clear error).
- **Data Exploration no longer crashes when an analysis has fewer components than
  the selected axis** (e.g. a 3rd axis on a 2-component PCA).
- **A requested CVA/MANOVA that fails is reported**, instead of claiming success
  while silently saving nothing.
- **Saving an object is now atomic** — a failure while attaching its image/3D
  model can no longer leave a half-written object.
- **More dialog actions surface errors instead of silently closing the window**,
  with a global crash handler as a backstop.
- Importing a crafted dataset package can no longer copy files from outside the
  package (path-traversal hardening).

Added
~~~~~

- **Export semi-landmark curves to TPS** (``CURVES=``), symmetric to the existing
  import.

Changed / Internal
~~~~~~~~~~~~~~~~~~~

- Cross-platform CI (Linux/Windows/macOS) with an import smoke test; linting,
  formatting, type-checking (mypy), a dependency CVE scan, and a coverage floor
  are now enforced.
- A complexity-refactoring campaign brought the worst application function from a
  cyclomatic complexity of 56 down to 21, with characterization tests added for
  the viewers.

Version 0.2.0-alpha.1 (2026-07-23)
-----------------------------------

Semi-landmark curves: trace a curve on a specimen and have it resampled into
evenly-spaced semi-landmarks for analysis, with edge-snapping auto-detection.
First alpha of the 0.2 series.

Added
~~~~~

- **Semi-landmark curves.** Define curves for a dataset — how many semi-landmarks
  each carries — then trace them on each specimen. The traced curve is resampled
  into evenly-spaced points along its length, and analysis treats those points
  like ordinary landmarks. Fixed (anatomical) landmarks keep their positions and
  indices; the semi-landmarks follow after them. The raw trace is kept with the
  specimen, so you can re-trace or change the count at any time. A dataset can be
  analyzed with only semi-landmarks (no fixed landmarks) as well.
- **Snap to curve — edge auto-detection.** While tracing, the curve snaps to the
  strongest image edge between your clicks (a "live-wire"), so a clean outline
  needs only a few clicks. On by default in curve mode; uncheck **Snap to curve**
  for a plain hand trace. Enter accepts the trace, Esc cancels.
- **Smooth curve.** Snapped traces are smoothed to remove the pixel staircase, so
  the semi-landmarks sit on a clean curve while the points you clicked stay put.
  Toggle with the **Smooth curve** checkbox.
- **Edit a traced curve.** Select a curve to adjust it — drag a point, click the
  line to add one, right-click to delete a point or the whole curve. Snapped
  curves are edited by their clicked anchors and re-snap to the edge live as you
  drag.
- **Dataset-wide landmark names.** Give each landmark a name/abbreviation and a
  description at the dataset level; the viewer shows the name instead of the index
  while digitizing, with the description as a tooltip.
- **"Show Expected" digitizing aid (2D).** Once two landmarks are placed on a new
  specimen, the remaining positions are predicted from the dataset mean shape and
  shown as a guide.
- **Import curves from TPS.** ``CURVES=`` blocks in TPS files are read in as
  semi-landmark curves.

Changed
~~~~~~~

- **The dataset dialog is organized into tabs**, and gains tables for
  dataset-wide landmark names and the curve scheme.
- **The object list shows an "LM Count" column and a "Curve" column**, and
  refreshes on Save/Next/Previous while keeping your selection.

Version 0.1.12 (2026-07-21)
----------------------------

Legend arrangement in Data Exploration, a sharper 2D viewer, and a complete
Korean interface.

Added
~~~~~

- **Arrange the legend in Data Exploration.** With the legend shown, a **Movable**
  checkbox lets you drag it wherever it suits the plot, and **Order...** opens a
  list you can drag entries into the order you want (with A-Z / Z-A shortcuts).
  Both the order and the position are remembered per grouping variable.

Changed
~~~~~~~

- **The 2D viewer scales images more smoothly**, so zooming and fitting no longer
  show jagged edges while placing landmarks.
- **The Korean interface is fully translated** (strings added over several
  releases had never been picked up).

Fixed
~~~~~

- **A failure during startup now says what went wrong.** The message was hidden
  behind the splash screen; the splash now closes first and the message points at
  the log file.
- **``--db`` now opens the database you name** (the option was accepted and then
  ignored).

Version 0.1.8 (2026-07-21)
---------------------------

Better handling of large images, much more accurate missing-landmark estimation,
and fixes for memory that was never released.

Added
~~~~~

- **Oversized images are downscaled when attached.** Photos whose longer side
  exceeds 2560 px are stored as a smaller working copy (used for landmarking),
  while the pristine original is archived alongside it. No image data is lost.
- **"Show Original" checkbox in the object dialog.** When an archived original
  exists, you can render the 2D view from the full-resolution image for extra
  detail. This affects display only.
- **The About box links to the project page.**

Changed
~~~~~~~

- **Missing landmarks are estimated far more accurately.** Both the preview and
  the estimation used in analysis now fit the mean shape onto the landmarks a
  specimen actually has — matching rotation, scale and position — before filling
  the gaps, and analysis repeats the estimate as the alignment settles. On test
  shapes where the right answer is known, the error went from 61% of specimen
  size to essentially zero. Analysis results change for datasets with missing
  landmarks; datasets without them are unaffected.

Fixed
~~~~~

- **Zooming far into a 2D image no longer risks exhausting memory** (the zoom
  scale is capped).
- **Dialogs are now released when closed** (every dialog previously stayed in
  memory for the rest of the session).
- **Replacing an object's image no longer leaves the old files behind.**
- **Deleting a dataset or an object now deletes its files too** (images, archived
  originals, and 3D models). Files orphaned by earlier versions are not cleaned up
  automatically.

Version 0.1.7 (2026-07-21)
---------------------------

A small maintenance release: one crash fix and a 3D rendering speedup.

Changed
~~~~~~~

- **3D landmark spheres render much faster** — drawn from a sphere compiled once
  and reused, instead of being rebuilt triangle-by-triangle every frame.

Fixed
~~~~~

- **Chart no longer fails with "string index out of range"** when the selected
  grouping variable is blank for some objects. Those objects now appear in the
  legend as an unlabeled group.

Version 0.1.6 (2026-07-20)
---------------------------

Focused on making **missing landmarks** work end to end — from import, through
editing and display, to analysis.

Added
~~~~~

- **Missing landmark handling on import.** Import detects the ``-999``
  morphometrics placeholder and asks whether to treat those coordinates as
  missing landmarks (with an "always" checkbox to remember the answer), and
  handles the invert-Y option correctly.
- **Insert a missing landmark at a chosen position.** "Add Missing" now inserts
  before the selected row instead of only appending; the button reads "Insert
  Missing" or "Add Missing" depending on whether a row is selected.
- **Missing landmarks visible in the object list** — the Landmarks column shows
  the recorded count with the missing tally beside it in red, e.g. ``9 (1)``.
- **Italic legend labels** — a grouping value wrapped in asterisks renders italic
  in plot legends (``*Eurekia*`` → *Eurekia*).

Changed
~~~~~~~

- **Landmark table cells are validated when an edit is committed.** A cell accepts
  a number or ``MISSING`` (a blank cell counts as missing); anything else reverts
  to the stored value with an explanatory tooltip.
- **Edits to the landmark table update the viewer immediately.**
- **Analysis errors say what to do.** A landmark-count mismatch names the object,
  both counts, and points at "Insert Missing".

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
