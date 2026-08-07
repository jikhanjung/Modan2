"""Moving a library to another folder, and refusing to put it somewhere bad.

The invariant every test here circles is one sentence: **either the whole
library ends up at the destination, or the source is left exactly as it was.**
A move that half-succeeds is the failure the feature exists to prevent -- the
user is left with two folders, neither usable, and no way to tell which one is
real. So the interesting assertions are not "the files arrived"; they are
"after this failure, the source is still complete".

The two transports fail differently and are tested separately. Within a volume
each member is renamed, so failure means putting back what was already renamed.
Across volumes everything is copied and verified before anything is deleted, so
failure means the source was never touched at all. ``_same_volume`` is patched
to choose between them, since a test cannot conjure a second filesystem.
"""

import logging
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdUtils as mu


@pytest.fixture
def data_directory(monkeypatch):
    """Set (or clear) the configured data directory, undone afterwards."""
    monkeypatch.setattr(mu, "_configured_data_directory", None)
    return mu.set_data_directory


@pytest.fixture
def library(tmp_path):
    """A source folder holding a plausible library."""
    root = tmp_path / "old-library"
    (root / "data" / "1").mkdir(parents=True)
    (root / "backups").mkdir()
    (root / "logs").mkdir()
    (root / mu.DATABASE_FILENAME).write_bytes(b"sqlite" * 100)
    (root / "data" / "1" / "3.jpg").write_bytes(b"image bytes")
    (root / "data" / "1" / "4.obj").write_bytes(b"model bytes")
    (root / "backups" / "Modan2.db.20260101").write_bytes(b"old db")
    (root / "logs" / "Modan2_20260101.log").write_text("log line")
    return root


@pytest.fixture
def no_file_handlers():
    """Leave the root logger exactly as the test found it.

    These tests add and remove file handlers on the *real* root logger, so
    anything left behind would keep writing into a temp directory pytest is
    about to delete -- or, worse, into the developer's log directory.
    """
    root = logging.getLogger()
    before = list(root.handlers)
    yield
    for handler in [h for h in root.handlers if h not in before]:
        root.removeHandler(handler)
        handler.close()


@pytest.fixture
def across_volumes(monkeypatch):
    """Force the copy-verify-delete transport instead of rename."""
    monkeypatch.setattr(mu, "_same_volume", lambda source, destination: False)


def _tree(root):
    """Every file under ``root``, relative and sorted. The comparison unit."""
    return sorted(
        os.path.relpath(os.path.join(dirpath, name), root) for dirpath, _, names in os.walk(root) for name in names
    )


class TestRefusals:
    """Nothing is touched until the answer to "can this work?" is yes."""

    def test_destination_must_be_empty(self, library, tmp_path):
        destination = tmp_path / "new"
        destination.mkdir()
        (destination / "something.txt").write_text("in the way")

        assert "not empty" in mu.describe_move_problem(str(library), str(destination))
        with pytest.raises(mu.DataDirectoryMoveError):
            mu.move_data_directory(str(library), str(destination))
        assert _tree(library)

    def test_destination_inside_the_source_is_refused(self, library):
        # Copying a folder into itself does not terminate. Finding that out
        # during the move rather than before it would be expensive.
        inside = library / "data" / "somewhere"
        problem = mu.describe_move_problem(str(library), str(inside))
        assert "inside" in problem

    def test_same_place_is_refused(self, library):
        assert "already in" in mu.describe_move_problem(str(library), str(library))

    def test_a_source_that_does_not_exist(self, tmp_path):
        problem = mu.describe_move_problem(str(tmp_path / "nowhere"), str(tmp_path / "new"))
        assert "nothing to move" in problem

    def test_a_source_with_no_library_in_it(self, tmp_path):
        empty = tmp_path / "not-a-library"
        empty.mkdir()
        (empty / "notes.txt").write_text("just a folder")
        problem = mu.describe_move_problem(str(empty), str(tmp_path / "new"))
        assert "nothing to move" in problem

    def test_a_file_where_the_destination_should_be(self, library, tmp_path):
        target = tmp_path / "a-file"
        target.write_text("not a folder")
        assert "is a file" in mu.describe_move_problem(str(library), str(target))

    def test_insufficient_space_stops_it_before_it_starts(self, library, tmp_path, monkeypatch, across_volumes):
        import shutil

        monkeypatch.setattr(mu.shutil, "disk_usage", lambda p: shutil._ntuple_diskusage(100, 90, 1))
        problem = mu.describe_move_problem(str(library), str(tmp_path / "new"))
        assert "not enough space" in problem

    def test_space_is_not_required_for_a_rename(self, library, tmp_path, monkeypatch):
        """Within a volume a move shifts no bytes, so a full disk is irrelevant."""
        import shutil

        monkeypatch.setattr(mu, "_same_volume", lambda source, destination: True)
        monkeypatch.setattr(mu.shutil, "disk_usage", lambda p: shutil._ntuple_diskusage(100, 100, 0))
        assert mu.describe_move_problem(str(library), str(tmp_path / "new")) is None


