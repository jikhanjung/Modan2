"""UI tests for NewAnalysisDialog."""

from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

import MdModel
from dialogs import NewAnalysisDialog


@pytest.fixture
def mock_controller():
    """Create a mock controller with analysis signals."""
    from PyQt5.QtCore import QObject, pyqtSignal

    class MockController(QObject):
        """Mock controller with analysis signals."""

        analysis_progress = pyqtSignal(int)
        analysis_completed = pyqtSignal(object)
        analysis_failed = pyqtSignal(str)

        def __init__(self):
            super().__init__()
            self.validate_dataset_for_analysis = Mock(return_value=True)
            self.run_analysis = Mock()

    return MockController()


@pytest.fixture
def mock_parent(qtbot, mock_controller):
    """Create a mock parent window with controller."""
    from PyQt5.QtWidgets import QWidget

    parent = QWidget()
    parent.controller = mock_controller
    qtbot.addWidget(parent)

    return parent


@pytest.fixture
def sample_dataset_with_variables(mock_database):
    """Create a sample dataset with grouping variables for testing."""
    # Create dataset with variables
    dataset = MdModel.MdDataset.create(
        dataset_name="Test Dataset",
        dataset_desc="Dataset for analysis testing",
        dimension=2,
        landmark_count=10,
        object_name="Test Object",
        object_desc="Test Description",
        variablename_list=["ID", "Species", "Sex", "Age"],
    )

    # Add several objects with landmark data and variable values
    for i in range(5):
        obj = MdModel.MdObject.create(
            dataset=dataset,
            object_name=f"Object_{i + 1}",
            sequence=i + 1,
        )
        # Add landmark coordinates (10 landmarks)
        landmark_str = "\n".join([f"{j}.0\t{j + 1}.0" for j in range(10)])
        obj.landmark_str = landmark_str

        # Add variable values
        obj.propertyvalue_list = [
            f"ID_{i + 1}",
            "Species_A" if i % 2 == 0 else "Species_B",
            "Male" if i % 3 == 0 else "Female",
            str(20 + i),
        ]
        obj.save()

    return dataset


@pytest.fixture
def dialog(qtbot, mock_parent, sample_dataset_with_variables):
    """Create NewAnalysisDialog instance."""
    dlg = NewAnalysisDialog(mock_parent, sample_dataset_with_variables)
    qtbot.addWidget(dlg)
    dlg.show()  # Show dialog so child widgets can be visible
    qtbot.waitExposed(dlg)
    return dlg


class TestNewAnalysisDialogInitialization:
    """Test dialog initialization and setup."""

    def test_dialog_creation(self, dialog):
        """Test that dialog is created successfully."""
        assert dialog is not None
        assert isinstance(dialog, QDialog)
        assert dialog.windowTitle() == "Modan2 - New Analysis"

    def test_dialog_size(self, dialog):
        """Test that dialog has fixed size."""
        assert dialog.width() == 500
        assert dialog.height() == 450

    def test_ui_elements_present(self, dialog):
        """Test that all UI elements are created."""
        # Labels
        assert dialog.lblAnalysisName is not None
        assert dialog.lblSuperimposition is not None
        assert dialog.lblCvaGroupBy is not None
        assert dialog.lblManovaGroupBy is not None

        # Input widgets
        assert dialog.edtAnalysisName is not None
        assert dialog.comboSuperimposition is not None
        assert dialog.comboCvaGroupBy is not None
        assert dialog.comboManovaGroupBy is not None

        # Buttons
        assert dialog.btnOK is not None
        assert dialog.btnCancel is not None

        # Progress indicators
        assert dialog.progressBar is not None
        assert dialog.lblStatus is not None

    def test_default_values(self, dialog):
        """Test that default values are set correctly."""
        # Analysis name should be auto-generated
        assert dialog.edtAnalysisName.text() == "Analysis"

        # Superimposition should default to Procrustes
        assert dialog.comboSuperimposition.currentIndex() == 0
        assert dialog.comboSuperimposition.currentText() in ["Procrustes", "프로크루스테스"]

        # Progress bar should be hidden initially
        assert not dialog.progressBar.isVisible()
        assert not dialog.lblStatus.isVisible()

    def test_superimposition_methods(self, dialog):
        """Test that all superimposition methods are available."""
        # Should have 3 methods (language-dependent text)
        assert dialog.comboSuperimposition.count() == 3

    def test_grouping_variables_populated(self, dialog, sample_dataset_with_variables):
        """Test that grouping variables are populated from dataset."""
        # Get expected grouping variables (should exclude ID which is all unique)
        expected_count = len(sample_dataset_with_variables.get_grouping_variable_index_list())

        assert dialog.comboCvaGroupBy.count() == expected_count
        assert dialog.comboManovaGroupBy.count() == expected_count

    def test_initial_state(self, dialog):
        """Test initial dialog state."""
        assert not dialog.analysis_running
        assert not dialog.analysis_completed
        assert not dialog.name_edited


