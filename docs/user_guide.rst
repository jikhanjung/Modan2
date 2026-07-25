User Guide
==========

This guide provides comprehensive instructions for using Modan2 for geometric morphometric analysis.

Getting Started
---------------

Launching Modan2
~~~~~~~~~~~~~~~~

**From installed application**:

- **Windows**: Start Menu → Modan2
- **macOS**: Applications → Modan2.app
- **Linux**: Terminal: ``python3 main.py``

**From source**:

.. code-block:: bash

   cd Modan2
   python3 main.py

``main.py`` accepts ``--debug``, ``--db <path>`` (open a specific database),
``--lang <en|ko>``, and ``--no-splash``.

Main Window Overview
~~~~~~~~~~~~~~~~~~~~

The Modan2 main window consists of several key components:

1. **Menu Bar**: File, Edit, View, Data, Help
2. **Toolbar**: Quick access to common operations
3. **Dataset Tree View** (Left): Hierarchical view of datasets
4. **Object Table** (Center): List of objects in the selected dataset, with
   **LM Count** and **Curve** columns
5. **Object Preview** (Right): Visual preview of the selected object
   (toggle with ``Ctrl+P``)
6. **Status Bar** (Bottom): Information and progress indicators

Working with Datasets
---------------------

Creating a New Dataset
~~~~~~~~~~~~~~~~~~~~~~

1. Click **"New Dataset"** button or press ``Ctrl+N``
2. Enter dataset information:

   - **Name**: Descriptive name for your dataset
   - **Dimension**: 2D or 3D
   - **Description**: Optional detailed description
   - **Parent Dataset**: Optional - create hierarchical structure

3. Click **OK** to create the dataset

.. note::
   Hierarchical datasets allow you to organize related studies. For example:

   - Study_2024 (parent)

     - Subspecies_A (child)
     - Subspecies_B (child)

The dataset dialog is organized into tabs. Beyond the basic information above, it
also holds:

- **Wireframe / Baseline / Polygons**: define how landmarks are connected for
  display.
- **Landmark names**: a table giving each landmark index a name/abbreviation and
  a description (see :ref:`landmark-names`).
- **Curve scheme**: the dataset's semi-landmark curves — each with a name and a
  point count ``N`` (see :ref:`semi-landmark-curves`).

These schemes are shared by every object in the dataset, so a landmark name or a
curve you define once applies to all specimens.

Dataset Variables
~~~~~~~~~~~~~~~~~

Variables define grouping and categorical data for statistical analysis.

**Adding Variables**:

1. Select a dataset
2. Click **"Add Variable"** in the toolbar
3. Choose variable type:

   - **Categorical**: Groups (e.g., "male", "female", "juvenile")
   - **Continuous**: Numeric measurements (e.g., age, weight)

4. Enter variable name
5. For categorical variables, add possible values

**Setting Object Variables**:

1. Select object(s) in the table
2. Click on the variable column
3. Enter or select value
4. Press ``Enter`` or click away to save

**Example Workflow**:

.. code-block:: text

   Dataset: Bird Wings
   Variables:
     - Species (categorical): sparrow, robin, finch
     - Sex (categorical): male, female
     - Age (continuous): numeric

   Objects:
     - wing_001.jpg → Species: sparrow, Sex: male, Age: 2.5
     - wing_002.jpg → Species: sparrow, Sex: female, Age: 1.8

Importing Data
--------------

Importing 2D Images
~~~~~~~~~~~~~~~~~~~

**Supported formats**: JPG, PNG, BMP, TIFF, GIF

**Method 1: Drag and Drop**

1. Select a dataset in the tree view
2. Drag image files from your file manager
3. Drop them onto the dataset or object table
4. Images are automatically imported with filenames as object names

**Method 2: Import Dialog**

1. Select dataset → **File → Import Objects**
2. Click **"Add Images"**
3. Select one or more image files
4. Review the list
5. Click **"Import"**

.. tip::
   Use consistent naming: ``specimen_001.jpg``, ``specimen_002.jpg`` for easier sorting

Importing 3D Models
~~~~~~~~~~~~~~~~~~~~

**Supported formats**: OBJ, PLY, STL

**Method 1: Drag and Drop**

1. Select a 3D dataset
2. Drag 3D model files into the application
3. Models are imported with automatic scaling

