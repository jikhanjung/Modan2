import contextlib
import json
import logging
import os
import shutil
import sys
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path

import numpy as np
import platformdirs

# from stl import mesh
import trimesh
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

# Import version from centralized version file
try:
    from version import __version__ as PROGRAM_VERSION
except ImportError:
    # Fallback for compatibility
    PROGRAM_VERSION = "0.1.5-alpha.1"

COMPANY_NAME = "PaleoBytes"
PROGRAM_NAME = "Modan2"


# Build information
def get_build_info():
    """Get build information from build_info.json file.

    Returns:
        dict: Build information with version, build_number, build_date, platform
    """
    import json
    from pathlib import Path

    # Try to find build_info.json in various locations
    search_paths = [
        Path("build_info.json"),  # Development environment
        Path(sys.executable).parent / "build_info.json",  # PyInstaller onedir
        Path(sys._MEIPASS) / "build_info.json" if hasattr(sys, "_MEIPASS") else None,  # PyInstaller onefile
    ]

    for path in search_paths:
        if path and path.exists():
            try:
                # Read as UTF-8 rather than the platform default: this runs at
                # import time, so a byte the locale cannot decode (cp949 on
                # Korean Windows, say) would stop the application before it
                # opens. UnicodeDecodeError is a ValueError, which the old
                # except clause did not cover either.
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except (ValueError, OSError):
                pass

    # Return default values if build_info.json not found
    from datetime import datetime

    return {
        "version": PROGRAM_VERSION,
        "build_number": "local",
        "build_date": "development",
        "build_year": datetime.now().astimezone().year,  # Use current year for development
        "platform": sys.platform,
    }


# Get build information on module import
BUILD_INFO = get_build_info()

# Copyright with build-time year
from datetime import UTC, datetime


# Get build year from build_info.json, fallback to current year for development
def get_copyright_year():
    """Get the year for copyright display, preferring build-time year."""
    if "build_year" in BUILD_INFO:
        return BUILD_INFO["build_year"]
    # Fallback to current year for development environment
    return datetime.now().astimezone().year


COPYRIGHT_YEAR = get_copyright_year()
PROGRAM_COPYRIGHT = f"© 2023-{COPYRIGHT_YEAR} Jikhan Jung"
PROGRAM_HOMEPAGE = "https://github.com/jikhanjung/Modan2"
PROGRAM_BUILD_NUMBER = BUILD_INFO.get("build_number", "local")
PROGRAM_BUILD_DATE = BUILD_INFO.get("build_date", "unknown")

DB_LOCATION = ""

# print(os.name)
USER_PROFILE_DIRECTORY = os.path.expanduser("~")

DEFAULT_DB_DIRECTORY = os.path.join(USER_PROFILE_DIRECTORY, COMPANY_NAME, PROGRAM_NAME)
DEFAULT_STORAGE_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "data/")
DEFAULT_LOG_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "logs/")
DB_BACKUP_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "backups/")

DATABASE_FILENAME = PROGRAM_NAME + ".db"

# The user's data directory, when they have chosen one. None means "use
# DEFAULT_DB_DIRECTORY"; the choice is stored as an empty string rather than a
# resolved path so a user who never chose keeps following the default instead of
# a snapshot of what it was on the day they first launched.
#
# Module state rather than an attribute on the QApplication: the database is
# opened during application setup, before the main window exists to carry one,
# and a second place to read the location from is exactly how the preferences
# load and save paths drifted apart in devlog 272. Everything below derives from
# this one value, and callers must go through the getters -- never through the
# DEFAULT_* constants, which are only the fallback.
_configured_data_directory: str | None = None


def set_data_directory(path: str | None) -> str:
    """Point every data path at ``path`` ("" or None for the default).

    Called once during startup, after preferences are read and before the
    database is opened. Returns the directory now in effect.
    """
    global _configured_data_directory
    _configured_data_directory = os.path.abspath(path) if path else None
    return get_data_directory()


def get_data_directory() -> str:
    """The directory holding the database, attachments, backups and logs."""
    return _configured_data_directory or os.path.abspath(DEFAULT_DB_DIRECTORY)


def get_storage_directory() -> str:
    """Where attached images and 3D models live.

    **The single place this is resolved.** Every read, write, copy and delete of
    an attachment must come through here, directly or via a ``base_path``
    threaded down from a caller that did.

    It has to be a function, not a constant. ``DEFAULT_STORAGE_DIRECTORY`` is
    evaluated once at import, so a module-level default -- including a default
    *argument*, which is the same thing -- freezes the location before the
    preference that sets it has been read. That was a live hazard: the callers
    that passed a path explicitly were mostly reads, while the ones bound to the
    import-time default were the writes, deletes and copies inside ``MdModel``,
    so honouring the preference at all would have made reads look in the new
    place and writes land in the old one.
    """
    return os.path.join(get_data_directory(), "data")


def get_backup_directory() -> str:
    """Where rotating database backups are written."""
    return os.path.join(get_data_directory(), "backups")


def get_log_directory() -> str:
    """Where log files are written.

    Logs follow the data directory rather than staying put. The original plan
    excluded them because logging is configured before preferences are read --
    but preferences moved out to the OS configuration location (devlog 277), so
    they can now be read without the database or the QApplication existing, and
    ``setup_logging`` does exactly that. The remaining reason pointed the other
    way: the argument for keeping logs beside the data is only served if they
    actually move with it.
    """
    return os.path.join(get_data_directory(), "logs")


def get_database_path() -> str:
    """The database file implied by the current data directory.

    ``--db`` overrides this; it names a file directly and is independent of the
    data directory by design.
    """
    return os.path.join(get_data_directory(), DATABASE_FILENAME)


def read_configured_data_directory(config_path: str | None = None) -> str:
    """Read the chosen data directory straight from the preferences file.

    For the startup steps that run before the configuration has been parsed into
    an application object -- logging, and the database open. Returns "" for the
    default, and for any unreadable or malformed file: a broken preferences file
    must not stop the program from starting, and falling back to the default is
    the same outcome as a fresh install.
    """
    path = config_path or DEFAULT_CONFIG_PATH
    try:
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
        return (config.get("data") or {}).get("directory") or ""
    except (OSError, ValueError, AttributeError):
        return ""


# Preferences: the OS configuration location, not the data directory.
#
# They are application data, not user documents -- losing them resets window
# positions, not anyone's research -- and they have to sit outside the data
# directory regardless, because that directory's location is itself becoming a
# preference and a setting cannot be stored in the place it points at.
#
# platformdirs rather than Qt's QStandardPaths: this module is imported before
# main.py constructs the QApplication (logging is configured first), and Qt's
# app-specific locations are derived from names that are not set yet, so an
# eager resolution would silently yield the bare config root shared with every
# other application. platformdirs is pure Python and has no such ordering.
#
# The vendor directory is appended by hand. platformdirs drops appauthor on
# macOS and Linux, where a vendor level is not the convention -- but every other
# path this application owns is grouped under PaleoBytes (the install directory,
# the Start Menu folder, the data directory), and having settings alone diverge
# on two of three platforms is worse than following a convention that merely
# permits rather than requires the extra level.
#
#   Windows  %LOCALAPPDATA%\PaleoBytes\Modan2\preferences.json
#   macOS    ~/Library/Application Support/PaleoBytes/Modan2/preferences.json
#   Linux    $XDG_CONFIG_HOME (or ~/.config)/PaleoBytes/Modan2/preferences.json
#
# Note macOS resolves to Application Support, not ~/Library/Preferences: Apple
# reserves the latter for the plist/defaults system, and this is a JSON file the
# application manages itself.
DEFAULT_CONFIG_PATH = os.path.join(platformdirs.user_config_dir(), COMPANY_NAME, PROGRAM_NAME, "preferences.json")

# Where preferences have lived, newest first. Only read, and only to migrate.
#   ~/PaleoBytes/Modan2/preferences.json   0.2.0-beta.2 (devlog 272)
#   ~/.modan2/config.json                  before that
LEGACY_CONFIG_PATHS = (
    os.path.join(DEFAULT_DB_DIRECTORY, "preferences.json"),
    os.path.join(USER_PROFILE_DIRECTORY, ".modan2", "config.json"),
)


def migrate_legacy_config():
    """Copy preferences forward from wherever they were last kept, once.

    Without this a relocation silently resets every preference the user has set
    (window geometry, language, overlay placement) -- they would look lost
    rather than moved. Legacy files are left in place: they cost nothing and
    keep an older build usable against the same profile.

    Unlike the data directory, this is done automatically: the file is under a
    kilobyte and a failed copy costs window positions, not research data.

    Returns the path migrated from, or None if nothing was done.
    """
    if os.path.exists(DEFAULT_CONFIG_PATH):
        return None

    source = next((p for p in LEGACY_CONFIG_PATHS if os.path.exists(p)), None)
    if source is None:
        return None

    try:
        os.makedirs(os.path.dirname(DEFAULT_CONFIG_PATH), exist_ok=True)
        shutil.copyfile(source, DEFAULT_CONFIG_PATH)
    except OSError as e:
        # Not fatal: the caller falls back to defaults, which is the same
        # outcome as a fresh install.
        logger.warning(f"Could not migrate preferences from {source}: {e}")
        return None
    logger.info(f"Migrated preferences from {source} to {DEFAULT_CONFIG_PATH}")
    return source


