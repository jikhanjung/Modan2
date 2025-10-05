"""New Analysis Dialog for creating and running morphometric analyses."""

import re

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
)

from dialogs.base_dialog import BaseDialog


class NewAnalysisDialog(BaseDialog):
    """Dialog for creating and running new morphometric analysis.

    Features:
    - Analysis name input
    - Superimposition method selection
    - CVA/MANOVA grouping variable selection
    - Progress tracking with bar and status messages
    - Signal-based communication with controller
    """

    def __init__(self, parent, dataset):
        """Initialize new analysis dialog.

        Args:
            parent: Parent window with controller attribute
            dataset: MdDataset to analyze
        """
        super().__init__(parent, title=self.tr("Modan2 - New Analysis"))
        self.parent = parent
        self.setFixedSize(500, 450)

        # Center the dialog on screen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.dataset = dataset
        self.name_edited = False
        self.controller = parent.controller
        self.analysis_running = False
        self.analysis_completed = False

        # Create UI
        self._create_widgets()
        self._create_layout()
        self._connect_signals()
        self.get_analysis_name()

    def _create_widgets(self):
        """Create UI widgets."""
        # Analysis name
        self.lblAnalysisName = QLabel(self.tr("Analysis name"), self)
        self.edtAnalysisName = QLineEdit(self)
        self.edtAnalysisName.textChanged.connect(self.edtAnalysisName_changed)

        # Superimposition method
        self.lblSuperimposition = QLabel(self.tr("Superimposition method"), self)
        self.comboSuperimposition = QComboBox(self)
        self.comboSuperimposition.addItem(self.tr("Procrustes"))
        self.comboSuperimposition.addItem(self.tr("Bookstein"))
        self.comboSuperimposition.addItem(self.tr("Resistant Fit"))

        # CVA grouping variable
        self.lblCvaGroupBy = QLabel(self.tr("CVA grouping variable"), self)
        self.comboCvaGroupBy = QComboBox(self)

        # MANOVA grouping variable
        self.lblManovaGroupBy = QLabel(self.tr("MANOVA grouping variable"), self)
        self.comboManovaGroupBy = QComboBox(self)

        # Populate grouping variables
        valid_property_index_list = self.dataset.get_grouping_variable_index_list()
        variablename_list = self.dataset.get_variablename_list()
        for idx in valid_property_index_list:
            property = variablename_list[idx]
            self.comboCvaGroupBy.addItem(property, idx)
            self.comboManovaGroupBy.addItem(property, idx)

        self.ignore_change = False

        # Buttons
        self.btnOK = QPushButton(self.tr("OK"), self)
        self.btnCancel = QPushButton(self.tr("Cancel"), self)
        self.btnOK.clicked.connect(self.btnOK_clicked)
        self.btnCancel.clicked.connect(self.btnCancel_clicked)

        # Progress bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.hide()

        # Status label
        self.lblStatus = QLabel("", self)
        self.lblStatus.setAlignment(Qt.AlignCenter)
        self.lblStatus.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        self.lblStatus.hide()

    def _create_layout(self):
        """Create dialog layout."""
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        i = 0
        self.layout.addWidget(self.lblAnalysisName, i, 0)
        self.layout.addWidget(self.edtAnalysisName, i, 1)
        i += 1
        self.layout.addWidget(self.lblSuperimposition, i, 0)
        self.layout.addWidget(self.comboSuperimposition, i, 1)
        i += 1
        self.layout.addWidget(self.lblCvaGroupBy, i, 0)
        self.layout.addWidget(self.comboCvaGroupBy, i, 1)
        i += 1
        self.layout.addWidget(self.lblManovaGroupBy, i, 0)
        self.layout.addWidget(self.comboManovaGroupBy, i, 1)

        # Add progress bar and status label
        i += 1
        self.layout.addWidget(self.progressBar, i, 0, 1, 2)

        i += 1
        self.layout.addWidget(self.lblStatus, i, 0, 1, 2)

        # Buttons
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.btnOK)
        self.buttonLayout.addWidget(self.btnCancel)
        i += 1
        self.layout.addWidget(QLabel(""), i, 0, 1, 2)
        i += 1
        self.layout.addLayout(self.buttonLayout, i, 0, 1, 2)

    def _connect_signals(self):
        """Connect controller signals for progress tracking."""
        # Store signal connections for cleanup
        self.signal_connections = []

        # Connect controller signals for progress
        if hasattr(self.controller, "analysis_progress"):
            self.signal_connections.append((self.controller.analysis_progress, self.on_analysis_progress))
            self.controller.analysis_progress.connect(self.on_analysis_progress)
        if hasattr(self.controller, "analysis_completed"):
            self.signal_connections.append((self.controller.analysis_completed, self.on_analysis_completed))
            self.controller.analysis_completed.connect(self.on_analysis_completed)
        if hasattr(self.controller, "analysis_failed"):
            self.signal_connections.append((self.controller.analysis_failed, self.on_analysis_failed))
            self.controller.analysis_failed.connect(self.on_analysis_failed)

    def edtAnalysisName_changed(self):
        """Handle analysis name text change."""
        if not self.ignore_change:
            self.name_edited = True

    def get_analysis_name(self):
        """Generate unique analysis name if not manually edited."""
        if not self.name_edited:
            analysis_name = "Analysis"

            analysis_name_list = [analysis.analysis_name for analysis in self.dataset.analyses]
            if analysis_name in analysis_name_list:
                analysis_name = self.get_unique_name(analysis_name, analysis_name_list)
            self.ignore_change = True
            self.edtAnalysisName.setText(analysis_name)
            self.ignore_change = False

    def btnOK_clicked(self):
        """Run analysis with progress bar."""
        if self.analysis_running:
            return

        # Validate inputs
        if not self.edtAnalysisName.text().strip():
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Please enter an analysis name"))
            return

        # Store parameters for later use
        self.analysis_name = self.edtAnalysisName.text()
        self.superimposition_method = self.comboSuperimposition.currentText()
        self.cva_group_by = self.comboCvaGroupBy.currentData()
        self.manova_group_by = self.comboManovaGroupBy.currentData()

        # Disable controls during analysis
        self.set_controls_enabled(False)
        self.analysis_running = True

        # Set wait cursor during analysis
        QApplication.setOverrideCursor(Qt.WaitCursor)

        # Show progress bar and status
        self.progressBar.show()
        self.lblStatus.show()
        self.progressBar.setValue(0)
        self.lblStatus.setText(self.tr("Validating dataset..."))

        # Change button text
        self.btnOK.setText(self.tr("Running..."))
        self.btnCancel.setText(self.tr("Close"))

        try:
            # Validate dataset
            if not self.controller.validate_dataset_for_analysis(self.dataset):
                self.on_analysis_failed(self.tr("Dataset validation failed"))
                return

            self.lblStatus.setText(self.tr("Starting analysis..."))
            QApplication.processEvents()

            # Run analysis
            self.controller.run_analysis(
                dataset=self.dataset,
                analysis_name=self.analysis_name,
                superimposition_method=self.superimposition_method,
                cva_group_by=self.cva_group_by,
                manova_group_by=self.manova_group_by,
            )

        except Exception as e:
            self.on_analysis_failed(str(e))

    def btnCancel_clicked(self):
        """Handle cancel button click."""
        # Disconnect signals before closing
        self.cleanup_connections()

        if self.analysis_completed:
            # If analysis completed successfully, accept
            self.accept()
        else:
            # Otherwise reject
            self.reject()

    def set_controls_enabled(self, enabled):
        """Enable/disable input controls.

        Args:
            enabled: True to enable, False to disable
        """
        self.edtAnalysisName.setEnabled(enabled)
        self.comboSuperimposition.setEnabled(enabled)
        self.comboCvaGroupBy.setEnabled(enabled)
        self.comboManovaGroupBy.setEnabled(enabled)
        self.btnOK.setEnabled(enabled)

    def on_analysis_progress(self, progress):
        """Update progress bar.

        Args:
            progress: Progress value (0-100)
        """
        self.progressBar.setValue(progress)

        # Update status message based on progress
        if progress < 25:
            self.lblStatus.setText(self.tr("Validating objects and landmarks..."))
        elif progress < 50:
            self.lblStatus.setText(self.tr("Performing Procrustes superimposition..."))
        elif progress < 75:
            self.lblStatus.setText(self.tr("Running PCA analysis..."))
        elif progress < 90:
            self.lblStatus.setText(self.tr("Computing CVA and MANOVA..."))
        else:
            self.lblStatus.setText(self.tr("Finalizing results..."))

        QApplication.processEvents()

    def on_analysis_completed(self, analysis):
        """Handle successful analysis completion.

        Args:
            analysis: Completed MdAnalysis object
        """
        if self.analysis_completed:  # Prevent multiple calls
            return

        self.analysis_result = analysis
        self.analysis_completed = True
        self.analysis_running = False

        # Restore normal cursor
        QApplication.restoreOverrideCursor()

        self.progressBar.setValue(100)
        self.lblStatus.setText(self.tr("Analysis completed successfully!"))
        self.lblStatus.setStyleSheet("QLabel { color: green; font-weight: bold; }")

        # Re-enable controls
        self.set_controls_enabled(True)

        # Change button text
        self.btnOK.setText(self.tr("OK"))
        self.btnOK.hide()  # Hide OK button after success
        self.btnCancel.setText(self.tr("Close"))

        # Auto-close after a short delay (with cleanup)
        QTimer.singleShot(1500, self.close_dialog)

    def on_analysis_failed(self, error_msg):
        """Handle analysis failure.

        Args:
            error_msg: Error message to display
        """
        # Restore normal cursor
        QApplication.restoreOverrideCursor()

        self.progressBar.setValue(0)
        self.lblStatus.setText(self.tr("Analysis failed: {}").format(error_msg))
        self.lblStatus.setStyleSheet("QLabel { color: red; font-weight: bold; }")

        # Re-enable controls
        self.set_controls_enabled(True)
        self.analysis_running = False

        # Reset button text
        self.btnOK.setText(self.tr("OK"))
        self.btnCancel.setText(self.tr("Cancel"))

        QMessageBox.critical(self, self.tr("Analysis Failed"), self.tr("Analysis failed:\n{}").format(error_msg))

    def cleanup_connections(self):
        """Disconnect all signal connections to prevent errors on close."""
        # Restore cursor if still in wait state
        QApplication.restoreOverrideCursor()

        for signal, slot in self.signal_connections:
            try:
                signal.disconnect(slot)
            except TypeError:
                # Signal might already be disconnected
                pass
        self.signal_connections.clear()

    def close_dialog(self):
        """Safely close the dialog."""
        self.cleanup_connections()
        if self.analysis_completed:
            self.accept()
        else:
            self.reject()

    def closeEvent(self, event):
        """Handle dialog close event.

        Args:
            event: QCloseEvent
        """
        self.cleanup_connections()
        event.accept()

    def get_unique_name(self, name, name_list):
        """Generate unique name by appending number if name exists.

        Args:
            name: Base name
            name_list: List of existing names

        Returns:
            Unique name
        """
        if name not in name_list:
            return name
        else:
            i = 1
            # Get last index of current name which is in the form of "name (i)"
            match = re.match(r"(.+)\s+\((\d+)\)", name)
            if match:
                name = match.group(1)
                i = int(match.group(2))
                i += 1
            while True:
                new_name = name + " (" + str(i) + ")"
                if new_name not in name_list:
                    return new_name
                i += 1
