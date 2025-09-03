#!/usr/bin/env python
"""
Test script for the Modan2 splash screen.
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from MdSplashScreen import create_splash_screen

def test_splash_screen():
    """Test the splash screen display."""
    app = QApplication(sys.argv)
    
    # Test with background image if available
    icon_path = Path(__file__).parent / "icons" / "Modan2.png"
    background_path = str(icon_path) if icon_path.exists() else None
    
    # Create splash screen
    splash = create_splash_screen(background_path)
    
    # Show progress messages
    splash.setProgress("Initializing application...")
    splash.show()
    app.processEvents()
    
    # Update progress messages over time
    def update_progress():
        messages = [
            "Loading configuration...",
            "Setting up database...", 
            "Preparing UI components...",
            "Loading plugins...",
            "Ready!"
        ]
        
        current_msg = getattr(update_progress, 'index', 0)
        if current_msg < len(messages):
            splash.setProgress(messages[current_msg])
            app.processEvents()
            update_progress.index = current_msg + 1
            
            # Schedule next update
            if current_msg < len(messages) - 1:
                QTimer.singleShot(800, update_progress)
            else:
                # Close after showing "Ready!" for a bit
                QTimer.singleShot(1000, lambda: [splash.close(), app.quit()])
        
    # Start progress updates
    QTimer.singleShot(500, update_progress)
    
    print("Showing splash screen with styled text...")
    print("Features:")
    print("- 'Modan2' title with decorative font")
    print("- 'Morphometrics made easy' subtitle")
    print("- Gradient background")
    print("- Progress messages")
    print("- Version and copyright info")
    
    app.exec()

if __name__ == "__main__":
    test_splash_screen()