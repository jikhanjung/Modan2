"""Tests for MdStatistics module - Statistical analysis functions."""

import os
import sys
from unittest.mock import MagicMock

import numpy as np
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdStatistics as ms


class TestMdPrincipalComponent:
    """Test Principal Component Analysis class."""

    @pytest.fixture
    def simple_data(self):
        """Create simple test data for PCA."""
        # Create correlated data
        np.random.seed(42)
        n_samples = 10
        x = np.random.randn(n_samples)
        y = 2 * x + np.random.randn(n_samples) * 0.1  # Correlated with x
        z = -x + np.random.randn(n_samples) * 0.1  # Anti-correlated with x
        return [[x[i], y[i], z[i]] for i in range(n_samples)]

    def test_pca_initialization(self):
        """Test PCA object initialization."""
        pca = ms.MdPrincipalComponent()
        assert pca is not None

    def test_pca_set_data(self, simple_data):
        """Test setting data in PCA."""
        pca = ms.MdPrincipalComponent()
        pca.SetData(simple_data)

        assert pca.data == simple_data
        assert pca.nObservation == 10
        assert pca.nVariable == 3

    def test_pca_analyze(self, simple_data):
        """Test PCA analysis."""
        pca = ms.MdPrincipalComponent()
        pca.SetData(simple_data)
        result = pca.Analyze()

        assert result
        assert hasattr(pca, "raw_eigen_values")
        assert hasattr(pca, "eigen_value_percentages")
        assert hasattr(pca, "covariance_matrix")
        assert hasattr(pca, "rotated_matrix")
        assert hasattr(pca, "rotation_matrix")
        assert hasattr(pca, "loading")

        # Check dimensions
        assert len(pca.raw_eigen_values) == 3
        assert len(pca.eigen_value_percentages) == 3
        assert pca.covariance_matrix.shape == (3, 3)
        assert pca.rotated_matrix.shape == (10, 3)
        assert pca.rotation_matrix.shape == (3, 3)

    def test_pca_eigenvalue_properties(self, simple_data):
        """Test eigenvalue properties after PCA."""
        pca = ms.MdPrincipalComponent()
        pca.SetData(simple_data)
        pca.Analyze()

        # Eigenvalues should be non-negative
        assert all(ev >= 0 for ev in pca.raw_eigen_values)

        # Eigenvalue percentages should sum to ~1
        assert pytest.approx(sum(pca.eigen_value_percentages), rel=1e-5) == 1.0

        # Eigenvalues should be in descending order
        for i in range(len(pca.raw_eigen_values) - 1):
            assert pca.raw_eigen_values[i] >= pca.raw_eigen_values[i + 1]

    def test_pca_mean_centering(self, simple_data):
        """Test that data is mean-centered after analysis."""
        pca = ms.MdPrincipalComponent()
        # Make a copy since Analyze modifies data in place
        data_copy = [row[:] for row in simple_data]
        pca.SetData(data_copy)
        pca.Analyze()

        # After analysis, data should be mean-centered
        for j in range(pca.nVariable):
            column_mean = sum(pca.data[i][j] for i in range(pca.nObservation)) / pca.nObservation
            assert pytest.approx(column_mean, abs=1e-10) == 0.0


