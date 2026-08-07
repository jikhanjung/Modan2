"""Backing up the whole library, and restoring it.

The rotating database backups protect against the wrong thing: they cover the
database but not the media, and they live on the same disk as the library, so
the one failure they cannot survive is the likely one. This is the answer to
that — a single archive the user can put on another disk, or in a synchronised
folder, which is safe for a snapshot in a way a live database is not.

Two properties carry most of the weight here, and both are about not lying to
the user:

* **A backup is complete or it is not written.** An interrupted run leaves no
  file, because believing you have a backup you do not have is worse than
  knowing you have none. And media the database knows about but the disk has
  lost is *reported*, not logged and forgotten.
* **Restoring adds; it never replaces.** A restore started by mistake cannot
  destroy anything — which is exactly what wiping the library first would make
  possible.
"""

import datetime
import json
import os
import sys
import tempfile
import zipfile

import pytest
from peewee import SqliteDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdModel as mm
import MdUtils as mu


@pytest.fixture
def test_database():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        path = tmp.name
    db = SqliteDatabase(path, pragmas={"foreign_keys": 1})
    models = [mm.MdDataset, mm.MdObject, mm.MdImage, mm.MdThreeDModel, mm.MdAnalysis]
    originals = {m: m._meta.database for m in models}
    original_g = mm.gDatabase
    mm.gDatabase = db
    for m in models:
        m._meta.database = db
    db.connect()
    db.create_tables(models)
    yield db
    db.drop_tables(models)
    db.close()
    mm.gDatabase = original_g
    for m in models:
        m._meta.database = originals[m]
    os.unlink(path)


@pytest.fixture
def storage(tmp_path, monkeypatch):
    """Point the single storage resolver at a temp directory."""
    directory = str(tmp_path / "storage")
    os.makedirs(directory, exist_ok=True)
    monkeypatch.setattr(mu, "get_storage_directory", lambda: directory)
    return directory


def _png(path, size=(24, 18)):
    from PIL import Image

    Image.new("RGB", size, (200, 40, 40)).save(str(path))
    return str(path)


@pytest.fixture
def library(test_database, storage, tmp_path):
    """Two datasets: one with an attached image and a saved analysis."""
    first = mm.MdDataset.create(dataset_name="Trilobites", dimension=2, landmark_count=3)
    obj = mm.MdObject.create(object_name="Specimen 1", dataset=first, sequence=1)
    obj.landmark_str = "1.0\t2.0\n3.0\t4.0\n5.0\t6.0"
    obj.save()
    image = mm.MdImage()
    image.object = obj
    image.add_file(_png(tmp_path / "spec1.png"))
    image.save()

    mm.MdAnalysis.create(
        analysis_name="PCA run 1",
        analysis_desc="the one in the paper",
        dataset=first,
        dimension=2,
        superimposition_method="Procrustes",
        pca_analysis_result_json=json.dumps([[0.1, 0.2], [0.3, 0.4]]),
        pca_eigenvalues_json=json.dumps([0.9, 0.1]),
        superimposed_landmark_json=json.dumps([[[1.0, 2.0]], [[3.0, 4.0]]]),
        created_at=datetime.datetime(2026, 3, 14, 9, 30, 0),
    )

    second = mm.MdDataset.create(dataset_name="Ammonites", dimension=2, landmark_count=2)
    other = mm.MdObject.create(object_name="Specimen 2", dataset=second, sequence=1)
    other.landmark_str = "7.0\t8.0\n9.0\t10.0"
    other.save()

    return first, second


