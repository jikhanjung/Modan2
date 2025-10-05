"""Tests for MdConstants module."""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdConstants as mc


class TestConstants:
    """Test constant definitions."""

    def test_app_info_constants(self):
        """Test application information constants."""
        assert mc.APP_NAME == "Modan2"
        assert mc.APP_AUTHOR == "Modan2 Team"
        assert mc.APP_LICENSE == "MIT"
        assert mc.APP_URL.startswith("https://github.com")

    def test_version_info(self):
        """Test version information."""
        assert isinstance(mc.APP_VERSION, str)
        assert len(mc.APP_VERSION) > 0
        assert mc.VERSION_INFO["full"] == mc.APP_VERSION


class TestPathConstants:
    """Test path constants."""

    def test_path_types(self):
        """Test that paths are Path objects."""
        assert isinstance(mc.BASE_DIR, Path)
        assert isinstance(mc.ICONS_DIR, Path)
        assert isinstance(mc.TRANSLATIONS_DIR, Path)
        assert isinstance(mc.CONFIG_DIR, Path)
        assert isinstance(mc.TEMP_DIR, Path)

    def test_base_dir_exists(self):
        """Test BASE_DIR points to project root."""
        assert mc.BASE_DIR.exists()
        assert mc.BASE_DIR.is_dir()


class TestIconMappings:
    """Test icon mappings."""

    def test_icons_dict(self):
        """Test ICONS dictionary."""
        assert isinstance(mc.ICONS, dict)
        assert len(mc.ICONS) > 0

        # Test some key icons exist
        assert "new_dataset" in mc.ICONS
        assert "import" in mc.ICONS
        assert "analysis" in mc.ICONS
        assert "app_icon" in mc.ICONS


class TestFileFilters:
    """Test file filter constants."""

    def test_file_filters_dict(self):
        """Test FILE_FILTERS dictionary."""
        assert isinstance(mc.FILE_FILTERS, dict)

        # Test key filters exist
        assert "landmark" in mc.FILE_FILTERS
        assert "image" in mc.FILE_FILTERS
        assert "3d_model" in mc.FILE_FILTERS
        assert "csv" in mc.FILE_FILTERS

    def test_filter_format(self):
        """Test filter strings are properly formatted."""
        for _filter_name, filter_str in mc.FILE_FILTERS.items():
            assert isinstance(filter_str, str)
            assert len(filter_str) > 0


class TestDefaultSettings:
    """Test default settings."""

    def test_default_settings_dict(self):
        """Test DEFAULT_SETTINGS dictionary."""
        assert isinstance(mc.DEFAULT_SETTINGS, dict)
        assert len(mc.DEFAULT_SETTINGS) > 0

        # Test critical settings exist
        assert "language" in mc.DEFAULT_SETTINGS
        assert "theme" in mc.DEFAULT_SETTINGS
        assert "auto_save" in mc.DEFAULT_SETTINGS

    def test_setting_types(self):
        """Test default setting types."""
        assert isinstance(mc.DEFAULT_SETTINGS["auto_save"], bool)
        assert isinstance(mc.DEFAULT_SETTINGS["auto_save_interval"], int)
        assert isinstance(mc.DEFAULT_SETTINGS["max_recent_files"], int)


class TestAnalysisTypes:
    """Test analysis type configurations."""

    def test_analysis_types_list(self):
        """Test ANALYSIS_TYPES is a list."""
        assert isinstance(mc.ANALYSIS_TYPES, list)
        assert len(mc.ANALYSIS_TYPES) > 0

    def test_analysis_type_structure(self):
        """Test each analysis type has required fields."""
        for analysis in mc.ANALYSIS_TYPES:
            assert "name" in analysis
            assert "display_name" in analysis
            assert "description" in analysis
            assert "min_objects" in analysis
            assert "supports_2d" in analysis
            assert "supports_3d" in analysis

    def test_analysis_names(self):
        """Test expected analysis types exist."""
        names = [a["name"] for a in mc.ANALYSIS_TYPES]
        assert "PCA" in names
        assert "CVA" in names
        assert "MANOVA" in names
        assert "PROCRUSTES" in names


class TestSupportedExtensions:
    """Test supported file extensions."""

    def test_extensions_dict(self):
        """Test SUPPORTED_EXTENSIONS dictionary."""
        assert isinstance(mc.SUPPORTED_EXTENSIONS, dict)

        # Test categories exist
        assert "landmark" in mc.SUPPORTED_EXTENSIONS
        assert "image" in mc.SUPPORTED_EXTENSIONS
        assert "3d_model" in mc.SUPPORTED_EXTENSIONS

    def test_all_supported_extensions(self):
        """Test ALL_SUPPORTED_EXTENSIONS list."""
        assert isinstance(mc.ALL_SUPPORTED_EXTENSIONS, list)
        assert len(mc.ALL_SUPPORTED_EXTENSIONS) > 0

        # Test includes extensions from different categories
        assert ".tps" in mc.ALL_SUPPORTED_EXTENSIONS
        assert ".jpg" in mc.ALL_SUPPORTED_EXTENSIONS or ".jpeg" in mc.ALL_SUPPORTED_EXTENSIONS
        assert ".obj" in mc.ALL_SUPPORTED_EXTENSIONS


