Modan2 Documentation
====================

Welcome to Modan2's documentation!

Modan2 is a user-friendly desktop application that empowers researchers to explore and understand shape variations through geometric morphometrics. It streamlines the entire workflow from data acquisition (2D/3D) to statistical analysis and visualization.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quick_start
   user_guide
   faq
   troubleshooting
   advanced_features
   developer_guide
   changelog

Features
--------

* **Hierarchical Data Management**: Organize data into nested datasets with a clear structure
* **2D & 3D Visualization**: Integrated viewers for 2D images and 3D models with landmark plotting
* **Semi-landmark Curves**: Trace curves on specimens and resample them into evenly-spaced semi-landmarks, with edge-snapping (live-wire) auto-detection
* **Statistical Analysis**: Perform Principal Component Analysis (PCA), Canonical Variate Analysis (CVA), and MANOVA
* **Missing Landmark Support**: Advanced handling of incomplete landmark data with shape-fitted visual estimation
* **Digitizing Aids**: Dataset-wide landmark names/descriptions and a "Show Expected" guide that predicts remaining landmark positions
* **Data Import/Export**: Supports various file types (TPS, NTS, X1Y1, Morphologika, OBJ, PLY, STL) plus a JSON+ZIP package format that bundles images and 3D models, all with drag-and-drop
* **Persistent Storage**: All data and analyses saved in a local SQLite database managed by Peewee ORM

Quick Start
-----------

Installation
~~~~~~~~~~~~

Download the latest version from the `releases page <https://github.com/jikhanjung/Modan2/releases>`_.
Package names carry the version and build number.

For Windows:
   Download the installer ZIP and run the installer inside it

For macOS:
   Download the DMG and drag ``Modan2.app`` to Applications

For Linux:
   Download the AppImage, make it executable, and run it

Only the Windows build is well tested; see :doc:`installation` for details.

Basic Usage
~~~~~~~~~~~

1. **Create a New Dataset**

   Click "New Dataset" or press ``Ctrl+N`` to create a dataset for your morphometric study.

2. **Import Objects**

   Drag and drop 2D images or 3D models onto your dataset's object table, or use **Data → Import** (``Ctrl+I``) to load a landmark file (TPS, NTS, X1Y1, Morphologika) as a new dataset.

3. **Place Landmarks**

   Double-click an object to open the Object Dialog, then click on the image/model to place landmarks.

4. **Run Analysis**

   Select your dataset and click **Analyze** (``Ctrl+G``) to perform:

   - Superimposition (Procrustes or Bookstein; aligns shapes)
   - Principal Component Analysis (PCA)
   - Canonical Variate Analysis (CVA)
   - MANOVA (multivariate analysis of variance)

5. **Explore Results**

   Select the analysis in the tree to see its PCA, CVA (with classification accuracy) and MANOVA results; on the PCA tab, click **Data Exploration** for interactive plots and shape variations, or **Analysis Details** for the result tables.

**Keyboard Shortcuts**:

- ``Ctrl+N`` - New Dataset
- ``Ctrl+Shift+N`` - New Object
- ``Ctrl+S`` - Save changes
- ``Ctrl+I`` - Import
- ``Ctrl+G`` - Analyze
- ``Delete`` - Clear the selected cells in the object table

For more detailed instructions, see the :doc:`user_guide`.

Technology Stack
----------------

- **Language**: Python 3.12+
- **GUI Framework**: PyQt5
- **Core Libraries**:
    - **Database ORM**: Peewee
    - **Numerical/Scientific**: NumPy, SciPy, Pandas, Statsmodels
    - **3D Graphics & Image Processing**: PyOpenGL, Trimesh, Pillow, OpenCV

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
