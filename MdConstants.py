"""
Constants and configuration values for Modan2 application.
"""

from pathlib import Path

# Import version from centralized version file
try:
    from version import __version__ as APP_VERSION
except ImportError:
    APP_VERSION = "0.1.5-alpha.1"  # Fallback

# ========== Application Information ==========
APP_NAME = "Modan2"
APP_AUTHOR = "Modan2 Team"
APP_LICENSE = "MIT"
APP_DESCRIPTION = "Morphometric Data Analysis Application"
APP_URL = "https://github.com/jikhanjung/Modan2"

# ========== Paths ==========
BASE_DIR = Path(__file__).parent
ICONS_DIR = BASE_DIR / "icons"
TRANSLATIONS_DIR = BASE_DIR / "translations"
CONFIG_DIR = Path.home() / ".modan2"
TEMP_DIR = BASE_DIR / "temp"

# ========== Icon Mappings ==========
ICONS = {
    # Main actions
    "new_dataset": str(ICONS_DIR / "M2NewDataset_1.png"),
    "new_object": str(ICONS_DIR / "M2NewObject_2.png"),
    "import": str(ICONS_DIR / "M2Import_1.png"),
    "export": str(ICONS_DIR / "M2Export_1.png"),
    "analysis": str(ICONS_DIR / "M2Analysis_1.png"),
    "preferences": str(ICONS_DIR / "M2Preferences_1.png"),
    "about": str(ICONS_DIR / "M2About_1.png"),
    # Tools
    "landmark": str(ICONS_DIR / "M2Landmark_2.png"),
    "landmark_hover": str(ICONS_DIR / "M2Landmark_2_hover.png"),
    "landmark_down": str(ICONS_DIR / "M2Landmark_2_down.png"),
    "landmark_disabled": str(ICONS_DIR / "M2Landmark_2_disabled.png"),
    "wireframe": str(ICONS_DIR / "M2Wireframe_2.png"),
    "wireframe_hover": str(ICONS_DIR / "M2Wireframe_2_hover.png"),
    "wireframe_down": str(ICONS_DIR / "M2Wireframe_2_down.png"),
    "calibration": str(ICONS_DIR / "M2Calibration_2.png"),
    "calibration_hover": str(ICONS_DIR / "M2Calibration_2_hover.png"),
    "calibration_down": str(ICONS_DIR / "M2Calibration_2_down.png"),
    "calibration_disabled": str(ICONS_DIR / "M2Calibration_2_disabled.png"),
    # Data types
    "dataset_2d": str(ICONS_DIR / "M2Dataset2D_3.png"),
    "dataset_3d": str(ICONS_DIR / "M2Dataset3D_4.png"),
    "analysis_result": str(ICONS_DIR / "M2Analysis_1.png"),
    # General
    "app_icon": str(ICONS_DIR / "Modan2.png"),
    "app_icon_alt": str(ICONS_DIR / "Modan2_2.png"),
    "edit_object": str(ICONS_DIR / "EditObject.png"),
    "add_variable": str(ICONS_DIR / "add_variable.png"),
    "save_changes": str(ICONS_DIR / "SaveChanges.png"),
    # Selection types
    "cell_selection": str(ICONS_DIR / "cell_selection.png"),
    "row_selection": str(ICONS_DIR / "row_selection.png"),
}

# ========== File Filters ==========
FILE_FILTERS = {
    "landmark": "Landmark Files (*.tps *.nts *.txt);;TPS Files (*.tps);;NTS Files (*.nts);;Text Files (*.txt);;All Files (*.*)",
    "image": "Image Files (*.jpg *.jpeg *.png *.bmp *.tiff);;JPEG Files (*.jpg *.jpeg);;PNG Files (*.png);;BMP Files (*.bmp);;TIFF Files (*.tiff);;All Files (*.*)",
    "3d_model": "3D Model Files (*.obj *.ply *.stl);;Wavefront OBJ (*.obj);;Stanford PLY (*.ply);;STL Files (*.stl);;All Files (*.*)",
    "all_supported": "All Supported Files (*.tps *.nts *.txt *.jpg *.jpeg *.png *.bmp *.tiff *.obj *.ply *.stl);;All Files (*.*)",
    "csv": "CSV Files (*.csv);;All Files (*.*)",
    "excel": "Excel Files (*.xlsx *.xls);;XLSX Files (*.xlsx);;XLS Files (*.xls);;All Files (*.*)",
    "json": "JSON Files (*.json);;All Files (*.*)",
    "xml": "XML Files (*.xml);;All Files (*.*)",
}

