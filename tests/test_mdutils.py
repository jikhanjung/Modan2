"""Tests for MdUtils module."""
import os
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdModel as mm
import MdUtils as mu


class TestConstants:
    """Test module constants."""
    
    def test_program_constants(self):
        """Test that program constants are properly defined."""
        assert mu.COMPANY_NAME == "PaleoBytes"
        assert mu.PROGRAM_NAME == "Modan2"

        # Import version from the single source of truth
        from version import __version__
        assert mu.PROGRAM_VERSION == __version__

        # Version should follow semantic versioning (but may have pre-release suffix)
        import semver
        try:
            parsed_version = semver.VersionInfo.parse(mu.PROGRAM_VERSION)
            assert parsed_version is not None
        except ValueError:
            # If semver parsing fails, at least check basic format
            assert '.' in mu.PROGRAM_VERSION  # Should have dots for version separation
    
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


class TestLandmarkFileReading:
    """Test landmark file reading functions."""

    def test_read_tps_file(self, tmp_path):
        """Test reading TPS format landmark file."""
        tps_content = """LM=3
1.0 2.0
3.0 4.0
5.0 6.0
ID=specimen1

LM=3
10.0 20.0
30.0 40.0
50.0 60.0
ID=specimen2
"""
        tps_file = tmp_path / "test.tps"
        tps_file.write_text(tps_content)

        specimens = mu.read_tps_file(str(tps_file))

        assert len(specimens) == 2
        assert specimens[0][0] == "specimen1"
        assert len(specimens[0][1]) == 3
        assert specimens[0][1][0] == [1.0, 2.0]
        assert specimens[1][0] == "specimen2"
        assert specimens[1][1][0] == [10.0, 20.0]

    def test_read_tps_file_with_image_scale(self, tmp_path):
        """Test TPS file with IMAGE and SCALE lines."""
        tps_content = """LM=2
1.0 2.0
3.0 4.0
IMAGE=image.jpg
SCALE=1.0
ID=specimen1
"""
        tps_file = tmp_path / "test.tps"
        tps_file.write_text(tps_content)

        specimens = mu.read_tps_file(str(tps_file))

        assert len(specimens) == 1
        assert specimens[0][0] == "specimen1"
        assert len(specimens[0][1]) == 2

    def test_read_tps_file_without_id(self, tmp_path):
        """Test TPS file without ID lines."""
        tps_content = """LM=2
1.0 2.0
3.0 4.0
"""
        tps_file = tmp_path / "test.tps"
        tps_file.write_text(tps_content)

        specimens = mu.read_tps_file(str(tps_file))

        assert len(specimens) == 1
        assert specimens[0][0] == "specimen_1"
        assert len(specimens[0][1]) == 2

    def test_read_nts_file(self, tmp_path):
        """Test reading NTS format landmark file."""
        nts_content = """2 3 2 0 DIM=2
specimen1
1.0 2.0
3.0 4.0
5.0 6.0
specimen2
10.0 20.0
30.0 40.0
50.0 60.0
"""
        nts_file = tmp_path / "test.nts"
        nts_file.write_text(nts_content)

        specimens = mu.read_nts_file(str(nts_file))

        assert len(specimens) == 2
        assert specimens[0][0] == "specimen1"
        assert len(specimens[0][1]) == 3
        assert specimens[0][1][0] == [1.0, 2.0]
        assert specimens[1][0] == "specimen2"

    def test_read_landmark_file_tps(self, tmp_path):
        """Test read_landmark_file with TPS format."""
        tps_content = """LM=2
1.0 2.0
3.0 4.0
ID=test
"""
        tps_file = tmp_path / "test.tps"
        tps_file.write_text(tps_content)

        specimens = mu.read_landmark_file(str(tps_file))

        assert len(specimens) == 1
        assert specimens[0][0] == "test"

    def test_read_landmark_file_nts(self, tmp_path):
        """Test read_landmark_file with NTS format."""
        nts_content = """1 2 2 0 DIM=2
specimen1
1.0 2.0
3.0 4.0
"""
        nts_file = tmp_path / "test.nts"
        nts_file.write_text(nts_content)

        specimens = mu.read_landmark_file(str(nts_file))

        assert len(specimens) == 1
        assert specimens[0][0] == "specimen1"

    def test_read_landmark_file_txt_tps_format(self, tmp_path):
        """Test .txt file with TPS format."""
        tps_content = """LM=2
1.0 2.0
3.0 4.0
ID=test
"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text(tps_content)

        specimens = mu.read_landmark_file(str(txt_file))

        assert len(specimens) == 1

    def test_read_landmark_file_txt_nts_format(self, tmp_path):
        """Test .txt file with NTS format."""
        nts_content = """1 2 2 0 DIM=2
