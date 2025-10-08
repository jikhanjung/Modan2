# Screenshot Guide for Documentation

**Purpose**: Capture screenshots for user documentation (Quick Start and User Guide)

**Target**: Phase 8 Day 2
**Status**: TODO - Requires GUI environment

---

## Required Screenshots

### Quick Start Guide

#### 1. Installation Screenshots

**File**: `docs/screenshots/quickstart/01_installation_windows.png`
- Windows installer welcome screen
- Or: Modan2 in Start Menu

**File**: `docs/screenshots/quickstart/01_installation_macos.png`
- Modan2.dmg mounted with drag-to-Applications
- Or: Modan2 in Applications folder

**File**: `docs/screenshots/quickstart/01_installation_linux.png`
- Terminal showing `python3 Modan2.py` command
- Or: Modan2 main window on Linux

#### 2. Create Dataset

**File**: `docs/screenshots/quickstart/02_new_dataset_button.png`
- Main window with "New Dataset" button highlighted
- Arrow or highlight pointing to the button

**File**: `docs/screenshots/quickstart/02_dataset_dialog.png`
- Dataset Dialog with filled fields:
  - Name: "My_First_Dataset"
  - Dimension: 2D selected
- OK button visible

**File**: `docs/screenshots/quickstart/02_dataset_created.png`
- Main window showing "My_First_Dataset" in left panel
- Dataset selected/highlighted

#### 3. Import Data

**File**: `docs/screenshots/quickstart/03_import_menu.png`
- File → Import menu expanded
- TPS option highlighted

**File**: `docs/screenshots/quickstart/03_import_dialog.png`
- Import dialog with file selected
- Dataset dropdown showing "My_First_Dataset"
- Import button visible

**File**: `docs/screenshots/quickstart/03_objects_imported.png`
- Main window with objects in center table
- Multiple rows visible

**File**: `docs/screenshots/quickstart/03_import_images.png`
- File → Import → Images menu
- Or: Import Images dialog

#### 4. Digitize Landmarks

**File**: `docs/screenshots/quickstart/04_object_editor.png`
- Object editor window with image loaded
- Some landmarks already placed (numbered)
- Toolbar visible with zoom/pan tools

**File**: `docs/screenshots/quickstart/04_landmark_placement.png`
- Close-up of image with landmarks being placed
- Show landmark numbers (1, 2, 3...)
- Crosshair cursor visible (if possible)

**File**: `docs/screenshots/quickstart/04_keyboard_shortcuts.png`
- Object editor with keyboard shortcuts overlay
- Or: Help menu showing shortcuts

#### 5. Run Analysis

**File**: `docs/screenshots/quickstart/05_analysis_menu.png`
- Analysis → New Analysis menu highlighted

**File**: `docs/screenshots/quickstart/05_analysis_dialog.png`
- New Analysis dialog with:
  - Dataset: "My_First_Dataset" selected
  - Superimposition: Procrustes selected
  - Analysis Type: PCA selected
  - Run Analysis button visible

**File**: `docs/screenshots/quickstart/05_analysis_progress.png`
- Progress dialog during analysis (if quick enough to capture)
- Or: Analysis running indicator

**File**: `docs/screenshots/quickstart/05_pca_results.png`
- PCA results window/dialog
- Scree plot visible
- PC scores table visible

**File**: `docs/screenshots/quickstart/05_shape_plot.png`
- Shape variation plot (PCA morphospace)
- PC1 vs PC2 scatter plot
- Objects plotted as points

---

### User Guide

#### Main Window

**File**: `docs/screenshots/userguide/main_window_annotated.png`
- Full main window with annotations:
  - Dataset panel (left)
  - Object table (center)
  - Toolbar (top)
  - Status bar (bottom)
- Use arrows/numbers to label each section

#### Dataset Management

**File**: `docs/screenshots/userguide/dataset_panel.png`
- Dataset tree view with multiple datasets
- Context menu (right-click)