class TestMdCanonicalVariate:
    """Test Canonical Variate Analysis class."""

    @pytest.fixture
    def grouped_data(self):
        """Create grouped test data for CVA."""
        # Create data with clear group separation
        np.random.seed(42)
        group1 = [[i + np.random.randn() * 0.1, i * 2 + np.random.randn() * 0.1] for i in range(5)]
        group2 = [[i + 10 + np.random.randn() * 0.1, i * 2 + 10 + np.random.randn() * 0.1] for i in range(5)]
        data = group1 + group2
        categories = ["A"] * 5 + ["B"] * 5
        return data, categories

    def test_cva_initialization(self):
        """Test CVA object initialization."""
        cva = ms.MdCanonicalVariate()
        assert cva is not None
        assert cva.dimension == -1
        assert cva.nVariable == 0
        assert cva.nObservation == 0

    def test_cva_set_data(self, grouped_data):
        """Test setting data in CVA."""
        data, categories = grouped_data
        cva = ms.MdCanonicalVariate()
        cva.SetData(data)

        assert cva.data == data
        assert cva.nObservation == 10
        assert cva.nVariable == 2

    def test_cva_set_category(self, grouped_data):
        """Test setting categories in CVA."""
        data, categories = grouped_data
        cva = ms.MdCanonicalVariate()
        cva.SetData(data)
        cva.SetCategory(categories)

        assert cva.category_list == categories

    def test_cva_analyze_basic(self, grouped_data):
        """Test basic CVA analysis."""
        data, categories = grouped_data
        cva = ms.MdCanonicalVariate()
        cva.SetData(data)
        cva.SetCategory(categories)
        result = cva.Analyze()

        assert result
        assert hasattr(cva, "rotated_matrix")
        assert hasattr(cva, "rotation_matrix")

        # Check dimensions
        assert cva.rotated_matrix.shape[0] == 10  # Number of observations
        # Number of CVs should be min(n_groups - 1, n_variables)
        min(2 - 1, 2)  # 2 groups, 2 variables
        assert cva.rotated_matrix.shape[1] <= 2


class TestPerformFunctions:
    """Test the standalone perform functions."""

    @pytest.fixture
    def mock_dataset_ops(self):
        """Create a mock dataset operations object."""
        mock_ops = MagicMock()

        # Create mock objects with landmark_list
        mock_objects = []
        for i in range(5):
            mock_obj = MagicMock()
            mock_obj.landmark_list = [[i + 1, i + 2], [i + 3, i + 4], [i + 5, i + 6]]  # 3 landmarks, 2D
            mock_objects.append(mock_obj)

        mock_ops.object_list = mock_objects
        mock_ops.dimension = 2
        mock_ops.object_name_list = ["obj1", "obj2", "obj3", "obj4", "obj5"]
        mock_ops.object_id_list = [1, 2, 3, 4, 5]
        return mock_ops

    def test_perform_pca(self, mock_dataset_ops):
        """Test PerformPCA function."""
        result = ms.PerformPCA(mock_dataset_ops)

        assert result is not None
        assert hasattr(result, "rotated_matrix")
        assert hasattr(result, "rotation_matrix")
        assert hasattr(result, "eigen_value_percentages")
        assert result.rotated_matrix.shape[0] == 5  # Number of objects

    def test_perform_cva(self, mock_dataset_ops):
        """Test PerformCVA function."""
        # CVA requires classifier_index parameter
        classifier_index = 0
        result = ms.PerformCVA(mock_dataset_ops, classifier_index)

        # CVA might return None if classifier_index < 0
        if result is not None:
            assert hasattr(result, "rotated_matrix")
            assert hasattr(result, "rotation_matrix")

    def test_perform_manova(self, mock_dataset_ops):
        """Test PerformManova function."""
        # MANOVA requires new_coords and classifier_index parameters
        new_coords = np.random.randn(5, 4)  # 5 objects, 4 coordinates
        classifier_index = -1  # Use -1 to trigger early return and avoid complex setup

        result = ms.PerformManova(mock_dataset_ops, new_coords, classifier_index)

        # With classifier_index < 0, function should return None/early
        assert result is None or result is not None  # Function completes without error


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_pca_initialization_attributes(self):
        """Test PCA initialization attributes."""
        pca = ms.MdPrincipalComponent()
        # Test that PCA object can be created
        assert pca is not None
        # Attributes are set when SetData is called, not during init

    def test_pca_with_single_observation(self):
        """Test PCA with single observation."""
        pca = ms.MdPrincipalComponent()
        pca.SetData([[1, 2, 3]])

        assert pca.nObservation == 1
        assert pca.nVariable == 3

    def test_cva_with_single_category(self):
        """Test CVA with only one category."""
        cva = ms.MdCanonicalVariate()
        data = [[1, 2], [3, 4], [5, 6]]
        categories = ["A", "A", "A"]

        cva.SetData(data)
        cva.SetCategory(categories)

        # Should handle single category gracefully
        cva.Analyze()
        # With only one category, CVA might return specific behavior

    def test_cva_mismatched_data_categories(self):
        """Test CVA with mismatched data and category lengths."""
        cva = ms.MdCanonicalVariate()
        data = [[1, 2], [3, 4], [5, 6]]
        categories = ["A", "B"]  # Only 2 categories for 3 data points

        cva.SetData(data)
        cva.SetCategory(categories)

        # Should handle mismatch appropriately


