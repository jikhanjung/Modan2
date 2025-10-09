Modan2 Documentation
====================

Welcome to Modan2's documentation!

Modan2 is a user-friendly desktop application that empowers researchers to explore and understand shape variations through geometric morphometrics. It streamlines the entire workflow from data acquisition (2D/3D) to statistical analysis and visualization.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
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
* **Statistical Analysis**: Perform Principal Component Analysis (PCA), Canonical Variate Analysis (CVA), and MANOVA
* **Missing Landmark Support**: Advanced handling of incomplete landmark data with visual estimation
* **Data Import/Export**: Supports various file types (TPS, NTS, OBJ, PLY, STL) with drag-and-drop
* **Persistent Storage**: All data and analyses saved in a local SQLite database managed by Peewee ORM

Quick Start
-----------

Installation
~~~~~~~~~~~~

Download the latest version from the `releases page <https://github.com/jikhanjung/Modan2/releases>`_.

For Windows:
   Download and run the installer (``Modan2-Setup.exe``)

For Linux/macOS:
   Download the appropriate package or run from source

Basic Usage
~~~~~~~~~~~

1. **Create a New Dataset**

   Click "New Dataset" or press ``Ctrl+N`` to create a dataset for your morphometric study.

2. **Import Objects**

   Drag and drop 2D images or 3D models into your dataset, or use File → Import to load landmark files (TPS, NTS).

3. **Place Landmarks**

   Double-click an object to open the Object Dialog, then click on the image/model to place landmarks.

4. **Run Analysis**

   Select your dataset and click "Analyze Dataset" to perform:

   - Procrustes superimposition (aligns shapes)
   - Principal Component Analysis (PCA)
   - Canonical Variate Analysis (CVA)
   - MANOVA (multivariate analysis of variance)

5. **Explore Results**

   View PC plots, shape variations, and statistical outputs in the Data Exploration dialog.

**Keyboard Shortcuts**:

- ``Ctrl+N`` - New Dataset
- ``Ctrl+Shift+N`` - New Object
- ``Ctrl+S`` - Save changes
- ``Ctrl+O`` - Open database
- ``Delete`` - Delete selected items

For more detailed instructions, see the :doc:`user_guide`.

Technology Stack
----------------

- **Language**: Python 3.11+
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
