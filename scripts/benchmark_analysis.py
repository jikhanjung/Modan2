#!/usr/bin/env python3
"""
Performance benchmarking script for Modan2 analysis operations.

This script benchmarks:
- PCA analysis
- CVA analysis
- MANOVA analysis
- Procrustes superimposition

Usage:
    python scripts/benchmark_analysis.py
"""

import json
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import MdModel as mm  # noqa: N813
import MdStatistics


def create_test_dataset(n_objects=50, n_landmarks=10, dimension=2):
    """Create a test dataset with random landmarks."""
    import numpy as np

    # Create database in memory
    mm.gDatabase.init(":memory:")
    mm.gDatabase.create_tables([mm.MdDataset, mm.MdObject, mm.MdAnalysis, mm.MdImage, mm.MdThreeDModel])

    # Create dataset
    dataset = mm.MdDataset.create(
        dataset_name=f"Benchmark_{n_objects}obj_{n_landmarks}lm",
        dimension=dimension,
        landmark_count=n_landmarks,
        propertyname_str="Group,Size",
    )

    # Create objects with random landmarks
    for i in range(n_objects):
        landmarks = np.random.randn(n_landmarks, dimension) * 10 + 50
        landmark_str = "\n".join(["\t".join(map(str, lm)) for lm in landmarks])

        mm.MdObject.create(
            dataset=dataset,
            object_name=f"Object_{i + 1}",
            sequence=i + 1,
            landmark_str=landmark_str,
            property_str=f"Group{i % 3},10",  # 3 groups for CVA/MANOVA
        )

    return dataset


def benchmark_procrustes(dataset):
    """Benchmark Procrustes superimposition."""
    ds_ops = mm.MdDatasetOps(dataset)

    start = time.perf_counter()
    success = ds_ops.procrustes_superimposition()
    elapsed = time.perf_counter() - start

    return {
        "operation": "procrustes",
        "success": success,
        "time_seconds": elapsed,
        "n_objects": len(ds_ops.object_list),
        "n_landmarks": dataset.landmark_count if hasattr(dataset, "landmark_count") else None,
    }


def benchmark_pca(landmarks_data, n_components=None):
    """Benchmark PCA analysis."""
    start = time.perf_counter()
    result = MdStatistics.do_pca_analysis(landmarks_data, n_components=n_components)
    elapsed = time.perf_counter() - start

    return {
        "operation": "pca",
        "success": result is not None,
        "time_seconds": elapsed,
        "n_samples": len(landmarks_data),
        "n_components": result.get("n_components", None) if result else None,
    }


def benchmark_cva(landmarks_data, groups):
    """Benchmark CVA analysis."""
    start = time.perf_counter()
    try:
        _result = MdStatistics.do_cva_analysis(landmarks_data, groups)
        elapsed = time.perf_counter() - start
        success = True
    except Exception as e:
        elapsed = time.perf_counter() - start
        success = False
        _error_result = {"error": str(e)}

    return {
        "operation": "cva",
        "success": success,
        "time_seconds": elapsed,
        "n_samples": len(landmarks_data),
        "n_groups": len(set(groups)) if success else None,
    }


def benchmark_manova(landmarks_data, groups):
    """Benchmark MANOVA analysis."""
    start = time.perf_counter()
    try:
        # Flatten landmarks for MANOVA
        flattened_data = []
        for lm_list in landmarks_data:
            flat = []
            for lm in lm_list:
                flat.extend(lm)
            flattened_data.append(flat)

        _result = MdStatistics.do_manova_analysis_on_procrustes(flattened_data, groups)
        elapsed = time.perf_counter() - start
        success = True
    except Exception as e:
        elapsed = time.perf_counter() - start
        success = False
        _error_result = {"error": str(e)}

    return {
        "operation": "manova",
        "success": success,
        "time_seconds": elapsed,
        "n_samples": len(landmarks_data),
        "n_groups": len(set(groups)) if success else None,
    }


def run_benchmark_suite(sizes=None):
    """Run complete benchmark suite."""
    if sizes is None:
        sizes = [(10, 10), (50, 20), (100, 30)]
    results = []

    for n_objects, n_landmarks in sizes:
        print(f"\n=== Benchmarking {n_objects} objects, {n_landmarks} landmarks ===")

        # Create test dataset
        print("Creating test dataset...")
        dataset = create_test_dataset(n_objects, n_landmarks, dimension=2)

        # Benchmark Procrustes
        print("Benchmarking Procrustes...")
        procrustes_result = benchmark_procrustes(dataset)
        procrustes_result["n_objects"] = n_objects
        procrustes_result["n_landmarks"] = n_landmarks
        results.append(procrustes_result)
        print(f"  Procrustes: {procrustes_result['time_seconds']:.3f}s")

        # Get landmarks for analysis
        ds_ops = mm.MdDatasetOps(dataset)
        ds_ops.procrustes_superimposition()
        landmarks_data = [obj.landmark_list for obj in ds_ops.object_list]

        # Get groups for CVA/MANOVA
        groups = [f"Group{i % 3}" for i in range(n_objects)]

        # Benchmark PCA
        print("Benchmarking PCA...")
        pca_result = benchmark_pca(landmarks_data, n_components=None)
        pca_result["n_objects"] = n_objects
        pca_result["n_landmarks"] = n_landmarks
        results.append(pca_result)
        print(f"  PCA: {pca_result['time_seconds']:.3f}s")

        # Benchmark CVA
        print("Benchmarking CVA...")
        cva_result = benchmark_cva(landmarks_data, groups)
        cva_result["n_objects"] = n_objects
        cva_result["n_landmarks"] = n_landmarks
        results.append(cva_result)
        print(f"  CVA: {cva_result['time_seconds']:.3f}s")

        # Benchmark MANOVA
        print("Benchmarking MANOVA...")
        manova_result = benchmark_manova(landmarks_data, groups)
        manova_result["n_objects"] = n_objects
        manova_result["n_landmarks"] = n_landmarks
        results.append(manova_result)
        print(f"  MANOVA: {manova_result['time_seconds']:.3f}s")

    return results


def main():
    """Main benchmark runner."""
    print("Modan2 Analysis Performance Benchmarks")
    print("=" * 50)

    # Define test sizes
    sizes = [
        (10, 10),  # Small dataset
        (50, 20),  # Medium dataset
        (100, 30),  # Large dataset
    ]

    # Run benchmarks
    results = run_benchmark_suite(sizes)

    # Save results
    output_file = Path(__file__).parent.parent / "benchmarks" / "analysis_benchmarks.json"
    with open(output_file, "w") as f:
        json.dump({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "benchmarks": results}, f, indent=2)

    print(f"\n✅ Results saved to {output_file}")

    # Print summary
    print("\n=== Summary ===")
    for result in results:
        op = result["operation"]
        n_obj = result["n_objects"]
        n_lm = result["n_landmarks"]
        t = result["time_seconds"]
        success = "✅" if result["success"] else "❌"
        print(f"{success} {op.upper():10s} ({n_obj:3d}obj, {n_lm:2d}lm): {t:6.3f}s")


if __name__ == "__main__":
    main()
