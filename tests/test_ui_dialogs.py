"""Tests for Modan2 dialog windows.

Most of this file used to be six classes skipped as "causing CI timeout - needs
refactoring". They were not timing out: they addressed widgets and methods that
do not exist and never did — ``dialog.edit_dataset_name`` where the real widget
is ``edtDatasetName``, ``dialog.slider_landmark_size``, ``main_window
.on_action_open_image``, ``ObjectDialog(parent, object)`` when the constructor
takes only a parent. Written speculatively, skipped before they could fail, and
never run against the application.

Deleting them costs no coverage: each dialog has a real suite under
``tests/dialogs/`` (dataset 21 tests, preferences 38, analysis 34, plus import,
export, object-mode and calibration). What remains here is what actually
exercises the application. See devlog 233.
"""

import os
import sys
from unittest.mock import patch

from PyQt5.QtWidgets import QMessageBox

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAboutDialog:
    """Test About dialog."""

    def test_about_dialog_shows(self, qtbot, main_window):
        """Test that about dialog shows information.

        The box is built rather than shown through QMessageBox.about, so that
        the project URL can be a live link; see tests/test_about_dialog.py.
        """
        message = main_window.build_about_message()
        message.deleteLater()
        assert "Modan2" in message.text()

        # The action itself still runs (exec_ is stubbed out for tests).
        main_window.on_action_about_triggered()


class TestControllerMessages:
    """The main window surfaces what the controller reports."""

    def test_error_is_shown_to_the_user(self, qtbot, main_window):
        with patch.object(QMessageBox, "critical") as mock_critical:
            main_window.on_controller_error("Test error message")

            mock_critical.assert_called_once()
            assert "Test error message" in mock_critical.call_args[0][2]

    def test_analysis_failure_is_shown_to_the_user(self, qtbot, main_window):
        with patch.object(QMessageBox, "critical") as mock_critical:
            main_window.on_analysis_failed("singular matrix")

            mock_critical.assert_called_once()
            assert "singular matrix" in mock_critical.call_args[0][2]