**Method 2: Import Dialog**

1. **File → Import Objects → Add 3D Models**
2. Select files
3. Review and import

**3D Model Requirements**:

- Mesh should be manifold (closed surface)
- Reasonable polygon count (<100k faces recommended)
- Centered at origin for best visualization

Importing Landmark Files
~~~~~~~~~~~~~~~~~~~~~~~~~

**Supported formats**: TPS, NTS, X1Y1, Morphologika, and JSON+ZIP dataset
packages.

Open **File → Import** (``Ctrl+I``). Modan2 detects the format from the file
extension (``.tps``, ``.nts``, ``.txt`` for Morphologika, ``.zip`` for a
JSON+ZIP package), but you can also pick it explicitly with the format radio
buttons. An **Invert Y** option flips the Y axis for files that use a
bottom-left origin.

.. note::
   **Missing-landmark placeholder.** If an imported file contains the
   ``-999`` morphometrics placeholder, Modan2 asks whether to treat those
   coordinates as missing landmarks (recommended). Tick the "always" option to
   remember your answer. The invert-Y option is accounted for before the scan.

.. note::
   **Semi-landmark curves in TPS.** ``CURVES=`` / ``POINTS=`` blocks in a TPS
   file are read in as semi-landmark curves (see :ref:`semi-landmark-curves`).

**TPS Format Example**:

.. code-block:: text

   LM=5
   12.5 34.2
   45.6 78.9
   23.1 56.4
   67.8 12.3
   89.0 45.6
   IMAGE=specimen_001.jpg
   ID=1

   LM=5
   15.2 32.8
   ...

**Importing a landmark file**:

1. **File → Import** (``Ctrl+I``)
2. Select the file (TPS, NTS, X1Y1, or Morphologika)
3. Modan2 will:

   - Create objects for each specimen
   - Link to image files (if an ``IMAGE=`` field exists)
   - Import landmark coordinates (and any curves, for TPS)

4. Click **"Import"**

