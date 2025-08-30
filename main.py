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
    
    parser.add_argument(
        '--version',
        action='version',
        version='Modan2 0.1.4'
    )
    
    return parser.parse_args()


def setup_logging(debug: bool = False):
    """Setup application logging."""
    level = logging.DEBUG if debug else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('modan2.log', encoding='utf-8')
        ]
    )
    
    # Reduce noise from Qt
    logging.getLogger('PyQt5').setLevel(logging.WARNING)


def main():
    """Main application entry point."""
    args = parse_arguments()
    
    # Setup logging first
    setup_logging(debug=args.debug)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Modan2 application...")
    logger.debug(f"Command line arguments: {vars(args)}")
    
    try:
        # Qt application setup
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon
        
        # High DPI support
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Modan2")
        app.setApplicationVersion("0.1.4")
        app.setOrganizationName("Modan2 Team")
        
        # Set application icon
        icon_path = Path(__file__).parent / "icons" / "Modan2.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Initialize application setup
        from MdAppSetup import ApplicationSetup
        setup = ApplicationSetup(
            debug=args.debug,
            db_path=args.db,
            config_path=args.config,
            language=args.lang
        )
        setup.initialize()
        
        # Create and show main window
        from Modan2 import ModanMainWindow
        window = ModanMainWindow(setup.get_config())
        
        # Show splash screen if not disabled
        if not args.no_splash:
            from MdSplashScreen import create_splash_screen
            
            # Try to use background image if available
            splash_bg_path = Path(__file__).parent / "icons" / "Modan2.png"
            background_path = str(splash_bg_path) if splash_bg_path.exists() else None
            
            splash = create_splash_screen(background_path)
            splash.setProgress("Initializing application...")
            splash.showWithTimer(3000)  # Show for 3 seconds
            
            # Simulate loading steps with progress updates
            import time
            time.sleep(0.5)
            splash.setProgress("Loading configuration...")
            time.sleep(0.5)
            splash.setProgress("Setting up database...")
            time.sleep(0.5)
            splash.setProgress("Ready!")
            time.sleep(0.5)
        
        window.show()
        
        # Apply command line configuration
        if args.debug:
            window.statusBar().showMessage("Debug mode enabled")
        
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