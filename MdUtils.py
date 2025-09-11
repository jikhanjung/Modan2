from PyQt5.QtWidgets import QMessageBox
import sys, os
import copy
import logging
from PyQt5.QtGui import QColor

import numpy as np
#from stl import mesh
import trimesh
import tempfile
import json
import zipfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Callable

# Import version from centralized version file
try:
    from version import __version__ as PROGRAM_VERSION
except ImportError:
    # Fallback for compatibility
    PROGRAM_VERSION = "0.1.4"

COMPANY_NAME = "PaleoBytes"
PROGRAM_NAME = "Modan2"

# Build information
def get_build_info():
    """Get build information from build_info.json file.
    
    Returns:
        dict: Build information with version, build_number, build_date, platform
    """
    import json
    from pathlib import Path
    
    # Try to find build_info.json in various locations
    search_paths = [
        Path("build_info.json"),  # Development environment
        Path(sys.executable).parent / "build_info.json",  # PyInstaller onedir
        Path(sys._MEIPASS) / "build_info.json" if hasattr(sys, '_MEIPASS') else None,  # PyInstaller onefile
    ]
    
    for path in search_paths:
        if path and path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
    
    # Return default values if build_info.json not found
    from datetime import datetime
    return {
        "version": PROGRAM_VERSION,
        "build_number": "local",
        "build_date": "development",
        "build_year": datetime.now().year,  # Use current year for development
        "platform": sys.platform
    }

# Get build information on module import
BUILD_INFO = get_build_info()

# Copyright with build-time year
from datetime import datetime

# Get build year from build_info.json, fallback to current year for development
def get_copyright_year():
    """Get the year for copyright display, preferring build-time year."""
    if 'build_year' in BUILD_INFO:
        return BUILD_INFO['build_year']
    # Fallback to current year for development environment
    return datetime.now().year

COPYRIGHT_YEAR = get_copyright_year()
PROGRAM_COPYRIGHT = f"© 2023-{COPYRIGHT_YEAR} Jikhan Jung"
PROGRAM_BUILD_NUMBER = BUILD_INFO.get("build_number", "local")
PROGRAM_BUILD_DATE = BUILD_INFO.get("build_date", "unknown")

DB_LOCATION = ""

#print(os.name)
USER_PROFILE_DIRECTORY = os.path.expanduser('~')

DEFAULT_DB_DIRECTORY = os.path.join( USER_PROFILE_DIRECTORY, COMPANY_NAME, PROGRAM_NAME )
DEFAULT_STORAGE_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "data/")
DEFAULT_LOG_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "logs/")
DB_BACKUP_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "backups/")

def ensure_directories():
    """Safely create necessary directories with error handling."""
    directories = [
        DEFAULT_DB_DIRECTORY,
        DEFAULT_STORAGE_DIRECTORY, 
        DEFAULT_LOG_DIRECTORY,
        DB_BACKUP_DIRECTORY
    ]
    
    for directory in directories:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create directory {directory}: {e}")
            # Don't fail completely, let the application try to continue

# Try to create directories on import, but don't fail if it doesn't work
try:
    ensure_directories()