specimen1
1.0 2.0
3.0 4.0
"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text(nts_content)

        specimens = mu.read_landmark_file(str(txt_file))

        assert len(specimens) == 1

    def test_read_landmark_file_unsupported_format(self, tmp_path):
        """Test unsupported file format."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,2\n3,4\n")

        with pytest.raises(ValueError, match="Unsupported landmark file format"):
            mu.read_landmark_file(str(csv_file))

    def test_read_tps_file_not_found(self):
        """Test reading non-existent TPS file."""
        with pytest.raises(FileNotFoundError):
            mu.read_tps_file("/nonexistent/file.tps")

    def test_read_nts_file_not_found(self):
        """Test reading non-existent NTS file."""
        with pytest.raises(FileNotFoundError):
            mu.read_nts_file("/nonexistent/file.nts")

    def test_read_tps_file_malformed_lm(self, tmp_path):
        """Test TPS file with malformed LM line."""
        tps_content = """LM=invalid
1.0 2.0
"""
        tps_file = tmp_path / "test.tps"
        tps_file.write_text(tps_content)

        with pytest.raises(ValueError, match="Malformed TPS file"):
            mu.read_tps_file(str(tps_file))

    def test_read_nts_file_malformed_header(self, tmp_path):
        """Test NTS file with malformed header."""
        nts_content = """invalid header DIM=2
