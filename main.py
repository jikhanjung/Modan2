#!/usr/bin/env python
"""
Modan2 - Morphometric Data Analysis Application
Main entry point for the application
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# Desktop OpenGL 강제 (ANGLE 방지) - QApplication 생성 전 필수
os.environ["QT_OPENGL"] = "desktop"

def parse_arguments():
    """Parse command line arguments."""
    from MdUtils import DEFAULT_DB_DIRECTORY
    import os
    
    default_db_path = os.path.join(DEFAULT_DB_DIRECTORY, 'modan2.db')
    
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
        default=default_db_path,
        help=f'Database file path (default: {default_db_path})'
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
    from MdUtils import DEFAULT_LOG_DIRECTORY
    import os
    
    level = logging.DEBUG if debug else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Ensure log directory exists (already handled in MdUtils.py but ensure it's imported)
    log_file_path = os.path.join(DEFAULT_LOG_DIRECTORY, 'modan2.log')
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file_path, encoding='utf-8')
        ]
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
        # Qt application setup
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon, QSurfaceFormat
        
        # High DPI support
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # OpenGL Compatibility 프로파일 설정 (QApplication 생성 전)
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)  # 안정성을 위해 2.1 사용
        fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
        QSurfaceFormat.setDefaultFormat(fmt)
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Modan2")
        app.setApplicationVersion("0.1.4")
        app.setOrganizationName("Modan2 Team")
        
        # Set application icon
        icon_path = Path(__file__).parent / "icons" / "Modan2.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Show splash screen immediately if not disabled
        splash = None
        if not args.no_splash:
            from MdSplashScreen import create_splash_screen
            from PyQt5.QtWidgets import QApplication
            
            # Try to use background image if available
            splash_bg_path = Path(__file__).parent / "icons" / "Modan2.png"
            background_path = str(splash_bg_path) if splash_bg_path.exists() else None
            
            splash = create_splash_screen(background_path)
            splash.setProgress("Starting Modan2...")
            splash.show()
            app.processEvents()
        
        # Initialize application setup with progress updates
        from MdAppSetup import ApplicationSetup
        setup = ApplicationSetup(
            debug=args.debug,
            db_path=args.db,
            config_path=args.config,
            language=args.lang
        )
        
        if splash:
            splash.setProgress("Loading configuration...")
            app.processEvents()
        
        setup.initialize()
        
        if splash:
            splash.setProgress("Setting up database...")
            app.processEvents()
        
        # Create main window
        from Modan2 import ModanMainWindow
        window = ModanMainWindow(setup.get_config())
        
        if splash:
            splash.setProgress("Initializing interface...")
            app.processEvents()
        
        # Show main window
        window.show()
        
        if splash:
            splash.setProgress("Ready!")
            app.processEvents()
            # Close splash after a short delay
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, splash.close)
        
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