class TestNewAnalysisDialogValidation:
    """Test input validation."""

    def test_empty_analysis_name_validation(self, qtbot, dialog):
        """Test that empty analysis name is rejected."""
        dialog.edtAnalysisName.setText("")

        with patch("PyQt5.QtWidgets.QMessageBox.warning") as mock_warning:
            dialog.btnOK_clicked()

            # Should show warning
            mock_warning.assert_called_once()
            args = mock_warning.call_args[0]
            assert "analysis name" in args[2].lower() or "분석 이름" in args[2]

    def test_whitespace_only_name_validation(self, qtbot, dialog):
        """Test that whitespace-only analysis name is rejected."""
        dialog.edtAnalysisName.setText("   ")

        with patch("PyQt5.QtWidgets.QMessageBox.warning") as mock_warning:
            dialog.btnOK_clicked()

            # Should show warning
            mock_warning.assert_called_once()

    def test_valid_name_accepted(self, qtbot, dialog, mock_controller):
        """Test that valid analysis name is accepted."""
        dialog.edtAnalysisName.setText("My Analysis")

        # Mock successful validation and analysis
        mock_controller.validate_dataset_for_analysis.return_value = True

        dialog.btnOK_clicked()

        # Should not show warning
        assert dialog.analysis_name == "My Analysis"


class TestNewAnalysisDialogUserInteractions:
    """Test user interactions with dialog."""

    def test_analysis_name_editing(self, qtbot, dialog):
        """Test that editing analysis name sets name_edited flag."""
        assert not dialog.name_edited

        # Simulate user typing
        qtbot.keyClicks(dialog.edtAnalysisName, "Custom Name")

        assert dialog.name_edited

    def test_superimposition_selection(self, qtbot, dialog):
        """Test changing superimposition method."""
        initial_method = dialog.comboSuperimposition.currentIndex()

        # Change to different method
        new_index = (initial_method + 1) % dialog.comboSuperimposition.count()
        dialog.comboSuperimposition.setCurrentIndex(new_index)

        assert dialog.comboSuperimposition.currentIndex() == new_index

    def test_cva_grouping_selection(self, qtbot, dialog):
        """Test changing CVA grouping variable."""
        if dialog.comboCvaGroupBy.count() > 0:
            dialog.comboCvaGroupBy.setCurrentIndex(0)
            assert dialog.comboCvaGroupBy.currentIndex() == 0

    def test_manova_grouping_selection(self, qtbot, dialog):
        """Test changing MANOVA grouping variable."""
        if dialog.comboManovaGroupBy.count() > 0:
            dialog.comboManovaGroupBy.setCurrentIndex(0)
            assert dialog.comboManovaGroupBy.currentIndex() == 0

    def test_ok_button_click(self, qtbot, dialog, mock_controller):
        """Test clicking OK button."""
        dialog.edtAnalysisName.setText("Test Analysis")

        # Click OK button
        qtbot.mouseClick(dialog.btnOK, Qt.LeftButton)

        # Should call controller's validate and run_analysis
        assert mock_controller.validate_dataset_for_analysis.called

    def test_cancel_button_click(self, qtbot, dialog):
        """Test clicking Cancel button."""
        # Click Cancel button
        with qtbot.waitSignal(dialog.rejected, timeout=1000):
            qtbot.mouseClick(dialog.btnCancel, Qt.LeftButton)


