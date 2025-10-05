# Large Dialog Splitting Strategy - Phase 2

**Date**: 2025-10-05
**Status**: Planning
**Target**: ObjectDialog, DatasetAnalysisDialog, DataExplorationDialog

## Overview

Phase 2 has successfully extracted all simple dialogs (8/8) and moved all utility widgets (2/2). The remaining work involves splitting 3 large, complex dialogs into manageable modules.

## Large Dialogs Analysis

### 1. ObjectDialog (1,175 lines)

**Location**: ModanDialogs.py:846-2020

**Complexity**: High
- 40+ methods
- Multiple UI sections (landmark editor, image viewer, 3D viewer)
- Complex state management (missing landmarks, estimation)

**Key Responsibilities**:
1. **Object metadata management** (name, sequence, description)
2. **Landmark data editing** (add/update/delete coordinates)
3. **Image file management** (attach images to objects)
4. **3D model visualization** (ObjectViewer3D integration)
5. **Missing landmark estimation** (TPS-based estimation)
6. **Calibration** (pixel-to-metric conversion)

**Method Categories**:
- **Initialization**: `__init__`, `read_settings`, `write_settings`, `closeEvent`
- **Data management**: `set_dataset`, `set_object`, `save_object`, `make_landmark_str`
- **Landmark editing**: `add_landmark`, `update_landmark`, `delete_landmark`, `on_landmark_selected`
- **Missing landmarks**: `estimate_missing_for_object`, `compute_aligned_mean`, `toggle_estimation`
- **UI controls**: `btnAddInput_clicked`, `btnUpdateInput_clicked`, `btnDeleteInput_clicked`
- **Image management**: `btnAddFile_clicked`, `set_object_calibration`, `btnCalibration_clicked`
- **Navigation**: `Previous`, `Next`, `Delete`
- **View controls**: `show_index_state_changed`, `show_model_state_changed`, `show_wireframe_state_changed`

**Proposed Splitting**:
```
dialogs/
└── object_dialog/
    ├── __init__.py
    ├── base.py              (ObjectDialog base class - 400 lines)
    ├── landmark_panel.py    (Landmark editing UI - 400 lines)
    └── estimation.py        (Missing landmark estimation - 375 lines)
```

**Rationale**:
- **base.py**: Core dialog, dataset/object management, navigation
- **landmark_panel.py**: UI components for landmark table, input controls
- **estimation.py**: Missing landmark computation logic (TPS, aligned mean)

### 2. DatasetAnalysisDialog (1,306 lines)

**Location**: ModanDialogs.py:4989-6293

**Complexity**: Very High
- 50+ methods
- Multiple analysis types (PCA, CVA, MANOVA)
- Complex visualization (scatter plots, shape viewers)
- Object selection management

**Key Responsibilities**:
1. **Analysis configuration** (type, parameters, superimposition)
2. **Object selection** (select all/none/invert, table view)
3. **Analysis execution** (PCA, CVA, MANOVA)
4. **Results visualization** (scatter plots, charts)
5. **Shape viewer integration** (ObjectViewer3D)
6. **Results export** (save analysis data)

**Method Categories**:
- **Initialization**: `__init__`, `read_settings`, `write_settings`, `closeEvent`
- **Dataset management**: `set_dataset`, `load_object`, `reset_tableView`
- **Analysis configuration**: `on_analysis_type_changed`, `propertyname_changed`, `axis_changed`
- **Analysis execution**: `on_btnAnalyze_clicked`, `PerformPCA`, `PerformCVA`
- **Results display**: `show_analysis_result`, `show_result_table`, `show_object_shape`
- **Object selection**: `select_all`, `select_none`, `select_invert`, `get_selected_object_id_list`
- **Chart options**: `chart_options_clicked`, `on_chart_dim_changed`, `flip_axis_changed`
- **Events**: `on_pick`, `on_mouse_clicked`, `on_scatter_item_clicked`

**Proposed Splitting**:
```
dialogs/
└── dataset_analysis_dialog/
    ├── __init__.py
    ├── base.py              (DatasetAnalysisDialog base - 450 lines)
    ├── config_panel.py      (Analysis configuration UI - 400 lines)
    └── results_panel.py     (Results visualization - 456 lines)
```

**Rationale**:
- **base.py**: Core dialog, dataset management, object selection table
- **config_panel.py**: Analysis type, parameters, superimposition options
- **results_panel.py**: Chart display, scatter plots, results export

### 3. DataExplorationDialog (2,600 lines)

**Location**: ModanDialogs.py:2388-4987

**Complexity**: Extremely High
- 70+ methods
- Multiple visualization modes (scatter, regression, growth trajectory)
- Complex shape grid system
- Animation support
- Overlay settings

