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

# OpenGL backend configuration - allow fallbacks in deployment builds
if getattr(sys, 'frozen', False):  # Only in PyInstaller builds
    # Enable Qt plugin debugging in deployed builds
    os.environ.setdefault("QT_DEBUG_PLUGINS", "0")  # Set to "1" for debugging
    os.environ.setdefault("QT_FATAL_WARNINGS", "0")  # Set to "1" for debugging
    
    # Allow OpenGL fallback in deployment
    if "QT_OPENGL" not in os.environ:
        # Try desktop OpenGL first, it works better with QOpenGLWidget
        # Users can override with QT_OPENGL environment variable if needed
        os.environ["QT_OPENGL"] = "desktop"
else:
    # Development: don't force any backend, let Qt choose
    # This allows testing different backends with environment variables
    pass
    # Ensure Qt finds plugins in bundled app
    if hasattr(sys, '_MEIPASS'):
        plugin_path = os.path.join(sys._MEIPASS, "PyQt5", "Qt", "plugins")
        if os.path.exists(plugin_path):
            os.environ["QT_PLUGIN_PATH"] = plugin_path

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
    """Setup application logging with fallback options."""
    level = logging.DEBUG if debug else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Try to get proper log directory, with fallbacks
    log_file_path = None
    try:
        from MdUtils import DEFAULT_LOG_DIRECTORY, ensure_directories
        ensure_directories()  # Make sure directories exist
        log_file_path = os.path.join(DEFAULT_LOG_DIRECTORY, 'modan2.log')
    except Exception as e:
        print(f"Warning: Could not access configured log directory: {e}")
        # Fallback to temp directory
        import tempfile
        temp_dir = tempfile.gettempdir()
        log_file_path = os.path.join(temp_dir, 'modan2.log')
        print(f"Using fallback log file: {log_file_path}")
    
    # Setup logging handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Try to add file handler
    if log_file_path:
        try:
            handlers.append(logging.FileHandler(log_file_path, encoding='utf-8'))
        except Exception as e:
            print(f"Warning: Could not create log file {log_file_path}: {e}")
            # Continue with just console logging
    
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
    # Very early error handling - even before logging setup
    try:
        # Parse arguments first
        args = parse_arguments()
        
        # Setup logging with error handling
        setup_logging(debug=args.debug)
        logger = logging.getLogger(__name__)
        
        logger.info("Starting Modan2 application...")
        logger.debug(f"Command line arguments: {vars(args)}")
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Working directory: {os.getcwd()}")
        
    except Exception as e:
        # If even basic setup fails, print to console and try to continue
        print(f"Early initialization error: {e}")
        import traceback
        traceback.print_exc()
        # Try to continue with basic logging
        try:
            import tempfile
            log_path = os.path.join(tempfile.gettempdir(), 'modan2_emergency.log')
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.FileHandler(log_path)
                ]
            )
            logger = logging.getLogger(__name__)
            logger.error(f"Emergency logging activated due to setup failure: {e}")
        except:
            print("Could not even setup emergency logging")
            return 1
    
    try:
        # Qt application setup
        logger.info("Importing PyQt5 modules...")
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QIcon, QSurfaceFormat
            logger.info("PyQt5 modules imported successfully")
        except Exception as e:
            logger.error(f"Failed to import PyQt5 modules: {e}")
            raise
        
        # High DPI support
        logger.info("Setting up High DPI support...")
        try:
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            logger.info("High DPI support configured")
        except Exception as e:
            logger.error(f"Failed to setup High DPI support: {e}")
            raise
        
        # OpenGL Compatibility 프로파일 설정 (QApplication 생성 전)
        # This must be done before QApplication creation for QOpenGLWidget
        logger.info("Configuring OpenGL surface format for QOpenGLWidget...")
        try:
            fmt = QSurfaceFormat()
            fmt.setVersion(2, 1)  # 안정성을 위해 2.1 사용 (GLU/immediate mode compatible)
            fmt.setProfile(QSurfaceFormat.CompatibilityProfile)  # For GLU and fixed-function
            fmt.setDepthBufferSize(24)  # Proper depth buffer
            fmt.setStencilBufferSize(8)  # Stencil buffer for advanced rendering
            fmt.setSamples(4)  # MSAA for smoother edges
            fmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)  # Double buffering
            QSurfaceFormat.setDefaultFormat(fmt)
            logger.info("OpenGL surface format configured (2.1 Compatibility with enhanced buffers)")
        except Exception as e:
            logger.error(f"Failed to configure OpenGL surface format: {e}")
            raise
        
        # Create Qt application
        logger.info("Creating QApplication...")
        try:
            app = QApplication(sys.argv)
            logger.info("QApplication created successfully")
        except Exception as e:
            logger.error(f"Failed to create QApplication: {e}")
            raise
        logger.info("Setting application metadata...")
        app.setApplicationName("Modan2")
        app.setApplicationVersion("0.1.4")
        app.setOrganizationName("Modan2 Team")
        logger.info("Application metadata configured")
        
        # Set application icon
        logger.info("Setting application icon...")
        try:
            icon_path = Path(__file__).parent / "icons" / "Modan2.png"
            if icon_path.exists():
                app.setWindowIcon(QIcon(str(icon_path)))
                logger.info(f"Application icon set: {icon_path}")
            else:
                logger.warning(f"Application icon not found: {icon_path}")
        except Exception as e:
            logger.warning(f"Failed to set application icon: {e}")
        
        # Show splash screen immediately if not disabled
        splash = None
        if not args.no_splash:
            logger.info("Creating splash screen...")
            try:
                from MdSplashScreen import create_splash_screen
                
                # Try to use background image if available
                splash_bg_path = Path(__file__).parent / "icons" / "Modan2.png"
                background_path = str(splash_bg_path) if splash_bg_path.exists() else None
                logger.debug(f"Splash background path: {background_path}")
                
                splash = create_splash_screen(background_path)
                splash.setProgress("Starting Modan2...")
                splash.show()
                app.processEvents()
                logger.info("Splash screen displayed")
            except Exception as e:
                logger.error(f"Failed to create splash screen: {e}")
                # Continue without splash screen
        
        # Initialize application setup with progress updates
        logger.info("Initializing ApplicationSetup...")
        logger.debug(f"Database path: {args.db}")
        logger.debug(f"Config path: {args.config}")
        logger.debug(f"Language: {args.lang}")
        
        try:
            from MdAppSetup import ApplicationSetup
            setup = ApplicationSetup(
                debug=args.debug,
                db_path=args.db,
                config_path=args.config,
                language=args.lang
            )
            logger.info("ApplicationSetup created successfully")
        except Exception as e:
            logger.error(f"Failed to create ApplicationSetup: {e}")
            raise
        
        if splash:
            splash.setProgress("Loading configuration...", process_events=False)
        
        setup.initialize()
        
        if splash:
            splash.setProgress("Setting up database...", process_events=False)
        
        # Create main window
        logger.info("Creating main window...")
        try:
            from Modan2 import ModanMainWindow
            logger.info("ModanMainWindow class imported successfully")
            window = ModanMainWindow(setup.get_config())
            logger.info("Main window created successfully")
            
            # Check window state immediately after creation
            logger.info(f"Window visibility: {window.isVisible()}")
            logger.info(f"Window size: {window.size()}")
            logger.info(f"Window position: {window.pos()}")
            
        except Exception as e:
            logger.error(f"Failed to create main window: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        if splash:
            logger.info("Setting splash screen to 'Initializing interface...'")
            try:
                # Reduce event processing during critical window initialization
                splash.setProgress("Initializing interface...", process_events=False)
                logger.info("Splash screen updated (no event processing)")
            except Exception as e:
                logger.error(f"Failed to update splash screen: {e}")
                # Continue without splash screen updates
        
        # Show main window
        logger.info("About to show main window...")
        try:
            # Pre-show checks
            logger.info("Checking window validity before show()...")
            if window is None:
                logger.error("Window is None!")
                raise RuntimeError("Window object is None")
            
            logger.info(f"Window object type: {type(window)}")
            logger.info(f"Window is widget: {window.isWidgetType()}")
            
            logger.info("Calling window.show()...")
            window.show()
            logger.info("window.show() completed")
            
            # Post-show checks
            logger.info(f"Window visible after show(): {window.isVisible()}")
            
            logger.info("Processing Qt events after window.show() (single batch)...")
            app.processEvents()  # Single event processing after window is shown
            logger.info("Qt events processed (single batch)")
            
            logger.info("Main window shown successfully")
        except Exception as e:
            logger.error(f"Failed to show main window: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        if splash:
            logger.info("Updating splash screen to Ready...")
            try:
                splash.setProgress("Ready!")
                app.processEvents()
                logger.info("Splash screen updated to Ready")
                
                logger.info("Scheduling splash screen close...")
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1000, splash.close)
                logger.info("Splash screen close scheduled")
            except Exception as e:
                logger.error(f"Error updating splash screen: {e}")
                # Continue even if splash screen fails
        
        # Apply command line configuration
        logger.info("Applying command line configuration...")
        try:
            if args.debug:
                window.statusBar.showMessage("Debug mode enabled")
            logger.info("Command line configuration applied")
        except Exception as e:
            logger.error(f"Error applying command line configuration: {e}")
        
        logger.info("Application startup completed successfully")
        logger.info("Starting Qt event loop...")
        
        # Run application
        try:
            exit_code = app.exec_()
            logger.info(f"Qt event loop exited with code: {exit_code}")
        except Exception as e:
            logger.error(f"Qt event loop crashed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return 1
        
        logger.info(f"Application exited normally with code: {exit_code}")
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