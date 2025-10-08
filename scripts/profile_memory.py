#!/usr/bin/env python3
"""Memory profiling for Modan2.

Tests memory usage patterns:
- Memory usage at scale
- Memory leak detection
- Long-running operation stability
- Object lifecycle memory management
"""

import gc
import sys
import tracemalloc
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import MdModel
from MdStatistics import do_cva_analysis, do_pca_analysis


def format_size(bytes_size):
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def setup_test_database():
    """Set up in-memory test database."""
    test_db = MdModel.SqliteDatabase(":memory:", pragmas={"foreign_keys": 1})
    models = [
        MdModel.MdDataset,
        MdModel.MdObject,
        MdModel.MdImage,
        MdModel.MdThreeDModel,
        MdModel.MdAnalysis,
    ]
    for model in models:
        model._meta.database = test_db
    test_db.create_tables(models)
    return test_db


def create_dataset(n_objects, n_landmarks, dimension=2):
    """Create test dataset."""
    dataset = MdModel.MdDataset.create(
        dataset_name=f"Memory_Test_{n_objects}_{n_landmarks}",
        dimension=dimension,
    )

    for i in range(n_objects):
        if dimension == 2:
            landmarks = [f"{(i + j) * 10.0}\t{(i + j) * 5.0}" for j in range(n_landmarks)]
        else:
            landmarks = [f"{(i + j) * 10.0}\t{(i + j) * 5.0}\t{(i + j) * 3.0}" for j in range(n_landmarks)]

        MdModel.MdObject.create(
            object_name=f"Object_{i:04d}",
            dataset=dataset,
            landmark_str="\n".join(landmarks),
            property_str=f"Group{i % 3}",
        )

    return dataset


def memory_snapshot():
    """Get current memory snapshot."""
    current, peak = tracemalloc.get_traced_memory()
    return {"current": current, "peak": peak}


def test_memory_usage_scaling():
    """Test memory usage scaling with dataset size."""
    print("=" * 70)
    print("Memory Usage Scaling Test")
    print("=" * 70)

    scenarios = [
        (100, 10, "Small"),
        (500, 10, "Medium"),
        (1000, 10, "Large"),
        (2000, 10, "Very Large"),
        (100, 100, "High-dimensional"),
    ]

    results = []

    for n_obj, n_lm, label in scenarios:
        print(f"\n{label}: {n_obj} objects × {n_lm} landmarks")

        # Start fresh
        gc.collect()
        tracemalloc.start()
        baseline = memory_snapshot()

        # Create dataset
        dataset = create_dataset(n_obj, n_lm)
        after_create = memory_snapshot()

        # Load objects
        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        after_load = memory_snapshot()

        # Run analysis
        landmarks = [obj.landmark_list for obj in objects]
        _ = do_pca_analysis(landmarks)
        after_pca = memory_snapshot()

        # Get stats
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Cleanup
        dataset.delete_instance()
        del dataset, objects, landmarks
        gc.collect()

        result = {
            "label": label,
            "objects": n_obj,
            "landmarks": n_lm,
            "baseline": baseline["current"],
            "after_create": after_create["current"] - baseline["current"],
            "after_load": after_load["current"] - baseline["current"],
            "after_pca": after_pca["current"] - baseline["current"],
            "peak": peak,
        }
        results.append(result)

        print(f"  After create:  {format_size(result['after_create'])}")
        print(f"  After load:    {format_size(result['after_load'])}")
        print(f"  After PCA:     {format_size(result['after_pca'])}")
        print(f"  Peak usage:    {format_size(result['peak'])}")

    # Summary table
    print("\n" + "=" * 70)
    print("Memory Usage Summary")
    print("=" * 70)
    print(f"{'Scenario':<20} {'Objects':>8} {'LM':>5} {'Create':>12} {'Load':>12} {'PCA':>12} {'Peak':>12}")
    print("-" * 70)

    for r in results:
        print(
            f"{r['label']:<20} {r['objects']:>8} {r['landmarks']:>5} "
            f"{format_size(r['after_create']):>12} {format_size(r['after_load']):>12} "
            f"{format_size(r['after_pca']):>12} {format_size(r['peak']):>12}"
        )

    return results


def test_memory_leak_detection():
    """Test for memory leaks with repeated operations."""
    print("\n" + "=" * 70)
    print("Memory Leak Detection Test")
    print("=" * 70)

    n_iterations = 50
    n_objects = 100
    n_landmarks = 10

    print(f"\nRunning {n_iterations} iterations of create-analyze-delete cycle")
    print(f"Dataset size: {n_objects} objects × {n_landmarks} landmarks\n")

    tracemalloc.start()
    baseline = memory_snapshot()

    memory_history = []

    for i in range(n_iterations):
        # Create dataset
        dataset = create_dataset(n_objects, n_landmarks)

        # Load and analyze
        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        landmarks = [obj.landmark_list for obj in objects]
        _ = do_pca_analysis(landmarks)

        # Delete dataset
        dataset.delete_instance()
        del dataset, objects, landmarks

        # Force garbage collection
        gc.collect()

        # Record memory
        snapshot = memory_snapshot()
        memory_history.append(snapshot["current"])

        if (i + 1) % 10 == 0:
            current_mem = snapshot["current"] - baseline["current"]
            print(f"  Iteration {i + 1:3d}: {format_size(current_mem)}")

    tracemalloc.stop()

    # Analyze trend
    print("\nMemory Trend Analysis:")
    early_avg = sum(memory_history[:10]) / 10
    late_avg = sum(memory_history[-10:]) / 10
    growth = late_avg - early_avg

    print(f"  Early average (iter 1-10):   {format_size(early_avg)}")
    print(f"  Late average (iter 41-50):   {format_size(late_avg)}")
    print(f"  Growth:                      {format_size(growth)}")

    if growth > 1024 * 1024:  # 1MB growth
        print(f"  ⚠️  WARNING: Possible memory leak detected ({format_size(growth)} growth)")
    else:
        print("  ✅ No significant memory leak detected")

    return memory_history


