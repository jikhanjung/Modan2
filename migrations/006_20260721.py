"""Add MdAnalysis.chart_settings_json.

Holds how the user arranged the chart for an analysis — legend entry order and
the dragged legend position, keyed by grouping variable. Nullable, so existing
analyses simply have no saved arrangement.
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

    # Skip when the column is already there. peewee_migrate records a migration
    # only after its statements succeed, so an interrupted run can leave the
    # column added but unrecorded — and the retry then dies on "duplicate column
    # name". Worse, its error handler calls rollback() on a connection with no
    # active transaction, so the real cause is replaced by "cannot roll back, no
    # transaction is active" and startup fails with nothing useful in the log.
    # In fake mode the database is mocked, so only the migrator state is built.
    if not fake and _has_column(database, "mdanalysis", "chart_settings_json"):
        return

    migrator.add_fields("mdanalysis", chart_settings_json=pw.CharField(null=True))


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    if not fake and not _has_column(database, "mdanalysis", "chart_settings_json"):
        return

    migrator.remove_fields("mdanalysis", "chart_settings_json")
