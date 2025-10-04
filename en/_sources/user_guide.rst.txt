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
- **Linux**: Terminal: ``python3 Modan2.py``

**From source**:

.. code-block:: bash

   cd Modan2
   python3 Modan2.py

Main Window Overview
~~~~~~~~~~~~~~~~~~~~

The Modan2 main window consists of several key components:

1. **Menu Bar**: File, Edit, View, Tools, Help
2. **Toolbar**: Quick access to common operations
3. **Dataset Tree View** (Left): Hierarchical view of datasets
4. **Object Table** (Center): List of objects in the selected dataset
5. **Object Preview** (Right): Visual preview of selected object
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

**Supported formats**: TPS, NTS, CSV

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

**Importing TPS/NTS**:

1. **File → Import → Import Landmark File**
2. Select TPS or NTS file
3. Modan2 will:

   - Create objects for each specimen
   - Link to image files (if IMAGE= field exists)
   - Import landmark coordinates

4. Click **"Import"**

**CSV Format**:

.. code-block:: text

   object,lm1_x,lm1_y,lm2_x,lm2_y,lm3_x,lm3_y
   specimen_001,12.5,34.2,45.6,78.9,23.1,56.4
   specimen_002,15.2,32.8,48.1,76.2,25.3,54.7

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

Placing Landmarks (2D)
~~~~~~~~~~~~~~~~~~~~~~

1. Open Object Dialog for a 2D object
2. Click on the image to place a landmark
3. Landmarks are numbered sequentially (1, 2, 3, ...)
4. Right-click a landmark to delete it
5. Click and drag to move an existing landmark

**Keyboard Shortcuts in Object Dialog**:

- ``Ctrl+Z`` - Undo last landmark
- ``Delete`` - Remove selected landmark
- ``+/-`` - Zoom in/out
- ``Space+Drag`` - Pan image
- ``Home`` - Reset zoom

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

- ``R`` - Reset camera
- ``W`` - Wireframe mode
- ``S`` - Solid/surface mode
- ``L`` - Toggle lighting

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

If a landmark cannot be placed (damaged specimen, obscured feature):

1. Leave the landmark position empty, or
2. Right-click in the landmark table → **"Mark as Missing"**
3. The cell shows **"MISSING"**
4. In the viewer:

   - **Checkbox "Show Estimated" checked**: Hollow circle shows estimated position
   - **Checkbox unchecked**: No visualization

**How Estimation Works**:

- Modan2 uses Procrustes-aligned mean shape from complete specimens
- Estimates are transformed to match the scale and position of the current object
- Estimated landmarks shown as **hollow circles** with **"3?"** label

.. note::
   Missing landmarks are handled during Procrustes superimposition through iterative imputation. See :ref:`analysis-missing-landmarks` for details.

Display Options
~~~~~~~~~~~~~~~

In the Object Dialog, customize visualization:

- **Show Landmarks**: Toggle landmark visibility
- **Show Index**: Show/hide landmark numbers
- **Show Polygon**: Connect landmarks with lines (wireframe)
- **Show Baseline**: Highlight baseline between specific landmarks
- **Show Estimated**: Display estimated positions for missing landmarks (hollow circles)

**Size Controls**:

- **Landmark Size**: Adjust circle radius
- **Index Size**: Adjust label font size

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

1. Select a dataset in the tree view
2. Click **"Analyze Dataset"** button or menu: **Tools → Analyze Dataset**
3. The **New Analysis Dialog** opens:

   - **Analysis Type**: PCA, CVA, or MANOVA
   - **Dataset**: Pre-selected
   - **Options**: Analysis-specific settings

4. Configure options (see below)
5. Click **"OK"** to run

.. _analysis-procrustes:

Procrustes Superimposition
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What it does**:

- Aligns all shapes to a common coordinate system
- Removes differences due to position, rotation, and scale
- Leaves only shape variation

**Handling Missing Landmarks**:

If your dataset has missing landmarks, Procrustes uses **iterative imputation**:

