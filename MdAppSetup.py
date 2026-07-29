"""
Application setup and initialization module for Modan2.
"""

import json
import logging
from pathlib import Path
from typing import Any

import MdModel
import MdUtils as mu


class ApplicationSetup:
    """Application initialization and configuration management."""

    def __init__(
        self,
        debug: bool = False,
        db_path: str | None = None,
        config_path: str | None = None,
        language: str | None = None,
        on_data_directory_problem=None,
    ):
        """Initialize application setup.

        Args:
            debug: Enable debug mode
            db_path: Custom database file path
            config_path: Custom configuration file path
            language: UI language (en/ko)
            on_data_directory_problem: Called as ``(problem, directory)`` when
                the data directory the user chose cannot be used, and must
                return ``"continue"``, ``"default"`` or ``"quit"``. Without it
                startup continues and creates the directory, which is the
                behaviour scripts and tests want; an interactive run passes one
                so the user is asked instead.
        """
        self.debug = debug
        # Only what was asked for on the command line. There is no default to
        # substitute here: the application's database lives where MdModel says
        # it does, and inventing a path sends it at an empty file.
        self.db_path = db_path
        self.config_path = config_path or self._get_default_config_path()
        self.language = language or "en"
        self.config: dict[str, Any] = {}
        self.on_data_directory_problem = on_data_directory_problem
        self.quit_requested = False

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def _get_default_config_path(self) -> str:
        """Get default configuration file path.

        The OS configuration location (see ``mu.DEFAULT_CONFIG_PATH``), not the
        data directory. The directory is created on first write.
        """
        return mu.DEFAULT_CONFIG_PATH

    def initialize(self):
        """Initialize application components."""
        self.logger.info("Initializing Modan2 application...")

        try:
            # 1. Load settings
            #
            # Before the database, not after. The data directory is a
            # preference, and the database file lives in it -- opening the
            # database first would have pinned it to the default location and
            # made the setting unreachable for everything except attachments.
            self._load_settings()
            self._apply_data_directory()
            if self.quit_requested:
                return

            # 2. Prepare database
            self._prepare_database()

            # 3. Load translations
            self._load_translations()

            # 4. Setup Qt style
            self._setup_qt_style()

            # 5. Load plugins (for future extension)
            self._load_plugins()

            self.logger.info("Application initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            raise

    def _apply_data_directory(self):
        """Put the chosen data directory into effect for the rest of startup.

        Everything downstream -- the database file, attachments, backups, logs
        -- derives from ``MdUtils.get_data_directory()``, so this single call is
        what makes the preference real.

        A directory the user chose is checked *before* anything is created in
        it. That order is the whole point: a moment later ``ensure_directories``
        would recreate it and the database would be opened inside, and the user
        would be looking at an empty library with no indication that their real
        one is on a drive that is merely unplugged. The default location gets no
        such check -- it is created on demand and its absence means nothing.
        """
        configured = (self.config.get("data") or {}).get("directory") or ""
        directory = mu.set_data_directory(configured)

        if configured:
            problem = mu.describe_data_directory_problem(directory)
            if problem:
                self.logger.warning(f"Configured data directory unusable: {problem}")
                if not self._resolve_data_directory_problem(problem, directory):
                    return
            else:
                self.logger.info(f"Using the configured data directory: {directory}")

        mu.ensure_directories()

    def _resolve_data_directory_problem(self, problem, directory):
        """Ask what to do about an unusable data directory. False to quit."""
        choice = self.on_data_directory_problem(problem, directory) if self.on_data_directory_problem else "continue"

        if choice == "quit":
            self.quit_requested = True
            return False
        if choice == "default":
            mu.set_data_directory("")
            self.config.setdefault("data", {})["directory"] = ""
            self._save_settings()
            self.logger.info("Reverted to the default data directory")
        else:
            self.logger.warning(f"Starting with an empty library at {directory}")
        return True

    def _prepare_database(self):
        """Initialize database and run migrations."""
        # --db names a file outright and wins over the data directory; the two
        # are independent by design. Otherwise follow the data directory, which
        # is the default location unless the user chose another.
        #
        # Redirect only when one of those applies. Overriding unconditionally
        # pointed every normal start at ~/.modan2/modan2.db -- not where the
        # database has ever lived -- so the app came up empty and migrated a
        # fresh file from scratch, while the real data sat untouched under
        # PaleoBytes/Modan2/.
        if self.db_path:
            MdModel.set_database_path(self.db_path)
        else:
            self.db_path = MdModel.set_database_path(mu.get_database_path())
        self.logger.debug(f"Preparing database at: {self.db_path}")

        # Runs the migrations too.
        MdModel.prepare_database()

    def _load_settings(self):
        """Load application settings from file."""
        self.logger.debug(f"Loading settings from: {self.config_path}")

        # One-time move of preferences from wherever they were last kept.
        # Only applies to the default location; --config is taken at face value.
        if self.config_path == mu.DEFAULT_CONFIG_PATH:
            mu.migrate_legacy_config()

        if Path(self.config_path).exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    self.config = json.load(f)
                self.logger.debug("Settings loaded successfully")
            except (OSError, json.JSONDecodeError) as e:
                # A corrupt config would otherwise be silently replaced with
                # defaults (every preference reset). Preserve it as .bak for
                # recovery/diagnosis and make the failure loud in the log.
                self.logger.error(f"Failed to load settings: {e}; using defaults and backing up the corrupt file")
                try:
                    backup = Path(self.config_path).with_suffix(".json.bak")
                    Path(self.config_path).replace(backup)
                    self.logger.error(f"Corrupt config backed up to: {backup}")
                except OSError as backup_err:
                    self.logger.warning(f"Could not back up corrupt config: {backup_err}")
                self.config = self._get_default_config()
        else:
            self.logger.debug("Settings file not found, using defaults")
            self.config = self._get_default_config()
            self._save_settings()

        # Override with command line language if specified
        if self.language:
            self.config["language"] = self.language

    def _get_default_config(self) -> dict[str, Any]:
        """Get default application configuration."""
        return {
            "language": self.language,
            "theme": "default",
            "toolbar_icon_size": 32,
            "auto_save": True,
            "auto_save_interval": 300,  # seconds
            "max_recent_files": 10,
            "recent_files": [],
            "window_geometry": None,
            "window_state": None,
            "splitter_state": None,
            # Viewer settings
            "landmark_size": 2,
            "landmark_color": "#ff0000",
            "wireframe_color": "#0000ff",
            "background_color": "#ffffff",
            "selection_color": "#00ff00",
            "hover_color": "#ffff00",
            # Display settings
            "show_object_names": True,
            "show_landmark_numbers": True,
            "show_wireframe": True,
            "anti_aliasing": True,
            # Analysis settings
            "default_analysis_type": "PCA",
            "pca_components": None,  # Auto
            "procrustes_scaling": True,
            "procrustes_reflection": True,
            # Export settings
            "default_export_format": "CSV",
            "include_metadata": True,
            "decimal_places": 6,
        }

    def _save_settings(self):
        """Save current settings to file."""
        try:
            # Ensure directory exists
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.logger.debug("Settings saved successfully")

        except OSError as e:
            self.logger.error(f"Failed to save settings: {e}")

    def _load_translations(self):
        """Load translation files."""
        if self.config.get("language") == "ko":
            try:
                from PyQt5.QtCore import QTranslator
                from PyQt5.QtWidgets import QApplication

                translator = QTranslator()
                translation_path = Path(__file__).parent / "translations" / "Modan2_ko.qm"

                if translation_path.exists():
                    if translator.load(str(translation_path)):
                        QApplication.instance().installTranslator(translator)
                        self.logger.debug("Korean translation loaded")
                    else:
                        self.logger.warning("Failed to load Korean translation")
                else:
                    self.logger.warning(f"Translation file not found: {translation_path}")

            except Exception as e:
                self.logger.warning(f"Failed to load translations: {e}")

    def _setup_qt_style(self):
        """Setup Qt application style."""
        try:
            from PyQt5.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                # Apply theme if available
                theme = self.config.get("theme", "default")

                if theme == "dark":
                    self._apply_dark_theme(app)
                elif theme == "light":
                    self._apply_light_theme(app)

                self.logger.debug(f"Applied theme: {theme}")

        except Exception as e:
            self.logger.warning(f"Failed to setup Qt style: {e}")

    def _apply_dark_theme(self, app):
        """Apply dark theme stylesheet."""
        dark_style = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QTreeWidget {
            background-color: #353535;
            color: #ffffff;
            selection-background-color: #4a90e2;
        }
        QTableWidget {
            background-color: #353535;
            color: #ffffff;
            gridline-color: #555555;
            selection-background-color: #4a90e2;
        }
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMenuBar::item:selected {
            background-color: #4a90e2;
        }
        QToolBar {
            background-color: #2b2b2b;
            border: 1px solid #555555;
        }
        """
        app.setStyleSheet(dark_style)

    def _apply_light_theme(self, app):
        """Apply light theme stylesheet."""
        # Use default Qt style for light theme
        app.setStyleSheet("")

    def _load_plugins(self):
        """Load application plugins (placeholder for future extension)."""
        plugins_dir = Path(__file__).parent / "plugins"

        if plugins_dir.exists():
            self.logger.debug(f"Scanning for plugins in: {plugins_dir}")

            for plugin_file in plugins_dir.glob("*.py"):
                if plugin_file.name.startswith("plugin_"):
                    try:
                        # Dynamic plugin loading logic would go here
                        self.logger.debug(f"Found plugin: {plugin_file.name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to load plugin {plugin_file.name}: {e}")

    def get_config(self) -> dict[str, Any]:
        """Get current application configuration."""
        return self.config.copy()

    def update_config(self, updates: dict[str, Any]):
        """Update configuration and save to file."""
        self.config.update(updates)
        self._save_settings()
        self.logger.debug(f"Configuration updated with: {list(updates.keys())}")

    def add_recent_file(self, file_path: str):
        """Add file to recent files list."""
        recent_files = self.config.get("recent_files", [])

        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)

        # Add to beginning
        recent_files.insert(0, file_path)

        # Keep only max number of files
        max_files = self.config.get("max_recent_files", 10)
        recent_files = recent_files[:max_files]

        # Update config
        self.config["recent_files"] = recent_files
        self._save_settings()

    def get_recent_files(self) -> list:
        """Get list of recent files."""
        recent_files = self.config.get("recent_files", [])

        # Filter out files that no longer exist
        existing_files = [file_path for file_path in recent_files if Path(file_path).exists()]

        # Update config if files were removed
        if len(existing_files) != len(recent_files):
            self.config["recent_files"] = existing_files
            self._save_settings()

        return existing_files

    def save_window_state(self, geometry: bytes, state: bytes, splitter_state: bytes | None = None):
        """Save window geometry and state."""
        self.config.update(
            {
                "window_geometry": geometry.hex() if geometry else None,
                "window_state": state.hex() if state else None,
                "splitter_state": splitter_state.hex() if splitter_state else None,
            }
        )
        self._save_settings()

    def restore_window_state(self) -> tuple:
        """Restore window geometry and state.

        Returns:
            tuple: (geometry_bytes, state_bytes, splitter_state_bytes)
        """
        geometry = None
        state = None
        splitter_state = None

        try:
            if self.config.get("window_geometry"):
                geometry = bytes.fromhex(self.config["window_geometry"])
            if self.config.get("window_state"):
                state = bytes.fromhex(self.config["window_state"])
            if self.config.get("splitter_state"):
                splitter_state = bytes.fromhex(self.config["splitter_state"])
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to restore window state: {e}")

        return geometry, state, splitter_state

    def cleanup(self):
        """Cleanup resources before application exit."""
        self.logger.info("Cleaning up application resources...")

        try:
            # Save any pending changes
            self._save_settings()

            # Close database connections
            MdModel.close_database()

            self.logger.info("Cleanup completed successfully")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def create_default_setup() -> ApplicationSetup:
    """Create ApplicationSetup with default configuration.

    Convenience function for testing and simple usage.
    """
    setup = ApplicationSetup()
    setup.initialize()
    return setup
