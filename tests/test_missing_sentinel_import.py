"""Tests for -999 sentinel detection/conversion on import."""

import os
import sys
from typing import ClassVar

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdUtils as mu


class TestFindMissingSentinels:
    def test_finds_sentinel_in_both_columns(self):
        data = {"A": [[1.0, 2.0], [-999.0, -999.0], [3.0, 4.0]]}
        assert mu.find_missing_sentinels(data) == [("A", 1, 0), ("A", 1, 1)]

    def test_finds_sentinel_in_one_column_only(self):
        data = {"A": [[1.0, -999.0]]}
        assert mu.find_missing_sentinels(data) == [("A", 0, 1)]

    def test_no_sentinel_returns_empty(self):
        data = {"A": [[1.0, 2.0], [3.0, 4.0]]}
        assert mu.find_missing_sentinels(data) == []

    def test_scans_every_object(self):
        data = {"A": [[-999.0, 1.0]], "B": [[2.0, 3.0]], "C": [[4.0, -999.0]]}
        assert mu.find_missing_sentinels(data) == [("A", 0, 0), ("C", 0, 1)]

    def test_three_d_z_column(self):
        data = {"A": [[1.0, 2.0, -999.0]]}
        assert mu.find_missing_sentinels(data) == [("A", 0, 2)]

    def test_integer_sentinel_matches(self):
        data = {"A": [[-999, 1.0]]}
        assert mu.find_missing_sentinels(data) == [("A", 0, 0)]

    def test_non_numeric_values_are_skipped(self):
        data = {"A": [[None, "x"], [-999.0, 1.0]]}
        assert mu.find_missing_sentinels(data) == [("A", 1, 0)]

    def test_near_miss_not_matched(self):
        data = {"A": [[-999.5, -99.0, 999.0]]}
        assert mu.find_missing_sentinels(data) == []

    def test_custom_sentinel(self):
        data = {"A": [[-9999.0, 1.0]]}
        assert mu.find_missing_sentinels(data, sentinel=-9999.0) == [("A", 0, 0)]


class TestInvertedY:
    """The readers negate Y before detection runs, so a Y sentinel reads as +999."""

    def test_inverted_y_sentinel_found_in_y_column(self):
        data = {"A": [[1.0, 999.0]]}
        assert mu.find_missing_sentinels(data, inverted_y=True) == [("A", 0, 1)]

    def test_inverted_y_leaves_x_column_rule_alone(self):
        data = {"A": [[-999.0, 999.0]]}
        assert mu.find_missing_sentinels(data, inverted_y=True) == [("A", 0, 0), ("A", 0, 1)]

    def test_inverted_y_does_not_match_negative_y(self):
        # -999 in Y would have been +999 in the file: a real coordinate.
        data = {"A": [[1.0, -999.0]]}
        assert mu.find_missing_sentinels(data, inverted_y=True) == []

    def test_without_invert_y_positive_999_is_real(self):
        data = {"A": [[1.0, 999.0]]}
        assert mu.find_missing_sentinels(data) == []

    def test_inverted_y_does_not_affect_z(self):
        data = {"A": [[1.0, 2.0, -999.0]]}
        assert mu.find_missing_sentinels(data, inverted_y=True) == [("A", 0, 2)]


class TestReplaceMissingSentinels:
    def test_replaces_only_the_hits(self):
        data = {"A": [[1.0, 2.0], [-999.0, -999.0]]}
        mu.replace_missing_sentinels(data, mu.find_missing_sentinels(data))
        assert data == {"A": [[1.0, 2.0], [None, None]]}

    def test_partial_replacement_keeps_sibling_coordinate(self):
        data = {"A": [[1.0, -999.0]]}
        mu.replace_missing_sentinels(data, mu.find_missing_sentinels(data))
        assert data == {"A": [[1.0, None]]}

    def test_empty_hits_is_a_noop(self):
        data = {"A": [[1.0, 2.0]]}
        mu.replace_missing_sentinels(data, [])
        assert data == {"A": [[1.0, 2.0]]}

    def test_mutates_in_place_and_returns_same_object(self):
        data = {"A": [[-999.0, 1.0]]}
        assert mu.replace_missing_sentinels(data, mu.find_missing_sentinels(data)) is data


class _Settings:
    """Stand-in for QSettings: records what the dialog remembers."""

    def __init__(self, stored=None):
        self._store = {} if stored is None else dict(stored)

    def value(self, key, default=None):
        return self._store.get(key, default)

    def setValue(self, key, value):
        self._store[key] = value


class _ImportData:
    def __init__(self, landmark_data):
        self.landmark_data = landmark_data


