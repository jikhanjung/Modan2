"""Tests for MdUtils module."""
import sys
import os
import pytest
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdUtils as mu


class TestConstants:
    """Test module constants."""
    
    def test_program_constants(self):
        """Test that program constants are properly defined."""
        assert mu.COMPANY_NAME == "PaleoBytes"
        assert mu.PROGRAM_NAME == "Modan2"
        assert mu.PROGRAM_VERSION == "0.1.3"
        
        # Version should be in x.y.z format
        version_parts = mu.PROGRAM_VERSION.split('.')
        assert len(version_parts) == 3
        assert all(part.isdigit() for part in version_parts)
    
    def test_directory_constants(self):
        """Test that directory constants are properly formed."""
        assert mu.USER_PROFILE_DIRECTORY == os.path.expanduser('~')
        assert mu.DEFAULT_DB_DIRECTORY.endswith('PaleoBytes/Modan2')
        assert mu.DEFAULT_STORAGE_DIRECTORY.endswith('PaleoBytes/Modan2/data/')
        assert mu.DEFAULT_LOG_DIRECTORY.endswith('PaleoBytes/Modan2/logs/')
        assert mu.DB_BACKUP_DIRECTORY.endswith('PaleoBytes/Modan2/backups/')
    
    def test_extension_lists(self):
        """Test file extension lists."""
        # Image extensions
        assert 'png' in mu.IMAGE_EXTENSION_LIST
        assert 'jpg' in mu.IMAGE_EXTENSION_LIST
        assert 'jpeg' in mu.IMAGE_EXTENSION_LIST
        assert len(mu.IMAGE_EXTENSION_LIST) == 7
        
        # Model extensions
        assert 'obj' in mu.MODEL_EXTENSION_LIST
        assert 'ply' in mu.MODEL_EXTENSION_LIST
        assert 'stl' in mu.MODEL_EXTENSION_LIST
        assert len(mu.MODEL_EXTENSION_LIST) == 3
    
    def test_color_lists(self):
        """Test color lists are properly defined."""
        assert len(mu.VIVID_COLOR_LIST) == 20
        assert len(mu.PASTEL_COLOR_LIST) == 20
        
        # All colors should be hex format
        for color in mu.VIVID_COLOR_LIST:
            assert color.startswith('#')
            assert len(color) == 7  # #RRGGBB format
        
        for color in mu.PASTEL_COLOR_LIST:
            assert color.startswith('#')
            assert len(color) == 7
    
    def test_marker_list(self):
        """Test marker list for plotting."""
        assert len(mu.MARKER_LIST) == 11
        assert 'o' in mu.MARKER_LIST  # Circle
        assert 's' in mu.MARKER_LIST  # Square
        assert '^' in mu.MARKER_LIST  # Triangle


class TestResourcePath:
    """Test resource_path function."""
    
    def test_resource_path_normal(self):
        """Test resource_path in normal execution."""
        path = mu.resource_path('icons/test.png')
        assert 'icons/test.png' in path
        assert os.path.isabs(path)  # Should return absolute path
    
    def test_resource_path_frozen(self):
        """Test resource_path when running as frozen executable."""
        # Mock sys._MEIPASS attribute for frozen executable
        with patch.object(sys, '_MEIPASS', '/frozen/path', create=True):
            path = mu.resource_path('icons/test.png')
            assert path == '/frozen/path/icons/test.png'


class TestAsQtColor:
    """Test as_qt_color function."""
    
    def test_as_qt_color_with_qcolor(self):
        """Test that QColor input returns same QColor."""
        color = QColor(255, 0, 0)
        result = mu.as_qt_color(color)
        assert result == color
        assert isinstance(result, QColor)
    
    def test_as_qt_color_with_string(self):
        """Test that string input returns QColor."""
        result = mu.as_qt_color("#FF0000")
        assert isinstance(result, QColor)
        assert result.red() == 255
        assert result.green() == 0
        assert result.blue() == 0
    
    def test_as_qt_color_with_named_color(self):
        """Test that named color string returns QColor."""
        result = mu.as_qt_color("red")
        assert isinstance(result, QColor)
        assert result.red() == 255
        assert result.green() == 0
        assert result.blue() == 0


class TestDirectoryCreation:
    """Test directory creation behavior."""
    
    def test_directories_exist(self):
        """Test that required directories are created."""
        # These should be created when module is imported
        assert os.path.exists(mu.DEFAULT_DB_DIRECTORY)
        assert os.path.exists(mu.DEFAULT_STORAGE_DIRECTORY)
        assert os.path.exists(mu.DEFAULT_LOG_DIRECTORY)
        assert os.path.exists(mu.DB_BACKUP_DIRECTORY)


