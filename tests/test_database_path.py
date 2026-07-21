"""Choosing the database file with --db.

Every model binds to ``MdModel.gDatabase`` at import time, so pointing the
application at another file takes more than reassigning a path string. It used
to be attempted by setting ``MdModel.DATABASE_PATH``, an attribute nothing ever
read, so ``--db`` was silently ignored and the default database was always used.
"""

import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdModel


def _restore_default(original):
    MdModel.set_database_path(original)


def test_models_follow_the_new_path(tmp_path):
    original = MdModel.database_path
    target = tmp_path / "chosen.db"
    try:
        returned = MdModel.set_database_path(str(target))

        assert returned == str(target)
        assert MdModel.database_path == str(target)
        # The models share this one Database object, so redirecting it moves all
        # of them at once.
        assert MdModel.gDatabase.database == str(target)
        assert MdModel.MdDataset._meta.database is MdModel.gDatabase
    finally:
        _restore_default(original)


def test_writes_land_in_the_chosen_file(tmp_path):
    original = MdModel.database_path
    target = tmp_path / "chosen.db"
    try:
        MdModel.set_database_path(str(target))
        MdModel.gDatabase.connect(reuse_if_open=True)
        MdModel.gDatabase.create_tables([MdModel.MdDataset], safe=True)
        MdModel.MdDataset.create(dataset_name="Written here", dimension=2)
        MdModel.gDatabase.close()

        rows = sqlite3.connect(str(target)).execute("SELECT dataset_name FROM mddataset").fetchall()
        assert rows == [("Written here",)]
    finally:
        _restore_default(original)


def test_missing_directories_are_created(tmp_path):
    original = MdModel.database_path
    target = tmp_path / "nested" / "deeper" / "chosen.db"
    try:
        MdModel.set_database_path(str(target))
        assert target.parent.is_dir()
    finally:
        _restore_default(original)


def test_path_is_absolute_and_user_expanded(tmp_path, monkeypatch):
    original = MdModel.database_path
    monkeypatch.chdir(tmp_path)
    try:
        returned = MdModel.set_database_path("relative.db")
        assert os.path.isabs(returned)
        assert returned == str(tmp_path / "relative.db")
    finally:
        _restore_default(original)


def test_an_open_connection_is_not_left_on_the_old_file(tmp_path):
    original = MdModel.database_path
    first = tmp_path / "first.db"
    second = tmp_path / "second.db"
    try:
        MdModel.set_database_path(str(first))
        MdModel.gDatabase.connect(reuse_if_open=True)

        MdModel.set_database_path(str(second))

        assert MdModel.gDatabase.database == str(second)
        assert MdModel.gDatabase.is_closed()
    finally:
        _restore_default(original)
