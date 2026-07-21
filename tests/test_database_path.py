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

MIGRATIONS_DIR = __import__("pathlib").Path(__file__).resolve().parent.parent / "migrations"


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


class TestApplicationSetupPicksTheRightDatabase:
    """Startup must not move the database unless asked to.

    0.1.11 substituted ~/.modan2/modan2.db whenever --db was absent — a path the
    application had never used. It came up on an empty file and migrated it from
    001, so every user's data appeared to be gone while it sat untouched under
    PaleoBytes/Modan2/.
    """

    def test_no_db_argument_leaves_the_database_where_it_is(self, monkeypatch):
        from MdAppSetup import ApplicationSetup

        expected = MdModel.database_path
        moved = []
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: moved.append(p))
        monkeypatch.setattr(MdModel, "prepare_database", lambda: None)

        setup = ApplicationSetup()
        setup._prepare_database()

        assert moved == [], f"startup redirected the database to {moved}"
        assert setup.db_path == expected

    def test_db_argument_is_honoured(self, monkeypatch, tmp_path):
        from MdAppSetup import ApplicationSetup

        target = str(tmp_path / "chosen.db")
        moved = []
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: moved.append(p))
        monkeypatch.setattr(MdModel, "prepare_database", lambda: None)

        setup = ApplicationSetup(db_path=target)
        setup._prepare_database()

        assert moved == [target]

    def test_the_default_is_not_under_dot_modan2(self):
        """The invented path that caused it, named so nobody reintroduces it."""
        from MdAppSetup import ApplicationSetup

        setup = ApplicationSetup()

        assert setup.db_path is None
        assert not hasattr(ApplicationSetup, "_get_default_db_path")


class TestDatabaseBackup:
    """prepare_database snapshots the file before migrating it."""

    def _prepare_into(self, monkeypatch, tmp_path, db_file):
        """Run prepare_database with the storage dirs pointed at tmp_path."""
        import MdUtils as mu

        backups = tmp_path / "backups"
        backups.mkdir(exist_ok=True)
        monkeypatch.setattr(mu, "DB_BACKUP_DIRECTORY", str(backups))
        monkeypatch.setattr(MdModel.mu, "DB_BACKUP_DIRECTORY", str(backups))
        MdModel.set_database_path(str(db_file))
        MdModel.prepare_database()
        MdModel.gDatabase.close()
        return backups

    def test_the_backup_predates_the_migration(self, monkeypatch, tmp_path):
        """The point of the snapshot: what the file looked like before."""
        original = MdModel.database_path
        db_file = tmp_path / "Modan2.db"
        try:
            # A database one migration behind.
            from peewee import SqliteDatabase
            from peewee_migrate import Router

            migrations = str(MIGRATIONS_DIR)
            seed = SqliteDatabase(str(db_file))
            seed.connect()
            Router(seed, migrate_dir=migrations).run()
            seed.execute_sql("ALTER TABLE mdanalysis DROP COLUMN chart_settings_json")
            seed.execute_sql("DELETE FROM migratehistory WHERE name = ?", (MIGRATIONS_DIR.name and "006_20260721",))
            seed.close()

            backups = self._prepare_into(monkeypatch, tmp_path, db_file)

            copies = list(backups.glob("Modan2.db.*"))
            assert len(copies) == 1, f"expected one backup, got {copies}"
            backed_up = sqlite3.connect(str(copies[0]))
            assert not any(r[1] == "chart_settings_json" for r in backed_up.execute("PRAGMA table_info(mdanalysis)")), (
                "the backup was taken after the migration, so it cannot undo it"
            )
            # while the live file did get migrated
            live = sqlite3.connect(str(db_file))
            assert any(r[1] == "chart_settings_json" for r in live.execute("PRAGMA table_info(mdanalysis)"))
        finally:
            _restore_default(original)

    def test_backups_are_named_after_the_file_in_use(self, monkeypatch, tmp_path):
        """A database opened with --db must not overwrite the default's backups."""
        original = MdModel.database_path
        try:
            chosen = tmp_path / "chosen.db"
            # First run creates the file; there is nothing to snapshot yet.
            self._prepare_into(monkeypatch, tmp_path, chosen)
            backups = self._prepare_into(monkeypatch, tmp_path, chosen)

            names = [p.name for p in backups.iterdir()]
            assert any(n.startswith("chosen.db.") for n in names), names
            assert not any(n.startswith("Modan2.db.") for n in names), names
        finally:
            _restore_default(original)

    def test_a_new_database_has_nothing_to_back_up(self, monkeypatch, tmp_path):
        original = MdModel.database_path
        try:
            backups = self._prepare_into(monkeypatch, tmp_path, tmp_path / "brand_new.db")
            assert list(backups.iterdir()) == []
        finally:
            _restore_default(original)
