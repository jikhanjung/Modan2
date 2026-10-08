"""Export writes what the dialog says it will.

Three bugs, all in the export dialog:

- **X1Y1** was offered but ``export_dataset`` had no branch for it, so choosing
  it closed the dialog and wrote nothing.
- The **Object List / Export List** selection was ignored: every object was
  written regardless of what had been moved out of the Export List.
- A **missing landmark** was written as the text ``None``, which no reader can
  parse back -- Modan2's own TPS import failed on its own export. It is now the
  ``-999`` placeholder that the import offers to turn back into a gap.
"""

import pytest
from PyQt5.QtWidgets import QFileDialog, QMessageBox

import MdModel
from components.formats.tps import TPS
from components.formats.x1y1 import X1Y1
from dialogs.export_dialog import ExportDatasetDialog, format_coordinate, format_tps, format_x1y1


class TestFormatters:
    def test_missing_coordinate_is_the_placeholder(self):
        assert format_coordinate(None) == "-999"
        assert format_coordinate(1.5) == "1.5"

    def test_tps_with_a_missing_landmark_reads_back(self, tmp_path):
        path = tmp_path / "m.tps"
        path.write_text(format_tps([("s1", [[1.0, 2.0], [None, None], [5.0, 6.0]], [])], 2))
        tps = TPS(str(path), "ds")
        assert tps.landmark_data["s1"] == [[1.0, 2.0], [-999.0, -999.0], [5.0, 6.0]]

    @pytest.mark.parametrize("dimension", [2, 3])
    def test_x1y1_round_trips_through_the_reader(self, tmp_path, dimension):
        rows = [("a", [[float(i + j + k) for k in range(dimension)] for j in range(4)]) for i in range(3)]
        path = tmp_path / "t.x1y1"
        path.write_text(format_x1y1(rows, dimension))
        data = X1Y1(str(path), "ds")
        assert data.dimension == dimension
        assert data.nobjects == 3
        assert data.object_name_list == ["a", "a", "a"]


@pytest.fixture
def dataset(mock_database):
    ds = MdModel.MdDataset.create(dataset_name="Export", dimension=2, landmark_count=3)
    for i in range(3):
        landmarks = "\n".join(f"{i + j}.0\t{i * 2 + j}.0" for j in range(3))
        MdModel.MdObject.create(dataset=ds, object_name=f"obj{i}", sequence=i + 1, landmark_str=landmarks)
    return ds


@pytest.fixture
def dialog(qtbot, dataset):
    dlg = ExportDatasetDialog(None)
    qtbot.addWidget(dlg)
    dlg.set_dataset(dataset)
    dlg.rbNone.setChecked(True)
    return dlg


def _save_to(monkeypatch, path):
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(path), ""))


def _leave_out(dlg, name):
    """Move one object from the Export List back to the Object List."""
    for i in range(dlg.lstExportList.count()):
        if dlg.lstExportList.item(i).text() == name:
            dlg.lstExportList.item(i).setSelected(True)
    dlg.move_left()


class TestExportDialog:
    def test_x1y1_writes_a_file(self, dialog, monkeypatch, tmp_path):
        out = tmp_path / "out.x1y1"
        _save_to(monkeypatch, out)
        dialog.rbX1Y1.setChecked(True)
        dialog.export_dataset()
        data = X1Y1(str(out), "ds")
        assert data.object_name_list == ["obj0", "obj1", "obj2"]
        assert data.landmark_data["obj1"] == [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]]

    @pytest.mark.parametrize("fmt", ["TPS", "X1Y1", "Morphologika"])
    def test_only_the_export_list_is_written(self, dialog, monkeypatch, tmp_path, fmt):
        out = tmp_path / "out.txt"
        _save_to(monkeypatch, out)
        _leave_out(dialog, "obj1")
        {"TPS": dialog.rbTPS, "X1Y1": dialog.rbX1Y1, "Morphologika": dialog.rbMorphologika}[fmt].setChecked(True)
        dialog.export_dataset()
        text = out.read_text()
        assert "obj0" in text and "obj2" in text
        assert "obj1" not in text

    def test_empty_export_list_writes_nothing(self, dialog, monkeypatch, tmp_path):
        out = tmp_path / "out.tps"
        _save_to(monkeypatch, out)
        warned = []
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: warned.append(a))
        for name in ("obj0", "obj1", "obj2"):
            _leave_out(dialog, name)
        dialog.export_dataset()
        assert warned and not out.exists()

    def test_lists_are_disabled_for_a_package(self, dialog):
        dialog.rbJSONZip.setChecked(True)
        assert not dialog.lstExportList.isEnabled()
        assert dialog.chkIncludeFiles.isEnabled()
        dialog.rbTPS.setChecked(True)
        assert dialog.lstExportList.isEnabled()
        assert not dialog.chkIncludeFiles.isEnabled()

    def test_resistant_fit_is_no_longer_offered(self, dialog):
        assert not hasattr(dialog, "rbRFTRA")
