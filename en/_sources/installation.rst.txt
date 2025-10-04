Installation
============

This guide provides instructions for installing Modan2 on different operating systems.

System Requirements
-------------------

**Minimum Requirements**:

- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+, Fedora 34+)
- **Python**: 3.11 or newer (for source installation)
- **RAM**: 4 GB (8 GB recommended for large datasets)
- **Disk Space**: 500 MB for application + space for your data
- **Display**: 1280x720 resolution (1920x1080 recommended)

**For 3D Visualization**:

- OpenGL 3.3+ compatible graphics card
- Up-to-date graphics drivers

Installation Methods
---------------------

Windows Installation
~~~~~~~~~~~~~~~~~~~~

**Option 1: Using the Installer (Recommended)**

1. Download the latest installer from the `releases page <https://github.com/jikhanjung/Modan2/releases>`_
2. Run ``Modan2-Setup.exe``
3. Follow the installation wizard
4. Launch Modan2 from the Start Menu or desktop shortcut

.. note::
   Windows Defender may show a warning for unsigned executables. Click "More info" → "Run anyway" if you trust the source.

**Option 2: Portable Version**

1. Download ``Modan2-portable-windows.zip``
2. Extract to any folder
3. Run ``Modan2.exe``

No installation required - useful for USB drives or restricted environments.

**Option 3: From Source**

.. code-block:: bash

   # Install Python 3.11+ from python.org
   # Clone the repository
   git clone https://github.com/jikhanjung/Modan2.git
   cd Modan2

   # Install dependencies
   pip install -r requirements.txt

   # Run the application
   python Modan2.py

macOS Installation
~~~~~~~~~~~~~~~~~~

**Option 1: Application Bundle**

1. Download ``Modan2.dmg`` from the `releases page <https://github.com/jikhanjung/Modan2/releases>`_
2. Open the DMG file
3. Drag ``Modan2.app`` to your Applications folder
4. Launch from Applications

.. note::
   On first launch, right-click the app and select "Open" to bypass Gatekeeper warnings for unsigned applications.

**Option 2: From Source**

.. code-block:: bash

   # Install Python 3.11+ (via Homebrew)
   brew install python@3.11

   # Clone the repository
   git clone https://github.com/jikhanjung/Modan2.git
   cd Modan2

   # Install dependencies
   pip3 install -r requirements.txt

   # Run the application
   python3 Modan2.py

Linux Installation
~~~~~~~~~~~~~~~~~~

**Ubuntu/Debian**

.. code-block:: bash

   # Install system dependencies
   sudo apt-get update && sudo apt-get install -y \
     python3 python3-pip git \
     libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
     libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
     libxcb-xfixes0 libxcb-shape0 libxcb-cursor0 \
     qt5-qmake qtbase5-dev libqt5gui5 libqt5core5a libqt5widgets5 \
     libglut-dev libglut3.12 python3-opengl

   # Clone the repository
   git clone https://github.com/jikhanjung/Modan2.git
   cd Modan2

   # Install Python dependencies
   pip3 install -r requirements.txt

   # Run the application
   python3 Modan2.py

**Fedora/RHEL**

.. code-block:: bash

   # Install system dependencies
   sudo dnf install -y \
     python3 python3-pip git \
     qt5-qtbase qt5-qtbase-devel \
     freeglut freeglut-devel \
     libxcb libxcb-devel

   # Clone the repository
   git clone https://github.com/jikhanjung/Modan2.git
   cd Modan2

   # Install Python dependencies
   pip3 install -r requirements.txt

   # Run the application
   python3 Modan2.py

**Arch Linux**

.. code-block:: bash

   # Install system dependencies
   sudo pacman -S python python-pip git qt5-base freeglut

   # Clone the repository
   git clone https://github.com/jikhanjung/Modan2.git
   cd Modan2

   # Install Python dependencies
   pip install -r requirements.txt

   # Run the application
   python Modan2.py