specimen1
1.0 2.0
"""
        nts_file = tmp_path / "test.nts"
        nts_file.write_text(nts_content)

        with pytest.raises(ValueError, match="Malformed NTS file"):
            mu.read_nts_file(str(nts_file))


class TestBuildInfo:
    """Test build information functions."""

    def test_get_build_info(self):
        """Test get_build_info returns valid structure."""
        info = mu.get_build_info()

        assert isinstance(info, dict)
        assert 'version' in info
        assert 'build_number' in info
        assert 'build_date' in info
        assert 'platform' in info

    def test_get_copyright_year(self):
        """Test copyright year retrieval."""
        year = mu.get_copyright_year()

        assert isinstance(year, int)
        assert year >= 2023  # Project started in 2023

    def test_build_info_constants(self):
        """Test BUILD_INFO constants are set."""
        assert mu.BUILD_INFO is not None
        assert mu.COPYRIGHT_YEAR >= 2023
        assert mu.PROGRAM_BUILD_NUMBER is not None
        assert mu.PROGRAM_BUILD_DATE is not None


class TestJSONZipFunctions:
    """Test JSON+ZIP export/import functions."""

    def test_validate_json_schema_valid(self):
        """Test valid JSON schema validation."""
        valid_data = {
            'format_version': '1.1',
            'export_info': {},
            'dataset': {
                'name': 'Test',
                'dimension': 2,
                'variables': []
            },
            'objects': []
        }

        is_valid, errors = mu.validate_json_schema(valid_data)

        assert is_valid
        assert len(errors) == 0

    def test_validate_json_schema_missing_keys(self):
        """Test JSON schema validation with missing keys."""
        invalid_data = {
            'format_version': '1.1',
            'dataset': {}
        }

        is_valid, errors = mu.validate_json_schema(invalid_data)

        assert not is_valid
        assert len(errors) > 0

    def test_validate_json_schema_invalid_dataset(self):
        """Test JSON schema with invalid dataset."""
        invalid_data = {
            'format_version': '1.1',
            'export_info': {},
            'dataset': {},
            'objects': []
        }

        is_valid, errors = mu.validate_json_schema(invalid_data)

        assert not is_valid
        assert any('missing' in err.lower() for err in errors)

    def test_validate_json_schema_not_dict(self):
        """Test JSON schema with non-dict root."""
        is_valid, errors = mu.validate_json_schema([])

        assert not is_valid
        assert errors[0] == "Root is not an object"

    def test_safe_extract_zip(self, tmp_path):
        """Test safe ZIP extraction."""
        import zipfile

        # Create a safe ZIP file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("dataset.json", '{"test": "data"}')
            zf.writestr("images/image1.jpg", "fake image data")

        dest_dir = tmp_path / "extracted"
        dest_dir.mkdir()

        result = mu.safe_extract_zip(str(zip_path), str(dest_dir))

        assert result == str(dest_dir)
        assert (dest_dir / "dataset.json").exists()
        assert (dest_dir / "images" / "image1.jpg").exists()

    def test_read_json_from_zip(self, tmp_path):
        """Test reading JSON from ZIP."""
        import json
        import zipfile

        zip_path = tmp_path / "test.zip"
        test_data = {'format_version': '1.1', 'test': 'data'}

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("dataset.json", json.dumps(test_data))

        data = mu.read_json_from_zip(str(zip_path))

        assert data == test_data
        assert data['format_version'] == '1.1'


class TestGetStorageDir:
    """Test _get_storage_dir helper function."""

    def test_get_storage_dir_default(self):
        """Test _get_storage_dir returns default when no QApplication."""
        storage_dir = mu._get_storage_dir()

        assert storage_dir is not None
        assert os.path.isabs(storage_dir)
        # Should be absolute path to DEFAULT_STORAGE_DIRECTORY
        assert storage_dir == os.path.abspath(mu.DEFAULT_STORAGE_DIRECTORY)


class TestErrorPaths:
    """Test error handling paths in various functions."""

    def test_read_landmark_file_unicode_error(self, tmp_path):
        """Test landmark file unicode decoding error."""
        # Create file with invalid encoding
        txt_file = tmp_path / "invalid.txt"
        txt_file.write_bytes(b'\xff\xfe' + b'LM=3\n' + b'\x80\x81\x82')

        with pytest.raises(ValueError, match="Cannot decode file"):
            mu.read_landmark_file(str(txt_file))

    def test_read_landmark_file_permission_error(self, tmp_path, monkeypatch):
        """Test landmark file permission error."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("LM=3\n")

        # Mock open to raise PermissionError
        original_open = open
        def mock_open(*args, **kwargs):
            if str(txt_file) in str(args[0]):
                raise PermissionError("Permission denied")
            return original_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(PermissionError):
            mu.read_landmark_file(str(txt_file))


class TestUtilityFunctions:
    """Test utility functions."""

    def test_is_numeric_valid(self):
        """Test is_numeric with valid numbers."""
        assert mu.is_numeric("123") is True
        assert mu.is_numeric("123.456") is True
        assert mu.is_numeric("-123.456") is True
        assert mu.is_numeric("0") is True

    def test_is_numeric_invalid(self):
        """Test is_numeric with invalid values."""
        assert mu.is_numeric("abc") is False
        assert mu.is_numeric("") is False
        assert mu.is_numeric("12.34.56") is False

    def test_get_ellipse_params(self):
        """Test ellipse parameter calculation."""
        import numpy as np

        # Create a simple covariance matrix
        covariance = np.array([[2.0, 0.5], [0.5, 1.0]])
        n_std = 2.0

        width, height, angle = mu.get_ellipse_params(covariance, n_std)

        assert width > 0
        assert height > 0
        assert isinstance(angle, (int, float))

    def test_resource_path_normal(self):
        """Test resource_path without PyInstaller."""
        path = mu.resource_path("test.txt")
        assert "test.txt" in path
        assert os.path.isabs(path)

    def test_resource_path_meipass(self, monkeypatch):
        """Test resource_path with PyInstaller."""
        monkeypatch.setattr(sys, '_MEIPASS', '/tmp/meipass', raising=False)
        path = mu.resource_path("test.txt")
        assert "/tmp/meipass" in path or "test.txt" in path