1. Start with complete specimens only
2. Compute mean shape
3. Estimate missing landmarks from mean
4. Re-run Procrustes with estimated values
5. Repeat until convergence (max 100 iterations)

**Options**:

- **Reference Shape**:
  - *Mean shape*: Default, uses average
  - *First object*: Uses first specimen as reference

**When Procrustes Runs**:

- Automatically before PCA, CVA, or MANOVA
- Results are cached - subsequent analyses reuse aligned shapes

.. _analysis-pca:

Principal Component Analysis (PCA)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Identify major axes of shape variation

**Use when**:

- Exploring shape diversity
- Visualizing morphospace
- Identifying outliers
- Reducing dimensionality

**Running PCA**:

1. **Tools → Analyze Dataset → PCA**
2. Options:

   - **Number of PCs**: How many principal components to compute (default: all)
   - **Use Covariance Matrix**: Unchecked = correlation matrix (default)

3. Click **OK**

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

**Running CVA**:

1. **Tools → Analyze Dataset → CVA**
2. Options:

   - **Grouping Variable**: Select categorical variable (e.g., "Species")
   - **Number of CVs**: Default = min(groups-1, landmarks*2)

3. Click **OK**

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

**Running MANOVA**:

1. **Tools → Analyze Dataset → MANOVA**
2. Options:

   - **Grouping Variable**: Select categorical variable
   - **Alpha Level**: Significance threshold (default: 0.05)

3. Click **OK**

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

Modan2 automatically handles missing landmarks during analysis:

**During Procrustes**:

1. Identifies complete specimens (no missing landmarks)
2. Runs Procrustes on complete specimens → mean shape
3. For each specimen with missing data:

   - Estimates missing landmarks from mean shape
   - Applies scale/position transformation to match the specimen
   - Updates coordinates in temporary working copy (NOT in database)

4. Re-runs Procrustes with estimated values
5. Repeats until convergence

**During PCA/CVA/MANOVA**:

- Uses coordinates after Procrustes (with imputed values)
- Missing landmarks are treated as estimated values
- No further imputation needed

**Limitations**:

- Simple mean-based imputation (advanced methods in future releases)
- Accuracy depends on having sufficient complete specimens
- Large amounts of missing data (>30%) may affect results

**Best Practices**:

- Aim for <10% missing landmarks in your dataset
- Ensure at least 50% of specimens are complete
- Use biological knowledge to verify estimated positions make sense

Visualization
-------------

2D Viewer
~~~~~~~~~

**Features**:

- Zoom: Mouse wheel or ``+/-``
- Pan: Space + drag or middle mouse button
- Reset view: ``Home`` key
- Landmark overlay: Colored circles with indices

**Export Options**:

- Right-click → **"Export Image"**
- Formats: PNG, JPG, PDF
- Resolution: Original or custom DPI

3D Viewer
~~~~~~~~~

**Controls**:

- **Rotate**: Left mouse drag
- **Pan**: Right mouse drag or Shift + left drag
- **Zoom**: Mouse wheel
- **Reset**: ``R`` key

**Rendering Modes**:

- **Wireframe** (``W``): Shows mesh edges
- **Solid** (``S``): Filled surface with lighting
- **Wireframe + Solid**: Both simultaneously

**Landmark Display**:

- Landmarks rendered as spheres
- Size adjustable via slider
- Index labels optional

**Lighting**:

- Toggle: ``L`` key
- Improves depth perception for complex surfaces

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

**File → Export Dataset**

1. Select dataset
2. Choose export format:

   - **TPS**: Landmark coordinates in TPS format
   - **NTS**: NTS format (legacy)
   - **CSV**: Spreadsheet-compatible
   - **JSON**: Machine-readable with metadata

3. Options:

   - **Include Analysis Results**: Embed PC/CV scores
   - **Include Variables**: Export grouping data
   - **Include Missing**: Export "NA" for missing landmarks

4. Click **"Export"**

**CSV Export Format**:

.. code-block:: text

   object,lm1_x,lm1_y,lm2_x,lm2_y,species,sex,PC1,PC2
   spec_001,12.5,34.2,45.6,78.9,A,male,0.234,-0.123
   spec_002,15.2,32.8,48.1,76.2,A,female,0.156,-0.089

