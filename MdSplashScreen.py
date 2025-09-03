"""
Custom splash screen for Modan2 application with styled text overlay.
"""
from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPen, QLinearGradient
import MdUtils as mu


class ModanSplashScreen(QSplashScreen):
    """Custom splash screen with application branding."""
    
    def __init__(self, pixmap=None, flags=Qt.WindowType.WindowStaysOnTopHint):
        """Initialize splash screen with custom text rendering.
        
        Args:
            pixmap: Background image (optional)
            flags: Window flags
        """
        # Create pixmap if not provided
        if pixmap is None:
            pixmap = QPixmap(600, 400)
            pixmap.fill(QColor("#2c3e50"))  # Dark blue-gray background
        
        super().__init__(pixmap, flags)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        # Version and copyright info from MdUtils (consistent with main app)
        version_text = f"v{mu.PROGRAM_VERSION} (Build {mu.PROGRAM_BUILD_NUMBER})"
        self.version = version_text
        self.copyright = mu.PROGRAM_COPYRIGHT
        
    def drawContents(self, painter):
        """Draw custom contents on splash screen.
        
        Args:
            painter: QPainter object for drawing
        """
        super().drawContents(painter)
        
        # Enable antialiasing for smooth text
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # Get dimensions
        width = self.pixmap().width()
        height = self.pixmap().height()
        
        # Create gradient for title text
        gradient = QLinearGradient(0, height * 0.3, 0, height * 0.5)
        gradient.setColorAt(0, QColor("#3498db"))  # Light blue
        gradient.setColorAt(1, QColor("#2980b9"))  # Darker blue
        
        # Draw title "Modan2" with decorative font
        title_font = QFont()
        title_font.setFamily("Segoe UI")  # Use a nice font
        title_font.setPointSize(48)
        title_font.setBold(True)
        title_font.setStrikeOut(False)  # Explicitly disable strikethrough
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        painter.setFont(title_font)
        
        # Draw shadow for title
        shadow_pen = QPen(QColor(0, 0, 0, 100))
        painter.setPen(shadow_pen)
        title_rect = QRect(0, int(height * 0.3) + 3, width, 70)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, "Modan2")
        
        # Draw title with gradient
        painter.setPen(QPen(QColor("#3498db")))
        title_rect = QRect(0, int(height * 0.3), width, 70)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, "Modan2")
        
        # Draw subtitle "Morphometrics made easy" with stylish font
        subtitle_font = QFont()
        subtitle_font.setFamily("Segoe UI Light")
        subtitle_font.setPointSize(20)
        subtitle_font.setItalic(True)
        subtitle_font.setStrikeOut(False)  # Explicitly disable strikethrough
        subtitle_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(subtitle_font)
        
        # Draw dark border/outline for subtitle (multiple layers for thickness)
        dark_border_pen = QPen(QColor(0, 0, 0, 200), 2)  # Very dark with thickness
        painter.setPen(dark_border_pen)
        subtitle_rect = QRect(0, int(height * 0.45), width, 40)
        
        # Draw outline in multiple directions for thick border effect
        offsets = [(-2, -1), (-1, -2), (0, -2), (1, -2), (2, -1), 
                  (2, 0), (2, 1), (1, 2), (0, 2), (-1, 2), (-2, 1), (-2, 0)]
        
        for dx, dy in offsets:
            offset_rect = QRect(dx, int(height * 0.45) + dy, width, 40)
            painter.drawText(offset_rect, Qt.AlignmentFlag.AlignCenter, "Morphometrics made easy")
        
        # Draw main subtitle text on top
        painter.setPen(QPen(QColor("#ecf0f1")))  # Light gray
        subtitle_rect = QRect(0, int(height * 0.45), width, 40)
        painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, "Morphometrics made easy")
        
        # Draw version info at bottom
        version_font = QFont()
        version_font.setFamily("Segoe UI")
        version_font.setPointSize(10)
        version_font.setStrikeOut(False)  # Explicitly disable strikethrough
        painter.setFont(version_font)
        painter.setPen(QPen(QColor("#95a5a6")))  # Gray
        
        version_rect = QRect(0, height - 60, width, 20)
        painter.drawText(version_rect, Qt.AlignmentFlag.AlignCenter, self.version)
        
        # Draw copyright
        copyright_rect = QRect(0, height - 40, width, 20)
        painter.drawText(copyright_rect, Qt.AlignmentFlag.AlignCenter, self.copyright)
    
    def showWithTimer(self, duration_ms=3000):
        """Show splash screen for specified duration.
        
        Args:
            duration_ms: Duration in milliseconds
        """
        self.show()
        QApplication.processEvents()
        
        # Auto close after duration
        QTimer.singleShot(duration_ms, self.close)
    
    def setProgress(self, message, process_events=True):
        """Update progress message.
        
        Args:
            message: Progress message to display
            process_events: Whether to process Qt events (default: True)
        """
        self.showMessage(
            message, 
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, 
            QColor("#bdc3c7")
        )
        if process_events:
            QApplication.processEvents()


def create_splash_screen(image_path=None):
    """Create and return a configured splash screen.
    
    Args:
        image_path: Optional path to background image
        
    Returns:
        ModanSplashScreen instance
    """
    if image_path:
        from pathlib import Path
        path = Path(image_path)
        if path.exists():
            pixmap = QPixmap(str(path))
            # Scale to reasonable size if needed
            if pixmap.width() > 800 or pixmap.height() > 600:
                pixmap = pixmap.scaled(
                    600, 400, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
        else:
            pixmap = None
    else:
        pixmap = None
    
    # Create custom pixmap with gradient background if no image
    if pixmap is None:
        pixmap = QPixmap(600, 400)
        painter = QPainter(pixmap)
        
        # Create gradient background
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0, QColor("#34495e"))  # Dark gray-blue
        gradient.setColorAt(0.5, QColor("#2c3e50"))  # Darker
        gradient.setColorAt(1, QColor("#1a252f"))  # Very dark
        
        painter.fillRect(pixmap.rect(), gradient)
        
        # Add subtle pattern overlay
        painter.setPen(QPen(QColor(255, 255, 255, 5)))
        for i in range(0, 600, 20):
            painter.drawLine(i, 0, i, 400)
        for i in range(0, 400, 20):
            painter.drawLine(0, i, 600, i)
            
        painter.end()
    
    return ModanSplashScreen(pixmap)