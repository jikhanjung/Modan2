#!/usr/bin/env python
"""
Modan2 - Morphometric Data Analysis Application
Main entry point for the application
"""

import argparse
import contextlib
import logging
import sys
from pathlib import Path


def _install_global_excepthook(logger):
    """Install a last-resort hook for exceptions not caught by a slot's guard.

    PyQt5 aborts the process when an exception escapes a slot invoked from the
    event loop. The per-slot ``@guard_slot`` decorator is the primary defense,
    but its coverage is partial; this hook is a backstop that logs the traceback
    and shows a non-fatal dialog so an unguarded slot raising does not kill the
    app with no explanation. ``KeyboardInterrupt`` is left to the default handler.
    """

    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox

            if QApplication.instance() is not None:
                QMessageBox.critical(
                    None,
                    "Modan2 - Unexpected Error",
                    f"An unexpected error occurred:\n\n{exc_value}\n\n"
                    "The application will try to continue. Details are in the log.",
                )
        except Exception:
            # Never let the error handler itself raise.
            pass

    sys.excepthook = _hook


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Modan2 - Morphometric Data Analysis Application",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose logging")

    parser.add_argument("--db", type=str, help="Database file path (default: ~/PaleoBytes/Modan2/Modan2.db)")

    parser.add_argument(
        "--config", type=str, help="Configuration file path (default: ~/PaleoBytes/Modan2/preferences.json)"
    )

    parser.add_argument("--lang", type=str, choices=["en", "ko"], default="en", help="UI language")

    parser.add_argument("--no-splash", action="store_true", help="Skip splash screen on startup")

    # Boot the full app (heavy imports + main window) then exit 0 without entering
    # interactive use. Used by CI to smoke-test the *frozen* build on a clean
    # runner (QT_QPA_PLATFORM=offscreen): catches "works from source, broken when
    # frozen" failures (a PyInstaller-missing data file / unbundled native lib)
    # that source-tree tests cannot reach.
    parser.add_argument("--self-test", action="store_true", help="Boot the app headless, then exit 0 (CI smoke test)")

    # Import version
    try:
        from version import __version__

        version_string = f"Modan2 {__version__}"
    except ImportError:
        version_string = "Modan2 0.1.5-alpha.1"

    parser.add_argument("--version", action="version", version=version_string)

    return parser.parse_args()


def setup_logging(debug: bool = False, config_path: str | None = None):
    """Setup application logging with fallback options.

    Logging is configured before anything else, so the chosen data directory is
    read straight from the preferences file here rather than from parsed
    configuration that does not exist yet. That is possible because preferences
    live in the OS configuration location (devlog 277) instead of inside the
    data directory -- when they were inside it, finding them required knowing
    the very thing being looked up.

    A first launch after upgrading writes this run's log to the default location,
    because the one-time preferences migration has not happened yet. Harmless,
    and only ever once.

    **A chosen directory that is missing is left alone here**, and this run logs
    to the default location instead. Creating it would be the wrong thing twice
    over: it destroys the evidence that startup needs in order to notice and ask
    the user (an unplugged drive would look like an empty library), and the log
    explaining that failure would be written to the very place nobody can find.
    """
    level = logging.DEBUG if debug else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Try to get proper log directory, with fallbacks
    from datetime import datetime

    date_str = datetime.now().astimezone().strftime("%Y%m%d")
    log_filename = f"Modan2_{date_str}.log"

    log_file_path = None
    try:
        import MdUtils

        configured = MdUtils.read_configured_data_directory(config_path)
        if configured and MdUtils.describe_data_directory_problem(configured):
            print(f"Warning: the configured data directory is unavailable ({configured}); logging to the default")
            configured = ""
        MdUtils.set_data_directory(configured)
        MdUtils.ensure_directories()
        log_file_path = Path(MdUtils.get_log_directory()) / log_filename
    except Exception as e:
        print(f"Warning: Could not access configured log directory: {e}")
        # Fallback to local logs directory
        try:
            log_dir = Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file_path = log_dir / log_filename
        except Exception:
            # Final fallback to temp directory
            import tempfile

            temp_dir = Path(tempfile.gettempdir())
            log_file_path = temp_dir / log_filename
            print(f"Using fallback log file: {log_file_path}")

    # Setup handlers
    try:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout), file_handler]
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")
        # Fallback to console-only logging if file handler cannot be created
        handlers = [logging.StreamHandler(sys.stdout)]

    logging.basicConfig(level=level, format=format_str, handlers=handlers)

    # Reduce noise from Qt and matplotlib
    logging.getLogger("PyQt5").setLevel(logging.WARNING)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)


