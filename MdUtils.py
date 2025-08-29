from PyQt5.QtWidgets import QMessageBox
import sys, os
import copy
from PyQt5.QtGui import QColor

import numpy as np
#from stl import mesh
import trimesh
import tempfile

COMPANY_NAME = "PaleoBytes"
PROGRAM_NAME = "Modan2"
PROGRAM_VERSION = "0.1.4"

DB_LOCATION = ""

#print(os.name)
USER_PROFILE_DIRECTORY = os.path.expanduser('~')

DEFAULT_DB_DIRECTORY = os.path.join( USER_PROFILE_DIRECTORY, COMPANY_NAME, PROGRAM_NAME )
DEFAULT_STORAGE_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "data/")
DEFAULT_LOG_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "logs/")
DB_BACKUP_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "backups/")

if not os.path.exists(DEFAULT_DB_DIRECTORY):
    os.makedirs(DEFAULT_DB_DIRECTORY)
if not os.path.exists(DEFAULT_STORAGE_DIRECTORY):
    os.makedirs(DEFAULT_STORAGE_DIRECTORY)
if not os.path.exists(DEFAULT_LOG_DIRECTORY):
    os.makedirs(DEFAULT_LOG_DIRECTORY)
if not os.path.exists(DB_BACKUP_DIRECTORY):
    os.makedirs(DB_BACKUP_DIRECTORY)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


IMAGE_EXTENSION_LIST = ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']
MODEL_EXTENSION_LIST = ['obj', 'ply', 'stl']

VIVID_COLOR_LIST =  [
    "#0000FF",  # Blue
    "#FF0000",  # Red
    "#008000",  # Green
    "#800080",  # Purple
    "#FFA500",  # Orange
    "#00FFFF",  # Cyan
    "#FF00FF",  # Magenta
    "#FFFF00",  # Yellow
    "#008080",  # Teal
    "#FF1493",  # Pink
    "#00FF00",  # Lime
    "#4B0082",  # Indigo
    "#800000",  # Maroon
    "#808000",  # Olive
    "#000080",  # Navy
    "#FF6F61",  # Coral
    "#40E0D0",  # Turquoise
    "#E6E6FA",  # Lavender
    "#FFD700",  # Gold
    "#6A5ACD"   # Slate
]
PASTEL_COLOR_LIST = [
    "#AEC6CF",  # Pastel Blue
    "#F49AC2",  # Pastel Pink
    "#B0E57C",  # Pastel Green
    "#B39EB5",  # Pastel Purple
    "#F9CB9C",  # Pastel Orange
    "#F8ED8E",  # Pastel Yellow
    "#DCD0FF",  # Pastel Lavender
    "#AAF0D1",  # Pastel Mint
    "#FFD1A3",  # Pastel Peach
    "#AEEEEE",  # Pastel Aqua
    "#E8A3E5",  # Pastel Lilac
    "#FFB5B5",  # Pastel Coral
    "#94E8B4",  # Pastel Teal
    "#FF9E9E",  # Pastel Salmon
    "#87CEEB",  # Pastel Sky Blue
    "#FFC7E5",  # Pastel Rose
    "#FDFD96",  # Pastel Lemon
    "#C5A3FF",  # Pastel Periwinkle
    "#AFEEEE",  # Pastel Turquoise
    "#FFD8B1"   # Pastel Apricot
]

MARKER_LIST = ['o','s','^','x','+','d','v','<','>','p','h']


def as_qt_color(color):
    if isinstance(color, QColor):
        return color
    if isinstance(color, str):
        return QColor(color)
    
    return QColor( *[ int(x*255) for x in color ] )

def as_gl_color(color):
    #print("as_gl_color", color)
    qcolor = QColor(color)
    return qcolor.redF(), qcolor.greenF(), qcolor.blueF()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def value_to_bool(value):
    return value.lower() == 'true' if isinstance(value, str) else bool(value)

def process_dropped_file_name(file_name):
    import os
    from urllib.parse import urlparse, unquote
    #print("file_name:", file_name)
    url = file_name
    parsed_url = urlparse(url)            
    #print("parsed_url:", parsed_url)
    file_path = unquote(parsed_url.path)
    if os.name == 'nt':
        file_path = file_path[1:]
    else:
        file_path = file_path
    return file_path