def test_long_running_operations():
    """Test memory stability during long-running operations."""
    print("\n" + "=" * 70)
    print("Long-Running Operations Test")
    print("=" * 70)

    print("\nSimulating sustained workload...")
    print("Creating and analyzing multiple large datasets sequentially\n")

    tracemalloc.start()
    baseline = memory_snapshot()

    operations = [
        (500, 10, "Large dataset 1"),
        (1000, 10, "Large dataset 2"),
        (500, 20, "High-dim dataset 1"),
        (1000, 20, "High-dim dataset 2"),
        (2000, 10, "Very large dataset"),
    ]

    for n_obj, n_lm, label in operations:
        print(f"{label}: {n_obj} obj × {n_lm} lm")

        # Create and analyze
        dataset = create_dataset(n_obj, n_lm)
        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        landmarks = [obj.landmark_list for obj in objects]

        _ = do_pca_analysis(landmarks)

        # CVA
        groups = [obj.property_str.split(",")[0] for obj in objects]
        _ = do_cva_analysis(landmarks, groups)

        # Check memory
        snapshot = memory_snapshot()
        current_mem = snapshot["current"] - baseline["current"]
        peak_mem = snapshot["peak"] - baseline["current"]

        print(f"  Current: {format_size(current_mem)}, Peak: {format_size(peak_mem)}")

        # Cleanup
        dataset.delete_instance()
        del dataset, objects, landmarks, groups
        gc.collect()

    final = memory_snapshot()
    tracemalloc.stop()

    final_mem = final["current"] - baseline["current"]
    peak_mem = final["peak"] - baseline["current"]

    print("\nFinal memory state:")
    print(f"  Final:  {format_size(final_mem)}")
    print(f"  Peak:   {format_size(peak_mem)}")

    if final_mem < 1024 * 1024:  # < 1MB final
        print("  ✅ Memory properly released")
    else:
        print(f"  ⚠️  Some memory retained ({format_size(final_mem)})")


def test_object_lifecycle():
    """Test memory management during object lifecycle."""
    print("\n" + "=" * 70)
    print("Object Lifecycle Memory Test")
    print("=" * 70)

    tracemalloc.start()
    baseline = memory_snapshot()

    # Create dataset
    print("\n1. Creating dataset...")
    dataset = create_dataset(100, 10)
    after_create = memory_snapshot()
    print(f"   Memory: {format_size(after_create['current'] - baseline['current'])}")

    # Load objects (lazy loading)
    print("\n2. Loading objects...")
    objects = list(dataset.object_list)
    after_load = memory_snapshot()
    print(f"   Memory: {format_size(after_load['current'] - baseline['current'])}")

    # Unpack landmarks
    print("\n3. Unpacking landmarks...")
    for obj in objects:
        obj.unpack_landmark()
    after_unpack = memory_snapshot()
    print(f"   Memory: {format_size(after_unpack['current'] - baseline['current'])}")

    # Analysis
    print("\n4. Running analysis...")
    landmarks = [obj.landmark_list for obj in objects]
    _ = do_pca_analysis(landmarks)
    after_analysis = memory_snapshot()
    print(f"   Memory: {format_size(after_analysis['current'] - baseline['current'])}")

    # Delete objects (but keep dataset)
    print("\n5. Deleting objects...")
    for obj in objects:
        obj.delete_instance()
    del objects, landmarks
    gc.collect()
    after_del_objects = memory_snapshot()
    print(f"   Memory: {format_size(after_del_objects['current'] - baseline['current'])}")

    # Delete dataset
    print("\n6. Deleting dataset...")
    dataset.delete_instance()
    del dataset
    gc.collect()
    after_del_dataset = memory_snapshot()
    print(f"   Memory: {format_size(after_del_dataset['current'] - baseline['current'])}")

    tracemalloc.stop()

    final_mem = after_del_dataset["current"] - baseline["current"]
    if final_mem < 100 * 1024:  # < 100KB
        print(f"\n✅ All memory properly released ({format_size(final_mem)} remaining)")
    else:
        print(f"\n⚠️  Some memory retained ({format_size(final_mem)})")


def main():
    """Run all memory profiling tests."""
    print("Modan2 Memory Profiling")
    print("=" * 70)

    # Setup database
    setup_test_database()

    # Run tests
    test_memory_usage_scaling()
    test_memory_leak_detection()
    test_long_running_operations()
    test_object_lifecycle()

    print("\n" + "=" * 70)
    print("Memory Profiling Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