class TestMessages:
    """Test message constants."""

    def test_error_messages(self):
        """Test ERROR_MESSAGES dictionary."""
        assert isinstance(mc.ERROR_MESSAGES, dict)
        assert len(mc.ERROR_MESSAGES) > 0
        assert "no_dataset" in mc.ERROR_MESSAGES
        assert "invalid_file" in mc.ERROR_MESSAGES

    def test_warning_messages(self):
        """Test WARNING_MESSAGES dictionary."""
        assert isinstance(mc.WARNING_MESSAGES, dict)
        assert len(mc.WARNING_MESSAGES) > 0
        assert "unsaved_changes" in mc.WARNING_MESSAGES

    def test_info_messages(self):
        """Test INFO_MESSAGES dictionary."""
        assert isinstance(mc.INFO_MESSAGES, dict)
        assert len(mc.INFO_MESSAGES) > 0
        assert "dataset_created" in mc.INFO_MESSAGES


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_icon_path(self):
        """Test get_icon_path function."""
        # Test valid icon
        path = mc.get_icon_path("app_icon")
        assert isinstance(path, str)
        assert len(path) > 0

        # Test invalid icon
        path = mc.get_icon_path("nonexistent_icon")
        assert path == ""

    def test_get_file_filter(self):
        """Test get_file_filter function."""
        # Test valid filter
        filter_str = mc.get_file_filter("landmark")
        assert isinstance(filter_str, str)
        assert len(filter_str) > 0
        assert "tps" in filter_str.lower() or "TPS" in filter_str

        # Test invalid filter
        filter_str = mc.get_file_filter("nonexistent_filter")
        assert filter_str == "All Files (*.*)"

    def test_get_analysis_info(self):
        """Test get_analysis_info function."""
        # Test valid analysis
        info = mc.get_analysis_info("PCA")
        assert isinstance(info, dict)
        assert info["name"] == "PCA"
        assert "display_name" in info

        # Test case insensitivity
        info = mc.get_analysis_info("pca")
        assert isinstance(info, dict)
        assert info["name"] == "PCA"

        # Test invalid analysis
        info = mc.get_analysis_info("INVALID_ANALYSIS")
        assert isinstance(info, dict)
        assert len(info) == 0

    def test_is_supported_file(self):
        """Test is_supported_file function."""
        # Test supported files
        assert mc.is_supported_file("test.tps")
        assert mc.is_supported_file("test.nts")
        assert mc.is_supported_file("test.jpg")
        assert mc.is_supported_file("test.obj")

        # Test case insensitivity
        assert mc.is_supported_file("TEST.TPS")
        assert mc.is_supported_file("TEST.JPG")

        # Test unsupported files
        assert not mc.is_supported_file("test.xyz")
        assert not mc.is_supported_file("test.doc")

        # Test with path
        assert mc.is_supported_file("/path/to/file.tps")
        assert not mc.is_supported_file("/path/to/file.unknown")

    def test_get_file_category(self):
        """Test get_file_category function."""
        # Test landmark files
        assert mc.get_file_category("test.tps") == "landmark"
        assert mc.get_file_category("test.nts") == "landmark"

        # Test image files
        category = mc.get_file_category("test.jpg")
        assert category == "image"

        # Test 3D model files
        category = mc.get_file_category("test.obj")
        assert category == "3d_model"

        # Test case insensitivity
        assert mc.get_file_category("TEST.TPS") == "landmark"

        # Test unknown files
        assert mc.get_file_category("test.xyz") == "unknown"
        assert mc.get_file_category("test.doc") == "unknown"

        # Test with paths
        assert mc.get_file_category("/path/to/file.tps") == "landmark"


class TestValidationConstants:
    """Test validation constants."""

    def test_validation_dict(self):
        """Test VALIDATION dictionary."""
        assert isinstance(mc.VALIDATION, dict)
        assert mc.VALIDATION["min_landmarks"] >= 3
        assert mc.VALIDATION["min_objects_for_pca"] >= 2
        assert mc.VALIDATION["min_objects_for_cva"] >= 6


class TestDatabaseConstants:
    """Test database constants."""

    def test_database_dict(self):
        """Test DATABASE dictionary."""
        assert isinstance(mc.DATABASE, dict)
        assert "default_name" in mc.DATABASE
        assert mc.DATABASE["default_name"] == "modan2.db"


class TestExportFormats:
    """Test export format configurations."""

    def test_export_formats_dict(self):
        """Test EXPORT_FORMATS dictionary."""
        assert isinstance(mc.EXPORT_FORMATS, dict)
        assert "csv" in mc.EXPORT_FORMATS
        assert "excel" in mc.EXPORT_FORMATS

    def test_export_format_structure(self):
        """Test each export format has required fields."""
        for _format_name, format_info in mc.EXPORT_FORMATS.items():
            assert "name" in format_info
            assert "extension" in format_info
            assert "supports_landmarks" in format_info
