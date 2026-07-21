"""Guards on the migration files themselves.

Migrations run before anything else at startup, so a broken one stops the
application from opening at all — and peewee_migrate's error handling replaces
the real cause with "cannot rollback, no transaction is active", leaving nothing
useful in the log. These checks catch the failure modes here instead.
"""

import os
import sys
from pathlib import Path

import pytest
from peewee import SqliteDatabase
from peewee_migrate import Router

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
MIGRATION_FILES = sorted(p for p in MIGRATIONS_DIR.glob("*.py") if not p.name.startswith("__"))


def test_there_are_migrations_to_check():
    assert MIGRATION_FILES, f"no migration files found in {MIGRATIONS_DIR}"


@pytest.mark.parametrize("path", MIGRATION_FILES, ids=lambda p: p.name)
def test_migration_is_pure_ascii(path):
    """peewee_migrate reads migrations with the platform default encoding.

    ``Router.read`` calls ``path.open("r")`` with no encoding, so on a Windows
    machine whose locale is not UTF-8 (cp949, for one) any non-ASCII byte raises
    UnicodeDecodeError and the application cannot start. An em dash in a comment
    is enough — that shipped in 0.1.9 and bricked startup for those users.
    """
    data = path.read_bytes()
    offenders = [(i, hex(b)) for i, b in enumerate(data) if b > 127]
    assert not offenders, (
        f"{path.name} has non-ASCII bytes at {offenders[:5]}; "
        f"migrations must stay ASCII or they cannot be read under a non-UTF-8 locale"
    )


def test_migrations_apply_to_a_fresh_database(tmp_path):
    """The new-install path: every migration in order, on an empty database."""
    db = SqliteDatabase(str(tmp_path / "fresh.db"), pragmas={"foreign_keys": 1})
    db.connect()
    try:
        Router(db, migrate_dir=str(MIGRATIONS_DIR)).run()
        tables = set(db.get_tables())
        assert {"mddataset", "mdobject", "mdimage", "mdthreedmodel", "mdanalysis"} <= tables
    finally:
        db.close()


def test_migrations_are_idempotent_after_an_interrupted_run(tmp_path):
    """A migration whose statements ran but were never recorded must not wedge.

    peewee_migrate writes to migratehistory only once a migration succeeds, so
    an interrupted run leaves the schema changed and the record missing. The
    retry has to cope with that instead of failing on "duplicate column name".
    """
    path = str(tmp_path / "interrupted.db")

    db = SqliteDatabase(path, pragmas={"foreign_keys": 1})
    db.connect()
    Router(db, migrate_dir=str(MIGRATIONS_DIR)).run()
    latest = MIGRATION_FILES[-1].stem
    db.execute_sql("DELETE FROM migratehistory WHERE name = ?", (latest,))
    db.close()

    retry = SqliteDatabase(path, pragmas={"foreign_keys": 1})
    retry.connect()
    try:
        Router(retry, migrate_dir=str(MIGRATIONS_DIR)).run()
        recorded = [row[0] for row in retry.execute_sql("SELECT name FROM migratehistory")]
        assert latest in recorded
    finally:
        retry.close()


def test_chart_settings_column_exists_after_migrating(tmp_path):
    db = SqliteDatabase(str(tmp_path / "cols.db"), pragmas={"foreign_keys": 1})
    db.connect()
    try:
        Router(db, migrate_dir=str(MIGRATIONS_DIR)).run()
        columns = [row[1] for row in db.execute_sql("PRAGMA table_info(mdanalysis)")]
        assert "chart_settings_json" in columns
    finally:
        db.close()
