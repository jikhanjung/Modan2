# Modan2 Code Index Report

**Generated**: 2026-07-21  
**Index Version**: 1.1

## Project Statistics

| Metric | Count |
|--------|-------|
| Total Files | 146 |
| Total Lines | 58855 |
| Classes | 547 |
| Functions | 3098 |
| Dialogs | 83 |
| Database Models | 5 |
| Qt Signal Definitions | 27 |
| Qt Connections | 241 |

## Key Components Indexed

### 1. Dialog Classes (83)
- `NewAnalysisDialog`
- `AnalysisResultDialog`
- `BaseDialog`
- `CalibrationDialog`
- `DatasetAnalysisDialog`
- `DatasetDialog`
- `DataExplorationDialog`
- `ExportDatasetDialog`
- `ImportDatasetDialog`
- `ObjectDialog`
- `PreferencesDialog`
- `ProgressDialog`
- `TestDatasetDialogDirect`
- `TestDatasetDialogEdgeCases`
- `TestObjectDialogDirect`
- `TestDatasetObjectDialogIntegration`
- `TestNewDatasetDialog`
- `TestPreferencesDialog`
- `TestAnalysisDialog`
- `TestAboutDialog`
- `TestFileDialogs`
- `TestEditObjectDialog`
- `TestNewAnalysisDialogInitialization`
- `TestNewAnalysisDialogValidation`
- `TestNewAnalysisDialogUserInteractions`
- `TestNewAnalysisDialogProgress`
- `TestNewAnalysisDialogCompletion`
- `TestNewAnalysisDialogHelpers`
- `TestNewAnalysisDialogIntegration`
- `TestAnalysisResultDialogInitialization`
- `TestAnalysisResultDialogPreferences`
- `TestAnalysisResultDialogDataStructures`
- `TestAnalysisResultDialogSettings`
- `TestAnalysisResultDialogCloseEvent`
- `TestAnalysisResultDialogIntegration`
- `TestBaseDialogInitialization`
- `TestBaseDialogMessageBoxes`
- `TestBaseDialogProgressBar`
- `TestBaseDialogWaitCursor`
- `TestBaseDialogButtonBox`
- `TestBaseDialogIntegration`
- `CustomDialog`
- `TestCalibrationDialogInitialization`
- `TestCalibrationDialogInput`
- `TestCalibrationDialogActions`
- `TestCalibrationDialogPixelNumber`
- `TestCalibrationDialogSettings`
- `TestCalibrationDialogIntegration`
- `TestDatasetDialogInitialization`
- `TestDatasetDialogDimensionSelection`
- `TestDatasetDialogBasicInput`
- `TestDatasetDialogVariableManagement`
- `TestDatasetDialogSettings`
- `TestDatasetDialogIntegration`
- `TestExportDatasetDialogInitialization`
- `TestExportDatasetDialogObjectSelection`
- `TestExportDatasetDialogFormatSelection`
- `TestExportDatasetDialogSuperimposition`
- `TestExportDatasetDialogJSONZipOptions`
- `TestExportDatasetDialogExport`
- `TestExportDatasetDialogButtons`
- `TestExportDatasetDialogSettings`
- `TestExportDatasetDialogIntegration`
- `TestImportDatasetDialogInitialization`
- `TestImportDatasetDialogFileSelection`
- `TestImportDatasetDialogDatasetNaming`
- `TestImportDatasetDialogFileTypes`
- `TestImportDatasetDialogOptions`
- `TestImportDatasetDialogValidation`
- `TestImportDatasetDialogProgress`
- `TestImportDatasetDialogIntegration`
- `TestPreferencesDialogInitialization`
- `TestPreferencesDialogGeometry`
- `TestPreferencesDialogToolbar`
- `TestPreferencesDialogPlot`
- `TestPreferencesDialogLandmarks`
- `TestPreferencesDialogWireframe`
- `TestPreferencesDialogIndex`
- `TestPreferencesDialogLanguage`
- `TestPreferencesDialogButtons`
- `TestPreferencesDialogSettingsPersistence`
- `TestPreferencesDialogColorPickers`
- `TestPreferencesDialogIntegration`

### 2. Database Models (5)
- `MdDataset`
- `MdObject`
- `MdImage`
- `MdThreeDModel`
- `MdAnalysis`

## Qt Signal/Slot Analysis

- Signal definitions: 27
- Connections: 241

## Code Complexity Metrics

### Largest Files (by lines)
1. `test_mdmodel.py` - 4,452 lines
1. `data_exploration_dialog.py` - 2,683 lines
1. `MdModel.py` - 2,469 lines
1. `Modan2.py` - 2,024 lines
1. `ModanController.py` - 1,567 lines

### Most Complex Classes (by method count)
1. `DataExplorationDialog` - 83 methods (data_exploration_dialog.py:122)
1. `ModanMainWindow` - 76 methods (Modan2.py:242)
1. `ObjectViewer3D` - 63 methods (object_viewer_3d.py:82)
1. `ObjectViewer2D` - 57 methods (object_viewer_2d.py:76)

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
