#!/usr/bin/env python3
"""Large-scale performance benchmarking for Modan2.

Tests application performance with large datasets:
- 500, 1000, 2000, 5000 objects
- Various landmark counts
- Memory usage tracking
- Analysis performance
"""

import json
import sys
import time
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


def format_time(seconds):
    """Format seconds to human-readable time."""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds / 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def create_large_dataset(n_objects, n_landmarks, dimension=2):
    """Create a large test dataset.

    Args:
        n_objects: Number of objects
        n_landmarks: Number of landmarks per object
        dimension: 2D or 3D

    Returns:
        MdDataset instance
    """
    print(f"  Creating dataset: {n_objects} objects, {n_landmarks} landmarks ({dimension}D)...")

    # Create dataset
    dataset = MdModel.MdDataset.create(
        dataset_name=f"Benchmark_{n_objects}obj_{n_landmarks}lm",
        dataset_desc=f"Performance test: {n_objects} objects, {n_landmarks} landmarks",
        dimension=dimension,
    )

    # Generate landmarks (simple pattern for speed)
    start_time = time.perf_counter()

    for obj_idx in range(n_objects):
        # Create landmark coordinates
        if dimension == 2:
            landmarks = [f"{(obj_idx + i) * 10.0}\t{(obj_idx + i) * 5.0}" for i in range(n_landmarks)]
        else:  # 3D
            landmarks = [
                f"{(obj_idx + i) * 10.0}\t{(obj_idx + i) * 5.0}\t{(obj_idx + i) * 3.0}" for i in range(n_landmarks)
            ]

        landmark_str = "\n".join(landmarks)

        # Create object with group label for CVA
        group = f"Group{obj_idx % 3}"  # 3 groups
        MdModel.MdObject.create(
            object_name=f"Object_{obj_idx:04d}",
            dataset=dataset,
            landmark_str=landmark_str,
            property_str=group,
        )

        # Progress indicator
        if (obj_idx + 1) % 100 == 0:
            print(f"    Created {obj_idx + 1}/{n_objects} objects...", end="\r")

    creation_time = time.perf_counter() - start_time
    print(f"    Dataset creation: {format_time(creation_time)}" + " " * 30)

    return dataset


def benchmark_dataset_operations(dataset):
    """Benchmark basic dataset operations.

    Args:
        dataset: MdDataset instance

    Returns:
        dict with benchmark results
    """
    results = {}

    # Count objects
    start_time = time.perf_counter()
    _ = dataset.object_list.count()
    results["count_objects"] = time.perf_counter() - start_time

    # Load all objects
    start_time = time.perf_counter()
    objects = list(dataset.object_list)
    results["load_objects"] = time.perf_counter() - start_time

    # Unpack landmarks
    start_time = time.perf_counter()
    for obj in objects:
        obj.unpack_landmark()
    results["unpack_landmarks"] = time.perf_counter() - start_time

    # Get landmark list
    start_time = time.perf_counter()
    landmarks = [obj.landmark_list for obj in objects]
    results["get_landmark_list"] = time.perf_counter() - start_time

    return results, landmarks, objects


def benchmark_analysis(landmarks, objects):
    """Benchmark analysis operations.

    Args:
        landmarks: List of landmark arrays
        objects: List of MdObject instances

    Returns:
        dict with benchmark results
    """
    results = {}

    # PCA
    print("  Benchmarking PCA...")
    start_time = time.perf_counter()
    try:
        _ = do_pca_analysis(landmarks)
        results["pca"] = time.perf_counter() - start_time
    except Exception as e:
        print(f"    PCA failed: {e}")
        results["pca"] = None

    # CVA (with groups)
    print("  Benchmarking CVA...")
    groups = [obj.property_str.split(",")[0] if obj.property_str else "Group0" for obj in objects]
    start_time = time.perf_counter()
    try:
        _ = do_cva_analysis(landmarks, groups)
        results["cva"] = time.perf_counter() - start_time
    except Exception as e:
        print(f"    CVA failed: {e}")
        results["cva"] = None

    return results


def benchmark_scenario(n_objects, n_landmarks, dimension=2):
    """Benchmark a single scenario.

    Args:
        n_objects: Number of objects
        n_landmarks: Number of landmarks
        dimension: 2D or 3D

    Returns:
        dict with all benchmark results
    """
    print(f"\n{'=' * 70}")
    print(f"Scenario: {n_objects} objects × {n_landmarks} landmarks ({dimension}D)")
    print("=" * 70)

    # Track memory
    tracemalloc.start()
    initial_memory = tracemalloc.get_traced_memory()[0]

    results = {
        "n_objects": n_objects,
        "n_landmarks": n_landmarks,
        "dimension": dimension,
    }

    # Create dataset
    dataset = create_large_dataset(n_objects, n_landmarks, dimension)
    after_creation_memory = tracemalloc.get_traced_memory()[0]
    results["memory_dataset_creation"] = after_creation_memory - initial_memory

    # Benchmark operations
    print("  Benchmarking dataset operations...")
    ops_results, landmarks, objects = benchmark_dataset_operations(dataset)
    results.update(ops_results)

    after_ops_memory = tracemalloc.get_traced_memory()[0]
    results["memory_after_ops"] = after_ops_memory - initial_memory

    # Benchmark analysis
    analysis_results = benchmark_analysis(landmarks, objects)
    results.update(analysis_results)

    # Final memory
    peak_memory, current_memory = tracemalloc.get_traced_memory()
    results["memory_peak"] = peak_memory - initial_memory
    results["memory_final"] = current_memory - initial_memory

    tracemalloc.stop()

    # Cleanup
    dataset.delete_instance()

    # Print results
    print("\n  Results:")
    print("    Dataset Operations:")
    print(f"      Count objects:     {format_time(results['count_objects'])}")
    print(f"      Load objects:      {format_time(results['load_objects'])}")
    print(f"      Unpack landmarks:  {format_time(results['unpack_landmarks'])}")
    print(f"      Get landmark list: {format_time(results['get_landmark_list'])}")
    print("    Analysis:")
    if results["pca"] is not None:
        print(f"      PCA:               {format_time(results['pca'])}")
    else:
        print("      PCA:               FAILED")
    if results["cva"] is not None:
        print(f"      CVA:               {format_time(results['cva'])}")
    else:
        print("      CVA:               FAILED")
    print("    Memory:")
    print(f"      Dataset creation:  {format_size(results['memory_dataset_creation'])}")
    print(f"      After operations:  {format_size(results['memory_after_ops'])}")
    print(f"      Peak usage:        {format_size(results['memory_peak'])}")
    print(f"      Final usage:       {format_size(results['memory_final'])}")

    return results