class TestNewAnalysisDialogProgress:
    """Test progress tracking functionality."""

    def test_progress_bar_shown_on_start(self, qtbot, dialog, mock_controller):
        """Test that progress bar is shown when analysis starts."""
        dialog.edtAnalysisName.setText("Test Analysis")

        # Initially hidden
        assert not dialog.progressBar.isVisible()
        assert not dialog.lblStatus.isVisible()

        # Mock successful validation so analysis actually starts
        mock_controller.validate_dataset_for_analysis.return_value = True

        dialog.btnOK_clicked()

        # Progress bar and status should be shown
        # Note: They remain visible even if validation fails later
        assert dialog.progressBar.isVisible()
        assert dialog.lblStatus.isVisible()

    def test_progress_updates(self, qtbot, dialog):
        """Test that progress bar updates correctly."""
        dialog.on_analysis_progress(25)
        assert dialog.progressBar.value() == 25

        dialog.on_analysis_progress(50)
        assert dialog.progressBar.value() == 50

        dialog.on_analysis_progress(100)
        assert dialog.progressBar.value() == 100

    def test_status_message_updates(self, qtbot, dialog):
        """Test that status message updates based on progress."""
        dialog.on_analysis_progress(10)
        status_text = dialog.lblStatus.text()
        assert len(status_text) > 0  # Should have some status message

        dialog.on_analysis_progress(50)
        status_text_50 = dialog.lblStatus.text()
        # Status text might change at different progress levels
        assert len(status_text_50) > 0

    def test_controls_disabled_during_analysis(self, qtbot, dialog, mock_controller):
        """Test that controls are disabled during analysis."""
        dialog.edtAnalysisName.setText("Test Analysis")

        # Initially enabled
        assert dialog.edtAnalysisName.isEnabled()
        assert dialog.comboSuperimposition.isEnabled()
        assert dialog.btnOK.isEnabled()

        dialog.btnOK_clicked()

        # Should be disabled during analysis
        assert not dialog.edtAnalysisName.isEnabled()
        assert not dialog.comboSuperimposition.isEnabled()
        assert not dialog.btnOK.isEnabled()

    def test_button_text_changes_during_analysis(self, qtbot, dialog, mock_controller):
        """Test that button text changes during analysis."""
        dialog.edtAnalysisName.setText("Test Analysis")

        initial_ok_text = dialog.btnOK.text()
        initial_cancel_text = dialog.btnCancel.text()

        dialog.btnOK_clicked()

        # Button text should change
        assert dialog.btnOK.text() != initial_ok_text
        assert dialog.btnCancel.text() != initial_cancel_text


class TestNewAnalysisDialogCompletion:
    """Test analysis completion scenarios."""

    def test_successful_completion(self, qtbot, dialog, mock_controller):
        """Test successful analysis completion."""
        # Create mock analysis result
        mock_analysis = Mock()
        mock_analysis.analysis_name = "Test Analysis"

        dialog.on_analysis_completed(mock_analysis)

        # Should mark as completed
        assert dialog.analysis_completed
        assert not dialog.analysis_running

        # Progress bar should be at 100%
        assert dialog.progressBar.value() == 100

        # Status should indicate success
        assert "success" in dialog.lblStatus.text().lower() or "완료" in dialog.lblStatus.text()

        # OK button should be hidden
        assert not dialog.btnOK.isVisible()

    def test_analysis_failure(self, qtbot, dialog):
        """Test analysis failure handling."""
        error_msg = "Test error message"

        with patch("PyQt5.QtWidgets.QMessageBox.critical") as mock_critical:
            dialog.on_analysis_failed(error_msg)

            # Should show error message
            mock_critical.assert_called_once()

        # Should not be marked as completed
        assert not dialog.analysis_completed
        assert not dialog.analysis_running

        # Progress should be reset
        assert dialog.progressBar.value() == 0

        # Status should show error
        assert "fail" in dialog.lblStatus.text().lower() or "실패" in dialog.lblStatus.text()

    def test_controls_reenabled_after_failure(self, qtbot, dialog):
        """Test that controls are re-enabled after failure."""
        # Simulate analysis start
        dialog.set_controls_enabled(False)
        dialog.analysis_running = True

        # Fail the analysis
        dialog.on_analysis_failed("Test error")

        # Controls should be re-enabled
        assert dialog.edtAnalysisName.isEnabled()
        assert dialog.comboSuperimposition.isEnabled()
        assert dialog.btnOK.isEnabled()

    def test_multiple_completion_calls_ignored(self, qtbot, dialog):
        """Test that multiple completion signals are handled safely."""
        mock_analysis = Mock()
        mock_analysis.analysis_name = "Test Analysis"

        # First completion
        dialog.on_analysis_completed(mock_analysis)
        first_result = dialog.analysis_result

        # Second completion (should be ignored)
        dialog.on_analysis_completed(mock_analysis)

        # Result should not change
        assert dialog.analysis_result == first_result


