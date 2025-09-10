# Modan2 Project Analysis for AI Collaboration

This document provides a comprehensive overview of the Modan2 project for AI agents responsible for analysis, planning, and implementation.

## 1. Project Overview

- **Project Name:** Modan2
- **Purpose:** A desktop application for Geometric Morphometrics, designed for researchers. It facilitates the entire workflow from data acquisition (2D/3D) to statistical analysis and visualization.
- **Status:** A mature, feature-rich application with a stable architecture. Core functionalities are well-implemented.

## 2. Technology Stack

- **Language:** Python 3
- **GUI Framework:** PyQt5
- **Database ORM:** Peewee (manages a local database, likely SQLite)
- **Core Libraries:**
    - **Numerical/Scientific:** `numpy`, `scipy`, `pandas`, `statsmodels`
    - **3D Graphics:** `PyOpenGL`, `trimesh`
    - **Image Processing:** `Pillow`, `opencv-python`
    - **Excel Export:** `xlsxwriter`
- **Database Migrations:** `peewee-migrate`
- **Packaging:** `pyinstaller`

## 3. Project Structure

```
/
├── Modan2.py             # Main application entry point, contains ModanMainWindow
├── MdModel.py              # Peewee database models (MdDataset, MdObject, etc.)
├── ModanDialogs.py         # Custom dialog windows (Analysis, Preferences, etc.)
├── ModanComponents.py      # Custom Qt widgets (e.g., MdTableView)
├── MdStatistics.py         # Core statistical analysis functions (PCA, CVA, MANOVA)
├── MdUtils.py              # Utility functions
├── requirements.txt        # Python dependencies
├── requirements_linux.txt  # Linux system dependencies
├── migrations/             # Database migration scripts
├── translations/           # Language files (en, ko) for i18n
├── icons/                  # Application icons
├── test_script/            # Folder with various test scripts
└── setup.py / build.py     # Build and packaging scripts
```

## 4. Core Functionality

### Data Management
- **Hierarchical Datasets:** Data is organized into datasets that can be nested.
- **Database Backend:** Peewee ORM manages all data (datasets, objects, landmarks, analyses) in a local database.
- **Migrations:** The database schema is version-controlled using the `migrations/` directory.
- **Data Import/Export:** Supports importing various file types (images, 3D models) and exporting datasets. Drag-and-drop is supported for importing files and moving objects between datasets.

### Analysis
- **Superimposition:** Performs Procrustes superimposition to align shapes.
- **Statistical Tests:**
    - Principal Component Analysis (PCA)
    - Canonical Variate Analysis (CVA)
    - Multivariate Analysis of Variance (MANOVA)
- **Analysis Results:** Analysis configurations and results are saved to the database and can be reviewed later.

### Visualization
- **2D/3D Viewers:** Separate, integrated viewers for 2D images and 3D models.
- **Landmark Plotting:** Visualizes landmarks on the objects.
- **Data Exploration:** Provides dialogs to explore analysis results with scatterplots and other charts.

## 5. Development & Deployment

### Running the Application
1.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **(Linux Only) Install System Dependencies:** This is critical for the Qt platform plugin.
    ```bash
    sudo apt-get update && sudo apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xfixes0 libxcb-shape0 libxcb-cursor0 qt5-qmake qtbase5-dev libqt5gui5 libqt5core5a libqt5widgets5 python3-pyqt5
    ```
3.  **Run:**
    ```bash
    python Modan2.py
    ```

### Building Executables
- The `pyinstaller` commands are documented in the comments at the end of `Modan2.py`.
- **Example for Linux/macOS:**
  ```bash
  pyinstaller --onedir --noconsole --add-data "icons/*.png:icons" --add-data "translations/*.qm:translations" --add-data "migrations/*:migrations" --icon="icons/Modan2_2.png" --noconfirm Modan2.py
  ```

### Internationalization (i18n)
- **Updating Translation Files (`.ts`):**
  ```bash
  pylupdate5 Modan2.py ModanComponents.py ModanDialogs.py -ts translations/Modan2_ko.ts
  ```
- **Compiling Translations (`.qm`):** Use the `linguist` tool from Qt.

## 6. Code Intelligence & Analysis

The project includes a code indexing system that provides valuable insights into the codebase, identifies refactoring opportunities, and offers powerful search capabilities. The output is stored in the `.index/` directory.

### Building the Index
To generate or update the code index:
```bash
python tools/build_index.py
```

### Searching the Index
A command-line tool, `tools/search_index.py`, allows for querying the generated index. This is the primary tool for an AI agent to explore the codebase.

**Example Usage:**
```bash
# Search for symbols (classes, functions, etc.)
python tools/search_index.py --symbol "DataExploration"

# Find all usages of a Qt signal like "clicked"
python tools/search_index.py --qt "clicked"

# Find where database models are used
python tools/search_index.py --model "MdAnalysis"

# Get statistics for a specific file
python tools/search_index.py --file "ModanDialogs.py"

# Show overall project statistics
python tools/search_index.py --stats
```

---
This document should serve as the primary reference for any AI agent working on this project.
