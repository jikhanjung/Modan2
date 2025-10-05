"""Progress Dialog for long-running operations."""

from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtWidgets import QApplication, QLabel, QProgressBar, QPushButton, QVBoxLayout

from dialogs.base_dialog import BaseDialog


class ProgressDialog(BaseDialog):
    """Dialog for displaying progress of long-running operations.

    Provides:
    - Progress bar
    - Status text
    - Stop button for cancellation
    """

    def __init__(self, parent):
        """Initialize progress dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent, title="Modan2 - Progress Dialog")
        self.parent = parent
        self.setGeometry(QRect(100, 100, 320, 180))
        self.move(self.parent.pos() + QPoint(100, 100))

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50, 50, 50, 50)

        self.lbl_text = QLabel(self)
        self.pb_progress = QProgressBar(self)
        self.pb_progress.setValue(0)
        self.stop_progress = False
        self.btnStop = QPushButton(self)
        self.btnStop.setText("Stop")
        self.btnStop.clicked.connect(self.set_stop_progress)
        self.layout.addWidget(self.lbl_text)
        self.layout.addWidget(self.pb_progress)
        self.layout.addWidget(self.btnStop)
        self.setLayout(self.layout)

    def set_stop_progress(self):
        """Set flag to stop progress."""
        self.stop_progress = True

    def set_progress_text(self, text_format):
        """Set text format for progress display.

        Args:
            text_format: Format string with {0} and {1} placeholders
        """
        self.text_format = text_format

    def set_max_value(self, max_value):
        """Set maximum progress value.

        Args:
            max_value: Maximum value
        """
        self.max_value = max_value

    def set_curr_value(self, curr_value):
        """Update current progress value.

        Args:
            curr_value: Current value
        """
        self.curr_value = curr_value
        self.pb_progress.setValue(int((self.curr_value / float(self.max_value)) * 100))
        self.lbl_text.setText(self.text_format.format(self.curr_value, self.max_value))
        self.update()
        QApplication.processEvents()
