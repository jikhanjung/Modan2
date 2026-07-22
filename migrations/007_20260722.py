"""Add semi-landmark curve fields.

Adds three nullable JSON-in-text columns that back curve-based semi-landmarks:
  - mddataset.curve_config_json  : the dataset's curve configuration (count,
    resample method and landmark start index per curve).
  - mdobject.curve_raw_json      : per-object raw digitized curve traces, the
    dense polyline traced before resampling. Optional.
  - mdanalysis.curve_config_json : a snapshot of the dataset config at analysis
    time, so an analysis stays reproducible if the dataset changes later.
All nullable, so existing datasets/objects/analyses simply have no curves.

Keep this file pure ASCII. peewee_migrate reads migrations with
``path.open("r")``, i.e. the platform default encoding, so a non-ASCII byte
makes the file undecodable on a Windows box whose locale is not UTF-8 (cp949
here) and the application cannot start at all.
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

    # Skip columns already present. peewee_migrate records a migration only after
    # its statements succeed, so an interrupted run can leave a column added but
    # unrecorded, and the retry then dies on "duplicate column name" (see 006).
    # In fake mode the database is mocked, so only the migrator state is built.
    if fake or not _has_column(database, "mddataset", "curve_config_json"):
        migrator.add_fields("mddataset", curve_config_json=pw.CharField(null=True))
    if fake or not _has_column(database, "mdobject", "curve_raw_json"):
        migrator.add_fields("mdobject", curve_raw_json=pw.CharField(null=True))
    if fake or not _has_column(database, "mdanalysis", "curve_config_json"):
        migrator.add_fields("mdanalysis", curve_config_json=pw.CharField(null=True))


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    if fake or _has_column(database, "mddataset", "curve_config_json"):
        migrator.remove_fields("mddataset", "curve_config_json")
    if fake or _has_column(database, "mdobject", "curve_raw_json"):
        migrator.remove_fields("mdobject", "curve_raw_json")
    if fake or _has_column(database, "mdanalysis", "curve_config_json"):
        migrator.remove_fields("mdanalysis", "curve_config_json")