def describe_data_directory_problem(path: str | None = None) -> str | None:
    """Why ``path`` is unusable as a data directory, or None if it is fine.

    Called once at startup, not per attachment. A chosen location can go missing
    in entirely ordinary ways -- an external drive is not plugged in, a network
    share is down, the folder was moved or renamed. The application must not
    quietly carry on: it would create the directory afresh and present an empty
    library, which to the user is indistinguishable from having lost their data.
    Silently reverting to the default is wrong for the same reason.

    The writability check is weak on Windows, where ``os.access`` does not
    consult directory ACLs and answers True for a folder that cannot be written
    to. The case that matters -- the location is not there at all, because the
    drive is unplugged or the share is down -- is detected on every platform.
    """
    path = path or get_data_directory()
    if os.path.isdir(path):
        return None if os.access(path, os.W_OK) else f"The data location is not writable: {path}"
    if os.path.exists(path):
        return f"The data location is not a folder: {path}"
    return f"The data location cannot be found: {path}"


def ensure_directories():
    """Create the data directory and its subdirectories, tolerating failure.

    Resolved through the getters, so calling this again after
    ``set_data_directory`` prepares the newly chosen location. At import time
    that is the default, which is what a fresh install needs.
    """
    directories = [get_data_directory(), get_storage_directory(), get_log_directory(), get_backup_directory()]

    for directory in directories:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create directory {directory}: {e}")
            # Don't fail completely, let the application try to continue


# Try to create directories on import, but don't fail if it doesn't work
try:
    ensure_directories()
except Exception as e:
    print(f"Warning: Directory initialization failed: {e}")


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def log_file_name():
    """This day's log file name. One definition, used by every caller.

    ``main.setup_logging`` opens it at startup and ``attach_log_file`` reopens it
    after the log directory moves; deriving the name twice is how two places
    start disagreeing about which file is the log.
    """
    return f"{PROGRAM_NAME}_{datetime.now().astimezone().strftime('%Y%m%d')}.log"


def detach_log_file():
    """Close the log file so the directory holding it can be moved.

    Logs follow the data directory, which makes the log file an obstacle to
    moving that directory: Windows refuses to rename a folder containing an open
    file, and where the rename does succeed the handler carries on writing to a
    path that no longer exists. Returns what ``attach_log_file`` needs to put it
    back.
    """
    root = logging.getLogger()
    detached = []
    for handler in list(root.handlers):
        if isinstance(handler, logging.FileHandler):
            root.removeHandler(handler)
            handler.close()
            detached.append((handler.level, handler.formatter))
    return detached


def attach_log_file(detached=None):
    """Reopen the log file in whatever the log directory is now.

    Called after a move whether it succeeded or not -- the point is to get
    logging back, and the failure path is exactly when the log matters most.
    Failing to reopen is warned about rather than raised: the console handler is
    still attached, so the application keeps running and keeps reporting.
    """
    # None means "no handler was captured, open a fresh one"; an empty list
    # means "there was nothing open", and those are different. Conflating them
    # made a move add a log file to a run that had deliberately been left
    # logging to the console only.
    if detached is None:
        detached = [(logging.NOTSET, None)]

    root = logging.getLogger()
    for level, formatter in detached:
        try:
            os.makedirs(get_log_directory(), exist_ok=True)
            handler = logging.FileHandler(os.path.join(get_log_directory(), log_file_name()), encoding="utf-8")
        except OSError as e:
            print(f"Warning: Could not reopen the log file in {get_log_directory()}: {e}")
            continue
        handler.setLevel(level)
        handler.setFormatter(formatter or logging.Formatter(LOG_FORMAT))
        root.addHandler(handler)


# ---------------------------------------------------------------------------
# Where a library must not go
#
# Making the location configurable means someone will put the library in a
# synchronised folder or on a network share, and both are bad places for a live
# SQLite database. The application cannot prevent it -- it is the user's disk --
# but it can refuse to let it happen silently.
# ---------------------------------------------------------------------------

# Folder names the mainstream sync clients use, matched against whole path
# components so that a directory merely *called* "boxes" is not flagged. Names
# with a suffix in practice (OneDrive - Contoso, Dropbox (Personal)) are matched
# by prefix, which is why the check below looks at both.
SYNC_FOLDER_NAMES = (
    "dropbox",
    "onedrive",
    "google drive",
    "googledrive",
    "my drive",
    "icloud drive",
    "icloud~",
    "com~apple~clouddocs",
    "nextcloud",
    "owncloud",
    "box sync",
    "box",
    "pclouddrive",
    "mega",
    "yandex.disk",
    "creative cloud files",
    "syncthing",
)


def _looks_like_sync_folder(path):
    """The sync folder ``path`` is inside, or None."""
    parts = Path(os.path.abspath(path)).parts
    for i, part in enumerate(parts):
        name = part.strip().lower()
        for candidate in SYNC_FOLDER_NAMES:
            if name == candidate or name.startswith((candidate + " ", candidate + "-")):
                return os.path.join(*parts[: i + 1])
    return None


def _is_network_path(path):
    """Whether ``path`` is on a network share.

    UNC paths are recognisable anywhere; a mapped Windows drive letter is not,
    so that case asks the OS. Failing to detect one is not serious -- the sync
    check catches the common way people get here -- so every error means "no".
    """
    path = os.path.abspath(path)
    if path.startswith(("\\\\", "//")):
        return True
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        drive = os.path.splitdrive(path)[0]
        if not drive:
            return False
        DRIVE_REMOTE = 4
        return ctypes.windll.kernel32.GetDriveTypeW(drive + "\\") == DRIVE_REMOTE
    except Exception:
        return False


def describe_location_risk(path):
    """Why ``path`` is a risky home for the library, or None if it looks fine.

    A warning, never a refusal: there are legitimate reasons to accept the risk,
    and the folder belongs to the user. But the failures being warned about are
    the *silent* kind, which is exactly what nobody discovers on their own.

    Sync clients are the worse case of the two. A live SQLite database is a file
    the application writes in place, and a sync client will upload it mid-write
    and hold a handle open while doing so. Worse, opening the same library from
    two machines does not merge -- the client writes a conflict copy
    (``Modan2-DESKTOP-ABC.db``) and both sides carry on, so the library silently
    splits in two and there is no later way to tell which half is real.

    Network shares fail differently: SQLite's locking is unreliable over SMB and
    NFS, which corrupts rather than duplicates.
    """
    sync_folder = _looks_like_sync_folder(path)
    if sync_folder:
        return (
            f"{sync_folder} looks like a folder that syncs to the cloud (Dropbox, OneDrive, Google Drive "
            "or similar).\n\n"
            "Modan2 keeps your data in a database file that it writes to as you work. Sync clients upload "
            "such a file while it is being written, and if you ever open the same library from two "
            "computers they will not merge it -- you get two copies that have silently drifted apart, with "
            "no way to tell which one is right.\n\n"
            "Keep the library on a local disk, and use a sync folder for backups and exported datasets "
            "instead."
        )

    if _is_network_path(path):
        return (
            f"{os.path.abspath(path)} is on a network drive.\n\n"
            "Modan2's database relies on file locking, which is unreliable over network shares and can "
            "corrupt the database. Keep the library on a local disk."
        )

    return None


# ---------------------------------------------------------------------------
# Moving an existing library
#
# Choosing a new data directory does not move anything by itself, and the dialog
# says so plainly. This is the separate, explicitly requested move that follows.
# It is deliberately not automatic: relocating gigabytes has to be something the
# user asked for and can be told about when it fails.
#
# One invariant governs all of it: **either the whole library ends up at the
# destination, or the source is left exactly as it was.** Anything in between is
# the failure this feature exists to avoid -- a library split across two folders,
# where neither half is usable and the user cannot tell which one is real.
# ---------------------------------------------------------------------------


class DataDirectoryMoveError(Exception):
    """A library move was refused before starting, or failed partway.

    The message reaches the user, so it names paths rather than error codes.
    """


class MoveResult:
    """What a completed (or cancelled) move did.

    ``cancelled`` and a successful move are told apart by the flag rather than
    by an exception: cancelling is a legitimate answer, not an error, and it
    leaves exactly the same state as never having started.
    """

    def __init__(self, moved=None, total_bytes=0, cancelled=False, source_removed=False):
        self.moved = moved or []
        self.total_bytes = total_bytes
        self.cancelled = cancelled
        self.source_removed = source_removed

    def __repr__(self):
        return (
            f"MoveResult(moved={self.moved!r}, total_bytes={self.total_bytes}, "
            f"cancelled={self.cancelled}, source_removed={self.source_removed})"
        )


class _CancelledError(Exception):
    """Internal: unwinds out of the middle of a copy. Never seen by callers."""


def library_members(source):
    """The entries of ``source`` that make up the library, in the order to move.

    Backups lead deliberately. They are the recovery path, so they should be the
    first thing complete in the new location -- if a later step fails, the user
    still has somewhere to recover from that is not the folder being disturbed.

    ``temp/`` is not a member: those are genuinely temporary files and belong in
    the OS temp location. Anything else the user happens to keep in the folder is
    not a member either, and is left alone rather than swept along.
    """
    names = ["backups", DATABASE_FILENAME]
    # SQLite side files. A clean close removes them, but a crash does not, and
    # they belong to the database rather than to whatever is left behind.
    names += [DATABASE_FILENAME + suffix for suffix in ("-journal", "-wal", "-shm")]
    names += ["data", "logs"]
    return [name for name in names if os.path.exists(os.path.join(source, name))]