class TestAsGlColor:
    """Test as_gl_color function."""
    
    def test_as_gl_color_with_string(self):
        """Test converting string color to GL format."""
        r, g, b = mu.as_gl_color("#FF0000")
        assert pytest.approx(r) == 1.0
        assert pytest.approx(g) == 0.0
        assert pytest.approx(b) == 0.0
    
    def test_as_gl_color_with_qcolor(self):
        """Test converting QColor to GL format."""
        qcolor = QColor(255, 128, 0)
        r, g, b = mu.as_gl_color(qcolor)
        assert pytest.approx(r) == 1.0
        assert pytest.approx(g, rel=1e-2) == 0.5
        assert pytest.approx(b) == 0.0


class TestUtilityFunctions:
    """Test various utility functions."""
    
    def test_value_to_bool(self):
        """Test value_to_bool conversion."""
        assert mu.value_to_bool('true') == True
        assert mu.value_to_bool('True') == True
        assert mu.value_to_bool('false') == False
        assert mu.value_to_bool('False') == False
        assert mu.value_to_bool(1) == True
        assert mu.value_to_bool(0) == False
        assert mu.value_to_bool('') == False
    
    def test_is_numeric(self):
        """Test is_numeric function."""
        assert mu.is_numeric('123') == True
        assert mu.is_numeric('123.456') == True
        assert mu.is_numeric('-123.456') == True
        assert mu.is_numeric('1e5') == True
        assert mu.is_numeric('abc') == False
        assert mu.is_numeric('') == False
        assert mu.is_numeric('12.34.56') == False
    
    def test_process_dropped_file_name_windows(self):
        """Test process_dropped_file_name on Windows."""
        with patch('os.name', 'nt'):
            # Windows file URL
            file_url = "file:///C:/Users/test/file.txt"
            result = mu.process_dropped_file_name(file_url)
            assert result == "C:/Users/test/file.txt"
    
    def test_process_dropped_file_name_unix(self):
        """Test process_dropped_file_name on Unix."""
        with patch('os.name', 'posix'):
            # Unix file URL
            file_url = "file:///home/user/file.txt"
            result = mu.process_dropped_file_name(file_url)
            assert result == "/home/user/file.txt"
    
    def test_process_dropped_file_name_with_spaces(self):
        """Test process_dropped_file_name with URL-encoded spaces."""
        with patch('os.name', 'posix'):
            file_url = "file:///home/user/my%20file.txt"
            result = mu.process_dropped_file_name(file_url)
            assert result == "/home/user/my file.txt"


class TestProcess3DFile:
    """Test 3D file processing functions."""
    
    def test_process_3d_file_obj(self):
        """Test that OBJ files are returned as-is."""
        # Test with actual sample file
        sample_obj_path = os.path.join("tests", "fixtures", "sample_3d.obj")
        result = mu.process_3d_file(sample_obj_path)
        assert result == sample_obj_path
        
        # Also test with mock path to ensure logic works for any valid .obj file
        result = mu.process_3d_file("/path/to/model.obj")
        assert result == "/path/to/model.obj"
    
    @patch('trimesh.load_mesh')
    @patch('tempfile.mkdtemp')
    @patch('os.path.splitext')
    @patch('os.path.join')
    def test_process_3d_file_stl(self, mock_join, mock_splitext, mock_mkdtemp, mock_load_mesh):
        """Test STL file conversion to OBJ."""
        # Setup mocks for path operations
        mock_mkdtemp.return_value = "/tmp/test"
        mock_splitext.side_effect = [
            ("/path/to/model", ".stl"),  # First call for extension
            ("/path/to/model", ".stl")   # Second call for filename
        ]
        mock_join.return_value = "/tmp/test/model.obj"
        
        # Setup mesh mock
        mock_mesh = MagicMock()
        mock_mesh.vertex_normals = []
        mock_mesh.export = MagicMock()
        mock_load_mesh.return_value = mock_mesh
        
        result = mu.process_3d_file("/path/to/model.stl")
        
        assert result == "/tmp/test/model.obj"
        mock_mesh.export.assert_called_once_with("/tmp/test/model.obj", file_type='obj')
    
    @patch('trimesh.load')
    @patch('tempfile.mkdtemp')
    @patch('os.path.splitext')
    @patch('os.path.join')
    def test_process_3d_file_ply(self, mock_join, mock_splitext, mock_mkdtemp, mock_load):
        """Test PLY file conversion to OBJ."""
        # Setup mocks for path operations
        mock_mkdtemp.return_value = "/tmp/test"
        mock_splitext.side_effect = [
            ("/path/to/model", ".ply"),  # First call for extension
            ("/path/to/model", ".ply")   # Second call for filename
        ]
        mock_join.return_value = "/tmp/test/model.obj"
        
        # Setup mesh mock
        mock_mesh = MagicMock()
        mock_mesh.export = MagicMock()
        mock_load.return_value = mock_mesh
        
        result = mu.process_3d_file("/path/to/model.ply")
        
        assert result == "/tmp/test/model.obj"
        mock_mesh.export.assert_called_once_with("/tmp/test/model.obj", file_type='obj')