class TestCreatingABackup:
    def test_it_holds_every_dataset(self, library, tmp_path):
        out = str(tmp_path / "backup.zip")

        result = mu.create_library_backup(out)

        assert len(result.datasets) == 2
        with zipfile.ZipFile(out) as zf:
            members = zf.namelist()
        assert mu.LIBRARY_BACKUP_MANIFEST in members
        assert len([m for m in members if m.startswith("datasets/")]) == 2

    def test_the_manifest_describes_what_is_inside(self, library, tmp_path):
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)

        manifest = mu.read_library_backup_manifest(out)

        assert manifest["format_version"] == mu.LIBRARY_BACKUP_FORMAT_VERSION
        assert manifest["dataset_count"] == 2
        assert {d["name"] for d in manifest["datasets"]} == {"Trilobites", "Ammonites"}
        assert manifest["datasets"][0]["object_count"] == 1

    def test_the_manifest_states_what_is_in_and_out(self, library, tmp_path):
        """Written into the archive rather than only said in a dialog, so the
        boundary survives being read years later by someone who never saw it."""
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)

        manifest = mu.read_library_backup_manifest(out)

        assert "analyses" in manifest["includes"]
        assert "landmarks" in manifest["includes"]
        assert "analyses" not in manifest["excludes"]

    def test_the_manifest_counts_the_analyses(self, library, tmp_path):
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)

        manifest = mu.read_library_backup_manifest(out)
        by_name = {d["name"]: d for d in manifest["datasets"]}

        assert by_name["Trilobites"]["analysis_count"] == 1
        assert by_name["Ammonites"]["analysis_count"] == 0

    def test_an_empty_library_is_refused(self, test_database, storage, tmp_path):
        """Writing a backup of nothing would be indistinguishable from a backup
        that failed to find anything."""
        with pytest.raises(mu.LibraryBackupError, match="nothing to back up"):
            mu.create_library_backup(str(tmp_path / "backup.zip"))

    def test_media_the_disk_has_lost_is_reported(self, library, tmp_path, storage):
        """The database still references the image; the file is gone. Silently
        omitting it would hand the user a backup with a hole in it."""
        first, _ = library
        attached = mm.MdImage.select().first()
        os.remove(attached.get_file_path())

        result = mu.create_library_backup(str(tmp_path / "backup.zip"))

        assert result.missing_files
        assert "Trilobites" in result.missing_files[0]
        assert not result.complete

    def test_nothing_is_left_behind_when_it_fails(self, library, tmp_path, monkeypatch):
        """A truncated file at the chosen path would look like a backup."""
        out = str(tmp_path / "backup.zip")

        def explode(*args, **kwargs):
            raise OSError(28, "No space left on device")

        monkeypatch.setattr(mu.zipfile, "ZipFile", explode)

        with pytest.raises(mu.LibraryBackupError):
            mu.create_library_backup(out)

        assert not os.path.exists(out)
        assert not os.path.exists(out + ".partial")

    def test_cancelling_writes_no_file(self, library, tmp_path):
        out = str(tmp_path / "backup.zip")

        result = mu.create_library_backup(out, should_cancel=lambda: True)

        assert result.cancelled
        assert not os.path.exists(out)

    def test_progress_is_reported(self, library, tmp_path):
        seen = []
        mu.create_library_backup(
            str(tmp_path / "backup.zip"),
            progress_callback=lambda done, total, label: seen.append((done, total)),
        )

        assert seen
        assert seen[-1][0] == seen[-1][1]

    def test_awkward_dataset_names_do_not_break_the_archive(self, test_database, storage, tmp_path):
        """Dataset names are user text and reach the archive as member names."""
        mm.MdDataset.create(dataset_name='bad/name: "with" <chars>', dimension=2, landmark_count=1)

        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)

        manifest = mu.read_library_backup_manifest(out)
        member = manifest["datasets"][0]["file"]
        assert not set(member.replace("datasets/", "")) & set('<>:"\\|?*')
        with zipfile.ZipFile(out) as zf:
            assert member in zf.namelist()
        # The real name survives in the manifest even though the file name cannot
        assert manifest["datasets"][0]["name"] == 'bad/name: "with" <chars>'


class TestReadingABackup:
    def test_a_file_that_is_not_a_backup_is_rejected(self, tmp_path):
        not_a_backup = tmp_path / "notes.zip"
        with zipfile.ZipFile(not_a_backup, "w") as zf:
            zf.writestr("hello.txt", "not a backup")

        with pytest.raises(mu.LibraryBackupError, match="not a Modan2 library backup"):
            mu.read_library_backup_manifest(str(not_a_backup))

    def test_a_manifest_without_datasets_is_rejected(self, tmp_path):
        wrong = tmp_path / "wrong.zip"
        with zipfile.ZipFile(wrong, "w") as zf:
            zf.writestr(mu.LIBRARY_BACKUP_MANIFEST, json.dumps({"format_version": "1.0"}))

        with pytest.raises(mu.LibraryBackupError, match="no dataset list"):
            mu.read_library_backup_manifest(str(wrong))

    def test_a_plain_file_is_rejected(self, tmp_path):
        plain = tmp_path / "photo.zip"
        plain.write_bytes(b"not a zip at all")

        with pytest.raises(mu.LibraryBackupError):
            mu.read_library_backup_manifest(str(plain))


