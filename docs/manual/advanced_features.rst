Advanced Features Guide
=======================

This guide covers advanced features and techniques for power users of Modan2.

.. contents:: Table of Contents
   :local:
   :depth: 2

Performance Optimization
------------------------

Database Optimization
~~~~~~~~~~~~~~~~~~~~~

Modan2 uses SQLite for data storage. Regular maintenance improves performance.

**Optimize database:**

.. code-block:: bash

   # Using SQLite command line
   sqlite3 ~/PaleoBytes/Modan2/Modan2.db "VACUUM;"

   # Or using Python
   import sqlite3
   conn = sqlite3.connect('Modan2.db')
   conn.execute('VACUUM')
   conn.close()

**Benefits:**

* Reduces database file size
* Improves query performance
* Reclaims unused space

**When to optimize:**

* After deleting many datasets
* Database file larger than expected
* Performance noticeably slower

Large Dataset Strategies
~~~~~~~~~~~~~~~~~~~~~~~~~

For datasets with 1000+ objects:

**1. Hierarchical Organization:**

.. code-block:: text

   Master Dataset (all objects)
   ├── Subset 1 (species A)
   ├── Subset 2 (species B)
   └── Subset 3 (time period 1)

**Benefits:**

* Analyze subsets independently
* Faster individual analyses
* Organized workflow

**2. Batch Processing:**

.. code-block:: python

   # Process multiple datasets programmatically
   from MdModel import MdDataset, MdDatasetOps
   from MdStatistics import PerformPCA

   datasets = MdDataset.select()
   for dataset in datasets:
       obj_count = len(dataset.get_object_list())
       if obj_count > 50:
           dataset_ops = MdDatasetOps()
           dataset_ops.read_from_dataset(dataset)
           pca = PerformPCA(dataset_ops)
           # Use pca results (pca.rotated_matrix, pca.eigen_value_percentages, etc.)

**3. Memory Management:**

* Close unused object viewers
* Don't keep all analyses open
* Export results and close tabs

Performance Benchmarks
~~~~~~~~~~~~~~~~~~~~~~

**Expected performance (Phase 7 validation):**

+----------------------+------------------+--------------------+
| Operation            | 100 objects      | 1000 objects       |
+======================+==================+====================+
| Dataset load         | < 50ms           | 277ms              |
+----------------------+------------------+--------------------+
| PCA                  | < 10ms           | 60ms               |
+----------------------+------------------+--------------------+
| CVA                  | < 5ms            | 2.5ms              |
+----------------------+------------------+--------------------+
| MANOVA               | < 10ms           | 28ms               |
+----------------------+------------------+--------------------+
| Object table         | 5ms              | 12.63ms            |
+----------------------+------------------+--------------------+

**Memory usage:**

* ~4KB per object (linear scaling)
* 1000 objects: ~4MB
* 10000 objects: ~40MB

**Scalability:**

* Tested up to 2000 objects
* Linear O(n) performance
* Production-ready for 100,000+ objects

Advanced Data Management
-------------------------

Hierarchical Datasets
~~~~~~~~~~~~~~~~~~~~~

**Parent-child relationships** allow flexible data organization:

**Creating child datasets:**

1. Right-click the parent dataset in the tree
2. Select **"Add child dataset"**
3. Fill in the new dataset's dialog as usual — the parent is preset for you

A child dataset is a new, empty dataset nested under the parent; objects are not
copied into it. Use it to organise a study into subsets you populate yourself.

**Use cases:**

**Example 1: Taxonomic subsets**

.. code-block:: text

   All Specimens (parent)
   ├── Species A (child)
   ├── Species B (child)
   └── Species C (child)

**Example 2: Time periods**

.. code-block:: text

   Complete Dataset (parent)
   ├── Pleistocene (child)
   ├── Holocene (child)
   └── Modern (child)

Batch Operations
~~~~~~~~~~~~~~~~

**Batch landmark editing:**

.. code-block:: python

   # Example: Apply transformation to all objects
   from MdModel import MdDataset, MdObject
   import numpy as np

   dataset = MdDataset.get_by_id(dataset_id)
   for obj in dataset.get_object_list():
       coords = obj.get_landmark_list()
       # Apply transformation
       coords = coords * 2.0  # Scale example
       obj.save_landmark_list(coords)