**File**: `docs/screenshots/userguide/dataset_dialog_advanced.png`
- Dataset dialog with all options:
  - Variables defined
  - Wireframe configured
  - Baseline set
  - Polygons defined

**File**: `docs/screenshots/userguide/dataset_properties.png`
- Dataset properties showing:
  - Number of objects
  - Number of landmarks
  - Dimension (2D/3D)
  - Variables list

#### Import Workflows

**File**: `docs/screenshots/userguide/import_tps.png`
- TPS import dialog with options

**File**: `docs/screenshots/userguide/import_morphologika.png`
- Morphologika import dialog

**File**: `docs/screenshots/userguide/import_json_zip.png`
- JSON+ZIP import dialog
- File selection showing .zip file

**File**: `docs/screenshots/userguide/import_3d_models.png`
- 3D model import (OBJ/PLY/STL)
- File browser with 3D files

#### Digitizing

**File**: `docs/screenshots/userguide/object_editor_2d.png`
- 2D object editor with:
  - Image loaded
  - Landmarks placed
  - Wireframe visible
  - Tools panel visible

**File**: `docs/screenshots/userguide/object_editor_3d.png`
- 3D object editor with:
  - 3D model loaded
  - Landmarks in 3D space
  - Rotation controls visible

**File**: `docs/screenshots/userguide/calibration_dialog.png`
- Calibration dialog with:
  - Scale measurement
  - Reference points

**File**: `docs/screenshots/userguide/landmark_tools.png`
- Landmark editing tools:
  - Add/delete landmarks
  - Reorder landmarks
  - Landmark information panel

#### Analysis

**File**: `docs/screenshots/userguide/analysis_types.png`
- Analysis type selection:
  - Procrustes
  - PCA
  - CVA
  - MANOVA
  - Regression

**File**: `docs/screenshots/userguide/procrustes_options.png`
- Procrustes superimposition options:
  - GPA (Generalized Procrustes Analysis)
  - Bookstein
  - Resistant Fit

**File**: `docs/screenshots/userguide/pca_full.png`
- Complete PCA results:
  - Scree plot
  - Loadings table
  - Scores table
  - Variance explained

**File**: `docs/screenshots/userguide/cva_results.png`
- CVA results:
  - Group separation
  - Canonical variates plot
  - Mahalanobis distances

**File**: `docs/screenshots/userguide/manova_results.png`
- MANOVA results:
  - Statistics table
  - P-values
  - Effect sizes

**File**: `docs/screenshots/userguide/regression_results.png`
- Regression analysis:
  - Scatter plot
  - Regression line
  - R² value

#### Data Exploration

**File**: `docs/screenshots/userguide/data_exploration.png`
- Data exploration dialog with:
  - Variable selection
  - Scatter plot matrix
  - Histogram panel

**File**: `docs/screenshots/userguide/shape_grid.png`
- Shape grid visualization:
  - Multiple shapes displayed
  - Grid layout
  - Shape variation across PCs

**File**: `docs/screenshots/userguide/shape_deformation.png`
- Shape deformation animation:
  - TPS deformation grid
  - Landmark displacement vectors

#### Export

**File**: `docs/screenshots/userguide/export_dialog.png`
- Export dialog with options:
  - Format selection (TPS, Morphologika, JSON+ZIP)
  - Object selection
  - File destination

**File**: `docs/screenshots/userguide/export_analysis.png`
- Export analysis results:
  - Format options (CSV, Excel)
  - Data selection
  - Preview panel

#### Preferences

**File**: `docs/screenshots/userguide/preferences_general.png`
- Preferences dialog - General tab:
  - Language selection
  - Theme options
  - Startup settings

**File**: `docs/screenshots/userguide/preferences_display.png`
- Preferences - Display tab:
  - Landmark size/color
  - Wireframe settings
  - Grid options

