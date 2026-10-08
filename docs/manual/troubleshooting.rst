Troubleshooting Guide
=====================

This guide provides solutions to common problems and errors you may encounter while using Modan2.

.. contents:: Table of Contents
   :local:
   :depth: 2

.. _where-things-live:

Where Modan2 Keeps Your Files
-----------------------------

Several problems below come down to a file being missing or unwritable, so it
helps to know where things are. ``~`` is your home folder (for example
``C:\Users\<you>`` on Windows). These are the defaults; **Edit → Preferences →
Data folder** moves the whole library elsewhere.

+-------------------+-------------------------------------+
| What              | Where                               |
+===================+=====================================+
| Database          | ``~/PaleoBytes/Modan2/Modan2.db``   |
+-------------------+-------------------------------------+
| Images, 3D models | ``~/PaleoBytes/Modan2/data/``       |
+-------------------+-------------------------------------+
| Log files         | ``~/PaleoBytes/Modan2/logs/``       |
+-------------------+-------------------------------------+
| Backups           | ``~/PaleoBytes/Modan2/backups/``    |
+-------------------+-------------------------------------+
| Preferences       | your OS settings folder (see below) |
+-------------------+-------------------------------------+

Installation Issues
-------------------

Application Will Not Start
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Windows**

* Windows Defender or SmartScreen may block the unsigned installer. Choose
  "More info" → "Run anyway" if you trust the source.
* If the installer itself will not run, check that you extracted it from the
  downloaded ZIP first — running it from inside the archive can fail.

**macOS**

* On first launch, right-click the app and choose "Open" to get past the
  Gatekeeper warning for unsigned applications.

**Linux**

* Make sure the AppImage is executable: ``chmod +x Modan2-Linux-*.AppImage``
* If it exits complaining about FUSE, either install it
  (``sudo apt-get install libfuse2`` on Ubuntu/Debian) or run it with
  ``--appimage-extract-and-run``.

.. note::
   Only the Windows build is well tested. If the macOS or Linux package fails in
   a way not covered here, please report it on the
   `issues page <https://github.com/jikhanjung/Modan2/issues>`_.

Permission Issues
~~~~~~~~~~~~~~~~~

**Problem:** "Permission denied" when opening the database or saving files

**Windows Solution:**

1. Right-click Modan2.exe → "Run as administrator" (not recommended for normal use)
2. Or change folder permissions:

   * Right-click the folder → Properties → Security
   * Ensure your user has "Full control"

**Linux/macOS Solution:**

.. code-block:: bash

   # Check permissions
   ls -la ~/PaleoBytes/Modan2

   # Fix permissions if needed
   chmod -R u+rw ~/PaleoBytes/Modan2

**Problem:** Settings not saving

Preferences are saved when you close the Preferences dialog (window sizes and
positions when you quit), to your operating system's settings folder:

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

**Solution:**

1. Check write permissions on that directory
2. Delete a corrupted settings file to regenerate defaults — quit Modan2 first:

   .. code-block:: bash

      # Windows (PowerShell)
      rm "$env:LOCALAPPDATA\PaleoBytes\Modan2\preferences.json"

      # macOS
      rm ~/Library/Application\ Support/PaleoBytes/Modan2/preferences.json

      # Linux
      rm ~/.config/PaleoBytes/Modan2/preferences.json

Database Issues
---------------

Database File Corrupted
~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** "Database is locked" or "Database disk image is malformed"

**Symptoms:**

* Cannot open Modan2
* Error messages about database
* Data not saving

**Solution 1: Close other instances**

Ensure no other Modan2 processes are running:

.. code-block:: bash

   # Windows
   tasklist | findstr Modan2
   # If found: taskkill /F /IM Modan2.exe

   # Linux/macOS
   ps aux | grep Modan2
   # If found: kill <pid>

**Solution 2: Backup and restore**

