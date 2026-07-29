"""The storage directory is configurable, and everything honours it.

The bug this file guards against is specific. ``base_path`` used to default to
``mu.DEFAULT_STORAGE_DIRECTORY``, and a default argument is evaluated once at
import -- so the setting could not move anything. Worse, the callers had split
into two camps: the ones passing a path explicitly were mostly *reads* (viewers,
controller), while the ones riding the default were the *writes, deletes and
copies* inside ``MdModel``. Honouring the preference at all would have made
reads look in the new place while writes landed in the old one.

Which is why these tests do not stop at "an attachment appears where I asked".
Every case asserts the negative too: **nothing was written under the default
directory**. A test that only checks the happy path misses precisely this bug.
"""

import json
import logging
import os
import sys
import tempfile

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
    """Point the single resolver at a temp directory."""
    d = str(tmp_path / "chosen-storage")
    os.makedirs(d, exist_ok=True)
    monkeypatch.setattr(mu, "get_storage_directory", lambda: d)
    return d


def _png(path, size=(40, 30)):
    from PIL import Image

    Image.new("RGB", size, (10, 120, 200)).save(str(path))
    return str(path)


def _default_dir_files():
    """Every file currently under the default storage directory."""
    root = os.path.abspath(mu.DEFAULT_STORAGE_DIRECTORY)
    if not os.path.isdir(root):
        return set()
    return {os.path.join(dirpath, f) for dirpath, _, files in os.walk(root) for f in files}


@pytest.fixture
def no_default_writes():
    """Fail if the body of the test wrote anything to the default location.

    This is the assertion that catches the read/write split. Everything else
    here would pass with writes still escaping to the real per-user directory.
    """
    before = _default_dir_files()
    yield
    assert _default_dir_files() - before == set(), "files leaked into the default storage directory"


def _object(name="Obj", dataset=None):
    dataset = dataset or mm.MdDataset.create(dataset_name="DS", dimension=2)
    return mm.MdObject.create(object_name=name, dataset=dataset)


@pytest.fixture
def data_directory(monkeypatch):
    """Set (or clear) the configured data directory, undone afterwards."""
    monkeypatch.setattr(mu, "_configured_data_directory", None)

    def _set(value):
        return mu.set_data_directory(value)

    return _set


class TestResolution:
    """One configured root; the database, attachments, backups and logs derive."""

    def test_falls_back_to_default_when_unset(self, data_directory):
        data_directory(None)
        assert mu.get_data_directory() == os.path.abspath(mu.DEFAULT_DB_DIRECTORY)
        assert mu.get_storage_directory() == os.path.join(os.path.abspath(mu.DEFAULT_DB_DIRECTORY), "data")

    def test_everything_derives_from_the_configured_root(self, data_directory, tmp_path):
        root = data_directory(str(tmp_path / "library"))

        assert mu.get_data_directory() == root
        assert mu.get_storage_directory() == os.path.join(root, "data")
        assert mu.get_backup_directory() == os.path.join(root, "backups")
        assert mu.get_log_directory() == os.path.join(root, "logs")
        assert mu.get_database_path() == os.path.join(root, "Modan2.db")

    def test_blank_means_the_default(self, data_directory):
        """An empty preference means "the default", not the current directory."""
        data_directory("")
        assert mu.get_data_directory() == os.path.abspath(mu.DEFAULT_DB_DIRECTORY)

    def test_result_is_absolute(self, data_directory):
        data_directory("relative/path")
        assert os.path.isabs(mu.get_data_directory())

    def test_no_import_time_binding(self, data_directory, monkeypatch, tmp_path):
        """Changing the location mid-run takes effect immediately.

        The regression in one line: with the old default arguments the value was
        frozen at import, so no later change could be observed.
        """
        data_directory(None)
        monkeypatch.setattr(mu, "DEFAULT_DB_DIRECTORY", str(tmp_path / "moved"))
        assert mu.get_storage_directory() == os.path.join(os.path.abspath(str(tmp_path / "moved")), "data")