Importing a Dataset Package (JSON+ZIP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A **JSON+ZIP package** (``.zip``) is Modan2's own complete-backup format: it
bundles the dataset's metadata, landmark names, curve scheme, variables, and —
optionally — the image and 3D-model files. Importing one recreates the whole
dataset, including traced semi-landmark curves and missing landmarks.

1. **File → Import** (``Ctrl+I``)
2. Select the ``.zip`` package
3. Click **"Import"**

Packages are imported inside a transaction and roll back on any error, and
extraction is hardened against path-traversal ("Zip Slip") archives. Older
packages (schema 1.1) still import; curves default to empty for those.

Working with Objects
--------------------

Viewing an Object
~~~~~~~~~~~~~~~~~

**Double-click** an object in the table to open the **Object Dialog**.

The Object Dialog shows:

- Object metadata (name, ID, creation date)
- Associated image or 3D model
- Landmark table
- 2D/3D viewer with landmarks visualized

The Object Dialog has mode buttons that decide what a click does:
**Landmark** (place/move landmarks, the default), **Curve** (trace a
semi-landmark curve), and **Calibration** (set the image scale). Only one is
active at a time.

Placing Landmarks (2D)
~~~~~~~~~~~~~~~~~~~~~~

1. Open the Object Dialog for a 2D object (**Landmark** mode is active by default)
2. Click on the image to place a landmark
3. Landmarks are numbered sequentially (1, 2, 3, ...)
4. Click and drag an existing landmark to move it
5. Right-click a landmark to delete it

**Mouse in the 2D viewer**:

- **Mouse wheel** - Zoom in/out
- **Right-drag on empty space** - Pan the image
- ``Ctrl+W`` - Close the dialog

Placing Landmarks (3D)
~~~~~~~~~~~~~~~~~~~~~~

1. Open Object Dialog for a 3D object
2. Rotate the model:

   - **Left mouse drag**: Rotate
   - **Right mouse drag**: Pan
   - **Mouse wheel**: Zoom

3. Click on the surface to place a landmark
4. Landmarks appear as colored spheres
5. Right-click a landmark to delete it

**3D Viewer Controls**:

- **Left-drag**: rotate
- **Right-drag**: pan
- **Mouse wheel**: zoom
- **3D Model** / **Rotate** checkboxes: show the mesh, and auto-rotate it

Editing Landmark Coordinates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**In the landmark table**:

1. Double-click a coordinate cell
2. Enter new value
3. Press ``Enter`` to save
4. The viewer updates automatically

**Manual coordinate entry is useful for**:

- Precise adjustments
- Correcting digitization errors
- Importing coordinates from external sources

Missing Landmarks
~~~~~~~~~~~~~~~~~

If a landmark cannot be placed (damaged specimen, obscured feature), mark it
missing in the landmark table instead of skipping it — this keeps the landmark
count consistent across the dataset. To mark a landmark missing:

- Click **"Add Missing"** to append a missing landmark, **or**
- Select a row first and the button becomes **"Insert Missing"**, which inserts
  the gap *before* the selected row (so it lands where it belongs), **or**
- Type ``MISSING`` into a coordinate cell, or leave the cell blank.

A cell only accepts a number or ``MISSING`` (blank counts as missing); anything
else reverts to the stored value with an explanatory tooltip.

**Visualizing missing landmarks** with the **"Show Estimated"** checkbox (on by
default) draws a hollow circle at each missing landmark's estimated position.
Uncheck it to hide the estimates.

**How estimation works**: Modan2 fits the dataset's mean shape onto the
landmarks the specimen actually has — matching rotation, scale, and position (a
similarity transform) — then reads the missing positions off the fitted mean.
This stays accurate even when a specimen was photographed at an angle.

.. note::
   During analysis, missing landmarks are filled with the same method and
   refined as the alignment settles. See :ref:`analysis-missing-landmarks`.

.. _landmark-names:

Landmark Names
~~~~~~~~~~~~~~

You can give each landmark a name/abbreviation and a description at the **dataset**
level, so they apply to every specimen.

1. In the Object Dialog, click **"Landmark Names"** (or use the dataset dialog's
   landmark-names tab)
2. Fill in the **Name** and **Description** columns for each landmark index
3. Click **Save**

While digitizing, switch the label mode with the **Show** checkbox and the
**Index** / **Name** radio buttons: **Name** draws the landmark's name instead of
its number, and the description appears as a tooltip.

.. _semi-landmark-curves:

Semi-landmark Curves
~~~~~~~~~~~~~~~~~~~~~

Semi-landmarks let you capture a *curve* (an outline or ridge) rather than
discrete points. You trace the curve on each specimen, and Modan2 resamples it
into a fixed number of evenly-spaced points along its length. Analysis treats
those points like ordinary landmarks — the fixed (anatomical) landmarks keep
their positions and indices, and the semi-landmarks follow after them. A dataset
can even be analyzed with only semi-landmarks and no fixed landmarks.

The raw trace is kept with the specimen, so you can re-trace it or change the
point count at any time. Semi-landmark curves are a **2D** feature.

**Tracing a curve**:

1. Open the Object Dialog for a 2D object and click the **Curve** mode button
   (tooltip: *Trace a curve (semi-landmarks)*)
2. Click along the curve to lay down points
3. Press **Enter** or **double-click** to accept the trace; press **Esc** or
   **right-click** to cancel
4. For a brand-new curve you are asked **"Number of semi-landmarks on this
   curve"** (default 10). This count is dataset-wide, so it applies to that curve
   on every specimen.

**Snap to curve (live-wire edge detection)** — on by default in Curve mode. The
trace snaps to the strongest image edge between your clicks, so a clean outline
needs only a few clicks (start and end for a gentle curve, a couple of points in
between for a sharp one). Uncheck **"Snap to curve"** for a plain hand trace.

**Smooth curve** — on by default. Removes the pixel staircase from a snapped
trace so the semi-landmarks sit on a clean curve, while the points you clicked
stay put. Toggle with the **"Smooth curve"** checkbox. (Snap and Smooth are only
available in Curve mode.)

**Editing a traced curve**:

- Click a curve to select it (it draws thicker, with square anchor handles)
- Drag a point to move it; click the line to add a point; right-click a point for
  **Delete Point** or the whole curve for **Delete Curve**
- Snapped curves are edited by their clicked anchors and re-snap to the edge live
  as you drag

**The curve table** (in the Object Dialog) lists each curve with **Name**, **N**
(point count), and **Traced** (✓). Editing **N** re-resamples the curve.
Right-click a row → **"Delete Curve (all specimens)"** removes that curve from the
whole dataset.

Curves are held in memory while you work and written to the database on **Save**.

Digitizing Aids
~~~~~~~~~~~~~~~

- **Show Expected** (2D): once at least two landmarks are placed on a new
  specimen, the remaining positions are predicted from the dataset mean shape and
  shown as a guide, so you know roughly where each one goes. Off by default.
- **Show Original** (2D): when a specimen's image was downscaled on import (its
  longer side exceeded 2560 px), an archived full-resolution original is kept.
  Tick **"Show Original"** to render the viewer from that original for extra
  detail while digitizing. This affects display only — coordinates stay in the
  working-copy pixel space. The checkbox appears only when an original exists.