**Batch variable editing:**

1. Select the dataset
2. Edit cells directly in the object table
3. Copy/paste to and from a spreadsheet with ``Ctrl+C`` / ``Ctrl+V``

**Batch import:**

Drag several landmark files onto the window at once, or select them together in
**File → Import** — each becomes an object in the dataset.

Semi-landmark Curves at Scale
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Curves are defined once for the dataset (a name and a point count ``N``) and then
traced per specimen, so the semi-landmark count stays consistent across the whole
dataset by construction.

* **Change ``N`` after tracing.** Editing ``N`` in the curve table re-resamples
  the stored trace — you do not have to re-trace anything.
* **Trace fewer clicks.** With **"Snap to curve"** on (the default in Curve
  mode), the trace follows the strongest image edge between clicks, so a clean
  outline usually needs only a handful of points.
* **Remove a curve everywhere.** Right-click a row in the curve table →
  **"Delete Curve (all specimens)"**.
* **Round-trip.** ``CURVES=`` / ``POINTS=`` blocks are read from and written to
  TPS, and the JSON+ZIP package carries the curve scheme and every traced curve.

Semi-landmark curves are a 2D feature. In analysis the derived points are treated
as ordinary landmarks, appended after the fixed (anatomical) ones.

Database Direct Access
~~~~~~~~~~~~~~~~~~~~~~

Access database directly for advanced operations:

.. code-block:: python

   from MdModel import MdDataset, MdObject, database

   # Query datasets
   datasets = MdDataset.select().where(
       MdDataset.dimension == 2
   )

   # Complex queries
   from peewee import fn
   large_datasets = MdDataset.select().where(
       fn.COUNT(MdObject.id) > 100
   ).join(MdObject)

   # Bulk operations
   with database.atomic():
       for obj in objects:
           obj.save()

Advanced Statistical Analysis
------------------------------

Custom Analysis Workflows
~~~~~~~~~~~~~~~~~~~~~~~~~~

A single analysis run always computes PCA, CVA, and MANOVA together; the
exploration below happens afterwards, in the **Data Exploration** dialog.

**Regression overlay:**

1. Open a completed analysis in **Data Exploration**
2. Tick **"Show regression"**
3. Choose the grouping with **Group by**, and whether the line is fitted to
   **All** points, **By group**, or a **Select group**

**Shape grid:**

Tick **"Shape grid"** in Data Exploration to draw the shape reconstructed at
positions across the plot, so you can see how shape changes along each axis.

Superimposition Methods
~~~~~~~~~~~~~~~~~~~~~~~

Modan2 offers three superimposition methods, chosen in the analysis dialog. All
three impute missing landmarks first (see `Missing Landmark Handling`_).

**Procrustes** (Generalized Procrustes Analysis):

* Translation + rotation + scaling
* Standardises centroid size, leaving pure shape
* The default, and the right choice unless you have a specific reason otherwise

**Bookstein** (baseline registration):

* Re-expresses each shape as Bookstein shape coordinates by fixing the dataset's
  **baseline** landmarks to a standard position
* 2D: the baseline endpoints go to (-0.5, 0) and (0.5, 0); 3D uses a 3-point baseline
* **Requires a baseline defined on the dataset**
* Useful when a well-defined anatomical axis should anchor the comparison

**Resistant Fit** (RFTRA):

* Robust alignment built on repeated medians of pairwise landmark relationships
* A few displaced (outlier) landmarks do not drag the whole fit the way they can
  under Procrustes
* Works for both 2D and 3D

**Choosing a method:**

+------------------+-------------------+---------------------------+
| Research Goal    | Recommended       | Notes                     |
+==================+===================+===========================+
| Pure shape       | Procrustes        | The default               |
+------------------+-------------------+---------------------------+
| Anchored on an   | Bookstein         | Needs a dataset baseline  |
| anatomical axis  |                   |                           |
+------------------+-------------------+---------------------------+
| A few unreliable | Resistant Fit     | Resists outlier landmarks |
| landmarks        |                   |                           |
+------------------+-------------------+---------------------------+

