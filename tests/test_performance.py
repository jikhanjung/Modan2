"""Performance tests for Modan2 - measure execution time and resource usage."""
import sys
import os
import pytest
import time
import gc
from unittest.mock import MagicMock

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdUtils as mu
import MdModel as mm
import MdStatistics as ms


# Mark all tests in this module as slow
pytestmark = pytest.mark.slow


class TestMdUtilsPerformance:
    """Performance tests for MdUtils functions."""
    
    def test_as_qt_color_performance(self):
        """Test performance of color conversion functions."""
        start_time = time.time()
        
        # Test with many color conversions
        colors = ["red", "green", "blue", "yellow", "cyan", "magenta"] * 100
        
        for color in colors:
            result = mu.as_qt_color(color)
            assert result is not None
        
        execution_time = time.time() - start_time
        print(f"\nColor conversion for {len(colors)} items: {execution_time:.4f} seconds")
        
        # Should complete reasonably quickly (adjust threshold as needed)
        assert execution_time < 1.0  # Should complete in less than 1 second
    
    def test_resource_path_performance(self):
        """Test performance of resource path generation."""
        start_time = time.time()
        
        # Test with many path generations
        paths = ["icons/test.png", "data/sample.txt", "config/settings.ini"] * 200
        
        for path in paths:
            result = mu.resource_path(path)
            assert result is not None
        
        execution_time = time.time() - start_time
        print(f"\nPath generation for {len(paths)} items: {execution_time:.4f} seconds")
        
        # Should complete very quickly
        assert execution_time < 0.5  # Should complete in less than 0.5 seconds


class TestMdModelPerformance:
    """Performance tests for database operations."""
    
    # Use the existing test database fixture from conftest.py
    
    def test_bulk_dataset_creation_performance(self, test_db_setup):
        """Test performance of creating many datasets."""
        start_time = time.time()
        dataset_count = 100
        
        datasets = []
        for i in range(dataset_count):
            dataset = mm.MdDataset.create(
                dataset_name=f"Performance Dataset {i}",
                dataset_desc=f"Description {i}",
                dimension=2
            )
            datasets.append(dataset)
        
        execution_time = time.time() - start_time
        print(f"\nCreated {dataset_count} datasets in: {execution_time:.4f} seconds")
        
        # Verify all were created
        assert len(datasets) == dataset_count
        assert mm.MdDataset.select().count() == dataset_count
        
        # Should complete reasonably quickly
        assert execution_time < 5.0  # Should complete in less than 5 seconds
    
    def test_bulk_object_creation_performance(self, test_db_setup):
        """Test performance of creating many objects."""
        # Create a parent dataset
        dataset = mm.MdDataset.create(dataset_name="Performance Parent")
        
        start_time = time.time()
        object_count = 500
        
        objects = []
        for i in range(object_count):
            obj = mm.MdObject.create(
                object_name=f"Performance Object {i}",
                dataset=dataset,
                sequence=i
            )
            objects.append(obj)
        
        execution_time = time.time() - start_time
        print(f"\nCreated {object_count} objects in: {execution_time:.4f} seconds")
        
        # Verify all were created
        assert len(objects) == object_count
        assert mm.MdObject.select().count() == object_count
        
        # Should complete reasonably quickly
        assert execution_time < 10.0  # Should complete in less than 10 seconds
    
    def test_large_landmark_processing_performance(self, test_db_setup):
        """Test performance of processing large landmark datasets."""
        dataset = mm.MdDataset.create(dataset_name="Large Landmark Dataset", dimension=2)
        obj = mm.MdObject.create(object_name="Large Landmark Object", dataset=dataset)
        
        # Create a large landmark dataset (1000 landmarks)
        large_landmarks = [[float(i), float(i+1)] for i in range(1000)]
        
        start_time = time.time()
        
        # Test packing performance
        obj.landmark_list = large_landmarks
        obj.pack_landmark()
        
        pack_time = time.time() - start_time
        print(f"\nPacked 1000 landmarks in: {pack_time:.4f} seconds")
        
        # Test unpacking performance
        start_time = time.time()
        obj.landmark_list = []
        obj.unpack_landmark()
        
        unpack_time = time.time() - start_time
        print(f"Unpacked 1000 landmarks in: {unpack_time:.4f} seconds")
        
        # Verify correctness
        assert len(obj.landmark_list) == 1000
        assert obj.landmark_list[0] == [0.0, 1.0]
        assert obj.landmark_list[999] == [999.0, 1000.0]
        
        # Performance assertions
        assert pack_time < 1.0  # Packing should be fast
        assert unpack_time < 1.0  # Unpacking should be fast