def process_3d_file(file_name):
    # get extension
    file_extension = os.path.splitext(file_name)[1][1:].lower()
    #print("file_extension:", file_extension)
    if file_extension == 'obj':
        return file_name
    
    temp_dir = tempfile.mkdtemp()

    # get filename without extension
    file_name_only = os.path.splitext(file_name)[0]
    # copy to temp dir
    new_file_name = os.path.join(temp_dir, file_name_only + ".obj")
    #print("new_file_name:", new_file_name)
    
    if file_extension == 'stl':

        #stl_mesh = mesh.Mesh.from_file(file_name)
        #tri_mesh = trimesh.Trimesh(stl_mesh.vectors, process=False)
        tri_mesh = trimesh.load_mesh(file_name)
        
        # if vertices are not 2D array, convert to 2D array
        # actually in that case vertices have faces data.
        # so for each face, extract vertices and make a new array of vertices
        # and make a new array of faces

        if False and len(tri_mesh.vertices.shape) == 3:
            print("tri_mesh.vertices.shape:", tri_mesh.vertices.shape)
            tri_mesh.faces = []
            vertices = []
            faces = []
            for i in range(tri_mesh.vertices.shape[0]):
                temp_face = []
                for j in range(tri_mesh.vertices.shape[1]):
                    #if tri_mesh.vertices[i,j,:].all() not in vertices:
                    vertices.append(tri_mesh.vertices[i,j,:])
                    temp_face.append(len(vertices)-1)
                faces.append(temp_face)
            tri_mesh.vertices = np.array(vertices)
            tri_mesh.faces = np.array(faces)
            #print("tri_mesh.vertices.shape:", tri_mesh.vertices.shape)
            #print("tri_mesh.faces.shape:", tri_mesh.faces.shape)
        vn = tri_mesh.vertex_normals
        #print("stl_mesh shape:", tri_mesh.vertices.shape)
        #print("vertex normals:", tri_mesh.vertex_normals)
        #print("stl_mesh vertices:", tri_mesh.vertices[0:5,:])
        #print("stl_mesh faces:", tri_mesh.faces[0:5,:])
        
        tri_mesh.export( new_file_name, file_type='obj')
    elif file_extension == 'ply':
        ply_mesh = trimesh.load(file_name)
        #print("ply_mesh shape:", ply_mesh.vertices.shape)
        #print("ply_mesh vertices:", ply_mesh.vertices[0:5,:])
        #print("ply_mesh faces:", ply_mesh.faces[0:5,:])
        ply_mesh.export( new_file_name, file_type='obj')
    return new_file_name

def show_error_message(error_message):
    #error_message = "Number of objects is too small for analysis."
    # show messagebox and close the window
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(error_message)
    msg.setWindowTitle("Error")
    msg.exec_()
    return

def is_numeric(value):
    """Checks if a value is numeric (float)."""
    try:
        float(value)
        return True
    except ValueError:
        return False

def get_ellipse_params(covariance, n_std):
    eigenvalues, eigenvectors = np.linalg.eig(covariance)
    order = eigenvalues.argsort()[::-1]
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
    vx, vy = eigenvectors[:, 0][0], eigenvectors[:, 0][1]
    theta = np.arctan2(vy, vx)

    width, height = 1 * n_std * np.sqrt(eigenvalues)
    angle = np.degrees(theta)
    return width, height, angle