def library_size(path):
    """``(file count, total bytes)`` of the library at ``path``.

    For telling the user what a move is about to shift, before they agree to it.
    """
    return _tree_stats(path)


def _tree_stats(path):
    """``(file count, total bytes)`` for a file or a directory tree."""
    if os.path.isfile(path):
        return 1, os.path.getsize(path)
    count = 0
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                total += os.path.getsize(full)
                count += 1
            except OSError:
                # A file that vanished mid-walk. Counting it would fail the
                # verification of an otherwise good copy.
                continue
    return count, total


def _existing_ancestor(path):
    """The nearest existing directory at or above ``path``.

    Free space and volume identity have to be asked of something that exists,
    and the destination may not have been created yet.
    """
    path = os.path.abspath(path)
    while not os.path.isdir(path):
        parent = os.path.dirname(path)
        if parent == path:
            return path
        path = parent
    return path


def _same_volume(source, destination):
    """Whether a rename can move between these two paths.

    Renames within a volume are atomic and instantaneous; across volumes the
    only option is copy-verify-delete, which is where the interesting failure
    modes live. ``st_dev`` identifies the volume on every platform Python
    supports, Windows included.
    """
    try:
        return os.stat(_existing_ancestor(source)).st_dev == os.stat(_existing_ancestor(destination)).st_dev
    except OSError:
        # Unknown means "assume the slow, careful path", never the fast one.
        return False


def describe_move_problem(source, destination):
    """Why the library at ``source`` cannot be moved to ``destination``, or None.

    Checked before anything is touched, so the answer can be a message rather
    than a half-finished move. Called by the dialog to decide whether to offer
    the move at all.
    """
    source = os.path.abspath(source)
    destination = os.path.abspath(destination)

    if source == destination:
        return f"The data is already in {destination}."

    if not os.path.isdir(source):
        return f"There is nothing to move: {source} does not exist."

    if not library_members(source):
        return f"There is nothing to move: {source} holds no database, images or backups."

    # Copying a folder into itself never terminates, and renaming into itself
    # fails halfway through. Neither is worth discovering during the move.
    if os.path.commonpath([source, destination]) == source:
        return f"{destination} is inside {source}, so the data cannot be moved there."

    if os.path.exists(destination) and not os.path.isdir(destination):
        return f"{destination} is a file, not a folder."

    if os.path.isdir(destination) and os.listdir(destination):
        # Merging into an occupied folder would make "did this work?"
        # unanswerable afterwards, and an existing Modan2.db there would be
        # silently overwritten.
        return f"{destination} is not empty. Choose an empty folder."

    _, needed = _tree_stats(source)
    try:
        free = shutil.disk_usage(_existing_ancestor(destination)).free
    except OSError:
        free = None
    # Only meaningful across volumes: a rename within one moves no bytes. The
    # margin covers the destination's own overhead and leaves the disk usable.
    if free is not None and not _same_volume(source, destination) and free < needed * 1.1:
        return f"There is not enough space in {destination}: {needed / 1e9:.1f} GB to move, {free / 1e9:.1f} GB free."

    return None


def move_data_directory(source, destination, progress=None, should_cancel=None):
    """Move an existing library from ``source`` to ``destination``.

    ``progress`` is called as ``(bytes_done, bytes_total, member)`` and
    ``should_cancel`` is polled between files; both are optional.

    How the invariant is kept depends on the volumes, and the two cases fail
    differently:

    *Within a volume*, each member is renamed -- atomic, instant, no bytes read.
    If one fails, the ones already renamed are renamed back. There is nothing to
    cancel partway because there is no partway.

    *Across volumes*, everything is copied first, then verified, and only then
    is the source deleted. That ordering is what makes cancelling safe: it does
    not undo copies, it simply never reaches the deletion, so the source is
    still whole. The partial copy is cleaned up on the way out.

    The source directory itself is removed only if the move emptied it. Files
    that are not part of the library are left where they are, and keep the
    folder alive.
    """
    source = os.path.abspath(source)
    destination = os.path.abspath(destination)

    problem = describe_move_problem(source, destination)
    if problem:
        raise DataDirectoryMoveError(problem)

    members = library_members(source)
    _, total_bytes = _tree_stats(source)

    try:
        os.makedirs(destination, exist_ok=True)
    except OSError as e:
        raise DataDirectoryMoveError(f"Could not create {destination}: {e}") from e

    if should_cancel and should_cancel():
        return MoveResult(cancelled=True)

    if _same_volume(source, destination):
        result = _move_by_rename(source, destination, members, progress, total_bytes)
    else:
        result = _move_by_copy(source, destination, members, progress, should_cancel, total_bytes)

    if not result.cancelled:
        result.source_removed = _remove_if_empty(source)
        logger.info("Moved the library from %s to %s (%s)", source, destination, ", ".join(result.moved))
    return result


def _move_by_rename(source, destination, members, progress, total_bytes):
    """Move within a volume. Renames back on failure."""
    done = []
    for member in members:
        src = os.path.join(source, member)
        dst = os.path.join(destination, member)
        try:
            os.rename(src, dst)
        except OSError as e:
            _undo_renames(source, destination, done)
            raise DataDirectoryMoveError(
                f"Could not move {member} to {destination}: {e}. Nothing was moved; your data is still in {source}."
            ) from e
        done.append(member)
        if progress:
            progress(total_bytes, total_bytes, member)
    return MoveResult(moved=done, total_bytes=total_bytes)


def _undo_renames(source, destination, done):
    """Put back what was already renamed, so a failure moves nothing at all."""
    for member in reversed(done):
        try:
            os.rename(os.path.join(destination, member), os.path.join(source, member))
        except OSError as e:
            # Reported, not raised: the caller is already raising the real
            # failure, and this one must not replace it.
            logger.error("Could not put %s back in %s: %s", member, source, e)


def _move_by_copy(source, destination, members, progress, should_cancel, total_bytes):
    """Move across volumes: copy everything, verify everything, then delete.

    The source is not touched until every member has been copied *and* checked,
    which is what makes a failure or a cancellation halfway through harmless.
    """
    state = {"done": 0}

    def copy_file(src, dst, *, follow_symlinks=True):
        if should_cancel and should_cancel():
            raise _CancelledError
        shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
        state["done"] += os.path.getsize(dst)
        if progress:
            progress(state["done"], total_bytes, state.get("member", ""))

    copied = []
    try:
        for member in members:
            state["member"] = member
            src = os.path.join(source, member)
            dst = os.path.join(destination, member)
            if os.path.isdir(src):
                shutil.copytree(src, dst, copy_function=copy_file)
            else:
                copy_file(src, dst)
            _verify_copy(src, dst, member)
            copied.append(member)
    except _CancelledError:
        _discard_partial_copy(destination, members)
        return MoveResult(cancelled=True)
    except (OSError, shutil.Error, DataDirectoryMoveError) as e:
        _discard_partial_copy(destination, members)
        failed = state.get("member", "")
        message = (
            e.args[0] if isinstance(e, DataDirectoryMoveError) else f"Could not copy {failed} to {destination}: {e}"
        )
        raise DataDirectoryMoveError(f"{message} Nothing was moved; your data is still in {source}.") from e

    # Everything is across and checked. Only now does the source go.
    for member in copied:
        src = os.path.join(source, member)
        try:
            if os.path.isdir(src):
                shutil.rmtree(src)
            else:
                os.remove(src)
        except OSError as e:
            # The data is safely at the destination, so this is untidiness
            # rather than loss. Saying so beats failing a move that worked.
            logger.warning("Copied %s but could not remove the original at %s: %s", member, src, e)

    return MoveResult(moved=copied, total_bytes=total_bytes)


def _verify_copy(src, dst, member):
    """Confirm the copy holds as many files and bytes as the original."""
    src_stats = _tree_stats(src)
    dst_stats = _tree_stats(dst)
    if src_stats != dst_stats:
        raise DataDirectoryMoveError(
            f"The copy of {member} does not match the original "
            f"({src_stats[0]} files/{src_stats[1]} bytes became {dst_stats[0]}/{dst_stats[1]})."
        )


def _discard_partial_copy(destination, members):
    """Remove what was copied before the failure, leaving the source untouched."""
    for member in members:
        path = os.path.join(destination, member)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        except OSError as e:
            logger.warning("Could not clean up %s after an incomplete move: %s", path, e)


def _remove_if_empty(directory):
    """Remove the old folder if the move emptied it. True if it went."""
    try:
        if os.path.isdir(directory) and not os.listdir(directory):
            os.rmdir(directory)
            return True
    except OSError as e:
        logger.warning("Could not remove the old data directory %s: %s", directory, e)
    return False


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


IMAGE_EXTENSION_LIST = ["png", "jpg", "jpeg", "bmp", "gif", "tif", "tiff"]
MODEL_EXTENSION_LIST = ["obj", "ply", "stl"]