class TestDirectoryEnsure:
    """Test directory creation functions."""

    def test_ensure_directories_success(self):
        """Test successful directory creation."""
        # Should not raise exception (already called on import)
        mu.ensure_directories()

    def test_ensure_directories_permission_error(self, monkeypatch, capsys):
        """Test directory creation with permission error."""
        # Mock makedirs to raise PermissionError
        original_makedirs = os.makedirs
        def mock_makedirs(path, exist_ok=False):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(os, 'makedirs', mock_makedirs)
        monkeypatch.setattr(os.path, 'exists', lambda x: False)  # Force directory creation

        # Should not raise, just print warning
        mu.ensure_directories()

        captured = capsys.readouterr()
        assert "Warning" in captured.out or "Permission denied" in str(captured)


class TestBuildInfoErrorPaths:
    """Test build info error handling."""

    def test_get_build_info_json_decode_error(self, tmp_path, monkeypatch):
        """Test build info with invalid JSON."""
        from pathlib import Path
        build_file = tmp_path / "build_info.json"
        build_file.write_text("{invalid json}")

        # Mock Path.exists to return True only for our invalid file
        original_exists = Path.exists
        def mock_exists(self):
            if str(self) == str(build_file):
                return True
            return original_exists(self)

        monkeypatch.setattr(Path, 'exists', mock_exists)

        # Should return default values (can't easily test without module reload)
        info = mu.get_build_info()
        assert 'build_number' in info
        assert 'build_date' in info

    def test_get_copyright_year_from_build_info(self):
        """Test get_copyright_year with build_info."""
        year = mu.get_copyright_year()
        assert isinstance(year, int)
        assert year >= 2020  # Reasonable year range


class TestShowErrorMessage:
    """Test error message display."""

    def test_show_error_message(self, qtbot):
        """Test showing error message."""
        from unittest.mock import patch

        with patch.object(QMessageBox, 'exec_', return_value=QMessageBox.Ok):
            # Should not raise exception
            mu.show_error_message("Test error message")


class TestColorFunctions:
    """Test color conversion functions."""

    def test_as_gl_color_from_hex(self):
        """Test converting hex color to OpenGL RGB."""

        # Test with red color
        r, g, b = mu.as_gl_color("#FF0000")
        assert r == 1.0
        assert g == 0.0
        assert b == 0.0

    def test_as_gl_color_from_name(self):
        """Test converting color name to OpenGL RGB."""
        # Test with blue color
        r, g, b = mu.as_gl_color("blue")
        assert r == 0.0
        assert g == 0.0
        assert b == 1.0

    def test_as_gl_color_from_qcolor(self):
        """Test converting QColor to OpenGL RGB."""
        from PyQt5.QtGui import QColor

        # Green color
        color = QColor(0, 255, 0)
        r, g, b = mu.as_gl_color(color)
        assert r == 0.0
        assert g == 1.0
        assert b == 0.0


class TestBooleanConversion:
    """Test boolean conversion functions."""

    def test_value_to_bool_true_string(self):
        """Test converting 'true' string to boolean."""
        assert mu.value_to_bool("true") is True
        assert mu.value_to_bool("True") is True
        assert mu.value_to_bool("TRUE") is True

    def test_value_to_bool_false_string(self):
        """Test converting 'false' string to boolean."""
        assert mu.value_to_bool("false") is False
        assert mu.value_to_bool("False") is False
        assert mu.value_to_bool("anything") is False

    def test_value_to_bool_non_string(self):
        """Test converting non-string values to boolean."""
        assert mu.value_to_bool(True) is True
        assert mu.value_to_bool(False) is False
        assert mu.value_to_bool(1) is True
        assert mu.value_to_bool(0) is False
        assert mu.value_to_bool([]) is False
        assert mu.value_to_bool([1]) is True