WSL (Windows Subsystem for Linux)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Modan2 can run on WSL with X11 forwarding:

.. code-block:: bash

   # Install WSL2 with Ubuntu
   # In WSL terminal, install dependencies (same as Ubuntu above)

   # Install X server on Windows (e.g., VcXsrv, X410)
   # Set DISPLAY environment variable
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

   # Run Modan2
   python3 Modan2.py

.. note::
   If you encounter Qt platform plugin errors, use:

   .. code-block:: bash

      python3 fix_qt_import.py

Troubleshooting
---------------

Qt Platform Plugin Error (Linux/WSL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Error**: ``could not load the Qt platform plugin "xcb"``

**Solution**:

.. code-block:: bash

   # Option 1: Use the fix script
   python3 fix_qt_import.py

   # Option 2: Set environment variable
   export QT_QPA_PLATFORM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt5/plugins/platforms

   # Option 3: Reinstall Qt packages
   sudo apt-get install --reinstall libqt5gui5 libqt5core5a libqt5widgets5

OpenGL/GLUT Errors
~~~~~~~~~~~~~~~~~~

**Error**: ``ImportError: Unable to load OpenGL library``

**Solution**:

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt-get install -y libglut-dev libglut3.12 python3-opengl

   # Fedora
   sudo dnf install -y freeglut freeglut-devel

   # Reinstall PyOpenGL
   pip3 install --upgrade --force-reinstall PyOpenGL PyOpenGL_accelerate

Missing Python Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Error**: ``ModuleNotFoundError: No module named 'PyQt5'``

**Solution**:

.. code-block:: bash

   # Ensure you're using Python 3.11+
   python3 --version

   # Reinstall all dependencies
   pip3 install -r requirements.txt

   # Or install individually
   pip3 install PyQt5 numpy pandas scipy peewee trimesh opencv-python

Database Migration Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Error**: ``peewee.OperationalError: no such column``

**Solution**:

.. code-block:: bash

   # Run database migration
   python3 migrate.py

   # If migration fails, backup your database and start fresh
   cp modan.db modan.db.backup
   rm modan.db
   python3 Modan2.py

Performance Issues
~~~~~~~~~~~~~~~~~~

**Slow startup or rendering**:

- Update graphics drivers
- Reduce dataset size (split large datasets)
- Close other GPU-intensive applications
- Increase system RAM if working with large 3D models

**High memory usage**:

- Close unused datasets
- Limit the number of objects loaded simultaneously
- Use lower resolution images for preview

Verifying Installation
----------------------

After installation, verify that Modan2 works correctly:

1. **Launch the application**

   - Windows: Start Menu → Modan2
   - macOS: Applications → Modan2
   - Linux: ``python3 Modan2.py``

2. **Create a test dataset**

   - Click "New Dataset" (``Ctrl+N``)
   - Name it "Test"
   - Click OK

3. **Import example data**

   - Download example TPS file from `examples/ <https://github.com/jikhanjung/Modan2/tree/main/ExampleDataset>`_
   - Drag and drop into your dataset

4. **Run a simple analysis**

   - Select dataset → "Analyze Dataset"
   - Choose PCA
   - Verify that results display correctly

If all steps complete without errors, your installation is successful!

Updating Modan2
---------------

**Installed Version**:

Download the latest installer and run it - it will replace the old version.

**Source Installation**:

.. code-block:: bash

   cd Modan2
   git pull origin main
   pip3 install --upgrade -r requirements.txt

Getting Help
------------

If you encounter issues not covered here:

1. Check the `GitHub Issues page <https://github.com/jikhanjung/Modan2/issues>`_
2. Search for similar problems in closed issues
3. Create a new issue with:
   - Your OS and version
   - Python version (``python3 --version``)
   - Full error message
   - Steps to reproduce

Next Steps
----------

- Read the :doc:`user_guide` for a comprehensive tutorial
- Explore the :doc:`developer_guide` if you want to contribute
- Check the :doc:`changelog` for the latest updates
