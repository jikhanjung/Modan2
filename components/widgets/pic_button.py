"""Picture Button widget with hover and pressed states."""

import logging

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QAbstractButton

logger = logging.getLogger(__name__)


class PicButton(QAbstractButton):
    """Custom button widget that displays pixmap images with state-based visuals.

    Supports different pixmaps for:
    - Normal state
    - Hover state
    - Pressed state
    - Disabled state (auto-generated grayscale if not provided)

    Features:
    - Automatic grayscale generation for disabled state
    - Hover detection and visual feedback
    - Press/release visual feedback
    """

    def __init__(self, pixmap, pixmap_hover, pixmap_pressed, pixmap_disabled=None, parent=None):
        """Initialize picture button with state-specific pixmaps.

        Args:
            pixmap: Normal state pixmap
            pixmap_hover: Hover state pixmap
            pixmap_pressed: Pressed state pixmap
            pixmap_disabled: Disabled state pixmap (optional, auto-generated if None)
            parent: Parent widget
        """
        super().__init__(parent)

        self.pixmap = pixmap
        self.pixmap_hover = pixmap_hover
        self.pixmap_pressed = pixmap_pressed

        # Auto-generate grayscale disabled pixmap if not provided
        if pixmap_disabled is None:
            result = pixmap_hover.copy()
            image = QPixmap.toImage(result)
            grayscale = image.convertToFormat(QImage.Format_Grayscale8)
            pixmap_disabled = QPixmap.fromImage(grayscale)

        self.pixmap_disabled = pixmap_disabled

        # Connect signals for visual updates
        self.pressed.connect(self.update)
        self.released.connect(self.update)

    def paintEvent(self, event):
        """Paint the button with appropriate pixmap based on state.

        Args:
            event: QPaintEvent
        """
        # Select pixmap based on button state
        pix = self.pixmap_hover if self.underMouse() else self.pixmap

        if self.isDown():
            pix = self.pixmap_pressed

        if not self.isEnabled() and self.pixmap_disabled is not None:
            pix = self.pixmap_disabled

        # Draw pixmap
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), pix)

    def enterEvent(self, event):
        """Handle mouse enter event.

        Args:
            event: QEnterEvent
        """
        self.update()

    def leaveEvent(self, event):
        """Handle mouse leave event.

        Args:
            event: QLeaveEvent
        """
        self.update()

    def sizeHint(self):
        """Provide size hint for layout management.

        Returns:
            QSize: Suggested size (200x200)
        """
        return QSize(200, 200)
