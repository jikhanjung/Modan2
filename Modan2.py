import sys
import os
import re

# Fix for Anaconda Python sys.version parsing issue with pandas/platform module
# This must be done before importing any module that uses platform.python_implementation()
if hasattr(sys, 'version') and '| packaged by Anaconda' in sys.version:
    # Remove the Anaconda-specific part from sys.version
    original_version = sys.version
    parts = sys.version.split('|')
    if len(parts) >= 3:
        # Keep only the first part (version) and last part (compiler info)
        sys.version = parts[0].strip() + ' ' + parts[-1].strip()

from PyQt6.QtWidgets import QMainWindow, QHeaderView, QApplication, QAbstractItemView, \
                            QMessageBox, QTreeView, QTableView, QSplitter, QMenu, \
                            QStatusBar, QInputDialog, QToolBar, QWidget, QPlainTextEdit, QVBoxLayout, QHBoxLayout, \
                            QPushButton, QRadioButton, QLabel, QDockWidget
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem, QKeySequence, QCursor, QAction, QActionGroup
from PyQt6.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QSize, QTranslator, QItemSelectionModel, QObject, QEvent

from PyQt6.QtCore import pyqtSlot
import logging
from pathlib import Path
from peewee import *
from PIL.ExifTags import TAGS
import shutil
import copy
from datetime import datetime

from MdModel import *
import MdUtils as mu
from ModanController import ModanController
from MdConstants import ICONS as ICON_CONSTANTS
from MdHelpers import show_error, show_warning, show_info, confirm_action
from peewee_migrate import Router

from ModanDialogs import DatasetAnalysisDialog, ObjectDialog, ImportDatasetDialog, DatasetDialog, PreferencesDialog, \
    MODE, ObjectViewer3D, ExportDatasetDialog, ObjectViewer2D, ProgressDialog, NewAnalysisDialog, DataExplorationDialog
from ModanComponents import MdTableModel, MdTableView, MdSequenceDelegate, AnalysisInfoWidget
from ModanWidgets import DatasetTreeWidget, ObjectTableWidget, LandmarkViewer2D
from MdStatistics import PerformCVA, PerformPCA, PerformManova

import matplotlib.pyplot as plt
import matplotlib
# Configure matplotlib to avoid font warnings
matplotlib.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']
matplotlib.rcParams['font.serif'] = ['DejaVu Serif', 'serif']
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']

import json
from MdLogger import setup_logger
logger = setup_logger(mu.PROGRAM_NAME)