Missing Landmark Handling
~~~~~~~~~~~~~~~~~~~~~~~~~

Modan2 fills missing landmarks automatically during analysis with an EM-style
loop that interleaves alignment and imputation:

1. Align every specimen with the gaps left open — the mean shape ignores them,
   and each specimen is aligned on the landmarks it actually has.
2. For each specimen with missing data, fit the current mean shape onto its
   observed landmarks by a similarity transform (rotation, scale, translation)
   and read the missing positions off the fitted mean.
3. Re-align with the filled-in values, then **re-open the original gaps** and
   re-estimate them from the improved mean.
4. Repeat step 3 a few times, so estimates improve as the alignment settles and
   are never fitted on previous estimates.

Imputed values exist only in the analysis working copy — they are never written
back to the database. The same shape-fitting drives the "Show Estimated" and
"Show Expected" previews in the Object Dialog.

**Best practices:**

* Limit missing data to < 10% of landmarks
* Keep a good number of complete (or near-complete) specimens
* Document which landmarks were missing
* Sensitivity analysis (compare with/without the affected specimens)

3D Visualization Techniques
----------------------------

Advanced 3D Controls
~~~~~~~~~~~~~~~~~~~~

**Navigation:**

* **Left-drag:** Rotate around centre
* **Middle-drag:** Pan (translate)
* **Right-drag** or **scroll wheel:** Zoom in/out

**Display toggles** (checkboxes beside the viewer):

* **3D Model:** show the mesh
* **Rotate:** spin the model continuously
* **Wireframe** / **Polygon** / **Baseline:** draw the dataset's landmark
  connections, filled polygons, and baseline

Landmark Visualization
~~~~~~~~~~~~~~~~~~~~~~

**Customization** — set in **Edit → Preferences**, separately for 2D and 3D:

* **Landmark** size: Small / Medium / Large
* **Wireframe** thickness: Thin / Medium / Thick
* **Index** (label) size: Small / Medium / Large
* **Background Color** for the viewer

**Landmark labels:**

* The **Show** checkbox toggles labels
* The **Index** / **Name** radio buttons choose whether the label is the
  landmark's number or its dataset-wide name

**Wireframe display:**

* Define the connections in the dataset dialog's wireframe tab

Model Import and Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Supported 3D formats:**

* **OBJ:** Wavefront format (most common)
* **PLY:** Polygon File Format
* **STL:** Stereolithography

**Pre-processing models:**

For best performance, prepare models:

1. **Reduce polygon count** (MeshLab/Blender):

   .. code-block:: text

      Original: 1,000,000 polygons
      Decimated: 100,000 polygons
      Quality: Still excellent
      Performance: 10x faster

2. **Center model:**

   * Model centered at origin
   * Easier landmark placement

3. **Scale appropriately:**

   * Reasonable coordinate range
   * Not too large/small

**Batch model processing:**

.. code-block:: python

   # Example: Decimate models with Trimesh
   import trimesh

   mesh = trimesh.load('model.obj')
   # Reduce to 10% of original faces
   simplified = mesh.simplify_quadratic_decimation(
       len(mesh.faces) // 10
   )
   simplified.export('model_simplified.obj')

Integration with External Tools
--------------------------------

R Integration
~~~~~~~~~~~~~

Export data for analysis in R:

**Export landmarks:**

.. code-block:: r

   # Modan2: Export as Morphologika or TPS

   # R: Import with geomorph
   library(geomorph)
   data <- readland.tps("export.tps", specID = "ID")

   # Or Morphologika
   data <- read.morphologika("export.txt")

   # Perform analysis in geomorph
   gpa <- gpagen(data)
   pca <- gm.prcomp(gpa$coords)

**Import R results:**

1. Save R results as CSV
2. Import as variables in Modan2
3. Visualize in Data Exploration

Python/NumPy Integration
~~~~~~~~~~~~~~~~~~~~~~~~~

Access data programmatically:

.. code-block:: python

   from MdModel import MdDataset, MdObject
   import numpy as np

   # Load dataset
   dataset = MdDataset.get_by_id(1)
   objects = dataset.get_object_list()

   # Extract landmark coordinates
   coords = []
   for obj in objects:
       landmarks = obj.get_landmark_list()
       coords.append(landmarks)

   # Convert to NumPy array
   data = np.array(coords)  # Shape: (n_objects, n_landmarks, n_dims)

   # Perform custom analysis
   from scipy.spatial.distance import pdist, squareform
   from sklearn.decomposition import PCA

   # Flatten for PCA
   flat_data = data.reshape(len(objects), -1)

   # Custom PCA
   pca = PCA(n_components=10)
   scores = pca.fit_transform(flat_data)

   # Save results back to Modan2
   # (Add as variables to objects)

MorphoJ Compatibility
~~~~~~~~~~~~~~~~~~~~~

**Export for MorphoJ:**

1. Export as Morphologika format
2. Open in MorphoJ
3. Perform additional analyses
4. Compare results

**Import from MorphoJ:**

1. Export from MorphoJ as Morphologika
2. Import into Modan2
3. Continue workflow

Scripting and Automation
-------------------------

Python API
~~~~~~~~~~

Use Modan2 modules in scripts:

.. code-block:: python

   #!/usr/bin/env python
   """
   Example: Batch PCA analysis
   """
   from MdModel import MdDataset, MdDatasetOps
   from MdStatistics import PerformPCA
   import json

   # Get all 2D datasets with sufficient objects
   datasets = MdDataset.select().where(MdDataset.dimension == 2)

   results = []
   for dataset in datasets:
       # Check object count
       obj_count = len(dataset.get_object_list())
       if obj_count < 50:
           continue

       print(f"Processing {dataset.dataset_name}...")

       # Create dataset ops and perform PCA
       dataset_ops = MdDatasetOps()
       dataset_ops.read_from_dataset(dataset)

       pca = PerformPCA(dataset_ops)
       if pca is None:
           continue

       # Save results
       results.append({
           'dataset': dataset.dataset_name,
           'n_components': len(pca.eigen_value_percentages),
           'variance_ratios': pca.eigen_value_percentages[:5]  # First 5 PCs
       })

   # Export summary
   with open('pca_summary.json', 'w') as f:
       json.dump(results, f, indent=2)

   print(f"Processed {len(results)} datasets")

Database Queries
~~~~~~~~~~~~~~~~

Advanced database operations:

.. code-block:: python

   from MdModel import MdDataset, MdObject, MdAnalysis
   from peewee import fn

   # Find datasets with most objects
   top_datasets = (MdDataset
       .select(MdDataset, fn.COUNT(MdObject.id).alias('count'))
       .join(MdObject)
       .group_by(MdDataset)
       .order_by(fn.COUNT(MdObject.id).desc())
       .limit(10))

   # Find objects with missing landmarks
   incomplete_objects = (MdObject
       .select()
       .where(MdObject.missing_landmarks.is_null(False)))

   # Get all PCA analyses
   pca_analyses = (MdAnalysis
       .select()
       .where(MdAnalysis.analysis_type == 'PCA'))

   # Complex join query
   results = (MdDataset
       .select(MdDataset.name, fn.AVG(MdObject.size).alias('mean_size'))
       .join(MdObject)
       .group_by(MdDataset)
       .having(fn.COUNT(MdObject.id) > 30))

Batch Export
~~~~~~~~~~~~

Export multiple datasets:

.. code-block:: python

   #!/usr/bin/env python
   """
   Export all datasets as JSON+ZIP
   """
   from MdModel import MdDataset
   from MdUtils import create_zip_package
   import os

   output_dir = "exports"
   os.makedirs(output_dir, exist_ok=True)

   datasets = MdDataset.select()
   for dataset in datasets:
       filename = f"{dataset.dataset_name.replace(' ', '_')}.zip"
       filepath = os.path.join(output_dir, filename)

       print(f"Exporting {dataset.dataset_name}...")
       create_zip_package(
           dataset.id,
           filepath,
           include_files=True
       )

   print(f"Exported {len(datasets)} datasets to {output_dir}")

Custom Visualizations
---------------------

Matplotlib Integration
~~~~~~~~~~~~~~~~~~~~~~

Create custom plots from Modan2 data:

.. code-block:: python

   import matplotlib.pyplot as plt
   from MdModel import MdDataset, MdDatasetOps
   from MdStatistics import PerformPCA
   import numpy as np

   # Load dataset and run PCA
   dataset = MdDataset.get_by_id(1)
   dataset_ops = MdDatasetOps()
   dataset_ops.read_from_dataset(dataset)

   pca = PerformPCA(dataset_ops)
   if pca is None:
       print("PCA failed")
       exit(1)

   # Extract PC scores and variance
   scores = np.array(pca.rotated_matrix)
   variance = [v * 100 for v in pca.eigen_value_percentages]  # Convert to percentages

   # Create custom scatter plot
   fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

   # PC1 vs PC2
   ax1.scatter(scores[:, 0], scores[:, 1], alpha=0.6)
   ax1.set_xlabel(f'PC1 ({variance[0]:.1f}%)')
   ax1.set_ylabel(f'PC2 ({variance[1]:.1f}%)')
   ax1.set_title('PCA Scores')
   ax1.grid(True, alpha=0.3)

   # Scree plot
   n_components = min(10, len(variance))  # Show first 10 components
   ax2.bar(range(1, n_components+1), variance[:n_components])
   ax2.set_xlabel('Component')
   ax2.set_ylabel('Variance Explained (%)')
   ax2.set_title('Scree Plot')

   plt.tight_layout()
   plt.savefig('pca_custom.png', dpi=300)
   plt.show()

Shape Deformation Grids
~~~~~~~~~~~~~~~~~~~~~~~~

Visualize shape changes along PC axes:

.. code-block:: python

   import matplotlib.pyplot as plt
   import numpy as np
   from MdModel import MdDataset, MdDatasetOps
   from MdStatistics import PerformPCA

   # Load dataset and run PCA
   dataset = MdDataset.get_by_id(1)
   dataset_ops = MdDatasetOps()
   dataset_ops.read_from_dataset(dataset)

   pca = PerformPCA(dataset_ops)
   if pca is None:
       print("PCA failed")
       exit(1)

   # Calculate mean shape (already centered in PCA)
   n_landmarks = len(dataset_ops.object_list[0].landmark_list)
   dimension = dataset.dimension

   # Get PC1 loadings (rotation matrix column 0)
   pc1_loadings = pca.rotation_matrix[:, 0]

   # Reconstruct shapes at -2SD, mean (0), +2SD along PC1
   sd = np.sqrt(pca.raw_eigen_values[0])
   shapes = []
   for multiplier in [-2, 0, 2]:
       # Apply PC1 loadings scaled by SD
       shape_vector = pc1_loadings * multiplier * sd
       # Reshape to landmarks
       shape = shape_vector.reshape(n_landmarks, dimension)
       shapes.append(shape)

   # Plot deformation
   fig, axes = plt.subplots(1, 3, figsize=(15, 5))
   wireframe = dataset.unpack_wireframe()

   for ax, shape, title in zip(
       axes,
       shapes,
       ['PC1 -2SD', 'Mean', 'PC1 +2SD']
   ):
       ax.scatter(shape[:, 0], shape[:, 1], c='red', s=50, zorder=2)
       # Add wireframe if defined
       if wireframe:
           for connection in wireframe:
               idx1, idx2 = connection
               ax.plot([shape[idx1, 0], shape[idx2, 0]],
                      [shape[idx1, 1], shape[idx2, 1]], 'b-', alpha=0.6)
       ax.set_title(title)
       ax.set_aspect('equal')
       ax.grid(True, alpha=0.3)

   plt.tight_layout()
   plt.savefig('shape_deformation.png', dpi=300)

Settings and Configuration
---------------------------

Preferences File Format
~~~~~~~~~~~~~~~~~~~~~~~

Modan2 keeps its preferences in a JSON file written when the application exits.

**Location** — the standard settings folder for your operating system:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Platform
     - Location
   * - Windows
     - ``%LOCALAPPDATA%\PaleoBytes\Modan2\preferences.json``
   * - macOS
     - ``~/Library/Application Support/PaleoBytes/Modan2/preferences.json``
   * - Linux
     - ``~/.config/PaleoBytes/Modan2/preferences.json``

