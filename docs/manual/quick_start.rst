Quick Start
===========

Get from a fresh install to your first analysis in about ten minutes. For the
full picture, see the :doc:`user_guide`.

1. Install
----------

Download the package for your platform from the
`releases page <https://github.com/jikhanjung/Modan2/releases>`_ and install it —
see :doc:`installation` for the details and the exact file names.

Launch Modan2 from the Start Menu (Windows), Applications (macOS), or by running
the AppImage (Linux).

2. Create a dataset
-------------------

1. Click **"New Dataset"** (``Ctrl+N``)
2. Give it a **Dataset Name** and set the **Dimension** to 2D or 3D
3. Click **Save**

The dataset appears in the tree on the left. (Importing a landmark file creates
its own dataset, so for that you can go straight to the next step.)

3. Get your data in
-------------------

**If you already have landmark coordinates**:

1. Click **Import** (``Ctrl+I``), then **Open File**, and pick the file — the
   format is detected from the extension (TPS, NTS, X1Y1, Morphologika, or a
   JSON+ZIP package)
2. Check the **Dataset Name** — the import creates a new dataset — and click
   **Execute Import**

The new dataset appears in the tree with its objects. You can also drag a
landmark file onto the dataset tree, which opens the same dialog with the file
chosen.

**If you are starting from photographs**:

Select a 2D dataset and drag the image files onto the object table — each image
becomes an object named after its file. Digitize them in the next step.

4. Digitize landmarks
---------------------

1. **Double-click** the first object in the table to open it — **Landmark** mode
   is active by default
2. **Click on the image** to place landmarks; they are numbered in order
3. **Zoom** with the mouse wheel, **pan** by right-dragging empty space
4. Drag a landmark to move it, right-click it to delete it
5. Click **Save**, then use **Next** / **Previous** to work through the dataset

.. tip::
   To capture an outline rather than discrete points, switch to **Curve** mode and
   trace it — the trace snaps to image edges and is resampled into evenly-spaced
   semi-landmarks. See :ref:`semi-landmark-curves`.

If a landmark cannot be placed on a specimen, mark it missing rather than skipping
it, so every object keeps the same landmark count — see
:ref:`analysis-missing-landmarks`.

5. Add variables
----------------

Variables are what CVA and MANOVA group by. An analysis currently needs at least
one, even if you only want PCA.

1. Open the dataset dialog → **Variables** tab → **"Add Variable"**, and name it
   (e.g. ``Species``)
2. Open each object and fill in its value for that variable

6. Run the analysis
-------------------

One run computes **PCA, CVA, and MANOVA together** — there is no analysis type to
choose.

1. Select the dataset and click **Analyze** (``Ctrl+G``)
2. Set the **superimposition method** (Procrustes is the default) and the
   **CVA** and **MANOVA grouping variables**
3. Click **OK**

7. Explore the results
----------------------

Open the finished analysis in the **Data Exploration** dialog to get an
interactive scatter plot — PC1 vs PC2 by default, coloured by group, with other
axis combinations, a regression overlay, and a shape grid available.

To export, select the dataset and choose **Export** (``Ctrl+E``) for the data, or
use **Export Chart** in the Data Exploration dialog to save a plot.

Typical workflow
----------------

.. code-block:: text

   1. Create a dataset
        ↓
   2. Import data (landmark files, or images to digitize)
        ↓
   3. Digitize landmarks / trace curves
        ↓
   4. Add variables (for grouping)
        ↓
   5. Analyze  (superimposition → PCA + CVA + MANOVA)
        ↓
   6. Explore and export

Essential shortcuts
-------------------

==================  =========================
Shortcut            Action
==================  =========================
``Ctrl+N``          New dataset
``Ctrl+Shift+N``    New object
``Ctrl+Shift+O``    Edit object
``Ctrl+I``          Import
``Ctrl+E``          Export
``Ctrl+G``          Analyze
``Ctrl+S``          Save changes
==================  =========================

Quick fixes
-----------

**Imported objects do not appear**
   Click the dataset in the tree to refresh it.

**Clicking does not place a landmark**
   Check that you opened the object dialog and that the **Landmark** mode button
   is selected — not **Curve** or **Calibration**.

**Analysis fails**
   The dataset needs at least 5 digitized objects and at least one variable, and
   every object needs the same number of landmarks; mark gaps as missing rather
   than leaving objects short. See :doc:`troubleshooting`.

Next steps
----------

- :doc:`user_guide` — the comprehensive guide
- :doc:`advanced_features` — power-user tips and integration with R/Python
- :doc:`faq` and :doc:`troubleshooting`