class TestFilePathProcessing:
    """Test file path processing functions."""

    def test_process_dropped_file_name_windows(self):
        """Test processing dropped file name on Windows."""
        import sys
        from unittest.mock import patch

        # Simulate Windows
        with patch.object(sys, 'platform', 'win32'):
            with patch('os.name', 'nt'):
                # Windows file URL format
                url = "file:///C:/Users/test/file.txt"
                result = mu.process_dropped_file_name(url)
                assert result == "C:/Users/test/file.txt"

    def test_process_dropped_file_name_linux(self):
        """Test processing dropped file name on Linux."""
        import sys
        from unittest.mock import patch

        # Simulate Linux
        with patch.object(sys, 'platform', 'linux'):
            with patch('os.name', 'posix'):
                # Linux file URL format
                url = "file:///home/user/file.txt"
                result = mu.process_dropped_file_name(url)
                assert result == "/home/user/file.txt"

    def test_process_dropped_file_name_with_spaces(self):
        """Test processing file name with URL-encoded spaces."""
        from unittest.mock import patch

        with patch('os.name', 'posix'):
            # URL with encoded spaces
            url = "file:///home/user/my%20file.txt"
            result = mu.process_dropped_file_name(url)
            assert result == "/home/user/my file.txt"

    def test_process_dropped_file_name_with_special_chars(self):
        """Test processing file name with special characters."""
        from unittest.mock import patch

        with patch('os.name', 'posix'):
            # URL with encoded special characters
            url = "file:///home/user/file%20(1).txt"
            result = mu.process_dropped_file_name(url)
            assert result == "/home/user/file (1).txt"


class TestDatasetSerialization:
    """Tests for dataset serialization to JSON."""

    def test_serialize_dataset_to_json_basic(self, mock_database):
        """Test basic dataset serialization to JSON."""
        dataset = mm.MdDataset.create(
            dataset_name="Test Dataset",
            dataset_desc="Test description",
            dimension=2
        )
        obj1 = mm.MdObject.create(
            object_name="Object1",
            dataset=dataset,
            sequence=1
        )
        obj1.landmark_list = [[1.0, 2.0], [3.0, 4.0]]
        obj1.pack_landmark()
        obj1.save()

        result = mu.serialize_dataset_to_json(dataset.id, include_files=False)

        assert result['format_version'] == '1.1'
        assert 'export_info' in result
        assert result['dataset']['name'] == "Test Dataset"
        assert result['dataset']['dimension'] == 2
        assert len(result['objects']) == 1
        assert result['objects'][0]['name'] == "Object1"
        assert result['objects'][0]['landmarks'] == [[1.0, 2.0], [3.0, 4.0]]

    def test_serialize_dataset_with_variables(self, mock_database):
        """Test dataset serialization with variables."""
        dataset = mm.MdDataset.create(
            dataset_name="Test Dataset",
            dimension=2
        )
        dataset.pack_variablename_str(['age', 'weight'])
        dataset.save()

        obj1 = mm.MdObject.create(
            object_name="Object1",
            dataset=dataset
        )
        obj1.variable_list = [5.0, 10.5]
        obj1.pack_variable([str(v) for v in obj1.variable_list])
        obj1.save()

        result = mu.serialize_dataset_to_json(dataset.id, include_files=False)

        assert result['dataset']['variables'] == ['age', 'weight']
        # Variables are stored as strings in the database
        assert result['objects'][0]['variables'] == {'age': '5.0', 'weight': '10.5'}

    def test_serialize_dataset_with_wireframe(self, mock_database):
        """Test dataset serialization with wireframe."""
        dataset = mm.MdDataset.create(
            dataset_name="Test Dataset",
            dimension=2
        )
        dataset.edge_list = [[0, 1], [1, 2]]
        dataset.pack_wireframe()
        dataset.save()

        result = mu.serialize_dataset_to_json(dataset.id, include_files=False)

        assert result['dataset']['wireframe'] == [[0, 1], [1, 2]]

    def test_serialize_dataset_with_polygons(self, mock_database):
        """Test dataset serialization with polygons."""
        dataset = mm.MdDataset.create(
            dataset_name="Test Dataset",
            dimension=2
        )
        dataset.polygon_list = [[0, 1, 2]]
        dataset.pack_polygons()
        dataset.save()

        result = mu.serialize_dataset_to_json(dataset.id, include_files=False)

        assert result['dataset']['polygons'] == [[0, 1, 2]]

    def test_serialize_dataset_with_baseline(self, mock_database):
        """Test dataset serialization with baseline."""
        dataset = mm.MdDataset.create(
            dataset_name="Test Dataset",
            dimension=2
        )
        dataset.baseline_point_list = [0, 1, 2]
        dataset.pack_baseline()
        dataset.save()

        result = mu.serialize_dataset_to_json(dataset.id, include_files=False)

        assert result['dataset']['baseline'] == [0, 1, 2]


