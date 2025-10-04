# Modan2 Sphinx Documentation Plan

**Date**: 2025-10-04
**Status**: 📋 Planning
**Reference**: CTHarvester Documentation (https://jikhanjung.github.io/CTHarvester/en/index.html)

## Overview

Create comprehensive Sphinx-based documentation for Modan2, following the structure and style of CTHarvester documentation. The documentation will be bilingual (English/Korean) and cover installation, user guide, developer guide, and API reference.

## CTHarvester Documentation Analysis

### Actual Structure (Examined from /mnt/d/projects/CTHarvester/docs/)

**File Organization**:
```
docs/
├── conf.py                    # Single Sphinx config for all languages
├── Makefile                   # Build commands
├── index.rst                  # Main index
├── installation.rst           # Installation guide
├── user_guide.rst             # Complete user guide (single file)
├── developer_guide.rst        # Complete developer guide (single file)
├── changelog.rst              # Version history
├── configuration.md           # Configuration reference (Markdown!)
├── requirements.txt           # Sphinx dependencies
├── _templates/
│   └── layout.html           # Language switcher template
└── locale/
    └── ko/
        └── LC_MESSAGES/      # .po/.mo translation files
            ├── index.po
            ├── user_guide.po
            ├── developer_guide.po
            └── changelog.po
```

### Key Insights from CTHarvester

1. **Simpler Structure**: Uses single-file approach (one file per major section) instead of deeply nested directories
2. **Gettext-based i18n**: Uses Sphinx's gettext/locale system with .po files, not separate language directories
3. **Custom Language Switcher**: Template override in `_templates/layout.html` with JavaScript to preserve page path
4. **Mixed Formats**: Uses both .rst and .md files (via myst-parser extension, though not in extensions list)
5. **Single conf.py**: Language switching done via `language = "en"` setting and locale_dirs

### Language Switching Implementation

**In layout.html**:
- Fixed position language switcher (top-right corner)
- JavaScript preserves current page when switching: `/en/user_guide.html` → `/ko/user_guide.html`
- Styling with CSS for professional appearance

**Translation Workflow**:
1. Write English .rst files
2. Run `make gettext` to extract translatable strings → .pot files
3. Create .po files from .pot templates
4. Translate .po files to Korean
5. Build with `make html -D language=ko`

### Key Features
- **Multilingual Support**: Gettext-based with .po files
- **Clean Navigation**: Read the Docs theme with customized layout
- **Search Functionality**: Built-in Sphinx search
- **Code Examples**: Syntax-highlighted code snippets
- **Progressive Learning**: Beginner → Advanced content flow

## Proposed Modan2 Documentation Structure

### Two Approaches Considered

#### Approach 1: CTHarvester Style (Simpler, Recommended)
```
docs/
├── conf.py                          # Single Sphinx config
├── Makefile                         # Build commands
├── make.bat                         # Windows build commands
├── requirements.txt                 # sphinx, sphinx-rtd-theme
├── index.rst                        # Main landing page
├── installation.rst                 # All installation content
├── user_guide.rst                   # All user guide content
├── developer_guide.rst              # All developer content
├── api_reference.rst                # API overview
├── changelog.rst                    # From CHANGELOG.md
├── _templates/
│   └── layout.html                  # Language switcher
├── _static/
│   ├── screenshots/                 # UI screenshots
│   ├── diagrams/                    # Architecture diagrams
│   └── custom.css                   # Custom styling
└── locale/
    └── ko/
        └── LC_MESSAGES/
            ├── index.po
            ├── installation.po
            ├── user_guide.po
            ├── developer_guide.po
            └── changelog.po
```

**Advantages**:
- Simpler to maintain (fewer files)
- Faster to write initially
- Easier translation (fewer .po files)
- Matches proven CTHarvester approach
- Good for medium-sized projects

**Disadvantages**:
- Large single files (can be harder to navigate while editing)
- Less modular (can't easily reorder sections)

#### Approach 2: Nested Structure (More Scalable)
```
docs/
├── conf.py
├── Makefile
├── index.rst
├── installation/
│   ├── index.rst
│   ├── windows.rst
│   └── linux.rst
├── user_guide/
│   ├── index.rst
│   ├── quickstart.rst
│   ├── datasets.rst
│   ├── analysis.rst
│   └── visualization.rst
├── developer_guide/
│   ├── index.rst
│   ├── architecture.rst
│   ├── contributing.rst
│   └── api_reference.rst
├── changelog.rst
├── _templates/
│   └── layout.html
├── _static/
│   └── screenshots/
└── locale/
    └── ko/
        └── LC_MESSAGES/
            └── *.po files (one per .rst)
```

**Advantages**:
- More modular and easier to navigate
- Can independently update sections
- Better for large-scale documentation
- Easier to assign sections to different contributors

**Disadvantages**:
- More files to maintain
- More .po files to translate
- Slightly more complex build process

### Recommended Approach

**Use Approach 1 (CTHarvester Style)** for Modan2 because:
1. Project documentation scope is similar to CTHarvester
2. Proven approach that works well
3. Easier to get started and maintain
4. Can always split files later if they become too large

The plan below follows **Approach 1**.

## Content Plan

### 1. Installation Guide

#### requirements.rst
- System requirements (Python version, OS)
- Hardware recommendations
- Disk space requirements

#### windows.rst
- Download from GitHub releases
- Installation steps (installer vs portable)
- Installing from source (pip, dependencies)
- Common Windows-specific issues

#### macos.rst
- Download options
- Installation via .app bundle
- Installing from source (Homebrew, pip)
- macOS-specific considerations

#### linux.rst
- Distribution-specific instructions (Ubuntu, Fedora, Arch)
- System package installation (Qt, OpenGL)
- pip installation
- WSL setup (specific section)

#### troubleshooting.rst
- Qt platform plugin errors
- OpenGL/GLUT issues
- Database migration issues
- Import errors

### 2. User Guide

#### quickstart.rst
- First launch
- Creating your first dataset
- Importing objects (2D images, 3D models)
- Placing landmarks
- Running basic PCA analysis
- Viewing results

#### interface.rst
- Main window layout
- Dataset tree view
- Object table view
- Toolbar and menus
- Status bar

#### datasets/creating.rst
- Dataset types (2D vs 3D)
- Naming conventions
- Hierarchical organization (parent/child datasets)
- Setting variables (categorical, continuous)

#### datasets/importing.rst
- Supported file formats
  - 2D: TPS, NTS, CSV, images (JPG, PNG)
  - 3D: OBJ, PLY, STL
- Drag-and-drop import
- Bulk import options
- Parsing landmark files

#### datasets/exporting.rst
- Export formats (TPS, CSV, JSON)
- Exporting with analysis results
- Export options and filters

#### objects/2d_objects.rst
- Adding 2D images
- Supported image formats
- EXIF data handling
- Landmark placement workflow
- Editing landmarks
- Image transformations (zoom, pan)

#### objects/3d_objects.rst
- Adding 3D models
- Supported 3D formats
- 3D viewer controls (rotate, zoom)
- Surface vs wireframe rendering
- Landmark placement in 3D space

#### objects/landmarks.rst
- Landmark definition and terminology
- Placing landmarks (mouse, keyboard)
- Editing landmark coordinates
- Missing landmarks (marking as missing)
- Landmark naming and numbering

#### analysis/procrustes.rst
- What is Procrustes superimposition?
- When to use it
- Handling missing landmarks (imputation)
- Interpreting results
- Reference shape selection

#### analysis/pca.rst
- Principal Component Analysis overview
- Running PCA
- PC scores interpretation
- Scree plot
- Shape variation visualization (wireframes)
- Exporting PC scores

#### analysis/cva.rst
- Canonical Variate Analysis overview
- Group definition
- Running CVA
- CV scores and classification
- Confusion matrix
- Discriminant function plots

#### analysis/manova.rst
- MANOVA overview
- Setting up groups
- Running MANOVA
- Interpreting results (Wilks' Lambda, F-statistics)

#### analysis/missing_landmarks.rst
- Missing data handling philosophy
- Marking landmarks as missing
- Visual representation (hollow circles, "3?")
- Estimation methods
- Limitations and best practices

#### visualization/2d_viewer.rst
- 2D viewer controls
- Landmark display options (size, color, index)
- Polygon and baseline display
- Wireframe overlay
- Exporting images

#### visualization/3d_viewer.rst
- 3D viewer controls
- Camera manipulation
- Lighting and materials
- Landmark spheres
- Surface rendering options
- Wireframe/surface toggle

#### visualization/plots.rst
- Scatter plots (PC1 vs PC2, CV1 vs CV2)
- Box plots and histograms
- Group coloring
- Customizing plots (matplotlib integration)
- Exporting plots (PNG, SVG, PDF)

#### preferences.rst
- General settings
- Display preferences
- Default colors and sizes
- File paths and directories
- Language selection

#### keyboard_shortcuts.rst
- Global shortcuts
  - Ctrl+N: New Dataset
  - Ctrl+S: Save
  - Ctrl+O: Open
- Context-specific shortcuts
- Customization options

### 3. Developer Guide

#### architecture/overview.rst
- High-level architecture diagram
- Component responsibilities
  - Modan2.py: Main window and application logic
  - MdModel.py: Database models (Peewee ORM)
  - MdStatistics.py: Statistical computation
  - ModanDialogs.py: Dialog windows
  - ModanComponents.py: Custom UI widgets
  - ModanController.py: MVC controller
- Data flow diagrams

#### architecture/database.rst
- Peewee ORM introduction
- Database schema
  - MdDataset: Dataset metadata
  - MdObject: Object and landmark data
  - MdImage: Image metadata
  - MdThreeDModel: 3D model metadata
  - MdAnalysis: Analysis results
- Relationships and foreign keys
- Migration system

#### architecture/mvc_pattern.rst
- Model-View-Controller explanation
- How Modan2 implements MVC
- ModanController role
- Signal/slot connections
- Event flow

#### architecture/file_formats.rst
- TPS format specification
- NTS format specification
- CSV format expectations
- OBJ/PLY/STL parsing
- Custom JSON format (if any)

#### setup/dev_environment.rst
- Cloning the repository
- Creating virtual environment
- Installing dependencies
- IDE setup (VSCode, PyCharm)
- Recommended extensions

#### setup/dependencies.rst
- Python version requirements
- Core dependencies (PyQt5, NumPy, Pandas)
- Development dependencies (pytest, ruff)
- Managing requirements.txt

#### setup/testing.rst
- pytest configuration
- Running tests (`pytest`)
- Test coverage (`pytest --cov`)
- Writing new tests
- Test fixtures
- Mocking database interactions

#### contributing/code_style.rst
- PEP 8 compliance
- Naming conventions
- Docstring format
- Type hints (if applicable)
- Linting with ruff

#### contributing/git_workflow.rst
- Branching strategy (main, feature branches)
- Commit message format
- Creating pull requests
- Code review process

#### building/pyinstaller.rst
- build.py script overview
- PyInstaller configuration
- Platform-specific builds
- Troubleshooting build issues

#### building/distribution.rst
- Creating GitHub releases
- Version numbering (semantic versioning)
- Release notes
- Windows installer (InnoSetup)
- Code signing (future)

#### api_reference/*.rst
- Auto-generated from docstrings using sphinx-apidoc
- Class and function documentation
- Usage examples
- Parameter descriptions

### 4. Changelog

#### changelog.rst
- Auto-generated from CHANGELOG.md
- Version history
- Breaking changes
- New features
- Bug fixes

## Sphinx Configuration

### conf.py (English)

```python
# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------
project = 'Modan2'
copyright = '2025, Modan2 Contributors'
author = 'Modan2 Contributors'
release = '0.1.5'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',       # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',      # Support for NumPy/Google style docstrings
    'sphinx.ext.viewcode',      # Add links to source code
    'sphinx.ext.intersphinx',   # Link to other projects' documentation
    'sphinx.ext.todo',          # Support for todo items
    'sphinx_rtd_theme',         # Read the Docs theme
    'sphinx.ext.autosectionlabel',  # Auto-label sections
]

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Custom CSS
html_css_files = [
    'custom.css',
]

# -- Extension configuration -------------------------------------------------
# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
}

# Napoleon settings (for docstring parsing)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

# Todo extension
todo_include_todos = True
```

### index.rst (English)

```rst
Welcome to Modan2 Documentation
================================

**Modan2** is a user-friendly desktop application for geometric morphometrics,
enabling researchers to explore and understand shape variations through
landmark-based analysis.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation/index

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/quickstart
   user_guide/interface
   user_guide/datasets/index
   user_guide/objects/index
   user_guide/analysis/index
   user_guide/visualization/index
   user_guide/preferences
   user_guide/keyboard_shortcuts

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   developer_guide/architecture/index
   developer_guide/setup/index
   developer_guide/contributing/index
   developer_guide/building/index
   developer_guide/api_reference/index

.. toctree::
   :maxdepth: 1
   :caption: Additional Information

   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Language
========

* `English <../en/index.html>`_
* `한국어 <../ko/index.html>`_
```

## Multilingual Support Strategy

### Language Switching
- Use relative paths: `../en/index.html` and `../ko/index.html`
- Add language selector in theme customization
- Maintain parallel directory structure

### Translation Workflow
1. Write English documentation first
2. Create Korean version with same file structure
3. Use consistent terminology across languages
4. Keep both versions synchronized during updates

### Shared Resources
- Screenshots and diagrams can be shared (language-agnostic)
- Code examples are language-independent
- Place shared resources in common `_static/` directory

## Build Process

### Local Development

```bash
# Install Sphinx and dependencies
pip install -r docs/requirements.txt

# Build English docs (default)
cd docs
make html
# Output: docs/_build/html/

# Build Korean docs
cd docs
make html SPHINXOPTS="-D language=ko"
# Output: docs/_build/html/ (with Korean content)

# Extract translatable strings (create .pot files)
make gettext
# Output: docs/_build/gettext/*.pot

# Update Korean .po files from .pot templates
sphinx-intl update -p _build/gettext -l ko

# Serve with auto-rebuild (for development)
sphinx-autobuild . _build/html
# Open http://127.0.0.1:8000 in browser

# Clean build artifacts
make clean
```

### Translation Workflow (English → Korean)

```bash
# 1. Write or update English .rst files
# ... edit index.rst, user_guide.rst, etc. ...

# 2. Extract translatable strings
cd docs
make gettext

# 3. Update .po files
sphinx-intl update -p _build/gettext -l ko

# 4. Translate .po files
# Edit locale/ko/LC_MESSAGES/*.po files
# Use text editor or Poedit (https://poedit.net/)

# 5. Build Korean version
make html SPHINXOPTS="-D language=ko"

# 6. Build English version
make html
```

### GitHub Pages Deployment

#### Option 1: Manual Build and Push
1. Build documentation locally
2. Commit `docs/build/` to `gh-pages` branch
3. Configure GitHub Pages to serve from `gh-pages` branch

#### Option 2: GitHub Actions (Recommended)
Create `.github/workflows/docs.yml`:

```yaml
name: Build Documentation

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install sphinx sphinx-rtd-theme

      - name: Build English docs
        run: |
          cd docs/source/en
          make html

      - name: Build Korean docs
        run: |
          cd docs/source/ko
          make html

      - name: Deploy to GitHub Pages
        if: github.event_name == 'push'
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/build
```

## Implementation Plan

### Phase 1: Setup and Infrastructure (Week 1)
- [ ] Create `docs/` directory structure
- [ ] Set up Sphinx configuration for English and Korean
- [ ] Create Makefile and make.bat
- [ ] Set up GitHub Actions for documentation build
- [ ] Create basic index.rst files for both languages
- [ ] Test local builds

### Phase 2: Installation Guide (Week 1-2)
- [ ] Write installation/requirements.rst
- [ ] Write installation/windows.rst
- [ ] Write installation/macos.rst
- [ ] Write installation/linux.rst
- [ ] Write installation/troubleshooting.rst
- [ ] Add screenshots for installation steps

### Phase 3: User Guide - Basics (Week 2-3)
- [ ] Write user_guide/quickstart.rst
- [ ] Write user_guide/interface.rst
- [ ] Write user_guide/datasets/*.rst
- [ ] Write user_guide/objects/*.rst
- [ ] Capture UI screenshots
- [ ] Create workflow diagrams

### Phase 4: User Guide - Analysis (Week 3-4)
- [ ] Write user_guide/analysis/procrustes.rst
- [ ] Write user_guide/analysis/pca.rst
- [ ] Write user_guide/analysis/cva.rst
- [ ] Write user_guide/analysis/manova.rst
- [ ] Write user_guide/analysis/missing_landmarks.rst
- [ ] Add example datasets and results

### Phase 5: User Guide - Visualization (Week 4)
- [ ] Write user_guide/visualization/*.rst
- [ ] Write user_guide/preferences.rst
- [ ] Write user_guide/keyboard_shortcuts.rst
- [ ] Complete user guide screenshots

### Phase 6: Developer Guide (Week 5-6)
- [ ] Write developer_guide/architecture/*.rst
- [ ] Create architecture diagrams
- [ ] Write developer_guide/setup/*.rst
- [ ] Write developer_guide/contributing/*.rst
- [ ] Write developer_guide/building/*.rst

### Phase 7: API Reference (Week 6-7)
- [ ] Add docstrings to all major classes and functions
- [ ] Set up sphinx-apidoc
- [ ] Generate API reference pages
- [ ] Write usage examples for key APIs

### Phase 8: Korean Translation (Week 7-8)
- [ ] Translate installation guide to Korean
- [ ] Translate user guide to Korean
- [ ] Translate developer guide to Korean
- [ ] Review and proofread Korean translations

### Phase 9: Polish and Deploy (Week 8)
- [ ] Add custom CSS styling
- [ ] Optimize images and diagrams
- [ ] Test all links and cross-references
- [ ] Deploy to GitHub Pages
- [ ] Update README.md with documentation link

## Content Guidelines

### Writing Style
- **User Guide**: Casual, tutorial-style, task-oriented
- **Developer Guide**: Technical, precise, architecture-focused
- **API Reference**: Formal, complete, parameter-focused

### Screenshots
- Use consistent window size and theme
- Highlight important UI elements with arrows or boxes
- Include captions with figure numbers
- Save as PNG with good compression

### Code Examples
- Always use syntax highlighting (.. code-block:: python)
- Include complete, runnable examples where possible
- Add comments to explain non-obvious code
- Show expected output

### Cross-References
- Use Sphinx cross-reference syntax (`:ref:`, `:doc:`)
- Link to related sections generously
- Create a glossary for technical terms

## Success Metrics

### Documentation Quality
- [ ] All major features documented
- [ ] Step-by-step tutorials for common workflows
- [ ] Troubleshooting section covers 80%+ of user issues
- [ ] API reference covers all public classes/functions

### Accessibility
- [ ] Search functionality works correctly
- [ ] Mobile-responsive design
- [ ] Clear navigation structure
- [ ] Consistent terminology

### Maintenance
- [ ] Documentation updated with each release
- [ ] Automated build process in place
- [ ] Contributors can easily add/update docs
- [ ] Translation workflow established

## Required Dependencies

Create `docs/requirements.txt` (based on CTHarvester):

```
# Sphinx documentation requirements
sphinx>=7.0.0
sphinx_rtd_theme>=1.3.0
sphinx-intl>=2.0.0
sphinx-autobuild>=2021.3.14  # For development
```

**Installation**:
```bash
pip install -r docs/requirements.txt
```

## Next Steps

1. **Create directory structure**: Set up `docs/` with initial files
2. **Configure Sphinx**: Create conf.py for both languages
3. **Set up build system**: Makefile, GitHub Actions
4. **Write quickstart guide**: First content to test the system
5. **Capture screenshots**: Gather visual assets for documentation
6. **Iterate and expand**: Follow the implementation plan phases

## References

- CTHarvester Documentation: https://jikhanjung.github.io/CTHarvester/en/index.html
- Sphinx Documentation: https://www.sphinx-doc.org/
- Read the Docs Theme: https://sphinx-rtd-theme.readthedocs.io/
- reStructuredText Primer: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html

## Estimated Effort

- **Total Time**: 8 weeks (part-time)
- **Priority**: Medium (improves user adoption and reduces support burden)
- **Dependencies**: None (can start immediately)
- **Maintainability**: High (Sphinx is industry standard, easy to update)
