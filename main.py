#!/usr/bin/env python
"""
Modan2 - Morphometric Data Analysis Application
Main entry point for the application
"""
import sys
import os
import tempfile
from datetime import datetime

# Create emergency log file immediately in a fixed location
# Simplified emergency logging - try user desktop first, then temp
emergency_log_dir = None
emergency_log_path = None

# Try desktop first (most likely to work and easy to find)
desktop_paths = [
    os.path.join(os.path.expanduser('~'), 'Desktop'),
    os.path.join(os.path.expanduser('~'), 'デスクトップ'),  # Japanese Windows
    os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop') if os.name == 'nt' else None,
]

for desktop in desktop_paths:
    if desktop and os.path.exists(desktop):
        try:
            emergency_log_path = os.path.join(desktop, f'modan2_startup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            # Test write immediately
            with open(emergency_log_path, 'w') as f:
                f.write(f"Modan2 Emergency Log - {datetime.now()}\n")
                f.write(f"Python: {sys.version}\n")
                f.write(f"Executable: {sys.executable}\n")
                f.write("=" * 50 + "\n")
                f.flush()  # Force write to disk
            emergency_log_dir = desktop
            break
        except:
            continue

# Fallback to temp directory
if not emergency_log_path:
    try:
        emergency_log_dir = tempfile.gettempdir()
        emergency_log_path = os.path.join(emergency_log_dir, f'modan2_startup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        with open(emergency_log_path, 'w') as f:
            f.write(f"Modan2 Emergency Log - {datetime.now()}\n")
            f.flush()
    except:
        # Last resort: create in current directory
        emergency_log_path = f'modan2_startup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        try:
            with open(emergency_log_path, 'w') as f:
                f.write(f"Modan2 Emergency Log - {datetime.now()}\n")
                f.flush()
        except:
            emergency_log_path = None

def emergency_log(msg):
    """Write to emergency log file and stdout"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    print(f"[LOG PATH: {emergency_log_path}]", file=sys.stderr)  # Also print path to stderr
    sys.stdout.flush()  # Force console output
    if emergency_log_path:
        try:
            with open(emergency_log_path, 'a') as f:
                f.write(log_msg + '\n')
                f.flush()  # Force write to disk immediately
                os.fsync(f.fileno())  # Force OS to write to disk
        except Exception as e:
            print(f"Failed to write to log: {e}", file=sys.stderr)

emergency_log(f"Modan2 startup initiated - Emergency log: {emergency_log_path}")
emergency_log(f"Python version: {sys.version}")
emergency_log(f"Executable: {sys.executable}")

try:
    emergency_log("Importing argparse...")
    import argparse
    emergency_log("Imported argparse successfully")
except Exception as e:
    emergency_log(f"Failed to import argparse: {e}")
    raise

try:
    emergency_log("Importing logging...")
    import logging
    emergency_log("Imported logging successfully")
except Exception as e:
    emergency_log(f"Failed to import logging: {e}")
    raise

try:
    emergency_log("Importing pathlib.Path...")
    from pathlib import Path
    emergency_log("Imported pathlib.Path successfully")
except Exception as e:
    emergency_log(f"Failed to import pathlib.Path: {e}")
    raise

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
        # Qt application setup
        emergency_log("Importing PyQt5.QtWidgets.QApplication...")
        from PyQt5.QtWidgets import QApplication
        emergency_log("Imported PyQt5.QtWidgets.QApplication successfully")
        
        emergency_log("Importing PyQt5.QtCore.Qt...")
        from PyQt5.QtCore import Qt
        emergency_log("Imported PyQt5.QtCore.Qt successfully")
        
        emergency_log("Importing PyQt5.QtGui.QIcon...")
        from PyQt5.QtGui import QIcon
        emergency_log("Imported PyQt5.QtGui.QIcon successfully")
        
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
        emergency_log("Importing MdAppSetup.ApplicationSetup...")
        from MdAppSetup import ApplicationSetup
        emergency_log("Imported MdAppSetup.ApplicationSetup successfully")
        
        emergency_log("Creating ApplicationSetup instance...")
        setup = ApplicationSetup(
            debug=args.debug,
            db_path=args.db,
            config_path=args.config,
            language=args.lang
        )
        emergency_log("ApplicationSetup instance created")
        
        emergency_log("Initializing ApplicationSetup...")
        setup.initialize()
        emergency_log("ApplicationSetup initialized")
        
        # Create and show main window
        emergency_log("Importing Modan2.ModanMainWindow...")
        from Modan2 import ModanMainWindow
        emergency_log("Imported Modan2.ModanMainWindow successfully")
        
        emergency_log("Creating ModanMainWindow instance...")
        window = ModanMainWindow(setup.get_config())
        emergency_log("ModanMainWindow instance created")
        
        # Show splash screen if not disabled
        if not args.no_splash:
            from MdSplashScreen import create_splash_screen
            from PyQt5.QtWidgets import QApplication
            
            # Try to use background image if available
            splash_bg_path = Path(__file__).parent / "icons" / "Modan2.png"
            background_path = str(splash_bg_path) if splash_bg_path.exists() else None
            
            splash = create_splash_screen(background_path)
            try:
                splash.setProgress("Initializing application...")
                splash.showWithTimer(3000)  # Show for 3 seconds
                
                # Quick progress updates without blocking
                splash.setProgress("Loading configuration...")
                QApplication.processEvents()
                splash.setProgress("Setting up database...")  
                QApplication.processEvents()
                splash.setProgress("Ready!")
                QApplication.processEvents()
            except Exception as e:
                logger.warning(f"Splash screen update failed: {e}")
                # Continue without splash screen updates
        
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
