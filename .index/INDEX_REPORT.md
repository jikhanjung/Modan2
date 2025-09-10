# Modan2 Code Index Report

**Generated**: 2025-09-10  
**Index Version**: 1.1

## Project Statistics

| Metric | Count |
|--------|-------|
| Total Files | 86 |
| Total Lines | 35303 |
| Classes | 194 |
| Functions | 1541 |
| Dialogs | 11 |
| Database Models | 5 |
| Qt Signal Definitions | 26 |
| Qt Connections | 281 |

## Key Components Indexed

### 1. Dialog Classes (11)
- `ProgressDialog`
- `CalibrationDialog`
- `DatasetDialog`
- `ObjectDialog`
- `NewAnalysisDialog`
- `AnalysisResultDialog`
- `DataExplorationDialog`
- `DatasetAnalysisDialog`
- `ExportDatasetDialog`
- `ImportDatasetDialog`
- `PreferencesDialog`

### 2. Database Models (5)
- `MdDataset`
- `MdObject`
- `MdImage`
- `MdThreeDModel`
- `MdAnalysis`

## Qt Signal/Slot Analysis

- Signal definitions: 26
- Connections: 281

## Code Complexity Metrics

### Largest Files (by lines)
1. `ModanDialogs.py` - 6,724 lines
1. `ModanComponents.py` - 4,528 lines
1. `Modan2.py` - 1,782 lines
1. `MdModel.py` - 1,752 lines
1. `Modan2_original.py` - 1,501 lines

### Most Complex Classes (by method count)
1. `ModanMainWindow` - 74 methods (Modan2.py:57)
1. `DataExplorationDialog` - 68 methods (ModanDialogs.py:1931)
1. `ObjectViewer3D` - 62 methods (ModanComponents.py:1132)
1. `ModanMainWindow` - 60 methods (Modan2_original.py:51)

## Recommendations

- Split very large UI files into focused modules.
- Extract common dialog base behaviors (validation/progress).
- Expand unit tests for core logic and indexing edge cases.

## Tools Created/Used

- `tools/build_index.py` - Build project index (AST+regex)
- `tools/search_index.py` - Query/search the index
- `tools/generate_cards.py` - Generate symbol cards
- `tools/generate_report.py` - Generate this report from JSON

## Usage

To rebuild the index:

```bash
python tools/build_index.py
```

To generate the report:

```bash
python tools/generate_report.py
```