class ModanMainWindow(QMainWindow):
    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.init_done = False
        self.setWindowIcon(QIcon(ICON_CONSTANTS['app_icon_alt']))
        self.setWindowTitle("{} v{}".format(self.tr("Modan2"), mu.PROGRAM_VERSION))
        
        # Initialize controller
        self.controller = ModanController()

        # Initialize widgets (temporary compatibility)
        self.tableView = MdTableView()
        self.tableView.setItemDelegateForColumn(1, MdSequenceDelegate())
        self.treeView = QTreeView()
        
        # Setup connections after widgets are created
        self.setup_controller_connections()

        self.toolbar = QToolBar(self.tr("Main Toolbar"))
        self.toolbar.setIconSize(QSize(32,32))
        self.actionNewDataset = QAction(QIcon(ICON_CONSTANTS['new_dataset']), self.tr("New Dataset\tCtrl+N"), self)
        self.actionNewDataset.triggered.connect(self.on_action_new_dataset_triggered)
        self.actionNewDataset.setShortcut(QKeySequence("Ctrl+N"))

        self.actionCellSelection = QAction(QIcon(ICON_CONSTANTS['cell_selection']), self.tr("Cell selection"), self)
        self.actionCellSelection.triggered.connect(self.on_action_cell_selection_triggered)
        self.actionCellSelection.setCheckable(True)
        self.actionCellSelection.setChecked(True)
        self.actionRowSelection = QAction(QIcon(ICON_CONSTANTS['row_selection']), self.tr("Row selection"), self)
        self.actionRowSelection.triggered.connect(self.on_action_row_selection_triggered)
        self.actionRowSelection.setCheckable(True)
        self.actionAddVariable = QAction(QIcon(ICON_CONSTANTS['add_variable']), self.tr("Add variable"), self)
        self.actionAddVariable.triggered.connect(self.on_action_add_variable_triggered)
        self.actionSaveChanges = QAction(QIcon(ICON_CONSTANTS['save_changes']), self.tr("Save changes\tCtrl+S"), self)
        self.actionSaveChanges.triggered.connect(self.on_btnSaveChanges_clicked)
        self.actionSaveChanges.setShortcut(QKeySequence("Ctrl+S"))

        self.selection_mode_group = QActionGroup(self)
        self.selection_mode_group.setExclusive(True)
        self.selection_mode_group.addAction(self.actionCellSelection)
        self.selection_mode_group.addAction(self.actionRowSelection)

        self.actionNewObject = QAction(QIcon(ICON_CONSTANTS['new_object']), self.tr("New Object\tCtrl+Shift+N"), self)
        self.actionNewObject.triggered.connect(self.on_action_new_object_triggered)
        self.actionNewObject.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.actionEditObject = QAction(QIcon(ICON_CONSTANTS['edit_object']), self.tr("Edit Object\tCtrl+Shift+O"), self)
        self.actionEditObject.triggered.connect(self.on_tableView_doubleClicked)
        self.actionEditObject.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.actionImport = QAction(QIcon(ICON_CONSTANTS['import']), self.tr("Import\tCtrl+I"), self)
        self.actionImport.triggered.connect(self.on_action_import_dataset_triggered)
        self.actionImport.setShortcut(QKeySequence("Ctrl+I"))
        self.actionExport = QAction(QIcon(ICON_CONSTANTS['export']), self.tr("Export\tCtrl+E"), self)
        self.actionExport.triggered.connect(self.on_action_export_dataset_triggered)
        self.actionExport.setShortcut(QKeySequence("Ctrl+E"))
        self.actionAnalyze = QAction(QIcon(ICON_CONSTANTS['analysis']), self.tr("Analyze\tCtrl+G"), self)
        self.actionAnalyze.triggered.connect(self.on_action_analyze_dataset_triggered)
        self.actionAnalyze.setShortcut(QKeySequence("Ctrl+G"))
        self.actionPreferences = QAction(QIcon(ICON_CONSTANTS['preferences']), self.tr("Preferences"), self)
        self.actionPreferences.triggered.connect(self.on_action_edit_preferences_triggered)
        self.actionExit = QAction(QIcon(), self.tr("Exit\tCtrl+W"), self)
        self.actionExit.triggered.connect(self.on_action_exit_triggered)
        self.actionExit.setShortcut(QKeySequence("Ctrl+W"))
        self.actionAbout = QAction(QIcon(ICON_CONSTANTS['about']), self.tr("About\tF1"), self)
        self.actionAbout.triggered.connect(self.on_action_about_triggered)
        self.actionAbout.setShortcut(QKeySequence("F1"))

        self.toolbar.addAction(self.actionNewDataset)
        self.toolbar.addAction(self.actionNewObject)
        self.toolbar.addAction(self.actionEditObject)
        self.toolbar.addAction(self.actionCellSelection)
        self.toolbar.addAction(self.actionRowSelection)
        self.toolbar.addAction(self.actionAddVariable)
        self.toolbar.addAction(self.actionSaveChanges)
        self.toolbar.addAction(self.actionImport)
        self.toolbar.addAction(self.actionExport)
        self.toolbar.addAction(self.actionAnalyze)
        self.toolbar.addAction(self.actionPreferences)
        self.toolbar.addAction(self.actionAbout)
        self.addToolBar(self.toolbar)
        # Or use stylesheets for the toolbar
        self.toolbar.setStyleSheet("""
            QToolButton {
                border: 1px solid transparent;
                padding: 4px;
            }
            QToolButton:checked {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                border-radius: 2px;
            }
            QToolButton:hover {
                border: 1px solid #c0c0c0;
                border-radius: 2px;
            }
        """)

        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu(self.tr("File"))
        self.file_menu.addAction(self.actionExit)
        self.edit_menu = self.main_menu.addMenu(self.tr("Edit"))
        self.edit_menu.addAction(self.actionPreferences)
        self.data_menu = self.main_menu.addMenu(self.tr("Data"))
        self.data_menu.addAction(self.actionNewDataset)
        self.data_menu.addAction(self.actionNewObject)
        self.data_menu.addSeparator()
        self.data_menu.addAction(self.actionAnalyze)
        self.data_menu.addSeparator()
        self.data_menu.addAction(self.actionImport)
        self.data_menu.addAction(self.actionExport)
        self.help_menu = self.main_menu.addMenu(self.tr("Help"))
        self.help_menu.addAction(self.actionAbout)

        self.m_app = QApplication.instance()
        self.m_app.toolbar_icon_size = "Small"

        logger.info("Reading settings...")
        self.read_settings()
        logger.info("Settings read successfully")
        
        logger.info("Starting initUI()...")
        self.initUI()
        logger.info("initUI() completed, continuing initialization...")
        
        self.selected_dataset = None
        self.selected_object = None
        
        logger.info("Resetting views...")
        self.reset_views()
        logger.info("Views reset successfully")
        
        logger.info("Loading dataset...")
        self.load_dataset()
        logger.info("Dataset loaded successfully")
        
        logger.info("ModanMainWindow.__init__() completed successfully")

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.analysis_dialog = None
        self.data_changed = False
        self.remember_geometry = True

        self.set_toolbar_icon_size(self.m_app.toolbar_icon_size)
        self.init_done = True
    
    def set_splash(self, splash):
        """Set splash screen reference for progress updates"""
        self.splash = splash

    def get_object_view_3d(self):
        """Get ObjectViewer3D instance, creating it lazily if needed."""
        if self.object_view_3d is None:
            logger = logging.getLogger(__name__)
            
            try:
                logger.info("=== Starting ObjectViewer3D creation (lazy loading) ===")
                
                # Step 1: Import check
                logger.info("Step 1: Importing ObjectViewer3D class...")
                from ModanComponents import ObjectViewer3D
                logger.info("Step 1 COMPLETE: ObjectViewer3D class imported successfully")
                
                # Step 2: Check OpenGL environment
                logger.info("Step 2: Checking OpenGL environment...")
                import os
                logger.info(f"QT_OPENGL environment: {os.environ.get('QT_OPENGL', 'not set')}")
                logger.info(f"QT_OPENGL_BACKEND environment: {os.environ.get('QT_OPENGL_BACKEND', 'not set')}")
                logger.info("Step 2 COMPLETE: Environment checked")
                
                # Step 3: Constructor call
                logger.info("Step 3: Calling ObjectViewer3D constructor...")
                logger.info(f"Parent object: {type(self)}")
                self.object_view_3d = ObjectViewer3D(self)
                logger.info("Step 3 COMPLETE: ObjectViewer3D constructor finished")
                
                # Step 4: Initial state setup
                logger.info("Step 4: Setting initial state (hide)...")
                self.object_view_3d.hide()
                logger.info("Step 4 COMPLETE: ObjectViewer3D hidden")
                
                # Step 5: Settings
                logger.info("Step 5: Loading settings...")
                self.object_view_3d.read_settings()
                logger.info("Step 5 COMPLETE: ObjectViewer3D settings loaded")
                
                # Step 6: Layout integration
                logger.info("Step 6: Adding to layout...")
                if hasattr(self, 'viewer_container') and hasattr(self.viewer_container, 'layout'):
                    logger.info("Step 6a: Adding to dockable viewer container...")
                    self.viewer_container.layout().addWidget(self.object_view_3d)
                    logger.info("Step 6a COMPLETE: Added to dock container layout")
                elif hasattr(self, 'vsplitter'):
                    logger.info("Step 6b: Adding to main vsplitter...")
                    self.vsplitter.addWidget(self.object_view_3d)
                    logger.info("Step 6b COMPLETE: Added to vsplitter layout")
                else:
                    logger.info("Step 6: No layout container found, skipping layout addition")
                
                logger.info("=== ObjectViewer3D creation SUCCESSFUL ===")
                
            except Exception as e:
                logger.error(f"=== ObjectViewer3D creation FAILED ===")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception message: {str(e)}")
                import traceback
                logger.error("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    logger.error(f"  {line}")
                
                logger.warning("Falling back to 2D viewer for 3D datasets")
                # Fallback to 2D viewer to prevent complete failure
                return self.object_view_2d
        return self.object_view_3d

    def setup_controller_connections(self):
        """Setup signal connections with the controller"""
        # Connect controller signals to UI updates
        self.controller.dataset_created.connect(self.on_dataset_created)
        self.controller.dataset_updated.connect(self.on_dataset_updated)
        self.controller.object_added.connect(self.on_object_added)
        self.controller.object_updated.connect(self.on_object_updated)
        self.controller.analysis_completed.connect(self.on_analysis_completed)
        self.controller.error_occurred.connect(self.on_controller_error)

    def on_dataset_created(self, dataset):
        """Handle dataset creation from controller"""
        self.load_dataset()
        show_info(self, "Dataset created successfully")

    def on_dataset_updated(self, dataset):
        """Handle dataset update from controller"""
        self.load_dataset()

    def on_object_added(self, obj):
        """Handle object addition from controller"""
        self.load_dataset()

    def on_object_updated(self, obj):
        """Handle object update from controller"""
        self.load_dataset()

    def on_analysis_completed(self, analysis):
        """Handle analysis completion from controller"""
        self.load_dataset()
        show_info(self, "Analysis completed successfully")

    def on_controller_error(self, error_msg):
        """Handle controller errors"""
        show_error(self, error_msg)

    def on_dataset_selected_from_tree(self, dataset):
        """Handle dataset selection from tree widget"""
        self.selected_dataset = dataset
        if dataset is None:
            self.actionNewObject.setEnabled(False)
            self.actionExport.setEnabled(False)
            self.actionAnalyze.setEnabled(False)
        else:
            self.actionNewObject.setEnabled(True)
            self.actionExport.setEnabled(True)
            self.actionAnalyze.setEnabled(True)
            self.load_object()

    def on_analysis_selected_from_tree(self, analysis):
        """Handle analysis selection from tree widget"""
        logger.info(f"on_analysis_selected_from_tree called with: {analysis}")
        self.selected_analysis = analysis
        if analysis:
            logger.info(f"Analysis selected: {analysis.analysis_name}")
            
            # Switch to analysis view on right panel
            if hasattr(self, 'hsplitter') and hasattr(self, 'analysis_view'):
                logger.info(f"Switching to analysis view. Current widget: {self.hsplitter.widget(1)}")
                if self.hsplitter.widget(1) != self.analysis_view:
                    self.hsplitter.replaceWidget(1, self.analysis_view)
                    logger.info("Switched to analysis view")
            
            # Update analysis info widget
            if hasattr(self, 'analysis_info_widget') and self.analysis_info_widget:
                logger.info("Setting analysis on analysis_info_widget")
                self.analysis_info_widget.set_analysis(analysis)
                self.analysis_info_widget.show_analysis_result()
                logger.info("Analysis info widget updated")
            else:
                logger.warning("analysis_info_widget not found or None")
        else:
            self.selected_analysis = None
            logger.info("Analysis selection cleared")

    def on_object_selected_from_table(self, obj):
        """Handle object selection from table widget"""
        self.selected_object = obj
        if obj:
            self.show_object(obj)

    def update_settings(self):
        size = self.m_app.toolbar_icon_size
        self.set_toolbar_icon_size(size)
        self.object_view_2d.read_settings()
        # 3D viewer settings will be read when it's created (lazy loading)

    def set_toolbar_icon_size(self, size):
        if size.lower() == 'small':
            self.toolbar.setIconSize(QSize(24,24))
        elif size.lower() == 'medium':
            self.toolbar.setIconSize(QSize(32,32))
        else:
            self.toolbar.setIconSize(QSize(48,48))

    def on_action_open_db_triggered(self):
        pass

    def on_action_new_db_triggered(self):
        pass

    def on_action_save_as_triggered(self):
        pass

    def read_settings(self):
        """Read settings from config object"""
        if self.config is None:
            return
            
        self.m_app = QApplication.instance()
        self.m_app.storage_directory = os.path.abspath(mu.DEFAULT_STORAGE_DIRECTORY)
        self.m_app.toolbar_icon_size = self.config.get("ui", {}).get("toolbar_icon_size", "Medium")
        
        # Create a complete settings wrapper for compatibility
        if not hasattr(self.m_app, 'settings'):
            class SettingsWrapper:
                def __init__(self, config, parent):
                    self.config = config
                    self.parent = parent  # ModanMainWindow instance for save_config
                    # Complete key mapping for all settings
                    self.key_map = {
                        # Window geometry
                        "WindowGeometry/RememberGeometry": ("ui", "remember_geometry"),
                        "WindowGeometry/MainWindow": ("ui", "window_geometry", "main_window"),
                        "WindowGeometry/ObjectDialog": ("ui", "window_geometry", "object_dialog"),
                        "WindowGeometry/DatasetDialog": ("ui", "window_geometry", "dataset_dialog"),
                        "WindowGeometry/DataExplorationWindow": ("ui", "window_geometry", "data_exploration_window"),
                        "WindowGeometry/DatasetAnalysisWindow": ("ui", "window_geometry", "dataset_analysis_window"),
                        "WindowGeometry/ExportDialog": ("ui", "window_geometry", "export_dialog"),
                        "WindowGeometry/ImportDialog": ("ui", "window_geometry", "import_dialog"),
                        "WindowGeometry/PreferencesDialog": ("ui", "window_geometry", "preferences_dialog"),
                        
                        # Maximized state
                        "IsMaximized/MainWindow": ("ui", "is_maximized", "main_window"),
                        "IsMaximized/DataExplorationWindow": ("ui", "is_maximized", "data_exploration_window"),
                        
                        # Calibration
                        "Calibration/Unit": ("calibration", "unit"),
                        
                        # UI settings
                        "ToolbarIconSize": ("ui", "toolbar_icon_size"),
                        "PlotSize": ("ui", "plot_size"),
                        "BackgroundColor": ("ui", "background_color"),
                        "Language": ("language",),
                        
                        # 2D settings
                        "LandmarkSize/2D": ("ui", "landmark_size_2d"),
                        "LandmarkColor/2D": ("ui", "landmark_color_2d"),
                        "WireframeThickness/2D": ("ui", "wireframe_thickness_2d"),
                        "WireframeColor/2D": ("ui", "wireframe_color_2d"),
                        "IndexSize/2D": ("ui", "index_size_2d"),
                        "IndexColor/2D": ("ui", "index_color_2d"),
                        
                        # 3D settings
                        "LandmarkSize/3D": ("ui", "landmark_size_3d"),
                        "LandmarkColor/3D": ("ui", "landmark_color_3d"),
                        "WireframeThickness/3D": ("ui", "wireframe_thickness_3d"),
                        "WireframeColor/3D": ("ui", "wireframe_color_3d"),
                        "IndexSize/3D": ("ui", "index_size_3d"),
                        "IndexColor/3D": ("ui", "index_color_3d"),
                    }
                    
                    # Data point colors and markers (dynamic)
                    for i in range(10):
                        self.key_map[f"DataPointColor/{i}"] = ("ui", "data_point_colors", str(i))
                        self.key_map[f"DataPointMarker/{i}"] = ("ui", "data_point_markers", str(i))
                
                def _get_nested_value(self, keys, default_value):
                    """Get a value from nested dictionary."""
                    try:
                        value = self.config
                        for k in keys:
                            if isinstance(value, dict):
                                value = value.get(k, {})
                            else:
                                return default_value
                        return value if value != {} else default_value
                    except (KeyError, TypeError, AttributeError):
                        return default_value
                
                def _set_nested_value(self, keys, value):
                    """Set a value in nested dictionary."""
                    if not keys:
                        return
                    
                    # Ensure all parent dictionaries exist
                    current = self.config
                    for key in keys[:-1]:
                        if key not in current:
                            current[key] = {}
                        elif not isinstance(current[key], dict):
                            current[key] = {}
                        current = current[key]
                    
                    # Set the final value
                    current[keys[-1]] = value
                
                def value(self, key, default_value):
                    """Get a setting value (QSettings compatible)."""
                    if key in self.key_map:
                        value = self._get_nested_value(self.key_map[key], default_value)
                        # Handle WindowGeometry keys that should return QRect
                        if key.startswith("WindowGeometry/") and key != "WindowGeometry/RememberGeometry":
                            if isinstance(value, list) and len(value) == 4:
                                from PyQt6.QtCore import QRect
                                return QRect(*value)
                            elif hasattr(default_value, 'x'):  # default_value is QRect
                                return default_value
                        return value
                    return default_value
                
                def setValue(self, key, value):
                    """Set a setting value (QSettings compatible)."""
                    # Convert QRect to list for JSON serialization
                    if hasattr(value, 'x'):  # QRect or similar
                        value = [value.x(), value.y(), value.width(), value.height()]
                    
                    if key in self.key_map:
                        self._set_nested_value(self.key_map[key], value)
                        # Auto-save after each change
                        self.save()
                
                def save(self):
                    """Save settings to file."""
                    try:
                        import json
                        from pathlib import Path
                        config_path = Path.home() / '.modan2' / 'config.json'
                        config_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(self.config, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        logger.error(f"Failed to save config: {e}")
                
                def sync(self):
                    """Force save settings to file (alias for save)."""
                    self.save()
            
            self.m_app.settings = SettingsWrapper(self.config, self)

        if not self.init_done:
            self.m_app.remember_geometry = self.config.get("ui", {}).get("remember_geometry", True)
            logger = logging.getLogger(__name__)
            logger.debug(f"READ_SETTINGS - Remember geometry: {self.m_app.remember_geometry}")
            
            if self.m_app.remember_geometry:
                geometry_data = self.config.get("ui", {}).get("window_geometry", {})
                logger.debug(f"READ_SETTINGS - Raw geometry data: {geometry_data}")
                
                # Handle both old list format and new dictionary format
                if isinstance(geometry_data, dict):
                    geometry = geometry_data.get("main_window", [100, 100, 1400, 800])
                elif isinstance(geometry_data, list):
                    geometry = geometry_data
                else:
                    geometry = [100, 100, 1400, 800]
                
                logger.debug(f"READ_SETTINGS - Parsed geometry: {geometry}")
                
                # Ensure all values are integers
                geometry = [int(x) if isinstance(x, (int, float, str)) and str(x).isdigit() else x for x in geometry]
                
                # Get multi-monitor info for debugging
                from PyQt6.QtGui import QGuiApplication
                screens = QGuiApplication.screens()
                primary_screen = QGuiApplication.primaryScreen()
                primary_rect = primary_screen.geometry()
                
                logger.debug(f"READ_SETTINGS - Using saved geometry: x={geometry[0]}, y={geometry[1]}, w={geometry[2]}, h={geometry[3]}")
                logger.debug(f"READ_SETTINGS - Primary monitor size: {primary_rect.width()}x{primary_rect.height()}")
                logger.debug(f"READ_SETTINGS - Number of screens: {len(screens)}")
                
                # Show all screen geometries for debugging
                for i, screen in enumerate(screens):
                    screen_geom = screen.geometry()
                    logger.debug(f"READ_SETTINGS - Screen {i}: {screen_geom.width()}x{screen_geom.height()} at ({screen_geom.x()}, {screen_geom.y()})")
                
                # Set geometry with window manager hints
                from PyQt6.QtCore import Qt
                
                # Store desired position for later enforcement
                self._desired_geometry = QRect(*geometry)
                
                # Set window flags to control positioning behavior
                current_flags = self.windowFlags()
                # Don't let window manager auto-position the window
                self.setWindowFlags(current_flags & ~Qt.WindowType.WindowContextHelpButtonHint)
                
                # Set geometry
                self.setGeometry(QRect(*geometry))
                logger.debug(f"SET_GEOMETRY - Requested: {geometry}, After setGeometry(): {[self.geometry().x(), self.geometry().y(), self.geometry().width(), self.geometry().height()]}")
                
                # Schedule position verification after window is fully shown
                from PyQt6.QtCore import QTimer
                def verify_position():
                    actual = self.geometry()
                    if abs(actual.x() - geometry[0]) > 10 or abs(actual.y() - geometry[1]) > 10:
                        logger.debug(f"POSITION_DRIFT - Expected: ({geometry[0]}, {geometry[1]}), Got: ({actual.x()}, {actual.y()}), Correcting...")
                        self.move(geometry[0], geometry[1])
                        # Final check
                        final = self.geometry()
                        logger.debug(f"POSITION_FINAL - After move(): ({final.x()}, {final.y()})")
                
                QTimer.singleShot(100, verify_position)  # Check sooner
                
                is_maximized_data = self.config.get("ui", {}).get("is_maximized", False)
                # Handle both boolean and dict format
                if isinstance(is_maximized_data, dict):
                    is_maximized = is_maximized_data.get("main_window", False)
                else:
                    is_maximized = is_maximized_data
                
                logger.debug(f"READ_SETTINGS - Is maximized setting: {is_maximized}")
                
                if is_maximized:
                    logger.debug("READ_SETTINGS - Showing maximized window")
                    self.showMaximized()
                else:
                    logger.debug("READ_SETTINGS - Showing normal window")
            else:
                logger.debug("READ_SETTINGS - Remember geometry disabled, using default")
                self.setGeometry(QRect(100, 100, 1400, 800))

        self.m_app.language = self.config.get("language", "en")
        if self.init_done:
            self.update_language()

        plt.rcParams["font.family"] = "serif" 
        plt.rcParams["font.serif"] = ["Times New Roman"] 
        plt.rcParams['mathtext.fontset'] = 'stix' 
        plt.rcParams['font.size'] = 12

    def write_settings(self):
        """Write settings using SettingsWrapper for proper JSON storage"""
        if not hasattr(self.m_app, 'settings') or not hasattr(self.m_app, 'remember_geometry'):
            return
            
        # Save remember geometry setting
        self.m_app.settings.setValue("WindowGeometry/RememberGeometry", self.m_app.remember_geometry)
        
        if self.m_app.remember_geometry:
            logger = logging.getLogger(__name__)
            current_geometry = self.geometry()
            logger.debug(f"WRITE_SETTINGS - Current window geometry: x={current_geometry.x()}, y={current_geometry.y()}, w={current_geometry.width()}, h={current_geometry.height()}")
            logger.debug(f"WRITE_SETTINGS - Is maximized: {self.isMaximized()}")
            
            # Save maximized state
            if self.isMaximized():
                self.m_app.settings.setValue("IsMaximized/MainWindow", True)
                logger.debug("WRITE_SETTINGS - Saved maximized state: True")
            else:
                self.m_app.settings.setValue("IsMaximized/MainWindow", False)
                # Save window geometry
                self.m_app.settings.setValue("WindowGeometry/MainWindow", current_geometry)
                logger.debug(f"WRITE_SETTINGS - Saved geometry: [{current_geometry.x()}, {current_geometry.y()}, {current_geometry.width()}, {current_geometry.height()}]")
        
        # Save language setting
        if hasattr(self.m_app, 'language'):
            self.m_app.settings.setValue("Language", self.m_app.language)

    def update_language(self):
        if False:
            if self.m_app.translator is not None:
                self.m_app.removeTranslator(self.m_app.translator)
                self.m_app.translator = None

            translator = QTranslator()
            translator_path = mu.resource_path("translations/Modan2_{}.qm".format(language))
            if os.path.exists(translator_path):
                translator.load(translator_path)
                self.m_app.installTranslator(translator)
                self.m_app.translator = translator

        self.setWindowTitle("{} v{}".format(self.tr(mu.PROGRAM_NAME), mu.PROGRAM_VERSION))

        self.file_menu.setTitle(self.tr("File"))
        self.edit_menu.setTitle(self.tr("Edit"))
        self.data_menu.setTitle(self.tr("Data"))
        self.help_menu.setTitle(self.tr("Help"))
        self.btnSaveChanges.setText(self.tr("Save Changes"))
        self.btnEditObject.setText(self.tr("Edit Object"))
        self.btnAddObject.setText(self.tr("Add Object"))
        self.btnAddProperty.setText(self.tr("Add Variable"))
        #self.btnSaveAnalysis.setText(self.tr("Save"))
        self.btnAnalysisDetail.setText(self.tr("Analysis Details"))
        self.btnDataExploration.setText(self.tr("Data Exploration"))
        #self.lblSelect.setText(self.tr("Select"))
        #self.rbSelectCells.setText(self.tr("Cells"))
        #self.rbSelectRows.setText(self.tr("Rows"))
        self.analysis_info_widget.update_language()

        return


    def closeEvent(self, event):
        self.write_settings()
        if self.analysis_dialog is not None:
            self.analysis_dialog.close()
        event.accept()

    @pyqtSlot()
    def on_action_edit_preferences_triggered(self):
        #print("edit preferences")
        self.preferences_dialog = PreferencesDialog(self)
        #self.preferences_dialog.setWindowModality(Qt.ApplicationModal)
        self.preferences_dialog.exec()
        self.read_settings()

    @pyqtSlot()
    def on_action_exit_triggered(self):
        self.close()

    @pyqtSlot() 
    def on_action_about_triggered(self):
        # Show version with build number
        version_text = f"v{mu.PROGRAM_VERSION} (Build {mu.PROGRAM_BUILD_NUMBER})"
        
        text = mu.PROGRAM_NAME + " " + version_text + "\n\n"
        text += "Morphometrics made easy\n\n"
        text += "This software is distributed under the terms of the MIT License.\n\n"
        text += mu.PROGRAM_COPYRIGHT + "\n"

        QMessageBox.about(self, "About", text)

        license_text = """
Modan2
Copyright 2023-2024 Jikhan Jung

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

    @pyqtSlot()
    def on_action_analyze_dataset_triggered(self):
        """Handle analyze dataset action using controller"""
        if self.selected_dataset is None:
            show_warning(self, "No dataset selected")
            return
        
        try:
            # Validate dataset using controller
            if not self.controller.validate_dataset_for_analysis(self.selected_dataset):
                return  # Controller will show appropriate error messages
            
            self.analysis_dialog = NewAnalysisDialog(self, self.selected_dataset)
            ret = self.analysis_dialog.exec()
            logger.info("new analysis dialog return value %s", ret)
            
            if ret == 1:
                superimposition_method = self.analysis_dialog.comboSuperimposition.currentText()
                cva_group_by = self.analysis_dialog.comboCvaGroupBy.currentData()
                manova_group_by = self.analysis_dialog.comboManovaGroupBy.currentData()
                analysis_name = self.analysis_dialog.edtAnalysisName.text()
                
                # Use controller for analysis
                self.controller.run_analysis(
                    dataset=self.selected_dataset,
                    analysis_name=analysis_name,
                    superimposition_method=superimposition_method,
                    cva_group_by=cva_group_by,
                    manova_group_by=manova_group_by
                )
        except Exception as e:
            show_error(self, f"Error running analysis: {str(e)}")


    def initUI(self):
        # add tableView and tableWidget to vertical layout
        #self.object_view_2d = LandmarkEditor(self)
        try:
            logger.info("Creating ObjectViewer2D instance...")
            self.object_view_2d = ObjectViewer2D(self)
            logger.info("ObjectViewer2D created successfully")
            self.object_view_2d.set_mode(MODE['VIEW'])
            logger.info("ObjectViewer2D mode set to VIEW")
        except Exception as e:
            logger.error(f"Failed to create ObjectViewer2D: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Initialize 3D viewer as None - will be created on first use (lazy loading)
        logger.info("Setting ObjectViewer3D to lazy loading mode...")
        self.object_view_3d = None
        logger.info("ObjectViewer3D set to lazy loading (will create when needed)")
            
        logger.info("Setting object_view reference...")
        self.object_view = self.object_view_2d
        logger.info("Object view reference set")

        logger.info("Checking dockable_object_view setting...")
        dockable_object_view = False
        logger.info(f"dockable_object_view = {dockable_object_view}")

        if dockable_object_view :
            # Create dock widget for the viewer
            self.viewer_dock = QDockWidget(self.tr("Object Viewer"), self)
            self.viewer_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            self.viewer_dock.setFeatures(QDockWidget.DockWidgetMovable | 
                                    QDockWidget.DockWidgetFloatable |
                                    QDockWidget.DockWidgetClosable)

            # Create container widget for both viewers
            self.viewer_container = QWidget()
            viewer_layout = QVBoxLayout(self.viewer_container)
            viewer_layout.addWidget(self.object_view_2d)
            # 3D viewer will be added to dock layout when first accessed
            viewer_layout.setContentsMargins(0, 0, 0, 0)

            # Set the container as the dock widget's content
            self.viewer_dock.setWidget(self.viewer_container)
            
            # Add dock widget to main window
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.viewer_dock)

        logger.info("Creating table view widgets...")
        self.tableview_widget = QWidget()
        self.tableview_layout = QVBoxLayout()
        self.object_button_widget = QWidget()
        self.object_button_layout = QHBoxLayout()
        self.object_button_widget.setLayout(self.object_button_layout)
        logger.info("Table view widgets created")

        #self.lblSelect = QLabel(self.tr("Select"))
        #self.rbSelectCells = QRadioButton(self.tr("Cells"))
        #self.rbSelectCells.setChecked(True)
        #self.rbSelectCells.clicked.connect(self.on_rbSelectCells_clicked)
        #self.rbSelectRows = QRadioButton(self.tr("Rows"))
        #self.rbSelectRows.clicked.connect(self.on_rbSelectRows_clicked)
        #self.select_layout = QHBoxLayout()
        #self.select_widget = QWidget()
        #self.select_widget.setLayout(self.select_layout)
        #self.select_layout.addWidget(self.lblSelect)
        #self.select_layout.addWidget(self.rbSelectCells)
        #self.select_layout.addWidget(self.rbSelectRows)


        logger.info("Creating button widgets...")
        self.btnSaveChanges = QPushButton(self.tr("Save Changes"))
        self.btnEditObject = QPushButton(self.tr("Edit Object"))
        self.btnAddObject = QPushButton(self.tr("Add Object"))
        self.btnAddProperty = QPushButton(self.tr("Add Variable"))
        logger.info("Button widgets created")
        
        logger.info("Adding buttons to layout...")
        #self.object_button_layout.addWidget(self.select_widget)
        self.object_button_layout.addWidget(self.btnAddObject)
        self.object_button_layout.addWidget(self.btnEditObject)
        self.object_button_layout.addWidget(self.btnAddProperty)
        self.object_button_layout.addWidget(self.btnSaveChanges)
        logger.info("Buttons added to layout")

        logger.info("Setting up table view layout...")
        self.tableview_layout.addWidget(self.tableView)
        #self.tableview_layout.addWidget(self.object_button_widget)
        self.tableview_widget.setLayout(self.tableview_layout)
        logger.info("Table view layout set up")
        
        logger.info("Connecting button signals...")
        self.btnSaveChanges.clicked.connect(self.on_btnSaveChanges_clicked)
        self.btnAddObject.clicked.connect(self.on_action_new_object_triggered)
        self.btnEditObject.clicked.connect(self.on_tableView_doubleClicked)
        self.btnAddProperty.clicked.connect(self.on_action_add_variable_triggered)
        logger.info("Button signals connected")

        logger.info("Creating splitters...")
        self.hsplitter = QSplitter(Qt.Orientation.Horizontal)
        self.vsplitter = QSplitter(Qt.Orientation.Vertical)
        logger.info("Splitters created")

        logger.info("Adding widgets to vsplitter...")
        self.vsplitter.addWidget(self.tableview_widget)
        if not dockable_object_view:
            self.vsplitter.addWidget(self.object_view_2d)
            # 3D viewer will be added to layout when first accessed
        logger.info("Widgets added to vsplitter")

        logger.info("Adding widgets to hsplitter...")
        #self.treeView = MyTreeView()
        self.hsplitter.addWidget(self.treeView)
        self.hsplitter.addWidget(self.vsplitter)
        self.hsplitter.setSizes([300, 800])
        logger.info("Widgets added to hsplitter")
        
        logger.info("Creating analysis view...")
        self.analysis_view = QWidget()
        self.analysis_view_layout = QVBoxLayout()
        self.analysis_view.setLayout(self.analysis_view_layout)
        self.analysis_info_widget = AnalysisInfoWidget(self)
        logger.info("Analysis view created")
        self.analysis_view_layout.addWidget(self.analysis_info_widget)

        self.btnSaveAnalysis = QPushButton(self.tr("Save"))
        self.btnSaveAnalysis.clicked.connect(self.btnSaveAnalysis_clicked)
        self.btnAnalysisDetail = QPushButton(self.tr("Analysis Details"))
        self.btnAnalysisDetail.clicked.connect(self.btnAnalysisDetail_clicked)
        self.btnDataExploration = QPushButton(self.tr("Data Exploration"))
        self.btnDataExploration.clicked.connect(self.btnDataExploration_clicked)
        self.analysis_button_layout = QHBoxLayout()
        self.analysis_button_layout.addWidget(self.btnSaveAnalysis)
        self.analysis_button_layout.addWidget(self.btnAnalysisDetail)
        self.analysis_button_layout.addWidget(self.btnDataExploration)
        self.analysis_button_widget = QWidget()
        self.analysis_button_widget.setLayout(self.analysis_button_layout)
        self.analysis_view_layout.addWidget(self.analysis_button_widget)

        logger.info("Setting central widget...")
        self.setCentralWidget(self.hsplitter)
        logger.info("Central widget set")

        logger.info("Connecting final signals...")
        self.treeView.doubleClicked.connect(self.on_treeView_doubleClicked)
        self.treeView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.treeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.tableView.doubleClicked.connect(self.on_tableView_doubleClicked)
        self.treeView.customContextMenuRequested.connect(self.open_treeview_menu)
        logger.info("Final signals connected")
        
        logger.info("initUI() completed successfully")

    def on_action_cell_selection_triggered(self):
        if self.actionCellSelection.isChecked():
            self.tableView.set_cells_selection_mode()

    def on_action_row_selection_triggered(self):
        if self.actionRowSelection.isChecked():
            self.tableView.set_rows_selection_mode()

    #def on_rbSelectCells_clicked(self):
    #    self.tableView.set_cells_selection_mode()
        
    #def on_rbSelectRows_clicked(self):
    #    self.tableView.set_rows_selection_mode()
        
    def btnAnalysisDetail_clicked(self):
        #self.detail_dialog = DatasetAnalysisDialog(self.parent)
        self.analysis_dialog = DatasetAnalysisDialog(self,self.analysis_info_widget.analysis.dataset)
        self.analysis_dialog.show()


    def btnSaveAnalysis_clicked(self):
        pass

    def btnDataExploration_clicked(self):
        #print("btnExplore_clicked")
        self.exploration_dialog = DataExplorationDialog(self)
        #print("exploration dialog created")
        # get tab text
        tab_text = self.analysis_info_widget.analysis_tab.tabText(self.analysis_info_widget.analysis_tab.currentIndex())
        if tab_text == "PCA":
            group_by = self.analysis_info_widget.comboPcaGroupBy.currentText()
        elif tab_text == "CVA":
            group_by = self.analysis_info_widget.comboCvaGroupBy.currentText()
        elif tab_text == "MANOVA":
            group_by = self.analysis_info_widget.comboManovaGroupBy.currentText()

        #group_by = self.comboCvaGroupBy
        #print("going to call set_analysis")
        self.exploration_dialog.set_analysis(self.analysis_info_widget.analysis, tab_text, group_by)
        #print("going to update chart")
        #print("going to show")
        self.exploration_dialog.show()
        self.exploration_dialog.update_chart()
        #self.exploration_dialog.activateWindow()

    def on_action_add_variable_triggered(self):
        if self.selected_dataset is None:
            return
        text, ok = QInputDialog.getText(self, self.tr('Add Variable'), self.tr('Enter new variable name'), text="")
        if ok:
            self.selected_dataset.add_variablename(text)
            ds = self.selected_dataset
            self.load_dataset()
            # select current dataset
            self.select_dataset(ds)
            self.load_object()

    def on_btnSaveChanges_clicked(self):
        # save object info
        # get object info from tableview
        self.object_model.save_object_info()
        self.object_model.resetColors()
        self.data_changed = False
        self.btnSaveChanges.setEnabled(False)
        #indexes = self.tableView.selectedIndexes()

    @pyqtSlot()
    def on_action_delete_object_triggered(self):
        ret = QMessageBox.warning(self, self.tr("Warning"), self.tr("Are you sure to delete the selected object?"), QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No:
            return
        
        selected_object_list = self.get_selected_object_list()
        if selected_object_list:
            for object in selected_object_list:
                object.delete_instance()
            dataset = self.selected_dataset
            self.reset_treeView()
            self.load_dataset()
            self.reset_tableView()
            self.select_dataset(dataset)

    def open_treeview_menu(self, position):
        indexes = self.treeView.selectedIndexes()
        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            action_add_dataset = QAction(self.tr("Add child dataset"))
            action_add_dataset.triggered.connect(self.on_action_new_dataset_triggered)
            action_add_object = QAction(self.tr("Add object"))
            action_add_object.triggered.connect(self.on_action_new_object_triggered)
            action_add_analysis = QAction(self.tr("Add analysis"))
            action_add_analysis.triggered.connect(self.on_action_analyze_dataset_triggered)
            action_explore_data = QAction(self.tr("Explore data"))
            action_explore_data.triggered.connect(self.on_action_explore_data_triggered)
            action_delete_analysis = QAction(self.tr("Delete analysis"))
            action_delete_analysis.triggered.connect(self.on_action_delete_analysis_triggered)
            action_refresh_tree = QAction(self.tr("Reload"))
            action_refresh_tree.triggered.connect(self.load_dataset)

            # get item
            item = self.dataset_model.itemFromIndex(index)
            obj = item.data()

            menu = QMenu()
            if isinstance(obj, MdDataset):
                self.selected_dataset = obj
                menu.addAction(action_add_dataset)
                menu.addAction(action_add_object)
                menu.addAction(action_add_analysis)
                menu.addAction(self.actionExport)
                menu.addAction(action_refresh_tree)
            elif isinstance(obj, MdAnalysis):                
                #menu.addAction(action_explore_data)
                menu.addAction(action_delete_analysis)
                menu.addAction(action_refresh_tree)
            menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def on_action_delete_analysis_triggered(self):
        ret = QMessageBox.warning(self, self.tr("Warning"), self.tr("Are you sure to delete the selected analysis?"), QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No:
            return
        selected_indexes = self.treeView.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return
        item = self.dataset_model.itemFromIndex(selected_indexes[0])
        analysis = item.data()
        analysis.delete_instance()
        self.load_dataset()

    def on_action_explore_data_triggered(self):
        self.exploration_dialog = DataExplorationDialog(self)
        self.exploration_dialog.set_analysis(self.selected_analysis)
        self.exploration_dialog.show()

    @pyqtSlot()
    def on_action_import_dataset_triggered(self):
        """Handle import dataset action using controller"""
        self.dlg = ImportDatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.dlg.exec()
        # Controller signals will handle UI updates automatically        

    @pyqtSlot()
    def on_action_export_dataset_triggered(self):
        """Handle export dataset action using controller"""
        if self.selected_dataset is None:
            return
        try:
            self.dlg = ExportDatasetDialog(self)
            self.dlg.setModal(True)
            self.dlg.set_dataset(self.selected_dataset)
            self.dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.dlg.exec()
        except Exception as e:
            show_error(self, f"Error exporting dataset: {str(e)}")

    @pyqtSlot()
    def on_action_new_dataset_triggered(self):
        """Handle new dataset action using controller"""
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)
        if self.selected_dataset:
            try:
                self.selected_dataset = self.selected_dataset.get_by_id(self.selected_dataset.id)
                self.dlg.set_parent_dataset(self.selected_dataset)
            except DoesNotExist:
                logger = logging.getLogger(__name__)
                logger.error(f"Selected dataset {self.selected_dataset.id} no longer exists")
                self.selected_dataset = None
                self.dlg.set_parent_dataset(None)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error accessing selected dataset: {e}")
                self.dlg.set_parent_dataset(None)
        else:
            self.dlg.set_parent_dataset(None)

        ret = self.dlg.exec()
        # Controller signals will handle the UI updates automatically
        self.load_dataset()
        self.reset_tableView()


    def get_selected_dataset(self):
        selected_indexes = self.treeView.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return None
        else:
            selected_dataset_list = []
            for index in selected_indexes:
                item = self.dataset_model.itemFromIndex(index)
                dataset = item.data()
                selected_dataset_list.append(dataset)
            return selected_dataset_list[0]

    @pyqtSlot()
    def on_treeView_clicked(self,event):
        event.accept()
        self.selected_dataset = self.get_selected_dataset()
        if self.selected_dataset is None:
            self.actionNewObject.setEnabled(False)
            self.actionExport.setEnabled(False)
            self.actionAnalyze.setEnabled(False)
        else:
            self.actionNewObject.setEnabled(True)
            self.actionExport.setEnabled(True)
            self.actionAnalyze.setEnabled(True)
            self.load_object()

    @pyqtSlot()
    def on_treeView_doubleClicked(self):
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)

        #print("wireframe 1:", self.selected_dataset.wireframe)
        self.selected_dataset = self.selected_dataset.get_by_id(self.selected_dataset.id)
        #print("wireframe 2:", self.selected_dataset.wireframe)
        self.selected_dataset.unpack_wireframe()

        self.dlg.set_dataset( self.selected_dataset )
        ret = self.dlg.exec()
        if ret == 0:
            return
        elif ret == 1:
            if self.selected_dataset is None: #deleted
                self.load_dataset()
                self.reset_tableView()
            else:
                #self.dlg.set_parent_dataset( self.selected_dataset )

                dataset = self.selected_dataset
                self.reset_treeView()
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(dataset)

    def select_dataset(self,dataset,node=None):
        if dataset is None:
            return
        if node is None:
            node = self.dataset_model.invisibleRootItem()   

        for i in range(node.rowCount()):
            item = node.child(i,0)
            if item.data() == dataset:
                self.treeView.setCurrentIndex(item.index())
                break
            self.select_dataset(dataset,node.child(i,0))

    @pyqtSlot()
    def on_action_new_object_triggered(self):
        """Handle new object action using controller"""
        logger = logging.getLogger(__name__)
        logger.debug(f"selected_dataset = {self.selected_dataset}")
        if not self.selected_dataset:
            return
        try:
            # Convert ID to dataset object if needed
            if isinstance(self.selected_dataset, int):
                try:
                    dataset = MdDataset.get_by_id(self.selected_dataset)
                except DoesNotExist:
                    logger.error(f"Dataset {self.selected_dataset} no longer exists")
                    return
            else:
                dataset = self.selected_dataset
                
            logger.debug(f"dataset object = {dataset}")
            
            # Ensure controller knows about selected dataset
            self.controller.set_current_dataset(dataset)
            new_object = self.controller.create_object()
            if new_object is None:
                return  # Error already handled by controller
            logger.debug(f"new_object = {new_object}")
            
            self.dlg = ObjectDialog(self)
            self.dlg.set_dataset(dataset)
            self.dlg.set_object(new_object)
            ret = self.dlg.exec()
            if ret != 0:
                # Object was saved in dialog, UI will update via signals
                pass
        except Exception as e:
            show_error(self, f"Error creating new object: {str(e)}")

    @pyqtSlot()
    def on_tableView_doubleClicked(self):
        if self.selected_object is None:
            logger = logging.getLogger(__name__)
            logger.warning("no object selected")
            return
        self.dlg = ObjectDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset(self.selected_dataset)
        self.dlg.set_object( self.selected_object )
        self.dlg.set_tableview(self.tableView)
        ret = self.dlg.exec()
        if ret == 0:
            return
        elif ret == 1:
            if self.dlg.object_deleted:
                dataset = self.selected_dataset
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(dataset)
                self.load_object()
            return
        dataset = self.selected_dataset
        self.reset_treeView()
        self.load_dataset()
        self.reset_tableView()
        self.select_dataset(dataset)
        self.load_object()
        self.object_view.clear_object()

    def reset_treeView(self):
        self.dataset_model = QStandardItemModel()
        self.treeView.setModel(self.dataset_model)
        self.treeView.setHeaderHidden(True)
        self.dataset_selection_model = self.treeView.selectionModel()
        self.dataset_selection_model.selectionChanged.connect(self.on_dataset_selection_changed)
        header = self.treeView.header()
        self.treeView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.treeView.setDragEnabled(True)
        self.treeView.setAcceptDrops(True)
        self.treeView.setDropIndicatorShown(True)
        self.treeView.dropEvent = self.dropEvent
        self.treeView.dragEnterEvent = self.treeView_drag_enter_event
        self.treeView.dragLeaveEvent = self.treeView_drag_leave_event
        self.treeView.dragMoveEvent = self.treeView_drag_move_event

    #def treeView_drag_enter_event(self, event):
    #    event.accept()
    def treeView_drag_enter_event(self, event):
        event.accept()
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
            QApplication.setOverrideCursor(Qt.CursorShape.DragCopyCursor)
        else:
            QApplication.setOverrideCursor(Qt.CursorShape.DragMoveCursor)

    def treeView_drag_leave_event(self, event):
        event.accept()

    def treeView_drag_move_event(self, event):
        event.accept()
        target_index = self.treeView.indexAt(event.pos())
        target_item = self.dataset_model.itemFromIndex(target_index)
        if not target_item:
            return
        target_dataset = target_item.data()
        return

    def treeView_drag_move_event(self, event):
        event.accept()
        target_index = self.treeView.indexAt(event.pos())
        target_item = self.dataset_model.itemFromIndex(target_index)
        if not target_item:
            return
        target_dataset = target_item.data()

        # Update cursor based on modifier keys
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
            QApplication.changeOverrideCursor(Qt.CursorShape.DragCopyCursor)
        else:
            QApplication.changeOverrideCursor(Qt.CursorShape.DragMoveCursor)
        return

    def updateCursor(self, shift_pressed):
        if shift_pressed:
            QApplication.setOverrideCursor(Qt.CursorShape.DragCopyCursor)
        else:
            QApplication.setOverrideCursor(Qt.CursorShape.ClosedHandCursor)

    def dropEvent(self, event):
        if event.source() == self.treeView:
            target_index=self.treeView.indexAt(event.pos())
            target_item = self.dataset_model.itemFromIndex(target_index)
            target_dataset = target_item.data()

            source_index = event.source().currentIndex()
            source_item = self.dataset_model.itemFromIndex(source_index)
            source_dataset = source_item.data()

            source_dataset.parent = target_dataset
            source_dataset.save()
            self.load_dataset()
            self.reset_tableView()

        elif event.source() == self.tableView:
            shift_clicked = False
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.ShiftModifier:
                shift_clicked = True

            target_index=self.treeView.indexAt(event.pos())
            target_item = self.dataset_model.itemFromIndex(target_index)
            target_dataset = target_item.data()
            selected_object_list = self.get_selected_object_list()
            source_dataset = None
            total_count = len(selected_object_list)
            current_count = 0

            self.progress_dialog = ProgressDialog(self)
            self.progress_dialog.setModal(True)
            if shift_clicked:
                label_text = "Moving {} objects...".format(total_count)
            else:
                label_text = "Copying {} objects...".format(total_count)
            self.progress_dialog.lbl_text.setText(label_text)
            self.progress_dialog.pb_progress.setValue(0)
            self.progress_dialog.show()


            for source_object in selected_object_list:
                source_dataset = source_object.dataset
                current_count += 1
                self.progress_dialog.pb_progress.setValue(int((current_count/float(total_count))*100))
                self.progress_dialog.update()
                QApplication.processEvents()
                if self.progress_dialog.stop_progress:
                    break

                if source_object.dataset.dimension == target_dataset.dimension:
                    # if shift is pressed, move instead of copy
                    if shift_clicked:
                        source_object.change_dataset(target_dataset)
                        source_object.save()
                    else:
                        # copy object
                        new_object = source_object.copy_object(target_dataset)
                        new_object.save()
                        if source_object.has_image():
                            new_image = source_object.get_image().copy_image(new_object)
                            new_image.save()
                        elif source_object.has_threed_model():
                            new_model = source_object.get_threed_model().copy_threed_model(new_object)
                            new_model.save()
                            
                else:
                    QMessageBox.warning(self, self.tr("Warning"), self.tr("Dimension mismatch"))
                    break
            self.progress_dialog.close()

            if source_dataset is not None:
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(source_dataset)
        elif event.mimeData().hasUrls():
            file_path = event.mimeData().text()
            file_path = mu.process_dropped_file_name(file_path)
            self.import_dialog = ImportDatasetDialog(self)
            self.import_dialog.setModal(True)
            self.import_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.import_dialog.open_file2(file_path)
            self.import_dialog.exec()
            self.load_dataset()

    def get_selected_object_list(self):
        selected_indexes = self.tableView.selectionModel().selectedIndexes()
        if len(selected_indexes) == 0:
            return None

        new_index_list = []
        model = selected_indexes[0].model()
        if hasattr(model, 'mapToSource'):
            for index in selected_indexes:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
            selected_indexes = new_index_list

        selected_object_list = []
        for index in selected_indexes:
            object_id = self.object_model._data[index.row()][0]["value"]

            object_id = int(object_id)
            object = MdObject.get_by_id(object_id)
            if object is not None and object not in selected_object_list:
                selected_object_list.append(object)

        return selected_object_list

    def on_object_data_changed(self):
        self.data_changed = True
        self.btnSaveChanges.setEnabled(True)

    def reset_tableView(self):
        self.btnSaveChanges.setEnabled(False)
        self.btnAddObject.setEnabled(False)
        self.btnAddProperty.setEnabled(False)
        self.btnEditObject.setEnabled(False)
        self.object_model = MdTableModel()
        self.object_model.dataChangedCustomSignal.connect(self.on_object_data_changed)
        header_labels = ["ID", "Seq.", "Name", "Count", "CSize"]
        if self.selected_dataset is not None:
            self.selected_dataset.unpack_variablename_str()
            if self.selected_dataset.variablename_list is not None and len( self.selected_dataset.variablename_list ) > 0:
                header_labels.extend( self.selected_dataset.variablename_list )
            if self.selected_dataset.dimension == 2:
                self.object_view = self.object_view_2d
                self.object_view_2d.show()
                # Hide 3D viewer if it exists
                if self.object_view_3d is not None:
                    self.object_view_3d.hide()
            else:
                # Create 3D viewer lazily when needed
                self.object_view = self.get_object_view_3d()
                
                # Check if 3D viewer was actually created or fell back to 2D
                import sys
                if getattr(sys, 'frozen', False) and self.object_view == self.object_view_2d:
                    # Show warning message to user that 3D is not available
                    self.statusBar.showMessage("3D viewer not available in this build - displaying in 2D mode", 5000)
                
                self.object_view_2d.hide()
                self.object_view.show()
        self.object_model.setHorizontalHeader( header_labels )
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.object_model)
        self.tableView.setModel(self.proxy_model)        
        header = self.tableView.horizontalHeader()    
        header.resizeSection(1,200)
        header.setDefaultSectionSize(15)
        self.object_selection_model = self.tableView.selectionModel()
        self.object_selection_model.selectionChanged.connect(self.on_object_selection_changed)

        self.tableView.setDragEnabled(True)
        self.tableView.setAcceptDrops(True)
        self.tableView.setDropIndicatorShown(True)
        self.tableView.dropEvent = self.tableView_drop_event
        self.tableView.dragEnterEvent = self.tableView_drag_enter_event
        self.tableView.dragMoveEvent = self.tableView_drag_move_event
        self.tableView.setSortingEnabled(True)
        self.tableView.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.clear_object_view()

    def tableView_drop_event(self, event):
        logger = logging.getLogger(__name__)
        logger.debug(f"tableview drop event: {event.mimeData().text()}")
        if self.selected_dataset is None:
            return
        
        if event.mimeData().text() == "":
            return
        file_name_list = event.mimeData().text().strip().split("\n")
        if len(file_name_list) == 0:
            return

        logger.debug(f"file name list: {file_name_list}")

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        total_count = len(file_name_list)
        current_count = 0
        self.progress_dialog = ProgressDialog(self)
        self.progress_dialog.setModal(True)
        if self.selected_dataset.dimension == 3:
            label_text = self.tr("Importing 3d model files...")
        else:
            label_text = self.tr("Importing image files...")
        self.progress_dialog.lbl_text.setText(label_text)
        self.progress_dialog.pb_progress.setValue(0)
        self.progress_dialog.show()

        for file_name in file_name_list:
            current_count += 1
            self.progress_dialog.pb_progress.setValue(int((current_count/float(total_count))*100))
            self.progress_dialog.update()
            QApplication.processEvents()

            file_name = mu.process_dropped_file_name(file_name)

            ext = file_name.split('.')[-1].lower()
            if ext in mu.IMAGE_EXTENSION_LIST:
                if self.selected_dataset.dimension != 2:
                    QMessageBox.warning(self, self.tr("Warning"), self.tr("Dimension mismatch."))
                    break
                obj = self.selected_dataset.add_object(object_name=Path(file_name).stem)
                obj.save()
                img = obj.add_image(file_name)
                img.save()

            elif ext in mu.MODEL_EXTENSION_LIST:
                if self.selected_dataset.dimension != 3:
                    QMessageBox.warning(self, self.tr("Warning"), self.tr("Dimension mismatch."))
                    break
                obj = self.selected_dataset.add_object(object_name=Path(file_name).stem)
                obj.save()
                mdl = obj.add_threed_model(file_name)
                mdl.save()

            elif os.path.isdir(file_name):
                self.statusBar.showMessage(self.tr("Cannot process directory..."),2000)

            else:
                self.statusBar.showMessage(self.tr("Nothing to import."),2000)

            self.load_object()

        self.progress_dialog.close()

        dataset = self.selected_dataset
        self.load_dataset()
        self.reset_tableView()
        self.select_dataset(dataset)
        self.load_object()
        QApplication.restoreOverrideCursor()

    def tableView_drag_enter_event(self, event):
        event.accept()
        return
        logger = logging.getLogger(__name__)
        logger.debug(f"drag enter: {event.mimeData().text()}")
        file_name_list = event.mimeData().text().strip().split("\n")
        logger.debug(f"file name list: {file_name_list}")
        ext = file_name_list[0].split('.')[-1].lower()
        logger.debug(f"ext: {ext}")
        if ext in ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']:
            logger.debug("image file")
            logger.debug(f"source: {event.source()}")
            logger.debug(f"proposed action: {event.proposedAction()}")
            logger.debug(f"drop action: {event.dropAction()}")
            logger.debug(f"possible action: {int(event.possibleActions())}")
            logger.debug(f"kinds of drop actions: {Qt.DropAction.CopyAction}, {Qt.DropAction.MoveAction}, {Qt.DropAction.LinkAction}, {Qt.DropAction.ActionMask}, {Qt.DropAction.TargetMoveAction}")
            #event.acceptProposedAction()
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()


    def tableView_drag_move_event(self, event):
        self.copy_cursor = QCursor(Qt.CursorShape.DragCopyCursor)
        self.move_cursor = QCursor(Qt.CursorShape.DragMoveCursor)
        #print("table view drag move event")
        #print("drag move", event.mimeData().text())

        # Check if Shift is pressed
        modifiers = QApplication.queryKeyboardModifiers()
        if bool(modifiers & Qt.KeyboardModifier.ShiftModifier):
            logger = logging.getLogger(__name__)
            logger.debug("copy cursor")
            #QApplication.restoreOverrideCursor()
            #QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor) 
            #QApplication.changeOverrideCursor(self.copy_cursor)
        else:
            logger = logging.getLogger(__name__)
            logger.debug("move cursor")
            #QApplication.restoreOverrideCursor()
            #QApplication.setOverrideCursor(Qt.CursorShape.ClosedHandCursor) 
            #QApplication.changeOverrideCursor(self.move_cursor)

        event.accept()

    def _tableView_drag_move_event(self, event):
        logger = logging.getLogger(__name__)
        logger.debug("table view drag move event")
        logger.debug(f"drag move: {event.mimeData().text()}")
        event.accept()
        return
        logger.debug(f"drag move: {event.mimeData().text()}")
        file_name_list = event.mimeData().text().strip().split("\n")
        logger.debug(f"file name list: {file_name_list}")
        ext = file_name_list[0].split('.')[-1].lower()
        logger.debug(f"ext: {ext}")
        if ext in ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']:
            logger.debug("image file")
            logger.debug(f"source: {event.source()}")
            logger.debug(f"proposed action: {event.proposedAction()}")
            logger.debug(f"drop action: {event.dropAction()}")
            logger.debug(f"possible action: {int(event.possibleActions())}")
            print("kinds of drop actions:", Qt.DropAction.CopyAction, Qt.DropAction.MoveAction, Qt.DropAction.LinkAction, Qt.DropAction.ActionMask, Qt.DropAction.TargetMoveAction)
            #event.acceptProposedAction()
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def reset_views(self):
        self.reset_treeView()
        self.reset_tableView()
    
    def load_dataset(self):
        logger.info("Starting load_dataset()...")
        logger.info("Clearing dataset model...")
        self.dataset_model.clear()
        self.selected_dataset = None
        
        logger.info("Querying datasets from database...")
        all_record = MdDataset.filter(parent=None)
        record_count = len(list(all_record))
        logger.info(f"Found {record_count} datasets to load")
        
        all_record = MdDataset.filter(parent=None)  # Re-query since we consumed the iterator
        for i, rec in enumerate(all_record):
            logger.info(f"Processing dataset {i+1}/{record_count}: {rec.dataset_name}")
            
            logger.info(f"Unpacking wireframe for dataset: {rec.dataset_name}")
            rec.unpack_wireframe()
            logger.info(f"Wireframe unpacked successfully for: {rec.dataset_name}")
            
            object_count = rec.object_list.count()
            item1 = QStandardItem(rec.dataset_name + " (" + str(object_count) + ")")
            logger.info(f"Dataset {rec.dataset_name} has {object_count} objects")
            
            if rec.dimension == 2:
                item1.setIcon(QIcon(ICON_CONSTANTS['dataset_2d']))
            else:
                item1.setIcon(QIcon(ICON_CONSTANTS['dataset_3d']))
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            
            self.dataset_model.appendRow([item1,item2])
            
            analysis_count = rec.analyses.count()
            if analysis_count > 0:
                logger.info(f"Loading {analysis_count} analyses for dataset: {rec.dataset_name}")
                self.load_analysis(item1,rec)
                
            children_count = rec.children.count()
            if children_count > 0:
                logger.info(f"Loading {children_count} subdatasets for: {rec.dataset_name}")
                self.load_subdataset(item1,item1.data())
                
        logger.info("Expanding tree view...")
        self.treeView.expandAll()
        logger.info("Hiding tree view column 1...")
        self.treeView.hideColumn(1)
        logger.info("load_dataset() completed successfully")


    def load_analysis(self, parent_item, dataset):
        all_record = MdAnalysis.filter(dataset=dataset)
        for rec in all_record:
            item1 = QStandardItem(rec.analysis_name)
            item1.setIcon(QIcon(ICON_CONSTANTS['analysis']))
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            parent_item.appendRow([item1,item2])

    def load_subdataset(self, parent_item, dataset):
        all_record = MdDataset.filter(parent=dataset)
        for rec in all_record:
            rec.unpack_wireframe()
            item1 = QStandardItem(rec.dataset_name + " (" + str(rec.object_list.count()) + ")")
            if rec.dimension == 2:
                item1.setIcon(QIcon(ICON_CONSTANTS['dataset_2d'])) 
            else:
                item1.setIcon(QIcon(ICON_CONSTANTS['dataset_3d']))
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            parent_item.appendRow([item1,item2])#,item3] )
            if rec.analyses.count() > 0:
                self.load_analysis(item1,rec)
            if rec.children.count() > 0:
                self.load_subdataset(item1,item1.data())

    def on_dataset_selection_changed(self, selected, deselected):
        if self.data_changed:
            ret = QMessageBox.warning(self, self.tr("Warning"), self.tr("Data has been changed. Do you want to save?"), QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if ret == QMessageBox.Yes:
                self.on_btnSaveChanges_clicked()
            elif ret == QMessageBox.Cancel:
                # cancel selection change by selecting deselected
                self.treeView.selectionModel().selectionChanged.disconnect(self.on_dataset_selection_changed)
                self.treeView.selectionModel().clearSelection()
                self.treeView.selectionModel().select(deselected, QItemSelectionModel.Select)
                self.treeView.selectionModel().selectionChanged.connect(self.on_dataset_selection_changed)
                return
            else:
                self.data_changed = False
            
        indexes = selected.indexes()
        if indexes:
            self.object_model.clear()
            item1 =self.dataset_model.itemFromIndex(indexes[0])
            obj = item1.data()
            if isinstance(obj, MdDataset):
                self.selected_dataset = obj
                self.load_object()
                if self.hsplitter.widget(1) != self.vsplitter:
                    self.hsplitter.replaceWidget(1,self.vsplitter)                
                self.actionAnalyze.setEnabled(True)
                self.actionNewObject.setEnabled(True)
                self.actionExport.setEnabled(True)
            elif isinstance(obj, MdAnalysis):
                self.selected_analysis = obj
                if self.hsplitter.widget(1) != self.analysis_view:
                    self.hsplitter.replaceWidget(1,self.analysis_view)
                self.analysis_info_widget.set_analysis(self.selected_analysis)
                self.analysis_info_widget.show_analysis_result()
        else:
            self.actionAnalyze.setEnabled(False)
            self.actionNewObject.setEnabled(False)
            self.actionExport.setEnabled(False)

    def load_object(self):
        self.object_model.clear()
        self.reset_tableView()
        self.clear_object_view()
        if self.selected_dataset is None:
            return

        self.btnEditObject.setEnabled(False)
        self.btnAddProperty.setEnabled(True)
        self.btnAddObject.setEnabled(True)
        self.btnSaveChanges.setEnabled(False)

        rowdata_list = []
        for idx, obj in enumerate(self.selected_dataset.object_list):
            seq = obj.sequence
            if seq is None:
                seq = idx + 1
                obj.sequence = seq
                obj.save()
            row_data = [ obj.id, seq, obj.object_name, obj.count_landmarks(), obj.get_centroid_size()]

            if len(self.selected_dataset.variablename_list) > 0:
                variable_list = obj.unpack_variable()
                for idx,prop in enumerate(self.selected_dataset.variablename_list):
                    if idx < len(variable_list):
                        item = variable_list[idx]
                    else:
                        item = ''
                    row_data.append(item)
            rowdata_list.append( row_data )
        self.object_model.appendRows(rowdata_list)

    def on_object_selection_changed(self, selected, deselected):
        selected_object_list = self.get_selected_object_list()
        if selected_object_list is None or len(selected_object_list) != 1:
            self.btnEditObject.setEnabled(False)
            return

        self.btnEditObject.setEnabled(True)
        object_id = selected_object_list[0].id
        self.selected_object = MdObject.get_by_id(object_id)
        self.selected_object.unpack_landmark()
        self.show_object(self.selected_object)

    def show_object(self, obj):
        self.object_view.clear_object()
        self.object_view.landmark_list = copy.deepcopy(obj.landmark_list)
        self.object_view.set_object(obj)
        self.object_view.read_only = True
        self.object_view.update()

    def clear_object_view(self):
        self.object_view.clear_object()


''' 
How to make an exe file

pyinstaller --name "Modan2_v0.1.4_20250828.exe" --onefile --noconsole --add-data "icons/*.png;icons" --add-data "translations/*.qm;translations" --add-data "migrations/*;migrations" --icon="icons/Modan2_2.png" Modan2.py
pyinstaller --onedir --noconsole --add-data "icons/*.png;icons" --add-data "translations/*.qm;translations" --add-data "migrations/*;migrations" --icon="icons/Modan2_2.png" --noconfirm Modan2.py
#--upx-dir=/path/to/upx

for MacOS
pyinstaller --onefile --noconsole --add-data "icons/*.png:icons" --add-data "translations/*.qm:translations" --add-data "migrations/*:migrations" --icon="icons/Modan2_2.png" Modan2.py
pyinstaller --onedir --noconsole --add-data "icons/*.png:icons" --add-data "translations/*.qm:translations" --add-data "migrations/*:migrations" --icon="icons/Modan2_2.png" --noconfirm Modan2.py

pylupdate5 Modan2.py ModanComponents.py ModanDialogs.py -ts translations/Modan2_en.ts
pylupdate5 Modan2.py ModanComponents.py ModanDialogs.py -ts translations/Modan2_ko.ts
pylupdate5 Modan2.py ModanComponents.py ModanDialogs.py -ts translations/Modan2_ja.ts

linguist
'''