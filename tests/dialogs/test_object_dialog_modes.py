"""ObjectDialog tool-mode behavior:

- exactly one of landmark / wireframe / calibration is always selected;
- a confirmed calibration drops straight into landmark input mode (and a
  cancelled one does not).
"""

from unittest.mock import patch

from PyQt5.QtWidgets import QDialog

import MdModel
from dialogs.object_dialog import ObjectDialog
from MdConstants import MODE


def _dataset_2d():
    return MdModel.MdDataset.create(dataset_name="CalDS", dataset_desc="", dimension=2)


def _dialog(qtbot):
    dialog = ObjectDialog(parent=None)
    qtbot.addWidget(dialog)
    dialog.set_dataset(_dataset_2d())
    return dialog


def _checked_modes(dialog):
    return [
        name
        for btn, name in (
            (dialog.btnLandmark, "landmark"),
            (dialog.btnWireframe, "wireframe"),
            (dialog.btnCalibration, "calibration"),
        )
        if btn.isChecked()
    ]


def test_default_mode_is_landmark(qtbot, mock_database):
    dialog = _dialog(qtbot)
    assert _checked_modes(dialog) == ["landmark"]


def test_exactly_one_mode_selected_after_each_switch(qtbot, mock_database):
    """Every tool switch leaves exactly one of the three selected (never none)."""
    dialog = _dialog(qtbot)
    for handler, expected in (
        (dialog.btnWireframe_clicked, "wireframe"),
        (dialog.btnCalibration_clicked, "calibration"),
        (dialog.btnLandmark_clicked, "landmark"),
    ):
        handler()
        assert _checked_modes(dialog) == [expected]


def test_calibration_accept_switches_to_landmark(qtbot, mock_database):
    dialog = _dialog(qtbot)
    dialog.btnCalibration_clicked()
    assert _checked_modes(dialog) == ["calibration"]

    with patch("dialogs.object_dialog.CalibrationDialog") as MockCal:
        MockCal.return_value.exec_.return_value = QDialog.Accepted
        dialog.calibrate(100.0)

    assert _checked_modes(dialog) == ["landmark"]
    assert dialog.object_view.edit_mode == MODE["EDIT_LANDMARK"]


def test_calibration_cancel_keeps_calibration_mode(qtbot, mock_database):
    dialog = _dialog(qtbot)
    dialog.btnCalibration_clicked()

    with patch("dialogs.object_dialog.CalibrationDialog") as MockCal:
        MockCal.return_value.exec_.return_value = QDialog.Rejected
        dialog.calibrate(100.0)

    # Cancel does not force a mode change; calibration stays selected.
    assert _checked_modes(dialog) == ["calibration"]


def test_non_numeric_coordinate_update_is_guarded(qtbot, mock_database):
    """A non-numeric coordinate must not crash the Update slot.

    btnUpdateInput_clicked does float(inputX.text()); "abc" raises ValueError.
    With @guard_slot the slot logs, shows a (suppressed-in-tests) dialog and
    returns None instead of letting the exception escape the event loop. The
    selected landmark is left unchanged (the bad update is not partially applied).
    """
    dialog = _dialog(qtbot)
    dialog.add_landmark("1.0", "2.0")
    dialog.selected_landmark_index = 0
    before = list(dialog.landmark_list[0])

    dialog.inputX.setText("abc")  # not a number
    dialog.inputY.setText("2.0")

    assert dialog.btnUpdateInput_clicked() is None
    assert list(dialog.landmark_list[0]) == before
