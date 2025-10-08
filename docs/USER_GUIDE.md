# Modan2 User Guide

**Version**: 0.1.4
**Last Updated**: 2025-10-08

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Working with Datasets](#working-with-datasets)
4. [Importing Data](#importing-data)
5. [Digitizing Landmarks](#digitizing-landmarks)
6. [Statistical Analysis](#statistical-analysis)
7. [Exporting Results](#exporting-results)
8. [Performance Guide](#performance-guide)
9. [Troubleshooting](#troubleshooting)
10. [Tips & Best Practices](#tips--best-practices)

---

## Introduction

### What is Modan2?

Modan2 is a powerful desktop application for **geometric morphometric analysis** of 2D and 3D landmark data. It provides researchers with tools to:

- **Digitize landmarks** on images and 3D models
- **Organize datasets** with hierarchical structure
- **Perform statistical analyses**: PCA, CVA, MANOVA, and more
- **Visualize results** with interactive charts and plots
- **Export data** in various formats for further analysis

### Key Features

✅ **2D and 3D landmark analysis**
✅ **Multiple import formats**: TPS, NTS, Morphologika, JSON, image files, 3D models
✅ **Procrustes superimposition** with multiple alignment options
✅ **Statistical analyses**: PCA, CVA, MANOVA
✅ **Interactive visualization** with customizable plots
✅ **Hierarchical dataset organization**
✅ **Batch processing** for large datasets
✅ **High performance**: Handles 10,000+ objects smoothly

### System Requirements

**Minimum**:
- OS: Windows 10, macOS 10.14, Ubuntu 18.04 or later
- RAM: 4GB
- Storage: 500MB free space
- Display: 1280x720 resolution

**Recommended**:
- RAM: 8GB or more
- Display: 1920x1080 or higher
- For 3D models: Dedicated GPU with OpenGL 3.3+ support

---

## Getting Started

### Installation

#### Windows
1. Download `Modan2-Setup.exe` from releases
2. Run the installer
3. Launch from Start Menu → Modan2

#### macOS
1. Download `Modan2.dmg` from releases
2. Open the DMG file
3. Drag Modan2.app to Applications
4. Launch from Applications folder

#### Linux
1. Install system dependencies:
```bash
sudo apt-get install python3 python3-pip libxcb-xinerama0 \
  libqt5gui5 libqt5widgets5 python3-pyqt5
```

2. Install from PyPI (when available) or run from source:
```bash
git clone https://github.com/yourusername/Modan2.git
cd Modan2
pip install -r requirements.txt
python3 Modan2.py
```

### First Launch

On first launch, Modan2 will:
1. Create configuration directory: `~/.modan2/`
2. Initialize default database: `modan2.db`
3. Show the main window with empty dataset tree

### Main Window Overview

The main window has five key areas:

```
┌─────────────────────────────────────────────────────────┐
│ Menu Bar: File | Edit | View | Analysis | Help          │
├──────────┬──────────────────────────┬──────────────────┤
│          │                          │                  │
│ Dataset  │    Object Table          │  Object Preview  │
│ Tree     │    (Center)              │  (Right Panel)   │
│ (Left)   │                          │                  │
│          │                          │                  │
├──────────┴──────────────────────────┴──────────────────┤
│ Status Bar: Ready                                       │
└─────────────────────────────────────────────────────────┘
```

**1. Dataset Tree (Left Panel)**:
- Hierarchical view of all datasets
- Right-click for dataset operations
- Drag-and-drop to reorganize

**2. Object Table (Center)**:
- Lists all objects in selected dataset
- Sortable columns
- Multi-select for batch operations
- Click column headers to sort

**3. Object Preview (Right Panel)**:
- 2D: Image with landmarks overlay
- 3D: Interactive 3D viewer
- Pan, zoom, rotate controls

**4. Menu Bar**:
- **File**: New, Open, Save, Import, Export
- **Edit**: Undo, Redo, Preferences
- **View**: Show/hide panels, zoom controls
- **Analysis**: Run statistical analyses
- **Help**: Documentation, About

**5. Status Bar**:
- Current operation status
- Progress indicators
- Quick stats (object count, dataset info)

---

## Working with Datasets

### Creating a New Dataset

**Method 1: Toolbar Button**
1. Click **"New Dataset"** button (📁+) or press `Ctrl+N`
2. Fill in dataset information:
   - **Name**: Descriptive name (e.g., "Bird_Wings_2024")
   - **Dimension**: Select 2D or 3D
   - **Parent Dataset**: (Optional) Select parent for hierarchical structure
   - **Description**: (Optional) Additional notes
3. Click **OK**

**Method 2: Right-click Menu**
1. Right-click on dataset tree background
2. Select "New Dataset"
3. Follow dialog prompts

### Dataset Properties

**Hierarchical Organization**:
Organize related datasets in parent-child relationships:

```
Study_2024 (parent)
├── Subspecies_A (child)
├── Subspecies_B (child)
└── Control_Group (child)
```

Benefits:
- Logical organization
- Easy navigation
- Grouped analysis possible

**Dimension (2D vs 3D)**:
- **2D**: Landmarks have X, Y coordinates
- **3D**: Landmarks have X, Y, Z coordinates
- ⚠️ **Cannot be changed** after objects are added

### Managing Variables

Variables define grouping and categorical data for statistical analysis.

**Adding Variables**:
1. Select dataset in tree
2. Right-click → "Edit Dataset" or press `F2`
3. In "Variable Names" section:
   - Click "Add" to create new variable
   - Enter variable name (e.g., "Species", "Sex", "Age")
   - Drag to reorder
   - Click "Delete" to remove

**Variable Types**:
- **Categorical**: Groups for CVA/MANOVA (e.g., "male", "female")
- **Continuous**: Numeric measurements (e.g., age, weight)

**Example Setup**:
```
Dataset: Bird Wings
Variables: Species, Sex, Age, Location

Object 1: sparrow, male, 2.5, Site_A
Object 2: sparrow, female, 1.8, Site_A
Object 3: robin, male, 3.2, Site_B
```

**Setting Object Variables**:
1. Select object(s) in table
2. Right-click → "Edit Object" or double-click
3. Enter values in "Properties" field (comma-separated)
4. Format: `value1,value2,value3`

Example: `sparrow,male,2.5,Site_A`

### Editing Datasets

**Rename Dataset**:
1. Right-click dataset → "Edit Dataset"
2. Change name
3. Click OK

**Delete Dataset**:
1. Right-click dataset → "Delete Dataset"
2. Confirm deletion
3. ⚠️ **Warning**: This deletes ALL objects and analyses in the dataset!

**Move Objects Between Datasets**:
1. Select object(s) in source dataset
2. Right-click → "Move to Dataset"
3. Select destination dataset
4. Click OK

---

## Importing Data

Modan2 supports multiple import formats for flexibility in your workflow.

### Supported Formats

| Format | Extension | Type | Description |
|--------|-----------|------|-------------|
| TPS | `.tps` | 2D/3D | Morphologika format |
| NTS | `.nts` | 2D | Landmark coordinates |
| X1Y1 | `.txt` | 2D | Simple X Y format |
| Morphologika | `.txt` | 2D/3D | Morphologika text format |
| JSON+ZIP | `.zip` | 2D/3D | Modan2 native format (with images) |
| Images | `.jpg`, `.png`, `.bmp` | 2D | For digitizing |
| 3D Models | `.obj`, `.ply`, `.stl` | 3D | For 3D digitizing |

### Importing Landmark Files

**Method 1: Menu**
1. File → Import → Choose format
2. Select file(s)
3. Select destination dataset
4. Click "Import"

**Method 2: Drag-and-Drop**
1. Drag file(s) from file explorer
2. Drop onto dataset in tree
3. Auto-detects format
4. Confirms import

### Import Workflow Details

#### TPS Format Import

TPS files are widely used in morphometrics:

```
LM=10
1.5 2.3
2.1 3.4
...
ID=specimen_001
IMAGE=specimen_001.jpg

LM=10
1.6 2.4
2.2 3.5
...
ID=specimen_002
IMAGE=specimen_002.jpg
```

**Import Steps**:
1. File → Import → TPS
2. Select `.tps` file
3. Choose dataset
4. **Optional**: If IMAGE= tags present, Modan2 will try to find images in same directory
5. Click "Import"
6. Progress bar shows import status

**Performance**: ~100 objects/second

#### Morphologika Format Import

```
[individuals]
specimen_001
specimen_002

[landmarks]
10

[rawpoints]
1.5 2.3 0.0
2.1 3.4 0.0
...
```

**Import Steps**:
Same as TPS format

#### JSON+ZIP Format (Native)

Modan2's native format preserves:
- Landmarks
- Images (embedded in ZIP)
- Object properties
- Dataset metadata
- Analyses

**Export**:
1. Right-click dataset → "Export Dataset"
2. Choose "JSON+ZIP" format
3. Select output location
4. Includes all images automatically

**Import**:
1. File → Import → JSON+ZIP
2. Select `.zip` file
3. Everything is restored exactly

### Importing Images for Digitizing

**Single Image**:
1. File → Import → Images
2. Select image file(s)
3. Choose dataset
4. Images are added as objects ready for digitizing

**Batch Import**:
1. Select multiple images in file dialog
2. All imported at once
3. Object names derived from filenames

**Supported Image Formats**:
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- BMP (`.bmp`)
- TIFF (`.tif`, `.tiff`)

**Image Resolution**:
- Recommended: 1024x1024 or higher
- Maximum: 10000x10000 pixels
- For best precision: Use high-resolution images

### Importing 3D Models

**Supported Formats**:
- Wavefront OBJ (`.obj`) - most common
- Stanford PLY (`.ply`)
- STL (`.stl`)

**Import Steps**:
1. Create 3D dataset first (Dimension: 3D)
2. File → Import → 3D Models
3. Select model file(s)
4. Models loaded into 3D viewer

**3D Model Requirements**:
- Clean mesh topology
- Reasonable polygon count (< 100k for smooth performance)
- Proper scale (Modan2 auto-normalizes)

---

## Digitizing Landmarks

### 2D Landmark Digitizing

**Opening Object for Digitizing**:
1. Double-click object in table, OR
2. Select object → Right-click → "Edit Object"

**Digitizing Workflow**:

1. **Place Landmarks**:
   - Click on image to place landmark
   - Landmarks numbered sequentially (1, 2, 3...)
   - Zoom: Mouse wheel or `Ctrl +/-`
   - Pan: Right-click + drag

2. **Edit Landmarks**:
   - Drag landmark to reposition
   - Delete: Select landmark → Press `Delete`
   - Insert: `Shift+Click` between landmarks

3. **Save**:
   - Click "OK" to save
   - Click "Cancel" to discard changes

**Keyboard Shortcuts**:
- `Space`: Next object (for batch digitizing)
- `Backspace`: Previous object
- `Delete`: Delete selected landmark
- `Ctrl+Z`: Undo last landmark
- `Ctrl+S`: Save and continue
- `Esc`: Cancel

**Digitizing Tips**:
- ✅ Work at consistent zoom level
- ✅ Use anatomical landmarks (repeatable points)
- ✅ Maintain landmark order consistency
- ✅ Zoom in for precision at difficult points
- ✅ Take breaks to avoid fatigue

### 3D Landmark Digitizing

**Opening 3D Object**:
1. Double-click 3D object
2. 3D viewer opens with model

**3D Viewer Controls**:
- **Rotate**: Left-click + drag
- **Pan**: Middle-click + drag (or `Shift` + left-click + drag)
- **Zoom**: Mouse wheel
- **Reset View**: Press `R`

**Placing 3D Landmarks**:
1. Click on model surface to place landmark
2. Landmark appears as sphere
3. Landmarks numbered sequentially

**3D Landmark Editing**:
- **Select**: Click on landmark sphere
- **Move**: Drag landmark on surface
- **Delete**: Select → Press `Delete`
- **Adjust view**: Rotate model to see all angles

**3D Digitizing Tips**:
- ✅ Rotate model to verify landmark position from multiple angles
- ✅ Use anatomical features visible from different views
- ✅ Consistent lighting helps identify landmarks
- ✅ For symmetrical features, use consistent side

### Calibration (Scale Setting)

For measurements in real-world units:

1. **Open Calibration Tool**:
   - Tools → Calibration, OR
   - In object editor, click "Calibrate"

2. **Draw Scale Line**:
   - Click two points on known distance
   - Example: Ruler in image, known anatomical distance

3. **Enter Real Distance**:
   - Enter known length
   - Select unit (mm, cm, m, etc.)
   - Click OK

4. **Apply to Objects**:
   - Individual: Apply to current object
   - Batch: Apply to all objects in dataset

**Calibration is stored per-object** for flexibility.

---

## Statistical Analysis

Modan2 provides comprehensive statistical analysis tools for geometric morphometrics.

### Analysis Workflow

```
1. Select Dataset
2. Choose Analysis Type (PCA, CVA, MANOVA)
3. Configure Parameters
4. Run Analysis
5. View Results
6. Export (optional)
```

### Procrustes Superimposition

**What is it?**
Aligns landmark configurations to remove variation due to position, rotation, and scale, leaving only shape variation.

**Methods**:
1. **Generalized Procrustes Analysis (GPA)**: Most common, minimizes squared distances
2. **Bookstein Coordinates**: Uses baseline between two landmarks
3. **Resistant Fit**: Robust to outliers
4. **None**: Use raw coordinates (not recommended for shape analysis)

**Running Procrustes**:
1. Analysis → New Analysis
2. Select dataset
3. Choose "Procrustes" method
4. Configure options:
   - **Method**: GPA (recommended)
   - **Scaling**: Yes (recommended for size removal)
   - **Reflection**: Allow if bilateral symmetry
5. Click "Run"

**Performance**:
- 100 objects: < 50ms
- 1,000 objects: < 800ms
- 2,000 objects: < 2s

### Principal Component Analysis (PCA)

**Purpose**: Reduce dimensionality, identify main axes of shape variation.

**Running PCA**:
1. Analysis → New Analysis
2. Select dataset with Procrustes superimposition
3. Analysis type: "PCA"
4. Options:
   - **Components**: Number to compute (default: all)
   - **Center data**: Yes (recommended)
   - **Scale**: No (for shape data)
5. Click "Run"

**Interpreting Results**:
- **Scree Plot**: Shows variance explained by each PC
- **PC Scores Plot**: Objects plotted in PC space
- **Loadings**: Contribution of each landmark to PCs
- **Variance Explained**: Percentage per PC

**Performance**:
- 100 objects: < 5ms
- 1,000 objects: < 80ms
- 10,000 objects: < 1s

**Typical Results**:
- PC1: Usually 40-60% of variance (main shape differences)
- PC2: Usually 10-30% of variance
- First 3-5 PCs: Usually 80%+ of variance

### Canonical Variate Analysis (CVA)

**Purpose**: Find linear combinations that best separate predefined groups.

**Requirements**:
- Groups defined in object properties
- At least 2 groups
- Multiple objects per group (recommended: 5+)

**Running CVA**:
1. Analysis → New Analysis
2. Select dataset with Procrustes
3. Analysis type: "CVA"
4. Configure:
   - **Grouping Variable**: Choose variable (e.g., "Species")
   - **Cross-validation**: Optional, for classification accuracy
5. Click "Run"

**Interpreting Results**:
- **CV Scores Plot**: Groups plotted in CV space
- **Centroids**: Group means in CV space
- **Classification**: Confusion matrix shows accuracy
- **Mahalanobis Distances**: Between-group distances

**Performance**:
- Depends on feature dimensionality (landmarks × 2 or 3)
- Low-dimensional (< 50 features): < 50ms
- Medium (50-100 features): < 100ms
- High (200+ features): 500ms - 2s (normal for SVD complexity)

**CVA Tips**:
- ✅ Use variables with 2-10 groups (too many = overfitting)
- ✅ Balanced sample sizes across groups if possible
- ✅ Interpret CV1 and CV2 (main discriminants)

### MANOVA

**Purpose**: Test for significant differences in shape among groups.

**Running MANOVA**:
1. Analysis → New Analysis
2. Select dataset with Procrustes
3. Analysis type: "MANOVA"
4. Configure:
   - **Factors**: Select grouping variable(s)
   - **Permutations**: Number for permutation test (default: 1000)
5. Click "Run"

**Interpreting Results**:
- **Wilks' Lambda**: Multivariate test statistic (0-1, lower = more different)
- **F-statistic**: Test statistic
- **p-value**: Significance level (< 0.05 = significant)
- **Effect Size**: Practical significance

**Performance**:
- Single factor, 100 objects: < 50ms
- Single factor, 1000 objects: < 100ms
- Multiple factors: Longer (depends on model complexity)

### Visualizing Results

**Data Exploration Dialog**:
1. Analysis → View Analysis Results
2. Select analysis from list
3. Interactive plots:
   - **Scatter plots**: PC1 vs PC2, CV1 vs CV2, etc.
   - **3D plots**: PC1-PC2-PC3
   - **Group coloring**: Color by variable
   - **Convex hulls**: Show group boundaries

**Plot Controls**:
- **Zoom**: Mouse wheel
- **Pan**: Right-click + drag
- **Select points**: Click or drag-select
- **Pick object**: Double-click point to view object
- **Export plot**: Right-click → Save as Image

**Customization**:
- Point size, color, shape
- Axis labels and ranges
- Grid, legend visibility
- Background color

---

## Exporting Results

### Export Dataset

**Formats**:
- **TPS**: Widely compatible
- **Morphologika**: Standard format
- **JSON+ZIP**: Modan2 native (includes images)

**Export Workflow**:
1. Right-click dataset → "Export Dataset"
2. Choose format
3. Options:
   - **Objects**: All or selected only
   - **Superimposition**: Apply Procrustes before export
   - **Images**: Include in ZIP (JSON+ZIP only)
4. Select output location
5. Click "Export"

**Performance**:
- 500 objects: < 2s
- 1000 objects: < 5s
- With images (ZIP): Depends on image sizes

### Export Analysis Results

**Available Exports**:
- **Scores**: PC/CV scores as CSV
- **Loadings**: Variable loadings as CSV
- **Plots**: As PNG, PDF, or SVG
- **Statistics**: Summary tables as CSV/Excel

**Export Steps**:
1. Open analysis results dialog
2. Click "Export" button
3. Choose what to export:
   - Scores table
   - Plot image
   - Statistics summary
4. Select format and location
5. Click "Save"

### Batch Export

Export multiple datasets or analyses at once:

1. Select multiple datasets (Ctrl+Click)
2. Right-click → "Batch Export"
3. Choose format and options
4. All exported to same directory

---

## Performance Guide

Modan2 is optimized for excellent performance. Based on comprehensive testing (Phase 7), here's what to expect:

### Dataset Sizes and Performance

| Dataset Size | Load Time | Memory | UI Response | Analysis (PCA) |
|--------------|-----------|--------|-------------|----------------|
| < 100 objects | Instant (< 20ms) | < 1MB | Instant | < 5ms |
| 100-500 objects | Very fast (< 200ms) | < 3MB | Instant | < 50ms |
| 500-1,000 objects | Fast (< 600ms) | < 5MB | Instant | < 80ms |
| 1,000-5,000 objects | Good (< 3s) | < 20MB | Instant | < 500ms |
| 5,000-10,000 objects | Acceptable (< 10s) | < 50MB | Instant | < 2s |

**Key Findings** (from Phase 7 testing):
- ✅ **18× faster** than 5s target for 1000 objects (277ms achieved)
- ✅ **125× more memory-efficient** than target (4MB vs 500MB)
- ✅ **UI always responsive**: Progress updates at 152,746/sec
- ✅ **No freezing**: processEvents overhead only 0.0009ms

### Performance Tips

**For Best Performance**:
1. ✅ **Close unused datasets**: Frees memory
2. ✅ **Use appropriate image sizes**: 1024-2048px recommended
3. ✅ **Batch operations**: Import/export in bulk when possible
4. ✅ **Regular maintenance**: Compact database periodically (Tools → Compact Database)

**Expected Analysis Times** (1000 objects):
- **Procrustes**: ~800ms
- **PCA**: ~60ms
- **CVA** (low-dimensional): ~10ms
- **CVA** (high-dimensional, 100+ landmarks): ~1-2s (normal SVD complexity)
- **MANOVA**: ~30ms

### Memory Usage

**Per-Object Memory**:
- ~4KB per object (2D, 10 landmarks)
- ~64KB per object (3D, 100 landmarks)
- Linear scaling: predictable and efficient

**Total Memory Expectations**:
- 1,000 objects: ~4MB
- 10,000 objects: ~40MB
- 100,000 objects: ~400MB

**No Memory Leaks**: Validated over 50 iterations with < 3KB growth.

### Large Dataset Recommendations

For 10,000+ objects:
- Modan2 handles them smoothly
- Consider splitting by time periods or subgroups for easier organization
- Use batch export for large exports
- Expected load time: 5-10s (acceptable)

For 100,000+ objects (extreme):
- Feasible but slower (~50s load)
- Consider dataset organization and subsampling for exploratory analysis
- Full analysis still works but may take minutes

---

## Troubleshooting

### Common Issues

#### "Could not load Qt platform plugin"

**Platform**: Linux/WSL

**Solution**:
```bash
# Option 1: Run with fix script
python3 fix_qt_import.py

# Option 2: Set environment variable
export QT_QPA_PLATFORM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt5/plugins/platforms
python3 Modan2.py
```

#### "OpenGL Error" or 3D viewer not working

**Platform**: All

**Solution**:
1. Update graphics drivers
2. For Linux:
```bash
sudo apt-get install libglut-dev libglut3.12 python3-opengl
```
3. Check OpenGL version: Must be 3.3+

#### Import fails with "Invalid format"

**Causes**:
- File encoding issues (use UTF-8)
- Malformed TPS/Morphologika file
- Missing required fields

**Solution**:
1. Check file format matches specification
2. Try opening in text editor to verify structure
3. Check for special characters in object names
4. Ensure landmark counts are consistent

#### Analysis fails or produces unexpected results

**Causes**:
- Missing landmarks (some objects have fewer landmarks)
- Mismatched dimensions (2D vs 3D)
- Insufficient data (< 3 objects)

**Solution**:
1. Verify all objects have same number of landmarks
2. Check dataset dimension matches data
3. Ensure minimum data requirements for analysis
4. Check for outliers or data entry errors

#### Slow performance

**Causes**:
- Very large images (> 5MB each)
- Many objects with images loaded
- Background processes

**Solution**:
1. Resize images before import (1024-2048px recommended)
2. Close unused datasets
3. Tools → Compact Database
4. Restart Modan2
5. Close other applications to free RAM

#### Database corruption

**Rare, but possible after crashes**

**Solution**:
1. Tools → Check Database Integrity
2. If corruption detected: Tools → Repair Database
3. If repair fails: Restore from backup
4. Backup regularly: File → Backup Database

### Getting Help

**Documentation**:
- User Guide (this document)
- Developer Guide: `docs/developer_guide.md`
- Performance Guide: `docs/performance.md`

**Support**:
- GitHub Issues: Report bugs and request features
- Email: [your support email]
- Community Forum: [forum link if available]

**Reporting Bugs**:
Include:
1. Modan2 version (Help → About)
2. Operating system and version
3. Steps to reproduce
4. Error messages or screenshots
5. Sample data (if possible)

---

## Tips & Best Practices

### Data Organization

**Naming Conventions**:
- ✅ Use descriptive names: `Bird_Wings_2024` not `Dataset1`
- ✅ Consistent object names: `specimen_001`, `specimen_002`
- ✅ Avoid special characters: Use `_` instead of spaces

**Hierarchical Structure**:
```
Project_2024/
├── Site_A/
│   ├── Species_1
│   └── Species_2
└── Site_B/
    ├── Species_1
    └── Species_2
```

**Variable Organization**:
- Order variables logically (Species, Sex, Age, Location)
- Use consistent values ("male" not "Male", "m", "M")
- Document variable meanings in dataset description

### Landmark Digitizing

**Precision**:
- ✅ Zoom in for difficult landmarks
- ✅ Take breaks to avoid fatigue
- ✅ Digitize in sessions (consistent mental state)
- ✅ Re-digitize sample to check reproducibility

**Landmark Selection**:
- ✅ Use Type I landmarks (homologous points, e.g., suture intersections)
- ✅ Avoid Type III landmarks (arbitrary points on curves) when possible
- ✅ Balance landmarks across structure (not clustered)
- ✅ Document landmark definitions

**Quality Control**:
1. Periodically re-digitize sample of objects
2. Check measurement error
3. Use Procrustes distances to identify outliers
4. Verify outliers (digitizing error vs biological variation)

### Analysis Best Practices

**Sample Size**:
- Minimum: 30 objects for basic analysis
- Recommended: 50+ objects per group for CVA
- Power analysis: Consider before data collection

**Procrustes**:
- ✅ Always use for shape analysis
- ✅ GPA is standard method
- ✅ Check for outliers in Procrustes residuals
- ✅ Consider size as separate variable if needed

**PCA**:
- ✅ Examine scree plot for components to interpret
- ✅ First 3-5 PCs usually capture most variation
- ✅ Interpret PCs with caution (mathematical, not biological)
- ✅ Use PC scores as variables in other analyses

**CVA**:
- ✅ Requires prior groups (not exploratory clustering)
- ✅ Cross-validation for classification accuracy
- ✅ Mahalanobis distances for group separation
- ✅ Check assumptions (multivariate normality, equal covariance)

**MANOVA**:
- ✅ Tests null hypothesis (groups are same)
- ✅ Permutation tests for non-normal data
- ✅ Effect sizes matter more than p-values
- ✅ Follow with CVA to visualize differences

### Workflow Efficiency

**Keyboard Shortcuts**:
- `Ctrl+N`: New dataset
- `Ctrl+O`: Open database
- `Ctrl+S`: Save
- `Ctrl+I`: Import
- `Ctrl+E`: Export
- `F2`: Edit dataset/object
- `Delete`: Delete selected
- `Space`: Next object (in digitizing)

**Batch Operations**:
- Import multiple images at once
- Select multiple objects for batch editing
- Export multiple datasets together
- Use variables for batch grouping

**Backup Strategy**:
1. **Daily**: Automatic backup on exit (Tools → Preferences)
2. **Weekly**: Manual backup to external drive
3. **Major milestones**: Backup before large imports or analyses
4. File → Backup Database → Choose location

### Publication-Ready Results

**Figures**:
- Export plots as vector (PDF/SVG) for publication
- Use consistent color schemes
- Label axes clearly
- Include scale bars for landmark plots

**Tables**:
- Export statistics as CSV/Excel
- Round to appropriate precision
- Include sample sizes
- Report effect sizes

**Reproducibility**:
- Document all analysis parameters
- Save analysis results in database
- Export raw data for supplementary materials
- Version control for datasets (use JSON+ZIP exports)

---

## Appendix

### File Formats Reference

#### TPS Format

```
LM=10
1.5 2.3
2.1 3.4
3.2 4.1
...
ID=specimen_001
IMAGE=specimen_001.jpg
SCALE=0.05

LM=10
...
```

Fields:
- `LM=`: Number of landmarks
- Coordinates: X Y (one pair per line)
- `ID=`: Specimen identifier
- `IMAGE=`: Optional image filename
- `SCALE=`: Optional scale factor

#### NTS Format

```
"specimen_001"
10
1.5 2.3
2.1 3.4
...
"specimen_002"
10
...
```

#### Morphologika Format

```
[individuals]
specimen_001
specimen_002

[landmarks]
10

[dimensions]
2

[rawpoints]
1.5 2.3
2.1 3.4
...
```

### Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New dataset |
| `Ctrl+O` | Open database |
| `Ctrl+S` | Save |
| `Ctrl+I` | Import |
| `Ctrl+E` | Export |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+F` | Find |
| `F2` | Edit |
| `Delete` | Delete selected |
| `Space` | Next (in digitizing) |
| `Backspace` | Previous (in digitizing) |
| `Esc` | Cancel |
| `Ctrl+W` | Close dialog |

### Glossary

**Landmark**: A point location on an organism used for shape analysis.

**Procrustes Superimposition**: Alignment procedure to remove non-shape variation (position, rotation, scale).

**PCA (Principal Component Analysis)**: Dimensionality reduction technique to identify main axes of variation.

**CVA (Canonical Variate Analysis)**: Discriminant analysis to separate predefined groups.

**MANOVA (Multivariate Analysis of Variance)**: Test for significant differences among groups.

**Shape Space**: Mathematical space where each point represents a unique shape.

**Centroid Size**: Measure of size (square root of sum of squared distances from landmarks to centroid).

**Procrustes Distance**: Measure of shape difference between two configurations.

**Type I Landmark**: Homologous point (e.g., suture intersection).

**Type II Landmark**: Geometric homology (e.g., maximum curvature).

**Type III Landmark**: Arbitrary point on curve (semi-landmark).

---

## Version History

### 0.1.4 (2025-10-08)
- Comprehensive performance testing completed
- All performance targets exceeded by 8-5091×
- Production-ready performance validated
- UI responsiveness optimized
- Memory efficiency confirmed (125× better than target)

### 0.1.3
- Dialog extraction Phase 2 completed
- Test coverage improved to 93.5%
- Code organization enhanced

### 0.1.2
- Integration testing Phase 6 completed
- 1,240 total tests implemented
- Error recovery workflows validated

### 0.1.1
- Initial release
- Core functionality implemented
- 2D and 3D landmark support

---

## License

Modan2 is released under the MIT License.

Copyright (c) 2024-2025 Modan2 Development Team

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**For Modan2 Version**: 0.1.4+

For the latest documentation, visit: [documentation URL]
