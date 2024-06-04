from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext
# In your migrations directory, create a file like 20240604_104500_add_on_delete_cascade.py
def migrate(migrator, database, fake=False, **kwargs):
    # Create the new table with the desired schema and constraints
    migrator.sql("""
        CREATE TABLE new_mdanalysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_name TEXT NOT NULL,
            analysis_desc TEXT,
            dataset_id INTEGER,
            dimension INTEGER DEFAULT 2 NOT NULL,
            wireframe TEXT,
            baseline TEXT,
            polygons TEXT,
            propertyname_str TEXT,
            superimposition_method TEXT NOT NULL,
            object_info_json TEXT,
            raw_landmark_json TEXT,
            superimposed_landmark_json TEXT,
            cva_group_by TEXT,
            pca_analysis_result_json TEXT,
            pca_rotation_matrix_json TEXT,
            pca_eigenvalues_json TEXT,
            cva_analysis_result_json TEXT,
            cva_rotation_matrix_json TEXT,
            cva_eigenvalues_json TEXT,
            manova_group_by TEXT,
            manova_analysis_result_json TEXT,
            created_at DATETIME NOT NULL,
            modified_at DATETIME NOT NULL,
            FOREIGN KEY (dataset_id) REFERENCES mddataset (id) ON DELETE CASCADE
        );
    """)

    # Copy data from the old table to the new table
    migrator.sql("""
        INSERT INTO new_mdanalysis (
            id, analysis_name, analysis_desc, dataset_id, dimension, wireframe,
            baseline, polygons, propertyname_str, superimposition_method, object_info_json,
            raw_landmark_json, superimposed_landmark_json, cva_group_by, pca_analysis_result_json,
            pca_rotation_matrix_json, pca_eigenvalues_json, cva_analysis_result_json, cva_rotation_matrix_json,
            cva_eigenvalues_json, manova_group_by, manova_analysis_result_json, created_at, modified_at
        )
        SELECT 
            id, analysis_name, analysis_desc, dataset_id, dimension, wireframe,
            baseline, polygons, propertyname_str, superimposition_method, object_info_json,
            raw_landmark_json, superimposed_landmark_json, cva_group_by, pca_analysis_result_json,
            pca_rotation_matrix_json, pca_eigenvalues_json, cva_analysis_result_json, cva_rotation_matrix_json,
            cva_eigenvalues_json, manova_group_by, manova_analysis_result_json, created_at, modified_at
        FROM mdanalysis;
    """)

    # Drop the old table
    migrator.sql("DROP TABLE mdanalysis;")

    # Rename the new table to the old table name
    migrator.sql("ALTER TABLE new_mdanalysis RENAME TO mdanalysis;")

def rollback(migrator, database, fake=False, **kwargs):
    # To rollback, we need to reverse the migration steps
    # Create the old table schema
    migrator.sql("""
        CREATE TABLE old_mdanalysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_name TEXT NOT NULL,
            analysis_desc TEXT,
            dataset_id INTEGER,
            dimension INTEGER DEFAULT 2 NOT NULL,
            wireframe TEXT,
            baseline TEXT,
            polygons TEXT,
            propertyname_str TEXT,
            superimposition_method TEXT NOT NULL,
            object_info_json TEXT,
            raw_landmark_json TEXT,
            superimposed_landmark_json TEXT,
            cva_group_by TEXT,
            pca_analysis_result_json TEXT,
            pca_rotation_matrix_json TEXT,
            pca_eigenvalues_json TEXT,
            cva_analysis_result_json TEXT,
            cva_rotation_matrix_json TEXT,
            cva_eigenvalues_json TEXT,
            manova_group_by TEXT,
            manova_analysis_result_json TEXT,
            created_at DATETIME NOT NULL,
            modified_at DATETIME NOT NULL
        );
    """)

    # Copy data from the current table to the old table
    migrator.sql("""
        INSERT INTO old_mdanalysis (
            id, analysis_name, analysis_desc, dataset_id, dimension, wireframe,
            baseline, polygons, propertyname_str, superimposition_method, object_info_json,
            raw_landmark_json, superimposed_landmark_json, cva_group_by, pca_analysis_result_json,
            pca_rotation_matrix_json, pca_eigenvalues_json, cva_analysis_result_json, cva_rotation_matrix_json,
            cva_eigenvalues_json, manova_group_by, manova_analysis_result_json, created_at, modified_at
        )
        SELECT 
            id, analysis_name, analysis_desc, dataset_id, dimension, wireframe,
            baseline, polygons, propertyname_str, superimposition_method, object_info_json,
            raw_landmark_json, superimposed_landmark_json, cva_group_by, pca_analysis_result_json,
            pca_rotation_matrix_json, pca_eigenvalues_json, cva_analysis_result_json, cva_rotation_matrix_json,
            cva_eigenvalues_json, manova_group_by, manova_analysis_result_json, created_at, modified_at
        FROM mdanalysis;
    """)

    # Drop the current table
    migrator.sql("DROP TABLE mdanalysis;")

    # Rename the old table to the current table name
    migrator.sql("ALTER TABLE old_mdanalysis RENAME TO mdanalysis;")
