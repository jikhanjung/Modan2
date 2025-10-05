"""Base dialog class with common functionality.

This module provides the BaseDialog class that serves as the foundation
for all Modan2 dialog windows.
"""

import logging
from collections.abc import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QHBoxLayout, QMessageBox, QProgressBar, QPushButton

logger = logging.getLogger(__name__)


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
        QApplication.setOverrideCursor(Qt.WaitCursor)
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