**File**: `docs/screenshots/userguide/preferences_analysis.png`
- Preferences - Analysis tab:
  - Default superimposition method
  - Precision settings
  - Performance options

---

## Screenshot Capture Instructions

### Prerequisites
1. **Clean Database**: Use fresh database with sample data
2. **Sample Data**: Prepare example datasets beforehand
3. **Window Size**: Set consistent window size (1280x720 or 1920x1080)
4. **Theme**: Use default theme for consistency

### Tools

**Windows**:
- Snipping Tool (Windows 10)
- Snip & Sketch (Windows 11)
- Or: ShareX (free, advanced)

**macOS**:
- Cmd+Shift+4 (area selection)
- Cmd+Shift+5 (screenshot toolbar)

**Linux**:
- GNOME Screenshot
- Flameshot (recommended)
- Spectacle (KDE)

### Capture Workflow

#### Step 1: Prepare Sample Data
```bash
# Use provided sample dataset or create one
python3 Modan2.py

# Create sample dataset:
# - Name: "Example_Dataset"
# - Dimension: 2D
# - 10-20 objects with landmarks
# - 2-3 variables defined
```

#### Step 2: Capture Screenshots Systematically

**For Each Screenshot**:
1. Navigate to the screen/dialog
2. Ensure clean, professional appearance:
   - No debug messages
   - No error dialogs in background
   - Proper window sizing
3. Capture screenshot
4. Save with descriptive filename
5. Check image quality and clarity

#### Step 3: Annotate if Needed

**Tools for Annotation**:
- **Windows**: Paint, Paint 3D, or PowerPoint
- **macOS**: Preview (Markup tools)
- **Linux**: GIMP, Inkscape, or Krita
- **Cross-platform**: Photopea (web-based)

**Annotation Elements**:
- Red arrows pointing to important UI elements
- Red rectangles highlighting key areas
- Numbers (1, 2, 3...) for step sequences
- Brief text labels if necessary
- Keep annotations minimal and clear

### File Organization

```
docs/
└── screenshots/
    ├── quickstart/
    │   ├── 01_installation_windows.png
    │   ├── 01_installation_macos.png
    │   ├── 01_installation_linux.png
    │   ├── 02_new_dataset_button.png
    │   ├── 02_dataset_dialog.png
    │   ├── 02_dataset_created.png
    │   ├── 03_import_menu.png
    │   ├── 03_import_dialog.png
    │   ├── 03_objects_imported.png
    │   ├── 03_import_images.png
    │   ├── 04_object_editor.png
    │   ├── 04_landmark_placement.png
    │   ├── 04_keyboard_shortcuts.png
    │   ├── 05_analysis_menu.png
    │   ├── 05_analysis_dialog.png
    │   ├── 05_analysis_progress.png
    │   ├── 05_pca_results.png
    │   └── 05_shape_plot.png
    └── userguide/
        ├── main_window_annotated.png
        ├── dataset_panel.png
        ├── dataset_dialog_advanced.png
        ├── [... all user guide screenshots ...]
        └── preferences_analysis.png
```

### Image Specifications

**Format**: PNG (preferred for UI screenshots)
**Resolution**:
- Minimum: 1280x720
- Recommended: 1920x1080
- High DPI: 2560x1440 (scale down if needed)

**File Size**:
- Target: < 500KB per image
- Use PNG compression (OptiPNG, TinyPNG)
- Balance quality vs file size

**Quality Guidelines**:
- Text must be readable at 100% zoom
- UI elements clearly visible
- No compression artifacts
- Colors accurate (use sRGB color space)

---

## Adding Screenshots to Documentation

### Quick Start Guide