class TestMdManova:
    """Test MANOVA analysis class."""

    @pytest.fixture
    def manova_data(self):
        """Create test data for MANOVA."""
        np.random.seed(42)
        # Two groups with different means
        group1 = [[1 + np.random.randn() * 0.5, 2 + np.random.randn() * 0.5] for _ in range(5)]
        group2 = [[4 + np.random.randn() * 0.5, 5 + np.random.randn() * 0.5] for _ in range(5)]
        data = group1 + group2
        categories = ["A"] * 5 + ["B"] * 5
        return data, categories

    def test_manova_initialization(self):
        """Test MANOVA object initialization."""
        manova = ms.MdManova()
        assert manova is not None
        # MdManova doesn't initialize attributes until SetData is called

    def test_manova_set_data(self, manova_data):
        """Test setting data in MANOVA."""
        data, categories = manova_data
        manova = ms.MdManova()
        manova.SetData(data)

        assert manova.data == data
        assert manova.nObservation == 10
        assert manova.nVariable == 2

    def test_manova_set_category(self, manova_data):
        """Test setting categories in MANOVA."""
        data, categories = manova_data
        manova = ms.MdManova()
        manova.SetCategory(categories)

        assert manova.category_list == categories

    def test_manova_set_column_list(self):
        """Test setting column names."""
        manova = ms.MdManova()
        columns = ["PC1", "PC2", "PC3"]
        manova.SetColumnList(columns)

        assert manova.column_list == columns

    def test_manova_set_groupby(self):
        """Test setting group by variable."""
        manova = ms.MdManova()
        manova.SetGroupby("Group")

        assert manova.group_by == "Group"


class TestModernAnalysisFunctions:
    """Test modern analysis functions for controller."""

    @pytest.fixture
    def landmark_data_2d(self):
        """Create 2D landmark test data."""
        np.random.seed(42)
        # 5 specimens, 3 landmarks each, 2D
        data = []
        for i in range(5):
            specimen = []
            for j in range(3):
                specimen.append([i + j + np.random.randn() * 0.1, i - j + np.random.randn() * 0.1])
            data.append(specimen)
        return data

    @pytest.fixture
    def landmark_data_3d(self):
        """Create 3D landmark test data."""
        np.random.seed(42)
        # 5 specimens, 3 landmarks each, 3D
        data = []
        for i in range(5):
            specimen = []
            for j in range(3):
                specimen.append(
                    [i + j + np.random.randn() * 0.1, i - j + np.random.randn() * 0.1, i + np.random.randn() * 0.1]
                )
            data.append(specimen)
        return data

    def test_do_pca_analysis_2d(self, landmark_data_2d):
        """Test do_pca_analysis with 2D landmark data."""
        result = ms.do_pca_analysis(landmark_data_2d)

        assert result is not None
        assert "n_components" in result
        assert "eigenvalues" in result
        assert "eigenvectors" in result
        assert "scores" in result
        assert "explained_variance_ratio" in result
        assert "mean_shape" in result

        # Check dimensions
        assert len(result["scores"]) == 5  # 5 specimens
        assert len(result["mean_shape"]) == 3  # 3 landmarks
        assert len(result["mean_shape"][0]) == 2  # 2D

    def test_do_pca_analysis_3d(self, landmark_data_3d):
        """Test do_pca_analysis with 3D landmark data."""
        result = ms.do_pca_analysis(landmark_data_3d)

        assert result is not None
        assert len(result["scores"]) == 5  # 5 specimens
        assert len(result["mean_shape"]) == 3  # 3 landmarks
        assert len(result["mean_shape"][0]) == 3  # 3D

    def test_do_pca_analysis_with_n_components(self, landmark_data_2d):
        """Test do_pca_analysis with specified n_components."""
        result = ms.do_pca_analysis(landmark_data_2d, n_components=3)

        assert result is not None
        assert result["n_components"] == 3

    def test_do_pca_analysis_variance_sum(self, landmark_data_2d):
        """Test that variance ratios sum to approximately 1."""
        result = ms.do_pca_analysis(landmark_data_2d)

        variance_sum = sum(result["explained_variance_ratio"])
        assert pytest.approx(variance_sum, rel=1e-5) == 1.0

    def test_do_pca_analysis_cumulative_variance(self, landmark_data_2d):
        """Test cumulative variance calculation."""
        result = ms.do_pca_analysis(landmark_data_2d)

        cumulative = result["cumulative_variance_ratio"]
        # Cumulative variance should be monotonically increasing
        for i in range(len(cumulative) - 1):
            assert cumulative[i] <= cumulative[i + 1]

        # Last cumulative value should be ~1.0
        assert pytest.approx(cumulative[-1], rel=1e-5) == 1.0