Display Options
~~~~~~~~~~~~~~~

In the Object Dialog, customize visualization:

- **Show** + **Index** / **Name**: toggle landmark labels and choose whether the
  label is the index number or the landmark name
- **Wireframe**: connect landmarks along the dataset wireframe
- **Polygon**: fill defined polygons
- **Baseline**: highlight the baseline landmarks
- **Show Estimated**: hollow circles at estimated positions of missing landmarks
- **Show Expected**: predicted positions of not-yet-placed landmarks (see
  Digitizing Aids)
- **Curve**: show the raw traced curves
- **Semi-LM**: show the derived semi-landmarks
- **3D Model** / **Rotate** (3D objects): show the mesh and auto-rotate it

Landmark size, wireframe thickness, and label size are set in
**Preferences** (separately for 2D and 3D).

Statistical Analysis
--------------------

Overview
~~~~~~~~

Modan2 provides three main statistical analyses:

1. **Principal Component Analysis (PCA)**: Explore shape variation
2. **Canonical Variate Analysis (CVA)**: Discriminate between groups
3. **MANOVA**: Test for group differences

All analyses require **Procrustes superimposition** as a preprocessing step.

Running an Analysis
~~~~~~~~~~~~~~~~~~~

A single analysis run performs the superimposition and then computes **PCA, CVA,
and MANOVA together** — you don't pick one type. The results are saved with the
dataset and can be re-opened later.

1. Select a dataset in the tree view
2. Click **Analyze** (``Ctrl+G``) or use the **Data** menu
3. In the analysis dialog, set:

   - **Analysis name** (a unique name is suggested)
   - **Superimposition method**: Procrustes (Bookstein and Resistant Fit are
     listed but currently disabled)
   - **CVA grouping variable**: the categorical variable that defines groups for CVA
   - **MANOVA grouping variable**: the categorical variable for MANOVA

4. Click **"OK"** to run. Progress is shown, and if CVA/MANOVA cannot be computed
   (e.g. too few groups) the failure is reported rather than silently skipped.
5. Explore the results in the **Data Exploration** dialog.

.. _analysis-procrustes:

Procrustes Superimposition
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What it does**:

- Aligns all shapes to a common coordinate system
- Removes differences due to position, rotation, and scale
- Leaves only shape variation

**Handling Missing Landmarks**:

If your dataset has missing landmarks, Procrustes fills them in with an
EM-style refinement loop (see :ref:`analysis-missing-landmarks`).

**Superimposition method**:

Procrustes (Generalized Procrustes Analysis) is the method used for analysis.
*Bookstein* (two-point baseline registration) and *Resistant Fit* (outlier-robust
alignment) appear in the dialog but are currently disabled.

**When Procrustes Runs**:

- Automatically as the first step of every analysis run
- The aligned shapes feed PCA, CVA, and MANOVA

.. _analysis-pca:

Principal Component Analysis (PCA)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Identify major axes of shape variation

**Use when**:

- Exploring shape diversity
- Visualizing morphospace
- Identifying outliers
- Reducing dimensionality

**Running PCA**: PCA is computed automatically as part of every analysis run (see
`Running an Analysis`_). Open the completed analysis in the **Data Exploration**
dialog to explore its principal components.

**Interpreting Results**:

The **Data Exploration Dialog** opens with:

- **Scree Plot**: Shows variance explained by each PC

  - X-axis: PC number
  - Y-axis: % variance
  - Look for "elbow" to determine how many PCs are meaningful

- **PC Score Plot**: Scatter plot of specimens

  - X-axis: PC1 (usually highest variance)
  - Y-axis: PC2 (second highest)
  - Points colored by groups (if variables defined)