class TestAttachmentsFollowTheSetting:
    def test_image_is_written_to_the_chosen_directory(self, test_database, storage, tmp_path, no_default_writes):
        obj = _object()
        img = mm.MdImage(object=obj)
        img.add_file(_png(tmp_path / "a.png"))

        stored = img.get_file_path()
        assert stored.startswith(storage)
        assert os.path.exists(stored)

    def test_reads_resolve_to_the_same_place_as_writes(self, test_database, storage, tmp_path, no_default_writes):
        """The exact asymmetry of the old bug: reads new, writes old."""
        obj = _object()
        img = mm.MdImage(object=obj)
        img.add_file(_png(tmp_path / "a.png"))
        img.save()

        from ModanController import ModanController

        paths = ModanController.object_file_paths(obj)
        assert img.get_file_path() in paths
        for p in paths:
            assert p.startswith(storage)

    def test_threed_model_add_file_honours_it(self, test_database, storage, tmp_path, no_default_writes):
        """``MdThreeDModel.add_file`` had no ``base_path`` parameter at all."""
        obj = _object()
        src = tmp_path / "m.obj"
        src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")

        model = mm.MdThreeDModel(object=obj)
        model.add_file(str(src))

        assert model.get_file_path().startswith(storage)
        assert os.path.exists(model.get_file_path())

    def test_explicit_base_path_still_wins(self, test_database, storage, tmp_path, no_default_writes):
        other = str(tmp_path / "explicit")
        os.makedirs(other, exist_ok=True)
        obj = _object()

        img = mm.MdImage(object=obj)
        img.add_file(_png(tmp_path / "a.png"), base_path=other)

        assert os.path.exists(img.get_file_path(other))
        assert not os.path.exists(img.get_file_path(storage))


class TestMutationsStayInTheChosenDirectory:
    """Replace, move and duplicate -- the writes that rode the import default."""

    def test_replacing_an_image_deletes_the_old_file_there(self, test_database, storage, tmp_path, no_default_writes):
        obj = _object()
        # add_image first: update_image assumes one exists (its only production
        # caller guards with has_image()).
        obj.add_image(_png(tmp_path / "first.png")).save()
        first_path = obj.get_image().get_file_path()
        assert os.path.exists(first_path)

        # A different extension: the replacement cannot overwrite it in place,
        # so the old file has to be removed explicitly -- from the chosen
        # directory, which is the part that used to be resolved elsewhere.
        replacement = obj.update_image(_png(tmp_path / "second.bmp"))
        replacement.save()

        assert not os.path.exists(first_path)
        assert replacement.get_file_path().startswith(storage)
        assert os.path.exists(replacement.get_file_path())

    def test_moving_an_object_moves_its_media(self, test_database, storage, tmp_path, no_default_writes):
        source_ds = mm.MdDataset.create(dataset_name="From", dimension=2)
        target_ds = mm.MdDataset.create(dataset_name="To", dimension=2)
        obj = _object(dataset=source_ds)
        img = mm.MdImage(object=obj)
        img.add_file(_png(tmp_path / "a.png"))
        img.save()
        old_path = img.get_file_path()

        obj.change_dataset(target_ds)

        new_path = obj.get_image().get_file_path()
        assert new_path.startswith(os.path.join(storage, str(target_ds.id)))
        assert os.path.exists(new_path)
        assert not os.path.exists(old_path)

    def test_copying_an_image_lands_there(self, test_database, storage, tmp_path, no_default_writes):
        obj = _object()
        img = mm.MdImage(object=obj)
        img.add_file(_png(tmp_path / "a.png"))
        img.save()

        target = _object(name="Copy")
        copied = img.copy_image(target)

        assert copied.get_file_path().startswith(storage)
        assert os.path.exists(copied.get_file_path())

    def test_copying_a_threed_model_lands_there(self, test_database, storage, tmp_path, no_default_writes):
        obj = _object()
        src = tmp_path / "m.obj"
        src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
        model = mm.MdThreeDModel(object=obj)
        model.add_file(str(src))
        model.save()

        target = _object(name="Copy")
        copied = model.copy_threed_model(target)

        assert copied.get_file_path().startswith(storage)
        assert os.path.exists(copied.get_file_path())

    def test_archived_original_follows_too(self, test_database, storage, tmp_path, no_default_writes):
        """Oversized images archive a pristine original beside the working copy."""
        obj = _object()
        img = mm.MdImage(object=obj)
        img.add_file(_png(tmp_path / "big.png", size=(mm.IMAGE_MAX_DIM + 200, 400)))

        assert img.has_archived_original()
        assert img.get_original_file_path().startswith(storage)

    def test_deleting_a_dataset_removes_its_directory_there(self, test_database, storage, tmp_path, no_default_writes):
        from ModanController import ModanController

        obj = _object()
        dataset_id = obj.dataset.id
        img = mm.MdImage(object=obj)
        img.add_file(_png(tmp_path / "a.png"))
        img.save()
        assert os.path.isdir(os.path.join(storage, str(dataset_id)))

        ModanController()._remove_dataset_directory(dataset_id)

        assert not os.path.exists(os.path.join(storage, str(dataset_id)))


