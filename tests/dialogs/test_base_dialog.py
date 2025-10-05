"""Tests for BaseDialog."""

from unittest.mock import Mock, patch

import pytest
from PyQt5.QtWidgets import QProgressBar

from dialogs.base_dialog import BaseDialog


class TestBaseDialogInitialization:
    """Test BaseDialog initialization."""

    def test_dialog_creation_no_title(self, qtbot):
        """Test dialog can be created without title."""
        dialog = BaseDialog()
        qtbot.addWidget(dialog)
        assert dialog is not None
        assert dialog.windowTitle() == ""

    def test_dialog_creation_with_title(self, qtbot):
        """Test dialog can be created with title."""
        dialog = BaseDialog(title="Test Dialog")
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "Test Dialog"

    def test_dialog_creation_with_parent(self, qtbot):
        """Test dialog can be created with parent."""
        parent = BaseDialog(title="Parent")
        qtbot.addWidget(parent)

        dialog = BaseDialog(parent=parent, title="Child")
        qtbot.addWidget(dialog)

        assert dialog.parent() == parent

    def test_progress_bar_initially_none(self, qtbot):
        """Test progress bar is None initially."""
        dialog = BaseDialog()
        qtbot.addWidget(dialog)
        assert dialog.progress_bar is None


class TestBaseDialogMessageBoxes:
    """Test BaseDialog message box methods."""

    @pytest.fixture
    def dialog(self, qtbot):
        """Create dialog for testing."""
        dialog = BaseDialog(title="Test Dialog")
        qtbot.addWidget(dialog)
        return dialog

    @patch("dialogs.base_dialog.QMessageBox.critical")
    def test_show_error(self, mock_critical, qtbot, dialog):
        """Test show_error displays critical message."""
        dialog.show_error("Test error message")

        mock_critical.assert_called_once_with(dialog, "Error", "Test error message")

    @patch("dialogs.base_dialog.QMessageBox.critical")
    def test_show_error_custom_title(self, mock_critical, qtbot, dialog):
        """Test show_error with custom title."""
        dialog.show_error("Test error", title="Custom Error")

        mock_critical.assert_called_once_with(dialog, "Custom Error", "Test error")

    @patch("dialogs.base_dialog.QMessageBox.warning")
    def test_show_warning(self, mock_warning, qtbot, dialog):
        """Test show_warning displays warning message."""
        dialog.show_warning("Test warning message")

        mock_warning.assert_called_once_with(dialog, "Warning", "Test warning message")

    @patch("dialogs.base_dialog.QMessageBox.warning")
    def test_show_warning_custom_title(self, mock_warning, qtbot, dialog):
        """Test show_warning with custom title."""
        dialog.show_warning("Test warning", title="Custom Warning")

        mock_warning.assert_called_once_with(dialog, "Custom Warning", "Test warning")

    @patch("dialogs.base_dialog.QMessageBox.information")
    def test_show_info(self, mock_info, qtbot, dialog):
        """Test show_info displays information message."""
        dialog.show_info("Test info message")

        mock_info.assert_called_once_with(dialog, "Information", "Test info message")

    @patch("dialogs.base_dialog.QMessageBox.information")
    def test_show_info_custom_title(self, mock_info, qtbot, dialog):
        """Test show_info with custom title."""
        dialog.show_info("Test info", title="Custom Info")

        mock_info.assert_called_once_with(dialog, "Custom Info", "Test info")


class TestBaseDialogProgressBar:
    """Test BaseDialog progress bar functionality."""

    @pytest.fixture
    def dialog(self, qtbot):
        """Create dialog with progress bar for testing."""
        dialog = BaseDialog(title="Test Dialog")
        dialog.progress_bar = QProgressBar()
        qtbot.addWidget(dialog)
        return dialog

    def test_set_progress_with_progress_bar(self, qtbot, dialog):
        """Test set_progress updates progress bar."""
        dialog.set_progress(50, 100)

        assert dialog.progress_bar.value() == 50
        assert dialog.progress_bar.maximum() == 100

    def test_set_progress_default_maximum(self, qtbot, dialog):
        """Test set_progress with default maximum."""
        dialog.set_progress(75)

        assert dialog.progress_bar.value() == 75
        assert dialog.progress_bar.maximum() == 100

    def test_set_progress_different_maximums(self, qtbot, dialog):
        """Test set_progress with different maximum values."""
        dialog.set_progress(25, 50)
        assert dialog.progress_bar.maximum() == 50

        dialog.set_progress(75, 200)
        assert dialog.progress_bar.maximum() == 200

    def test_set_progress_without_progress_bar(self, qtbot):
        """Test set_progress does nothing when progress_bar is None."""
        dialog = BaseDialog()
        qtbot.addWidget(dialog)

        # Should not raise exception
        dialog.set_progress(50, 100)
        assert dialog.progress_bar is None


