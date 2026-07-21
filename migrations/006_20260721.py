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


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    migrator.add_fields("mdanalysis", chart_settings_json=pw.CharField(null=True))


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_fields("mdanalysis", "chart_settings_json")
