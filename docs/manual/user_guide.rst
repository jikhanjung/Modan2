User Guide
==========

This guide provides comprehensive instructions for using Modan2 for geometric morphometric analysis.

Getting Started
---------------

Launching Modan2
~~~~~~~~~~~~~~~~

- **Windows**: Start Menu → Modan2
- **macOS**: Applications → Modan2.app
- **Linux**: run the AppImage

See :doc:`installation` for how to obtain each package.

Checking for Updates
~~~~~~~~~~~~~~~~~~~~

Open **Help → About** (``F1``). Modan2 asks GitHub whether a newer release has
been published and, if there is one, shows its version with a link to the
installer for your system and to its release notes. Nothing is downloaded or
installed automatically, and Modan2 contacts GitHub only when you open this box
(once per session).

- Running a **beta or other pre-release**, you are offered later builds of the
  same version (e.g. 0.2.0-beta.6 or 0.2.0-rc.1 after 0.2.0-beta.5) and any
  newer stable release — not test builds of the next version.
- Running a **stable** release, you are offered newer stable releases only.

If the check fails (no internet, or a network that blocks the request), the box
says so and links the releases page instead. On a network that inspects secure
connections with its own certificate, the check trusts the certificates your
operating system trusts, as your browser does.

Main Window Overview
~~~~~~~~~~~~~~~~~~~~

The Modan2 main window consists of several key components:

1. **Menu Bar**: File, Edit, View, Data, Help
2. **Toolbar**: Quick access to common operations
3. **Dataset Tree View** (Left): Hierarchical view of datasets
4. **Object Table** (Center): List of objects in the selected dataset, with
   **LM Count** and **Curve** columns
5. **Object Preview**: a floating preview of the selected object over the
   object table (bottom-right by default; drag it to another corner; toggle with
   ``Ctrl+P``)
6. **Status Bar** (Bottom): Information and progress indicators

Working with Datasets
---------------------

Creating a New Dataset
~~~~~~~~~~~~~~~~~~~~~~

1. Click **"New Dataset"** button or press ``Ctrl+N``
2. Enter dataset information:

   - **Parent**: optional - create hierarchical structure (pre-filled with the
     dataset selected in the tree)
   - **Dataset Name**: Descriptive name for your dataset
   - **Description**: Optional detailed description
   - **Dimension**: 2D or 3D

3. Click **Save** to create the dataset

.. note::
   Hierarchical datasets allow you to organize related studies. For example:

   - Study_2024 (parent)

     - Subspecies_A (child)
     - Subspecies_B (child)

The dataset dialog is organized into tabs — **General** (the basic information
above), **Landmarks**, **Curves** and **Variables**:

- **Landmarks** tab: **Wireframe** / **Baseline** / **Polygons** define how
  landmarks are connected for display, and the **Landmark Names** table gives
  each landmark index a name/abbreviation and a description (see
  :ref:`landmark-names`).
- **Curves** tab: the number of **Fixed Landmarks** and the dataset's
  semi-landmark curves — each with a name, a description and a point count ``N``
  (see :ref:`semi-landmark-curves`).

These schemes are shared by every object in the dataset, so a landmark name or a
curve you define once applies to all specimens.

Dataset Variables
~~~~~~~~~~~~~~~~~

Variables hold the per-specimen data you analyse by — the grouping used for CVA
and MANOVA, plus any measurements you want to keep alongside the shape.

A variable is just a **name** defined at the dataset level. Modan2 does not ask
you to declare a type or a list of allowed values; each object stores whatever
text you type, and you pick which variable to group by when you run an analysis.

**Adding Variables**:

1. Open the dataset dialog and go to the **Variables** tab
2. Click **"Add Variable"** and type the name (e.g. "Species", "Sex", "Age")
3. Double-click a name in the list to rename it, or select it and click
   **"Delete Variable"** to remove it

The main window also has an **"Add variable"** action, which prompts for a name
and appends it to the selected dataset.

**Setting Object Variables**:

Open the object (``Ctrl+Shift+O``, or double-click it). Each dataset variable
appears as its own labelled field in the object dialog — type the value there and
save. Values are free text, so a variable can hold a category ("male") or a
number ("2.5") equally well.

**Example Workflow**:

.. code-block:: text

   Dataset: Bird Wings
   Variables: Species, Sex, Age

   Objects:
     - wing_001.jpg → Species: sparrow, Sex: male, Age: 2.5
     - wing_002.jpg → Species: sparrow, Sex: female, Age: 1.8

   Analysis: group CVA by Species, MANOVA by Sex

Editing and Organising Datasets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rename a dataset** by opening its dataset dialog (double-click it in the
tree), changing the name, and clicking **Save**.

**Re-parent a dataset** by dragging it onto another dataset in the tree; it
becomes a child of the target.

**Copy objects to another dataset** by selecting them in the object table and
dragging them onto a dataset in the tree; hold **Shift** while dropping to move
them instead. Both datasets must have the same dimension.

.. warning::
   **Deleting a dataset deletes everything under it** — every object, every
   analysis, and the image and 3D-model files those objects owned, removed from
   disk. There is no undo.

Importing Data
--------------

Importing 2D Images
~~~~~~~~~~~~~~~~~~~

**Supported formats**: JPG, PNG, BMP, TIFF, GIF

**Method 1: Drag and Drop**

1. Select a dataset in the tree view
2. Drag image files from your file manager
3. Drop them onto the object table (not the tree)
4. Images are automatically imported with filenames as object names

**Method 2: Object Dialog**

1. Select the dataset → **Data → New Object** (``Ctrl+Shift+N``)
2. Click **"Load Image"** (or drop an image onto the viewer)
3. Click **Save**

.. tip::
   Use consistent naming: ``specimen_001.jpg``, ``specimen_002.jpg`` for easier sorting

Importing 3D Models
~~~~~~~~~~~~~~~~~~~~

**Supported formats**: OBJ, PLY, STL

**Method 1: Drag and Drop**

1. Select a 3D dataset
2. Drag 3D model files onto the object table
3. Models are imported with automatic scaling

**Method 2: Object Dialog**

1. Select the dataset → **Data → New Object** (``Ctrl+Shift+N``)
2. Click **"Load 3D Model"**
3. Click **Save**

**3D Model Requirements**:

- Mesh should be manifold (closed surface)
- Reasonable polygon count (<100k faces recommended)
- Centered at origin for best visualization

Importing Landmark Files
~~~~~~~~~~~~~~~~~~~~~~~~~

**Supported formats**: TPS, NTS, X1Y1, Morphologika, and JSON+ZIP dataset
packages.

Open **Data → Import** (``Ctrl+I``). Modan2 detects the format from the file
extension (``.tps``, ``.nts``, ``.x1y1``, ``.txt`` for Morphologika, ``.zip``
for a JSON+ZIP package), but you can also pick it explicitly with the
**File Type** radio buttons. The **Y coordinate: Inverted** checkbox flips the
Y axis for files that use a bottom-left origin. Importing always creates a new
dataset, named in the **Dataset Name** field.

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

1. **Data → Import** (``Ctrl+I``)
2. Click **Open File** and select the file (TPS, NTS, X1Y1, or Morphologika)
3. Check the **Dataset Name** for the new dataset
4. Click **"Execute Import"**. Modan2 will:

   - Create a new dataset with an object for each specimen
   - Link to image files (if an ``IMAGE=`` field exists)
   - Import landmark coordinates (and any curves, for TPS)

