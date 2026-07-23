"""TPS export of semi-landmark curves (symmetric to CURVES= import).

Covers the pure text builder (format_tps) and a full export->import round-trip
so a curve dataset survives being written and read back.
"""

import os
import sys
import tempfile
from unittest.mock import Mock

import pytest
from peewee import SqliteDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdModel as mm
from components.formats.tps import TPS
from dialogs.export_dialog import ExportDatasetDialog, format_tps


@pytest.fixture
def test_database():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        path = tmp.name
    db = SqliteDatabase(path, pragmas={"foreign_keys": 1})
    original = mm.gDatabase
    mm.gDatabase = db
    models = [mm.MdDataset, mm.MdObject, mm.MdImage, mm.MdThreeDModel, mm.MdAnalysis]
    for model in models:
        model._meta.database = db
    db.connect()
    db.create_tables(models)
    yield db
    db.drop_tables(models)
    db.close()
    mm.gDatabase = original
    for model in models:
        model._meta.database = original
    try:
        os.unlink(path)
    except OSError:
        pass


class TestFormatTps:
    def test_plain_landmarks_no_curves(self):
        rows = [("obj1", [[1.0, 2.0], [3.0, 4.0]], [])]
        text = format_tps(rows, 2)
        assert text == "LM=2\n1.0\t2.0\n3.0\t4.0\nID=obj1\n"

    def test_writes_curves_block(self):
        rows = [("obj1", [[0.0, 0.0]], [[[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]]])]
        text = format_tps(rows, 2)
        assert "LM=1" in text
        assert "CURVES=1" in text
        assert "POINTS=3" in text
        # LM block, then the curve, then ID -- the order the reader expects.
        assert text.index("LM=1") < text.index("CURVES=1") < text.index("ID=obj1")

    def test_multiple_curves(self):
        rows = [("o", [[0.0, 0.0]], [[[1.0, 1.0], [2.0, 2.0]], [[5.0, 5.0], [6.0, 6.0]]])]
        text = format_tps(rows, 2)
        assert "CURVES=2" in text
        assert text.count("POINTS=2") == 2

    def test_truncates_to_dimension(self):
        # A 3D landmark exported as 2D drops the z component.
        rows = [("o", [[1.0, 2.0, 9.0]], [])]
        assert "1.0\t2.0\n" in format_tps(rows, 2)


class TestExportImportRoundTrip:
    def test_curves_survive_export_then_import(self, tmp_path):
        # A specimen with 2 fixed landmarks and one traced curve of 3 points.
        rows = [
            ("specimenA", [[0.0, 0.0], [4.0, 0.0]], [[[0.0, 1.0], [0.0, 2.0], [0.0, 3.0]]]),
            ("specimenB", [[1.0, 1.0], [5.0, 1.0]], [[[1.0, 2.0], [1.0, 3.0], [1.0, 4.0]]]),
        ]
        path = tmp_path / "out.tps"
        path.write_text(format_tps(rows, 2))

        tps = TPS(str(path), "ds")
        # Fixed landmarks come back as landmarks; curves come back as curves.
        assert tps.object_name_list == ["specimenA", "specimenB"]
        assert tps.landmark_data["specimenA"] == [[0.0, 0.0], [4.0, 0.0]]
        assert tps.curve_data["specimenA"] == [[[0.0, 1.0], [0.0, 2.0], [0.0, 3.0]]]
        assert tps.curve_data["specimenB"] == [[[1.0, 2.0], [1.0, 3.0], [1.0, 4.0]]]


def _curve_dataset(n_semi=3):
    """A dataset: 2 fixed landmarks + one traced curve (merge-at-analysis)."""
    ds = mm.MdDataset.create(dataset_name="Curved", dimension=2)
    ds.set_curve_config([{"id": "c1", "n": n_semi, "method": "equidistant", "start": 2, "name": "", "desc": ""}])
    ds.save()
    obj = mm.MdObject.create(object_name="s1", dataset=ds, sequence=0)
    obj.landmark_list = [[0.0, 0.0], [4.0, 0.0]]  # fixed only (semis derived)
    obj.pack_landmark()
    obj.set_curve_raw({"c1": [[0.0, 1.0], [0.0, 2.0], [0.0, 3.0], [0.0, 4.0], [0.0, 5.0]]})
    obj.save()
    return ds


def _stub_dialog(ds, procrustes):
    dlg = ExportDatasetDialog.__new__(ExportDatasetDialog)
    dlg.dataset = ds
    dlg.ds_ops = mm.MdDatasetOps(ds)
    dlg.rbProcrustes = Mock()
    dlg.rbProcrustes.isChecked.return_value = procrustes
    return dlg


class TestTpsRowsFromDataset:
    def test_raw_export_writes_fixed_landmarks_and_curves(self, test_database):
        ds = _curve_dataset()
        dlg = _stub_dialog(ds, procrustes=False)
        text = format_tps(dlg._tps_rows(dlg.ds_ops.object_list), 2)

        with tempfile.NamedTemporaryFile("w", suffix=".tps", delete=False) as fh:
            fh.write(text)
            fname = fh.name
        tps = TPS(fname, "ds")
        # Only the 2 fixed landmarks under LM=, and the raw curve preserved.
        assert tps.landmark_data["s1"] == [[0.0, 0.0], [4.0, 0.0]]
        assert tps.curve_data["s1"] == [[[0.0, 1.0], [0.0, 2.0], [0.0, 3.0], [0.0, 4.0], [0.0, 5.0]]]
        os.unlink(fname)

    def test_procrustes_export_writes_merged_landmarks_no_curves(self, test_database):
        ds = _curve_dataset(n_semi=3)
        dlg = _stub_dialog(ds, procrustes=True)
        rows = dlg._tps_rows(dlg.ds_ops.object_list)
        _name, landmarks, curves = rows[0]
        # Merged view: 2 fixed + 3 resampled semi-landmarks, and no curve block.
        assert len(landmarks) == 5
        assert curves == []
