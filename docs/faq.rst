Frequently Asked Questions (FAQ)
=================================

.. contents:: Table of Contents
   :local:
   :depth: 2

General Questions
-----------------

What is Modan2?
~~~~~~~~~~~~~~~

Modan2 is a user-friendly desktop application for geometric morphometrics research. It enables researchers to analyze shape variations in 2D and 3D data through landmark-based methods and statistical analysis.

**Key features:**

* Hierarchical dataset management with parent-child relationships
* 2D image and 3D model landmark digitization
* Statistical analysis (PCA, CVA, MANOVA)
* Multiple file format support (TPS, NTS, Morphologika, OBJ, PLY, STL)
* Comprehensive visualization tools
* Built-in Procrustes superimposition

Who is Modan2 for?
~~~~~~~~~~~~~~~~~~

Modan2 is designed for:

* **Researchers** in biology, paleontology, anthropology
* **Graduate students** learning geometric morphometrics
* **Morphologists** analyzing shape variation
* **Evolutionary biologists** studying form and function
* **Anyone** working with landmark-based shape analysis

What makes Modan2 different from other morphometrics software?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Traditional morphometrics software challenges:**

* Complex commercial software with steep learning curve
* Expensive licenses
* Limited 2D/3D integration
* Difficult data management

**Modan2 advantages:**

* Free and open source (MIT license)
* Intuitive interface designed for researchers
* Integrated 2D/3D workflow in one application
* Hierarchical dataset organization
* Built-in database for persistent storage
* Active development and community support

What file formats does Modan2 support?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Input Formats:**

* **Landmark data:** TPS, NTS, X1Y1, Morphologika
* **3D models:** OBJ, PLY, STL
* **Images:** JPG, PNG, BMP, TIF (for 2D landmark digitization)
* **Import/Export:** JSON+ZIP packages (complete dataset backup)

**Output Formats:**

* Same as input for landmark data
* Excel/CSV for analysis results
* JSON+ZIP for complete dataset sharing

Installation and Setup
----------------------

What are the system requirements?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Minimum Requirements:**

* **OS:** Windows 10+, macOS 10.14+, or Ubuntu 18.04+
* **CPU:** Dual-core processor (2.0 GHz+)
* **RAM:** 4GB minimum
* **Disk:** 500MB for application + space for datasets
* **Display:** 1280×720 resolution
* **Graphics:** OpenGL 3.3+ compatible GPU

**Recommended Requirements:**

* **CPU:** Quad-core processor (3.0 GHz+)
* **RAM:** 8GB or more
* **Disk:** 2GB for datasets
* **Display:** 1920×1080 or higher
* **Graphics:** Dedicated GPU for 3D visualization

How do I install Modan2?
~~~~~~~~~~~~~~~~~~~~~~~~~

**Binary Installation (Easiest):**

1. Download from https://github.com/jikhanjung/Modan2/releases
2. Windows: Run installer ``Modan2-Setup.exe``
3. macOS: Open DMG and drag to Applications
4. Linux: Use AppImage or install from source

**From Source (For Developers):**

.. code-block:: bash

   git clone https://github.com/jikhanjung/Modan2.git
   cd Modan2
   pip install -r requirements.txt
   python Modan2.py

See the Installation Guide for detailed instructions.

Where is my data stored?
~~~~~~~~~~~~~~~~~~~~~~~~~

**Database Location:**

* Windows: ``%APPDATA%\Modan2\modan.db``
* Linux/macOS: ``~/.local/share/Modan2/modan.db``

**Settings File:**

* Windows: ``%APPDATA%\Modan2\settings.json``
* Linux/macOS: ``~/.config/Modan2/settings.json``

**Log Files:**

* Windows: ``%APPDATA%\Modan2\logs\``
* Linux/macOS: ``~/.local/share/Modan2/logs/``

**Note:** Original image and 3D model files remain in their original locations. Only landmark data is stored in the database.

Can I backup my data?
~~~~~~~~~~~~~~~~~~~~~

**Yes!** Multiple backup options:

1. **Copy database file**

   * Locate ``modan.db`` (see above)
   * Copy to backup location
   * Restore by replacing database file

2. **Export datasets**

   * Export as JSON+ZIP package (includes all data and files)
   * Export as TPS, Morphologika, or other formats

3. **Manual backup**

   * Keep original image/model files
   * Export landmark data regularly
   * Export analysis results

Data Management
---------------

What is a dataset in Modan2?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A **dataset** is a collection of objects (specimens) with shared:

* Number of landmarks
* Dimension (2D or 3D)
* Variable definitions (measurements, categories)
* Wireframe/baseline/polygon definitions
* Analysis settings

Datasets can have **parent-child relationships** for hierarchical organization.

How do parent-child datasets work?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Parent dataset:**

* Contains original landmark data
* Defines basic structure (landmark count, dimension)

**Child dataset:**

* Inherits from parent
* Can apply different Procrustes superimposition
* Can have different object subsets
* Can have additional variables
* Shares landmark definitions with parent

**Use cases:**

* Compare different superimposition methods
* Analyze subgroups from same original data
* Test different analytical approaches

What is the difference between objects and datasets?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Dataset:**

* Container for multiple objects
* Defines structure (landmark count, dimension, variables)
* Settings for visualization and analysis

**Object:**

* Individual specimen
* Contains landmark coordinates
* Can have attached image or 3D model
* Has variable values (measurements, categories)

**Relationship:** Dataset contains multiple objects

How many landmarks can I use?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Practical limits:**

* **2D:** Up to 1000 landmarks per object (tested)
* **3D:** Up to 1000 landmarks per object (tested)
* **Objects:** Tested with 2,000 objects successfully

**Performance:**

* 100 landmarks, 1000 objects: Excellent performance
* Memory usage scales linearly (~4KB per object)
* Analysis time depends on landmark count and algorithm

Can I have missing landmarks?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Yes!** Modan2 supports missing landmarks:

* Mark landmarks as "missing" in object dialog
* Missing landmarks excluded from analyses
* Visualization shows missing landmarks differently
* Can estimate missing landmarks from existing data

**Estimation methods:**

* Thin-plate spline (TPS) interpolation
* Mean configuration estimation
* Manual estimation

Landmark Digitization
---------------------

How do I digitize landmarks on 2D images?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Steps:**

1. Create dataset → Set dimension to 2D
2. Create object → Attach image
3. Open object dialog
4. Click on image to place landmarks
5. Landmarks numbered sequentially
6. Right-click to delete last landmark
7. Save when complete

**Tips:**

* Zoom in for precision (mouse wheel)
* Pan by dragging with middle button
* Use wireframe to verify landmark placement
* Mark missing landmarks if needed

How do I digitize landmarks on 3D models?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Steps:**

1. Create dataset → Set dimension to 3D
2. Create object → Attach 3D model
3. Open object dialog
4. Rotate model to view landmark location
5. Click to place landmark
6. Landmark appears as sphere
7. Continue for all landmarks
8. Save when complete

**3D Controls:**

* Left-drag: Rotate
* Middle-drag: Pan
* Scroll: Zoom
* Double-click: Reset view
* Right-click: Context menu

Can I edit existing landmarks?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Yes!** Multiple editing options:

1. **Visual editing:**

   * Open object dialog
   * Click and drag landmarks
   * Updates in real-time

2. **Table editing:**

   * Edit X, Y, Z coordinates directly in table
   * Precision editing for fine adjustments

3. **Batch editing:**

   * Select multiple objects
   * Apply transformations
   * Update landmarks programmatically

Statistical Analysis
--------------------

What analyses does Modan2 support?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Multivariate Analysis:**

* **PCA (Principal Component Analysis):** Explore main patterns of variation
* **CVA (Canonical Variate Analysis):** Analyze group differences
* **MANOVA (Multivariate Analysis of Variance):** Test group differences

**Procrustes Methods:**