VIVID_COLOR_LIST = [
    "#0000FF",  # Blue
    "#FF0000",  # Red
    "#008000",  # Green
    "#800080",  # Purple
    "#FFA500",  # Orange
    "#00FFFF",  # Cyan
    "#FF00FF",  # Magenta
    "#FFFF00",  # Yellow
    "#008080",  # Teal
    "#FF1493",  # Pink
    "#00FF00",  # Lime
    "#4B0082",  # Indigo
    "#800000",  # Maroon
    "#808000",  # Olive
    "#000080",  # Navy
    "#FF6F61",  # Coral
    "#40E0D0",  # Turquoise
    "#E6E6FA",  # Lavender
    "#FFD700",  # Gold
    "#6A5ACD",  # Slate
]
PASTEL_COLOR_LIST = [
    "#AEC6CF",  # Pastel Blue
    "#F49AC2",  # Pastel Pink
    "#B0E57C",  # Pastel Green
    "#B39EB5",  # Pastel Purple
    "#F9CB9C",  # Pastel Orange
    "#F8ED8E",  # Pastel Yellow
    "#DCD0FF",  # Pastel Lavender
    "#AAF0D1",  # Pastel Mint
    "#FFD1A3",  # Pastel Peach
    "#AEEEEE",  # Pastel Aqua
    "#E8A3E5",  # Pastel Lilac
    "#FFB5B5",  # Pastel Coral
    "#94E8B4",  # Pastel Teal
    "#FF9E9E",  # Pastel Salmon
    "#87CEEB",  # Pastel Sky Blue
    "#FFC7E5",  # Pastel Rose
    "#FDFD96",  # Pastel Lemon
    "#C5A3FF",  # Pastel Periwinkle
    "#AFEEEE",  # Pastel Turquoise
    "#FFD8B1",  # Pastel Apricot
]

MARKER_LIST = ["o", "s", "^", "x", "+", "d", "v", "<", ">", "p", "h"]


def as_qt_color(color):
    if isinstance(color, QColor):
        return color
    if isinstance(color, str):
        return QColor(color)

    return QColor(*[int(x * 255) for x in color])


def as_gl_color(color):
    # print("as_gl_color", color)
    qcolor = QColor(color)
    return qcolor.redF(), qcolor.greenF(), qcolor.blueF()


def value_to_bool(value):
    return value.lower() == "true" if isinstance(value, str) else bool(value)


def process_dropped_file_name(file_name):
    import os
    from urllib.parse import unquote, urlparse

    # print("file_name:", file_name)
    url = file_name
    parsed_url = urlparse(url)
    # print("parsed_url:", parsed_url)
    file_path = unquote(parsed_url.path)
    file_path = file_path[1:] if os.name == "nt" else file_path
    return file_path


def process_3d_file(file_name):
    # get extension
    file_extension = os.path.splitext(file_name)[1][1:].lower()
    # print("file_extension:", file_extension)
    if file_extension == "obj":
        return file_name

    temp_dir = tempfile.mkdtemp()

    # get filename without extension (basename only — an absolute source path
    # would otherwise win the os.path.join and drop the converted file next to the
    # original instead of in temp_dir)
    file_name_only = os.path.splitext(os.path.basename(file_name))[0]
    # copy to temp dir
    new_file_name = os.path.join(temp_dir, file_name_only + ".obj")
    # print("new_file_name:", new_file_name)

    if file_extension == "stl":
        # stl_mesh = mesh.Mesh.from_file(file_name)
        # tri_mesh = trimesh.Trimesh(stl_mesh.vectors, process=False)
        try:
            tri_mesh = trimesh.load_mesh(file_name)
        except Exception as e:
            logger.error(f"Failed to load STL mesh from {file_name}: {e}")
            raise ValueError(f"Cannot load STL file {file_name}: {e}") from e

        # if vertices are not 2D array, convert to 2D array
        # actually in that case vertices have faces data.
        # print("stl_mesh shape:", tri_mesh.vertices.shape)
        # print("vertex normals:", tri_mesh.vertex_normals)
        # print("stl_mesh vertices:", tri_mesh.vertices[0:5,:])
        # print("stl_mesh faces:", tri_mesh.faces[0:5,:])

        try:
            tri_mesh.export(new_file_name, file_type="obj")
        except Exception as e:
            logger.error(f"Failed to export STL mesh to {new_file_name}: {e}")
            raise ValueError(f"Cannot export to OBJ file {new_file_name}: {e}") from e
    elif file_extension == "ply":
        try:
            ply_mesh = trimesh.load(file_name)
        except Exception as e:
            logger.error(f"Failed to load PLY mesh from {file_name}: {e}")
            raise ValueError(f"Cannot load PLY file {file_name}: {e}") from e
        # print("ply_mesh shape:", ply_mesh.vertices.shape)
        # print("ply_mesh vertices:", ply_mesh.vertices[0:5,:])
        # print("ply_mesh faces:", ply_mesh.faces[0:5,:])
        try:
            ply_mesh.export(new_file_name, file_type="obj")
        except Exception as e:
            logger.error(f"Failed to export PLY mesh to {new_file_name}: {e}")
            raise ValueError(f"Cannot export to OBJ file {new_file_name}: {e}") from e
    return new_file_name


def show_error_message(error_message):
    # error_message = "Number of objects is too small for analysis."
    # show messagebox and close the window
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(error_message)
    msg.setWindowTitle("Error")
    msg.exec_()
    return