Importing a Dataset Package (JSON+ZIP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A **JSON+ZIP package** (``.zip``) is Modan2's own complete-backup format: it
bundles the dataset's metadata, landmark names, curve scheme, variables, and —
optionally — the image and 3D-model files. Importing one recreates the whole
dataset, including traced semi-landmark curves and missing landmarks.

1. **Data → Import** (``Ctrl+I``)
2. Click **Open File** and select the ``.zip`` package
3. Click **"Execute Import"**

Packages are imported inside a transaction and roll back on any error, and
extraction is hardened against path-traversal ("Zip Slip") archives. Older
packages (schema 1.1) still import; curves default to empty for those.

Working with Objects
--------------------

Viewing an Object
~~~~~~~~~~~~~~~~~

**Double-click** an object in the table to open the **Object Dialog**.

The Object Dialog shows:

- Object fields (Dataset Name, Object Name, Sequence, Description, and one
  field per dataset variable)
- Associated image or 3D model
- Landmark table
- 2D/3D viewer with landmarks visualized

The Object Dialog has mode buttons that decide what a click does:
**Landmark** (place/move landmarks, the default), **Wireframe** (drag from one
landmark to another to connect them; right-click an edge to delete it),
**Calibration** (set the image scale), and **Curve** (trace a semi-landmark
curve). Only one is active at a time. An image that has not been calibrated
yet opens in **Calibration** mode first.

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
   - **Middle mouse drag**: Pan
   - **Right mouse drag** / **Mouse wheel**: Zoom

3. Click on the surface to place a landmark
4. Landmarks appear as colored spheres
5. Right-click a landmark to delete it

**3D Viewer Controls**:

- **Left-drag**: rotate
- **Middle-drag**: pan
- **Right-drag** or **mouse wheel**: zoom
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

1. In the Object Dialog, click **"Landmark Names"** (or use the **Landmark
   Names** table on the dataset dialog's **Landmarks** tab)
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
   curve"** (10 for the first curve, then the previous curve's count). This
   count is dataset-wide, so it applies to that curve
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
(point count), **Traced** (✓), and **Closed**. Editing **N** re-resamples the
curve. Right-click a row → **"Delete Curve (all specimens)"** removes that curve
from the whole dataset.

**Closed curves (outlines)** — tick **Closed** for a curve that goes all the way
round, such as the outline of a shell or a leaf. Its end is joined back to its
start, its first point is drawn as a small square, and its semi-landmarks are
spread round the loop. Closed is dataset-wide, like **N**, and can also be set on
the **Curves** tab of the dataset dialog. A closed curve is what
:ref:`outline analysis <analysis-efa>` takes.

Curves are held in memory while you work and written to the database on **Save**.

Calibration (Setting the Scale)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Landmark coordinates are in image pixels. If you want size reported in real-world
units instead, calibrate the object against a known distance — a ruler in the
photograph, or an anatomical distance you have measured.

1. In the Object Dialog, click the **Calibration** mode button.
2. **Drag** across the known distance in the image: press at one end and release
   at the other. A line follows the cursor while you drag.
3. Enter the real length in the dialog that appears and pick the unit
   (**nm**, **um**, **mm**, **cm**, or **m**). The dialog shows how many pixels
   you spanned.
4. Click OK, then save the object.

Modan2 stores the result as pixels-per-mm **on that object**, so calibration is
per-specimen — photographs taken at different magnifications each get their own
scale. Once set, centroid size is reported in real units rather than pixels.

.. note::
   There is no batch calibration: each object is calibrated on its own. The unit
   you chose last is remembered as the default for the next one.

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
- **Polygon** (3D objects): fill defined polygons
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

All analyses run on superimposed shapes (Procrustes or Bookstein), computed as
the first step of the run.

Running an Analysis
~~~~~~~~~~~~~~~~~~~

A single analysis run performs the superimposition and then computes **PCA, CVA,
and MANOVA together** — you don't pick one type. The results are saved with the
dataset and can be re-opened later.

1. Select a dataset in the tree view
2. Click **Analyze** (``Ctrl+G``) or use the **Data** menu
3. In the analysis dialog, set:

   - **Analysis name** (a unique name is suggested)
   - **Superimposition method**: Procrustes, Bookstein, or — for a 2D dataset
     with a closed curve — **Elliptic Fourier (outline)**
     (see :ref:`analysis-efa`)
   - **CVA grouping variable**: the categorical variable that defines groups for CVA
   - **MANOVA grouping variable**: the categorical variable for MANOVA

4. Click **"OK"** to run. Progress is shown, and if CVA/MANOVA cannot be computed
   (e.g. too few groups) the failure is reported rather than silently skipped.
5. Select the new analysis in the tree: its results appear in **PCA**, **CVA**
   and **MANOVA** tabs. On the **PCA** tab, click **Data Exploration** for
   interactive plots, or **Analysis Details** for the result tables (both buttons
   are available on the PCA tab only).

The run is refused before it starts if the dataset has fewer than 5 objects with
landmarks, has objects with differing landmark counts, has a landmark that is
missing in every object, or has an object that records too few landmarks for its
missing ones to be estimated (fewer than 2 in 2D data, 3 in 3D). A dataset
without variables runs PCA only: both grouping variables then read *None (no
variables)*.

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

- *Procrustes* (Generalized Procrustes Analysis): the default; also imputes
  missing landmarks.
- *Bookstein* (baseline registration): re-expresses each shape as Bookstein shape
  coordinates by fixing the dataset's baseline landmarks to a standard position
  (2D: endpoints at (-0.5, 0) and (0.5, 0); 3D uses a 3-point baseline). It
  **requires a baseline** defined on the dataset; missing landmarks are imputed
  first (as in Procrustes).

Resistant Fit (RFTRA) was offered in earlier 0.2.0 pre-releases and has been
withdrawn; see the note under :doc:`advanced_features`.

**When the superimposition runs**:

- Automatically as the first step of every analysis run, using the method
  chosen in the analysis dialog
- The aligned shapes feed PCA, CVA, and MANOVA

.. _analysis-efa:

Outline Analysis (Elliptic Fourier)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Elliptic Fourier analysis (EFA) describes a closed outline as a sum of
*harmonics* — ellipses of increasing frequency, four coefficients each
(Kuhl & Giardina 1982). It suits forms whose shape lies in the whole outline
rather than in a few homologous points. Outline analysis is a **2D** feature.

**Tracing outlines for EFA**:

1. Define the outline as a curve and tick **Closed** (see
   :ref:`semi-landmark-curves`).
2. **Start every outline at the same landmark-like point** — an apex, a beak, the
   end of a hinge line: a point you could place as a landmark on every specimen.
   Modan2 keeps the first traced point as the outline's starting point and does
   *not* move it, so it must correspond across specimens. A start placed at an
   arbitrary point adds variation that is not shape.
3. Trace round the outline in either direction and finish near the start. Modan2
   always analyzes outlines **clockwise** (as seen on screen): a trace drawn
   anticlockwise is reversed about its first point before analysis, so the
   direction you traced in does not matter.

**Running it**: in the analysis dialog choose **Elliptic Fourier (outline)**,
pick the **Outline** (closed curve) and the number of **Harmonics**.

- **Harmonics — Auto (99% power)**, the default, uses the fewest harmonics that
  keep at least 99% of the harmonic power of *every* outline in the dataset. The
  count is limited by the most coarsely traced outline (half its point count)
  and by 50.
- Or set a fixed number of harmonics.

Every specimen must have the outline traced; the analysis names any that do not.
Fixed landmarks and other curves are not used by an outline analysis.

**Normalization** — what an outline analysis removes before comparing shapes:

- **Position**: the outline's centre is dropped.
- **Size**: each outline is divided by the semi-major axis of its first-harmonic
  ellipse. That axis length (calibrated if the specimen has a scale) is what the
  analysis reports as the specimen's size, in place of centroid size.
- **Rotation**: each outline is turned so its first-harmonic ellipse's major
  axis lies along x. Of the axis's two ends, the one nearer the starting point
  is used.
- **Starting point**: *not* normalized — it is your homologous start (step 2).

.. note::

   When the first-harmonic ellipse is nearly a circle, its major axis is poorly
   defined and the rotation can differ between similar specimens. The same is
   true when the starting point lies close to the ends of the ellipse's *minor*
   axis, where "the nearer end" can switch between the two. Starting outlines at
   a point near one end of the long axis of the form avoids both.

**Results**: PCA, CVA and MANOVA run on the normalized coefficients, and are
shown in the Data Exploration dialog like any other analysis; shapes there
(including the shape grid and reconstructions along a PC) are drawn as outlines.
The coefficients are stored with the analysis.

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
`Running an Analysis`_). Select the analysis, choose the **PCA** tab and click
**Data Exploration** to explore its principal components.

**Interpreting Results**:

The **Data Exploration Dialog** shows:

- **Score plot**: a scatter plot of specimens

  - Axis 1 / Axis 2 (and Axis 3 for a 3D chart): any of PC1–PC10, plus
    centroid size (CSize) on Axis 1
  - Points coloured by the **Grouping variable**
  - Tick **Var. explained** to add each axis's % variance to its label

- **Shape view**: the shape at a point of the plot — in *Exploration* mode,
  click the chart to see the shape at that position; *Regression*, *Average*,
  *Comparison* and *Comparison (overlap)* show other reconstructions

The eigenvalues (variance per PC) and the numeric scores are in the
**Analysis Details** window (**Eigenvalues** and **Result table** tabs).

**Exporting PCA Results**:

- **Analysis Details → Save Results**: an Excel (``.xlsx``) workbook with the
  scores and centroid size, the rotation matrix, and the eigenvalues
- **Export Chart** (Data Exploration): save the plot as PNG, JPG, PDF or SVG

.. note::
   **Analysis Details** recomputes the PCA from the dataset's current landmarks
   when it opens, with the analysis's superimposition method (Bookstein only if
   the dataset has a baseline).

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
defines your groups (e.g. "Species"), then select the analysis and open its
**CVA** tab.

**Interpreting Results**:

- **CV Score Plot** (the **CVA** tab): specimens plotted on CV axes

  - Ideally, groups form distinct clusters
  - Overlap indicates similarity

- **Classification accuracy** (the line under the plot): how often a specimen's
  group is predicted correctly.

  - The main figure is **cross-validated**: each specimen is classified by a
    model fitted without it (leave-one-out; stratified folds for very large
    data), so it estimates how well new specimens would be classified.
  - **Chance** is what always guessing the largest group would score — the
    figure to beat.
  - **Resubstitution** classifies the very specimens the model was fitted on. It
    is always optimistic, and is the figure Modan2 0.1.x reported.
  - When the data have more variables than the specimens can support, CVA runs
    on a reduced set, and the line says how many variables were used.
  - Analyses saved before the accuracy was stored show none; run them again.

Modan2 does not display a classification table or discriminant-function
statistics.

**Example**:

.. code-block:: text

   Dataset: Bird beaks, Variable: Species (A, B, C)

   CVA Results:
     CV1: 78% discrimination
     CV2: 15% discrimination
     Classification accuracy: 86.7% (leave-one-out cross-validation)
       · chance 33.3% · resubstitution 96.7%

.. _analysis-manova:

MANOVA
~~~~~~

**Purpose**: Test if groups differ significantly in shape

**Use when**:

- Formal hypothesis testing
- Comparing multiple groups simultaneously

**Running MANOVA**: MANOVA is computed as part of every analysis run. In the
analysis dialog, set the **MANOVA grouping variable** to the categorical variable
you want to test.

**Interpreting Results** (the **MANOVA** tab: one row each for Wilks' lambda,
Pillai's trace, Hotelling-Lawley trace and Roy's greatest root, with columns
Value, Num DF, Den DF, F Value and Pr>F):

- **Wilks' Lambda**: Test statistic (0-1)

  - Smaller = more group separation
  - 0 = perfect separation
  - 1 = no separation

- **F-statistic**: Ratio of between-group to within-group variation
- **P-value**: Probability that group differences are due to chance

  - P < 0.05: Significant difference (reject null hypothesis)
  - P ≥ 0.05: No significant difference


**Example**:

.. code-block:: text

   Hypothesis: Male and female skulls differ in shape

   MANOVA Results:
     Wilks' Lambda: 0.234
     F(40, 18) = 3.45
     P-value: 0.002

   Conclusion: Significant sex-related shape differences (P < 0.05)

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
- **Pan**: middle-drag
- **Zoom**: right-drag or mouse wheel

**Landmark Display**:

- Landmarks rendered as spheres
- Size adjustable in **Preferences**
- Index/name labels optional