except Exception as e:
    print(f"Warning: Directory initialization failed: {e}")
    pass


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
            logger = logging.getLogger(__name__)
            logger.debug(f"tri_mesh.vertices.shape: {tri_mesh.vertices.shape}")
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
        
        try:
            tri_mesh.export( new_file_name, file_type='obj')
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to export STL mesh to {new_file_name}: {e}")
            raise ValueError(f"Cannot export to OBJ file {new_file_name}: {e}")
    elif file_extension == 'ply':
        try:
            ply_mesh = trimesh.load(file_name)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load PLY mesh from {file_name}: {e}")
            raise ValueError(f"Cannot load PLY file {file_name}: {e}")
        #print("ply_mesh shape:", ply_mesh.vertices.shape)
        #print("ply_mesh vertices:", ply_mesh.vertices[0:5,:])
        #print("ply_mesh faces:", ply_mesh.faces[0:5,:])
        try:
            ply_mesh.export( new_file_name, file_type='obj')
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to export PLY mesh to {new_file_name}: {e}")
            raise ValueError(f"Cannot export to OBJ file {new_file_name}: {e}")
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
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('LM='):
                    return read_tps_file(file_path)
                elif 'DIM=' in first_line:
                    return read_nts_file(file_path)
        except (FileNotFoundError, PermissionError) as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Cannot read landmark file {file_path}: {e}")
            raise
        except UnicodeDecodeError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Encoding error reading {file_path}: {e}")
            raise ValueError(f"Cannot decode file {file_path}. Please check file encoding.")
    
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
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('LM='):
                    # Start new specimen
                    if current_landmarks and current_name:
                        specimens.append((current_name, current_landmarks))
                    
                    try:
                        landmark_count = int(line.split('=')[1])
                    except (ValueError, IndexError) as e:
                        logger = logging.getLogger(__name__)
                        logger.error(f"Invalid LM line in {file_path}: {line}")
                        raise ValueError(f"Malformed TPS file: invalid LM line '{line}'")
                    current_landmarks = []
                    current_name = ""
                    
                elif line.startswith('ID='):
                    try:
                        current_name = line.split('=')[1].strip()
                    except IndexError:
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Invalid ID line in {file_path}: {line}")
                        current_name = "Unknown"
                    
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
        
    except (FileNotFoundError, PermissionError) as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Cannot read TPS file {file_path}: {e}")
        raise
    except UnicodeDecodeError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Encoding error reading TPS file {file_path}: {e}")
        raise ValueError(f"Cannot decode TPS file {file_path}. Please check file encoding.")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error reading TPS file {file_path}: {e}")
        raise ValueError(f"Failed to read TPS file {file_path}: {e}")
    
    return specimens


