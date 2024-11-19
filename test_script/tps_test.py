import numpy as np
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
from scipy.linalg import orthogonal_procrustes

def procrustes_align(source, target):
    """
    Perform Procrustes superimposition to align target shape to source shape.
    """
    source_centroid = np.mean(source, axis=0)
    target_centroid = np.mean(target, axis=0)
    
    centered_source = source - source_centroid
    centered_target = target - target_centroid
    
    source_scale = np.sqrt(np.sum(centered_source**2))
    target_scale = np.sqrt(np.sum(centered_target**2))
    
    scaled_source = centered_source / source_scale
    scaled_target = centered_target / target_scale
    
    R, _ = orthogonal_procrustes(scaled_target, scaled_source)
    
    aligned_target = scaled_target @ R * source_scale + source_centroid
    
    return aligned_target

def create_rectangular_grid(x_min, x_max, y_min, y_max, n_x, n_y):
    """Create points for a rectangular grid"""
    x = np.linspace(x_min, x_max, n_x)
    y = np.linspace(y_min, y_max, n_y)
    xx, yy = np.meshgrid(x, y)
    
    # Create vertical lines
    vert_lines = []
    for i in range(n_x):
        line = np.column_stack((xx[:, i], yy[:, i]))
        vert_lines.append(line)
    
    # Create horizontal lines
    horz_lines = []
    for i in range(n_y):
        line = np.column_stack((xx[i, :], yy[i, :]))
        horz_lines.append(line)
    
    return vert_lines, horz_lines

# [Previous imports and helper functions remain the same]

def thin_plate_spline_grid(source_points, target_points, n_grid_lines=20, output_size=(12, 8), show_source=False):
    """
    Visualize thin plate spline transformation between two sets of landmarks.
    
    Parameters:
    source_points: source landmarks
    target_points: target landmarks
    n_grid_lines: number of grid lines in each direction
    output_size: figure size
    show_source: whether to show source landmarks (default: False)
    """
    def U(r):
        """TPS kernel function"""
        return (r**2) * np.log(r + np.finfo(float).eps)
    
    def calculate_tps_params(control_points, target_points):
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
    
    def transform_point(point, control_points, weights, affine):
        k = cdist(point.reshape(1, -1), control_points)
        k = U(k)
        wx = weights[:, 0]
        wy = weights[:, 1]
        px = np.sum(k * wx) + affine[0, 0] + affine[1, 0] * point[0] + affine[2, 0] * point[1]
        py = np.sum(k * wy) + affine[0, 1] + affine[1, 1] * point[0] + affine[2, 1] * point[1]
        return np.array([px, py])

    # Perform Procrustes alignment
    aligned_target = procrustes_align(source_points, target_points)
    
    # Calculate TPS parameters
    weights, affine = calculate_tps_params(source_points, aligned_target)
    
    # Get fish shape bounds (excluding boundary control points)
    n_fish_points = 14
    padding = 0.1
    x_min = np.min(source_points[:n_fish_points, 0]) - padding
    x_max = np.max(source_points[:n_fish_points, 0]) + padding
    y_min = np.min(source_points[:n_fish_points, 1]) - padding
    y_max = np.max(source_points[:n_fish_points, 1]) + padding
    
    # Create rectangular grid
    vert_lines, horz_lines = create_rectangular_grid(x_min, x_max, y_min, y_max, n_grid_lines, n_grid_lines)
    
    # Transform grid lines
    transformed_vert_lines = []
    transformed_horz_lines = []
    
    # Transform vertical lines
    for line in vert_lines:
        transformed_line = np.array([transform_point(p, source_points, weights, affine) for p in line])
        transformed_vert_lines.append(transformed_line)
    
    # Transform horizontal lines
    for line in horz_lines:
        transformed_line = np.array([transform_point(p, source_points, weights, affine) for p in line])
        transformed_horz_lines.append(transformed_line)
    
    # Create visualization
    plt.figure(figsize=output_size)
    
    # Plot transformed grid lines
    for line in transformed_vert_lines:
        plt.plot(line[:, 0], line[:, 1], 'b-', alpha=0.15)
    for line in transformed_horz_lines:
        plt.plot(line[:, 0], line[:, 1], 'b-', alpha=0.15)
    
    # Plot landmarks based on show_source parameter
    if show_source:
        plt.scatter(source_points[:n_fish_points, 0], source_points[:n_fish_points, 1], 
                   c='red', s=50, zorder=2)
    plt.scatter(aligned_target[:n_fish_points, 0], aligned_target[:n_fish_points, 1], 
               c='green', s=50, zorder=2)
    
    # Clean up the plot
    plt.axis('equal')
    plt.axis('off')
    
    # Set axis limits with margin
    margin = 0.2
    plt.xlim(x_min - margin, x_max + margin)
    plt.ylim(y_min - margin, y_max + margin)
    
    plt.tight_layout(pad=0)
    plt.show()


# Example usage with fish-like shapes
if __name__ == "__main__":
    def create_boundary_points(center, radius, n_points):
        angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
        return np.column_stack((
            center[0] + radius * np.cos(angles),
            center[1] + radius * np.sin(angles)
        ))
    
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
    
    # Create boundary control points with smaller radius
    fish_center = np.mean(fish_source, axis=0)
    outer_radius = 0.8
    n_boundary_points = 24
    boundary_source = create_boundary_points(fish_center, outer_radius, n_boundary_points)
    
    # Combine fish and boundary points
    source = np.vstack([fish_source, boundary_source])
    
    # Target points with small deformation
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
    
    # Create boundary points for target with smaller deformation
    boundary_target = create_boundary_points(fish_center, outer_radius * 1.1, n_boundary_points)
    boundary_target = boundary_target * np.array([[0.9, 1.1]])
    
    # Combine fish and boundary points for target
    target = np.vstack([fish_target, boundary_target])
    
    # Add small rotation and translation
    angle = np.pi / 12
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle)],
                              [np.sin(angle), np.cos(angle)]])
    target = target @ rotation_matrix + np.array([0.2, 0.2])
    

    # Example calls with different source point visibility
    print("Visualization with source points hidden:")
    thin_plate_spline_grid(source, target, show_source=False)
    
    print("\nVisualization with source points visible:")
    thin_plate_spline_grid(source, target, show_source=True)    
    #thin_plate_spline_grid(source, target)