- **Shape Variation Wireframes**:

  - Shows shape changes along each PC
  - Min/Max shapes at extremes of PC axis

- **PC Scores Table**: Numeric scores for each specimen

**Exporting PCA Results**:

- **Export PC Scores**: CSV file with scores for each object
- **Export Loadings**: Landmark contributions to each PC
- **Export Plot**: Save scatter plot as PNG/PDF

**Example Workflow**:

.. code-block:: text

   Dataset: Skull shapes (50 specimens, 20 landmarks)

   PCA Results:
     PC1: 45% variance → Overall size (allometry)
     PC2: 23% variance → Skull width
     PC3: 12% variance → Jaw length

   Interpretation:
     - Most variation is size-related
     - PC2 separates species A (narrow) vs. B (wide)
     - PC3 shows sexual dimorphism within species

.. _analysis-cva:

Canonical Variate Analysis (CVA)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Maximize separation between predefined groups

**Use when**:

- Discriminating between species/populations
- Testing classification accuracy
- Identifying diagnostic features

**Requirements**:

- At least 2 groups defined via dataset variables
- At least 2 specimens per group

**Running CVA**: CVA is computed as part of every analysis run. In the analysis
dialog, set the **CVA grouping variable** to the categorical variable that
defines your groups (e.g. "Species"), then open the result in **Data
Exploration**.

**Interpreting Results**:

- **CV Score Plot**: Specimens plotted on CV axes

  - Ideally, groups form distinct clusters
  - Overlap indicates similarity

- **Classification Table**: Shows how well CVA discriminates

  - Rows: True group
  - Columns: Predicted group
  - Diagonal = correct classifications
  - Off-diagonal = misclassifications

- **Discriminant Function**: Statistical details

  - Wilks' Lambda: Smaller = better separation (0-1 scale)
  - P-value: Significance of group differences

**Example**:

.. code-block:: text

   Dataset: Bird beaks, Variable: Species (A, B, C)

   CVA Results:
     CV1: 78% discrimination
     CV2: 15% discrimination

   Classification Table:
              Predicted A  Predicted B  Predicted C
   Actual A      18           2            0
   Actual B       1          19            0
   Actual C       0           1           19

   Overall accuracy: 93.3%

.. _analysis-manova:

MANOVA
~~~~~~

**Purpose**: Test if groups differ significantly in shape

**Use when**:

- Formal hypothesis testing
- Comparing multiple groups simultaneously
- Assessing effect size

**Running MANOVA**: MANOVA is computed as part of every analysis run. In the
analysis dialog, set the **MANOVA grouping variable** to the categorical variable
you want to test.

**Interpreting Results**:

- **Wilks' Lambda**: Test statistic (0-1)

  - Smaller = more group separation
  - 0 = perfect separation
  - 1 = no separation

- **F-statistic**: Ratio of between-group to within-group variation
- **P-value**: Probability that group differences are due to chance

  - P < 0.05: Significant difference (reject null hypothesis)
  - P ≥ 0.05: No significant difference

- **Effect Size (Partial η²)**: Proportion of variance explained by groups

**Example**:

.. code-block:: text

   Hypothesis: Male and female skulls differ in shape

   MANOVA Results:
     Wilks' Lambda: 0.234
     F(40, 18) = 3.45
     P-value: 0.002
     Partial η²: 0.766

   Conclusion: Significant sex-related shape differences (P < 0.05)
   76.6% of shape variation explained by sex

.. _analysis-missing-landmarks:

Handling Missing Landmarks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Modan2 fills in missing landmarks automatically during analysis, using an
EM-style refinement loop that interleaves alignment and imputation:

1. Align all specimens, leaving missing landmarks as gaps (the mean shape is
   computed ignoring the gaps, and each specimen is aligned on the landmarks it
   actually has).
2. For each specimen with missing data, fit the current mean shape onto its
   observed landmarks by a similarity transform (rotation, scale, and
   translation) and read the missing positions off the fitted mean.
3. Re-align with the filled-in values, then **re-open the original gaps** and
   re-estimate them from the improved mean.
4. Repeat step 3 a small number of times so estimates keep improving as the
   alignment settles (they are never fitted on previous estimates).

Imputed values live only in the analysis working copy — they are never written
back to the database. PCA, CVA, and MANOVA then run on the aligned coordinates.