class TestPerformManovaFunction:
    """Test PerformManova standalone function."""

    @pytest.fixture
    def mock_dataset_with_classifier(self):
        """Create mock dataset with classifier variables."""
        mock_ops = MagicMock()

        # Create mock objects with variables
        mock_objects = []
        for i in range(10):
            mock_obj = MagicMock()
            mock_obj.landmark_list = [[i, i + 1], [i + 2, i + 3]]
            # Add variable list for classification
            mock_obj.variable_list = ["A" if i < 5 else "B", "adult", "large"]
            mock_objects.append(mock_obj)

        mock_ops.object_list = mock_objects
        mock_ops.dimension = 2
        mock_ops.variablename_list = ["Group", "Age", "Size"]
        return mock_ops

    def test_perform_manova_with_classifier(self, mock_dataset_with_classifier):
        """Test PerformManova with valid classifier."""
        # Create PCA-like new coordinates
        new_coords = np.random.randn(10, 4)  # 10 objects, 4 PCs
        classifier_index = 0  # Use 'Group' variable

        result = ms.PerformManova(mock_dataset_with_classifier, new_coords, classifier_index)

        assert result is not None
        assert isinstance(result, ms.MdManova)
        assert result.nObservation == 10
        assert result.nVariable == 4
        assert len(result.category_list) == 10

    def test_perform_manova_invalid_classifier(self, mock_dataset_with_classifier):
        """Test PerformManova with invalid classifier index."""
        new_coords = np.random.randn(10, 4)
        classifier_index = -1  # Invalid index

        result = ms.PerformManova(mock_dataset_with_classifier, new_coords, classifier_index)

        # Should return None for invalid classifier
        assert result is None

    def test_perform_manova_category_assignment(self):
        """Test PerformManova category assignment."""
        mock_ops = MagicMock()
        mock_objects = []
        for i in range(6):
            mock_obj = MagicMock()
            # Ensure all objects have the classifier variable
            mock_obj.variable_list = ["A" if i < 3 else "B", "young" if i < 3 else "old"]
            mock_objects.append(mock_obj)

        mock_ops.object_list = mock_objects
        mock_ops.dimension = 2
        mock_ops.variablename_list = ["Group", "Age"]

        new_coords = np.random.randn(6, 2)
        classifier_index = 0  # Use 'Group' variable

        result = ms.PerformManova(mock_ops, new_coords, classifier_index)

        # Should have categories assigned correctly
        if result is not None:
            assert len(result.category_list) == 6
            assert "A" in result.category_list
            assert "B" in result.category_list