This is separate from your data (``~/PaleoBytes/Modan2/``, which holds the
database, images, 3D models, logs and backups). Preferences are settings the
application can recreate; your data cannot be recreated, so the two are kept
apart.

Preferences are copied forward automatically when the location changes, so
upgrading never loses them. Earlier versions kept them in
``~/PaleoBytes/Modan2/preferences.json`` and, before that,
``~/.modan2/config.json``; those files are left in place and can be deleted once
you have upgraded.

Everything in the file is written by the **Preferences** dialog and by the
window geometry that is remembered between sessions, so the normal way to change
a setting is through the UI. To reset Modan2 to defaults, quit it and delete the
file — it is recreated on the next launch.

.. code-block:: bash

   # Backup (Linux; adjust the path for your platform, see the table above)
   cp ~/.config/PaleoBytes/Modan2/preferences.json{,.backup}

   # Restore
   cp ~/.config/PaleoBytes/Modan2/preferences.json{.backup,}

Command-Line Options
~~~~~~~~~~~~~~~~~~~~

The application accepts a few options at startup:

* ``--db <path>`` — open a specific database instead of the default
* ``--config <path>`` — use a different configuration file
* ``--lang <en|ko>`` — start in the given language
* ``--debug`` — verbose logging
* ``--no-splash`` — skip the splash screen
* ``--version`` — print the version and exit

.. note::
   Modan2 is not configured through environment variables; use these options (or
   the Preferences dialog) instead.

Tips and Tricks
---------------

Keyboard Shortcuts
~~~~~~~~~~~~~~~~~~

**Main window:**

* ``Ctrl+N``: New dataset
* ``Ctrl+Shift+N``: New object
* ``Ctrl+Shift+O``: Edit object
* ``Ctrl+S``: Save changes
* ``Ctrl+I``: Import
* ``Ctrl+E``: Export
* ``Ctrl+G``: Analyze
* ``Ctrl+P``: Toggle the object preview
* ``Ctrl+W``: Exit
* ``F1``: About

**Object Dialog (Curve mode):**

* ``Enter`` / double-click: accept the current trace
* ``Esc`` / right-click: cancel the current trace

**Tables:**

* ``Ctrl+C`` / ``Ctrl+V``: copy and paste cells (e.g. to and from a spreadsheet)

Workflow Optimization
~~~~~~~~~~~~~~~~~~~~~

**Efficient data entry:**

1. **Template datasets:**

   * Create dataset with complete structure
   * Duplicate for new studies
   * Pre-defined variables and wireframes

2. **Keyboard navigation:**

   * Tab between fields
   * Enter to confirm
   * Escape to cancel

3. **Batch operations:**

   * Select multiple objects
   * Edit variables in table
   * Copy/paste from spreadsheet

**Analysis workflows:**

.. code-block:: text

   Quick exploration:
   1. Import data
   2. Quick PCA (no grouping)
   3. Identify outliers
   4. Refine dataset

   Publication workflow:
   1. Clean data
   2. Document variables
   3. Multiple analyses
   4. Export high-quality figures
   5. Export data for R/Python

Hidden Features
~~~~~~~~~~~~~~~

**Double-click behaviors:**

* Double-click dataset: Expand/collapse
* Double-click object: Open object dialog
* Double-click analysis: Open results

**Right-click context menus:**

* Right-click dataset in the tree: add a child dataset, object, or analysis;
  explore data; reload
* Right-click a landmark in the 2D viewer: delete it
* Right-click a curve point (Curve mode): **Delete Point** / **Delete Curve**
* Right-click a row in the curve table: **Delete Curve (all specimens)**

**Drag-and-drop:**

* Drag TPS file to window: Import
* Drag image to object: Attach
* Drag 3D model to object: Attach

Further Resources
-----------------

**Documentation:**

* Installation Guide: Detailed setup
* User Guide: Basic usage
* Troubleshooting Guide: Problem-solving
* FAQ: Common questions

**Community:**

* GitHub Discussions: Ask questions
* GitHub Issues: Report bugs

**Development:**

* Developer Guide: Architecture
* CONTRIBUTING.md: Contribution guide
* GitHub Repository: Source code

**Contact:**

* Email: jikhanjung@gmail.com
* GitHub: @jikhanjung
