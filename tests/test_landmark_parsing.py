"""Tests for ``MdObject.unpack_landmark`` blank/missing field handling.

Regression net for the crash where clearing a cell in the ObjectDialog landmark
table produced a short row (``[]`` / ``[x]``), which made every downstream
``lm[0]``/``lm[1]`` access raise ``IndexError``.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peewee import SqliteDatabase

import MdModel
from MdModel import MdDataset, MdDatasetOps, MdObject

test_db = SqliteDatabase(":memory:")


@pytest.fixture
def setup_database():
    MdModel.gDatabase = test_db
    test_db.create_tables([MdDataset, MdObject])
    yield
    test_db.drop_tables([MdDataset, MdObject])
    test_db.close()


@pytest.fixture
def ds_2d(setup_database):
    return MdDataset.create(dataset_name="2D", dataset_desc="d", dimension=2)


@pytest.fixture
def ds_3d(setup_database):
    return MdDataset.create(dataset_name="3D", dataset_desc="d", dimension=3)


def _parse(dataset, landmark_str, name="O"):
    obj = MdObject.create(dataset=dataset, object_name=name, sequence=1, landmark_str=landmark_str)
    obj.unpack_landmark()
    return obj


class TestBlankFieldsKeepPosition:
    """A blank tab/comma field is a missing coordinate, not padding."""

    def test_both_cells_cleared(self, ds_2d):
        obj = _parse(ds_2d, "1.0\t2.0\n\t\n3.0\t4.0")
        assert obj.landmark_list == [[1.0, 2.0], [None, None], [3.0, 4.0]]

    def test_only_y_cleared_keeps_x(self, ds_2d):
        obj = _parse(ds_2d, "1.0\t2.0\n5.0\t\n3.0\t4.0")
        assert obj.landmark_list == [[1.0, 2.0], [5.0, None], [3.0, 4.0]]

    def test_only_x_cleared_keeps_y(self, ds_2d):
        obj = _parse(ds_2d, "1.0\t2.0\n\t5.0")
        assert obj.landmark_list == [[1.0, 2.0], [None, 5.0]]

    def test_comma_separated_blank(self, ds_2d):
        obj = _parse(ds_2d, "1.0,2.0\n,\n3.0,4.0")
        assert obj.landmark_list == [[1.0, 2.0], [None, None], [3.0, 4.0]]

    def test_missing_marker_still_works(self, ds_2d):
        obj = _parse(ds_2d, "1.0\t2.0\nMissing\tMissing")
        assert obj.landmark_list == [[1.0, 2.0], [None, None]]

    def test_z_cleared_in_3d(self, ds_3d):
        obj = _parse(ds_3d, "1\t2\t3\n4\t5\t\n6\t7\t8")
        assert obj.landmark_list == [[1.0, 2.0, 3.0], [4.0, 5.0, None], [6.0, 7.0, 8.0]]


class TestRowWidthNormalisation:
    def test_short_row_padded_to_dimension(self, ds_2d):
        obj = _parse(ds_2d, "1.0\t2.0\n7.0")
        assert obj.landmark_list == [[1.0, 2.0], [7.0, None]]

    def test_2d_row_padded_in_3d_dataset(self, ds_3d):
        obj = _parse(ds_3d, "1\t2\n3\t4")
        assert obj.landmark_list == [[1.0, 2.0, None], [3.0, 4.0, None]]

    def test_trailing_delimiter_trimmed_to_dimension(self, ds_2d):
        # A trailing comma is formatting, not a third coordinate.
        obj = _parse(ds_2d, "1.0,2.0,\n3.0,4.0,")
        assert obj.landmark_list == [[1.0, 2.0], [3.0, 4.0]]

    def test_extra_real_values_are_not_dropped(self, ds_2d):
        # Only trailing None is trimmed; real numbers survive so data loss is
        # never silent.
        obj = _parse(ds_2d, "1.0\t2.0\t9.0")
        assert obj.landmark_list == [[1.0, 2.0, 9.0]]

    def test_every_row_has_at_least_two_slots(self, ds_2d):
        obj = _parse(ds_2d, "5.0\n6.0")
        assert all(len(lm) >= 2 for lm in obj.landmark_list)


class TestWhitespaceSeparatorsUnchanged:
    """Runs of spaces are padding, so their blanks are still discarded."""

    def test_single_space(self, ds_2d):
        assert _parse(ds_2d, "1.0 2.0\n3.0 4.0").landmark_list == [[1.0, 2.0], [3.0, 4.0]]

    def test_multiple_spaces(self, ds_2d):
        assert _parse(ds_2d, "1.0  2.0\n3.0   4.0").landmark_list == [[1.0, 2.0], [3.0, 4.0]]

    def test_empty_landmark_str(self, ds_2d):
        assert _parse(ds_2d, "").landmark_list == []


class TestDownstreamNoLongerCrashes:
    """These three raised IndexError on a cleared cell before the fix."""

    @pytest.fixture
    def dataset_with_cleared_cell(self, ds_2d):
        for i in range(3):
            rows = [f"{i}.0\t{i}.0", "1.0\t2.0", "3.0\t4.0"]
            if i == 0:
                rows[1] = "\t"  # user cleared a cell
            MdObject.create(dataset=ds_2d, object_name=f"O{i}", sequence=i, landmark_str="\n".join(rows))
        return ds_2d

    def test_count_landmarks(self, dataset_with_cleared_cell):
        obj = dataset_with_cleared_cell.object_list[0]
        obj.unpack_landmark()
        assert obj.count_landmarks() == 2  # 3 rows, one missing

    def test_has_missing_landmarks(self, dataset_with_cleared_cell):
        ops = MdDatasetOps(dataset_with_cleared_cell)
        assert ops.has_missing_landmarks() is True

    def test_procrustes_superimposition(self, dataset_with_cleared_cell):
        ops = MdDatasetOps(dataset_with_cleared_cell)
        assert ops.procrustes_superimposition() is True
        remaining = [c for o in ops.object_list for lm in o.landmark_list for c in lm if c is None]
        assert remaining == []  # imputation filled the gap
