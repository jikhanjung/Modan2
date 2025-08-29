"""
Application setup and initialization module for Modan2.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import MdModel
import MdUtils as mu


class ApplicationSetup:
    """Application initialization and configuration management."""
    
    def __init__(self, debug: bool = False, db_path: Optional[str] = None,
                 config_path: Optional[str] = None, language: Optional[str] = None):
        """Initialize application setup.
        
        Args:
            debug: Enable debug mode
            db_path: Custom database file path
            config_path: Custom configuration file path
            language: UI language (en/ko)
        """
        self.debug = debug
        self.db_path = db_path or self._get_default_db_path()
        self.config_path = config_path or self._get_default_config_path()
        self.language = language or 'en'
        self.config: Dict[str, Any] = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _get_default_db_path(self) -> str:
        """Get default database file path."""
        app_dir = Path.home() / '.modan2'
        app_dir.mkdir(exist_ok=True)
        return str(app_dir / 'modan2.db')
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        app_dir = Path.home() / '.modan2'
        app_dir.mkdir(exist_ok=True)
        return str(app_dir / 'config.json')
    
    def initialize(self):
        """Initialize application components."""
        self.logger.info("Initializing Modan2 application...")
        
        try:
            # 1. Prepare database
            self._prepare_database()
            
            # 2. Load settings
            self._load_settings()
            
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
    
    def _prepare_database(self):
        """Initialize database and run migrations."""
        self.logger.debug(f"Preparing database at: {self.db_path}")
        
        # Set database path in model
        MdModel.DATABASE_PATH = self.db_path
        
        # Initialize database
        MdModel.prepare_database()
        
        # Run migrations if needed
        try:
            from migrate import run_migrations
            run_migrations()
            self.logger.debug("Database migrations completed")
        except ImportError:
            self.logger.warning("Migration module not found, skipping migrations")
        except Exception as e:
            self.logger.warning(f"Migration failed: {e}")
    
    def _load_settings(self):
        """Load application settings from file."""
        self.logger.debug(f"Loading settings from: {self.config_path}")
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.debug("Settings loaded successfully")
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load settings: {e}, using defaults")
                self.config = self._get_default_config()
        else:
            self.logger.debug("Settings file not found, using defaults")
            self.config = self._get_default_config()
            self._save_settings()
        
        # Override with command line language if specified
        if self.language:
            self.config['language'] = self.language
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default application configuration."""
        return {
            'language': self.language,
            'theme': 'default',
            'toolbar_icon_size': 32,
            'auto_save': True,
            'auto_save_interval': 300,  # seconds
            'max_recent_files': 10,
            'recent_files': [],
            'window_geometry': None,
            'window_state': None,
            'splitter_state': None,
            
            # Viewer settings
            'landmark_size': 2,
            'landmark_color': '#ff0000',
            'wireframe_color': '#0000ff',
            'background_color': '#ffffff',
            'selection_color': '#00ff00',
            'hover_color': '#ffff00',
            
            # Display settings
            'show_object_names': True,
            'show_landmark_numbers': True,
            'show_wireframe': True,
            'anti_aliasing': True,
            
            # Analysis settings
            'default_analysis_type': 'PCA',
            'pca_components': None,  # Auto
            'procrustes_scaling': True,
            'procrustes_reflection': True,
            
            # Export settings
            'default_export_format': 'CSV',
            'include_metadata': True,
            'decimal_places': 6,
        }
    
    def _save_settings(self):
        """Save current settings to file."""
        try:
            # Ensure directory exists
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("Settings saved successfully")
            
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to save settings: {e}")
    
    def _load_translations(self):
        """Load translation files."""
        if self.config.get('language') == 'ko':
            try:
                from PyQt5.QtCore import QTranslator, QLocale
                from PyQt5.QtWidgets import QApplication
                
                translator = QTranslator()
                translation_path = Path(__file__).parent / 'translations' / 'Modan2_ko.qm'
                
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
                theme = self.config.get('theme', 'default')
                
                if theme == 'dark':
                    self._apply_dark_theme(app)
                elif theme == 'light':
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
        plugins_dir = Path(__file__).parent / 'plugins'
        
        if plugins_dir.exists():
            self.logger.debug(f"Scanning for plugins in: {plugins_dir}")
            
            for plugin_file in plugins_dir.glob('*.py'):
                if plugin_file.name.startswith('plugin_'):
                    try:
                        # Dynamic plugin loading logic would go here
                        self.logger.debug(f"Found plugin: {plugin_file.name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to load plugin {plugin_file.name}: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current application configuration."""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration and save to file."""
        self.config.update(updates)
        self._save_settings()
        self.logger.debug(f"Configuration updated with: {list(updates.keys())}")
    
    def add_recent_file(self, file_path: str):
        """Add file to recent files list."""
        recent_files = self.config.get('recent_files', [])
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Keep only max number of files
        max_files = self.config.get('max_recent_files', 10)
        recent_files = recent_files[:max_files]
        
        # Update config
        self.config['recent_files'] = recent_files
        self._save_settings()
    
    def get_recent_files(self) -> list:
        """Get list of recent files."""
        recent_files = self.config.get('recent_files', [])
        
        # Filter out files that no longer exist
        existing_files = []
        for file_path in recent_files:
            if Path(file_path).exists():
                existing_files.append(file_path)
        
        # Update config if files were removed
        if len(existing_files) != len(recent_files):
            self.config['recent_files'] = existing_files
            self._save_settings()
        
        return existing_files
    
    def save_window_state(self, geometry: bytes, state: bytes, splitter_state: bytes = None):
        """Save window geometry and state."""
        self.config.update({
            'window_geometry': geometry.hex() if geometry else None,
            'window_state': state.hex() if state else None,
            'splitter_state': splitter_state.hex() if splitter_state else None,
        })
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
            if self.config.get('window_geometry'):
                geometry = bytes.fromhex(self.config['window_geometry'])
            if self.config.get('window_state'):
                state = bytes.fromhex(self.config['window_state'])
            if self.config.get('splitter_state'):
                splitter_state = bytes.fromhex(self.config['splitter_state'])
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