def _patch_frozen_dependency_versions():
    """Restore ``pytz.__version__`` when it goes missing in a frozen build.

    In a PyInstaller-frozen app pandas' hard dependency pytz can end up without
    its ``__version__`` attribute — the version is derived from the package
    metadata, which isn't always bundled — and pandas then aborts its own import
    with "Can't determine version for pytz" (pandas/compat/_optional.py). Rebuild
    the attribute from any source available, falling back to a hardcoded string
    so pandas always sees a non-empty value. No-op in a normal environment where
    ``__version__`` is present; must run before anything imports pandas.
    """
    try:
        import pytz

        if not getattr(pytz, "__version__", None):
            version = getattr(pytz, "VERSION", None) or getattr(pytz, "OLSON_VERSION", None)
            if not version:
                try:
                    from importlib.metadata import version as _pkg_version

                    version = _pkg_version("pytz")
                except Exception:
                    version = None
            # Last-resort constant: pandas only requires a non-empty version string.
            pytz.__version__ = version or "2025.1"
    except Exception:
        # The shim must never be the thing that breaks startup.
        pass


def _ask_about_data_directory(problem, splash=None):
    """Ask what to do about a data directory the user chose that is unusable.

    Returns "quit", "default" or "continue". Asked before anything is created in
    the location, because carrying on writes a fresh empty library there and
    that is indistinguishable, to the user, from having lost the real one.
    Falling back to the default without asking would look the same, so it is
    offered rather than taken.

    Deliberately untranslated. This runs during ``ApplicationSetup.initialize``,
    before ``_load_translations`` has installed a QTranslator, so ``tr()`` here
    would return the English string anyway -- with the added cost of looking as
    though it had been handled.
    """
    from PyQt5.QtWidgets import QMessageBox

    if splash is not None:
        splash.hide()

    box = QMessageBox()
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle("Modan2 — data location unavailable")
    box.setText(problem)
    box.setInformativeText(
        "Your data has not been deleted. Check that the drive or network location "
        "is connected, then start Modan2 again.\n\n"
        "Starting anyway will create a new, empty library in that location."
    )
    quit_button = box.addButton("Quit", QMessageBox.RejectRole)
    default_button = box.addButton("Use default location", QMessageBox.AcceptRole)
    box.addButton("Start anyway", QMessageBox.DestructiveRole)
    box.setDefaultButton(quit_button)
    box.exec_()

    clicked = box.clickedButton()
    if clicked is quit_button:
        return "quit"
    if clicked is default_button:
        return "default"
    return "continue"