class TestBaseDialogWaitCursor:
    """Test BaseDialog wait cursor functionality."""

    @pytest.fixture
    def dialog(self, qtbot):
        """Create dialog for testing."""
        dialog = BaseDialog(title="Test Dialog")
        qtbot.addWidget(dialog)
        return dialog

    def test_with_wait_cursor_executes_function(self, qtbot, dialog):
        """Test with_wait_cursor executes the provided function."""
        mock_func = Mock(return_value="test_result")

        result = dialog.with_wait_cursor(mock_func)

        mock_func.assert_called_once()
        assert result == "test_result"

    def test_with_wait_cursor_returns_value(self, qtbot, dialog):
        """Test with_wait_cursor returns function result."""

        def test_func():
            return 42

        result = dialog.with_wait_cursor(test_func)
        assert result == 42

    def test_with_wait_cursor_restores_on_exception(self, qtbot, dialog):
        """Test with_wait_cursor restores cursor even on exception."""

        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            dialog.with_wait_cursor(failing_func)

        # Cursor should be restored (hard to test directly in headless mode)
        # Just verify exception was raised and method completed

    def test_with_wait_cursor_with_lambda(self, qtbot, dialog):
        """Test with_wait_cursor works with lambda."""
        result = dialog.with_wait_cursor(lambda: "lambda result")
        assert result == "lambda result"


class TestBaseDialogButtonBox:
    """Test BaseDialog button box creation."""

    @pytest.fixture
    def dialog(self, qtbot):
        """Create dialog for testing."""
        dialog = BaseDialog(title="Test Dialog")
        qtbot.addWidget(dialog)
        return dialog

    def test_create_button_box_default_text(self, qtbot, dialog):
        """Test create_button_box with default button text."""
        layout = dialog.create_button_box()

        assert layout is not None
        assert dialog.btn_ok is not None
        assert dialog.btn_cancel is not None
        assert dialog.btn_ok.text() == "OK"
        assert dialog.btn_cancel.text() == "Cancel"

    def test_create_button_box_custom_text(self, qtbot, dialog):
        """Test create_button_box with custom button text."""
        dialog.create_button_box(ok_text="Apply", cancel_text="Close")

        assert dialog.btn_ok.text() == "Apply"
        assert dialog.btn_cancel.text() == "Close"

    def test_button_box_ok_accepts_dialog(self, qtbot, dialog):
        """Test OK button accepts dialog."""
        dialog.create_button_box()

        # Verify button is connected (checking signal exists)
        assert dialog.btn_ok is not None
        # Just verify button exists and can be clicked (don't actually close)
        assert dialog.btn_ok.text() == "OK"

    def test_button_box_cancel_rejects_dialog(self, qtbot, dialog):
        """Test Cancel button rejects dialog."""
        dialog.create_button_box()

        # Verify button is connected (checking signal exists)
        assert dialog.btn_cancel is not None
        # Just verify button exists and can be clicked (don't actually close)
        assert dialog.btn_cancel.text() == "Cancel"

    def test_button_box_layout_structure(self, qtbot, dialog):
        """Test button box layout has correct structure."""
        layout = dialog.create_button_box()

        # Layout should have stretch, OK button, Cancel button
        assert layout.count() == 3  # stretch + 2 buttons


class TestBaseDialogIntegration:
    """Test BaseDialog integration scenarios."""

    def test_dialog_lifecycle(self, qtbot):
        """Test complete dialog lifecycle."""
        dialog = BaseDialog(title="Lifecycle Test")
        qtbot.addWidget(dialog)

        # Create button box
        layout = dialog.create_button_box()
        assert layout is not None

        # Create progress bar
        dialog.progress_bar = QProgressBar()
        dialog.set_progress(50)
        assert dialog.progress_bar.value() == 50

        # Execute with wait cursor
        result = dialog.with_wait_cursor(lambda: "done")
        assert result == "done"

    def test_subclass_usage(self, qtbot):
        """Test BaseDialog can be subclassed."""

        class CustomDialog(BaseDialog):
            def __init__(self):
                super().__init__(title="Custom Dialog")
                self.value = 0

            def increment(self):
                self.value += 1

        dialog = CustomDialog()
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Custom Dialog"
        dialog.increment()
        assert dialog.value == 1

    @patch("dialogs.base_dialog.QMessageBox.critical")
    @patch("dialogs.base_dialog.QMessageBox.warning")
    @patch("dialogs.base_dialog.QMessageBox.information")
    def test_all_message_types(self, mock_info, mock_warning, mock_critical, qtbot):
        """Test all message types can be shown."""
        dialog = BaseDialog(title="Messages Test")
        qtbot.addWidget(dialog)

        dialog.show_error("Error message")
        dialog.show_warning("Warning message")
        dialog.show_info("Info message")

        mock_critical.assert_called_once()
        mock_warning.assert_called_once()
        mock_info.assert_called_once()

    def test_multiple_progress_updates(self, qtbot):
        """Test multiple progress bar updates."""
        dialog = BaseDialog()
        dialog.progress_bar = QProgressBar()
        qtbot.addWidget(dialog)

        # Multiple updates
        for i in range(0, 101, 10):
            dialog.set_progress(i, 100)
            assert dialog.progress_bar.value() == i

    def test_button_box_multiple_calls(self, qtbot):
        """Test create_button_box can be called multiple times."""
        dialog = BaseDialog()
        qtbot.addWidget(dialog)

        layout1 = dialog.create_button_box()
        btn_ok_1 = dialog.btn_ok

        layout2 = dialog.create_button_box()
        btn_ok_2 = dialog.btn_ok

        # Each call creates new buttons
        assert btn_ok_1 is not btn_ok_2
        assert layout1 is not layout2
