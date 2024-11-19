import sys
import numpy as np
from scipy.spatial.distance import cdist
from scipy.linalg import orthogonal_procrustes
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QCheckBox, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF
from math import atan2, cos, sin, pi

class TPSVisualizerWidget(QLabel):
    def __init__(self, source_points, target_points, parent=None):
        super().__init__(parent)
        # Store only the fish points initially
        self.source_fish = source_points
        self.target_fish = target_points
        self.show_source = False
        self.show_arrows = False
        self.n_grid_lines = 20
        self.n_fish_points = len(source_points)  # Now this is the actual number of fish points
        
        # Calculate transformed points and grid
        self.setup_transformation()
        
        # Set fixed size for the widget
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: white;")
        
    def setup_transformation(self):
        """Calculate TPS transformation parameters and prepare grid"""
        # First perform Procrustes alignment on fish points only
        self.aligned_target_fish = self.procrustes_align(self.source_fish, self.target_fish)
        
        # Now create boundary points based on aligned shapes
        self.source_points, self.aligned_target = self.add_boundary_points(
            self.source_fish, 
            self.aligned_target_fish
        )
        
        # Calculate TPS parameters
        self.weights, self.affine = self.calculate_tps_params(
            self.source_points, 
            self.aligned_target
        )
        
        # Get fish shape bounds for grid creation
        padding = 0.1
        self.x_min = np.min(self.source_fish[:, 0]) - padding
        self.x_max = np.max(self.source_fish[:, 0]) + padding
        self.y_min = np.min(self.source_fish[:, 1]) - padding
        self.y_max = np.max(self.source_fish[:, 1]) + padding
        
        # Create and transform grid
        self.create_grid()

    def add_boundary_points(self, source_fish, target_fish):
        """Add boundary points to source and target after alignment"""
        def create_boundary_points(points, radius):
            center = np.mean(points, axis=0)
            n_points = 24
            angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
            return np.column_stack((
                center[0] + radius * np.cos(angles),
                center[1] + radius * np.sin(angles)
            ))
        
        # Calculate radius based on shape size
        max_dist = np.max(np.sqrt(np.sum((source_fish - np.mean(source_fish, axis=0))**2, axis=1)))
        radius = max_dist * 1.2  # Radius relative to shape size
        
        # Create boundary points for both shapes
        boundary_source = create_boundary_points(source_fish, radius)
        boundary_target = create_boundary_points(target_fish, radius)
        
        # Combine fish and boundary points
        source_with_boundary = np.vstack([source_fish, boundary_source])
        target_with_boundary = np.vstack([target_fish, boundary_target])
        
        return source_with_boundary, target_with_boundary
    
    def create_grid(self):
        """Create and transform the rectangular grid"""
        # Create original grid lines
        x = np.linspace(self.x_min, self.x_max, self.n_grid_lines)
        y = np.linspace(self.y_min, self.y_max, self.n_grid_lines)
        
        # Transform grid lines
        self.transformed_vert_lines = []
        self.transformed_horz_lines = []
        
        # Vertical lines
        for i in range(self.n_grid_lines):
            line_points = np.array([(x[i], y_) for y_ in y])
            transformed_line = np.array([self.transform_point(p) for p in line_points])
            self.transformed_vert_lines.append(transformed_line)
        
        # Horizontal lines
        for i in range(self.n_grid_lines):
            line_points = np.array([(x_, y[i]) for x_ in x])
            transformed_line = np.array([self.transform_point(p) for p in line_points])
            self.transformed_horz_lines.append(transformed_line)

    def transform_point(self, point):
        """Transform a single point using TPS"""
        def U(r):
            return (r**2) * np.log(r + np.finfo(float).eps)
        
        k = cdist(point.reshape(1, -1), self.source_points)
        k = U(k)
        wx = self.weights[:, 0]
        wy = self.weights[:, 1]
        px = np.sum(k * wx) + self.affine[0, 0] + self.affine[1, 0] * point[0] + self.affine[2, 0] * point[1]
        py = np.sum(k * wy) + self.affine[0, 1] + self.affine[1, 1] * point[0] + self.affine[2, 1] * point[1]
        return np.array([px, py])

    def procrustes_align(self, source, target):
        """Perform Procrustes alignment"""
        source_centroid = np.mean(source, axis=0)
        target_centroid = np.mean(target, axis=0)
        
        centered_source = source - source_centroid
        centered_target = target - target_centroid
        
        source_scale = np.sqrt(np.sum(centered_source**2))
        target_scale = np.sqrt(np.sum(centered_target**2))
        
        scaled_source = centered_source / source_scale
        scaled_target = centered_target / target_scale
        
        R, _ = orthogonal_procrustes(scaled_target, scaled_source)
        
        return scaled_target @ R * source_scale + source_centroid

    def calculate_tps_params(self, control_points, target_points):
        """Calculate TPS parameters"""
        def U(r):
            return (r**2) * np.log(r + np.finfo(float).eps)
        
        n = control_points.shape[0]
        K = cdist(control_points, control_points)
        K = U(K)
        P = np.hstack([np.ones((n, 1)), control_points])
        L = np.vstack([
            np.hstack([K, P]),
            np.hstack([P.T, np.zeros((3, 3))])
        ])
        Y = np.vstack([target_points, np.zeros((3, 2))])
        params = np.linalg.solve(L, Y)
        return params[:-3], params[-3:]

    def map_to_screen(self, points):
        """Map points from data coordinates to screen coordinates"""
        margin = 40
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin
        
        # Scale points to fit the widget
        x_scale = width / (self.x_max - self.x_min)
        y_scale = height / (self.y_max - self.y_min)
        scale = min(x_scale, y_scale)
        
        # Center the visualization
        x_offset = margin + (width - scale * (self.x_max - self.x_min)) / 2
        y_offset = margin + (height - scale * (self.y_max - self.y_min)) / 2
        
        screen_points = []
        for point in points:
            x = x_offset + scale * (point[0] - self.x_min)
            y = y_offset + scale * (point[1] - self.y_min)
            screen_points.append(QPointF(x, y))
            
        return screen_points

    def draw_arrow(self, painter, start_point, end_point):
        """Draw an arrow from start_point to end_point"""
        # Arrow head parameters
        arrow_size = 10
        angle = pi/6  # 30 degrees
        
        # Calculate direction vector
        dx = end_point.x() - start_point.x()
        dy = end_point.y() - start_point.y()
        length = (dx**2 + dy**2)**0.5
        
        if length == 0:
            return
        
        # Normalize direction vector
        dx, dy = dx/length, dy/length
        
        # Calculate arrow head points
        right_x = end_point.x() - arrow_size * (dx*cos(angle) + dy*sin(angle))
        right_y = end_point.y() - arrow_size * (-dx*sin(angle) + dy*cos(angle))
        left_x = end_point.x() - arrow_size * (dx*cos(-angle) + dy*sin(-angle))
        left_y = end_point.y() - arrow_size * (-dx*sin(-angle) + dy*cos(-angle))
        
        # Draw arrow line
        painter.drawLine(start_point, end_point)
        
        # Draw arrow head
        arrow_head = QPolygonF([
            end_point,
            QPointF(right_x, right_y),
            QPointF(left_x, left_y)
        ])
        painter.drawPolygon(arrow_head)

    def paintEvent(self, event):
        """Draw the visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw grid lines
        pen = QPen(QColor(0, 0, 255, 40))  # Light blue
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Draw vertical grid lines
        for line in self.transformed_vert_lines:
            points = self.map_to_screen(line)
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        
        # Draw horizontal grid lines
        for line in self.transformed_horz_lines:
            points = self.map_to_screen(line)
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        
        # Draw arrows if enabled
        if self.show_arrows:
            pen.setColor(QColor(128, 128, 128, 180))  # Semi-transparent gray
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(QColor(128, 128, 128, 180))
            
            source_points = self.map_to_screen(self.source_points[:self.n_fish_points])
            target_points = self.map_to_screen(self.aligned_target[:self.n_fish_points])
            
            for start, end in zip(source_points, target_points):
                self.draw_arrow(painter, start, end)
        
        # Draw source points if enabled
        if self.show_source:
            pen.setColor(QColor(255, 0, 0))  # Red
            pen.setWidth(8)
            painter.setPen(pen)
            source_screen_points = self.map_to_screen(self.source_points[:self.n_fish_points])
            for point in source_screen_points:
                painter.drawPoint(point)
        
        # Draw target points
        pen.setColor(QColor(0, 255, 0))  # Green
        pen.setWidth(8)
        painter.setPen(pen)
        target_screen_points = self.map_to_screen(self.aligned_target[:self.n_fish_points])
        for point in target_screen_points:
            painter.drawPoint(point)

    def toggle_source_points(self, state):
        """Toggle visibility of source points"""
        self.show_source = state
        self.update()

    def toggle_arrows(self, state):
        """Toggle visibility of arrows"""
        self.show_arrows = state
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TPS Visualization")
        
        # Create main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Create and add TPS visualizer
        source, target = create_fish_shapes()
        self.visualizer = TPSVisualizerWidget(source, target)
        layout.addWidget(self.visualizer)
        
        # Create checkbox container
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout()
        
        # Add checkbox for source points visibility
        source_checkbox = QCheckBox("Show source points")
        source_checkbox.stateChanged.connect(self.visualizer.toggle_source_points)
        checkbox_layout.addWidget(source_checkbox)
        
        # Add checkbox for arrows visibility
        arrows_checkbox = QCheckBox("Show arrows")
        arrows_checkbox.stateChanged.connect(self.visualizer.toggle_arrows)
        checkbox_layout.addWidget(arrows_checkbox)
        
        checkbox_widget.setLayout(checkbox_layout)
        layout.addWidget(checkbox_widget)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)


def create_fish_shapes():
    """Create source and target fish shapes"""
    # Source points (normal fish)
    fish_source = np.array([
        [0.0, 0.0],     # Nose
        [1.0, 0.0],     # Tail tip
        [0.3, 0.2],     # Top of head
        [0.3, -0.2],    # Bottom of head
        [0.7, 0.15],    # Top of tail
        [0.7, -0.15],   # Bottom of tail
        [0.4, 0.0],     # Middle body
        [0.5, 0.1],     # Top fin
        [0.5, -0.1],    # Bottom fin
        [0.2, 0.0],     # Eye position
        [0.15, 0.15],   # Upper head
        [0.15, -0.15],  # Lower head
        [0.85, 0.1],    # Upper tail
        [0.85, -0.1],   # Lower tail
    ])

    fish_target = np.array([
        [-0.05, 0.0],    # Nose
        [0.95, 0.0],     # Tail tip
        [0.3, 0.25],     # Top of head
        [0.3, -0.25],    # Bottom of head
        [0.68, 0.12],    # Top of tail
        [0.68, -0.12],   # Bottom of tail
        [0.4, 0.02],     # Middle body
        [0.5, 0.15],     # Top fin
        [0.5, -0.08],    # Bottom fin
        [0.2, 0.05],     # Eye position
        [0.15, 0.18],    # Upper head
        [0.15, -0.18],   # Lower head
        [0.8, 0.08],     # Upper tail
        [0.8, -0.08],    # Lower tail
    ])

    '''
    # Target points with deformation (or same as source for testing)
    fish_target = np.array([
        [0.0, 0.0],     # Nose
        [1.0, 0.0],     # Tail tip
        [0.3, 0.2],     # Top of head
        [0.3, -0.2],    # Bottom of head
        [0.7, 0.15],    # Top of tail
        [0.7, -0.15],   # Bottom of tail
        [0.4, 0.0],     # Middle body
        [0.5, 0.1],     # Top fin
        [0.5, -0.1],    # Bottom fin
        [0.2, 0.0],     # Eye position
        [0.15, 0.15],   # Upper head
        [0.15, -0.15],  # Lower head
        [0.85, 0.1],    # Upper tail
        [0.85, -0.1],   # Lower tail
    ])'''

    # Apply some transformation to target (optional, for testing)
    # angle = np.pi / 12
    # rotation_matrix = np.array([[np.cos(angle), -np.sin(angle)],
    #                           [np.sin(angle), np.cos(angle)]])
    # fish_target = fish_target @ rotation_matrix + np.array([0.2, 0.2])
    
    return fish_source, fish_target

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())