.. code-block:: bash

   # 1. Locate database
   # Database: ~/PaleoBytes/Modan2/Modan2.db

   # 2. Make backup
   cp Modan2.db Modan2.db.backup

   # 3. Try SQLite repair
   sqlite3 Modan2.db "PRAGMA integrity_check;"

   # 4. If corrupted beyond repair, restore from backup
   cp Modan2.db.backup Modan2.db

**Solution 3: Export and reimport**

If you have a recent backup:

1. **Data → Back Up Library...** (or keep the backup you already have)
2. Quit Modan2 and move ``Modan2.db`` aside
3. Start Modan2 — it creates a new, empty database
4. **Data → Restore from Backup...**

Cannot Access Database
~~~~~~~~~~~~~~~~~~~~~~

**Problem:** "Unable to open database file" error

**Causes:**

* Database file missing
* Incorrect permissions
* Disk full
* File locked by another process

**Solution:**

1. **Check file exists:**

   .. code-block:: bash

      # Linux/macOS
      ls -la ~/PaleoBytes/Modan2/Modan2.db

2. **Check disk space:**

   .. code-block:: bash

      # Linux
      df -h ~

      # Windows (PowerShell)
      Get-PSDrive C

3. **Create directory if missing:**

   .. code-block:: bash

      mkdir -p ~/PaleoBytes/Modan2

4. **Let Modan2 create new database:**

   * Start Modan2
   * New database created automatically
   * Import data from backups

Data Loading and Import Issues
-------------------------------

Import File Format Not Recognized
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** "File type not supported.", "Failed to read package: …" or
"Import failed: …" error

**Supported formats:**

* **Landmark data:** TPS, NTS, X1Y1, Morphologika, JSON+ZIP
* **3D models:** OBJ, PLY, STL
* **Images:** JPG, PNG, BMP, TIF

**Solution:**

1. **Verify file format:**

   * Check file extension matches content
   * Open in text editor to verify format

2. **TPS file issues:**

   .. code-block:: text

      # Valid TPS format
      LM=5
      100.5 200.3
      150.2 180.9
      ...
      ID=specimen1
      IMAGE=path/to/image.jpg

   Common issues:

   * Missing LM= line
   * Incorrect coordinate format
   * Missing ID= or IMAGE= lines

3. **Try different format:**

   * Convert to TPS using tpsUtil
   * Or use Morphologika format

Missing Data After Import
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Objects imported but no landmarks visible

**Causes:**

* Landmark coordinates all zero
* Incorrect dimension (2D vs 3D)
* Scale mismatch

**Solution:**

1. **Check coordinates in table:**

   * Open object dialog
   * View landmark table
   * Verify non-zero coordinates

2. **Check dimension:**

   * Dataset should match file (2D/3D)
   * Recreate dataset with correct dimension

3. **Check scale:**

   * Landmarks may be outside viewing range
   * Zoom out with the mouse wheel
   * Check coordinate values are reasonable

Image/Model Not Loading
~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** "Failed to import image: …" or "Failed to import 3D model: …", or
an object shows no image or model

**Solution:**

1. **Check file paths:**

   * Modan2 keeps its own copy of each image or model in the data folder
     (``data/<dataset id>/``); moving or deleting your original file does not
     affect it
   * If that copy is missing, re-attach the file (below)

2. **Verify file integrity:**

   .. code-block:: bash

      # Check file size
      ls -lh image.jpg

      # Try opening in another program
      # Images: Image viewer
      # 3D models: MeshLab, Blender

3. **Supported formats:**

   * **Images:** JPG, PNG, BMP, TIF (RGB or grayscale)
   * **3D models:** OBJ, PLY, STL (text or binary)

4. **Re-attach files:**

   * Double-click the object (or right-click → **Edit object**)
   * Click **Load Image** / **Load 3D Model**
   * Browse to correct file, then **Save**

Analysis Errors
---------------

PCA/CVA/MANOVA Fails
~~~~~~~~~~~~~~~~~~~~

**Problem:** Analysis fails with error message

**Common causes:**

1. **Not enough objects:**

   * Any analysis: at least 5 objects with landmarks
   * CVA/MANOVA: at least 2 groups in the grouping variable