class TestMovingWithinAVolume:
    def test_every_member_arrives(self, library, tmp_path):
        before = _tree(library)
        result = mu.move_data_directory(str(library), str(tmp_path / "new"))

        assert _tree(tmp_path / "new") == before
        assert set(result.moved) == {"backups", mu.DATABASE_FILENAME, "data", "logs"}

    def test_the_emptied_folder_is_removed(self, library, tmp_path):
        result = mu.move_data_directory(str(library), str(tmp_path / "new"))
        assert result.source_removed
        assert not library.exists()

    def test_files_that_are_not_the_library_stay_behind(self, library, tmp_path):
        """Sweeping along whatever else the user keeps there is not this
        feature's business, and the folder survives to hold it."""
        (library / "my notes.txt").write_text("mine")

        result = mu.move_data_directory(str(library), str(tmp_path / "new"))

        assert not result.source_removed
        assert (library / "my notes.txt").exists()
        assert not (tmp_path / "new" / "my notes.txt").exists()

    def test_a_failure_partway_puts_everything_back(self, library, tmp_path, monkeypatch):
        """The whole point: a half-move must not be a possible outcome."""
        before = _tree(library)
        real_rename = os.rename
        calls = []

        def failing_rename(src, dst):
            calls.append(src)
            # Fail on the third member, so backups and the database have already
            # moved and have to come back.
            if len(calls) == 3:
                raise OSError(13, "Permission denied")
            return real_rename(src, dst)

        monkeypatch.setattr(mu.os, "rename", failing_rename)

        with pytest.raises(mu.DataDirectoryMoveError, match="still in"):
            mu.move_data_directory(str(library), str(tmp_path / "new"))

        assert _tree(library) == before
        assert _tree(tmp_path / "new") == []

    def test_sqlite_side_files_travel_with_the_database(self, library, tmp_path):
        """A crash leaves a journal behind; it belongs to the database, not to
        whatever is left in the old folder."""
        (library / (mu.DATABASE_FILENAME + "-journal")).write_bytes(b"journal")

        mu.move_data_directory(str(library), str(tmp_path / "new"))

        assert (tmp_path / "new" / (mu.DATABASE_FILENAME + "-journal")).exists()