**Key Responsibilities**:
1. **Analysis setup** (load analysis results, group selection)
2. **Scatter plot visualization** (2D/3D charts with matplotlib)
3. **Shape viewer grid** (multiple shape viewers with sync)
4. **Regression analysis** (shape regression, polynomial fits)
5. **Growth trajectory** (animation, video export)
6. **Interactive picking** (select objects from chart)
7. **Overlay settings** (customizable shape display)

**Method Categories**:
- **Initialization**: `__init__`, `init_UI`, `read_settings`, `write_settings`, `closeEvent`
- **UI setup**: `_setup_title_row`, `_setup_plot_canvases`, `_setup_chart_basic_options`, `_setup_overlay_settings`, `_setup_regression_controls`, `_setup_shape_view_controls`
- **Analysis management**: `set_analysis`, `prepare_scatter_data`, `show_analysis_result`
- **Visualization**: `update_chart`, `prepare_shape_view`, `show_average_shapes`
- **Regression**: `shape_regression`, `calculate_fit`, `calculate_r_squared`
- **Shape grid**: `cbxShapeGrid_state_changed`, `reposition_shape_grid`, `shape_grid_preference_changed`
- **Interactive events**: `on_pick`, `pick_shape`, `on_canvas_button_press`, `on_canvas_move`, `on_hover_enter`
- **Animation**: `chart_animation`, `animate_shape`, `create_video_from_frames`
- **Mode switching**: `set_mode`, `comboVisualizationMethod_changed`, `set_growth_trajectory_mode`
- **Synchronization**: `sync_rotation`, `sync_pan`, `sync_zoom`, `sync_temp_rotation`

**Proposed Splitting**:
```
dialogs/
└── data_exploration_dialog/
    ├── __init__.py
    ├── base.py              (DataExplorationDialog base - 600 lines)
    ├── chart_panel.py       (Scatter plot, matplotlib canvas - 700 lines)
    ├── shape_panel.py       (Shape viewers, grid system - 700 lines)
    └── controls_panel.py    (Overlay, regression, animation - 600 lines)
```

**Rationale**:
- **base.py**: Core dialog, analysis loading, mode management
- **chart_panel.py**: Matplotlib canvases, scatter plots, picking logic
- **shape_panel.py**: Shape viewer grid, synchronization, display
- **controls_panel.py**: UI controls for overlay, regression, animation

## Implementation Strategy

### Phase 1: ObjectDialog (Estimated: 1 day)
1. ✅ Create `dialogs/object_dialog/` package
2. ✅ Extract `base.py` with core dialog logic
3. ✅ Extract `landmark_panel.py` with UI components
4. ✅ Extract `estimation.py` with missing landmark logic
5. ✅ Update `dialogs/__init__.py` imports
6. ✅ Run tests, verify no regressions
7. ✅ Commit

### Phase 2: DatasetAnalysisDialog (Estimated: 1 day)
1. Create `dialogs/dataset_analysis_dialog/` package
2. Extract `base.py` with core dialog logic
3. Extract `config_panel.py` with configuration UI
4. Extract `results_panel.py` with visualization logic
5. Update `dialogs/__init__.py` imports
6. Run tests, verify no regressions
7. Commit

### Phase 3: DataExplorationDialog (Estimated: 2 days)
1. Create `dialogs/data_exploration_dialog/` package
2. Extract `base.py` with core dialog logic
3. Extract `chart_panel.py` with matplotlib canvas
4. Extract `shape_panel.py` with shape viewer grid
5. Extract `controls_panel.py` with UI controls
6. Update `dialogs/__init__.py` imports
7. Run tests, verify no regressions
8. Commit

## Success Criteria

1. **All tests passing**: 495 passed, 35 skipped (no regressions)
2. **Backward compatibility**: Existing imports still work
3. **Code quality**:
   - Full type hints on all methods
   - Comprehensive docstrings
   - Clear separation of concerns
   - No code duplication
4. **Maintainability**:
   - Each module < 800 lines
   - Logical grouping of functionality
   - Clear module boundaries

## Risks and Mitigation

### Risk 1: Circular dependencies
**Mitigation**: Use dependency injection, pass references via constructor

### Risk 2: Breaking existing functionality
**Mitigation**: Run full test suite after each extraction, manual testing

### Risk 3: Complex state sharing
**Mitigation**: Keep shared state in base class, use signals for communication

### Risk 4: Large refactoring scope
**Mitigation**: Break into small, incremental commits with tests

## Expected Outcome

**Before**:
- ModanDialogs.py: 7,653 lines
- 3 monolithic dialog classes (5,081 lines combined)

**After**:
- ModanDialogs.py: ~2,600 lines (only DataExplorationDialog remaining temporarily)
- 10 well-organized dialog modules (~500-700 lines each)
- Better testability, maintainability, readability

**Estimated Code Increase**: +20-30% (documentation, refactoring, type hints)

---

**Status**: Ready to implement Phase 1 (ObjectDialog)