# ========== Default Settings ==========
DEFAULT_SETTINGS = {
    # Appearance
    "language": "en",
    "theme": "default",  # default, dark, light
    "toolbar_icon_size": 32,
    "font_family": "Arial",
    "font_size": 9,
    # Behavior
    "auto_save": True,
    "auto_save_interval": 300,  # seconds
    "max_recent_files": 10,
    "confirm_deletions": True,
    "show_tooltips": True,
    # Window state
    "window_geometry": None,
    "window_state": None,
    "splitter_state": None,
    "remember_window_state": True,
    # Viewer settings
    "landmark_size": 3,
    "landmark_color": "#ff0000",
    "wireframe_color": "#0000ff",
    "background_color": "#ffffff",
    "selection_color": "#00ff00",
    "hover_color": "#ffff00",
    "grid_color": "#cccccc",
    # Display options
    "show_object_names": True,
    "show_landmark_numbers": True,
    "show_wireframe": True,
    "show_grid": False,
    "anti_aliasing": True,
    "smooth_rendering": True,
    # Analysis settings
    "default_analysis_type": "PCA",
    "pca_components": None,  # Auto-determine
    "procrustes_scaling": True,
    "procrustes_reflection": True,
    "cva_groups": 2,
    # Export settings
    "default_export_format": "CSV",
    "include_metadata": True,
    "decimal_places": 6,
    "date_format": "%Y-%m-%d %H:%M:%S",
    # Performance
    "max_objects_in_memory": 1000,
    "cache_analysis_results": True,
    "parallel_processing": True,
    "max_worker_threads": 4,
}

# ========== Analysis Types ==========
ANALYSIS_TYPES = [
    {
        "name": "PCA",
        "display_name": "Principal Component Analysis",
        "description": "Dimensionality reduction and variance analysis",
        "min_objects": 2,
        "supports_2d": True,
        "supports_3d": True,
        "parameters": ["n_components"],
    },
    {
        "name": "CVA",
        "display_name": "Canonical Variate Analysis",
        "description": "Linear discriminant analysis for group classification",
        "min_objects": 6,
        "supports_2d": True,
        "supports_3d": True,
        "parameters": ["groups", "prior_probabilities"],
    },
    {
        "name": "MANOVA",
        "display_name": "Multivariate Analysis of Variance",
        "description": "Test for differences between group means",
        "min_objects": 6,
        "supports_2d": True,
        "supports_3d": True,
        "parameters": ["groups", "alpha_level"],
    },
    {
        "name": "PROCRUSTES",
        "display_name": "Procrustes Analysis",
        "description": "Shape superimposition and alignment",
        "min_objects": 2,
        "supports_2d": True,
        "supports_3d": True,
        "parameters": ["scaling", "reflection", "translation"],
    },
    {
        "name": "THIN_PLATE_SPLINE",
        "display_name": "Thin Plate Spline",
        "description": "Deformation analysis between shapes",
        "min_objects": 2,
        "supports_2d": True,
        "supports_3d": False,
        "parameters": ["reference_shape", "lambda_value"],
    },
]

