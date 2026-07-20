"""One definition of "do these objects agree on landmark count".

`check_object_list` (the Procrustes gate) and the controller's pre-analysis
validation used to answer this separately and disagree: the controller compared a
missing-*excluding* expected count against missing-*including* actuals, so any
object with a missing landmark failed against itself.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peewee import SqliteDatabase

import MdModel
from MdModel import MdDataset, MdDatasetOps, MdObject, find_landmark_count_mismatch, landmark_position_count

test_db = SqliteDatabase(":memory:")


@pytest.fixture
def setup_database():
    MdModel.gDatabase = test_db
    test_db.create_tables([MdDataset, MdObject])
    yield
    test_db.drop_tables([MdDataset, MdObject])
    test_db.close()


def _dataset(setup_database, rows):
    ds = MdDataset.create(dataset_name="d", dataset_desc="x", dimension=2)
    for i, r in enumerate(rows):
        MdObject.create(dataset=ds, object_name=f"O{i}", sequence=i, landmark_str="\n".join(r))
    return ds


COMPLETE = [
    ["0\t0", "1\t0", "1\t1", "0\t1"],
    ["0.1\t0.1", "1.1\t0.1", "1.1\t1.1", "0.1\t1.1"],
    ["0.2\t0", "1\t0.2", "1.2\t1", "0\t1.2"],
]


class TestLandmarkPositionCount:
    def test_counts_missing_positions(self, setup_database):
        ds = _dataset(setup_database, [["0\t0", "Missing\tMissing", "1\t1"]])
        obj = list(ds.object_list)[0]
        assert landmark_position_count(obj) == 3
        # ...unlike count_landmarks, which reports recorded landmarks.
        assert obj.count_landmarks() == 2

    def test_unpacks_on_demand(self, setup_database):
        ds = _dataset(setup_database, [["0\t0", "1\t1"]])
        obj = list(ds.object_list)[0]
        assert not getattr(obj, "landmark_list", None)
        assert landmark_position_count(obj) == 2

    def test_empty_object(self, setup_database):
        ds = MdDataset.create(dataset_name="e", dataset_desc="x", dimension=2)
        obj = MdObject.create(dataset=ds, object_name="O", sequence=1, landmark_str="")
        assert landmark_position_count(obj) == 0

    def test_works_on_objectops(self, setup_database):
        ds = _dataset(setup_database, COMPLETE)
        ops = MdDatasetOps(ds)
        assert all(landmark_position_count(o) == 4 for o in ops.object_list)


class TestFindLandmarkCountMismatch:
    def test_consistent_returns_none(self, setup_database):
        ds = _dataset(setup_database, COMPLETE)
        assert find_landmark_count_mismatch(list(ds.object_list)) is None

    def test_missing_landmarks_do_not_count_as_a_mismatch(self, setup_database):
        rows = [list(r) for r in COMPLETE]
        rows[0][1] = "Missing\tMissing"
        ds = _dataset(setup_database, rows)
        assert find_landmark_count_mismatch(list(ds.object_list)) is None

    def test_all_objects_missing_the_same_landmark(self, setup_database):
        rows = [list(r) for r in COMPLETE]
        for r in rows:
            r[2] = "Missing\tMissing"
        ds = _dataset(setup_database, rows)
        assert find_landmark_count_mismatch(list(ds.object_list)) is None

    def test_genuinely_short_object_is_reported(self, setup_database):
        rows = [list(r) for r in COMPLETE]
        rows[2] = rows[2][:3]
        ds = _dataset(setup_database, rows)
        mismatch = find_landmark_count_mismatch(list(ds.object_list))
        assert mismatch is not None
        obj, expected, found = mismatch
        assert (obj.object_name, expected, found) == ("O2", 4, 3)

    def test_reports_the_first_offender(self, setup_database):
        rows = [list(r) for r in COMPLETE]
        rows[1] = rows[1][:2]
        rows[2] = rows[2][:3]
        _, expected, found = find_landmark_count_mismatch(list(_dataset(setup_database, rows).object_list))
        assert (expected, found) == (4, 2)

    def test_empty_input(self):
        assert find_landmark_count_mismatch([]) is None

    def test_single_object_is_always_consistent(self, setup_database):
        ds = _dataset(setup_database, [COMPLETE[0]])
        assert find_landmark_count_mismatch(list(ds.object_list)) is None


class TestGatesAgree:
    """The Procrustes gate and the controller validators must give one answer."""

    @staticmethod
    def _controller(ds):
        import ModanController

        ModanController.show_warning = lambda *a, **k: None
        c = ModanController.ModanController()
        c.current_dataset = ds
        return c

    def test_missing_landmarks_pass_every_gate(self, setup_database, qapp):
        rows = [list(r) for r in COMPLETE]
        rows[0][1] = "Missing\tMissing"
        ds = _dataset(setup_database, rows)

        assert MdDatasetOps(ds).check_object_list() is True
        ok, _ = self._controller(ds)._validate_dataset_for_analysis_type("PCA")
        assert ok is True

    def test_short_object_fails_every_gate(self, setup_database, qapp):
        rows = [list(r) for r in COMPLETE]
        rows[2] = rows[2][:3]
        ds = _dataset(setup_database, rows)

        assert MdDatasetOps(ds).check_object_list() is False
        ok, message = self._controller(ds)._validate_dataset_for_analysis_type("PCA")
        assert ok is False
        assert "O2" in message

    def test_clean_dataset_passes(self, setup_database, qapp):
        ds = _dataset(setup_database, COMPLETE)
        assert MdDatasetOps(ds).check_object_list() is True
        ok, _ = self._controller(ds)._validate_dataset_for_analysis_type("PCA")
        assert ok is True


class TestMismatchMessageIsActionable:
    """A rejected dataset must say how to fix it, not just that it is wrong."""

    @staticmethod
    def _short_dataset(setup_database):
        rows = [list(r) for r in COMPLETE]
        rows[2] = rows[2][:3]
        return _dataset(setup_database, rows)

    def test_message_names_object_and_both_counts(self, setup_database):
        from ModanController import landmark_mismatch_message

        ds = self._short_dataset(setup_database)
        message = landmark_mismatch_message(*find_landmark_count_mismatch(list(ds.object_list)))
        assert "O2" in message
        assert "3" in message and "4" in message

    def test_message_points_at_insert_missing(self, setup_database):
        from ModanController import landmark_mismatch_message

        ds = self._short_dataset(setup_database)
        message = landmark_mismatch_message(*find_landmark_count_mismatch(list(ds.object_list)))
        assert "Insert Missing" in message

    def test_validation_uses_the_actionable_message(self, setup_database, qapp):
        import ModanController

        ModanController.show_warning = lambda *a, **k: None
        controller = ModanController.ModanController()
        ds = self._short_dataset(setup_database)
        controller.current_dataset = ds
        ok, message = controller._validate_dataset_for_analysis_type("PCA")
        assert ok is False
        assert "Insert Missing" in message

    def test_analysis_path_uses_the_actionable_message(self, setup_database, qapp):
        """_prepare_landmarks used to raise a bare "Procrustes superimposition
        failed", which named neither the object nor the remedy."""
        import ModanController

        ModanController.show_warning = lambda *a, **k: None
        controller = ModanController.ModanController()
        controller.current_dataset = self._short_dataset(setup_database)
        with pytest.raises(ValueError) as excinfo:
            controller._prepare_landmarks()
        assert "Insert Missing" in str(excinfo.value)
        assert "O2" in str(excinfo.value)

    def test_generic_failure_message_still_available(self, setup_database, qapp):
        """A consistent dataset that still fails Procrustes keeps the old message."""
        import ModanController

        controller = ModanController.ModanController()
        controller.current_dataset = _dataset(setup_database, COMPLETE)
        # Consistent counts, so the mismatch pre-check must not fire.
        assert find_landmark_count_mismatch(list(controller.current_dataset.object_list)) is None