* **Full Procrustes:** Translation, rotation, scaling
* **Partial Procrustes:** Translation, rotation only
* **Bookstein registration:** Align using baseline
* **Resistant Fit:** Robust to outliers

**Shape Analysis:**

* Mean shape calculation
* Shape differences visualization
* Regression analysis
* Size and shape components

How do I run a PCA analysis?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Steps:**

1. Select dataset in tree view
2. Click Analysis → New Analysis
3. Analysis Type: PCA
4. Optional: Select grouping variable for coloring
5. Click OK
6. Results appear in new tab

**PCA Results Include:**

* Scree plot (variance explained)
* Score plots (PC1 vs PC2, etc.)
* Loadings visualization
* Shape variation along PCs
* Export options

What is Procrustes superimposition?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Procrustes superimposition** removes non-shape variation:

1. **Translation:** Centers configurations
2. **Rotation:** Aligns to minimize distance
3. **Scaling:** Standardizes size (optional)

**Purpose:** Compare shape independent of:

* Position (translation)
* Orientation (rotation)
* Size (scaling, if full Procrustes)

**Result:** Procrustes coordinates represent pure shape

How many objects do I need for analysis?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Minimum requirements:**

* **PCA:** At least 3 objects (more recommended)
* **CVA:** At least 2 groups with 3+ objects each
* **MANOVA:** At least 2 groups with 3+ objects each

**Recommended sample sizes:**

* **Exploratory PCA:** 20-30 objects minimum
* **Group comparison (CVA):** 10-15 per group minimum
* **Publication quality:** 30+ per group recommended

**General rule:** More is better for robust results

File Import and Export
----------------------

How do I import landmark data?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Steps:**

1. File → Import → [Format]
2. Select file (TPS, NTS, Morphologika, etc.)
3. Choose or create target dataset
4. Map variables if needed
5. Click Import

**Supported formats:**

* TPS (most common)
* NTS
* X1Y1
* Morphologika
* JSON+ZIP (complete backup)

Can I import from other software?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Yes!** Modan2 supports standard formats:

* **From MorphoJ:** Export as TPS or Morphologika
* **From tpsUtil/tpsDig:** Use TPS files directly
* **From Landmark Editor:** Export as NTS
* **From R packages:** Save as TPS or Morphologika

**Format compatibility:**

* TPS: Most compatible format
* Morphologika: Good for complex datasets
* NTS: Simple format

How do I export my data?
~~~~~~~~~~~~~~~~~~~~~~~~~

**Export options:**

1. **Dataset export:**

   * File → Export → Dataset
   * Choose format (TPS, Morphologika, JSON+ZIP)
   * Select objects to export

2. **Analysis results:**

   * Right-click analysis → Export
   * Save as Excel or CSV
   * Includes scores, loadings, statistics

3. **Complete backup:**

   * Export as JSON+ZIP
   * Includes all data, images, models
   * Perfect for sharing or archiving

What is JSON+ZIP export?
~~~~~~~~~~~~~~~~~~~~~~~~~

**JSON+ZIP** is Modan2's comprehensive backup format:

**Includes:**

* Landmark coordinates
* Object metadata and variables
* Dataset settings (wireframe, baseline, polygons)
* Attached images and 3D models (optional)
* Analysis results

**Use cases:**

* Complete dataset backup
* Sharing data with collaborators
* Moving data between computers
* Long-term archival

**Format:** Industry-standard JSON + ZIP compression

Performance and Optimization
-----------------------------

How fast can Modan2 handle large datasets?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Tested Performance** (Phase 7 validation):

* **1000 objects load:** 277ms (18× faster than target)
* **1000 objects PCA:** 60ms (33× faster than target)
* **Memory usage:** 4KB per object (125× better than target)
* **UI responsiveness:** 12.63ms for 1000-row table

**Scalability:**

* Linear O(n) scaling confirmed
* Production-ready for 100,000+ objects
* Tested up to 2,000 objects

Can I improve performance?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Tips for best performance:**