class TestExport:
    def test_zip_export_finds_the_attachments(self, test_database, storage, tmp_path, no_default_writes):
        """``collect_dataset_files`` resolved through the same broken default."""
        obj = _object()
        img = mm.MdImage(object=obj)
        img.add_file(_png(tmp_path / "a.png"))
        img.save()

        images, _models = mu.collect_dataset_files(obj.dataset.id)

        assert images == [img.get_file_path()]
        assert images[0].startswith(storage)

    def test_serialize_takes_no_storage_directory(self):
        """The parameter was documented, accepted, and thrown away."""
        import inspect

        assert "storage_dir" not in inspect.signature(mu.serialize_dataset_to_json).parameters


class TestPreferencePersistence:
    """The setting survives a restart, and an unset one is stored as unset."""

    def test_round_trips_through_the_config(self, tmp_path):
        from Modan2 import SettingsWrapper

        config = {}
        sw = SettingsWrapper(config, None)
        sw.save = lambda: None  # keep the real preferences file out of it

        sw.setValue("Data/Directory", str(tmp_path / "elsewhere"))

        assert config["data"]["directory"] == str(tmp_path / "elsewhere")
        assert SettingsWrapper(config, None).value("Data/Directory", "") == str(tmp_path / "elsewhere")

    def test_default_is_stored_as_empty_not_as_a_resolved_path(self):
        """Recording the resolved default would pin the user to today's default.

        The location is configurable precisely so it can change; a user who never
        chose anything must keep following the default, not a snapshot of it
        taken at first launch.
        """
        from Modan2 import SettingsWrapper

        config = {}
        sw = SettingsWrapper(config, None)
        sw.save = lambda: None

        sw.setValue("Data/Directory", "")

        assert config["data"]["directory"] == ""

    def test_config_resolves_to_the_configured_directory(self, tmp_path):
        from Modan2 import ModanMainWindow

        chosen = str(tmp_path / "chosen")
        path, is_custom = ModanMainWindow.resolve_data_directory({"data": {"directory": chosen}})

        assert path == os.path.abspath(chosen)
        assert is_custom is True

    @pytest.mark.parametrize(
        "config",
        [{}, {"ui": {}}, {"data": {}}, {"data": None}, {"data": {"directory": ""}}],
        ids=["empty", "other-section", "empty-section", "null-section", "blank-value"],
    )
    def test_config_without_a_choice_falls_back(self, config):
        from Modan2 import ModanMainWindow

        path, is_custom = ModanMainWindow.resolve_data_directory(config)

        assert path == os.path.abspath(mu.DEFAULT_DB_DIRECTORY)
        assert is_custom is False

    def test_read_straight_from_the_preferences_file(self, tmp_path):
        """Logging and the database open before the config is parsed."""
        config_file = tmp_path / "preferences.json"
        config_file.write_text(json.dumps({"data": {"directory": "/somewhere/else"}}), encoding="utf-8")

        assert mu.read_configured_data_directory(str(config_file)) == "/somewhere/else"

    @pytest.mark.parametrize(
        "content",
        ["not json at all", "{}", '{"data": {}}', '{"data": null}', '{"data": {"directory": ""}}', "[]"],
    )
    def test_unreadable_or_unset_preferences_mean_the_default(self, tmp_path, content):
        """A broken preferences file must not stop the program from starting."""
        config_file = tmp_path / "preferences.json"
        config_file.write_text(content, encoding="utf-8")

        assert mu.read_configured_data_directory(str(config_file)) == ""

    def test_missing_preferences_file_means_the_default(self, tmp_path):
        assert mu.read_configured_data_directory(str(tmp_path / "nope.json")) == ""

    def test_attachments_land_there_after_reload(self, data_directory, test_database, tmp_path, no_default_writes):
        """End to end: configure, "restart", attach. The whole point of phase 1."""
        chosen = str(tmp_path / "after-restart")
        os.makedirs(chosen, exist_ok=True)

        # What a restart does: read the preferences file, apply it.
        config_file = tmp_path / "preferences.json"
        config_file.write_text(json.dumps({"data": {"directory": chosen}}), encoding="utf-8")
        data_directory(mu.read_configured_data_directory(str(config_file)))

        obj = _object()
        img = mm.MdImage(object=obj)
        img.add_file(_png(tmp_path / "a.png"))

        assert img.get_file_path().startswith(chosen)
        assert os.path.exists(img.get_file_path())