class TestRestoring:
    def test_the_round_trip_brings_the_data_back(self, library, tmp_path, storage):
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)
        # Wipe the library, as a failed disk would
        mm.MdObject.delete().execute()
        mm.MdImage.delete().execute()
        mm.MdDataset.delete().execute()

        result = mu.restore_library_backup(out)

        assert len(result.datasets) == 2
        assert {d.dataset_name for d in mm.MdDataset.select()} == {"Trilobites", "Ammonites"}
        restored = mm.MdObject.get(mm.MdObject.object_name == "Specimen 1")
        restored.unpack_landmark()
        assert restored.landmark_list[0] == [1.0, 2.0]

    def test_media_comes_back_too(self, library, tmp_path, storage):
        """Landmarks without their images would be a restore in name only."""
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)
        mm.MdObject.delete().execute()
        mm.MdImage.delete().execute()
        mm.MdDataset.delete().execute()

        mu.restore_library_backup(out)

        image = mm.MdImage.select().first()
        assert image is not None
        assert os.path.exists(image.get_file_path())

    def test_saved_analyses_come_back(self, library, tmp_path, storage):
        """A backup is not allowed to be lossy. "You can recompute it" is not
        the same as still having the analysis that was actually run."""
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)
        mm.MdAnalysis.delete().execute()
        mm.MdObject.delete().execute()
        mm.MdImage.delete().execute()
        mm.MdDataset.delete().execute()

        mu.restore_library_backup(out)

        analysis = mm.MdAnalysis.get(mm.MdAnalysis.analysis_name == "PCA run 1")
        assert analysis.analysis_desc == "the one in the paper"
        assert analysis.superimposition_method == "Procrustes"
        assert json.loads(analysis.pca_analysis_result_json) == [[0.1, 0.2], [0.3, 0.4]]
        assert json.loads(analysis.pca_eigenvalues_json) == [0.9, 0.1]
        assert analysis.dataset.dataset_name == "Trilobites"

    def test_an_analysis_keeps_the_date_it_was_run(self, library, tmp_path, storage):
        """An analysis is dated evidence. Restoring it with today's date would
        misrepresent when the work was done."""
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)
        mm.MdAnalysis.delete().execute()
        mm.MdObject.delete().execute()
        mm.MdImage.delete().execute()
        mm.MdDataset.delete().execute()

        mu.restore_library_backup(out)

        analysis = mm.MdAnalysis.get(mm.MdAnalysis.analysis_name == "PCA run 1")
        assert analysis.created_at.date() == datetime.date(2026, 3, 14)

    def test_export_still_leaves_analyses_out(self, library, tmp_path, storage):
        """Handing a dataset to a colleague should not carry every object's
        landmarks a second time. The flag defaults off for exactly that."""
        first, _ = library
        package = str(tmp_path / "one-dataset.zip")

        mu.create_zip_package(first.id, package)

        assert "analyses" not in mu.read_json_from_zip(package)

    def test_a_package_without_analyses_still_imports(self, library, tmp_path, storage):
        """Packages written before schema 1.3 have no analyses key at all."""
        first, _ = library
        package = str(tmp_path / "old-style.zip")
        mu.create_zip_package(first.id, package, include_analyses=False)

        new_id = mu.import_dataset_from_zip(package)

        assert mm.MdAnalysis.select().where(mm.MdAnalysis.dataset == new_id).count() == 0
        assert mm.MdObject.select().where(mm.MdObject.dataset == new_id).count() == 1

    def test_restoring_adds_and_never_replaces(self, library, tmp_path, storage):
        """The property that makes a mistaken restore harmless."""
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)
        before = mm.MdDataset.select().count()

        mu.restore_library_backup(out)

        assert mm.MdDataset.select().count() == before + 2
        # The originals are still there, untouched, beside the copies
        assert mm.MdDataset.select().where(mm.MdDataset.dataset_name == "Trilobites").count() == 1

    def test_a_name_already_taken_gets_a_new_one(self, library, tmp_path, storage):
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)

        mu.restore_library_backup(out)

        names = [d.dataset_name for d in mm.MdDataset.select()]
        assert len(names) == len(set(names)), "restoring must not create duplicate names"

    def test_one_bad_dataset_does_not_stop_the_others(self, library, tmp_path, storage):
        """Each import is its own transaction, so stopping would deny the user
        the datasets that were fine."""
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)
        broken = str(tmp_path / "broken.zip")
        with zipfile.ZipFile(out) as src, zipfile.ZipFile(broken, "w") as dst:
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename.endswith(".zip") and "0001" in item.filename:
                    data = b"corrupt"
                dst.writestr(item, data)

        result = mu.restore_library_backup(broken)

        assert len(result.datasets) == 1
        assert len(result.failed) == 1
        assert result.failed[0]["name"] == "Trilobites"
        assert not result.complete

    def test_a_missing_member_is_a_failure_not_a_crash(self, library, tmp_path, storage):
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)
        stripped = str(tmp_path / "stripped.zip")
        with zipfile.ZipFile(out) as src, zipfile.ZipFile(stripped, "w") as dst:
            for item in src.infolist():
                if "0001" not in item.filename:
                    dst.writestr(item, src.read(item.filename))

        result = mu.restore_library_backup(stripped)

        assert len(result.failed) == 1
        assert len(result.datasets) == 1

    def test_cancelling_keeps_what_already_arrived(self, library, tmp_path, storage):
        """Restoring is additive, so a half-finished one is not a broken state —
        it is simply fewer datasets than asked for."""
        out = str(tmp_path / "backup.zip")
        mu.create_library_backup(out)
        state = {"calls": 0}

        def cancel_after_one():
            state["calls"] += 1
            return state["calls"] > 1

        result = mu.restore_library_backup(out, should_cancel=cancel_after_one)

        assert result.cancelled
        assert len(result.datasets) == 1