.. note::
   This is the same shape-fitting method used by the "Show Estimated" and "Show
   Expected" previews in the Object Dialog. On synthetic test shapes where the
   true answer is known, its error is essentially zero.

**Best Practices**:

- Aim for <10% missing landmarks in your dataset
- Keep a good number of complete (or near-complete) specimens
- Use biological knowledge to verify estimated positions make sense

Visualization
-------------

2D Viewer
~~~~~~~~~

**Features**:

- Zoom: mouse wheel
- Pan: right-drag on empty space
- Landmark overlay: colored circles with index or name labels
- Semi-landmark curves and their derived points (toggle with the **Curve** and
  **Semi-LM** checkboxes)

3D Viewer
~~~~~~~~~

**Controls**:

- **Rotate**: left-drag
- **Pan**: right-drag
- **Zoom**: mouse wheel

**Landmark Display**:

- Landmarks rendered as spheres
- Size adjustable in **Preferences**
- Index/name labels optional

Statistical Plots
~~~~~~~~~~~~~~~~~

**Available Plots**:

- **Scree Plot** (PCA): Variance explained per PC
- **PC Score Plot** (PCA): Specimens on PC axes
- **CV Score Plot** (CVA): Specimens on CV axes
- **Shape Variation Plot**: Wireframes at PC/CV extremes

**Customization**:

- **Group Colors**: Auto-assigned by variable
- **Point Size**: Adjustable
- **Axis Labels**: Automatic with variance %
- **Legend**: Shows group names and colors

**Exporting Plots**:

1. Right-click on plot → **"Export Plot"**
2. Formats: PNG, SVG, PDF
3. Resolution: 300 DPI default (adjustable)

Data Export
-----------

Exporting Datasets
~~~~~~~~~~~~~~~~~~

Select a dataset and choose **Export** (``Ctrl+E``).

1. Choose the export **format**:

   - **TPS**: landmark coordinates in TPS format
   - **X1Y1**: plain coordinate columns
   - **Morphologika**: Morphologika format (with images and metadata)
   - **JSON+ZIP**: a complete dataset package (see below)

2. Choose the **superimposition** applied on export: **None** (raw coordinates) or
   **Procrustes** (aligned). For a raw TPS export, traced semi-landmark curves are
   written under ``CURVES=`` / ``POINTS=`` blocks; a Procrustes export writes the
   merged aligned landmarks.
3. Pick which objects to include from the object list.
4. Click **"Export"**.