Exporting Analysis Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the **Data Exploration Dialog**:

- **Export PC Scores**: CSV with scores per specimen
- **Export Shape Data**: Aligned landmark coordinates (post-Procrustes)
- **Export Statistics**: Summary statistics (mean, SD, etc.)

Keyboard Shortcuts
------------------

Global Shortcuts
~~~~~~~~~~~~~~~~

- ``Ctrl+N`` - New Dataset
- ``Ctrl+Shift+N`` - New Object
- ``Ctrl+O`` - Open Database
- ``Ctrl+S`` - Save Changes
- ``Ctrl+W`` - Close Window
- ``Ctrl+Q`` - Quit Application
- ``Delete`` - Delete Selected Items
- ``F5`` - Refresh View

Object Dialog
~~~~~~~~~~~~~

- ``Ctrl+Z`` - Undo Last Action
- ``Delete`` - Remove Selected Landmark
- ``+`` / ``-`` - Zoom In/Out
- ``Home`` - Reset Zoom
- ``Space+Drag`` - Pan
- ``Ctrl+C`` - Copy Landmark Coordinates
- ``Ctrl+V`` - Paste Coordinates

3D Viewer
~~~~~~~~~

- ``R`` - Reset Camera
- ``W`` - Wireframe Mode
- ``S`` - Solid Mode
- ``L`` - Toggle Lighting
- ``F`` - Fit to View

Preferences
-----------

**File → Preferences** or ``Ctrl+,`` (macOS: ``Cmd+,``)

General Settings
~~~~~~~~~~~~~~~~

- **Default Database Location**: Where new databases are created
- **Auto-Save Interval**: Frequency of automatic saves (0 = disabled)
- **Language**: English or Korean (한국어)

Display Settings
~~~~~~~~~~~~~~~~

- **Landmark Color**: Default color for new objects
- **Index Color**: Color for landmark number labels
- **Background Color**: Viewer background (white/black/gray)
- **Font Size**: UI text size
- **Theme**: Light or Dark (if available)

Analysis Settings
~~~~~~~~~~~~~~~~~

- **Max Procrustes Iterations**: Default 100
- **Convergence Threshold**: When to stop iterating (default: 0.0001)
- **PCA Method**: Covariance or Correlation matrix
- **CVA Cross-Validation**: Leave-one-out or K-fold

Advanced Settings
~~~~~~~~~~~~~~~~~

- **Enable Logging**: Write debug logs to file
- **Log Level**: INFO, DEBUG, WARNING, ERROR
- **GPU Acceleration**: Use GPU for 3D rendering (if available)
- **Memory Limit**: Max RAM for large datasets (MB)

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

1. **Close unused datasets**: Reduces memory usage
2. **Limit 3D polygon count**: Simplify meshes before import
3. **Use lower resolution for preview**: Full resolution for analysis only
4. **Run analyses on subsets**: Test on small sample first
5. **Clear cache**: Tools → Clear Cache (if application becomes slow)

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
   2. Mark missing landmarks (right-click → "Mark as Missing")
   3. Verify estimation: Object Dialog → "Show Estimated" checkbox
   4. Run Procrustes (automatic imputation)
   5. Check convergence (logged in console)
   6. Run PCA/CVA/MANOVA with imputed data
   7. Validate results against complete-specimen-only analysis

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

- Check "Show Landmarks" checkbox is enabled
- Adjust "Landmark Size" slider
- Zoom in - landmarks may be too small

Slow Performance
~~~~~~~~~~~~~~~~

**Problem**: Application freezes during analysis

**Solution**:

- Reduce dataset size (split into smaller datasets)
- Close other applications
- Increase RAM allocation (Preferences → Memory Limit)
- Simplify 3D meshes (reduce polygon count)

Next Steps
----------

- Explore the :doc:`developer_guide` to contribute or extend Modan2
- Check the :doc:`changelog` for latest features and bug fixes
- Visit the `GitHub repository <https://github.com/jikhanjung/Modan2>`_ for example datasets