def is_numeric(value):
    """Checks if a value is numeric (float)."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        # TypeError covers None and other non-stringifiable inputs.
        return False


# Morphometrics convention for "this coordinate was not recorded". Files using it
# parse as a real coordinate unless it is recognised, so an unnoticed sentinel
# silently drags every shape toward (-999, -999).
MISSING_SENTINEL = -999.0


def find_missing_sentinels(landmark_data, inverted_y=False, sentinel=MISSING_SENTINEL):
    """Locate sentinel coordinates in parsed import data.

    Args:
        landmark_data: ``{object_name: [[x, y[, z]], …]}`` as produced by the
            format readers.
        inverted_y: pass the import's invert-Y flag. The readers negate Y
            *before* this runs, so a sentinel in the Y column now reads as
            ``+999`` and would otherwise be missed.
        sentinel: the value to treat as missing.

    Returns:
        List of ``(object_name, row, col)`` triples, in iteration order.
    """
    hits = []
    for object_name, landmarks in landmark_data.items():
        for row, landmark in enumerate(landmarks):
            for col, value in enumerate(landmark):
                if not is_numeric(value):
                    continue
                target = -sentinel if (inverted_y and col == 1) else sentinel
                if float(value) == target:
                    hits.append((object_name, row, col))
    return hits


def replace_missing_sentinels(landmark_data, hits):
    """Blank out the coordinates named by ``hits`` (from ``find_missing_sentinels``).

    Mutates ``landmark_data`` in place, setting each hit to ``None`` — the
    representation the rest of the pipeline already treats as missing.
    """
    for object_name, row, col in hits:
        landmark_data[object_name][row][col] = None
    return landmark_data


def get_ellipse_params(covariance, n_std):
    # Covariance matrices are symmetric, so use eigh: it returns real
    # eigenvalues/eigenvectors (eig can yield a complex dtype that breaks
    # downstream arctan2/sqrt under numpy 2.x).
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = eigenvalues.argsort()[::-1]
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
    vx, vy = eigenvectors[:, 0][0], eigenvectors[:, 0][1]
    theta = np.arctan2(vy, vx)

    width, height = n_std * np.sqrt(eigenvalues)
    angle = np.degrees(theta)
    return width, height, angle


def read_landmark_file(file_path):
    """Read landmarks from TPS/NTS file.

    Args:
        file_path: Path to landmark file

    Returns:
        List of (specimen_name, landmarks) tuples
    """
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == ".tps":
        return read_tps_file(file_path)
    if file_ext == ".nts":
        return read_nts_file(file_path)
    if file_ext == ".txt":
        # Try to detect format
        try:
            from components.formats._encoding import open_text

            with open_text(file_path) as f:
                first_line = f.readline().strip()
                if first_line.startswith("LM="):
                    return read_tps_file(file_path)
                if "DIM=" in first_line:
                    return read_nts_file(file_path)
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"Cannot read landmark file {file_path}: {e}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {file_path}: {e}")
            raise ValueError(f"Cannot decode file {file_path}. Please check file encoding.") from e

    raise ValueError(f"Unsupported landmark file format: {file_ext}")


def read_tps_file(file_path):
    """Read TPS format landmark file.

    Args:
        file_path: Path to TPS file

    Returns:
        List of (specimen_name, landmarks) tuples
    """
    specimens = []
    current_landmarks = []
    current_name = ""

    try:
        from components.formats._encoding import open_text

        with open_text(file_path) as f:
            for line in f:
                line = line.strip()

                if line.startswith("LM="):
                    # Start new specimen
                    if current_landmarks and current_name:
                        specimens.append((current_name, current_landmarks))

                    try:
                        int(line.split("=")[1])
                    except (ValueError, IndexError) as e:
                        logger.error(f"Invalid LM line in {file_path}: {line}")
                        raise ValueError(f"Malformed TPS file: invalid LM line '{line}'") from e
                    current_landmarks = []
                    current_name = ""

                elif line.startswith("ID="):
                    try:
                        current_name = line.split("=")[1].strip()
                    except IndexError:
                        logger.warning(f"Invalid ID line in {file_path}: {line}")
                        current_name = "Unknown"

                elif line and not line.startswith(("IMAGE=", "SCALE=")):
                    # Landmark coordinates
                    try:
                        coords = [float(x) for x in line.split()]
                        if len(coords) >= 2:
                            current_landmarks.append(coords[:2])  # Use only X, Y
                    except ValueError:
                        continue

        # Add last specimen
        if current_landmarks and current_name:
            specimens.append((current_name, current_landmarks))
        elif current_landmarks:
            specimens.append((f"specimen_{len(specimens) + 1}", current_landmarks))

    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"Cannot read TPS file {file_path}: {e}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error reading TPS file {file_path}: {e}")
        raise ValueError(f"Cannot decode TPS file {file_path}. Please check file encoding.") from e
    except Exception as e:
        logger.error(f"Unexpected error reading TPS file {file_path}: {e}")
        raise ValueError(f"Failed to read TPS file {file_path}: {e}") from e

    return specimens


def read_nts_file(file_path):
    """Read NTS format landmark file.

    Args:
        file_path: Path to NTS file

    Returns:
        List of (specimen_name, landmarks) tuples
    """
    specimens = []

    try:
        from components.formats._encoding import open_text

        with open_text(file_path) as f:
            lines = f.readlines()
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"Cannot read NTS file {file_path}: {e}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error reading NTS file {file_path}: {e}")
        raise ValueError(f"Cannot decode NTS file {file_path}. Please check file encoding.") from e

    try:
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # NTS header: n_specimens n_landmarks n_dimensions unknown DIM=dimension
            if "DIM=" in line:
                parts = line.split()
                try:
                    n_specimens = int(parts[0])
                    n_landmarks = int(parts[1])
                    int(parts[2])
                except (ValueError, IndexError) as e:
                    logger.error(f"Invalid NTS header in {file_path}: {line}")
                    raise ValueError(f"Malformed NTS file: invalid header '{line}'") from e

                for _spec_idx in range(n_specimens):
                    i += 1
                    if i >= len(lines):
                        break

                    # Specimen name
                    specimen_name = lines[i].strip()
                    landmarks = []

                    # Read landmarks
                    for _lm_idx in range(n_landmarks):
                        i += 1
                        if i >= len(lines):
                            break

                        try:
                            coords = [float(x) for x in lines[i].split()]
                            landmarks.append(coords[:2])  # Use only X, Y
                        except (ValueError, IndexError):
                            # Skip invalid coordinate lines
                            continue

                    specimens.append((specimen_name, landmarks))

            i += 1

    except Exception as e:
        logger.error(f"Error parsing NTS file {file_path}: {e}")
        raise ValueError(f"Failed to parse NTS file {file_path}: {e}") from e

    return specimens


# -----------------------------
# JSON+ZIP Export/Import (Issue #048)
# -----------------------------


def serialize_dataset_to_json(dataset_id: int, include_files: bool = True, include_analyses: bool = False) -> dict:
    """Serialize dataset and objects to JSON structure for export.

    Takes no storage directory: every file reference it emits is relative to the
    package root (``images/<object id>.<ext>``), so where the attachments
    actually live is the packaging step's business, not this one's. It used to
    accept a ``storage_dir`` and document it, then evaluate
    ``os.path.abspath(storage_dir or ...)`` without assigning it -- a parameter
    that looked honoured and was not. ruff's B018 does not catch that: the
    expression is a call, which it must assume has side effects.

    Args:
        dataset_id: Dataset primary key
        include_files: Include image/model metadata
        include_analyses: Include saved analyses (schema 1.3). Off for export,
            on for a library backup. Export leaves them out because an analysis
            carries every object's raw and superimposed landmarks a second time
            and would multiply the size of a package whose purpose is to hand a
            dataset to someone else; a backup is not allowed to be lossy.

    Returns:
        dict representing the JSON schema (v1.3)
    """
    from MdModel import MdAnalysis, MdDataset, MdObject

    dataset = MdDataset.get_by_id(dataset_id)
    # Ensure lists are unpacked
    wf = dataset.unpack_wireframe()
    polys = dataset.unpack_polygons()
    base = dataset.unpack_baseline()
    vars_list = dataset.get_variablename_list()

    # Collect objects ordered by sequence (if present)
    objects_query = dataset.object_list.order_by(MdObject.sequence)

    objects_json = []
    landmark_counts = []

    for obj in objects_query:
        obj.unpack_landmark()
        obj.unpack_variable()
        # variables mapping
        variables = {}
        if vars_list:
            for i, name in enumerate(vars_list):
                val = obj.variable_list[i] if i < len(obj.variable_list) else None
                variables[name] = val

        files_meta = {}
        if include_files:
            # image
            if obj.has_image():
                img = obj.get_image()
                img_ext = (Path(img.original_path).suffix or "").lstrip(".")
                rel_path = f"images/{obj.id}.{img_ext}" if img_ext else f"images/{obj.id}"
                files_meta["image"] = {
                    "path": rel_path,
                    "original_filename": img.original_filename,
                    "size": img.size,
                    "md5hash": img.md5hash,
                    "last_modified": datetime.fromtimestamp(img.file_modified).astimezone().isoformat()
                    if img.file_modified
                    else None,
                }
            # model
            if obj.has_threed_model():
                mdl = obj.get_threed_model()
                mdl_ext = (Path(mdl.original_path).suffix or "").lstrip(".")
                rel_path = f"models/{obj.id}.{mdl_ext}" if mdl_ext else f"models/{obj.id}"
                files_meta["model"] = {
                    "path": rel_path,
                    "original_filename": mdl.original_filename,
                    "size": mdl.size,
                    "md5hash": mdl.md5hash,
                    "last_modified": datetime.fromtimestamp(mdl.file_modified).astimezone().isoformat()
                    if mdl.file_modified
                    else None,
                }

        # landmarks list (allow None entries)
        lms = obj.landmark_list or []
        if lms:
            landmark_counts.append(len(lms))

        objects_json.append(
            {
                "id": obj.id,
                "name": obj.object_name,
                "sequence": obj.sequence,
                "created_date": obj.created_at.date().isoformat() if obj.created_at else None,
                "pixels_per_mm": obj.pixels_per_mm,
                "landmarks": lms,
                "variables": variables,
                # Semi-landmark curves (schema 1.2). The raw trace and its click
                # anchors are per-object; the scheme they follow is on the dataset.
                "curve_raw": obj.get_curve_raw() or None,
                "curve_anchors": obj.get_curve_anchors() or None,
                "files": files_meta or None,
            }
        )

    lm_count = max(landmark_counts) if landmark_counts else 0

    export_info = {
        "exported_by": f"{PROGRAM_NAME} v{BUILD_INFO.get('version', PROGRAM_VERSION)}",
        "export_date": datetime.now(UTC).replace(tzinfo=None).isoformat() + "Z",
        "export_format": "JSON+ZIP",
        "include_files": bool(include_files),
    }

    dataset_json = {
        "id": dataset.id,
        "name": dataset.dataset_name,
        "description": dataset.dataset_desc,
        "dimension": dataset.dimension,
        "created_date": dataset.created_at.date().isoformat() if dataset.created_at else None,
        "modified_date": dataset.modified_at.date().isoformat() if dataset.modified_at else None,
        "variables": vars_list or [],
        "landmark_count": lm_count,
        "object_count": len(objects_json),
        "wireframe": wf or [],
        "polygons": polys or [],
        "baseline": base or [],
        # Semi-landmark curve scheme (schema 1.2): how many semi-landmarks each
        # curve carries and where its block starts. Shared by every object.
        "curve_config": dataset.get_curve_config() or [],
    }

    package = {
        "format_version": "1.3",
        "export_info": export_info,
        "dataset": dataset_json,
        "objects": objects_json,
    }
    if include_analyses:
        package["analyses"] = [_analysis_to_manifest(a) for a in dataset.analyses.order_by(MdAnalysis.id)]
    return package


# Every column MdAnalysis owns except the primary key and the dataset it hangs
# off. Listed rather than reflected so that adding a column is a decision about
# whether it belongs in a backup, not something that happens silently -- and so
# that a package written by a newer version stays readable by an older one.
ANALYSIS_FIELDS = (
    "analysis_name",
    "analysis_desc",
    "dimension",
    "wireframe",
    "baseline",
    "polygons",
    "propertyname_str",
    "superimposition_method",
    "object_info_json",
    "raw_landmark_json",
    "superimposed_landmark_json",
    "pca_analysis_result_json",
    "pca_rotation_matrix_json",
    "pca_eigenvalues_json",
    "cva_group_by",
    "cva_analysis_result_json",
    "cva_rotation_matrix_json",
    "cva_eigenvalues_json",
    "manova_group_by",
    "manova_analysis_result_json",
    "chart_settings_json",
    "curve_config_json",
)


def _analysis_to_manifest(analysis):
    """One MdAnalysis row as plain JSON data.

    The model is flat -- every result is already a JSON string in a column -- so
    this is a straight field copy. The timestamps are carried too: an analysis
    is dated evidence, and restoring one with today's date would misrepresent
    when the work was done.
    """
    entry = {field: getattr(analysis, field) for field in ANALYSIS_FIELDS}
    entry["created_at"] = analysis.created_at.isoformat() if analysis.created_at else None
    entry["modified_at"] = analysis.modified_at.isoformat() if analysis.modified_at else None
    return entry


def _analysis_from_manifest(entry, dataset):
    """Recreate an analysis from a package and attach it to ``dataset``."""
    from MdModel import MdAnalysis

    analysis = MdAnalysis(dataset=dataset)
    for field in ANALYSIS_FIELDS:
        if field in entry:
            setattr(analysis, field, entry[field])
    # A name is required by the schema; a package that lost it should not take
    # the whole restore down with it.
    if not analysis.analysis_name:
        analysis.analysis_name = "Restored analysis"
    if not analysis.superimposition_method:
        analysis.superimposition_method = "Procrustes"
    for field in ("created_at", "modified_at"):
        value = entry.get(field)
        if value:
            with contextlib.suppress(ValueError, TypeError):
                setattr(analysis, field, datetime.fromisoformat(value))
    analysis.save()
    return analysis


def collect_dataset_files(dataset_id: int, storage_dir: str | None = None) -> tuple[list[str], list[str]]:
    """Collect absolute file paths (images, models) for the dataset."""
    from MdModel import MdDataset, MdObject

    storage_base = os.path.abspath(storage_dir or get_storage_directory())
    ds = MdDataset.get_by_id(dataset_id)
    images: list[str] = []
    models: list[str] = []
    for obj in ds.object_list.order_by(MdObject.sequence):
        if obj.has_image():
            p = obj.get_image().get_file_path(storage_base)
            if os.path.exists(p):
                images.append(p)
        if obj.has_threed_model():
            p = obj.get_threed_model().get_file_path(storage_base)
            if os.path.exists(p):
                models.append(p)
    return images, models


def estimate_package_size(dataset_id: int, include_files: bool = True) -> int:
    """Estimate total size (bytes) of JSON + optional files."""
    try:
        data = serialize_dataset_to_json(dataset_id, include_files=include_files)
        json_size = len(json.dumps(data, ensure_ascii=False))
    except Exception:
        json_size = 0
    total = json_size
    if include_files:
        imgs, mdls = collect_dataset_files(dataset_id)
        for p in imgs + mdls:
            try:
                total += os.path.getsize(p)
            except OSError:
                continue
    return total


def create_zip_package(
    dataset_id: int,
    output_path: str,
    include_files: bool = True,
    progress_callback: Callable[[int, int], None] | None = None,
    include_analyses: bool = False,
) -> bool:
    """Create JSON+ZIP package for a dataset.

    progress_callback: callable(curr, total)
    include_analyses: see ``serialize_dataset_to_json``. Defaults off so export
        keeps producing what it always has; the library backup turns it on.
    """
    storage_base = get_storage_directory()
    data = serialize_dataset_to_json(dataset_id, include_files=include_files, include_analyses=include_analyses)

    # Prepare temp assembly dir
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        images_dir = tmp_root / "images"
        models_dir = tmp_root / "models"
        images_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON
        dataset_json_path = tmp_root / "dataset.json"
        with open(dataset_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        total_steps = 1
        files_to_copy: list[tuple[Path, Path]] = []
        if include_files:
            # Build copy plan based on objects in JSON
            for obj in data.get("objects", []):
                files = obj.get("files") or {}
                if "image" in files and files["image"] and files["image"].get("path"):
                    rel = files["image"]["path"]
                    ext = Path(rel).suffix
                    src = Path(storage_base) / str(data["dataset"]["id"]) / f"{obj['id']}{ext}"
                    dst = tmp_root / rel
                    files_to_copy.append((src, dst))
                if "model" in files and files["model"] and files["model"].get("path"):
                    rel = files["model"]["path"]
                    ext = Path(rel).suffix
                    src = Path(storage_base) / str(data["dataset"]["id"]) / f"{obj['id']}{ext}"
                    dst = tmp_root / rel
                    files_to_copy.append((src, dst))
        total_steps += len(files_to_copy)

        # Copy files
        curr = 0
        for src, dst in files_to_copy:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            except Exception as e:
                logger.warning(f"Failed to include file {src}: {e}")
            curr += 1
            if progress_callback:
                progress_callback(curr, total_steps)

        # Create ZIP
        zip_mode = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(output_path, "w", compression=zip_mode) as zf:
            for root, _, files in os.walk(tmp_root):
                for name in files:
                    full = Path(root) / name
                    arc = str(full.relative_to(tmp_root))
                    zf.write(str(full), arcname=arc)
                    curr += 1
                    if progress_callback:
                        progress_callback(curr, total_steps + len(list(files)))

    return True


def validate_json_schema(data: dict) -> tuple[bool, list[str]]:
    """Lightweight validation of the exported schema."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return False, ["Root is not an object"]
    errors.extend(f"Missing key: {k}" for k in ["format_version", "export_info", "dataset", "objects"] if k not in data)
    ds = data.get("dataset", {})
    errors.extend(f"dataset missing: {k}" for k in ["name", "dimension", "variables"] if k not in ds)
    if not isinstance(data.get("objects", []), list):
        errors.append("objects must be a list")
    return (len(errors) == 0), errors