2. **Missing landmarks:**

   * Missing landmarks are estimated automatically during analysis
   * A landmark missing in *every* object cannot be estimated
   * Objects with fewer landmarks than the dataset expects are refused
   * Solution: record each landmark on at least one object, and use **Insert
     Missing** in the object dialog where a specimen is short

3. **No variables:**

   * The analysis will not run at all without at least one variable (every run
     includes CVA and MANOVA)
   * Solution: add one in the dataset dialog's **Variables** tab (or **Add
     variable** in the main window) and fill in its values

4. **Insufficient variation:**

   * All objects identical or nearly identical
   * Solution: Check data quality

**Solution:**

1. **Check object count:**

   * The number in brackets after the dataset's name in the tree is its object
     count
   * Ensure sufficient objects

2. **Check for missing data:**

   * Review objects for missing landmarks
   * Tick **Show Estimated** in the object dialog to see the estimates

3. **Verify grouping variable:**

   * CVA/MANOVA require categorical variable
   * Create variable in dataset dialog
   * Assign values to objects

Procrustes Alignment Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** "Procrustes failed" or incorrect alignment

**Causes:**

* Collinear landmarks (all on one line)
* Insufficient landmarks (< 3 for 2D, < 4 for 3D)
* All landmarks at same position
* Scale issues

**Solution:**

1. **Check landmark quality:**

   * View objects in viewer
   * Ensure landmarks properly distributed
   * No duplicates at same position

2. **Try different method:**

   * Try Bookstein registration (needs a baseline on the dataset)

3. **Check for outliers:**

   * Some objects very different from others
   * May cause alignment issues
   * Try excluding outliers

Analysis Results Look Wrong
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Unexpected PCA/CVA results

**Possible causes:**

* Incorrect Procrustes method
* Wrong grouping variable
* Outliers affecting results
* Missing landmarks not handled properly

**Solution:**

1. **Verify Procrustes settings:**

   * Check which superimposition used
   * Try different method

2. **Check for outliers:**

   * View PC score plots
   * Look for extreme points
   * Investigate unusual specimens

3. **Verify grouping:**

   * CVA: Ensure correct grouping variable selected
   * Check group assignments

4. **Check sample size:**

   * Small samples may give unstable results
   * Need larger sample for robust analysis

3D Visualization Issues
-----------------------

3D Viewer Black Screen
~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** 3D viewer shows black screen or nothing visible

**Solution:**

1. **Reset view:**

   * Scroll or right-drag to zoom out, and middle-drag to pan (the object viewer
     has no reset-view command; in Data Exploration, use **Reset Pose**)

2. **Check OpenGL:**

   .. code-block:: bash

      # Linux - verify OpenGL working
      glxinfo | grep "OpenGL version"

      # Install if needed
      sudo apt-get install mesa-utils libglu1-mesa

3. **Update graphics drivers:**

   * Windows: NVIDIA, AMD, or Intel website
   * Linux: Use distribution's driver manager
   * macOS: Use Software Update

4. **Check model loaded:**

   * Verify 3D model file attached
   * Try different model
   * Check file is valid OBJ/PLY/STL

OpenGL Errors
~~~~~~~~~~~~~

**Problem:** "OpenGL error" or "Failed to initialize OpenGL context"

**Linux Solution:**

.. code-block:: bash

   # Install OpenGL libraries
   sudo apt-get install mesa-utils libglu1-mesa-dev \
     freeglut3-dev mesa-common-dev

   # Test OpenGL
   glxinfo | grep "OpenGL version"

**Windows Solution:**

1. Update graphics drivers
2. Try forcing software rendering (slower but works):

   .. code-block:: batch

      set LIBGL_ALWAYS_SOFTWARE=1
      Modan2.exe

**macOS Solution:**

* OpenGL should work out of the box on macOS 10.14+
* Update macOS to latest version if issues

Landmark Spheres Not Visible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Cannot see landmark spheres in 3D viewer

**Solution:**

1. **Increase sphere size:**

   * **Edit → Preferences** → **Landmark**, 3D
   * Choose **Large**