class TestMovingAcrossVolumes:
    def test_every_member_arrives_and_the_source_goes(self, library, tmp_path, across_volumes):
        before = _tree(library)

        result = mu.move_data_directory(str(library), str(tmp_path / "new"))

        assert _tree(tmp_path / "new") == before
        assert not library.exists()
        assert result.total_bytes > 0

    def test_backups_are_copied_first(self, library, tmp_path, across_volumes):
        """They are the recovery path, so they should be the first thing whole
        in the new place and the last thing missing from the old."""
        seen = []

        mu.move_data_directory(
            str(library),
            str(tmp_path / "new"),
            progress=lambda done, total, member: seen.append(member),
        )

        assert seen[0] == "backups"

    def test_a_failure_leaves_the_source_untouched(self, library, tmp_path, monkeypatch, across_volumes):
        before = _tree(library)
        real_copy2 = mu.shutil.copy2
        calls = []

        def failing_copy2(src, dst, **kwargs):
            calls.append(src)
            if len(calls) == 3:
                raise OSError(28, "No space left on device")
            return real_copy2(src, dst, **kwargs)

        monkeypatch.setattr(mu.shutil, "copy2", failing_copy2)

        with pytest.raises(mu.DataDirectoryMoveError, match="still in"):
            mu.move_data_directory(str(library), str(tmp_path / "new"))

        assert _tree(library) == before

    def test_a_failure_cleans_up_what_it_copied(self, library, tmp_path, monkeypatch, across_volumes):
        """Leaving a partial copy behind would make the destination look like a
        library, and the next attempt would refuse it as "not empty"."""
        real_copy2 = mu.shutil.copy2
        calls = []

        def failing_copy2(src, dst, **kwargs):
            calls.append(src)
            if len(calls) == 3:
                raise OSError(28, "No space left on device")
            return real_copy2(src, dst, **kwargs)

        monkeypatch.setattr(mu.shutil, "copy2", failing_copy2)

        with pytest.raises(mu.DataDirectoryMoveError):
            mu.move_data_directory(str(library), str(tmp_path / "new"))

        assert _tree(tmp_path / "new") == []

    def test_a_copy_that_does_not_match_is_a_failure(self, library, tmp_path, monkeypatch, across_volumes):
        """Verification is the reason deletion is safe, so it has to be real."""
        before = _tree(library)

        def truncating_copy2(src, dst, **kwargs):
            with open(dst, "wb") as f:
                f.write(b"")  # arrives, but not intact

        monkeypatch.setattr(mu.shutil, "copy2", truncating_copy2)

        with pytest.raises(mu.DataDirectoryMoveError, match="does not match"):
            mu.move_data_directory(str(library), str(tmp_path / "new"))

        assert _tree(library) == before

    def test_cancelling_leaves_the_source_whole(self, library, tmp_path, across_volumes):
        """Cancelling is made safe by never reaching the deletion, not by
        undoing copies."""
        before = _tree(library)
        state = {"calls": 0}

        def cancel_after_two():
            state["calls"] += 1
            return state["calls"] > 2

        result = mu.move_data_directory(str(library), str(tmp_path / "new"), should_cancel=cancel_after_two)

        assert result.cancelled
        assert result.moved == []
        assert _tree(library) == before
        assert _tree(tmp_path / "new") == []

    def test_progress_is_reported_in_bytes(self, library, tmp_path, across_volumes):
        seen = []
        mu.move_data_directory(
            str(library),
            str(tmp_path / "new"),
            progress=lambda done, total, member: seen.append((done, total)),
        )

        assert seen
        assert seen[-1][0] == seen[-1][1]  # ends at 100%
        assert [done for done, _ in seen] == sorted(done for done, _ in seen)


class TestTheLibraryWorksAfterwards:
    def test_the_paths_follow_the_move(self, library, tmp_path, data_directory):
        """The move is only half the job; the getters have to point at the
        result or the application starts with an empty library."""
        data_directory(str(library))
        destination = tmp_path / "new"

        mu.move_data_directory(str(library), str(destination))
        data_directory(str(destination))

        assert mu.get_database_path() == os.path.join(str(destination), mu.DATABASE_FILENAME)
        assert os.path.exists(mu.get_database_path())
        assert os.path.exists(os.path.join(mu.get_storage_directory(), "1", "3.jpg"))
        assert os.path.exists(mu.get_backup_directory())


