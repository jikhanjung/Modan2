#!/usr/bin/env python
"""
Modan2 - Morphometric Data Analysis Application
Main entry point for the application
"""
import sys
import argparse
import logging
from pathlib import Path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Modan2 - Morphometric Data Analysis Application',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Enable debug mode with verbose logging'
    )
    
    parser.add_argument(
        '--db', 
        type=str, 
        help='Database file path (default: ~/.modan2/modan2.db)'
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        help='Configuration file path (default: ~/.modan2/config.json)'
    )
    
    parser.add_argument(
        '--lang', 
        type=str, 
        choices=['en', 'ko'], 
        default='en',
        help='UI language'
    )
    
    parser.add_argument(
        '--no-splash',
        action='store_true',
        help='Skip splash screen on startup'
    )
    
    # Import version
    try:
        from version import __version__
        version_string = f'Modan2 {__version__}'
    except ImportError:
        version_string = 'Modan2 0.1.5-alpha.1'
    
    parser.add_argument(
        '--version',
        action='version',
        version=version_string
    )
    
    return parser.parse_args()


def setup_logging(debug: bool = False):
    """Setup application logging with fallback options."""
    level = logging.DEBUG if debug else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Try to get proper log directory, with fallbacks
    log_file_path = None
    try:
        from MdUtils import DEFAULT_LOG_DIRECTORY, ensure_directories
        ensure_directories()
        log_file_path = Path(DEFAULT_LOG_DIRECTORY) / 'modan2.log'
    except Exception as e:
        print(f"Warning: Could not access configured log directory: {e}")
        # Fallback to local logs directory
        try:
            log_dir = Path('logs')
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file_path = log_dir / 'modan2.log'
        except Exception:
            # Final fallback to temp directory
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            log_file_path = temp_dir / 'modan2.log'
            print(f"Using fallback log file: {log_file_path}")
    
    # Setup handlers
    try:
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        handlers = [logging.StreamHandler(sys.stdout), file_handler]
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")
        # Fallback to console-only logging if file handler cannot be created
        handlers = [logging.StreamHandler(sys.stdout)]

    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=handlers
    )
    
    # Reduce noise from Qt and matplotlib
    logging.getLogger('PyQt5').setLevel(logging.WARNING)
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)


def main():
    """Main application entry point."""
    args = parse_arguments()
    
    # Setup logging first
    setup_logging(debug=args.debug)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Modan2 application...")
    logger.debug(f"Command line arguments: {vars(args)}")
    
    try:
        # Qt application setup - minimal imports for splash screen
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon
        
        # High DPI support
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Import version for app metadata
        try:
            from version import __version__
            app_version = __version__
        except ImportError:
            app_version = "0.1.5-alpha.1"
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Modan2")
        app.setApplicationVersion(app_version)
        app.setOrganizationName("Modan2 Team")
        
        # Set application icon
        icon_path = Path(__file__).parent / "icons" / "Modan2.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Show splash screen FIRST, before any heavy imports
        splash = None
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
            language=args.lang
        )
        
        if splash:
            splash.setProgress("Initializing configuration...")
            QApplication.processEvents()
        
        setup.initialize()
        
        if splash:
            splash.setProgress("Loading main window...")
            QApplication.processEvents()
        
        # Create main window (heavy import)
        from Modan2 import ModanMainWindow
        window = ModanMainWindow(setup.get_config())
        
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
        
        # Run application
        exit_code = app.exec_()
        
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        
        # Try to show error dialog if Qt is available
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            if QApplication.instance():
                QMessageBox.critical(
                    None, 
                    "Modan2 Error", 
                    f"Application failed to start:\n\n{str(e)}"
                )
        except:
            pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
