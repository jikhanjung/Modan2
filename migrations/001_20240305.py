"""Peewee migrations -- 001_20240305.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    
    @migrator.create_model
    class MdDataset(pw.Model):
        id = pw.AutoField()
        dataset_name = pw.CharField(max_length=255)
        dataset_desc = pw.CharField(max_length=255, null=True)
        dimension = pw.IntegerField(default=2)
        wireframe = pw.CharField(max_length=255, null=True)
        baseline = pw.CharField(max_length=255, null=True)
        polygons = pw.CharField(max_length=255, null=True)
        parent = pw.ForeignKeyField(column_name='parent_id', field='id', model='self', null=True, on_delete='CASCADE')
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()
        propertyname_str = pw.CharField(max_length=255, null=True)

        class Meta:
            table_name = "mddataset"

    @migrator.create_model
    class MdObject(pw.Model):
        id = pw.AutoField()
        object_name = pw.CharField(max_length=255)
        object_desc = pw.CharField(max_length=255, null=True)
        pixels_per_mm = pw.DoubleField(null=True)
        landmark_str = pw.CharField(max_length=255, null=True)
        dataset = pw.ForeignKeyField(column_name='dataset_id', field='id', model=migrator.orm['mddataset'], on_delete='CASCADE')
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()
        property_str = pw.CharField(max_length=255, null=True)

        class Meta:
            table_name = "mdobject"

    @migrator.create_model
    class MdImage(pw.Model):
        id = pw.AutoField()
        original_path = pw.CharField(max_length=255, null=True)
        original_filename = pw.CharField(max_length=255, null=True)
        name = pw.CharField(max_length=255, null=True)
        md5hash = pw.CharField(max_length=255, null=True)
        size = pw.IntegerField(null=True)
        exifdatetime = pw.DateTimeField(null=True)
        file_created = pw.DateTimeField(null=True)
        file_modified = pw.DateTimeField(null=True)
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()
        object = pw.ForeignKeyField(column_name='object_id', field='id', model=migrator.orm['mdobject'], on_delete='CASCADE')

        class Meta:
            table_name = "mdimage"

    @migrator.create_model
    class MdThreeDModel(pw.Model):
        id = pw.AutoField()
        original_path = pw.CharField(max_length=255, null=True)
        original_filename = pw.CharField(max_length=255, null=True)
        name = pw.CharField(max_length=255, null=True)
        md5hash = pw.CharField(max_length=255, null=True)
        size = pw.IntegerField(null=True)
        file_created = pw.DateTimeField(null=True)
        file_modified = pw.DateTimeField(null=True)
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()
        object = pw.ForeignKeyField(column_name='object_id', field='id', model=migrator.orm['mdobject'], on_delete='CASCADE')

        class Meta:
            table_name = "mdthreedmodel"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    
    migrator.remove_model('mdthreedmodel')

    migrator.remove_model('mdimage')

    migrator.remove_model('mdobject')

    migrator.remove_model('mddataset')
