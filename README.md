# Modan2 - Geometric Morphometrics Software

[![Build](https://github.com/jikhanjung/Modan2/actions/workflows/build.yml/badge.svg)](https://github.com/jikhanjung/Modan2/actions/workflows/build.yml)
[![Tests](https://github.com/jikhanjung/Modan2/actions/workflows/test.yml/badge.svg)](https://github.com/jikhanjung/Modan2/actions/workflows/test.yml)
[![Release Status](https://github.com/jikhanjung/Modan2/actions/workflows/release.yml/badge.svg)](https://github.com/jikhanjung/Modan2/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

*Read this in other languages: [English](README.md), [한국어](README.ko.md)*

Modan2 is a user-friendly desktop application that empowers researchers to explore and understand shape variations through geometric morphometrics. It streamlines the entire workflow from data acquisition (2D/3D) to statistical analysis and visualization.

## 📚 Documentation

**[View Documentation](https://jikhanjung.github.io/Modan2/en/)** | **[한국어 문서](https://jikhanjung.github.io/Modan2/ko/)**

**New User? Start Here** 👇
- **[User Guide](https://jikhanjung.github.io/Modan2/en/user_guide.html)** - Comprehensive guide with all features
- **[Installation Guide](https://jikhanjung.github.io/Modan2/en/installation.html)** - Getting Modan2 running
- **[FAQ](https://jikhanjung.github.io/Modan2/en/faq.html)** and [Troubleshooting](https://jikhanjung.github.io/Modan2/en/troubleshooting.html)

**Additional Documentation**:
- [Advanced Features](https://jikhanjung.github.io/Modan2/en/advanced_features.html)
- [Developer Guide](https://jikhanjung.github.io/Modan2/en/developer_guide.html)
- [Changelog](https://jikhanjung.github.io/Modan2/en/changelog.html)
- Repository-only notes (architecture, performance, build and release process) live in [`docs/`](docs/README.md)

## Download

Get the latest version from our [releases page](https://github.com/jikhanjung/Modan2/releases).

## Key Features

- **Hierarchical Data Management:** Organize data into nested datasets with a clear structure.
- **2D & 3D Visualization:** Integrated viewers for 2D images and 3D models with landmark plotting.
- **Statistical Analysis:** Perform Principal Component Analysis (PCA), Canonical Variate Analysis (CVA), and MANOVA.
- **Missing Landmarks:** Record landmarks that could not be digitized, see them estimated from the
  aligned mean shape while you work, and include those specimens in analysis.
- **Data Import/Export:** Supports various file types and drag-and-drop for easy data handling.
- **Persistent Storage:** All data and analyses are saved in a local database, managed by Peewee ORM.

## Technology Stack

- **Language:** Python 3
- **GUI Framework:** PyQt5
- **Core Libraries:**
    - **Database ORM:** Peewee
    - **Numerical/Scientific:** NumPy, SciPy, Pandas, Statsmodels
    - **Plotting:** Matplotlib
    - **3D Graphics & Image Processing:** PyOpenGL, Trimesh, Pillow, OpenCV

## Installation and Usage (from Source)

Follow these instructions to run Modan2 from the source code.

### Prerequisites

- Python 3.12 or newer (CI runs the test suite on 3.12)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/jikhanjung/Modan2.git
cd Modan2
```

### 2. Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

**For Linux users:** You also need to install system-level dependencies for Qt and other libraries.

```bash
sudo apt-get update && sudo apt-get install -y \
  libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-xfixes0 libxcb-shape0 libxcb-cursor0 \
  qt5-qmake qtbase5-dev libqt5gui5 libqt5core5a libqt5widgets5 \
  libglut-dev python3-opengl
```

The last line provides GLUT, which the 3D viewer needs; without it 3D models
fail to render.

### 3. Run the Application

Once the dependencies are installed, you can start the application:

```bash
python main.py
```

## Building from Source

This project uses `PyInstaller` to create standalone executables. A helper script, `build.py`, automates this process.

To create a distributable package for your operating system, run:

```bash
python build.py
```

The build artifacts will be located in the `dist/` directory.

## Running Tests

The project is tested using `pytest`. To run the test suite, first install the development dependencies:

```bash
pip install -r config/requirements-dev.txt
```

Then, run pytest from the project root:

```bash
pytest
```

## License

**Source code: MIT.** See the [LICENSE](LICENSE) file.

**The builds on the releases page: GPL-3.0.** They include PyQt5, which is
available only under the GPL-3.0 or a commercial licence, so the binary as a
whole carries the GPL's terms. Copying Modan2 source into your own project is
still MIT. See [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