def read_nts_file(file_path):
    """Read NTS format landmark file.
    
    Args:
        file_path: Path to NTS file
        
    Returns:
        List of (specimen_name, landmarks) tuples
    """
    specimens = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (FileNotFoundError, PermissionError) as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Cannot read NTS file {file_path}: {e}")
        raise
    except UnicodeDecodeError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Encoding error reading NTS file {file_path}: {e}")
        raise ValueError(f"Cannot decode NTS file {file_path}. Please check file encoding.")
    
    try:
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # NTS header: n_specimens n_landmarks n_dimensions unknown DIM=dimension
            if 'DIM=' in line:
                parts = line.split()
                try:
                    n_specimens = int(parts[0])
                    n_landmarks = int(parts[1])
                    n_dimensions = int(parts[2])
                except (ValueError, IndexError) as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Invalid NTS header in {file_path}: {line}")
                    raise ValueError(f"Malformed NTS file: invalid header '{line}'")
            
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
                        
                        try:
                            coords = [float(x) for x in lines[i].split()]
                            landmarks.append(coords[:2])  # Use only X, Y
                        except (ValueError, IndexError):
                            # Skip invalid coordinate lines
                            continue
                    
                    specimens.append((specimen_name, landmarks))
            
            i += 1
    
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error parsing NTS file {file_path}: {e}")
        raise ValueError(f"Failed to parse NTS file {file_path}: {e}")
    
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
            
            # Get landmark count from first object
            first_obj = dataset.object_list.first() if dataset.object_list.count() > 0 else None
            landmark_count = first_obj.count_landmarks() if first_obj else 0
            
            metadata = f"# Dataset: {dataset.dataset_name}\n"
            metadata += f"# Description: {dataset.dataset_desc}\n"
            metadata += f"# Dimension: {dataset.dimension}D\n"
            metadata += f"# Landmarks: {landmark_count}\n"
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
                # Get landmark count from first object
                first_obj = dataset.object_list.first() if dataset.object_list.count() > 0 else None
                landmark_count = first_obj.count_landmarks() if first_obj else 0
                
                metadata_df = pd.DataFrame({
                    'Property': ['Dataset Name', 'Description', 'Dimension', 'Landmarks', 'Objects', 'Exported'],
                    'Value': [
                        dataset.dataset_name,
                        dataset.dataset_desc,
                        f"{dataset.dimension}D",
                        landmark_count,
                        len(data_rows),
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                })
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
        return True
        
    except Exception as e:
        show_error_message(f"Failed to export Excel: {e}")
        return False

# -----------------------------
# JSON+ZIP Export/Import (Issue #048)
# -----------------------------

def _get_storage_dir() -> str:
    """Resolve storage directory from QApplication or fallback to default."""
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app and hasattr(app, 'storage_directory'):
            return os.path.abspath(getattr(app, 'storage_directory'))
    except Exception:
        pass
    return os.path.abspath(DEFAULT_STORAGE_DIRECTORY)


def serialize_dataset_to_json(dataset_id: int, include_files: bool = True, storage_dir: Optional[str] = None) -> dict:
    """Serialize dataset and objects to JSON structure for export.

    Args:
        dataset_id: Dataset primary key
        include_files: Include image/model metadata
        storage_dir: Base storage directory for attached files

    Returns:
        dict representing the JSON schema (v1.1)
    """
    from MdModel import MdDataset, MdObject

    storage_base = os.path.abspath(storage_dir or _get_storage_dir())

    dataset = MdDataset.get_by_id(dataset_id)
    # Ensure lists are unpacked
    wf = dataset.unpack_wireframe()
    polys = dataset.unpack_polygons()
    base = dataset.unpack_baseline()
    vars_list = dataset.get_variablename_list()

    # Collect objects ordered by sequence (if present)
    objects_query = dataset.object_list.order_by(MdObject.sequence)

    objects_json = []
    landmark_counts = []

    for obj in objects_query:
        obj.unpack_landmark()
        obj.unpack_variable()
        # variables mapping
        variables = {}
        if vars_list:
            for i, name in enumerate(vars_list):
                val = obj.variable_list[i] if i < len(obj.variable_list) else None
                variables[name] = val

        files_meta = {}
        if include_files:
            # image
            if obj.has_image():
                img = obj.get_image()
                img_ext = (Path(img.original_path).suffix or '').lstrip('.')
                rel_path = f"images/{obj.id}.{img_ext}" if img_ext else f"images/{obj.id}"
                files_meta['image'] = {
                    'path': rel_path,
                    'original_filename': img.original_filename,
                    'size': img.size,
                    'md5hash': img.md5hash,
                    'last_modified': datetime.fromtimestamp(img.file_modified).isoformat() if img.file_modified else None,
                }
            # model
            if obj.has_threed_model():
                mdl = obj.get_threed_model()
                mdl_ext = (Path(mdl.original_path).suffix or '').lstrip('.')
                rel_path = f"models/{obj.id}.{mdl_ext}" if mdl_ext else f"models/{obj.id}"
                files_meta['model'] = {
                    'path': rel_path,
                    'original_filename': mdl.original_filename,
                    'size': mdl.size,
                    'md5hash': mdl.md5hash,
                    'last_modified': datetime.fromtimestamp(mdl.file_modified).isoformat() if mdl.file_modified else None,
                }

        # landmarks list (allow None entries)
        lms = obj.landmark_list or []
        if lms:
            landmark_counts.append(len(lms))

        objects_json.append({
            'id': obj.id,
            'name': obj.object_name,
            'sequence': obj.sequence,
            'created_date': obj.created_at.date().isoformat() if obj.created_at else None,
            'pixels_per_mm': obj.pixels_per_mm,
            'landmarks': lms,
            'variables': variables,
            'files': files_meta or None
        })

    lm_count = max(landmark_counts) if landmark_counts else 0

    export_info = {
        'exported_by': f"{PROGRAM_NAME} v{BUILD_INFO.get('version', PROGRAM_VERSION)}",
        'export_date': datetime.utcnow().isoformat() + 'Z',
        'export_format': 'JSON+ZIP',
        'include_files': bool(include_files),
    }

    dataset_json = {
        'id': dataset.id,
        'name': dataset.dataset_name,
        'description': dataset.dataset_desc,
        'dimension': dataset.dimension,
        'created_date': dataset.created_at.date().isoformat() if dataset.created_at else None,
        'modified_date': dataset.modified_at.date().isoformat() if dataset.modified_at else None,
        'variables': vars_list or [],
        'landmark_count': lm_count,
        'object_count': len(objects_json),
        'wireframe': wf or [],
        'polygons': polys or [],
        'baseline': base or []
    }

    return {
        'format_version': '1.1',
        'export_info': export_info,
        'dataset': dataset_json,
        'objects': objects_json,
    }


def collect_dataset_files(dataset_id: int, storage_dir: Optional[str] = None) -> Tuple[List[str], List[str]]:
    """Collect absolute file paths (images, models) for the dataset."""
    from MdModel import MdDataset, MdObject

    storage_base = os.path.abspath(storage_dir or _get_storage_dir())
    ds = MdDataset.get_by_id(dataset_id)
    images: List[str] = []
    models: List[str] = []
    for obj in ds.object_list.order_by(MdObject.sequence):
        if obj.has_image():
            p = obj.get_image().get_file_path(storage_base)
            if os.path.exists(p):
                images.append(p)
        if obj.has_threed_model():
            p = obj.get_threed_model().get_file_path(storage_base)
            if os.path.exists(p):
                models.append(p)
    return images, models


def estimate_package_size(dataset_id: int, include_files: bool = True) -> int:
    """Estimate total size (bytes) of JSON + optional files."""
    try:
        data = serialize_dataset_to_json(dataset_id, include_files=include_files)
        json_size = len(json.dumps(data, ensure_ascii=False))
    except Exception:
        json_size = 0
    total = json_size
    if include_files:
        imgs, mdls = collect_dataset_files(dataset_id)
        for p in imgs + mdls:
            try:
                total += os.path.getsize(p)
            except OSError:
                continue
    return total


def create_zip_package(dataset_id: int, output_path: str, include_files: bool = True, progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
    """Create JSON+ZIP package for a dataset.

    progress_callback: callable(curr, total)
    """
    storage_base = _get_storage_dir()
    data = serialize_dataset_to_json(dataset_id, include_files=include_files, storage_dir=storage_base)

    # Prepare temp assembly dir
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        images_dir = tmp_root / 'images'
        models_dir = tmp_root / 'models'
        images_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON
        dataset_json_path = tmp_root / 'dataset.json'
        with open(dataset_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        total_steps = 1
        files_to_copy: List[Tuple[Path, Path]] = []
        if include_files:
            # Build copy plan based on objects in JSON
            for obj in data.get('objects', []):
                files = obj.get('files') or {}
                if 'image' in files and files['image'] and files['image'].get('path'):
                    rel = files['image']['path']
                    ext = Path(rel).suffix
                    src = Path(storage_base) / str(data['dataset']['id']) / f"{obj['id']}{ext}"
                    dst = tmp_root / rel
                    files_to_copy.append((src, dst))
                if 'model' in files and files['model'] and files['model'].get('path'):
                    rel = files['model']['path']
                    ext = Path(rel).suffix
                    src = Path(storage_base) / str(data['dataset']['id']) / f"{obj['id']}{ext}"
                    dst = tmp_root / rel
                    files_to_copy.append((src, dst))
        total_steps += len(files_to_copy)

        # Copy files
        curr = 0
        for src, dst in files_to_copy:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to include file {src}: {e}")
            curr += 1
            if progress_callback:
                progress_callback(curr, total_steps)

        # Create ZIP
        zip_mode = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(output_path, 'w', compression=zip_mode) as zf:
            for root, _, files in os.walk(tmp_root):
                for name in files:
                    full = Path(root) / name
                    arc = str(full.relative_to(tmp_root))
                    zf.write(str(full), arcname=arc)
                    curr += 1
                    if progress_callback:
                        progress_callback(curr, total_steps + len(list(files)))

    return True


def validate_json_schema(data: dict) -> Tuple[bool, List[str]]:
    """Lightweight validation of the exported schema."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, ["Root is not an object"]
    for k in ['format_version', 'export_info', 'dataset', 'objects']:
        if k not in data:
            errors.append(f"Missing key: {k}")
    ds = data.get('dataset', {})
    for k in ['name', 'dimension', 'variables']:
        if k not in ds:
            errors.append(f"dataset missing: {k}")
    if not isinstance(data.get('objects', []), list):
        errors.append('objects must be a list')
    return (len(errors) == 0), errors


def safe_extract_zip(zip_path: str, dest_dir: str) -> str:
    """Safely extract ZIP to dest_dir, preventing Zip Slip."""
    dest = Path(dest_dir).resolve()
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            member_path = dest / member.filename
            resolved = member_path.resolve()
            if not str(resolved).startswith(str(dest)):
                raise ValueError(f"Unsafe path in ZIP: {member.filename}")
        zf.extractall(dest)
    return str(dest)


def read_json_from_zip(zip_path: str) -> dict:
    with zipfile.ZipFile(zip_path, 'r') as zf:
        with zf.open('dataset.json') as f:
            return json.loads(f.read().decode('utf-8'))


def import_dataset_from_zip(zip_path: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> int:
    """Import dataset from a JSON+ZIP package. Returns new dataset id."""
    from MdModel import MdDataset, MdObject, MdImage, MdThreeDModel, gDatabase

    with tempfile.TemporaryDirectory() as tmpdir:
        root = safe_extract_zip(zip_path, tmpdir)
        data = read_json_from_zip(zip_path)
        ok, errs = validate_json_schema(data)
        if not ok:
            raise ValueError("Invalid dataset.json: " + "; ".join(errs))

        ds_meta = data['dataset']
        objs = data.get('objects', [])

        total = max(1, len(objs) * 3)
        curr = 0
        if progress_callback:
            progress_callback(curr, total)

        with gDatabase.atomic():
            # Create dataset
            ds = MdDataset()
            # Ensure unique dataset name by appending (1), (2), ... if needed
            base_name = ds_meta.get('name') or 'Imported Dataset'
            candidate = base_name
            suffix = 1
            while MdDataset.select().where(MdDataset.dataset_name == candidate).exists():
                candidate = f"{base_name} ({suffix})"
                suffix += 1
            ds.dataset_name = candidate
            ds.dataset_desc = ds_meta.get('description')
            ds.dimension = int(ds_meta.get('dimension') or 2)
            # variables
            ds.variablename_list = ds_meta.get('variables') or []
            ds.pack_variablename_str()
            # geometry
            ds.edge_list = ds_meta.get('wireframe') or []
            ds.pack_wireframe()
            ds.polygon_list = ds_meta.get('polygons') or []
            ds.pack_polygons()
            baseline = ds_meta.get('baseline') or []
            if baseline:
                ds.baseline_point_list = baseline
                ds.pack_baseline()
            ds.save()

            storage_base = _get_storage_dir()

            for o in objs:
                mo = MdObject()
                mo.object_name = o.get('name') or str(o.get('id'))
                mo.object_desc = None
                ppm = o.get('pixels_per_mm')
                mo.pixels_per_mm = float(ppm) if ppm is not None else None
                mo.sequence = o.get('sequence')
                # landmarks -> landmark_str
                lm_lines = []
                for lm in o.get('landmarks') or []:
                    if lm is None:
                        continue
                    lm_str = '\t'.join([str(x) for x in lm[:ds.dimension]])
                    lm_lines.append(lm_str)
                mo.landmark_str = '\n'.join(lm_lines)
                # variables -> property_str
                varmap = o.get('variables') or {}
                varvals = [varmap.get(n) if varmap.get(n) is not None else '' for n in ds.variablename_list]
                mo.variable_list = varvals
                mo.pack_variable()
                mo.dataset = ds
                mo.save()

                curr += 1
                if progress_callback:
                    progress_callback(curr, total)

                # files
                files = o.get('files') or {}
                # image
                img_meta = files.get('image') if isinstance(files, dict) else None
                if img_meta and img_meta.get('path'):
                    src = Path(root) / img_meta['path']
                    if src.exists():
                        new_image = MdImage()
                        new_image.object = mo
                        new_image.load_file_info(str(src))
                        new_fp = new_image.get_file_path(storage_base)
                        Path(new_fp).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(src), str(new_fp))
                        new_image.save()

                # model
                mdl_meta = files.get('model') if isinstance(files, dict) else None
                if mdl_meta and mdl_meta.get('path'):
                    src = Path(root) / mdl_meta['path']
                    if src.exists():
                        new_model = MdThreeDModel()
                        new_model.object = mo
                        new_model.load_file_info(str(src))
                        new_fp = new_model.get_file_path(storage_base)
                        Path(new_fp).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(src), str(new_fp))
                        new_model.save()

                curr += 2
                if progress_callback:
                    progress_callback(curr, total)

        return ds.id
