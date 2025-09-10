# Modan2 Code Index Report

**Generated**: 2025-09-10  
**Index Version**: 1.0

## Project Statistics

| Metric | Count |
|--------|-------|
| Total Files | 27 |
| Total Lines | 24,145 |
| Classes | 63 |
| Functions | 960 |
| Dialogs | 11 |
| Database Models | 5 |
| Qt Signal Definitions | 26 |
| Qt Connections | 257 |
| Symbol Cards Generated | 23 |

## Index Structure

```
.index/
├── symbols/
│   ├── symbols.json         # All symbols (classes, functions, methods)
│   └── file_stats.json      # File statistics
├── graphs/
│   ├── qt_signals.json      # Qt signal/slot connections
│   ├── db_models.json       # Database model definitions
│   └── imports.json         # Import dependencies
├── cards/
│   ├── dialogs/             # Dialog symbol cards
│   ├── models/              # Database model cards
│   ├── classes/             # Class symbol cards
│   └── special/             # Special analysis cards
└── index_summary.json       # Overall index summary
```

## Key Components Indexed

### 1. Dialog Classes (11)
- `ProgressDialog` - Generic progress indicator
- `NewAnalysisDialog` - Analysis configuration with progress bar
- `DataExplorationDialog` - Data visualization and exploration
- `AnalysisResultDialog` - Analysis results display
- `DatasetDialog` - Dataset management
- `ObjectDialog` - Object editing
- `CalibrationDialog` - Calibration settings
- `ExportDatasetDialog` - Export functionality
- `ImportDatasetDialog` - Import functionality
- `PreferencesDialog` - Application preferences
- `DatasetAnalysisDialog` - Dataset analysis

### 2. Database Models (5)
- `MdDataset` - Dataset storage
- `MdObject` - Object data
- `MdImage` - Image attachments
- `MdThreeDModel` - 3D model data
- `MdAnalysis` - Analysis results

### 3. Core Classes
- `ModanMainWindow` - Main application window
- `ModanController` - MVC controller
- `ObjectViewer2D` - 2D visualization
- `ObjectViewer3D` - 3D OpenGL visualization
- `MdDatasetOps` - Dataset operations

### 4. Performance Optimizations Tracked

#### Wait Cursor Usage
Methods that implement wait cursor for better UX:
- `ModanDialogs.py:2402` - `cbxShapeGrid_state_changed` (Shape grid toggling)
- `ModanDialogs.py:4072` - `pick_shape` (Chart point selection)
- `ModanDialogs.py:1710` - `NewAnalysisDialog.btnOK_clicked` (Analysis execution)
- `Modan2.py:659` - `on_action_analyze_dataset_triggered` (Analysis trigger)

#### Progress Indicators
Dialogs with progress feedback:
- `NewAnalysisDialog` - Integrated progress bar with status messages
- `ProgressDialog` - Generic progress dialog with stop button

## Search Capabilities

### Available Search Commands

```bash
# Search for symbols
python tools/search_index.py --symbol "DataExploration"

# Find Qt connections
python tools/search_index.py --qt "clicked"

# Find wait cursor usage
python tools/search_index.py --wait-cursor

# Find database model usage
python tools/search_index.py --model "MdAnalysis"

# Get file information
python tools/search_index.py --file "ModanDialogs.py"

# Show project statistics
python tools/search_index.py --stats

# Find dialog widgets
python tools/search_index.py --dialog "NewAnalysisDialog"
```

## Qt Signal/Slot Analysis

### Signal Types
- **User Actions**: 257 connections total
  - Button clicks
  - Menu actions
  - Widget state changes
  
### Common Patterns
- `on_action_*_triggered`: Menu/toolbar actions
- `*_clicked`: Button handlers
- `*_changed`: State change handlers

## Database Schema

### Primary Models
1. **MdDataset**
   - Core dataset container
   - Relations: has_many MdObject, MdAnalysis

2. **MdObject**
   - Individual data objects
   - Relations: belongs_to MdDataset

3. **MdAnalysis**
   - Analysis results
   - Relations: belongs_to MdDataset

## Code Complexity Metrics

### Largest Files (by lines)
1. `ModanDialogs.py` - 6,511 lines
2. `ModanComponents.py` - 4,359 lines
3. `Modan2.py` - 2,293 lines
4. `Modan2_original.py` - 1,872 lines
5. `ModanController.py` - 1,160 lines

### Most Complex Classes (by method count)
1. `ModanMainWindow` - 80+ methods
2. `DataExplorationDialog` - 60+ methods
3. `ObjectViewer3D` - 40+ methods
4. `ModanController` - 35+ methods

## Recommendations

### 1. Refactoring Opportunities
- `ModanDialogs.py` is very large (6,511 lines) - consider splitting
- Several dialogs share common patterns - extract base class

### 2. Performance Improvements
- Add wait cursor to more long-running operations
- Implement progress feedback for file I/O operations

### 3. Test Coverage Gaps
- No test files detected in index
- Consider adding unit tests for core functionality

### 4. Documentation Needs
- Add docstrings to key methods
- Document Qt signal/slot connections

## Next Steps

1. **Expand Index Coverage**
   - Add test file analysis
   - Include documentation strings
   - Track TODO/FIXME comments

2. **Enhance Search**
   - Implement fuzzy search
   - Add regex pattern matching
   - Create web-based search UI

3. **Integration**
   - VSCode extension for inline hints
   - Git hooks for index updates
   - CI/CD pipeline integration

## Tools Created

1. **build_index.py** - Build complete project index
2. **search_index.py** - Search and query the index
3. **generate_cards.py** - Generate detailed symbol cards

## Usage

To rebuild the index:
```bash
python tools/build_index.py
```

To search the index:
```bash
python tools/search_index.py --help
```

To regenerate symbol cards:
```bash
python tools/generate_cards.py
```

---

*This index provides a searchable, queryable view of the Modan2 codebase, enabling faster navigation, better understanding of code relationships, and identification of optimization opportunities.*