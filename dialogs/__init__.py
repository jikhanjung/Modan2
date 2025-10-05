"""Modan2 Dialog Modules.

This package contains all dialog classes for the application.
During Phase 2 refactoring, dialogs are being migrated from ModanDialogs.py
to individual module files.
"""

# Base dialog
# Migrated dialogs
# Re-export widgets from components.widgets for backward compatibility
from components.widgets import DatasetOpsViewer, PicButton
from dialogs.analysis_dialog import NewAnalysisDialog
from dialogs.analysis_result_dialog import AnalysisResultDialog
from dialogs.base_dialog import BaseDialog
from dialogs.calibration_dialog import CalibrationDialog
from dialogs.data_exploration_dialog import DataExplorationDialog
from dialogs.dataset_analysis_dialog import DatasetAnalysisDialog
from dialogs.dataset_dialog import DatasetDialog
from dialogs.export_dialog import ExportDatasetDialog
from dialogs.import_dialog import ImportDatasetDialog
from dialogs.object_dialog import ObjectDialog
from dialogs.preferences_dialog import PreferencesDialog
from dialogs.progress_dialog import ProgressDialog

# All dialogs have been migrated from ModanDialogs.py!

__all__ = [
    # Base
    "BaseDialog",
    # Original dialogs (to be migrated)
    "ProgressDialog",
    "CalibrationDialog",
    "DatasetDialog",
    "ObjectDialog",
    "NewAnalysisDialog",
    "AnalysisResultDialog",
    "DataExplorationDialog",
    "DatasetAnalysisDialog",
    "ExportDatasetDialog",
    "ImportDatasetDialog",
    "PreferencesDialog",
    "DatasetOpsViewer",
]