# ========== File Extensions ==========
SUPPORTED_EXTENSIONS = {
    "landmark": [".tps", ".nts", ".txt"],
    "image": [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"],
    "3d_model": [".obj", ".ply", ".stl"],
    "export": [".csv", ".xlsx", ".xls", ".json", ".xml"],
    "archive": [".zip", ".tar", ".tar.gz"],
}

# Get all supported extensions as a flat list
ALL_SUPPORTED_EXTENSIONS = []
for ext_list in SUPPORTED_EXTENSIONS.values():
    ALL_SUPPORTED_EXTENSIONS.extend(ext_list)

# ========== Error Messages ==========
ERROR_MESSAGES = {
    # General
    "no_dataset": "Please select or create a dataset first.",
    "no_object": "Please select an object first.",
    "no_analysis": "Please select an analysis first.",
    # File operations
    "invalid_file": "The selected file is not valid or corrupted.",
    "file_not_found": "File not found: {}",
    "unsupported_format": "Unsupported file format: {}",
    "read_permission": "Permission denied reading file: {}",
    "write_permission": "Permission denied writing file: {}",
    # Data validation
    "insufficient_objects": "Insufficient objects for analysis. At least {} objects required.",
    "landmark_mismatch": "Landmark count mismatch. Expected {}, got {}.",
    "empty_dataset": "Dataset is empty. Please add objects first.",
    "invalid_landmarks": "Invalid landmark data in object: {}",
    # Analysis
    "analysis_failed": "Analysis failed: {}",
    "analysis_no_data": "No landmark data available for analysis.",
    "analysis_invalid_groups": "Invalid group configuration for analysis.",
    "analysis_singular_matrix": "Cannot perform analysis: data matrix is singular.",
    # Database
    "db_connection_failed": "Failed to connect to database: {}",
    "db_query_failed": "Database query failed: {}",
    "db_constraint_violation": "Database constraint violation: {}",
    # Export/Import
    "export_failed": "Export failed: {}",
    "import_failed": "Import failed: {}",
    "save_failed": "Failed to save: {}",
    "load_failed": "Failed to load: {}",
}

# ========== Warning Messages ==========
WARNING_MESSAGES = {
    "large_dataset": "Large dataset detected. Processing may take several minutes.",
    "unsaved_changes": "You have unsaved changes. Continue without saving?",
    "delete_confirmation": "Are you sure you want to delete '{}'? This action cannot be undone.",
    "overwrite_file": "File already exists. Do you want to overwrite it?",
    "outdated_analysis": "Analysis results may be outdated. Consider re-running the analysis.",
    "memory_usage": "High memory usage detected. Consider closing unused datasets.",
}

# ========== Info Messages ==========
INFO_MESSAGES = {
    "dataset_created": "Dataset '{}' created successfully.",
    "objects_imported": "Imported {} object(s) successfully.",
    "analysis_completed": "{} analysis completed in {:.2f} seconds.",
    "export_completed": "Data exported to '{}' successfully.",
    "settings_saved": "Settings saved successfully.",
    "database_updated": "Database updated successfully.",
}

# ========== UI Constants ==========

# Colors
COLORS = {
    "primary": "#3498db",
    "secondary": "#2c3e50",
    "success": "#27ae60",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "info": "#17a2b8",
    "light": "#f8f9fa",
    "dark": "#343a40",
    # Landmark colors
    "landmark_default": "#ff0000",
    "landmark_selected": "#00ff00",
    "landmark_hover": "#ffff00",
    "wireframe_default": "#0000ff",
    "background_default": "#ffffff",
}

# Dimensions
DIMENSIONS = {
    "toolbar_icon_sizes": [16, 24, 32, 48, 64],
    "landmark_sizes": [1, 2, 3, 4, 5, 6, 8, 10],
    "font_sizes": [8, 9, 10, 11, 12, 14, 16, 18, 20, 24],
    "min_window_width": 800,
    "min_window_height": 600,
    "default_window_width": 1200,
    "default_window_height": 800,
    "splitter_handle_width": 3,
    "tree_min_width": 200,
    "table_min_height": 150,
    "viewer_min_size": 300,
}

# ========== Keyboard Shortcuts ==========
SHORTCUTS = {
    # File operations
    "new_dataset": "Ctrl+N",
    "open_file": "Ctrl+O",
    "save": "Ctrl+S",
    "save_as": "Ctrl+Shift+S",
    "import": "Ctrl+I",
    "export": "Ctrl+E",
    "quit": "Ctrl+Q",
    # Edit operations
    "undo": "Ctrl+Z",
    "redo": "Ctrl+Y",
    "copy": "Ctrl+C",
    "paste": "Ctrl+V",
    "delete": "Delete",
    "select_all": "Ctrl+A",
    # View operations
    "zoom_in": "Ctrl++",
    "zoom_out": "Ctrl+-",
    "zoom_fit": "Ctrl+0",
    "fullscreen": "F11",
    "toggle_grid": "Ctrl+G",
    "toggle_wireframe": "Ctrl+W",
    # Analysis
    "run_analysis": "F5",
    "stop_analysis": "Esc",
    # Navigation
    "next_object": "Page Down",
    "prev_object": "Page Up",
    "first_object": "Home",
    "last_object": "End",
    # Help
    "help": "F1",
    "about": "Ctrl+F1",
}

# ========== Status Bar Messages ==========
STATUS_MESSAGES = {
    "ready": "Ready",
    "loading": "Loading...",
    "saving": "Saving...",
    "processing": "Processing...",
    "analyzing": "Running analysis...",
    "importing": "Importing files...",
    "exporting": "Exporting data...",
    "dataset_selected": "Dataset: {}",
    "object_selected": "Object: {} ({} landmarks)",
    "analysis_selected": "Analysis: {}",
    "objects_count": "{} objects",
    "landmarks_count": "{} landmarks",
}

# ========== Validation Constants ==========
VALIDATION = {
    "min_dataset_name_length": 1,
    "max_dataset_name_length": 100,
    "min_object_name_length": 1,
    "max_object_name_length": 100,
    "min_landmarks": 3,
    "max_landmarks": 1000,
    "min_objects_for_pca": 2,
    "min_objects_for_cva": 6,
    "min_objects_for_manova": 6,
    "max_file_size_mb": 100,
    "allowed_image_formats": [".jpg", ".jpeg", ".png", ".bmp", ".tiff"],
    "allowed_3d_formats": [".obj", ".ply", ".stl"],
    "allowed_landmark_formats": [".tps", ".nts", ".txt"],
}

# ========== Database Constants ==========
DATABASE = {
    "default_name": "modan2.db",
    "backup_suffix": ".backup",
    "migration_table": "modan_migrations",
    "max_connections": 5,
    "timeout_seconds": 30,
    "journal_mode": "WAL",  # Write-Ahead Logging
    "foreign_keys": True,
}

# ========== Performance Constants ==========
PERFORMANCE = {
    "max_objects_in_table": 1000,
    "table_update_batch_size": 100,
    "analysis_progress_interval": 10,  # Update progress every N operations
    "image_cache_size": 50,  # Number of images to keep in cache
    "max_undo_levels": 20,
    "auto_gc_interval": 300,  # Garbage collection interval (seconds)
}

# ========== Export Formats ==========
EXPORT_FORMATS = {
    "csv": {
        "name": "Comma Separated Values",
        "extension": ".csv",
        "mime_type": "text/csv",
        "supports_metadata": True,
        "supports_landmarks": True,
        "supports_images": False,
        "supports_3d": False,
    },
    "excel": {
        "name": "Microsoft Excel",
        "extension": ".xlsx",
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "supports_metadata": True,
        "supports_landmarks": True,
        "supports_images": False,
        "supports_3d": False,
    },
    "json": {
        "name": "JavaScript Object Notation",
        "extension": ".json",
        "mime_type": "application/json",
        "supports_metadata": True,
        "supports_landmarks": True,
        "supports_images": False,
        "supports_3d": False,
    },
    "tps": {
        "name": "TPS Format",
        "extension": ".tps",
        "mime_type": "text/plain",
        "supports_metadata": False,
        "supports_landmarks": True,
        "supports_images": False,
        "supports_3d": False,
    },
    "nts": {
        "name": "NTS Format",
        "extension": ".nts",
        "mime_type": "text/plain",
        "supports_metadata": False,
        "supports_landmarks": True,
        "supports_images": False,
        "supports_3d": False,
    },
}

# ========== Themes ==========
THEMES = {
    "default": {
        "name": "Default",
        "description": "Default system theme",
        "stylesheet": "",
    },
    "dark": {
        "name": "Dark",
        "description": "Dark theme for low-light environments",
        "stylesheet": """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTreeWidget, QTableWidget, QListWidget {
                background-color: #353535;
                color: #ffffff;
                selection-background-color: #4a90e2;
                alternate-background-color: #404040;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenuBar::item:selected {
                background-color: #4a90e2;
            }
            QMenu {
                background-color: #353535;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
            }
            QToolBar {
                background-color: #2b2b2b;
                border: 1px solid #555555;
            }
            QStatusBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
            QDockWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4a90e2;
            }
        """,
    },
    "light": {
        "name": "Light",
        "description": "Light theme with high contrast",
        "stylesheet": """
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
            }
            QTreeWidget, QTableWidget, QListWidget {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #0078d4;
                alternate-background-color: #f0f0f0;
            }
        """,
    },
}

# ========== Logging Configuration ==========
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "datefmt": "%Y-%m-%d %H:%M:%S"},
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "level": "INFO", "formatter": "standard", "stream": "sys.stdout"},
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/modan2.log",
            "encoding": "utf-8",
            "mode": "a",
        },
    },
    "loggers": {
        "ModanController": {"level": "DEBUG", "handlers": ["console", "file"], "propagate": False},
        "MdAppSetup": {"level": "DEBUG", "handlers": ["console", "file"], "propagate": False},
        "ModanWidgets": {"level": "DEBUG", "handlers": ["console", "file"], "propagate": False},
    },
}

