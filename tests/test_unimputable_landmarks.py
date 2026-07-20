"""A landmark missing in *every* object cannot be estimated from anything.

Procrustes imputes a missing coordinate from the per-coordinate mean of the other
objects. When every object is missing the same coordinate that mean is undefined,
the None survives superimposition, and the failure only surfaced later in the
analysis matrix as `float() argument must be ... not 'NoneType'`.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peewee import SqliteDatabase

import MdModel
from MdModel import MdDataset, MdObject, find_unimputable_landmarks
from ModanController import unimputable_landmarks_message

test_db = SqliteDatabase(":memory:")


@pytest.fixture
def setup_database():
    MdModel.gDatabase = test_db
    test_db.create_tables([MdDataset, MdObject])
    yield
    test_db.drop_tables([MdDataset, MdObject])
    test_db.close()


BASE = [
    ["0\t0", "1\t0", "1\t1", "0\t1"],
    ["0.1\t0.1", "1.1\t0.1", "1.1\t1.1", "0.1\t1.1"],
    ["0.2\t0", "1\t0.2", "1.2\t1", "0\t1.2"],
]


def _dataset(rows, dimension=2):
    ds = MdDataset.create(dataset_name="d", dataset_desc="x", dimension=dimension)
    for i, r in enumerate(rows):
        MdObject.create(dataset=ds, object_name=f"O{i}", sequence=i, landmark_str="\n".join(r))
    return ds


def _rows(**mutations):
    rows = [list(r) for r in BASE]
    for index, value in mutations.items():
        for r in rows:
            r[int(index[1:])] = value
    return rows


class TestDetection:
    def test_landmark_missing_everywhere_is_reported(self, setup_database):
        ds = _dataset(_rows(r2="Missing\tMissing"))
        assert find_unimputable_landmarks(list(ds.object_list)) == [2]

    def test_single_axis_missing_everywhere_still_counts(self, setup_database):
        """X present in every object, Y absent in every object — still unimputable."""
        rows = [list(r) for r in BASE]
        for r in rows:
            r[2] = r[2].split("\t")[0] + "\tMissing"
        ds = _dataset(rows)
        assert find_unimputable_landmarks(list(ds.object_list)) == [2]

    def test_several_landmarks_reported_in_order(self, setup_database):
        ds = _dataset(_rows(r1="Missing\tMissing", r3="Missing\tMissing"))
        assert find_unimputable_landmarks(list(ds.object_list)) == [1, 3]

    def test_missing_in_only_one_object_is_imputable(self, setup_database):
        rows = [list(r) for r in BASE]
        rows[0][2] = "Missing\tMissing"
        ds = _dataset(rows)
        assert find_unimputable_landmarks(list(ds.object_list)) == []

    def test_missing_in_all_but_one_object_is_imputable(self, setup_database):
        rows = [list(r) for r in BASE]
        rows[0][2] = "Missing\tMissing"
        rows[1][2] = "Missing\tMissing"
        ds = _dataset(rows)
        assert find_unimputable_landmarks(list(ds.object_list)) == []

    def test_clean_dataset_reports_nothing(self, setup_database):
        ds = _dataset(BASE)
        assert find_unimputable_landmarks(list(ds.object_list)) == []

    def test_empty_input(self):
        assert find_unimputable_landmarks([]) == []

    def test_single_object_dataset(self, setup_database):
        rows = [["0\t0", "Missing\tMissing"]]
        ds = _dataset(rows)
        # With one object there is no other specimen to borrow from.
        assert find_unimputable_landmarks(list(ds.object_list)) == [1]

    def test_3d_z_axis_missing_everywhere(self, setup_database):
        rows = [
            ["0\t0\t0", "1\t0\tMissing", "1\t1\t1"],
            ["0.1\t0.1\t0.1", "1.1\t0.1\tMissing", "1.1\t1.1\t1.1"],
        ]
        ds = _dataset(rows, dimension=3)
        assert find_unimputable_landmarks(list(ds.object_list)) == [1]


class TestMessage:
    def test_singular_wording(self):
        message = unimputable_landmarks_message([2])
        assert "Landmark 3 is missing in every object" in message
        assert "estimate it from" in message

    def test_plural_wording(self):
        message = unimputable_landmarks_message([1, 3])
        assert "Landmarks 2, 4 are missing in every object" in message
        assert "estimate them from" in message

    def test_numbers_are_one_based(self):
        """Table rows are numbered from 1, so the message must match."""
        assert "Landmark 1 " in unimputable_landmarks_message([0])

    def test_suggests_a_resolution(self):
        message = unimputable_landmarks_message([0])
        assert "at least one object" in message
        assert "remove" in message


class TestGatesBailOut:
    @staticmethod
    def _controller(ds):
        import ModanController

        ModanController.show_warning = lambda *a, **k: None
        c = ModanController.ModanController()
        c.current_dataset = ds
        return c

    def test_analysis_path_raises_instead_of_crashing_later(self, setup_database, qapp):
        ds = _dataset(_rows(r2="Missing\tMissing"))
        with pytest.raises(ValueError) as excinfo:
            self._controller(ds)._prepare_landmarks()
        message = str(excinfo.value)
        assert "Landmark 3" in message
        # Not the opaque downstream failure this replaces.
        assert "NoneType" not in message

    def test_validation_reports_it(self, setup_database, qapp):
        ds = _dataset(_rows(r2="Missing\tMissing"))
        ok, message = self._controller(ds)._validate_dataset_for_analysis_type("PCA")
        assert ok is False
        assert "Landmark 3" in message

    def test_imputable_dataset_still_proceeds(self, setup_database, qapp):
        rows = [list(r) for r in BASE]
        rows[0][2] = "Missing\tMissing"
        ds = _dataset(rows)
        ok, _ = self._controller(ds)._validate_dataset_for_analysis_type("PCA")
        assert ok is True
        ds_ops, landmarks = self._controller(ds)._prepare_landmarks()
        assert all(c is not None for obj in landmarks for lm in obj for c in lm)
