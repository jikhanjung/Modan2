"""Analysis Result Dialog for displaying dataset analysis results."""

import logging

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QApplication, QSplitter

import MdUtils as mu
from dialogs.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class AnalysisResultDialog(BaseDialog):
    """Dialog for displaying dataset analysis results.

    This is a placeholder dialog that sets up the basic structure for
    analysis result visualization. The actual analysis UI is implemented
    in other specialized dialogs (DataExplorationDialog, DatasetAnalysisDialog).

    Features:
    - Window geometry management
    - Plot color and marker preferences
    - Object shape management
    - Horizontal splitter layout
    """

    def __init__(self, parent):
        """Initialize analysis result dialog.

        Args:
            parent: Parent window
        """
        super().__init__(parent, title=self.tr("Modan2 - Dataset Analysis"))
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.parent = parent
        self.m_app = QApplication.instance()

        # Preferences
        self.remember_geometry = True
        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        self.color_list = self.default_color_list[:]
        self.marker_list = mu.MARKER_LIST[:]
        self.plot_size = "medium"

        # Analysis data
        self.ds_ops = None
        self.object_hash = {}
        self.shape_list = []
        self.shape_name_list = []

        # Load settings and initialize
        self.read_settings()
        self.initialize_UI()

        # Create main layout
        self.main_hsplitter = QSplitter(Qt.Horizontal)

    def initialize_UI(self):
        """Initialize UI components.

        Note:
            This is a placeholder method. Subclasses should override this
            to implement specific UI initialization.
        """
        pass

    def read_settings(self):
        """Read dialog settings from application settings."""
        if hasattr(self.m_app, "settings"):
            self.remember_geometry = mu.value_to_bool(
                self.m_app.settings.value("WindowGeometry/RememberGeometry", True)
            )
            if self.remember_geometry:
                self.setGeometry(
                    self.m_app.settings.value("WindowGeometry/AnalysisResultDialog", QRect(100, 100, 1400, 800))
                )
            else:
                self.setGeometry(QRect(100, 100, 1400, 800))

    def write_settings(self):
        """Save dialog settings to application settings."""
        if hasattr(self.m_app, "settings") and self.remember_geometry:
            self.m_app.settings.setValue("WindowGeometry/AnalysisResultDialog", self.geometry())

    def closeEvent(self, event):
        """Handle dialog close event.

        Args:
            event: QCloseEvent
        """
        self.write_settings()
        event.accept()