class TestStartupOrder:
    """The database has to follow the setting too, which fixes the ordering."""

    def _setup(self, tmp_path, config, **kwargs):
        from MdAppSetup import ApplicationSetup

        config_file = tmp_path / "preferences.json"
        config_file.write_text(json.dumps(config), encoding="utf-8")
        return ApplicationSetup(config_path=str(config_file), **kwargs)

    def test_database_lands_in_the_configured_directory(self, data_directory, tmp_path, monkeypatch):
        import MdModel

        chosen = tmp_path / "library"
        chosen.mkdir()
        setup = self._setup(tmp_path, {"data": {"directory": str(chosen)}})
        monkeypatch.setattr(MdModel, "prepare_database", lambda: None)
        opened = []
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: opened.append(p) or p)

        setup.initialize()

        assert opened == [str(chosen / "Modan2.db")]

    def test_db_flag_still_wins(self, data_directory, tmp_path, monkeypatch):
        """--db names a file outright; the two are independent by design."""
        import MdModel

        chosen = tmp_path / "library"
        chosen.mkdir()
        explicit = str(tmp_path / "elsewhere.db")
        setup = self._setup(tmp_path, {"data": {"directory": str(chosen)}}, db_path=explicit)
        monkeypatch.setattr(MdModel, "prepare_database", lambda: None)
        opened = []
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: opened.append(p) or p)

        setup.initialize()

        assert opened == [explicit]

    def test_settings_are_read_before_the_database_opens(self, data_directory, tmp_path, monkeypatch):
        """The ordering bug in one assertion.

        The database used to be prepared first, which pinned it to the default
        location no matter what the preference said.
        """
        import MdModel

        order = []
        setup = self._setup(tmp_path, {"data": {"directory": str(tmp_path)}})
        monkeypatch.setattr(MdModel, "prepare_database", lambda: order.append("database"))
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: p)
        original = setup._load_settings
        monkeypatch.setattr(setup, "_load_settings", lambda: (order.append("settings"), original())[1])

        setup.initialize()

        assert order.index("settings") < order.index("database")


class TestMissingLocation:
    """A configured location can vanish; the app must say so, not fake it."""

    def test_no_problem_reported_for_a_usable_directory(self, tmp_path):
        assert mu.describe_data_directory_problem(str(tmp_path)) is None

    def test_missing_directory_is_reported(self, tmp_path):
        problem = mu.describe_data_directory_problem(str(tmp_path / "unplugged-drive"))
        assert problem is not None
        assert "unplugged-drive" in problem

    def test_a_file_where_a_folder_should_be(self, tmp_path):
        f = tmp_path / "not-a-folder"
        f.write_text("")
        problem = mu.describe_data_directory_problem(str(f))
        assert problem is not None
        assert "not a folder" in problem

    # ``os.name`` is checked first so ``or`` short-circuits: geteuid does not
    # exist on Windows, and this expression runs at import, so naming it
    # unguarded fails *collection of the whole file* rather than one test.
    # Skipping there is right on the merits too -- chmod does not remove write
    # access from a directory on Windows, so the case cannot be set up.
    @pytest.mark.skipif(
        os.name != "posix" or os.geteuid() == 0,
        reason="needs POSIX permission bits, and a non-root user to respect them",
    )
    def test_unwritable_directory_is_reported(self, tmp_path):
        d = tmp_path / "read-only"
        d.mkdir()
        d.chmod(0o500)
        try:
            problem = mu.describe_data_directory_problem(str(d))
            assert problem is not None
            assert "not writable" in problem
        finally:
            d.chmod(0o700)

    def test_defaults_to_the_current_location(self, storage):
        assert mu.describe_data_directory_problem() is None