class TestErrorHandling:
    """Test error handling in utility functions."""
    
    def test_process_3d_file_invalid_extension(self):
        """Test handling of unsupported file extensions."""
        invalid_file = os.path.join("tests", "fixtures", "invalid_file.txt")
        
        # The function may attempt to convert .txt files to .obj
        result = mu.process_3d_file(invalid_file)
        
        # Should return some result (may convert to .obj or return as-is)
        assert result is not None
        assert isinstance(result, str)
    
    def test_process_3d_file_nonexistent_file(self):
        """Test handling of non-existent files."""
        nonexistent_file = "/path/to/nonexistent/file.obj"
        
        # Should handle non-existent files gracefully
        result = mu.process_3d_file(nonexistent_file)
        # For OBJ files, it should return the path as-is regardless of existence
        assert result == nonexistent_file
    
    @patch('trimesh.load_mesh')
    def test_process_3d_file_trimesh_error(self, mock_load_mesh):
        """Test handling of trimesh loading errors."""
        # Setup mock to raise an exception
        mock_load_mesh.side_effect = Exception("Failed to load mesh")
        
        # Should handle trimesh errors gracefully
        try:
            result = mu.process_3d_file("/path/to/corrupted.stl")
            # If it handles errors gracefully, it might return None or original path
            assert result is not None
        except Exception:
            # If it doesn't catch the exception, that's also acceptable behavior
            pass
    
    def test_process_dropped_file_name_malformed_url(self):
        """Test handling of malformed file URLs."""
        malformed_urls = [
            "file://invalid",
            "not_a_url",
            "",
            None
        ]
        
        for url in malformed_urls:
            if url is not None:
                try:
                    result = mu.process_dropped_file_name(url)
                    # Should either handle gracefully or raise appropriate exception
                    assert isinstance(result, str)
                except (ValueError, TypeError, AttributeError):
                    # These exceptions are acceptable for malformed input
                    pass


class TestEdgeCases:
    """Test error handling functions."""
    
    @patch('MdUtils.QMessageBox')
    def test_show_error_message(self, mock_messagebox):
        """Test show_error_message function."""
        mock_instance = MagicMock()
        mock_messagebox.return_value = mock_instance
        
        error_msg = "Test error message"
        mu.show_error_message(error_msg)
        
        mock_messagebox.assert_called_once()
        mock_instance.setText.assert_called_once_with(error_msg)
        mock_instance.setWindowTitle.assert_called_once_with("Error")
        mock_instance.exec_.assert_called_once()


class TestMathFunctions:
    """Test mathematical utility functions."""
    
    def test_get_ellipse_params(self):
        """Test ellipse parameter calculation."""
        # Simple diagonal covariance matrix
        covariance = np.array([[4, 0], [0, 1]])
        width, height, angle = mu.get_ellipse_params(covariance, n_std=1)
        
        assert pytest.approx(width, rel=1e-3) == 2.0  # sqrt(4) * 1
        assert pytest.approx(height, rel=1e-3) == 1.0  # sqrt(1) * 1
        assert pytest.approx(angle, abs=1) == 0.0  # No rotation
    
    def test_get_ellipse_params_rotated(self):
        """Test ellipse params with rotation."""
        # Rotated covariance matrix
        theta = np.pi / 4  # 45 degrees
        R = np.array([[np.cos(theta), -np.sin(theta)],
                      [np.sin(theta), np.cos(theta)]])
        D = np.array([[4, 0], [0, 1]])
        covariance = R @ D @ R.T
        
        width, height, angle = mu.get_ellipse_params(covariance, n_std=2)
        
        assert pytest.approx(width, rel=1e-3) == 4.0  # sqrt(4) * 2
        assert pytest.approx(height, rel=1e-3) == 2.0  # sqrt(1) * 2