# ========== Regular Expressions ==========
REGEX_PATTERNS = {
    "dataset_name": r"^[a-zA-Z0-9_\-\s]{1,100}$",
    "object_name": r"^[a-zA-Z0-9_\-\s\.]{1,100}$",
    "file_extension": r"\\.([a-zA-Z0-9]+)$",
    "landmark_line": r"^\\s*([+-]?\\d*\\.?\\d+)\\s+([+-]?\\d*\\.?\\d+)\\s*$",
    "number": r"^[+-]?\\d*\\.?\\d+$",
    "integer": r"^[+-]?\\d+$",
    "positive_integer": r"^[1-9]\\d*$",
}

# ========== Units ==========
UNITS = {
    "length": ["mm", "cm", "m", "inch", "pixel"],
    "angle": ["degree", "radian"],
    "time": ["second", "minute", "hour", "day"],
    "size": ["B", "KB", "MB", "GB"],
}

# ========== Help URLs ==========
HELP_URLS = {
    "documentation": "https://github.com/jikhanjung/Modan2/wiki",
    "tutorial": "https://github.com/jikhanjung/Modan2/wiki/Tutorial",
    "pca_help": "https://github.com/jikhanjung/Modan2/wiki/PCA-Analysis",
    "cva_help": "https://github.com/jikhanjung/Modan2/wiki/CVA-Analysis",
    "file_formats": "https://github.com/jikhanjung/Modan2/wiki/File-Formats",
    "bug_report": "https://github.com/jikhanjung/Modan2/issues",
    "feature_request": "https://github.com/jikhanjung/Modan2/issues/new",
}