def _is_within_directory(base: Path, target: Path) -> bool:
    """Return True if resolved ``target`` is inside (or equals) resolved ``base``.

    Uses path-component containment rather than a raw string-prefix test, so a
    sibling directory sharing the prefix (e.g. base ``/tmp/ab`` vs
    ``/tmp/abcd``) is correctly rejected.
    """
    base = base.resolve()
    target = target.resolve()
    return target == base or base in target.parents


def safe_extract_zip(zip_path: str, dest_dir: str) -> str:
    """Safely extract ZIP to dest_dir, preventing Zip Slip."""
    dest = Path(dest_dir).resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            member_path = dest / member.filename
            if not _is_within_directory(dest, member_path):
                raise ValueError(f"Unsafe path in ZIP: {member.filename}")
        zf.extractall(dest)
    return str(dest)


def read_json_from_zip(zip_path: str) -> dict:
    with zipfile.ZipFile(zip_path, "r") as zf, zf.open("dataset.json") as f:
        return json.loads(f.read().decode("utf-8"))


def _unique_dataset_name(MdDataset, base_name):
    """Append (1), (2), ... until the dataset name is free."""
    candidate = base_name
    suffix = 1
    while MdDataset.select().where(MdDataset.dataset_name == candidate).exists():
        candidate = f"{base_name} ({suffix})"
        suffix += 1
    return candidate


def _dataset_from_manifest(ds_meta):
    """Create and save the MdDataset described by a package manifest."""
    from MdModel import MdDataset

    ds = MdDataset()
    ds.dataset_name = _unique_dataset_name(MdDataset, ds_meta.get("name") or "Imported Dataset")
    ds.dataset_desc = ds_meta.get("description")
    try:
        ds.dimension = int(ds_meta.get("dimension") or 2)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid dimension in manifest: {ds_meta.get('dimension')!r}") from e

    ds.variablename_list = ds_meta.get("variables") or []
    ds.pack_variablename_str()
    ds.edge_list = ds_meta.get("wireframe") or []
    ds.pack_wireframe()
    ds.polygon_list = ds_meta.get("polygons") or []
    ds.pack_polygons()
    baseline = ds_meta.get("baseline") or []
    if baseline:
        ds.baseline_point_list = baseline
        ds.pack_baseline()
    # Semi-landmark curve scheme (schema 1.2+); absent in 1.1 packages.
    curve_config = ds_meta.get("curve_config") or []
    if curve_config:
        ds.set_curve_config(curve_config)
    ds.save()
    return ds


def _object_from_manifest(obj_meta, ds):
    """Create and save one MdObject described by a package manifest."""
    from MdModel import MdObject

    mo = MdObject()
    mo.object_name = obj_meta.get("name") or str(obj_meta.get("id"))
    mo.object_desc = None

    ppm = obj_meta.get("pixels_per_mm")
    try:
        mo.pixels_per_mm = float(ppm) if ppm is not None else None
    except (ValueError, TypeError):
        logger.warning(f"Invalid pixels_per_mm {ppm!r}; leaving unset")
        mo.pixels_per_mm = None

    mo.sequence = obj_meta.get("sequence")

    # Missing coordinates are exported as JSON null; write them back with the
    # app's own marker (pack_landmark's "Missing"), not str(None).
    mo.dataset = ds
    mo.landmark_list = [lm[: ds.dimension] for lm in (obj_meta.get("landmarks") or []) if lm is not None]
    mo.pack_landmark()

    varmap = obj_meta.get("variables") or {}
    mo.variable_list = [varmap.get(n) if varmap.get(n) is not None else "" for n in ds.variablename_list]
    mo.pack_variable()
    mo.save()

    # Semi-landmark curves (schema 1.2+); absent in 1.1 packages.
    curve_raw = obj_meta.get("curve_raw") or {}
    curve_anchors = obj_meta.get("curve_anchors") or {}
    if curve_raw or curve_anchors:
        mo.set_curve_raw(curve_raw)
        mo.set_curve_anchors(curve_anchors)
        mo.save()
    return mo


