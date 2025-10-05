"""Modan2 Dialog Modules.

This package contains all dialog classes for the application.
During Phase 2 refactoring, dialogs are being migrated from ModanDialogs.py
to individual module files.
"""

# Base dialog
# Migrated dialogs
from dialogs.analysis_dialog import NewAnalysisDialog
from dialogs.base_dialog import BaseDialog
from dialogs.calibration_dialog import CalibrationDialog
from dialogs.export_dialog import ExportDatasetDialog
from dialogs.import_dialog import ImportDatasetDialog
from dialogs.progress_dialog import ProgressDialog

# TODO: Gradually migrate remaining dialogs from ModanDialogs.py
# Temporary re-exports from original ModanDialogs.py until migration complete
from ModanDialogs import (
    AnalysisResultDialog,
    DataExplorationDialog,
    DatasetAnalysisDialog,
    DatasetDialog,
    DatasetOpsViewer,
    ObjectDialog,
    PreferencesDialog,
)

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