def read_landmark_file(file_path):
    """Read landmarks from TPS/NTS file.
    
    Args:
        file_path: Path to landmark file
        
    Returns:
        List of (specimen_name, landmarks) tuples
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.tps':
        return read_tps_file(file_path)
    elif file_ext == '.nts':
        return read_nts_file(file_path)
    elif file_ext == '.txt':
        # Try to detect format
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
            if first_line.startswith('LM='):
                return read_tps_file(file_path)
            elif 'DIM=' in first_line:
                return read_nts_file(file_path)
    
    raise ValueError(f"Unsupported landmark file format: {file_ext}")


def read_tps_file(file_path):
    """Read TPS format landmark file.
    
    Args:
        file_path: Path to TPS file
        
    Returns:
        List of (specimen_name, landmarks) tuples
    """
    specimens = []
    current_landmarks = []
    current_name = ""
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            if line.startswith('LM='):
                # Start new specimen
                if current_landmarks and current_name:
                    specimens.append((current_name, current_landmarks))
                
                landmark_count = int(line.split('=')[1])
                current_landmarks = []
                current_name = ""
                
            elif line.startswith('ID='):
                current_name = line.split('=')[1].strip()
                
            elif line and not line.startswith(('IMAGE=', 'SCALE=')):
                # Landmark coordinates
                try:
                    coords = [float(x) for x in line.split()]
                    if len(coords) >= 2:
                        current_landmarks.append(coords[:2])  # Use only X, Y
                except ValueError:
                    continue
    
    # Add last specimen
    if current_landmarks and current_name:
        specimens.append((current_name, current_landmarks))
    elif current_landmarks:
        specimens.append((f"specimen_{len(specimens)+1}", current_landmarks))
    
    return specimens


def read_nts_file(file_path):
    """Read NTS format landmark file.
    
    Args:
        file_path: Path to NTS file
        
    Returns:
        List of (specimen_name, landmarks) tuples
    """
    specimens = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # NTS header: n_specimens n_landmarks n_dimensions unknown DIM=dimension
        if 'DIM=' in line:
            parts = line.split()
            n_specimens = int(parts[0])
            n_landmarks = int(parts[1])
            n_dimensions = int(parts[2])
            
            for spec_idx in range(n_specimens):
                i += 1
                if i >= len(lines):
                    break
                
                # Specimen name
                specimen_name = lines[i].strip()
                landmarks = []
                
                # Read landmarks
                for lm_idx in range(n_landmarks):
                    i += 1
                    if i >= len(lines):
                        break
                    
                    coords = [float(x) for x in lines[i].split()]
                    landmarks.append(coords[:2])  # Use only X, Y
                
                specimens.append((specimen_name, landmarks))
        
        i += 1
    
    return specimens


def export_dataset_to_csv(dataset, file_path, include_metadata=True):
    """Export dataset to CSV file.
    
    Args:
        dataset: MdDataset instance
        file_path: Output CSV file path
        include_metadata: Include dataset metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import pandas as pd
        
        # Collect data
        data_rows = []
        for obj in dataset.objects:
            if obj.landmarks:
                row = {'object_name': obj.object_name}
                
                # Add landmark coordinates
                for i, landmark in enumerate(obj.landmarks):
                    row[f'x{i+1}'] = landmark[0]
                    row[f'y{i+1}'] = landmark[1]
                    if len(landmark) > 2:
                        row[f'z{i+1}'] = landmark[2]
                
                data_rows.append(row)
        
        if not data_rows:
            return False
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        
        # Add metadata if requested
        if include_metadata:
            with open(file_path, 'r') as f:
                content = f.read()
            
            metadata = f"# Dataset: {dataset.dataset_name}\n"
            metadata += f"# Description: {dataset.dataset_desc}\n"
            metadata += f"# Dimension: {dataset.dimension}D\n"
            metadata += f"# Landmarks: {dataset.landmark_count}\n"
            metadata += f"# Objects: {len(data_rows)}\n"
            metadata += f"# Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            with open(file_path, 'w') as f:
                f.write(metadata + content)
        
        return True
        
    except Exception as e:
        show_error_message(f"Failed to export CSV: {e}")
        return False


def export_dataset_to_excel(dataset, file_path, include_metadata=True):
    """Export dataset to Excel file.
    
    Args:
        dataset: MdDataset instance
        file_path: Output Excel file path
        include_metadata: Include dataset metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import pandas as pd
        
        # Collect data
        data_rows = []
        for obj in dataset.objects:
            if obj.landmarks:
                row = {'object_name': obj.object_name}
                
                # Add landmark coordinates
                for i, landmark in enumerate(obj.landmarks):
                    row[f'x{i+1}'] = landmark[0]
                    row[f'y{i+1}'] = landmark[1]
                    if len(landmark) > 2:
                        row[f'z{i+1}'] = landmark[2]
                
                data_rows.append(row)
        
        if not data_rows:
            return False
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Create Excel writer
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            # Write data
            df.to_excel(writer, sheet_name='Landmarks', index=False)
            
            # Add metadata sheet if requested
            if include_metadata:
                metadata_df = pd.DataFrame({
                    'Property': ['Dataset Name', 'Description', 'Dimension', 'Landmarks', 'Objects', 'Exported'],
                    'Value': [
                        dataset.dataset_name,
                        dataset.dataset_desc,
                        f"{dataset.dimension}D",
                        dataset.landmark_count,
                        len(data_rows),
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                })
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
        return True
        
    except Exception as e:
        show_error_message(f"Failed to export Excel: {e}")
        return False
