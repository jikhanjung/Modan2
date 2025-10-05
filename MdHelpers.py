"""
Helper functions and utilities for Modan2 application.
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QSettings, QStandardPaths, QUrl
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

logger = logging.getLogger(__name__)


def show_message(parent, title: str, message: str, message_type: str = "info") -> int | None:
    """Show message box to user.

    Args:
        parent: Parent widget
        title: Message box title
        message: Message text
        message_type: Type of message ('info', 'warning', 'error', 'question')

    Returns:
        Button clicked for question type, None for others
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Showing {message_type} message: {title}")

    if message_type == "info":
        QMessageBox.information(parent, title, message)
    elif message_type == "warning":
        QMessageBox.warning(parent, title, message)
    elif message_type == "error":
        QMessageBox.critical(parent, title, message)
    elif message_type == "question":
        return QMessageBox.question(parent, title, message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)


def show_error(parent, message: str):
    """Show error message.

    Args:
        parent: Parent widget
        message: Error message
    """
    show_message(parent, "Error", message, "error")


def show_warning(parent, message: str):
    """Show warning message.

    Args:
        parent: Parent widget
        message: Warning message
    """
    show_message(parent, "Warning", message, "warning")


def show_info(parent, message: str):
    """Show information message.

    Args:
        parent: Parent widget
        message: Information message
    """
    show_message(parent, "Information", message, "info")


def confirm_action(parent, message: str, title: str = "Confirm") -> bool:
    """Show confirmation dialog.

    Args:
        parent: Parent widget
        message: Confirmation message
        title: Dialog title

    Returns:
        True if user confirmed, False otherwise
    """
    result = show_message(parent, title, message, "question")
    return result == QMessageBox.Yes


def get_open_file_name(parent, title: str, file_filter: str, start_dir: str = "") -> str | None:
    """Show open file dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        file_filter: File filter string
        start_dir: Starting directory

    Returns:
        Selected file path or None if cancelled
    """
    file_name, _ = QFileDialog.getOpenFileName(parent, title, start_dir, file_filter)
    return file_name if file_name else None


def get_open_file_names(parent, title: str, file_filter: str, start_dir: str = "") -> list[str]:
    """Show open multiple files dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        file_filter: File filter string
        start_dir: Starting directory

    Returns:
        List of selected file paths
    """
    file_names, _ = QFileDialog.getOpenFileNames(parent, title, start_dir, file_filter)
    return file_names


def get_save_file_name(parent, title: str, file_filter: str, start_dir: str = "") -> str | None:
    """Show save file dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        file_filter: File filter string
        start_dir: Starting directory

    Returns:
        Selected file path or None if cancelled
    """
    file_name, _ = QFileDialog.getSaveFileName(parent, title, start_dir, file_filter)
    return file_name if file_name else None


def get_directory(parent, title: str, start_dir: str = "") -> str | None:
    """Show directory selection dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        start_dir: Starting directory

    Returns:
        Selected directory path or None if cancelled
    """
    dir_name = QFileDialog.getExistingDirectory(
        parent, title, start_dir, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
    )
    return dir_name if dir_name else None


def calculate_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """Calculate file hash.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')

    Returns:
        Hex digest of file hash
    """
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except OSError:
        return ""


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_file_size(file_path: str) -> int:
    """Get file size in bytes.

    Args:
        file_path: Path to file

    Returns:
        File size in bytes, 0 if file doesn't exist
    """
    try:
        return Path(file_path).stat().st_size
    except OSError:
        return 0


def load_json_file(file_path: str) -> dict[str, Any]:
    """Load JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If file cannot be parsed
        FileNotFoundError: If file doesn't exist
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(f"JSON file not found: {file_path}") from e


def save_json_file(file_path: str, data: dict[str, Any], indent: int = 2) -> bool:
    """Save data to JSON file.

    Args:
        file_path: Output file path
        data: Data to save
        indent: JSON indentation

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

        return True

    except OSError as e:
        logging.getLogger(__name__).error(f"Failed to save JSON file {file_path}: {e}")
        return False