1. **Use SSD** for database storage
2. **Close unused objects** in tree view
3. **Reduce polygon count** for 3D models
4. **Disable** 3D preview during batch editing
5. **Export subsets** for large analyses

**System optimization:**

* Ensure adequate RAM (8GB+ recommended)
* Update graphics drivers for 3D performance
* Use 64-bit Python installation

What if analysis is taking too long?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**For large datasets:**

1. **Check progress bar** - may still be running
2. **Reduce object count** - analyze subset first
3. **Simplify analysis** - fewer variables
4. **Check memory** - ensure sufficient RAM

**Typical analysis times:**

* 100 objects: < 1 second
* 1000 objects: 1-5 seconds
* 2000 objects: 5-15 seconds

**If much slower:** Check troubleshooting guide

Troubleshooting
---------------

Where do I get help?
~~~~~~~~~~~~~~~~~~~~

**Resources (in order):**

1. **This FAQ** - Quick answers to common questions
2. **User Guide** - Comprehensive documentation
3. **Troubleshooting Guide** - Detailed problem-solving
4. **GitHub Issues** - Search existing problems/solutions

   https://github.com/jikhanjung/Modan2/issues

5. **GitHub Discussions** - Ask questions, share workflows

   https://github.com/jikhanjung/Modan2/discussions

6. **Email Support** - jikhanjung@gmail.com

   (Please try above resources first)

How do I report a bug?
~~~~~~~~~~~~~~~~~~~~~~

**GitHub Issues:** https://github.com/jikhanjung/Modan2/issues/new

**Include this information:**

1. **System info:**

   * Operating system and version
   * Python version (``python --version``)
   * Modan2 version (Help → About)

2. **Problem description:**

   * What you were trying to do
   * What actually happened
   * Error message (if any)

3. **Steps to reproduce:**

   1. Open dataset...
   2. Click button...
   3. Error appears...

4. **Log files:**

   * Help → View Logs
   * Attach relevant log files

5. **Screenshots** (if UI-related)

**Good bug reports get fixed faster!**

Why does Modan2 crash?
~~~~~~~~~~~~~~~~~~~~~~

**Common causes:**

1. **Corrupted database** → Restore from backup
2. **Out of memory** → Close other applications
3. **Graphics driver issues** → Update GPU drivers
4. **Qt plugin conflicts** → Use fix_qt_import.py (Linux)
5. **Missing dependencies** → Reinstall requirements

**Debugging steps:**

1. Check log files for error messages
2. Try with sample data (isolate problem)
3. Run from command line to see errors
4. Report crash with log files attached

See Troubleshooting Guide for detailed solutions.

The 3D viewer is not working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Common issues:**

1. **OpenGL not available:**

   * Update graphics drivers
   * Install OpenGL libraries (Linux)
   * Check GPU compatibility

2. **Model not loading:**

   * Verify file format (OBJ, PLY, STL)
   * Check file is not corrupted
   * Try different model

3. **Black screen:**

   * Reset view (double-click)
   * Check lighting settings
   * Try different model

See Troubleshooting Guide → 3D Visualization Issues

Advanced Topics
---------------

Can I use Modan2 in a publication?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Yes! Please do.**

**How to cite:**