class TestResolveMissingSentinels:
    """The ask / remember / convert decision, with the message box stubbed out."""

    @pytest.fixture
    def dialog(self):
        from dialogs.import_dialog import ImportDatasetDialog

        dlg = ImportDatasetDialog.__new__(ImportDatasetDialog)
        dlg.m_app = type("App", (), {})()
        dlg.m_app.settings = _Settings()
        dlg.asked = 0
        return dlg

    def _stub_answer(self, dialog, answer, always=False):
        def _ask(count):
            dialog.asked += 1
            dialog.last_count = count
            return answer, always

        dialog._ask_about_sentinels = _ask

    def test_no_sentinel_does_not_ask(self, dialog):
        self._stub_answer(dialog, True)
        data = _ImportData({"A": [[1.0, 2.0]]})
        assert dialog._resolve_missing_sentinels(data, False) is True
        assert dialog.asked == 0
        assert data.landmark_data == {"A": [[1.0, 2.0]]}

    def test_yes_converts_to_none(self, dialog):
        self._stub_answer(dialog, True)
        data = _ImportData({"A": [[1.0, -999.0]]})
        assert dialog._resolve_missing_sentinels(data, False) is True
        assert dialog.asked == 1
        assert data.landmark_data == {"A": [[1.0, None]]}

    def test_no_keeps_literal_values(self, dialog):
        self._stub_answer(dialog, False)
        data = _ImportData({"A": [[1.0, -999.0]]})
        assert dialog._resolve_missing_sentinels(data, False) is True
        assert data.landmark_data == {"A": [[1.0, -999.0]]}

    def test_cancel_aborts_the_import(self, dialog):
        self._stub_answer(dialog, None)
        data = _ImportData({"A": [[1.0, -999.0]]})
        assert dialog._resolve_missing_sentinels(data, False) is False
        # Untouched — nothing should be converted on an aborted import.
        assert data.landmark_data == {"A": [[1.0, -999.0]]}

    def test_reports_the_hit_count(self, dialog):
        self._stub_answer(dialog, True)
        dialog._resolve_missing_sentinels(_ImportData({"A": [[-999.0, -999.0], [1.0, -999.0]]}), False)
        assert dialog.last_count == 3

    def test_always_is_remembered(self, dialog):
        from dialogs.import_dialog import SENTINEL_SETTING_KEY

        self._stub_answer(dialog, True, always=True)
        dialog._resolve_missing_sentinels(_ImportData({"A": [[1.0, -999.0]]}), False)
        assert dialog.m_app.settings.value(SENTINEL_SETTING_KEY) is True

    def test_without_always_nothing_is_remembered(self, dialog):
        from dialogs.import_dialog import SENTINEL_SETTING_KEY

        self._stub_answer(dialog, True, always=False)
        dialog._resolve_missing_sentinels(_ImportData({"A": [[1.0, -999.0]]}), False)
        assert dialog.m_app.settings.value(SENTINEL_SETTING_KEY) is None

    def test_remembered_yes_skips_the_prompt(self, dialog):
        from dialogs.import_dialog import SENTINEL_SETTING_KEY

        dialog.m_app.settings = _Settings({SENTINEL_SETTING_KEY: True})
        self._stub_answer(dialog, False)  # would say no if asked
        data = _ImportData({"A": [[1.0, -999.0]]})
        dialog._resolve_missing_sentinels(data, False)
        assert dialog.asked == 0
        assert data.landmark_data == {"A": [[1.0, None]]}

    def test_remembered_no_skips_the_prompt(self, dialog):
        from dialogs.import_dialog import SENTINEL_SETTING_KEY

        dialog.m_app.settings = _Settings({SENTINEL_SETTING_KEY: False})
        self._stub_answer(dialog, True)
        data = _ImportData({"A": [[1.0, -999.0]]})
        dialog._resolve_missing_sentinels(data, False)
        assert dialog.asked == 0
        assert data.landmark_data == {"A": [[1.0, -999.0]]}

    def test_remembered_value_survives_qsettings_stringification(self, dialog):
        """QSettings hands booleans back as "true"/"false" strings."""
        from dialogs.import_dialog import SENTINEL_SETTING_KEY

        dialog.m_app.settings = _Settings({SENTINEL_SETTING_KEY: "true"})
        self._stub_answer(dialog, False)
        data = _ImportData({"A": [[1.0, -999.0]]})
        dialog._resolve_missing_sentinels(data, False)
        assert dialog.asked == 0
        assert data.landmark_data == {"A": [[1.0, None]]}

    def test_invert_y_is_passed_through(self, dialog):
        self._stub_answer(dialog, True)
        data = _ImportData({"A": [[1.0, 999.0]]})
        dialog._resolve_missing_sentinels(data, True)
        assert data.landmark_data == {"A": [[1.0, None]]}

    def test_missing_landmark_data_attribute_is_tolerated(self, dialog):
        self._stub_answer(dialog, True)
        assert dialog._resolve_missing_sentinels(object(), False) is True
        assert dialog.asked == 0


class TestControllerSerialisation:
    """None must reach the DB as the 'Missing' marker, not the string 'None'."""

    @pytest.fixture
    def imported_object(self, tmp_path):
        from peewee import SqliteDatabase

        import MdModel
        from MdModel import MdDataset, MdObject
        from ModanController import ModanController

        db = SqliteDatabase(":memory:")
        MdModel.gDatabase = db
        db.create_tables([MdDataset, MdObject])

        class _ImportData:
            dimension = 2
            nobjects = 1
            variablename_list: ClassVar = []
            edge_list: ClassVar = []
            object_name_list: ClassVar = ["A"]
            object_comment: ClassVar = {}
            object_images: ClassVar = {}
            landmark_data: ClassVar = {"A": [[1.0, 2.0], [None, None], [3.0, None]]}

        controller = ModanController()
        dataset = controller.import_dataset(_ImportData(), "ds", str(tmp_path))
        obj = list(dataset.object_list)[0]
        yield obj
        db.drop_tables([MdDataset, MdObject])
        db.close()

    def test_none_is_stored_as_missing_marker(self, imported_object):
        assert "None" not in imported_object.landmark_str
        assert "Missing" in imported_object.landmark_str

    def test_round_trips_back_to_none(self, imported_object):
        imported_object.unpack_landmark()
        assert imported_object.landmark_list == [[1.0, 2.0], [None, None], [3.0, None]]