def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if needed.

    Args:
        path: Directory path

    Returns:
        True if directory exists or was created
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def get_timestamp_string(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """Get current timestamp as string.

    Args:
        format_str: Datetime format string

    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_str)


def get_app_data_dir() -> Path:
    """Get application data directory.

    Returns:
        Path to application data directory
    """
    if os.name == "nt":  # Windows
        app_data = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    else:  # Linux/Mac
        app_data = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        app_data = str(Path(app_data) / ".modan2")

    path = Path(app_data)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_temp_dir() -> Path:
    """Get temporary directory for application.

    Returns:
        Path to temporary directory
    """
    temp_dir = get_app_data_dir() / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def cleanup_temp_files(older_than_days: int = 7):
    """Clean up old temporary files.

    Args:
        older_than_days: Remove files older than this many days
    """
    import time

    temp_dir = get_temp_dir()
    cutoff_time = time.time() - (older_than_days * 24 * 3600)

    removed_count = 0
    for file_path in temp_dir.rglob("*"):
        if file_path.is_file():
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    removed_count += 1
            except OSError:
                pass

    if removed_count > 0:
        logging.getLogger(__name__).info(f"Cleaned up {removed_count} temporary files")


def validate_landmark_data(landmarks: list[list[float]], expected_count: int) -> tuple[bool, str]:
    """Validate landmark data.

    Args:
        landmarks: List of landmark coordinates
        expected_count: Expected number of landmarks

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not landmarks:
        return False, "No landmark data provided"

    if len(landmarks) != expected_count:
        return False, f"Expected {expected_count} landmarks, got {len(landmarks)}"

    for i, landmark in enumerate(landmarks):
        if not isinstance(landmark, (list, tuple)) or len(landmark) not in [2, 3]:
            return False, f"Invalid landmark {i + 1}: must be 2D or 3D coordinates"

        for coord in landmark:
            if not isinstance(coord, (int, float)):
                return False, f"Invalid coordinate in landmark {i + 1}: {coord}"

    return True, "Valid landmark data"


def validate_dataset_name(name: str) -> tuple[bool, str]:
    """Validate dataset name.

    Args:
        name: Dataset name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Dataset name cannot be empty"

    name = name.strip()

    if len(name) < 1:
        return False, "Dataset name is too short"

    if len(name) > 100:
        return False, "Dataset name is too long (max 100 characters)"

    # Check for invalid characters
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    for char in invalid_chars:
        if char in name:
            return False, f"Dataset name cannot contain '{char}'"

    return True, "Valid dataset name"


def validate_file_path(file_path: str) -> tuple[bool, str]:
    """Validate file path.

    Args:
        file_path: File path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "No file path provided"

    path = Path(file_path)

    if not path.exists():
        return False, f"File does not exist: {file_path}"

    if not path.is_file():
        return False, f"Path is not a file: {file_path}"

    if not os.access(file_path, os.R_OK):
        return False, f"Cannot read file: {file_path}"

    return True, "Valid file path"


def parse_color(color_str: str) -> QColor | None:
    """Parse color string to QColor.

    Args:
        color_str: Color string (hex, name, or rgb)

    Returns:
        QColor object or None if invalid
    """
    try:
        color = QColor(color_str)
        if color.isValid():
            return color
    except (TypeError, ValueError) as e:
        logger.debug(f"Invalid color string '{color_str}': {e}")

    return None


def color_to_hex(color: QColor) -> str:
    """Convert QColor to hex string.

    Args:
        color: QColor object

    Returns:
        Hex color string
    """
    return color.name()


def create_icon(icon_path: str, size: int = 32) -> QIcon:
    """Create QIcon from file path.

    Args:
        icon_path: Path to icon file
        size: Icon size

    Returns:
        QIcon object
    """
    icon = QIcon()

    if Path(icon_path).exists():
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon.addPixmap(pixmap.scaled(size, size, aspectRatioMode=1))

    return icon


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object.

    Args:
        dt: Datetime object
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime | None:
    """Parse datetime string.

    Args:
        dt_str: Datetime string
        format_str: Expected format

    Returns:
        Datetime object or None if parsing failed
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError:
        return None


def safe_cast(value: Any, target_type: type, default=None):
    """Safely cast value to target type.

    Args:
        value: Value to cast
        target_type: Target type
        default: Default value if casting fails

    Returns:
        Cast value or default
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max.

    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def normalize_path(path: str) -> str:
    """Normalize file path.

    Args:
        path: File path

    Returns:
        Normalized path
    """
    return str(Path(path).resolve())


def get_relative_path(file_path: str, base_path: str) -> str:
    """Get relative path from base path.

    Args:
        file_path: Target file path
        base_path: Base directory path

    Returns:
        Relative path
    """
    try:
        return str(Path(file_path).relative_to(Path(base_path)))
    except ValueError:
        return file_path


def create_backup_filename(original_path: str) -> str:
    """Create backup filename.

    Args:
        original_path: Original file path

    Returns:
        Backup file path
    """
    path = Path(original_path)
    timestamp = get_timestamp_string()
    return str(path.with_suffix(f".backup_{timestamp}{path.suffix}"))


def backup_file(file_path: str) -> bool:
    """Create backup of file.

    Args:
        file_path: File to backup

    Returns:
        True if backup created successfully
    """
    if not Path(file_path).exists():
        return False

    try:
        backup_path = create_backup_filename(file_path)
        import shutil

        shutil.copy2(file_path, backup_path)

        logging.getLogger(__name__).info(f"Created backup: {backup_path}")
        return True

    except OSError as e:
        logging.getLogger(__name__).error(f"Failed to create backup: {e}")
        return False


def find_files(directory: str, pattern: str = "*", recursive: bool = True) -> list[str]:
    """Find files matching pattern.

    Args:
        directory: Directory to search
        pattern: File pattern (glob style)
        recursive: Search recursively

    Returns:
        List of matching file paths
    """
    path = Path(directory)

    if not path.exists() or not path.is_dir():
        return []

    try:
        if recursive:
            files = path.rglob(pattern)
        else:
            files = path.glob(pattern)

        return [str(f) for f in files if f.is_file()]

    except OSError:
        return []


def get_file_info(file_path: str) -> dict[str, Any]:
    """Get file information.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information
    """
    path = Path(file_path)

    if not path.exists():
        return {}

    try:
        stat = path.stat()

        return {
            "name": path.name,
            "stem": path.stem,
            "suffix": path.suffix,
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "is_readable": os.access(file_path, os.R_OK),
            "is_writable": os.access(file_path, os.W_OK),
        }

    except OSError:
        return {"name": path.name}


def create_url_from_path(file_path: str) -> QUrl:
    """Create QUrl from file path.

    Args:
        file_path: File path

    Returns:
        QUrl object
    """
    return QUrl.fromLocalFile(str(Path(file_path).resolve()))


def extract_urls_from_mime(mime_data) -> list[str]:
    """Extract file paths from QMimeData.

    Args:
        mime_data: QMimeData object

    Returns:
        List of file paths
    """
    file_paths = []

    if mime_data.hasUrls():
        for url in mime_data.urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if Path(file_path).exists():
                    file_paths.append(file_path)

    return file_paths


def load_settings() -> QSettings:
    """Load application settings.

    Returns:
        QSettings object
    """
    return QSettings("Modan2Team", "Modan2")


def save_window_state(window, settings: QSettings):
    """Save window geometry and state.

    Args:
        window: Main window object
        settings: QSettings object
    """
    settings.setValue("geometry", window.saveGeometry())
    settings.setValue("windowState", window.saveState())

    # Save splitter states if they exist
    if hasattr(window, "hsplitter"):
        settings.setValue("hsplitter", window.hsplitter.saveState())
    if hasattr(window, "vsplitter"):
        settings.setValue("vsplitter", window.vsplitter.saveState())


def restore_window_state(window, settings: QSettings):
    """Restore window geometry and state.

    Args:
        window: Main window object
        settings: QSettings object
    """
    geometry = settings.value("geometry")
    if geometry:
        window.restoreGeometry(geometry)

    window_state = settings.value("windowState")
    if window_state:
        window.restoreState(window_state)

    # Restore splitter states
    hsplitter_state = settings.value("hsplitter")
    if hsplitter_state and hasattr(window, "hsplitter"):
        window.hsplitter.restoreState(hsplitter_state)

    vsplitter_state = settings.value("vsplitter")
    if vsplitter_state and hasattr(window, "vsplitter"):
        window.vsplitter.restoreState(vsplitter_state)


def is_dark_theme() -> bool:
    """Check if system is using dark theme.

    Returns:
        True if dark theme detected
    """
    try:
        app = QApplication.instance()
        if app:
            palette = app.palette()
            bg_color = palette.color(palette.Window)
            return bg_color.lightness() < 128
    except (RuntimeError, AttributeError) as e:
        logger.debug(f"Failed to detect dark theme: {e}")

    return False


def interpolate_color(color1: QColor, color2: QColor, factor: float) -> QColor:
    """Interpolate between two colors.

    Args:
        color1: First color
        color2: Second color
        factor: Interpolation factor (0.0 to 1.0)

    Returns:
        Interpolated color
    """
    factor = clamp(factor, 0.0, 1.0)

    r = int(color1.red() * (1 - factor) + color2.red() * factor)
    g = int(color1.green() * (1 - factor) + color2.green() * factor)
    b = int(color1.blue() * (1 - factor) + color2.blue() * factor)
    a = int(color1.alpha() * (1 - factor) + color2.alpha() * factor)

    return QColor(r, g, b, a)


def generate_unique_name(base_name: str, existing_names: list[str]) -> str:
    """Generate unique name by appending number if needed.

    Args:
        base_name: Base name
        existing_names: List of existing names

    Returns:
        Unique name
    """
    if base_name not in existing_names:
        return base_name

    counter = 1
    while f"{base_name}_{counter}" in existing_names:
        counter += 1

    return f"{base_name}_{counter}"


def chunk_list(lst: list, chunk_size: int) -> list[list]:
    """Split list into chunks.

    Args:
        lst: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: list[list]) -> list:
    """Flatten nested list.

    Args:
        nested_list: List of lists

    Returns:
        Flattened list
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def round_to_precision(value: float, precision: int) -> float:
    """Round value to specified precision.

    Args:
        value: Value to round
        precision: Number of decimal places

    Returns:
        Rounded value
    """
    return round(value, precision)


def format_number(value: int | float, precision: int = 6, scientific: bool = False) -> str:
    """Format number for display.

    Args:
        value: Number to format
        precision: Decimal places
        scientific: Use scientific notation

    Returns:
        Formatted number string
    """
    if scientific:
        return f"{value:.{precision}e}"
    else:
        return f"{value:.{precision}f}".rstrip("0").rstrip(".")


def calculate_centroid(points: list[list[float]]) -> list[float]:
    """Calculate centroid of points.

    Args:
        points: List of point coordinates

    Returns:
        Centroid coordinates
    """
    if not points:
        return []

    n_dims = len(points[0])
    centroid = [0.0] * n_dims

    for point in points:
        for i in range(n_dims):
            centroid[i] += point[i]

    for i in range(n_dims):
        centroid[i] /= len(points)

    return centroid


def calculate_distance(point1: list[float], point2: list[float]) -> float:
    """Calculate Euclidean distance between points.

    Args:
        point1: First point coordinates
        point2: Second point coordinates

    Returns:
        Euclidean distance
    """
    if len(point1) != len(point2):
        raise ValueError("Points must have same number of dimensions")

    return sum((a - b) ** 2 for a, b in zip(point1, point2)) ** 0.5


def calculate_bounding_box(points: list[list[float]]) -> tuple[list[float], list[float]]:
    """Calculate bounding box of points.

    Args:
        points: List of point coordinates

    Returns:
        Tuple of (min_coords, max_coords)
    """
    if not points:
        return [], []

    n_dims = len(points[0])
    min_coords = [float("inf")] * n_dims
    max_coords = [float("-inf")] * n_dims

    for point in points:
        for i in range(n_dims):
            min_coords[i] = min(min_coords[i], point[i])
            max_coords[i] = max(max_coords[i], point[i])

    return min_coords, max_coords


def scale_points(points: list[list[float]], scale_factor: float) -> list[list[float]]:
    """Scale points by factor.

    Args:
        points: List of point coordinates
        scale_factor: Scaling factor

    Returns:
        Scaled points
    """
    return [[coord * scale_factor for coord in point] for point in points]


def translate_points(points: list[list[float]], translation: list[float]) -> list[list[float]]:
    """Translate points by offset.

    Args:
        points: List of point coordinates
        translation: Translation vector

    Returns:
        Translated points
    """
    return [[point[i] + translation[i] for i in range(len(point))] for point in points]


def center_points(points: list[list[float]]) -> list[list[float]]:
    """Center points around their centroid.

    Args:
        points: List of point coordinates

    Returns:
        Centered points
    """
    centroid = calculate_centroid(points)
    translation = [-coord for coord in centroid]
    return translate_points(points, translation)


def get_system_info() -> dict[str, str]:
    """Get system information.

    Returns:
        Dictionary with system information
    """
    import platform
    import sys

    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "qt_version": "5.15.x",  # PyQt5 version
    }