class TestLogFileHandling:
    """The log file lives in the directory being moved, which makes it the one
    thing likely to keep the old folder locked on Windows."""

    def test_detaching_closes_the_file_handler(self, tmp_path, data_directory, no_file_handlers):
        data_directory(str(tmp_path / "lib"))
        mu.ensure_directories()
        mu.attach_log_file()
        root = logging.getLogger()
        assert any(isinstance(h, logging.FileHandler) for h in root.handlers)

        detached = mu.detach_log_file()

        assert detached
        assert not any(isinstance(h, logging.FileHandler) for h in root.handlers)

    def test_reattaching_follows_the_new_directory(self, tmp_path, data_directory, no_file_handlers):
        data_directory(str(tmp_path / "old"))
        mu.ensure_directories()
        mu.attach_log_file()
        detached = mu.detach_log_file()
        data_directory(str(tmp_path / "new"))

        mu.attach_log_file(detached)

        handlers = [h for h in logging.getLogger().handlers if isinstance(h, logging.FileHandler)]
        assert handlers
        assert os.path.dirname(handlers[-1].baseFilename) == str(tmp_path / "new" / "logs")

    def test_nothing_open_means_nothing_reopened(self, tmp_path, data_directory, no_file_handlers):
        """An empty capture is not the same as no capture. Treating them alike
        gave a console-only run a log file it had never asked for -- which in a
        test run means writing into the developer's real log directory."""
        data_directory(str(tmp_path / "lib"))
        detached = mu.detach_log_file()
        assert detached == []

        mu.attach_log_file(detached)

        assert not [h for h in logging.getLogger().handlers if isinstance(h, logging.FileHandler)]

    def test_the_name_is_defined_once(self):
        """main.setup_logging and attach_log_file must open the same file."""
        assert mu.log_file_name().startswith(mu.PROGRAM_NAME + "_")
        assert mu.log_file_name().endswith(".log")


class TestRiskyLocations:
    """A warning, not a refusal -- but the failures are silent ones, so nobody
    finds them without being told."""

    @pytest.mark.parametrize(
        "folder",
        [
            os.path.join("home", "me", "Dropbox", "research"),
            os.path.join("home", "me", "OneDrive", "Modan2"),
            os.path.join("home", "me", "OneDrive - Contoso University", "Modan2"),
            os.path.join("home", "me", "Google Drive", "data"),
            os.path.join("Users", "me", "Library", "Mobile Documents", "com~apple~CloudDocs", "x"),
            os.path.join("home", "me", "Nextcloud"),
        ],
    )
    def test_sync_folders_are_flagged(self, folder):
        risk = mu.describe_location_risk(os.sep + folder)
        assert risk is not None
        assert "sync" in risk.lower()

    def test_the_message_says_what_actually_goes_wrong(self):
        """ "Not recommended" teaches nothing. The two failures are a database
        uploaded mid-write and two copies that silently diverge."""
        risk = mu.describe_location_risk(os.sep + os.path.join("home", "me", "Dropbox"))
        assert "written" in risk
        assert "two" in risk
        assert "backups" in risk  # and what to do instead

    @pytest.mark.parametrize(
        "folder",
        [
            os.path.join("home", "me", "PaleoBytes", "Modan2"),
            os.path.join("home", "me", "Documents", "research"),
            os.path.join("home", "me", "boxes", "data"),  # not "Box"
            os.path.join("home", "me", "dropboxes"),  # not "Dropbox"
        ],
    )
    def test_ordinary_folders_are_not_flagged(self, folder):
        assert mu.describe_location_risk(os.sep + folder) is None

    def test_the_offending_folder_is_named(self):
        risk = mu.describe_location_risk(os.sep + os.path.join("home", "me", "Dropbox", "a", "b"))
        assert os.path.join(os.sep + "home", "me", "Dropbox") in risk
        # The folder they chose is not the folder at fault; naming the parent is
        # what makes the warning actionable.
        assert risk.index("Dropbox") < risk.index("\n")

    @pytest.mark.skipif(sys.platform == "win32", reason="UNC paths are absolute only on Windows")
    def test_a_unc_path_is_flagged_as_a_network_drive(self, monkeypatch):
        monkeypatch.setattr(mu.os.path, "abspath", lambda p: p)
        risk = mu.describe_location_risk("\\\\server\\share\\Modan2")
        assert risk is not None
        assert "network" in risk.lower()

    def test_a_risky_location_is_still_allowed(self, library, tmp_path, monkeypatch):
        """The check informs the dialog; it must not block the move itself."""
        monkeypatch.setattr(mu, "describe_location_risk", lambda p: "risky")
        assert mu.describe_move_problem(str(library), str(tmp_path / "new")) is None
