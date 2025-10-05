"""Dataset Operations Viewer widget for visualizing landmark data."""

import logging

from PyQt5.QtGui import QBrush, QFont, QPainter, QPen
from PyQt5.QtWidgets import QLabel

import MdUtils as mu

logger = logging.getLogger(__name__)

# Color constants for visualization
COLOR = {
    "BACKGROUND": "#FFFFFF",
    "WIREFRAME": "#FFFF00",
    "NORMAL_SHAPE": "#0000FF",
    "SELECTED_SHAPE": "#FF0000",
    "AVERAGE_SHAPE": "#00FF00",
}


class DatasetOpsViewer(QLabel):
    """Custom QLabel widget for visualizing dataset operations and landmark data.

    This widget displays 2D landmark data with various visualization options:
    - Individual object landmarks
    - Average shape
    - Wireframe connections
    - Baseline
    - Landmark indices

    Features:
    - Automatic scaling and panning to fit data
    - Selection highlighting
    - Customizable display options
    """

    def __init__(self, widget):
        """Initialize dataset operations viewer.

        Args:
            widget: Parent widget
        """
        super().__init__(widget)

        # Dataset operations
        self.ds_ops = None

        # View transformation
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Display options
        self.show_index = True
        self.show_wireframe = False
        self.show_baseline = False
        self.show_average = True

    def set_ds_ops(self, ds_ops):
        """Set dataset operations object and recalculate view.

        Args:
            ds_ops: Dataset operations object containing landmark data
        """
        self.ds_ops = ds_ops
        self.calculate_scale_and_pan()

    def calculate_scale_and_pan(self):
        """Calculate optimal scale and pan values to fit all landmarks in view."""
        min_x = 100000000
        max_x = -100000000
        min_y = 100000000
        max_y = -100000000

        # Get min and max x,y from all landmarks
        for obj in self.ds_ops.object_list:
            for _idx, landmark in enumerate(obj.landmark_list):
                if landmark[0] < min_x:
                    min_x = landmark[0]
                if landmark[0] > max_x:
                    max_x = landmark[0]
                if landmark[1] < min_y:
                    min_y = landmark[1]
                if landmark[1] > max_y:
                    max_y = landmark[1]

        # Calculate scale to fit data with 1.5x padding
        width = max_x - min_x
        height = max_y - min_y
        w_scale = (self.width() * 1.0) / (width * 1.5)
        h_scale = (self.height() * 1.0) / (height * 1.5)
        self.scale = min(w_scale, h_scale)

        # Calculate pan to center data
        self.pan_x = -min_x * self.scale + (self.width() - width * self.scale) / 2.0
        self.pan_y = -min_y * self.scale + (self.height() - height * self.scale) / 2.0

        self.repaint()

    def resizeEvent(self, ev):
        """Handle widget resize event.

        Args:
            ev: QResizeEvent

        Returns:
            Result of parent resizeEvent
        """
        self.calculate_scale_and_pan()
        self.repaint()
        return super().resizeEvent(ev)

    def paintEvent(self, event):
        """Paint the landmark visualization.

        Args:
            event: QPaintEvent
        """
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(mu.as_qt_color(COLOR["BACKGROUND"])))

        if self.ds_ops is None:
            return

        # Draw wireframe
        if self.show_wireframe:
            self._draw_wireframe(painter)

        # Draw individual object landmarks
        self._draw_object_landmarks(painter)

        # Draw average shape
        if self.show_average:
            self._draw_average_shape(painter)

    def _draw_wireframe(self, painter):
        """Draw wireframe connections between landmarks.

        Args:
            painter: QPainter instance
        """
        painter.setPen(QPen(mu.as_qt_color(COLOR["WIREFRAME"]), 2))
        painter.setBrush(QBrush(mu.as_qt_color(COLOR["WIREFRAME"])))

        landmark_list = self.ds_ops.get_average_shape().landmark_list

        for wire in self.ds_ops.edge_list:
            # Skip invalid wire indices
            if wire[0] >= len(landmark_list) or wire[1] >= len(landmark_list):
                continue

            from_x = landmark_list[wire[0]][0]
            from_y = landmark_list[wire[0]][1]
            to_x = landmark_list[wire[1]][0]
            to_y = landmark_list[wire[1]][1]

            painter.drawLine(
                int(self._2canx(from_x)), int(self._2cany(from_y)), int(self._2canx(to_x)), int(self._2cany(to_y))
            )

    def _draw_object_landmarks(self, painter):
        """Draw landmarks for all objects.

        Args:
            painter: QPainter instance
        """
        radius = 1
        painter.setFont(QFont("Helvetica", 12))

        for obj in self.ds_ops.object_list:
            # Set color based on selection state
            if obj.id in self.ds_ops.selected_object_id_list:
                painter.setPen(QPen(mu.as_qt_color(COLOR["SELECTED_SHAPE"]), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR["SELECTED_SHAPE"])))
            else:
                painter.setPen(QPen(mu.as_qt_color(COLOR["NORMAL_SHAPE"]), 2))
                painter.setBrush(QBrush(mu.as_qt_color(COLOR["NORMAL_SHAPE"])))

            # Draw each landmark
            for idx, landmark in enumerate(obj.landmark_list):
                x = self._2canx(landmark[0])
                y = self._2cany(landmark[1])
                painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

    def _draw_average_shape(self, painter):
        """Draw average shape landmarks with indices.

        Args:
            painter: QPainter instance
        """
        radius = 3
        painter.setPen(QPen(mu.as_qt_color(COLOR["AVERAGE_SHAPE"]), 2))
        painter.setBrush(QBrush(mu.as_qt_color(COLOR["AVERAGE_SHAPE"])))

        for idx, landmark in enumerate(self.ds_ops.get_average_shape().landmark_list):
            x = self._2canx(landmark[0])
            y = self._2cany(landmark[1])
            painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

            # Draw landmark index
            if self.show_index:
                painter.drawText(x + 10, y + 10, str(idx + 1))

    def _2canx(self, x):
        """Convert data X coordinate to canvas X coordinate.

        Args:
            x: Data X coordinate

        Returns:
            Canvas X coordinate (int)
        """
        return int(x * self.scale + self.pan_x)

    def _2cany(self, y):
        """Convert data Y coordinate to canvas Y coordinate.

        Args:
            y: Data Y coordinate

        Returns:
            Canvas Y coordinate (int)
        """
        return int(y * self.scale + self.pan_y)
