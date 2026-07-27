Installation
============

This guide provides instructions for installing Modan2 on different operating systems.

System Requirements
-------------------

**Minimum Requirements**:

- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+, Fedora 34+)
- **RAM**: 4 GB (8 GB recommended for large datasets)
- **Disk Space**: 500 MB for application + space for your data
- **Display**: 1280x720 resolution (1920x1080 recommended)

**For 3D Visualization**:

- OpenGL 3.3+ compatible graphics card
- Up-to-date graphics drivers

Installation Methods
---------------------

Modan2 is distributed as a prebuilt package for each platform on the
`releases page <https://github.com/jikhanjung/Modan2/releases>`_. Every file
carries the version and build number, so the exact names change from release to
release — ``<version>`` and ``<build>`` below stand for what you see on the
release you are downloading (for example ``v0.1.12`` and ``build672``).

Each release also publishes ``SHA256SUMS.txt`` if you want to verify a download.

.. warning::
   **Only the Windows build is well tested.** The macOS and Linux packages are
   produced by the same automated build, but they have not been through the same
   testing, so you may hit problems that do not occur on Windows. If one of them
   fails for you, please report it on the
   `issues page <https://github.com/jikhanjung/Modan2/issues>`_.

Windows
~~~~~~~

1. Download ``Modan2-Windows-Installer-v<version>-build<build>.zip`` from the
   releases page.
2. Extract the ZIP. It contains a single installer,
   ``Modan2_v<version>_build<build>_Installer.exe``.
3. Run the installer and follow the wizard.
4. Launch Modan2 from the Start Menu or the desktop shortcut.

.. note::
   Windows Defender may warn about an unsigned executable. Click "More info" →
   "Run anyway" if you trust the source.

.. note::
   A portable (no-install) Windows build is **not** currently published — the
   installer is the only Windows package.

macOS
~~~~~

1. Download ``Modan2-macOS-Installer-v<version>-build<build>.dmg`` from the
   releases page.
2. Open the DMG.
3. Drag ``Modan2.app`` into your Applications folder.
4. Launch it from Applications.

.. note::
   On first launch, right-click the app and choose "Open" to get past the
   Gatekeeper warning shown for unsigned applications.

Linux
~~~~~

Linux is distributed as an AppImage, which runs without installation.

.. code-block:: bash

   # Download Modan2-Linux-v<version>-build<build>.AppImage from the releases page
   chmod +x Modan2-Linux-v<version>-build<build>.AppImage
   ./Modan2-Linux-v<version>-build<build>.AppImage

.. note::
   If the AppImage does not start, your distribution may be missing FUSE. Either
   install it (``sudo apt-get install libfuse2`` on Ubuntu/Debian) or run the
   AppImage with ``--appimage-extract-and-run``.

Troubleshooting
---------------

OpenGL / 3D Rendering Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom**: the 3D viewer is blank, or the application reports an OpenGL error
on startup.

- Update your graphics drivers.
- Check that your GPU supports OpenGL 3.3 or newer.
- On Linux, a headless or remote session (SSH, VNC, some WSL setups) may not
  expose a usable OpenGL context; run Modan2 on a normal desktop session.

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
   - Linux: run the AppImage

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

Download the package for the new release and install it the same way as before:

- **Windows**: run the new installer; it replaces the old version.
- **macOS**: open the new DMG and replace ``Modan2.app`` in Applications.
- **Linux**: download the new AppImage and run it instead of the old one.

Your database and data files are kept separately from the application, so
updating does not touch them.

Getting Help
------------

If you encounter issues not covered here:

1. Check the `GitHub Issues page <https://github.com/jikhanjung/Modan2/issues>`_
2. Search for similar problems in closed issues
3. Create a new issue with:
   - Your OS and version
   - The Modan2 version and build number you downloaded
   - Full error message
   - Steps to reproduce

Next Steps
----------

- Read the :doc:`user_guide` for a comprehensive tutorial
- Explore the :doc:`developer_guide` if you want to contribute
- Check the :doc:`changelog` for the latest updates