# ========== Debug Constants ==========
DEBUG = {
    "log_level": "DEBUG",
    "show_debug_menu": True,
    "enable_profiling": False,
    "memory_profiling": False,
    "sql_logging": False,
    "qt_logging": False,
}

# ========== Version Information ==========
VERSION_INFO = {
    "major": 0,
    "minor": 1,
    "patch": 5,
    "pre_release": "alpha.1",  # 'alpha', 'beta', 'rc1', etc.
    "build": None,
    "full": APP_VERSION,
}


def get_icon_path(icon_name: str) -> str:
    """Get full path for icon.

    Args:
        icon_name: Icon name from ICONS dict

    Returns:
        Full path to icon file
    """
    return ICONS.get(icon_name, "")


def get_file_filter(filter_name: str) -> str:
    """Get file filter string.

    Args:
        filter_name: Filter name from FILE_FILTERS dict

    Returns:
        File filter string for dialogs
    """
    return FILE_FILTERS.get(filter_name, "All Files (*.*)")


def get_analysis_info(analysis_name: str) -> dict:
    """Get analysis type information.

    Args:
        analysis_name: Analysis type name

    Returns:
        Dictionary with analysis information
    """
    for analysis in ANALYSIS_TYPES:
        if analysis["name"] == analysis_name.upper():
            return analysis
    return {}


def is_supported_file(file_path: str) -> bool:
    """Check if file format is supported.

    Args:
        file_path: Path to file

    Returns:
        True if file format is supported
    """
    ext = Path(file_path).suffix.lower()
    return ext in ALL_SUPPORTED_EXTENSIONS


def get_file_category(file_path: str) -> str:
    """Get file category based on extension.

    Args:
        file_path: Path to file

    Returns:
        File category ('landmark', 'image', '3d_model', or 'unknown')
    """
    ext = Path(file_path).suffix.lower()

    for category, extensions in SUPPORTED_EXTENSIONS.items():
        if ext in extensions:
            return category

    return "unknown"