Exporting a Dataset Package (JSON+ZIP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **JSON+ZIP** format is Modan2's complete-backup format. It captures the
dataset metadata, landmark names, curve scheme, variables, landmarks, and traced
curves in a JSON manifest, and can bundle the image and 3D-model files alongside
it.

- Tick **"Include image and model files"** to bundle the media; an **Estimated
  size** figure updates as you change the options.
- The output is a ``<dataset>_<timestamp>.zip`` you can archive or share, and
  re-import losslessly on another machine (see `Importing a Dataset Package
  (JSON+ZIP)`_).

Exporting Analysis Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the **Data Exploration Dialog**:

- **Export PC Scores**: CSV with scores per specimen
- **Export Shape Data**: Aligned landmark coordinates (post-Procrustes)
- **Export Statistics**: Summary statistics (mean, SD, etc.)

Keyboard Shortcuts
------------------

Main Window
~~~~~~~~~~~

- ``Ctrl+N`` - New Dataset
- ``Ctrl+Shift+N`` - New Object
- ``Ctrl+Shift+O`` - Edit Object
- ``Ctrl+S`` - Save Changes
- ``Ctrl+I`` - Import
- ``Ctrl+E`` - Export
- ``Ctrl+G`` - Analyze
- ``Ctrl+P`` - Toggle object preview
- ``Ctrl+W`` - Exit
- ``F1`` - About

Object Dialog (Curve mode)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Enter** / **double-click** - Accept the current trace
- **Esc** / **right-click** - Cancel the current trace
- **Right-click a curve point** - Delete Point / Delete Curve
- ``Ctrl+W`` - Close the dialog

Preferences
-----------

Open **Edit → Preferences**.

General
~~~~~~~

- **Language**: English or Korean (한국어), applied immediately
- **Remember Geometry**: restore window size/position between sessions (Yes/No)
- **Toolbar Icon Size**: Small / Medium / Large

Viewer Appearance
~~~~~~~~~~~~~~~~~~

Set separately for **2D** and **3D**:

- **Landmark** size: Small / Medium / Large
- **Wireframe** thickness: Thin / Medium / Thick
- **Index** (label) size: Small / Medium / Large

Also:

- **Background Color**: viewer background

Plot Appearance
~~~~~~~~~~~~~~~~

- **Data point size**: Small / Medium / Large
- **Data point colors** and **Data point markers**: per-group defaults used in the
  Data Exploration plots

Tips and Best Practices
------------------------

Data Organization
~~~~~~~~~~~~~~~~~

1. **Use consistent naming**: ``species_ID_number.jpg`` (e.g., ``sparrow_001.jpg``)
2. **Organize hierarchically**: Group related datasets
3. **Document metadata**: Use description fields
4. **Back up regularly**: Export database or copy ``modan.db``

Landmark Placement
~~~~~~~~~~~~~~~~~~

1. **Define landmarks carefully**: Use anatomically meaningful points
2. **Be consistent**: Same landmarks across all specimens
3. **Use high-resolution images**: Better precision
4. **Avoid ambiguous points**: Choose clear, repeatable features
5. **Document landmarks**: Write down definitions (e.g., "tip of beak")

Statistical Analysis
~~~~~~~~~~~~~~~~~~~~

1. **Check assumptions**: Normal distribution, homogeneity of variance
2. **Sample size**: At least 30 specimens for PCA, 10+ per group for CVA
3. **Validate results**: Cross-validation, bootstrap resampling
4. **Interpret cautiously**: Statistical significance ≠ biological significance
5. **Visualize first**: Explore with PCA before formal tests

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

1. **Limit 3D polygon count**: Simplify meshes before import
2. **Let large photos downscale**: oversized images (longer side > 2560 px) are
   stored as a smaller working copy automatically, with the original archived;
   use **Show Original** only when you need full detail
3. **Run analyses on subsets**: test on a small sample first

Common Workflows
----------------

Workflow 1: 2D Morphometric Study
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   1. Collect images (photographs, scans)
   2. Create dataset in Modan2
   3. Import images
   4. Define landmarks (e.g., 15 points on butterfly wing)
   5. Place landmarks on all specimens
   6. Define variables (species, sex, location)
   7. Run Procrustes + PCA
   8. Explore shape variation
   9. Run CVA if groups exist
   10. Export results for publication

Workflow 2: 3D Morphometric Study
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   1. Acquire 3D scans (CT, laser, photogrammetry)
   2. Clean/process meshes (MeshLab, Blender)
   3. Import OBJ/PLY files to Modan2
   4. Place 3D landmarks
   5. Run Procrustes
   6. Perform PCA/CVA
   7. Export shape data for further analysis (R, Python)

Workflow 3: Missing Data Study
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   1. Import dataset with incomplete specimens
   2. Mark missing landmarks ("Add/Insert Missing", or type MISSING in a cell)
   3. Verify estimation: Object Dialog -> "Show Estimated" checkbox
   4. Run the analysis (missing landmarks are imputed automatically)
   5. Explore PCA/CVA/MANOVA results in Data Exploration
   6. Validate results against a complete-specimen-only analysis

Troubleshooting
---------------

Analysis Fails
~~~~~~~~~~~~~~

**Error**: ``Not enough complete specimens for Procrustes``

**Solution**: Need at least 2 complete specimens without missing landmarks

**Error**: ``CVA requires at least 2 groups``

**Solution**: Define a grouping variable with multiple values

Landmarks Not Showing
~~~~~~~~~~~~~~~~~~~~~

**Problem**: Placed landmarks but not visible

**Solution**:

- Check the "Show" checkbox is enabled (with Index or Name selected)
- Increase the landmark size in Preferences
- Zoom in - landmarks may be too small

Slow Performance
~~~~~~~~~~~~~~~~

**Problem**: Application freezes during analysis

**Solution**:

- Reduce dataset size (split into smaller datasets)
- Close other applications
- Simplify 3D meshes (reduce polygon count)

Next Steps
----------

- Explore the :doc:`developer_guide` to contribute or extend Modan2
- Check the :doc:`changelog` for latest features and bug fixes
- Visit the `GitHub repository <https://github.com/jikhanjung/Modan2>`_ for example datasets
