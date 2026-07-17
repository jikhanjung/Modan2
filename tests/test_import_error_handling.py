"""Error-handling test for import: a malformed file must surface an error, not crash
the app or leave a partial dataset (audit 198, batch 2)."""

from unittest.mock import Mock, patch

from PyQt5.QtWidgets import QMessageBox, QWidget

import MdModel
from dialogs.import_dialog import ImportDatasetDialog


def test_malformed_import_file_shows_error_not_crash(qtbot, mock_database, tmp_path, monkeypatch):
    parent = QWidget()
    qtbot.addWidget(parent)

    def mock_value(key, default=None):
        if key == "width_scale":
            return 1.0
        if key == "dataset_mode":
            return 0
        return default if default is not None else True

    mock_settings = Mock()
    mock_settings.value.side_effect = mock_value
    mock_app = Mock()
    mock_app.settings = mock_settings
    mock_app.storage_directory = str(tmp_path)

    bad = tmp_path / "bad.tps"
    bad.write_text("this is not a valid tps file\nrandom garbage\n")

    crit = Mock()
    monkeypatch.setattr(QMessageBox, "critical", crit)

    with patch("PyQt5.QtWidgets.QApplication.instance", return_value=mock_app):
        dialog = ImportDatasetDialog(parent=parent)
        qtbot.addWidget(dialog)

        before = MdModel.MdDataset.select().count()
        # Selecting the file previews it (parses immediately) — must not crash.
        dialog.open_file2(str(bad))
        # And an explicit import attempt must also surface an error, not crash.
        dialog.rbnTPS.setChecked(True)
        dialog.import_file()
        after = MdModel.MdDataset.select().count()

    assert crit.call_count >= 1  # error surfaced via guard_slot (no silent crash)
    assert after == before  # no partial dataset persisted
