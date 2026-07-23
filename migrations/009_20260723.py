"""Add MdObject.curve_anchor_json.

Sparse click anchors for edge-snapped (live-wire) curves (JSON), keyed by curve
id. Present only for snap-traced curves; the dense curve_raw_json is re-derived
by snapping between these anchors when one is edited. Nullable, so existing
objects (hand-traced or imported curves, or none) simply have no anchors.

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
    if fake or not _has_column(database, "mdobject", "curve_anchor_json"):
        migrator.add_fields("mdobject", curve_anchor_json=pw.CharField(null=True))


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    if fake or _has_column(database, "mdobject", "curve_anchor_json"):
        migrator.remove_fields("mdobject", "curve_anchor_json")