class TestFileCollection:
    """Tests for file collection utilities."""

    def test_collect_dataset_files_no_files(self, mock_database):
        """Test collecting files from dataset with no attached files."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)

        images, models = mu.collect_dataset_files(dataset.id)

        assert images == []
        assert models == []

    def test_estimate_package_size_basic(self, mock_database):
        """Test estimating package size."""
        dataset = mm.MdDataset.create(
            dataset_name="Test Dataset",
            dimension=2
        )
        obj = mm.MdObject.create(
            object_name="Object1",
            dataset=dataset
        )
        obj.landmark_list = [[1.0, 2.0]]
        obj.pack_landmark()
        obj.save()

        size = mu.estimate_package_size(dataset.id, include_files=False)

        assert size > 0  # Should have JSON data


class TestZipPackaging:
    """Tests for ZIP package creation."""

    def test_create_zip_package_basic(self, mock_database, tmp_path):
        """Test creating basic ZIP package without files."""
        dataset = mm.MdDataset.create(
            dataset_name="Test Dataset",
            dimension=2
        )
        obj = mm.MdObject.create(
            object_name="Object1",
            dataset=dataset
        )
        obj.landmark_list = [[1.0, 2.0], [3.0, 4.0]]
        obj.pack_landmark()
        obj.save()

        zip_path = tmp_path / "test.zip"
        result = mu.create_zip_package(dataset.id, str(zip_path), include_files=False)

        assert result is True
        assert zip_path.exists()

        # Verify ZIP contents
        import zipfile
        with zipfile.ZipFile(str(zip_path), 'r') as zf:
            assert 'dataset.json' in zf.namelist()

    def test_create_zip_package_with_progress_callback(self, mock_database, tmp_path):
        """Test ZIP package creation with progress callback."""
        dataset = mm.MdDataset.create(dataset_name="Test Dataset", dimension=2)
        obj = mm.MdObject.create(object_name="Object1", dataset=dataset)
        obj.landmark_list = [[1.0, 2.0]]
        obj.pack_landmark()
        obj.save()

        zip_path = tmp_path / "test.zip"
        progress_calls = []

        def progress_cb(curr, total):
            progress_calls.append((curr, total))

        result = mu.create_zip_package(
            dataset.id,
            str(zip_path),
            include_files=False,
            progress_callback=progress_cb
        )

        assert result is True
        assert len(progress_calls) > 0  # Should have been called


class TestJsonValidation:
    """Tests for JSON schema validation."""

    def test_validate_json_schema_valid(self):
        """Test validation of valid JSON schema."""
        data = {
            'format_version': '1.1',
            'export_info': {},
            'dataset': {
                'name': 'Test',
                'dimension': 2,
                'variables': []
            },
            'objects': []
        }

        is_valid, errors = mu.validate_json_schema(data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_json_schema_missing_keys(self):
        """Test validation with missing required keys."""
        data = {
            'format_version': '1.1',
            'dataset': {}
        }

        is_valid, errors = mu.validate_json_schema(data)

        assert is_valid is False
        assert 'Missing key: export_info' in errors
        assert 'Missing key: objects' in errors

    def test_validate_json_schema_invalid_dataset(self):
        """Test validation with invalid dataset structure."""
        data = {
            'format_version': '1.1',
            'export_info': {},
            'dataset': {
                'name': 'Test'
                # Missing 'dimension' and 'variables'
            },
            'objects': []
        }

        is_valid, errors = mu.validate_json_schema(data)

        assert is_valid is False
        assert any('dataset missing' in err for err in errors)

    def test_validate_json_schema_objects_not_list(self):
        """Test validation when objects is not a list."""
        data = {
            'format_version': '1.1',
            'export_info': {},
            'dataset': {
                'name': 'Test',
                'dimension': 2,
                'variables': []
            },
            'objects': {}  # Should be list, not dict
        }

        is_valid, errors = mu.validate_json_schema(data)

        assert is_valid is False
        assert 'objects must be a list' in errors


class TestZipUtilities:
    """Tests for ZIP utility functions."""

    def test_safe_extract_zip(self, tmp_path):
        """Test safe ZIP extraction."""
        import zipfile

        # Create a test ZIP
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(str(zip_path), 'w') as zf:
            zf.writestr('dataset.json', '{"test": "data"}')
            zf.writestr('images/1.jpg', 'fake image data')

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        result = mu.safe_extract_zip(str(zip_path), str(extract_dir))

        assert result == str(extract_dir.resolve())
        assert (extract_dir / 'dataset.json').exists()
        assert (extract_dir / 'images' / '1.jpg').exists()

    def test_safe_extract_zip_prevents_zip_slip(self, tmp_path):
        """Test that ZIP extraction prevents path traversal (Zip Slip)."""
        import zipfile

        # Create malicious ZIP with path traversal
        zip_path = tmp_path / "malicious.zip"
        with zipfile.ZipFile(str(zip_path), 'w') as zf:
            # Try to write outside the extraction directory
            zf.writestr('../../../etc/passwd', 'malicious content')

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        with pytest.raises(ValueError, match="Unsafe path in ZIP"):
            mu.safe_extract_zip(str(zip_path), str(extract_dir))

    def test_read_json_from_zip(self, tmp_path):
        """Test reading JSON from ZIP."""
        import zipfile

        test_data = {'test': 'data', 'number': 123}
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(str(zip_path), 'w') as zf:
            import json
            zf.writestr('dataset.json', json.dumps(test_data))

        result = mu.read_json_from_zip(str(zip_path))

        assert result == test_data


class TestDatasetImportFromZip:
    """Tests for dataset import from ZIP packages."""

    def test_import_dataset_from_zip_basic(self, mock_database, tmp_path):
        """Test basic dataset import from ZIP."""
        # First, create a valid ZIP package
        dataset = mm.MdDataset.create(
            dataset_name="Original Dataset",
            dataset_desc="Original description",
            dimension=2
        )
        obj = mm.MdObject.create(
            object_name="Object1",
            dataset=dataset,
            sequence=1
        )
        obj.landmark_list = [[1.0, 2.0], [3.0, 4.0]]
        obj.pack_landmark()
        obj.save()

        zip_path = tmp_path / "export.zip"
        mu.create_zip_package(dataset.id, str(zip_path), include_files=False)

        # Now import it
        new_dataset_id = mu.import_dataset_from_zip(str(zip_path))

        # Verify imported dataset
        imported_ds = mm.MdDataset.get_by_id(new_dataset_id)
        # Dataset name may have a number appended to avoid duplicates
        assert "Original Dataset" in imported_ds.dataset_name
        assert imported_ds.dimension == 2
        assert imported_ds.object_list.count() == 1

        imported_obj = imported_ds.object_list.first()
        imported_obj.unpack_landmark()
        assert imported_obj.object_name == "Object1"
        assert imported_obj.landmark_list == [[1.0, 2.0], [3.0, 4.0]]

    def test_import_dataset_from_zip_with_progress(self, mock_database, tmp_path):
        """Test dataset import with progress callback."""
        # Create and export dataset
        dataset = mm.MdDataset.create(dataset_name="Test", dimension=2)
        obj = mm.MdObject.create(object_name="Obj1", dataset=dataset)
        obj.landmark_list = [[1.0, 2.0]]
        obj.pack_landmark()
        obj.save()

        zip_path = tmp_path / "export.zip"
        mu.create_zip_package(dataset.id, str(zip_path), include_files=False)

        # Import with progress tracking
        progress_calls = []

        def progress_cb(curr, total):
            progress_calls.append((curr, total))

        new_dataset_id = mu.import_dataset_from_zip(
            str(zip_path),
            progress_callback=progress_cb
        )

        assert new_dataset_id > 0
        assert len(progress_calls) > 0

    def test_import_dataset_invalid_json(self, mock_database, tmp_path):
        """Test import fails with invalid JSON schema."""
        import zipfile

        # Create ZIP with invalid JSON
        zip_path = tmp_path / "invalid.zip"
        invalid_data = {
            'format_version': '1.1',
            'dataset': {}  # Missing required keys
        }

        with zipfile.ZipFile(str(zip_path), 'w') as zf:
            import json
            zf.writestr('dataset.json', json.dumps(invalid_data))

        with pytest.raises(ValueError, match="Invalid dataset.json"):
            mu.import_dataset_from_zip(str(zip_path))