2. **Check colours:**

   * Spheres may be hard to see against the background
   * Pick a brighter 3D landmark colour, or change **Background Color**, in
     **Edit → Preferences**

3. **Zoom in:**

   * Spheres may be too small at current zoom
   * Scroll to zoom closer

4. **Check wireframe:**

   * Wireframe may obscure spheres
   * Toggle wireframe visibility

Performance Issues
------------------

Application Slow to Start
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Modan2 takes long time to start

**Causes:**

* Large database
* Many datasets/objects loaded
* Disk I/O issues

**Solution:**

1. **Check database size:**

   * Location: See FAQ
   * Large database (>1GB) may slow startup

2. **Optimize database:**

   .. code-block:: bash

      sqlite3 Modan2.db "VACUUM;"

3. **Move to SSD:**

   * Database on HDD is slower
   * Move to SSD for better performance

4. **Reduce loaded data:**

   * Delete analyses you no longer need (right-click → **Delete analysis**)

Slow Analysis or Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Analysis takes very long or UI freezes

**Expected performance:**

* 100 objects: < 1 second
* 1000 objects: 1-5 seconds
* 2000 objects: 5-15 seconds

**If much slower:**

1. **Check object count:**

   * Select dataset → View object count
   * Verify within expected range

2. **Close other applications:**

   * Free up RAM
   * Close web browsers
   * Stop background processes

3. **Check system resources:**

   * Task Manager / Activity Monitor
   * Look for high CPU or memory usage
   * Close resource-heavy apps

4. **Simplify visualization:**

   * Reduce polygon count for 3D models
   * Disable wireframes
   * Close object viewers not in use

Out of Memory Errors
~~~~~~~~~~~~~~~~~~~~

**Problem:** "Out of memory" or crash with large datasets

**Solution:**

1. **Check RAM usage:**

   * Task Manager / Activity Monitor
   * Ensure sufficient RAM available

2. **Close other applications:**

   * Web browsers use lots of RAM
   * Close unnecessary programs

3. **Work with subsets:**

   * Analyze smaller groups
   * Export subsets of data

4. **Upgrade RAM:**

   * 4GB: Small datasets only
   * 8GB: Recommended for most work
   * 16GB+: Large datasets

UI and Display Issues
---------------------

UI Elements Not Displaying Correctly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Buttons, menus, or dialogs appear garbled or cut off

**Solution:**

1. **Check display scaling (Windows):**

   * Right-click desktop → Display settings
   * Set scaling to 100% or 125%
   * Restart Modan2

2. **Reset window geometry:**

   * Delete settings file (see above)
   * Restart Modan2
   * Windows repositioned to defaults

Font Issues
~~~~~~~~~~~

**Problem:** Text appears too small or too large

**Solution:**

1. **Adjust system font size:**

   * Windows: Settings → Display → Scale
   * macOS: System Preferences → Displays
   * Linux: Display settings in DE

2. **Application-specific (future):**

   * Font size settings planned
   * Currently uses system fonts

High DPI Display Issues
~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** UI elements tiny on 4K/high DPI displays

**Solution:**

1. **Enable high DPI scaling (Windows):**

   * Right-click Modan2.exe → Properties
   * Compatibility → High DPI settings
   * Override scaling behavior

2. **Set the Qt scaling environment variable** before launching Modan2:

   .. code-block:: bash

      # Windows (PowerShell)
      $env:QT_AUTO_SCREEN_SCALE_FACTOR=1

      # Linux/macOS
      export QT_AUTO_SCREEN_SCALE_FACTOR=1

   This is a Qt setting, not a Modan2 one; it must be set in the same shell you
   start the application from.

Advanced Troubleshooting
-------------------------

Collecting Debug Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When reporting issues, include this information:

1. **System Information:**

   * Your OS and its version
     (Windows: ``winver``; macOS: ``sw_vers``; Linux: ``lsb_release -a``)

2. **Modan2 version:**

   * **Help → About** (``F1``) shows the version
   * The build number appears on the splash screen and, with the version, in
     the name of the package you downloaded