Statistical Plots
~~~~~~~~~~~~~~~~~

**Available Plots**:

- **PC Score Plot** (PCA): Specimens on PC axes
- **CV Score Plot** (CVA): Specimens on CV axes
- **Shape view** (Data Exploration): the shape at a chosen point of the plot

**Customization**:

- **Group Colors**: Auto-assigned by variable
- **Point Size**: Adjustable
- **Axis Labels**: tick **Var. explained** to add the variance %
- **Legend**: Shows group names and colors

**Exporting Plots**:

1. In Data Exploration, click **"Export Chart"**
2. Formats: PNG, JPG, PDF, SVG

Data Export
-----------

Exporting Datasets
~~~~~~~~~~~~~~~~~~

Select a dataset and choose **Export** (``Ctrl+E``).

1. Choose the export **format**:

   - **TPS**: landmark coordinates in TPS format
   - **X1Y1**: a tab-separated table, one row per object
   - **Morphologika**: Morphologika format (with images and metadata)
   - **JSON+ZIP**: a complete dataset package (see below)

2. Choose the **superimposition** applied on export: **None** (raw coordinates) or
   **Procrustes** (aligned; the default). For a raw TPS export, traced semi-landmark curves are
   written under ``CURVES=`` / ``POINTS=`` blocks; a Procrustes export writes the
   merged aligned landmarks.
3. Only the objects in the **Export List** are written; move any you want to
   leave out to the **Object List** with ``<``. (A JSON+ZIP package always holds
   the whole dataset.)
4. Click **"Export"**.

A missing landmark is written as ``-999``, which Modan2's import offers to turn
back into a missing landmark.

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

- **Analysis Details → Save Results**: an Excel (``.xlsx``) workbook with the
  scores, the rotation matrix and the eigenvalues
- **Export Chart** (Data Exploration): the plot as PNG, JPG, PDF or SVG

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

- **Language**: English or Korean, applied immediately
- **Data folder**: where the whole library lives (**Browse...** / **Reset**); see
  :doc:`faq`
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
4. **Back up regularly**: use **Data → Back Up Library...**, or export datasets
   as JSON+ZIP packages

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

**Error**: ``… has too few objects with landmarks … At least 5 objects required``

**Solution**: Digitize at least 5 objects

**Error**: ``Object '…' has N landmarks but this dataset expects M``

**Solution**: Open the object and use **"Insert Missing"** at each position that
was not recorded

**Error**: ``Landmark N is missing in every object``

**Solution**: Record that landmark on at least one object, so there is something
to estimate it from

**Error**: ``Object '…' records N landmarks, so its missing landmarks cannot be estimated``

**Solution**: Record more landmarks on that object — at least 2 in 2D data, 3 in
3D — or remove it from the dataset

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

File Format Reference
---------------------

What Modan2's readers actually expect. Blank lines are ignored throughout.

TPS
~~~

An object is an ``LM=<n>`` header, ``n`` coordinate lines, and optional
``KEY=VALUE`` lines. Recognised keys are ``ID``, ``IMAGE`` and ``COMMENT``
(others, such as ``SCALE``, are ignored). Lines beginning with ``#``, ``"`` or ``'`` are comments.

.. code-block:: text

   LM=4
   1.5 2.3
   2.1 3.4
   3.2 4.1
   4.0 2.8
   ID=specimen_001
   IMAGE=specimen_001.jpg

   LM=4
   ...