def main():
    """Run large-scale benchmarks."""
    print("Modan2 Large-Scale Performance Benchmarks")
    print("=" * 70)

    # Setup in-memory database for testing
    test_db = MdModel.SqliteDatabase(":memory:", pragmas={"foreign_keys": 1})

    # Update all model classes to use test database
    models = [MdModel.MdDataset, MdModel.MdObject, MdModel.MdImage, MdModel.MdThreeDModel, MdModel.MdAnalysis]
    for model in models:
        model._meta.database = test_db

    # Create tables
    test_db.create_tables(models)

    all_results = []

    # Scenario 1: Many objects, few landmarks
    scenarios = [
        # (objects, landmarks, dimension)
        (500, 10, 2),  # Medium-large
        (1000, 10, 2),  # Large
        (2000, 10, 2),  # Very large
        # (5000, 5, 2),   # Extreme (uncomment if needed)
    ]

    for n_objects, n_landmarks, dimension in scenarios:
        try:
            result = benchmark_scenario(n_objects, n_landmarks, dimension)
            all_results.append(result)
        except KeyboardInterrupt:
            print("\n\nBenchmark interrupted by user.")
            break
        except Exception as e:
            print(f"\nERROR in scenario ({n_objects}obj, {n_landmarks}lm): {e}")
            import traceback

            traceback.print_exc()

    # Scenario 2: Few objects, many landmarks
    print(f"\n{'=' * 70}")
    print("High-dimensional scenarios (many landmarks)")
    print("=" * 70)

    high_dim_scenarios = [
        (100, 100, 2),  # 100 landmarks
        (50, 200, 2),  # 200 landmarks
        # (20, 500, 2),   # 500 landmarks (uncomment if needed)
    ]

    for n_objects, n_landmarks, dimension in high_dim_scenarios:
        try:
            result = benchmark_scenario(n_objects, n_landmarks, dimension)
            all_results.append(result)
        except KeyboardInterrupt:
            print("\n\nBenchmark interrupted by user.")
            break
        except Exception as e:
            print(f"\nERROR in scenario ({n_objects}obj, {n_landmarks}lm): {e}")
            import traceback

            traceback.print_exc()

    # Save results
    output_dir = Path(__file__).parent.parent / "benchmarks"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "large_scale_benchmarks.json"

    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'=' * 70}")
    print(f"✅ Results saved to {output_file}")
    print("=" * 70)

    # Summary
    print("\n=== SUMMARY ===\n")
    for result in all_results:
        n_obj = result["n_objects"]
        n_lm = result["n_landmarks"]
        dim = result["dimension"]

        pca = format_time(result["pca"]) if result["pca"] is not None else "FAILED"
        cva = format_time(result["cva"]) if result["cva"] is not None else "FAILED"
        memory = format_size(result["memory_peak"])

        print(f"{n_obj:4d} obj × {n_lm:3d} lm ({dim}D):")
        print(f"  PCA: {pca:>10s}  CVA: {cva:>10s}  Mem: {memory}")

    print()

    # Check against targets
    print("=== TARGET VALIDATION ===\n")

    targets = {
        1000: {
            "load": 5.0,  # < 5s load time
            "pca": 2.0,  # < 2s PCA
            "memory": 500 * 1024 * 1024,  # < 500MB
        }
    }

    for result in all_results:
        n_obj = result["n_objects"]
        if n_obj in targets:
            target = targets[n_obj]

            load_time = result["load_objects"] + result["unpack_landmarks"]
            pca_time = result["pca"]
            memory = result["memory_peak"]

            print(f"{n_obj} objects validation:")
            print(
                f"  Load time: {format_time(load_time)} (target: < {format_time(target['load'])}) "
                f"{'✅' if load_time < target['load'] else '❌'}"
            )
            print(
                f"  PCA time:  {format_time(pca_time)} (target: < {format_time(target['pca'])}) "
                f"{'✅' if pca_time < target['pca'] else '❌'}"
            )
            print(
                f"  Memory:    {format_size(memory)} (target: < {format_size(target['memory'])}) "
                f"{'✅' if memory < target['memory'] else '❌'}"
            )
            print()


if __name__ == "__main__":
    main()