**Format**:
```markdown
## 2. Create Your First Dataset (1 minute)

![New Dataset Button](screenshots/quickstart/02_new_dataset_button.png)
*Click the "New Dataset" button in the toolbar*

1. Click **"New Dataset"** button (or press `Ctrl+N`)
2. Fill in:
   - **Name**: `My_First_Dataset`
   - **Dimension**: `2D`

![Dataset Dialog](screenshots/quickstart/02_dataset_dialog.png)
*Dataset creation dialog*

3. Click **OK**

![Dataset Created](screenshots/quickstart/02_dataset_created.png)
*Your new dataset appears in the left panel*

Done! Your dataset appears in the left panel.
```

### User Guide

**Format**:
```markdown
## Main Window Overview

![Main Window](screenshots/userguide/main_window_annotated.png)
*Modan2 main window with labeled components*

The main window consists of:

1. **Dataset Panel** (left) - Browse and manage datasets
2. **Object Table** (center) - View and edit objects
3. **Toolbar** (top) - Quick access to common functions
4. **Status Bar** (bottom) - Information and progress
```

---

## Screenshot Checklist

### Before Capture
- [ ] Fresh database with sample data prepared
- [ ] Window size set consistently (1280x720 or 1920x1080)
- [ ] No debug messages or errors visible
- [ ] Default theme applied
- [ ] Test data representative and clean

### During Capture
- [ ] Screenshot tool ready (hotkey configured)
- [ ] Capture exactly what's needed (no extra desktop)
- [ ] Check focus and clarity
- [ ] Save with descriptive filename immediately

### After Capture
- [ ] Image quality checked (readable text, clear UI)
- [ ] File size optimized (< 500KB if possible)
- [ ] Annotations added if needed
- [ ] Saved in correct directory
- [ ] Filename matches documentation reference

### Integration
- [ ] Screenshot referenced in markdown
- [ ] Alt text/caption added
- [ ] Image displays correctly in preview
- [ ] Links work correctly
- [ ] Documentation flows well with images

---

## Priority Order

### Phase 1 (Essential - Quick Start)
1. ✅ Installation screenshots (all platforms)
2. ✅ New Dataset flow (3 screenshots)
3. ✅ Import data (3-4 screenshots)
4. ✅ Digitize landmarks (2-3 screenshots)
5. ✅ Run analysis (4-5 screenshots)

**Total**: ~15-20 screenshots

### Phase 2 (Important - User Guide)
1. Main window overview (1 screenshot)
2. Dataset management (3-4 screenshots)
3. Import workflows (4-5 screenshots)
4. Digitizing (4-5 screenshots)
5. Analysis (5-6 screenshots)
6. Data exploration (3-4 screenshots)
7. Export (2-3 screenshots)
8. Preferences (3 screenshots)

**Total**: ~25-35 screenshots

### Phase 3 (Optional - Advanced)
- Tutorial videos (animated GIFs)
- Troubleshooting visual guides
- Advanced workflow diagrams

---

## Automation (Future)

Consider creating automated screenshot capture script:

```python
# scripts/capture_screenshots.py (future enhancement)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
import sys

def capture_window(window, filename):
    """Capture screenshot of specific window"""
    pixmap = window.grab()
    pixmap.save(filename, 'PNG')

# Automate screenshot workflow:
# 1. Launch Modan2
# 2. Programmatically navigate to each screen
# 3. Capture screenshot
# 4. Save with correct filename
# 5. Close and move to next
```

---

## Notes

- **Platform Differences**: Capture screenshots on each platform (Windows, macOS, Linux) where UI differs significantly
- **Localization**: Currently targeting English version; may need Korean screenshots in future
- **Versioning**: Include version number in screenshot metadata for tracking
- **Updates**: Plan to recapture screenshots if UI changes significantly

---

## Completion Status

**Status**: 📋 READY TO EXECUTE
**Blockers**: Requires GUI environment (Windows/macOS/Linux with display)
**Estimated Time**: 2-3 hours for all screenshots
**Priority**: High (needed for user documentation)

---

**Document Version**: 1.0
**Created**: 2025-10-08
**For Phase**: Phase 8 Day 2