class TestUnavailableDataDirectoryAtStartup:
    """A chosen directory that is missing must stop and ask, not fake a library.

    The order matters more than the dialog: the check has to happen before
    ``ensure_directories`` recreates the folder and before the database is
    opened inside it. Miss that window and the user is looking at a brand-new
    empty library with no hint that the real one is on a drive that is merely
    unplugged.
    """

    def _setup(self, tmp_path, directory, answer=None):
        from MdAppSetup import ApplicationSetup

        config_file = tmp_path / "preferences.json"
        config_file.write_text(json.dumps({"data": {"directory": str(directory)}}), encoding="utf-8")
        asked = []

        def callback(problem, resolved):
            asked.append((problem, resolved))
            return answer

        return (
            ApplicationSetup(
                config_path=str(config_file),
                on_data_directory_problem=callback if answer else None,
            ),
            asked,
        )

    def test_missing_directory_is_not_created_before_asking(self, data_directory, tmp_path, monkeypatch):
        import MdModel

        missing = tmp_path / "unplugged"
        setup, asked = self._setup(tmp_path, missing, answer="quit")
        monkeypatch.setattr(MdModel, "prepare_database", lambda: None)
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: p)

        setup.initialize()

        assert len(asked) == 1
        assert "unplugged" in asked[0][0]
        assert not missing.exists(), "the missing directory was recreated before the user was asked"

    def test_quitting_stops_before_the_database_opens(self, data_directory, tmp_path, monkeypatch):
        import MdModel

        setup, _ = self._setup(tmp_path, tmp_path / "unplugged", answer="quit")
        opened = []
        monkeypatch.setattr(MdModel, "prepare_database", lambda: opened.append("prepared"))
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: opened.append(p) or p)

        setup.initialize()

        assert setup.quit_requested is True
        assert opened == []

    def test_choosing_the_default_clears_the_preference(self, data_directory, tmp_path, monkeypatch):
        import MdModel

        setup, _ = self._setup(tmp_path, tmp_path / "unplugged", answer="default")
        monkeypatch.setattr(MdModel, "prepare_database", lambda: None)
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: p)

        setup.initialize()

        assert setup.quit_requested is False
        assert mu.get_data_directory() == os.path.abspath(mu.DEFAULT_DB_DIRECTORY)
        # Written back, so the next launch does not ask the same question again.
        assert setup.config["data"]["directory"] == ""

    def test_continuing_uses_the_chosen_location(self, data_directory, tmp_path, monkeypatch):
        import MdModel

        missing = tmp_path / "unplugged"
        setup, _ = self._setup(tmp_path, missing, answer="continue")
        monkeypatch.setattr(MdModel, "prepare_database", lambda: None)
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: p)

        setup.initialize()

        assert setup.quit_requested is False
        assert mu.get_data_directory() == str(missing)
        assert missing.exists(), "continuing should create the directory it was told to use"

    def test_a_present_directory_is_not_questioned(self, data_directory, tmp_path, monkeypatch):
        import MdModel

        present = tmp_path / "library"
        present.mkdir()
        setup, asked = self._setup(tmp_path, present, answer="quit")
        monkeypatch.setattr(MdModel, "prepare_database", lambda: None)
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: p)

        setup.initialize()

        assert asked == []
        assert setup.quit_requested is False

    def test_headless_startup_continues_without_a_callback(self, data_directory, tmp_path, monkeypatch):
        """Scripts and tests have nobody to ask; they must not hang or die."""
        import MdModel

        missing = tmp_path / "unplugged"
        setup, _ = self._setup(tmp_path, missing)  # no callback
        monkeypatch.setattr(MdModel, "prepare_database", lambda: None)
        monkeypatch.setattr(MdModel, "set_database_path", lambda p: p)

        setup.initialize()

        assert setup.quit_requested is False
        assert mu.get_data_directory() == str(missing)


class TestLoggingDoesNotPreemptTheCheck:
    """``setup_logging`` runs first and must not create a missing location.

    Logs follow the data directory, so logging resolves it before anything else
    does. Creating it there would silently destroy the evidence the startup
    check needs -- an unplugged drive would be indistinguishable from an empty
    library by the time anyone looked -- and the log explaining the failure
    would land in the folder nobody can reach.
    """

    def _config(self, tmp_path, directory):
        config_file = tmp_path / "preferences.json"
        config_file.write_text(json.dumps({"data": {"directory": str(directory)}}), encoding="utf-8")
        return str(config_file)

    def test_a_missing_directory_is_left_alone(self, data_directory, tmp_path, monkeypatch):
        import main

        missing = tmp_path / "unplugged"
        monkeypatch.setattr("logging.basicConfig", lambda **kw: None)
        monkeypatch.setattr("logging.FileHandler", lambda *a, **kw: logging.NullHandler())

        main.setup_logging(config_path=self._config(tmp_path, missing))

        assert not missing.exists(), "logging created the directory the startup check needs to find absent"
        assert mu.get_data_directory() == os.path.abspath(mu.DEFAULT_DB_DIRECTORY)

    def test_a_present_directory_is_used_for_logs(self, data_directory, tmp_path, monkeypatch):
        import main

        present = tmp_path / "library"
        present.mkdir()
        monkeypatch.setattr("logging.basicConfig", lambda **kw: None)
        monkeypatch.setattr("logging.FileHandler", lambda *a, **kw: logging.NullHandler())

        main.setup_logging(config_path=self._config(tmp_path, present))

        assert mu.get_data_directory() == str(present)
        assert mu.get_log_directory() == str(present / "logs")
        assert (present / "logs").is_dir()