def main():
    """Main application entry point."""
    args = parse_arguments()

    # Setup logging first
    setup_logging(debug=args.debug, config_path=args.config)
    logger = logging.getLogger(__name__)

    # Guard against frozen-build dependency-version quirks before any heavy
    # (pandas-pulling) imports happen below.
    _patch_frozen_dependency_versions()

    logger.info("Starting Modan2 application...")
    logger.debug(f"Command line arguments: {vars(args)}")

    # Bound before the try so the error handler can always close it, whatever
    # step failed.
    splash = None

    try:
        # Qt application setup - minimal imports for splash screen
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon
        from PyQt5.QtWidgets import QApplication

        # High DPI support
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # Import version for app metadata
        try:
            from version import __version__

            app_version = __version__
        except ImportError:
            app_version = "0.1.5-alpha.1"

        # Qt derives QStandardPaths locations from the organisation and
        # application names, so both come from MdUtils rather than being spelled
        # out again here -- the organisation used to read "Modan2 Team" while
        # everything else (COMPANY_NAME, the install path) said PaleoBytes, which
        # would have put preferences beside nothing else.
        # MdConstants.APP_AUTHOR stays "Modan2 Team": a credit, not a path.
        from MdUtils import COMPANY_NAME, PROGRAM_NAME

        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName(PROGRAM_NAME)
        app.setApplicationVersion(app_version)
        app.setOrganizationName(COMPANY_NAME)

        # Backstop behind @guard_slot: keep an unguarded slot exception from
        # aborting the whole process (see _install_global_excepthook).
        _install_global_excepthook(logger)

        # Set application icon
        icon_path = Path(__file__).parent / "icons" / "Modan2.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))

        # Show splash screen FIRST, before any heavy imports
        if not args.no_splash:
            from MdSplashScreen import create_splash_screen

            # Try to use background image if available
            splash_bg_path = Path(__file__).parent / "icons" / "Modan2.png"
            background_path = str(splash_bg_path) if splash_bg_path.exists() else None

            splash = create_splash_screen(background_path)
            splash.setProgress("Starting Modan2...")
            splash.show()
            QApplication.processEvents()  # Force immediate display

        # Now do heavy imports and initialization with splash screen visible
        if splash:
            splash.setProgress("Loading application modules...")
            QApplication.processEvents()

        # Initialize application setup
        from MdAppSetup import ApplicationSetup

        setup = ApplicationSetup(
            debug=args.debug,
            db_path=args.db,
            config_path=args.config,
            language=args.lang,
            # No prompt under --self-test: there is nobody to answer it, and a
            # modal waiting forever would hang CI rather than fail it.
            on_data_directory_problem=(
                None if args.self_test else lambda problem, directory: _ask_about_data_directory(problem, splash)
            ),
        )

        if splash:
            splash.setProgress("Initializing configuration...")
            QApplication.processEvents()

        setup.initialize()

        if setup.quit_requested:
            # The chosen data directory was missing and the user chose to quit
            # rather than start an empty library somewhere else.
            logger.info("Startup cancelled: the configured data directory is unavailable")
            if splash:
                splash.close()
            return 0

        if splash:
            splash.setProgress("Loading main window...")
            QApplication.processEvents()

        # Create main window (heavy import)
        from Modan2 import ModanMainWindow

        window = ModanMainWindow(setup.get_config(), config_path=setup.config_path)

        if splash:
            splash.setProgress("Ready!")
            QApplication.processEvents()
            # Close splash screen when main window is about to show
            splash.finish(window)

        window.show()

        # Apply command line configuration
        if args.debug:
            window.statusBar.showMessage("Debug mode enabled")

        logger.info("Application started successfully")

        # Self-test: the full startup path above already exercised the frozen
        # bundle (every heavy import + main-window construction). Now let the
        # event loop spin briefly so deferred work runs, then quit with 0. Close
        # any top-levels first so a stray modal's nested loop can't outlive quit().
        if args.self_test:
            from PyQt5.QtCore import QTimer

            def _self_test_exit():
                logger.info("Self-test: main window reached; exiting cleanly")
                for w in QApplication.topLevelWidgets():
                    w.close()
                app.quit()

            QTimer.singleShot(2000, _self_test_exit)

        # Run application
        exit_code = app.exec_()

        logger.info(f"Application exited with code: {exit_code}")
        return exit_code

    except Exception as e:
        logger.exception(f"Application failed to start: {e}")

        # Close the splash screen first. It is WindowStaysOnTopHint, so the
        # error dialog below opens *behind* it — leaving the user staring at a
        # splash frozen on whatever step failed, with no way to see why.
        if splash is not None:
            with contextlib.suppress(Exception):
                splash.close()

        # Try to show error dialog if Qt is available
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox

            if QApplication.instance():
                from MdUtils import get_log_directory

                QMessageBox.critical(
                    None,
                    "Modan2 Error",
                    f"Application failed to start:\n\n{e}\n\nDetails are in the log:\n{get_log_directory()}",
                )
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    sys.exit(main())
