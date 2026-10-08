"""Add MdAnalysis.cva_accuracy_json.

The CVA's classification accuracy (JSON): cross-validated and resubstitution
accuracy, the chance level, how the accuracy was estimated, and whether the data
were reduced first. It was computed by every run but never stored, so nothing
could show it. Nullable, so analyses saved before this have none.

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

    # Skip if already present. peewee_migrate records a migration only after its
    # statements succeed, so an interrupted run can leave a column added but
    # unrecorded, and the retry then dies on "duplicate column name" (see 006).
    if fake or not _has_column(database, "mdanalysis", "cva_accuracy_json"):
        migrator.add_fields("mdanalysis", cva_accuracy_json=pw.CharField(null=True))


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    if fake or _has_column(database, "mdanalysis", "cva_accuracy_json"):
        migrator.remove_fields("mdanalysis", "cva_accuracy_json")
