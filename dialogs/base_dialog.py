"""Base dialog class with common functionality.

This module provides the BaseDialog class that serves as the foundation
for all Modan2 dialog windows.
"""

import logging
from collections.abc import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QHBoxLayout, QMessageBox, QProgressBar, QPushButton

import MdUtils as mu

logger = logging.getLogger(__name__)


def load_color_marker_lists(settings, color_list, default_color_list, marker_list):
    """Load per-index data-point colours and markers from settings, in place.

    Shared by the QDialog-based plot dialogs (DataExploration / DatasetAnalysis) that
    can't inherit BaseDialog's methods but still duplicated these two loops.
    """
    for i in range(len(color_list)):
        color_list[i] = settings.value("DataPointColor/" + str(i), default_color_list[i])
    for i in range(len(marker_list)):
        marker_list[i] = settings.value("DataPointMarker/" + str(i), marker_list[i])


class BaseDialog(QDialog):
    """Base class for all Modan2 dialogs.

    Provides common functionality:
    - Progress bar handling
    - Error/warning/info message display
    - Wait cursor management
    - Standard button layout creation
    """

    def __init__(self, parent: QDialog | None = None, title: str = ""):
        """Initialize the base dialog.

        Args:
            parent: Parent widget
            title: Window title
        """
        super().__init__(parent)
        if title:
            self.setWindowTitle(title)
        self.progress_bar: QProgressBar | None = None

    def _restore_geometry(self, geometry_key, default_rect, move_offset=None):
        """Restore window geometry from settings (shared read_settings helper).

        Sets ``self.remember_geometry`` from ``WindowGeometry/RememberGeometry``, then
        either restores the saved geometry for ``geometry_key`` or falls back to
        ``default_rect`` — moved by ``move_offset`` (a QPoint) relative to the parent
        when given.
        """
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry:
            self.setGeometry(self.m_app.settings.value(geometry_key, default_rect))
        else:
            self.setGeometry(default_rect)
            if move_offset is not None:
                self.move(self.parent.pos() + move_offset)

    def show_error(self, message: str, title: str = "Error") -> None:
        """Display error message dialog.

        Args:
            message: Error message to display
            title: Dialog title
        """
        QMessageBox.critical(self, title, message)
        logger.error(f"{title}: {message}")

    def show_warning(self, message: str, title: str = "Warning") -> None:
        """Display warning message dialog.

        Args:
            message: Warning message to display
            title: Dialog title
        """
        QMessageBox.warning(self, title, message)
        logger.warning(f"{title}: {message}")

    def show_info(self, message: str, title: str = "Information") -> None:
        """Display information message dialog.

        Args:
            message: Information message to display
            title: Dialog title
        """
        QMessageBox.information(self, title, message)
        logger.info(f"{title}: {message}")

    def set_progress(self, value: int, maximum: int = 100) -> None:
        """Update progress bar.

        Args:
            value: Current progress value
            maximum: Maximum progress value
        """
        if self.progress_bar:
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(value)

    def with_wait_cursor(self, func: Callable) -> object:
        """Execute function with wait cursor.

        Args:
            func: Function to execute

        Returns:
            Return value from func
        """
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            return func()
        finally:
            QApplication.restoreOverrideCursor()

    def create_button_box(self, ok_text: str = "OK", cancel_text: str = "Cancel") -> QHBoxLayout:
        """Create standard OK/Cancel button box.

        Args:
            ok_text: Text for OK button
            cancel_text: Text for Cancel button

        Returns:
            QHBoxLayout containing the buttons
        """
        layout = QHBoxLayout()

        self.btn_ok = QPushButton(ok_text)
        self.btn_ok.clicked.connect(self.accept)

        self.btn_cancel = QPushButton(cancel_text)
        self.btn_cancel.clicked.connect(self.reject)

        layout.addStretch()
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_cancel)

        return layout