def _import_media(meta, media_cls, mo, root, storage_base, copied_files, kind):
    """Copy one packaged media file (image or 3D model) into permanent storage.

    The path comes from the (untrusted) dataset.json inside the package, so it is
    rejected unless it stays within the extraction root -- a crafted "../../.."
    must not copy an arbitrary host file. Shared by the image and model paths,
    which were otherwise identical.
    """
    if not (meta and meta.get("path")):
        return
    src = Path(root) / meta["path"]
    if not _is_within_directory(Path(root), src):
        logger.warning(f"Skipping unsafe {kind} path in package: {meta['path']!r}")
        return
    if not src.exists():
        return

    media = media_cls()
    media.object = mo
    media.load_file_info(str(src))
    new_fp = media.get_file_path(storage_base)
    Path(new_fp).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(new_fp))
    copied_files.append(str(new_fp))
    media.save()


def import_dataset_from_zip(zip_path: str, progress_callback: Callable[[int, int], None] | None = None) -> int:
    """Import dataset from a JSON+ZIP package. Returns new dataset id."""
    from MdModel import MdImage, MdThreeDModel, gDatabase

    # Media copied into permanent storage; removed if the transaction rolls back
    # so a failed import doesn't leave orphaned files behind.
    copied_files: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            root = safe_extract_zip(zip_path, tmpdir)
            data = read_json_from_zip(zip_path)
        except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Corrupt or invalid dataset package: {e}") from e
        ok, errs = validate_json_schema(data)
        if not ok:
            raise ValueError("Invalid dataset.json: " + "; ".join(errs))

        objs = data.get("objects", [])
        total = max(1, len(objs) * 3)
        curr = 0
        if progress_callback:
            progress_callback(curr, total)

        ds = None
        try:
            with gDatabase.atomic():
                ds = _dataset_from_manifest(data["dataset"])
                storage_base = get_storage_directory()

                for obj_meta in objs:
                    mo = _object_from_manifest(obj_meta, ds)
                    curr += 1
                    if progress_callback:
                        progress_callback(curr, total)

                    files = obj_meta.get("files") or {}
                    if isinstance(files, dict):
                        _import_media(files.get("image"), MdImage, mo, root, storage_base, copied_files, "image")
                        _import_media(files.get("model"), MdThreeDModel, mo, root, storage_base, copied_files, "model")

                    curr += 2
                    if progress_callback:
                        progress_callback(curr, total)

                # Analyses last: they reference the dataset, and restoring them
                # inside the same transaction means a package either arrives
                # whole or not at all. Absent in packages before schema 1.3 and
                # in every export, so the key is optional.
                for entry in data.get("analyses") or []:
                    _analysis_from_manifest(entry, ds)

            return ds.id
        except Exception:
            # atomic() rolled back the DB, so the new dataset no longer exists.
            # Remove its whole storage directory: it holds every media file
            # copied for this import (all under <storage>/<ds.id>/) plus any
            # directories created along the way, including a file left partially
            # written by a copy that failed mid-way and so was never tracked.
            if ds is not None:
                storage_dir = os.path.join(get_storage_directory(), str(ds.id))
                try:
                    if os.path.isdir(storage_dir):
                        shutil.rmtree(storage_dir)
                except OSError as e:
                    logger.warning(f"Failed to remove orphaned import directory {storage_dir}: {e}")
            # Backstop for any tracked file that somehow sits outside that tree.
            for fp in copied_files:
                try:
                    if os.path.exists(fp):
                        os.remove(fp)
                except OSError as e:
                    logger.warning(f"Failed to clean up orphaned import file {fp}: {e}")
            raise


# ---------------------------------------------------------------------------
# Backing up the whole library
#
# The database has rotating backups (``prepare_database``) but the media do not,
# and those backups sit on the same disk as the thing they protect -- so the one
# failure they cannot survive is the likely one. This produces a single
# self-contained archive the user can put anywhere: an external drive, or a
# synchronised folder, which is safe for an archive in a way a live database is
# not (see ``describe_location_risk``). It is the answer to the risk that made
# moving the default location the wrong fix.
#
# The format is a ZIP of the per-dataset packages that export already produces.
# That is deliberate: both the writing and the reading side are code that is
# already exercised, and a backup nobody can restore is not a backup. The outer
# archive is stored uncompressed because its members are already deflated.
#
# **Saved analyses are included** (schema 1.3), which is why the packages here
# are written with ``include_analyses=True`` while export is not. A backup is
# not allowed to be lossy: an analysis is dated evidence of work done, and
# "you can recompute it" is not the same as still having the one that was run.
# Export keeps them out because an analysis repeats every object's raw and
# superimposed landmarks, which would multiply the size of a package whose job
# is to hand one dataset to a colleague.
#
# What is left out is preferences, which the application recreates. The manifest
# states both lists in as many words, rather than leaving the boundary to be
# discovered after a disk failure.
# ---------------------------------------------------------------------------

LIBRARY_BACKUP_FORMAT_VERSION = "1.0"
LIBRARY_BACKUP_MANIFEST = "library.json"


class LibraryBackupError(Exception):
    """A backup or restore refused to start, or failed. The message is shown."""


class LibraryBackupResult:
    """What a backup or restore did.

    ``missing_files`` is the part worth surfacing: a media file the database
    knows about but the disk no longer has is exactly what a backup should be
    reporting, and it must not be mistaken for a complete one.
    """

    def __init__(self, path=None, datasets=None, missing_files=None, cancelled=False, failed=None):
        self.path = path
        self.datasets = datasets or []
        self.missing_files = missing_files or []
        self.cancelled = cancelled
        self.failed = failed or []

    @property
    def complete(self):
        return not self.cancelled and not self.missing_files and not self.failed


def _safe_member_name(name):
    """A dataset name reduced to something every filesystem accepts."""
    cleaned = "".join("_" if c in '<>:"/\\|?*' or ord(c) < 32 else c for c in (name or "")).strip(" .")
    return (cleaned or "dataset")[:80]


def _expected_media(dataset_id):
    """The archive-relative media paths a dataset's package should contain."""
    data = serialize_dataset_to_json(dataset_id, include_files=True)
    return [
        entry["path"]
        for obj in data.get("objects", [])
        for entry in (obj.get("files") or {}).values()
        if entry and entry.get("path")
    ]


def _missing_from_package(dataset_id, package_path):
    """Media the package should hold and does not.

    Checked against the written archive rather than trusted from the writer:
    ``create_zip_package`` logs a warning and carries on when a file cannot be
    copied, which is defensible for an export and not for a backup.
    """
    with zipfile.ZipFile(package_path) as zf:
        present = set(zf.namelist())
    return [path for path in _expected_media(dataset_id) if path not in present]


def create_library_backup(output_path, progress_callback=None, should_cancel=None):
    """Write every dataset in the library to one archive at ``output_path``.

    ``progress_callback`` is called as ``(done, total, label)``.

    The archive is assembled under a temporary name and moved into place only
    when it is complete. An interrupted run therefore leaves no file at all,
    rather than a truncated one that looks like a backup -- believing you have a
    backup you do not have is worse than knowing you have none.
    """
    from MdModel import MdDataset

    datasets = list(MdDataset.select().order_by(MdDataset.id))
    if not datasets:
        raise LibraryBackupError("There is nothing to back up: this library has no datasets.")

    output_path = os.path.abspath(output_path)
    partial_path = output_path + ".partial"
    entries = []
    missing_files = []

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            packages = []
            for index, dataset in enumerate(datasets, start=1):
                if should_cancel and should_cancel():
                    return LibraryBackupResult(cancelled=True)

                member = f"datasets/{index:04d}_{_safe_member_name(dataset.dataset_name)}.zip"
                package = os.path.join(tmpdir, f"{index:04d}.zip")
                create_zip_package(dataset.id, package, include_files=True, include_analyses=True)

                missing = _missing_from_package(dataset.id, package)
                missing_files.extend(f"{dataset.dataset_name}: {path}" for path in missing)
                packages.append((member, package))
                entries.append(
                    {
                        "file": member,
                        "id": dataset.id,
                        "name": dataset.dataset_name,
                        "dimension": dataset.dimension,
                        "object_count": dataset.object_list.count(),
                        "analysis_count": dataset.analyses.count(),
                        "missing_files": missing,
                    }
                )
                if progress_callback:
                    progress_callback(index, len(datasets) + 1, dataset.dataset_name)

            manifest = {
                "format_version": LIBRARY_BACKUP_FORMAT_VERSION,
                "program_version": PROGRAM_VERSION,
                "created": datetime.now().astimezone().isoformat(),
                "dataset_count": len(entries),
                "datasets": entries,
                # Stated in the archive itself, so it survives being read years
                # later by someone who never saw the dialog that made it.
                "includes": ("datasets, objects, landmarks, variables, images, 3D models, saved analyses"),
                "excludes": "preferences (window layout, colours), which the application recreates",
            }

            # ZIP_STORED: every member is an already-deflated package, and
            # compressing them again costs time to no purpose.
            with zipfile.ZipFile(partial_path, "w", compression=zipfile.ZIP_STORED) as zf:
                zf.writestr(LIBRARY_BACKUP_MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2))
                for member, package in packages:
                    zf.write(package, arcname=member)

            if progress_callback:
                progress_callback(len(datasets) + 1, len(datasets) + 1, "")

        os.replace(partial_path, output_path)
    except OSError as e:
        _discard_partial_backup(partial_path)
        raise LibraryBackupError(f"Could not write the backup to {output_path}: {e}") from e
    except Exception:
        _discard_partial_backup(partial_path)
        raise

    logger.info("Wrote a library backup of %d datasets to %s", len(entries), output_path)
    return LibraryBackupResult(path=output_path, datasets=entries, missing_files=missing_files)