Semi-landmark curves follow the landmarks as a ``CURVES=<k>`` header and then
``k`` blocks, each a ``POINTS=<m>`` header with ``m`` coordinate lines:

.. code-block:: text

   LM=4
   1.5 2.3
   ...
   CURVES=1
   POINTS=3
   5.0 6.0
   5.4 6.6
   5.9 7.1
   ID=specimen_001

Modan2 both reads and writes these blocks (see :ref:`semi-landmark-curves`).

NTS
~~~

An NTSYS-style matrix file: optional comment lines in quotes, then a header line,
then the data.

.. code-block:: text

   "Bird wing landmarks
   1 24L 20 0 DIM=2
   specimen_001
   1.5 2.3 2.1 3.4 ...
   specimen_002
   ...

The header fields are, in order: the matrix type, the number of objects with a
row-name flag, the number of variables with a column-name flag, a missing-value
indicator, and ``DIM=<d>`` giving the dimensionality.

The row-name flag says where object names live — ``L`` on their own line, ``B``
at the beginning of each data row, ``E`` at the end. The number of landmarks is
the variable count divided by ``DIM``.

Morphologika
~~~~~~~~~~~~

A sectioned text file. ``[names]`` and ``[rawpoints]`` are required; the rest are
optional.

.. code-block:: text

   [individuals]
   2
   [landmarks]
   4
   [dimensions]
   2
   [names]
   specimen_001
   specimen_002
   [rawpoints]
   1.5 2.3
   2.1 3.4
   ...

Optional sections Modan2 reads: ``[labels]`` and ``[labelvalues]`` (variables),
``[wireframe]``, ``[polygons]``, ``[images]``, and ``[pixelspermm]``.

X1Y1
~~~~

A tab-separated table: a header row (name, X1, Y1, X2, Y2, …) and then one
row per object.

Glossary
--------

**Landmark**
   A point location on a specimen, used for shape analysis. In Modan2 a landmark
   has an index, optionally a name, and coordinates in image (2D) or model (3D)
   space.

**Semi-landmark**
   A point placed along a *curve* rather than at a discrete feature. You trace the
   curve and Modan2 resamples it into evenly-spaced points
   (see :ref:`semi-landmark-curves`).

**Type I / II / III landmark**
   The conventional classification: **Type I** is a true homologous point (e.g. a
   suture intersection), **Type II** is geometrically defined (e.g. a point of
   maximum curvature), and **Type III** is an arbitrary point along a curve or
   outline — what semi-landmarks capture.

**Superimposition**
   Aligning specimens so that only shape differences remain. Modan2 offers
   Procrustes and Bookstein (see `Procrustes Superimposition`_).

**Procrustes superimposition**
   Superimposition that removes position, orientation, and size by translating,
   rotating, and scaling each configuration to best fit the others.

**Centroid size**
   A measure of size: the square root of the summed squared distances from every
   landmark to the configuration's centroid. Reported in real units when the
   object has been calibrated, in pixels otherwise.

**Procrustes distance**
   A measure of how different two shapes are, after superimposition.

**Shape space**
   The mathematical space in which each point is one shape; PCA and CVA are
   explored as projections of it.

**PCA (Principal Component Analysis)**
   Finds the axes along which the dataset varies most, so a few components
   summarise the main patterns of shape variation.

**CVA (Canonical Variate Analysis)**
   Finds the axes that best separate groups you have defined with a variable.

**MANOVA (Multivariate Analysis of Variance)**
   Tests whether the group differences are statistically significant.

**Missing landmark**
   A landmark that could not be recorded. Marked explicitly so the landmark count
   stays consistent, and filled in during analysis by shape-fitting
   (see :ref:`analysis-missing-landmarks`).

Next Steps
----------

- Explore the :doc:`developer_guide` to contribute or extend Modan2
- Check the :doc:`changelog` for latest features and bug fixes
- Visit the `GitHub repository <https://github.com/jikhanjung/Modan2>`_ for example datasets