def log_system_info():
    """Log system information for debugging."""
    logger = logging.getLogger(__name__)

    info = get_system_info()
    logger.info("System Information:")
    for key, value in info.items():
        logger.info(f"  {key}: {value}")


def check_dependencies() -> dict[str, bool]:
    """Check if all required dependencies are available.

    Returns:
        Dictionary with dependency availability
    """
    dependencies = {
        "PyQt5": False,
        "numpy": False,
        "pandas": False,
        "scipy": False,
        "opencv": False,
        "trimesh": False,
        "peewee": False,
        "matplotlib": False,
    }

    try:
        import PyQt5  # noqa: F401

        dependencies["PyQt5"] = True
    except ImportError:
        pass

    try:
        import numpy

        dependencies["numpy"] = True
    except ImportError:
        pass

    try:
        import pandas

        dependencies["pandas"] = True
    except ImportError:
        pass

    try:
        import scipy

        dependencies["scipy"] = True
    except ImportError:
        pass

    try:
        import cv2

        dependencies["opencv"] = True
    except ImportError:
        pass

    try:
        import trimesh

        dependencies["trimesh"] = True
    except ImportError:
        pass

    try:
        import peewee

        dependencies["peewee"] = True
    except ImportError:
        pass

    try:
        import matplotlib

        dependencies["matplotlib"] = True
    except ImportError:
        pass

    return dependencies


