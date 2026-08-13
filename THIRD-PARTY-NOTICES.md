# Licensing and third-party notices

**The source code is MIT. The installers and binaries we publish are GPL-3.0.**

Those two statements are both true and they are not in conflict, which is worth
a paragraph because the difference decides what you may do with each.

## Why the binaries are GPL-3.0

Modan2's own source, everything in this repository, is under the MIT License —
see [`LICENSE`](LICENSE). That does not change.

The released application is that source **combined with the libraries it needs
to run**, and one of them, **PyQt5**, is available only under the GPL-3.0 or a
commercial licence from Riverbank Computing. There is no permissive option for
it. A program that includes PyQt5 and is distributed as a whole must therefore
be distributed under the GPL-3.0.

MIT is compatible with the GPL, so the combination is allowed. What it means in
practice:

| What you have | Under which terms |
|---|---|
| This repository's source code | MIT |
| A `.zip`, `.dmg` or `.AppImage` from the releases page | GPL-3.0 |
| Your own program that copies Modan2 source into it | MIT (as long as it does not also link PyQt5) |

So a downloaded installer carries the GPL's obligations — most importantly, if
you redistribute it, you must pass on the same freedoms and make the
corresponding source available. Taking a function out of `MdStatistics.py` for
your own work does not; that file is MIT wherever you found it.

**Corresponding source** for the released binaries is this repository:
<https://github.com/jikhanjung/Modan2>, tagged with the version the binary
reports. The third-party components are the published releases of the packages
listed below, installed from PyPI.

## Full licence texts

- [`LICENSE`](LICENSE) — MIT, for Modan2's own source
- [`LICENSES/GPL-3.0.txt`](LICENSES/GPL-3.0.txt) — for the distributed binaries
- [`LICENSES/LGPL-3.0.txt`](LICENSES/LGPL-3.0.txt) — for the bundled Qt libraries

## What is bundled

Everything below ships inside the released binaries. Only the first entry is
copyleft; it is the one that sets the licence of the whole.

| Component | Licence |
|---|---|
| **PyQt5** | **GPL-3.0** *(or commercial — this build uses the GPL option)* |
| PyQt5-Qt5 (the Qt 5 libraries themselves) | LGPL-3.0 |
| PyQt5-sip | BSD-2-Clause |
| NumPy | BSD-3-Clause (with 0BSD, MIT, Zlib, CC0-1.0 parts) |
| SciPy | BSD-3-Clause |
| pandas | BSD-3-Clause |
| scikit-learn | BSD-3-Clause |
| statsmodels | BSD-3-Clause |
| Matplotlib | PSF-based (Matplotlib licence) |
| Pillow | MIT-CMU |
| OpenCV (`opencv-python-headless`) | Apache-2.0 |
| trimesh | MIT |
| PyOpenGL, PyOpenGL-accelerate | BSD-3-Clause |
| peewee, peewee-migrate | MIT |
| platformdirs | MIT |
| XlsxWriter | BSD-2-Clause |
| semver | BSD-3-Clause |

**Qt itself is LGPL-3.0**, which is a separate obligation from PyQt5's: if you
redistribute the binaries you must also let recipients replace the Qt libraries
with their own build. The Qt libraries are shipped as separate shared library
files inside the package rather than statically linked into the executable,
which is what makes that possible.

## If you need permissively-licensed binaries

Two routes, and one non-route:

- **PySide6** is the Qt Company's own binding under the LGPL-3.0. Replacing
  PyQt5 with it would leave the binaries LGPL rather than GPL — still with
  relinking obligations, but without the copyleft reaching Modan2's own code.
- **A commercial PyQt licence** from Riverbank removes the GPL requirement.
- **PyQt6 does not help.** It has the same GPL-or-commercial terms as PyQt5, so
  a port would change nothing about this page.

## Example datasets

The installer places example datasets in your data folder. These are research
data, not code, and carry their own terms from their original publications
rather than the licences above. Check the source publication before
redistributing them.