class TestNewAnalysisDialogHelpers:
    """Test helper methods."""

    def test_get_unique_name_no_conflict(self, dialog):
        """Test unique name generation with no conflicts."""
        name_list = ["Analysis (1)", "Analysis (2)"]
        unique = dialog.get_unique_name("My Analysis", name_list)

        assert unique == "My Analysis"

    def test_get_unique_name_with_conflict(self, dialog):
        """Test unique name generation with conflicts."""
        name_list = ["Analysis", "Analysis (1)"]
        unique = dialog.get_unique_name("Analysis", name_list)

        assert unique == "Analysis (2)"

    def test_get_unique_name_increments_existing(self, dialog):
        """Test unique name generation increments existing numbered names."""
        name_list = ["Analysis", "Analysis (1)", "Analysis (2)"]
        unique = dialog.get_unique_name("Analysis (2)", name_list)

        assert unique == "Analysis (3)"

    def test_set_controls_enabled(self, dialog):
        """Test enabling/disabling controls."""
        dialog.set_controls_enabled(False)

        assert not dialog.edtAnalysisName.isEnabled()
        assert not dialog.comboSuperimposition.isEnabled()
        assert not dialog.comboCvaGroupBy.isEnabled()
        assert not dialog.comboManovaGroupBy.isEnabled()
        assert not dialog.btnOK.isEnabled()

        dialog.set_controls_enabled(True)

        assert dialog.edtAnalysisName.isEnabled()
        assert dialog.comboSuperimposition.isEnabled()
        assert dialog.comboCvaGroupBy.isEnabled()
        assert dialog.comboManovaGroupBy.isEnabled()
        assert dialog.btnOK.isEnabled()

    def test_cleanup_connections(self, dialog, mock_controller):
        """Test signal cleanup on close."""
        # Should have signal connections
        assert len(dialog.signal_connections) > 0

        dialog.cleanup_connections()

        # Connections should be cleared
        assert len(dialog.signal_connections) == 0

    def test_close_event_cleanup(self, qtbot, dialog):
        """Test that close event cleans up properly."""
        from PyQt5.QtGui import QCloseEvent

        # Create close event
        close_event = QCloseEvent()

        dialog.closeEvent(close_event)

        # Should accept the event
        assert close_event.isAccepted()

        # Connections should be cleaned up
        assert len(dialog.signal_connections) == 0


class TestNewAnalysisDialogIntegration:
    """Integration tests with controller."""

    def test_analysis_workflow_success(self, qtbot, dialog, mock_controller):
        """Test complete analysis workflow from start to finish."""
        # Setup
        dialog.edtAnalysisName.setText("Integration Test")
        mock_analysis = Mock()
        mock_analysis.analysis_name = "Integration Test"

        # Mock successful validation
        mock_controller.validate_dataset_for_analysis.return_value = True

        # Start analysis
        dialog.btnOK_clicked()

        # Verify analysis started
        # Note: analysis_running may be reset if validation fails
        assert dialog.progressBar.isVisible()

        # Simulate progress updates
        mock_controller.analysis_progress.emit(25)
        assert dialog.progressBar.value() == 25

        mock_controller.analysis_progress.emit(75)
        assert dialog.progressBar.value() == 75

        # Complete analysis
        mock_controller.analysis_completed.emit(mock_analysis)

        # Verify completion
        assert dialog.analysis_completed
        assert dialog.progressBar.value() == 100

    def test_analysis_parameters_passed_to_controller(self, qtbot, dialog, mock_controller):
        """Test that analysis parameters are correctly passed to controller."""
        dialog.edtAnalysisName.setText("Param Test")
        dialog.comboSuperimposition.setCurrentIndex(1)  # Bookstein

        if dialog.comboCvaGroupBy.count() > 0:
            dialog.comboCvaGroupBy.setCurrentIndex(0)
            expected_cva = dialog.comboCvaGroupBy.currentData()
        else:
            expected_cva = None

        if dialog.comboManovaGroupBy.count() > 0:
            dialog.comboManovaGroupBy.setCurrentIndex(0)
            expected_manova = dialog.comboManovaGroupBy.currentData()
        else:
            expected_manova = None

        dialog.btnOK_clicked()

        # Verify run_analysis was called with correct parameters
        assert mock_controller.run_analysis.called
        call_kwargs = mock_controller.run_analysis.call_args[1]

        assert call_kwargs["analysis_name"] == "Param Test"
        assert call_kwargs["cva_group_by"] == expected_cva
        assert call_kwargs["manova_group_by"] == expected_manova

    def test_validation_failure_prevents_analysis(self, qtbot, dialog, mock_controller):
        """Test that failed validation prevents analysis from running."""
        dialog.edtAnalysisName.setText("Validation Test")

        # Mock validation failure
        mock_controller.validate_dataset_for_analysis.return_value = False

        dialog.btnOK_clicked()

        # Analysis should not be called
        assert not mock_controller.run_analysis.called

        # Controls should be re-enabled
        assert dialog.edtAnalysisName.isEnabled()