def memory_usage_mb() -> float:
    """Get current memory usage in MB.

    Returns:
        Memory usage in megabytes
    """
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def get_available_memory_mb() -> float:
    """Get available system memory in MB.

    Returns:
        Available memory in megabytes
    """
    try:
        import psutil

        return psutil.virtual_memory().available / 1024 / 1024
    except ImportError:
        return 0.0


def cleanup_resources():
    """Cleanup application resources."""
    logger = logging.getLogger(__name__)

    try:
        # Cleanup temporary files
        cleanup_temp_files()

        # Force garbage collection
        import gc

        gc.collect()

        logger.debug("Resources cleaned up")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


class ProgressReporter:
    """Helper class for reporting progress."""

    def __init__(self, callback=None, total_steps: int = 100):
        """Initialize progress reporter.

        Args:
            callback: Function to call with progress updates
            total_steps: Total number of steps
        """
        self.callback = callback
        self.total_steps = total_steps
        self.current_step = 0
        self.logger = logging.getLogger(__name__)

    def update(self, step: int = None, message: str = ""):
        """Update progress.

        Args:
            step: Current step number (or increment if None)
            message: Progress message
        """
        if step is not None:
            self.current_step = step
        else:
            self.current_step += 1

        percentage = int((self.current_step / self.total_steps) * 100)

        if self.callback:
            self.callback(percentage, message)

        if message:
            self.logger.debug(f"Progress {percentage}%: {message}")

    def finish(self, message: str = "Completed"):
        """Mark progress as finished.

        Args:
            message: Completion message
        """
        self.update(self.total_steps, message)


def debounce(wait_ms: int):
    """Decorator for debouncing function calls.

    Args:
        wait_ms: Wait time in milliseconds
    """

    def decorator(func):
        timer = None

        def wrapper(*args, **kwargs):
            nonlocal timer

            def call_func():
                func(*args, **kwargs)

            from PyQt5.QtCore import QTimer

            if timer:
                timer.stop()

            timer = QTimer()
            timer.timeout.connect(call_func)
            timer.setSingleShot(True)
            timer.start(wait_ms)

        return wrapper

    return decorator