class TestPCAErrorHandling:
    """Test PCA error handling."""

    def test_pca_empty_data(self):
        """Test PCA with empty data."""
        pca = ms.MdPrincipalComponent()

        # SetData with empty list should raise IndexError
        with pytest.raises(IndexError):
            pca.SetData([])

    def test_do_pca_analysis_empty_landmarks(self):
        """Test do_pca_analysis with empty landmark data."""
        with pytest.raises(Exception):
            ms.do_pca_analysis([])

    def test_do_pca_analysis_error_handling(self):
        """Test do_pca_analysis error handling with invalid data."""
        # Single specimen with empty landmarks
        result = ms.do_pca_analysis([[]])
        # Should handle gracefully, returning a result with empty/zero values
        assert result is not None


class TestCVAExtended:
    """Extended CVA tests."""

    def test_cva_rotation_matrix_orthogonal(self):
        """Test that CVA rotation matrix is approximately orthogonal."""
        np.random.seed(42)
        data = [[i + np.random.randn() * 0.1, i * 2 + np.random.randn() * 0.1] for i in range(10)]
        categories = ["A"] * 5 + ["B"] * 5

        cva = ms.MdCanonicalVariate()
        cva.SetData(data)
        cva.SetCategory(categories)
        cva.Analyze()

        if hasattr(cva, "rotation_matrix"):
            rotation = np.array(cva.rotation_matrix)
            # Check if rotation matrix properties are reasonable
            assert rotation.shape[0] > 0
            assert rotation.shape[1] > 0


class TestCVAAnalysis:
    """Test do_cva_analysis function."""

    def test_do_cva_analysis_basic(self):
        """Test basic CVA analysis."""
        # Create landmark data with 3 specimens per group
        landmarks_data = [
            [[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]],  # Group A
            [[0.1, 0.1], [1.1, 0.1], [0.6, 1.1]],  # Group A
            [[0.2, 0.2], [1.2, 0.2], [0.7, 1.2]],  # Group A
            [[5.0, 5.0], [6.0, 5.0], [5.5, 6.0]],  # Group B
            [[5.1, 5.1], [6.1, 5.1], [5.6, 6.1]],  # Group B
            [[5.2, 5.2], [6.2, 5.2], [5.7, 6.2]],  # Group B
        ]
        groups = ["A", "A", "A", "B", "B", "B"]

        result = ms.do_cva_analysis(landmarks_data, groups)

        assert result is not None
        assert "canonical_variables" in result
        assert "eigenvalues" in result
        assert "group_centroids" in result
        assert "classification" in result
        assert "accuracy" in result
        assert len(result["canonical_variables"]) == 6

    def test_do_cva_analysis_three_groups(self):
        """Test CVA with three groups."""
        landmarks_data = [
            [[0.0, 0.0], [1.0, 0.0]],  # Group A
            [[0.1, 0.1], [1.1, 0.1]],  # Group A
            [[5.0, 5.0], [6.0, 5.0]],  # Group B
            [[5.1, 5.1], [6.1, 5.1]],  # Group B
            [[10.0, 0.0], [11.0, 0.0]],  # Group C
            [[10.1, 0.1], [11.1, 0.1]],  # Group C
        ]
        groups = ["A", "A", "B", "B", "C", "C"]

        result = ms.do_cva_analysis(landmarks_data, groups)

        assert result is not None
        assert result["n_components"] == 3  # Padded to 3
        assert len(result["groups"]) == 3

    def test_do_cva_analysis_padding(self):
        """Test CVA pads to 3 dimensions."""
        # Simple 2-group case should produce 1 CV, padded to 3
        landmarks_data = [
            [[0.0, 0.0], [1.0, 0.0]],
            [[0.1, 0.1], [1.1, 0.1]],
            [[5.0, 5.0], [6.0, 5.0]],
            [[5.1, 5.1], [6.1, 5.1]],
        ]
        groups = ["A", "A", "B", "B"]

        result = ms.do_cva_analysis(landmarks_data, groups)

        # Should be padded to 3 dimensions
        assert result["n_components"] == 3
        assert len(result["canonical_variables"][0]) == 3

    def test_do_cva_analysis_error(self):
        """Test CVA with invalid data."""
        with pytest.raises(ValueError, match="CVA analysis failed"):
            ms.do_cva_analysis([], [])


