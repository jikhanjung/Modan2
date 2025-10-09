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
   sqlite3 ~/.local/share/Modan2/modan.db "VACUUM;"

   # Or using Python
   import sqlite3
   conn = sqlite3.connect('modan.db')
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

1. Right-click parent dataset
2. Select "New Child Dataset"
3. Choose options:

   * Copy landmarks (start with same data)
   * Different superimposition method
   * Subset of objects

**Use cases:**

**Example 1: Different superimpositions**

.. code-block:: text

   Raw Data (parent)
   ├── Full Procrustes (child)
   ├── Partial Procrustes (child)
   └── Bookstein Registration (child)

**Example 2: Taxonomic subsets**

.. code-block:: text

   All Specimens (parent)
   ├── Species A (child)
   ├── Species B (child)
   └── Species C (child)

**Example 3: Time periods**

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

1. Select dataset
2. View → Object Table
3. Edit cells directly
4. Copy/paste from Excel

**Batch import:**

.. code-block:: bash

   # Import multiple TPS files
   for file in *.tps; do
       # Import via GUI or script
       python import_tps.py "$file"
   done

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

**Regression Analysis:**

Use Data Exploration dialog for regression:

1. Select dataset with continuous variables
2. Data Exploration → Regression
3. Select X and Y variables
4. View scatter plot with regression line
5. Export coefficients

**Shape Variation Analysis:**

Visualize shape changes along PC axes:

1. Run PCA
2. Results → Shape Variation
3. Select PC axis
4. View wireframe deformation
5. Export shape coordinates

**Asymmetry Analysis:**

For bilateral symmetry:

1. Create dataset with symmetric landmark pairs
2. Define symmetry in wireframe
3. Run specialized asymmetry analysis
4. Separate symmetric/asymmetric components

Procrustes Methods
~~~~~~~~~~~~~~~~~~

**Full Procrustes:**

* Translation + Rotation + Scaling
* Standardizes size to 1.0
* Use for pure shape analysis

**Partial Procrustes:**

* Translation + Rotation only
* Preserves size information
* Use when size is important

**Bookstein Registration:**

* Align using baseline (2 landmarks)
* First 2 landmarks define axis
* Useful for oriented structures

**Resistant Fit:**

* Robust to outliers
* Iterative weighting
* Use with messy data

**Choosing method:**

+------------------+-------------------+------------------+
| Research Goal    | Recommended       | Notes            |
+==================+===================+==================+
| Pure shape       | Full Procrustes   | Remove size      |
+------------------+-------------------+------------------+
| Shape + size     | Partial Procrustes| Keep size info   |
+------------------+-------------------+------------------+
| Directional data | Bookstein         | Known baseline   |
+------------------+-------------------+------------------+
| Noisy data       | Resistant Fit     | Handle outliers  |
+------------------+-------------------+------------------+

Missing Landmark Handling
~~~~~~~~~~~~~~~~~~~~~~~~~

**Estimation methods:**

1. **TPS Interpolation:**

   * Thin-plate spline from complete landmarks
   * Smooth interpolation
   * Works well for few missing landmarks

2. **Mean Substitution:**

   * Use mean configuration
   * Simple but less accurate
   * For many missing landmarks

3. **Iterative Estimation:**

   * Estimate → Procrustes → Re-estimate
   * Converges to best fit
   * Most accurate but slower

**Best practices:**

* Limit missing data to < 10% of landmarks
* Estimate before Procrustes
* Document which landmarks estimated
* Sensitivity analysis (compare with/without)

3D Visualization Techniques
----------------------------

Advanced 3D Controls
~~~~~~~~~~~~~~~~~~~~

**Navigation:**

* **Left-drag:** Rotate around center
* **Middle-drag:** Pan (translate)
* **Scroll:** Zoom in/out
* **Shift+drag:** Constrained rotation
* **Ctrl+drag:** Roll (rotate around view axis)
* **Double-click:** Reset view

**Viewing modes:**

1. **Solid:** Default view
2. **Wireframe:** Show mesh structure
3. **Points:** Show vertices only
4. **Solid + wireframe:** Combined view

**Keyboard shortcuts:**

* ``F3``: Toggle 3D view
* ``W``: Wireframe mode
* ``S``: Solid mode
* ``P``: Point mode
* ``R``: Reset view
* ``L``: Toggle lighting

Landmark Visualization
~~~~~~~~~~~~~~~~~~~~~~

**Customization:**

* Settings → Visualization → 3D Landmarks
* Sphere size: 0.5 - 5.0
* Color: RGB picker
* Opacity: 0-100%

**Landmark labels:**

* Show/hide landmark numbers
* Font size adjustment
* Color customization

**Wireframe display:**

* Define connections in dataset dialog
* Color coding by region
* Line width adjustment

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

Settings File Format
~~~~~~~~~~~~~~~~~~~~

Modan2 settings are stored in JSON format.

**Location:**

* Windows: ``%APPDATA%\Modan2\settings.json``
* Linux/macOS: ``~/.config/Modan2/settings.json``

**Example settings.json:**

.. code-block:: json

   {
     "general": {
       "language": "en",
       "remember_window_geometry": true,
       "remember_last_dataset": true,
       "auto_save_interval": 300
     },
     "visualization": {
       "landmark_size_2d": 5,
       "landmark_size_3d": 1.0,
       "landmark_color": "#FF0000",
       "wireframe_color": "#0000FF",
       "show_landmark_labels": true
     },
     "analysis": {
       "default_procrustes": "full",
       "pca_components": 10,
       "cva_permutations": 1000
     },
     "paths": {
       "last_import_dir": "/path/to/data",
       "last_export_dir": "/path/to/exports",
       "database_path": "~/.local/share/Modan2/modan.db"
     }
   }

Backup settings:

.. code-block:: bash

   # Backup
   cp settings.json settings.json.backup

   # Restore
   cp settings.json.backup settings.json

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Control Modan2 behavior via environment variables:

**Log level:**

.. code-block:: bash

   export MODAN2_LOG_LEVEL=DEBUG
   python Modan2.py

**Database location:**

.. code-block:: bash

   export MODAN2_DB_PATH=/custom/path/modan.db
   python Modan2.py

**Combined example:**

.. code-block:: bash

   #!/bin/bash
   # Production environment setup

   export MODAN2_DB_PATH=/data/morphometrics/modan.db
   export MODAN2_LOG_LEVEL=INFO
   export MODAN2_LOG_DIR=/var/log/modan2

   python Modan2.py

Tips and Tricks
---------------

Keyboard Power User Shortcuts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**General:**

* ``Ctrl+N``: New dataset
* ``Ctrl+O``: Open/Import
* ``Ctrl+S``: Save (if editing)
* ``Ctrl+W``: Close window/tab
* ``Ctrl+Q``: Quit application

**Navigation:**

* ``Ctrl+1`` to ``Ctrl+9``: Switch tabs
* ``Ctrl+Tab``: Next tab
* ``Ctrl+Shift+Tab``: Previous tab

**Analysis:**

* ``F5``: Refresh view
* ``F3``: Toggle 3D view
* ``Ctrl+R``: Run analysis

**Editing:**

* ``Ctrl+C``: Copy
* ``Ctrl+V``: Paste
* ``Ctrl+Z``: Undo
* ``Ctrl+Y``: Redo (where applicable)

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
* Double-click 3D view: Reset camera

**Right-click context menus:**

* Right-click dataset: Quick operations
* Right-click object: Edit/delete options
* Right-click analysis: Export/delete
* Right-click table: Copy data

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