3. **Log files:**

   * ``~/PaleoBytes/Modan2/logs/`` — attach the most recent one

Enabling Debug Logging
~~~~~~~~~~~~~~~~~~~~~~~

Start Modan2 with ``--debug`` for verbose logging. Launch it from a terminal (or
a Windows shortcut with the flag appended) so you can also see any startup error
printed there:

.. code-block:: bash

   # Linux (AppImage)
   ./Modan2-Linux-v<version>-build<build>.AppImage --debug

   # macOS
   /Applications/Modan2.app/Contents/MacOS/Modan2 --debug

   # Windows (PowerShell), from the installation folder
   .\Modan2.exe --debug

**View logs in real time:**

.. code-block:: bash

   # Linux/macOS
   tail -f ~/PaleoBytes/Modan2/logs/*.log

   # Windows PowerShell
   Get-Content -Path "$env:USERPROFILE\PaleoBytes\Modan2\logs\*.log" -Wait

Other Startup Options
~~~~~~~~~~~~~~~~~~~~~

* ``--db <path>`` — open a different database, useful for testing whether the
  problem is in your data or in the application
* ``--config <path>`` — use a different configuration file, to rule out a bad
  setting without deleting your own
* ``--no-splash`` — skip the splash screen
* ``--lang <en|ko>`` — force the interface language

Common Error Messages
---------------------

"Failed to connect to database"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause:** Database file locked or inaccessible

**Solution:** See "Database Issues" section above

"Procrustes superimposition failed"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause:** Insufficient or collinear landmarks

**Solution:** See "Procrustes Alignment Issues" section above

"… has too few objects with landmarks"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause:** Insufficient sample size

**Solution:** At least 5 objects with landmarks (and at least one variable) are
required

"Object '…' has N landmarks but this dataset expects M"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause:** Object has wrong number of landmarks for dataset

**Solution:**

1. Open the object
2. Use **Insert Missing** to add a placeholder at each position that was not
   recorded
3. Re-digitize object if needed

Getting Additional Help
-----------------------

If this guide doesn't solve your problem:

1. **Check FAQ:**

   Quick answers to common questions

2. **Check GitHub Issues:**

   https://github.com/jikhanjung/Modan2/issues

   Search for similar problems - they may already be solved

3. **Create New Issue:**

   Include:

   * Operating system and version
   * Modan2 version and build number
   * Error message or description
   * Steps to reproduce
   * Log files (see "Collecting Debug Information" above)

4. **GitHub Discussions:**

   For questions and general discussion:

   https://github.com/jikhanjung/Modan2/discussions

5. **Email Support:**

   Contact: jikhanjung@gmail.com

   (Please try above resources first)

Known Issues and Limitations
-----------------------------

Current Limitations
~~~~~~~~~~~~~~~~~~~

1. **Semi-landmark curves are 2D only:**

   * Curve tracing is available for 2D specimens; 3D curve tracing is not
     implemented yet
   * Semi-landmarks are not slid during Procrustes alignment

2. **Testing coverage by platform:**

   * Only the Windows build is well tested
   * macOS builds are not code-signed (first launch requires manual approval)
   * The Linux AppImage may need FUSE installed

3. **GUI only:**

   * There is no batch/headless mode; the startup options exist to configure a
     normal GUI session, not to run analyses without one

4. **Language:**

   * English and Korean interfaces are available
   * A few messages may still appear in English in the Korean interface

Planned Improvements
~~~~~~~~~~~~~~~~~~~~

See the CHANGELOG and GitHub milestones for planned features:

* 3D semi-landmark curve tracing
* Sliding semi-landmarks during alignment
* Image-assisted landmark suggestion
* Better cross-platform support

Contributing
------------

Found a bug or have suggestions? Contributions welcome!

* Report bugs: https://github.com/jikhanjung/Modan2/issues
* Submit fixes: https://github.com/jikhanjung/Modan2/pulls
* Improve docs: Edit this file and submit PR

See CONTRIBUTING.md for detailed contribution guidelines (when available).
