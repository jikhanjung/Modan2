"""Peewee migrations -- 003_20240409.py.

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
    
    migrator.add_fields(
        'mdanalysis',

        cva_group_by=pw.CharField(max_length=255, null=True),
        pca_eigenvalues_json=pw.CharField(max_length=255, null=True),
        pca_rotation_matrix_json=pw.CharField(max_length=255, null=True),
        cva_eigenvalues_json=pw.CharField(max_length=255, null=True),
        manova_group_by=pw.CharField(max_length=255, null=True),
        pca_analysis_result_json=pw.CharField(max_length=255, null=True),
        cva_rotation_matrix_json=pw.CharField(max_length=255, null=True),
        manova_analysis_result_json=pw.CharField(max_length=255, null=True),
        cva_analysis_result_json=pw.CharField(max_length=255, null=True))

    migrator.remove_fields('mdanalysis', 'rotation_matrix_json', 'analysis_result_json', 'analysis_method', 'virtual_specimens_json', 'eigenvalues_json', 'group_by')


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    
    migrator.add_fields(
        'mdanalysis',

        rotation_matrix_json=pw.CharField(max_length=255, null=True),
        analysis_result_json=pw.CharField(max_length=255, null=True),
        analysis_method=pw.CharField(max_length=255),
        virtual_specimens_json=pw.CharField(max_length=255, null=True),
        eigenvalues_json=pw.CharField(max_length=255, null=True),
        group_by=pw.CharField(max_length=255, null=True))

    migrator.remove_fields('mdanalysis', 'cva_group_by', 'pca_eigenvalues_json', 'pca_rotation_matrix_json', 'cva_eigenvalues_json', 'manova_group_by', 'pca_analysis_result_json', 'cva_rotation_matrix_json', 'manova_analysis_result_json', 'cva_analysis_result_json')