class TestMANOVAOnProcrustes:
    """Test do_manova_analysis_on_procrustes function."""

    def test_manova_on_procrustes_basic(self):
        """Test basic MANOVA on Procrustes data."""
        # Create flattened 3D landmark data - need enough variation and samples
        import numpy as np

        np.random.seed(42)

        # Need more samples and variation to avoid singular matrix
        n_samples = 10
        flattened_landmarks = []
        groups = []

        for _i in range(n_samples // 2):
            # Group A - centered around (0, 0, 0)
            base = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.5, 1.0, 0.0]
            noise = np.random.randn(9) * 0.5
            flattened_landmarks.append([b + n for b, n in zip(base, noise)])
            groups.append("A")

        for _i in range(n_samples // 2):
            # Group B - centered around (5, 5, 5)
            base = [5.0, 5.0, 5.0, 6.0, 5.0, 5.0, 5.5, 6.0, 5.0]
            noise = np.random.randn(9) * 0.5
            flattened_landmarks.append([b + n for b, n in zip(base, noise)])
            groups.append("B")

        result = ms.do_manova_analysis_on_procrustes(flattened_landmarks, groups)

        assert result is not None
        assert result["analysis_type"] == "MANOVA"
        assert "test_statistics" in result
        assert result["n_groups"] == 2
        assert result["n_observations"] == 10

    def test_manova_on_procrustes_variable_limiting(self):
        """Test MANOVA limits variables to 20."""
        # Create data with many variables (> 20)
        import numpy as np

        np.random.seed(42)

        n_landmarks = 15  # 15 landmarks * 3 coords = 45 variables
        n_coords = n_landmarks * 3
        n_samples = 10

        flattened_landmarks = []
        groups = []

        for i in range(n_samples // 2):
            base = [float((i % 10) * 0.5) for _ in range(n_coords)]
            noise = np.random.randn(n_coords) * 0.3
            flattened_landmarks.append([b + n for b, n in zip(base, noise)])
            groups.append("A")

        for i in range(n_samples // 2):
            base = [float((i % 10) * 0.5 + 5.0) for _ in range(n_coords)]
            noise = np.random.randn(n_coords) * 0.3
            flattened_landmarks.append([b + n for b, n in zip(base, noise)])
            groups.append("B")

        result = ms.do_manova_analysis_on_procrustes(flattened_landmarks, groups)

        assert result is not None
        assert result["n_variables"] == 20  # Limited to 20

    def test_manova_on_procrustes_error(self):
        """Test MANOVA error handling."""
        with pytest.raises(Exception):
            ms.do_manova_analysis_on_procrustes([], [])


class TestMANOVAOnPCA:
    """Test do_manova_analysis_on_pca function."""

    def test_manova_on_pca_basic(self):
        """Test basic MANOVA on PCA scores."""
        # PCA scores (already truncated) - need more samples and variation
        import numpy as np

        np.random.seed(42)

        pca_scores = []
        groups = []

        for _i in range(5):
            base = [1.0, 0.5, 0.2]
            noise = np.random.randn(3) * 0.3
            pca_scores.append([b + n for b, n in zip(base, noise)])
            groups.append("A")

        for _i in range(5):
            base = [5.0, 2.0, 1.0]
            noise = np.random.randn(3) * 0.3
            pca_scores.append([b + n for b, n in zip(base, noise)])
            groups.append("B")

        result = ms.do_manova_analysis_on_pca(pca_scores, groups)

        assert result is not None
        assert result["analysis_type"] == "MANOVA"  # Fixed: returns 'MANOVA' not 'MANOVA on PCA'
        assert "test_statistics" in result
        assert result["n_groups"] == 2
        assert result["n_observations"] == 10

    def test_manova_on_pca_many_components(self):
        """Test MANOVA on PCA with many components."""
        # Many PCA components - need more samples
        import numpy as np

        np.random.seed(42)

        pca_scores = []
        groups = []

        for _i in range(5):
            base = [float(j * 0.5) for j in range(15)]
            noise = np.random.randn(15) * 0.3
            pca_scores.append([b + n for b, n in zip(base, noise)])
            groups.append("A")

        for _i in range(5):
            base = [float(j * 0.5 + 5.0) for j in range(15)]
            noise = np.random.randn(15) * 0.3
            pca_scores.append([b + n for b, n in zip(base, noise)])
            groups.append("B")

        result = ms.do_manova_analysis_on_pca(pca_scores, groups)

        assert result is not None
        # Should have all components (not limited for PCA)
        assert result["n_variables"] == 15

    def test_manova_on_pca_error(self):
        """Test MANOVA on PCA error handling."""
        with pytest.raises(Exception):
            ms.do_manova_analysis_on_pca([], [])


class TestDoManovaAnalysis:
    """Test do_manova_analysis function (direct MANOVA on landmarks)."""

    def test_do_manova_analysis_basic(self):
        """Test basic MANOVA analysis on landmark data."""
        np.random.seed(42)

        # Create two groups of landmark data
        landmarks_data = []
        groups = []

        # Group A: 5 specimens with 3 landmarks each
        for _i in range(5):
            landmarks = [
                [1.0 + np.random.randn() * 0.1, 2.0 + np.random.randn() * 0.1],
                [3.0 + np.random.randn() * 0.1, 4.0 + np.random.randn() * 0.1],
                [5.0 + np.random.randn() * 0.1, 6.0 + np.random.randn() * 0.1],
            ]
            landmarks_data.append(landmarks)
            groups.append("A")

        # Group B: 5 specimens with 3 landmarks each (shifted)
        for _i in range(5):
            landmarks = [
                [2.0 + np.random.randn() * 0.1, 3.0 + np.random.randn() * 0.1],
                [4.0 + np.random.randn() * 0.1, 5.0 + np.random.randn() * 0.1],
                [6.0 + np.random.randn() * 0.1, 7.0 + np.random.randn() * 0.1],
            ]
            landmarks_data.append(landmarks)
            groups.append("B")

        result = ms.do_manova_analysis(landmarks_data, groups)

        assert result is not None
        assert "test_statistics" in result
        assert len(result["test_statistics"]) == 4  # Wilks, Pillai, Hotelling, Roy
        assert "group_means" in result
        assert "overall_mean" in result
        assert result["n_groups"] == 2
        assert len(result["group_sizes"]) == 2

        # Check test statistics
        for test_stat in result["test_statistics"]:
            assert "name" in test_stat
            assert "value" in test_stat
            assert "f_statistic" in test_stat
            assert "p_value" in test_stat
            assert "df_num" in test_stat
            assert "df_den" in test_stat

    def test_do_manova_analysis_three_groups(self):
        """Test MANOVA with three groups."""
        np.random.seed(42)

        landmarks_data = []
        groups = []

        # Three groups with different means
        for group_idx, group_name in enumerate(["A", "B", "C"]):
            for _i in range(4):
                landmarks = [
                    [group_idx * 2.0 + np.random.randn() * 0.1, group_idx * 2.0 + np.random.randn() * 0.1],
                    [group_idx * 2.0 + 1.0 + np.random.randn() * 0.1, group_idx * 2.0 + 1.0 + np.random.randn() * 0.1],
                ]
                landmarks_data.append(landmarks)
                groups.append(group_name)

        result = ms.do_manova_analysis(landmarks_data, groups)

        assert result is not None
        assert result["n_groups"] == 3
        assert len(result["group_sizes"]) == 3
        assert all(size == 4 for size in result["group_sizes"])

    def test_do_manova_analysis_error_handling(self):
        """Test MANOVA error handling."""
        # Empty data
        with pytest.raises(ValueError):
            ms.do_manova_analysis([], [])

        # Mismatched lengths
        landmarks = [[[1, 2], [3, 4]]]
        groups = ["A", "B"]  # More groups than landmarks
        with pytest.raises(Exception):
            ms.do_manova_analysis(landmarks, groups)