.. code-block:: bibtex

   @software{modan2_2025,
     author = {Jung, Jikhan},
     title = {Modan2: Geometric Morphometrics Analysis Software},
     year = {2025},
     publisher = {GitHub},
     url = {https://github.com/jikhanjung/Modan2},
     version = {0.1.5-beta.1}
   }

**In text:**

"Geometric morphometric analyses were performed using Modan2 v0.1.5 (Jung, 2025), an open-source desktop application for landmark-based shape analysis."

Can I extend Modan2 with custom analyses?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Yes!** Modan2 is extensible:

* **Python API:** Use modules directly in custom scripts
* **Database access:** Query database with Peewee ORM
* **Export data:** Analyze in R, Python, MATLAB
* **Custom tools:** Add to Tools menu

See Developer Guide for API documentation.

How does the database work?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Technology:**

* **Engine:** SQLite (embedded database)
* **ORM:** Peewee (Python Object-Relational Mapping)
* **Location:** Single file (modan.db)

**Tables:**

* md_dataset: Dataset definitions
* md_object: Objects and landmark data
* md_image: 2D image attachments
* md_threedmodel: 3D model attachments
* md_analysis: Analysis results

**Advantages:**

* No server required
* Portable (single file)
* ACID compliant (data integrity)
* Fast queries
* Easy backup

Can I run Modan2 on a server?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Not currently.** Modan2 requires GUI environment.

**Future feature:** Command-line interface for server deployment planned.

**Current workarounds:**

* Use VNC/Remote Desktop for GUI access
* Or use X11 forwarding over SSH:

  .. code-block:: bash

     ssh -X user@server
     python Modan2.py

Development and Contributing
-----------------------------

Is Modan2 open source?
~~~~~~~~~~~~~~~~~~~~~~~

**Yes!**

* **License:** MIT License (permissive)
* **Repository:** https://github.com/jikhanjung/Modan2
* **Free to use:** Commercial and non-commercial
* **Free to modify:** Change, extend, redistribute

**This means you can:**

* Use in research (published papers)
* Use in commercial projects
* Modify for your specific needs
* Redistribute (must include license)

Can I contribute to Modan2?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Absolutely! Contributions welcome:**

**Ways to contribute:**

1. **Report bugs** - GitHub Issues
2. **Suggest features** - GitHub Discussions
3. **Fix bugs** - Submit Pull Request
4. **Add features** - Submit Pull Request
5. **Improve documentation** - Edit .rst/.md files
6. **Write tutorials** - Share workflows
7. **Translate UI** - Add new languages (future)

**Getting started:**

1. Read CONTRIBUTING.md (when available)
2. Fork the repository
3. Make your changes
4. Submit Pull Request

**No contribution is too small!** Even fixing typos helps.

What features are planned?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Short-term (v1.0):**

* Enhanced documentation
* UI polish and accessibility
* Performance optimization
* Additional statistical tests
* Beta testing program

**Long-term (v1.1+):**

* Command-line interface for batch processing
* Additional analysis methods
* Enhanced 3D visualization
* Plugin system
* Cloud storage integration
* Mobile companion app

See GitHub Issues and Milestones for details.

Who develops Modan2?
~~~~~~~~~~~~~~~~~~~~~

**Primary developer:**

* Jikhan Jung (@jikhanjung)
* Part of PaleoBytes software suite
* Developed for morphometrics research

**Contributors:**

* See GitHub contributors page
* Community bug reports and suggestions
* Open source contributions welcome

**Funding/Support:**

* Academic research project
* No commercial backing
* Developed for research community

License and Legal
-----------------

Can I use Modan2 commercially?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Yes!** MIT License permits:

* **Commercial use** - Use in for-profit projects
* **Modification** - Adapt to your needs
* **Distribution** - Redistribute modified versions
* **Private use** - Use internally without sharing

**Requirements:**

* Include MIT License text
* Include copyright notice

**No warranty:** Software provided "as-is"

What if Modan2 damages my data?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Disclaimer:**

* Software provided "as-is" (MIT License)
* No warranty of any kind
* **Always backup original data**

**Best practices:**

* Keep original landmark data unchanged
* Test with sample data first
* Regular backups
* Export important results

**In practice:**

* Modan2 uses database transactions (safe)
* Does not modify original files
* Risk is very low with normal use

Still Have Questions?
---------------------

**Check these resources:**

1. **Installation Guide** - Setup and configuration
2. **User Guide** - Detailed usage instructions
3. **Troubleshooting Guide** - Problem-solving
4. **Developer Guide** - Technical details
5. **Advanced Features** - Power user tips

**Contact:**

* GitHub Issues: https://github.com/jikhanjung/Modan2/issues
* Discussions: https://github.com/jikhanjung/Modan2/discussions
* Email: jikhanjung@gmail.com

**This FAQ is open source!**

Found an error? Have suggestions? Submit a PR to improve this document.