def _discard_partial_backup(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as e:
        logger.warning("Could not remove the incomplete backup %s: %s", path, e)


def read_library_backup_manifest(zip_path):
    """The manifest of a library backup, for showing what is in it before restoring."""
    try:
        with zipfile.ZipFile(zip_path) as zf, zf.open(LIBRARY_BACKUP_MANIFEST) as f:
            manifest = json.loads(f.read().decode("utf-8"))
    except (OSError, KeyError, zipfile.BadZipFile, ValueError) as e:
        raise LibraryBackupError(f"{zip_path} is not a Modan2 library backup: {e}") from e

    if not isinstance(manifest, dict) or "datasets" not in manifest:
        raise LibraryBackupError(f"{zip_path} is not a Modan2 library backup: no dataset list.")
    return manifest


def restore_library_backup(zip_path, progress_callback=None, should_cancel=None):
    """Import every dataset from a library backup into the current library.

    **This adds; it never replaces.** Datasets arrive alongside what is already
    there, taking a free name if one is taken. Restoring can therefore not
    destroy anything, which is what makes it safe to offer to someone who is
    unsure whether they need it -- the alternative, wiping the library first,
    turns a mistaken restore into the very loss it was meant to undo.

    A dataset that fails to import is recorded and the rest continue: each
    import is its own transaction, so a bad one leaves nothing behind, and
    stopping would deny the user the datasets that were fine.
    """
    manifest = read_library_backup_manifest(zip_path)
    entries = manifest.get("datasets", [])
    restored = []
    failed = []

    with tempfile.TemporaryDirectory() as tmpdir, zipfile.ZipFile(zip_path) as zf:
        for index, entry in enumerate(entries, start=1):
            if should_cancel and should_cancel():
                return LibraryBackupResult(datasets=restored, failed=failed, cancelled=True)

            member = entry.get("file")
            name = entry.get("name") or member
            try:
                if member not in zf.namelist():
                    raise LibraryBackupError(f"the archive has no member {member}")
                extracted = os.path.join(tmpdir, f"{index:04d}.zip")
                with zf.open(member) as src, open(extracted, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                restored.append({"name": name, "id": import_dataset_from_zip(extracted)})
            except Exception as e:
                logger.warning("Could not restore %s from %s: %s", name, zip_path, e)
                failed.append({"name": name, "error": str(e)})

            if progress_callback:
                progress_callback(index, len(entries), name)

    logger.info("Restored %d of %d datasets from %s", len(restored), len(entries), zip_path)
    return LibraryBackupResult(path=zip_path, datasets=restored, failed=failed)


def resample_polyline(points, n, closed=False):
    """Resample an ordered curve (polyline) to exactly ``n`` equidistant points.

    Points are spaced by arc length: this is the general, robust choice for
    semi-landmarks. Equal-angle spacing is deliberately not offered -- it only
    holds for curves single-valued in angle about a centre (a star-convex
    outline) and breaks on open curves, inflection points and non-convex shapes.

    This turns a densely traced curve into evenly-spaced semi-landmarks. The raw
    trace is preserved separately (MdObject.curve_raw_json); this only computes
    the resampled points that become ordinary landmarks.

    Args:
        points: ordered sequence of ``[x, y]`` (2D) or ``[x, y, z]`` (3D) coords
            tracing the curve.
        n: number of output points, ``>= 2``.
        closed: treat the polyline as a closed loop (last point joins the first).
            An open curve preserves both endpoints (points at ``i*L/(n-1)``); a
            closed one spreads ``n`` points over the loop with no duplicated end.

    Returns:
        list of ``n`` ``[x, y(, z)]`` points.

    Raises:
        ValueError: fewer than 2 input points, or ``n < 2``.
    """
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        raise ValueError("resample_polyline needs at least 2 input points")
    if n < 2:
        raise ValueError("resample_polyline needs n >= 2")

    if closed:
        pts = np.vstack([pts, pts[0]])

    deltas = np.diff(pts, axis=0)
    seg_len = np.sqrt((deltas**2).sum(axis=1))
    cum = np.concatenate([[0.0], np.cumsum(seg_len)])
    total = cum[-1]

    if total == 0:
        # Every point coincides -- nothing to space out.
        return [pts[0].tolist() for _ in range(n)]

    # Closed loops omit the duplicated end point; open curves keep both ends.
    targets = np.linspace(0.0, total, n, endpoint=not closed)

    out = []
    for t in targets:
        idx = int(np.searchsorted(cum, t, side="right") - 1)
        idx = min(max(idx, 0), len(seg_len) - 1)
        seg = seg_len[idx]
        frac = 0.0 if seg == 0 else (t - cum[idx]) / seg
        out.append((pts[idx] + frac * (pts[idx + 1] - pts[idx])).tolist())
    return out


def smooth_polyline(points, iterations=2, pin_ends=True):
    """Smooth a polyline with a 3-point moving average (Laplacian smoothing).

    Live-wire traces follow image edges pixel-by-pixel, so they carry a fine
    staircase jitter. Averaging each interior point with its two neighbours
    removes that jitter while keeping the overall shape; a few light iterations
    are enough. Endpoints are pinned by default so a snapped segment stays
    anchored to its clicked endpoints (the semi-landmark curve's control points).

    Args:
        points: ordered ``[x, y(, z)]`` polyline points.
        iterations: how many averaging passes; more means smoother/looser.
        pin_ends: keep the first and last points fixed (default True).

    Returns:
        list of ``[x, y(, z)]`` points, same length as the input. Inputs shorter
        than 3 points are returned unchanged (nothing to smooth).
    """
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 3 or iterations < 1:
        return [list(p) for p in np.asarray(points, dtype=float)]
    for _ in range(iterations):
        averaged = pts.copy()
        averaged[1:-1] = (pts[:-2] + pts[1:-1] + pts[2:]) / 3.0
        if pin_ends:
            averaged[0] = pts[0]
            averaged[-1] = pts[-1]
        pts = averaged
    return [p.tolist() for p in pts]


def build_landmarks_with_curves(fixed_landmarks, curves):
    """Assemble a landmark list and its curve configuration.

    Layout: the fixed (anatomical) landmarks first, unchanged, then each curve's
    evenly-spaced semi-landmarks appended in order. Keeping fixed landmarks first
    means their indices never move when curves are added, changed or removed, so
    wireframe/baseline references to them stay valid (see devlog 237).

    Args:
        fixed_landmarks: ordered ``[x, y(, z)]`` anatomical landmarks, kept as-is.
        curves: ordered list of dicts, one per curve:
            ``{"id": str, "n": int, "raw": [[x, y(, z)], ...], "closed": bool?}``
            -- the curve id, target semi-landmark count, the raw traced polyline,
            and whether it is a closed loop (default False).

    Returns:
        ``(landmark_list, config)`` where ``config`` is a list of
        ``{"id", "n", "method", "start"}`` with 0-based ``start`` indices into
        ``landmark_list`` marking where each curve's semi-landmarks begin.

    Raises:
        ValueError: propagated from :func:`resample_polyline` for a bad curve.
    """
    landmark_list = [list(p) for p in fixed_landmarks]
    config = []
    for curve in curves:
        start = len(landmark_list)
        points = resample_polyline(curve["raw"], curve["n"], closed=curve.get("closed", False))
        landmark_list.extend(points)
        config.append({"id": curve["id"], "n": curve["n"], "method": "equidistant", "start": start})
    return landmark_list, config


def build_curve_config(fixed_count, curves):
    """Build a semi-landmark curve config from a dataset-level scheme.

    The scheme fixes, for the whole dataset, how many fixed (anatomical)
    landmarks come first and how many semi-landmarks each curve contributes, so
    every specimen shares one unambiguous layout (see devlog 237). Curves are
    laid out after the fixed landmarks in order; each curve's ``start`` index is
    derived from the fixed count plus the preceding curves' counts. Ids are
    positional (``curve1``, ``curve2``, ...) so they renumber when curves are
    added or removed; the optional user ``name`` travels with the curve.

    Args:
        fixed_count: number of fixed landmarks that precede the curves (K).
        curves: ordered per-curve entries, each either an int count or a dict
            ``{"n": int, "name": str?}``.

    Returns:
        list of ``{"id", "n", "method", "start", "name"}`` (empty if no curves).
    """
    config = []
    start = int(fixed_count)
    for i, curve in enumerate(curves):
        if isinstance(curve, dict):
            n = int(curve.get("n", 0))
            name = curve.get("name", "")
            desc = curve.get("desc", "")
        else:
            n = int(curve)
            name = ""
            desc = ""
        config.append(
            {"id": f"curve{i + 1}", "n": n, "method": "equidistant", "start": start, "name": name, "desc": desc}
        )
        start += n
    return config
