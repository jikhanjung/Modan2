"""Tests for dataset-wide landmark names/abbreviations."""

import os
import sys
import tempfile

import pytest
from peewee import SqliteDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdModel as mm
from components.viewers.object_viewer_2d import ObjectViewer2D
from dialogs.landmark_name_dialog import LandmarkNameDialog


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


NAMES = [{"name": "CR1", "desc": "cranial right 1"}, {"name": "CL1", "desc": "cranial left 1"}]


class TestLandmarkNameModel:
    def test_round_trip(self, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        ds.set_landmark_names(NAMES)
        ds.save()
        assert mm.MdDataset.get_by_id(ds.id).get_landmark_names() == NAMES

    def test_default_empty(self, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        assert ds.get_landmark_names() == []

    def test_trailing_blank_entries_trimmed(self, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        ds.set_landmark_names([{"name": "S1", "desc": ""}, {"name": "", "desc": ""}, {"name": "", "desc": ""}])
        assert ds.get_landmark_names() == [{"name": "S1", "desc": ""}]

    def test_all_blank_clears(self, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        ds.set_landmark_names([{"name": "", "desc": ""}])
        assert ds.landmark_name_json is None
        assert ds.get_landmark_names() == []

    def test_corrupt_json_yields_empty(self, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        ds.landmark_name_json = "not json"
        assert ds.get_landmark_names() == []


class TestLandmarkNameDialog:
    def test_loads_existing_and_saves(self, qtbot, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        ds.set_landmark_names(NAMES)
        ds.save()
        dlg = LandmarkNameDialog(None, ds, landmark_count=3)
        qtbot.addWidget(dlg)
        # Sized to max(count, existing names); existing loaded into rows.
        assert dlg.table.rowCount() == 3
        assert dlg.table.item(0, 1).text() == "CR1"
        # Edit row 3 and save.
        dlg.table.item(2, 1).setText("S1")
        dlg.accept_names()
        saved = mm.MdDataset.get_by_id(ds.id).get_landmark_names()
        assert saved[2] == {"name": "S1", "desc": ""}


class TestViewerLandmarkLabel:
    class _Dlg:
        def __init__(self, dataset):
            self.dataset = dataset

    def test_label_uses_name_when_enabled(self, qtbot, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        ds.set_landmark_names(NAMES)
        v = ObjectViewer2D()
        qtbot.addWidget(v)
        v.object_dialog = self._Dlg(ds)
        v.show_landmark_name = True
        names = v._landmark_names()
        assert v._landmark_label(0, names) == "CR1"
        # Beyond the named entries falls back to the index number.
        assert v._landmark_label(5, names) == "6"

    def test_label_uses_index_when_disabled(self, qtbot, test_database):
        ds = mm.MdDataset.create(dataset_name="D", dimension=2)
        ds.set_landmark_names(NAMES)
        v = ObjectViewer2D()
        qtbot.addWidget(v)
        v.object_dialog = self._Dlg(ds)
        v.show_landmark_name = False
        assert v._landmark_label(0, []) == "1"
