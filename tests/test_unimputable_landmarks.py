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

from MdModel import MdDataset, MdDatasetOps, MdObject, find_unfittable_objects, find_unimputable_landmarks
from ModanController import unfittable_objects_message, unimputable_landmarks_message

test_db = SqliteDatabase(":memory:")


@pytest.fixture
def setup_database(bound_database):
    """Bind the models to an in-memory database for the test.

    Via ``bound_database``, not by assigning ``MdModel.gDatabase``: peewee
    resolves table creation and queries through each model's own
    ``_meta.database``, so reassigning gDatabase alone left this fixture
    creating and dropping tables in the user's real library.
    """
    yield bound_database(test_db, [MdDataset, MdObject])


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


# --------------------------------------------------------------------------- #
# An object that records fewer landmarks than the data have dimensions cannot
# have its gaps estimated either: the similarity fit of the mean shape onto it
# needs that many shared points. The fit used to log a warning and move on,
# and the None surfaced in the analysis matrix just as above (devlog 292).
# --------------------------------------------------------------------------- #


def _sparse_rows(recorded, dimension=2):
    """BASE (or its 3D version) with object 0 keeping only its first `recorded` landmarks."""
    missing = "\t".join(["Missing"] * dimension)
    rows = [list(r) for r in BASE]
    if dimension == 3:
        rows = [[f"{lm}\t{i * 0.1}" for i, lm in enumerate(r)] for r in rows]
    rows[0] = rows[0][:recorded] + [missing] * (len(rows[0]) - recorded)
    return rows


def _unfittable(ds):
    ops = MdDatasetOps(ds)
    return [(obj.object_name, n) for obj, n in find_unfittable_objects(ops.object_list, ops.dimension)]


class TestUnfittableDetection:
    def test_one_recorded_landmark_in_2d_is_reported(self, setup_database):
        assert _unfittable(_dataset(_sparse_rows(1))) == [("O0", 1)]

    def test_two_recorded_landmarks_in_2d_suffice(self, setup_database):
        assert _unfittable(_dataset(_sparse_rows(2))) == []

    def test_3d_needs_three(self, setup_database):
        assert _unfittable(_dataset(_sparse_rows(2, 3), dimension=3)) == [("O0", 2)]
        assert _unfittable(_dataset(_sparse_rows(3, 3), dimension=3)) == []

    def test_a_partly_recorded_landmark_does_not_count(self, setup_database):
        rows = _sparse_rows(2)
        rows[0][1] = "1\tMissing"
        assert _unfittable(_dataset(rows)) == [("O0", 1)]

    def test_complete_objects_are_never_reported(self, setup_database):
        assert _unfittable(_dataset([list(r) for r in BASE])) == []

    def test_traced_curve_points_count_as_recorded(self, setup_database):
        ds = _dataset(_sparse_rows(1))
        ds.set_curve_config([{"id": "c", "n": 4, "method": "equidistant", "start": 4}])
        ds.save()
        for obj in ds.object_list:
            obj.set_curve_raw({"c": [[0, 0], [0.5, 0.2], [1, 0]]})
            obj.save()
        assert _unfittable(ds) == []

    def test_untraced_curve_adds_gaps(self, setup_database):
        """With every fixed landmark recorded but the curve untraced, the object
        records 4 points and misses 4 -- still enough to fit in 2D."""
        ds = _dataset([list(r) for r in BASE])
        ds.set_curve_config([{"id": "c", "n": 4, "method": "equidistant", "start": 4}])
        ds.save()
        assert _unfittable(ds) == []
        ds2 = _dataset(_sparse_rows(1))
        ds2.set_curve_config([{"id": "c", "n": 4, "method": "equidistant", "start": 4}])
        ds2.save()
        assert ("O0", 1) in _unfittable(ds2)


class TestUnfittableMessage:
    def test_singular_wording_names_the_object(self):
        message = unfittable_objects_message([(type("O", (), {"object_name": "Skull 7"})(), 1)], 2)
        assert "Object 'Skull 7' records 1 landmark," in message
        assert "at least 2 recorded landmarks in 2D data" in message

    def test_plural_wording_lists_each_object(self):
        a, b = (type("O", (), {"object_name": n})() for n in ("A", "B"))
        message = unfittable_objects_message([(a, 0), (b, 2)], 3)
        assert "Objects 'A' (0), 'B' (2)" in message
        assert "3D data" in message

    def test_suggests_a_resolution(self):
        message = unfittable_objects_message([(type("O", (), {"object_name": "X"})(), 0)], 2)
        assert "Record more landmarks" in message
        assert "remove" in message


class TestUnfittableGates:
    _controller = staticmethod(TestGatesBailOut._controller)

    def test_analysis_path_raises_instead_of_crashing_later(self, setup_database, qapp):
        ds = _dataset(_sparse_rows(1))
        with pytest.raises(ValueError) as excinfo:
            self._controller(ds)._prepare_landmarks()
        message = str(excinfo.value)
        assert "'O0'" in message
        assert "NoneType" not in message

    def test_validation_reports_it(self, setup_database, qapp):
        ds = _dataset(_sparse_rows(1))
        ok, message = self._controller(ds)._validate_dataset_for_analysis_type("PCA")
        assert ok is False
        assert "'O0'" in message

    def test_fittable_sparse_object_still_proceeds(self, setup_database, qapp):
        ds = _dataset(_sparse_rows(2))
        ok, _ = self._controller(ds)._validate_dataset_for_analysis_type("PCA")
        assert ok is True
        _, landmarks = self._controller(ds)._prepare_landmarks()
        assert all(c is not None for obj in landmarks for lm in obj for c in lm)
