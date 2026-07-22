"""Add MdDataset.landmark_name_json.

Per-landmark name/abbreviation and description (JSON), dataset-wide, indexed by
landmark position. Nullable, so existing datasets simply have no landmark names.

Keep this file pure ASCII. peewee_migrate reads migrations with the platform
default encoding, so a non-ASCII byte makes the file undecodable on a Windows
box whose locale is not UTF-8 and the application cannot start (see 006).
"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator

with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def _has_column(database, table, column):
    return any(row[1] == column for row in database.execute_sql(f"PRAGMA table_info({table})"))


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    if fake or not _has_column(database, "mddataset", "landmark_name_json"):
        migrator.add_fields("mddataset", landmark_name_json=pw.CharField(null=True))


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    if fake or _has_column(database, "mddataset", "landmark_name_json"):
        migrator.remove_fields("mddataset", "landmark_name_json")