class TestMdStatisticsPerformance:
    """Performance tests for statistical analysis functions."""
    
    @pytest.fixture
    def large_dataset_for_pca(self):
        """Create a large dataset for PCA performance testing."""
        # Create 1000 observations with 10 variables each
        import numpy as np
        np.random.seed(42)  # For reproducible results
        
        n_observations = 1000
        n_variables = 10
        
        # Create correlated data for more realistic testing
        base_data = np.random.randn(n_observations, 3)
        data = []
        
        for i in range(n_observations):
            row = []
            for j in range(n_variables):
                # Create some correlation between variables
                value = base_data[i, j % 3] + np.random.randn() * 0.1
                row.append(value)
            data.append(row)
        
        return data
    
    def test_pca_performance_large_dataset(self, large_dataset_for_pca):
        """Test PCA performance with large dataset."""
        pca = ms.MdPrincipalComponent()
        pca.SetData(large_dataset_for_pca)
        
        start_time = time.time()
        result = pca.Analyze()
        execution_time = time.time() - start_time
        
        print(f"\nPCA analysis on 1000x10 dataset: {execution_time:.4f} seconds")
        
        # Verify success
        assert result == True
        assert hasattr(pca, 'raw_eigen_values')
        assert len(pca.raw_eigen_values) == 10
        
        # Performance assertion - should complete in reasonable time
        assert execution_time < 5.0  # Should complete in less than 5 seconds
    
    def test_cva_performance_large_dataset(self):
        """Test CVA performance with large dataset."""
        # Create large grouped dataset
        import numpy as np
        np.random.seed(42)
        
        # 500 observations per group, 2 groups, 5 variables
        group_size = 500
        n_variables = 5
        
        group1_data = [[i + np.random.randn() * 0.1 for i in range(n_variables)] 
                      for _ in range(group_size)]
        group2_data = [[i + 10 + np.random.randn() * 0.1 for i in range(n_variables)] 
                      for _ in range(group_size)]
        
        data = group1_data + group2_data
        categories = ['Group1'] * group_size + ['Group2'] * group_size
        
        cva = ms.MdCanonicalVariate()
        cva.SetData(data)
        cva.SetCategory(categories)
        
        start_time = time.time()
        result = cva.Analyze()
        execution_time = time.time() - start_time
        
        print(f"\nCVA analysis on 1000x5 dataset: {execution_time:.4f} seconds")
        
        # Verify success (CVA might return True or other success indicator)
        if result is not None:
            assert hasattr(cva, 'rotated_matrix')
        
        # Performance assertion
        assert execution_time < 10.0  # Should complete in less than 10 seconds


class TestMemoryUsage:
    """Tests for memory usage and garbage collection."""
    
    def test_memory_cleanup_after_large_operations(self):
        """Test that memory is properly cleaned up after large operations."""
        try:
            import psutil
            import os
            
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        # Perform memory-intensive operation
        dataset = mm.MdDataset.create(dataset_name="Memory Test")
        large_objects = []
        
        for i in range(100):
            obj = mm.MdObject.create(
                object_name=f"Memory Object {i}",
                dataset=dataset
            )
            # Add large landmark data
            obj.landmark_list = [[float(j), float(j+1)] for j in range(1000)]
            obj.pack_landmark()
            large_objects.append(obj)
        
        # Memory after operations
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Clean up references
        del large_objects
        gc.collect()
        
        # Memory after cleanup
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\nMemory usage - Initial: {initial_memory:.2f}MB, "
              f"Peak: {peak_memory:.2f}MB, Final: {final_memory:.2f}MB")
        
        # Memory should be significantly reduced after cleanup
        memory_reduction = peak_memory - final_memory
        assert memory_reduction > 0  # Should have freed some memory
        
        # Final memory shouldn't be too much higher than initial
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50  # Less than 50MB permanent increase


# Performance test configuration
def pytest_configure(config):
    """Configure pytest markers for performance tests."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )