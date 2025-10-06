#!/usr/bin/env python3
"""
Detailed profiling using cProfile for all analysis operations.

This script uses Python's built-in cProfile to identify performance bottlenecks.

Usage:
    python scripts/profile_detailed.py
"""

import cProfile
import pstats
import sys
from io import StringIO
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

import MdModel as mm  # noqa: N813
import MdStatistics


def create_test_dataset(n_objects=100, n_landmarks=30, dimension=2):
    """Create a test dataset for profiling."""
    # Create database in memory
    mm.gDatabase.init(":memory:")
    mm.gDatabase.create_tables([mm.MdDataset, mm.MdObject, mm.MdAnalysis, mm.MdImage, mm.MdThreeDModel])

    # Create dataset
    dataset = mm.MdDataset.create(
        dataset_name=f"Profile_{n_objects}obj_{n_landmarks}lm",
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
            property_str=f"Group{i % 3},10",
        )

    return dataset


def profile_procrustes():
    """Profile Procrustes superimposition."""
    print("\n" + "=" * 60)
    print("PROCRUSTES SUPERIMPOSITION PROFILING")
    print("=" * 60)

    dataset = create_test_dataset(50, 20, 2)  # Reduced for faster profiling

    # Profile the operation
    profiler = cProfile.Profile()
    profiler.enable()

    ds_ops = mm.MdDatasetOps(dataset)
    success = ds_ops.procrustes_superimposition()

    profiler.disable()

    # Print results
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)  # Top 30 functions
    print(s.getvalue())

    # Save detailed stats
    profiler.dump_stats("benchmarks/procrustes_profile.prof")
    print("\n✅ Detailed stats saved to benchmarks/procrustes_profile.prof")
    print("   View with: snakeviz benchmarks/procrustes_profile.prof")

    return success


def profile_pca():
    """Profile PCA analysis."""
    print("\n" + "=" * 60)
    print("PCA ANALYSIS PROFILING")
    print("=" * 60)

    dataset = create_test_dataset(50, 20, 2)  # Reduced for faster profiling

    # Get landmarks
    ds_ops = mm.MdDatasetOps(dataset)
    ds_ops.procrustes_superimposition()
    landmarks_data = [obj.landmark_list for obj in ds_ops.object_list]

    # Profile the operation
    profiler = cProfile.Profile()
    profiler.enable()

    result = MdStatistics.do_pca_analysis(landmarks_data, n_components=None)

    profiler.disable()

    # Print results
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(20)  # Top 20 functions
    print(s.getvalue())

    # Save detailed stats
    profiler.dump_stats("benchmarks/pca_profile.prof")
    print("\n✅ Detailed stats saved to benchmarks/pca_profile.prof")

    return result


def profile_cva():
    """Profile CVA analysis."""
    print("\n" + "=" * 60)
    print("CVA ANALYSIS PROFILING")
    print("=" * 60)

    # Test both small and medium datasets
    for size_name, n_obj, n_lm in [("SMALL", 10, 10), ("MEDIUM", 50, 20)]:
        print(f"\n--- {size_name} Dataset ({n_obj} objects, {n_lm} landmarks) ---")

        dataset = create_test_dataset(n_obj, n_lm, 2)

        # Get landmarks
        ds_ops = mm.MdDatasetOps(dataset)
        ds_ops.procrustes_superimposition()
        landmarks_data = [obj.landmark_list for obj in ds_ops.object_list]
        groups = [f"Group{i % 3}" for i in range(n_obj)]

        # Profile the operation
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            _result = MdStatistics.do_cva_analysis(landmarks_data, groups)
            profiler.disable()

            # Print results
            s = StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
            ps.print_stats(20)  # Top 20 functions
            print(s.getvalue())

            # Save detailed stats
            filename = f"benchmarks/cva_{size_name.lower()}_profile.prof"
            profiler.dump_stats(filename)
            print(f"\n✅ Detailed stats saved to {filename}")

        except Exception as e:
            profiler.disable()
            print(f"❌ CVA failed: {e}")


def profile_manova():
    """Profile MANOVA analysis."""
    print("\n" + "=" * 60)
    print("MANOVA ANALYSIS PROFILING")
    print("=" * 60)

    dataset = create_test_dataset(50, 20, 2)

    # Get landmarks
    ds_ops = mm.MdDatasetOps(dataset)
    ds_ops.procrustes_superimposition()
    landmarks_data = [obj.landmark_list for obj in ds_ops.object_list]
    groups = [f"Group{i % 3}" for i in range(50)]

    # Flatten landmarks
    flattened_data = []
    for lm_list in landmarks_data:
        flat = []
        for lm in lm_list:
            flat.extend(lm)
        flattened_data.append(flat)

    # Profile the operation
    profiler = cProfile.Profile()
    profiler.enable()

    try:
        _result = MdStatistics.do_manova_analysis_on_procrustes(flattened_data, groups)
        profiler.disable()

        # Print results
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        ps.print_stats(20)  # Top 20 functions
        print(s.getvalue())

        # Save detailed stats
        profiler.dump_stats("benchmarks/manova_profile.prof")
        print("\n✅ Detailed stats saved to benchmarks/manova_profile.prof")

    except Exception as e:
        profiler.disable()
        print(f"❌ MANOVA failed: {e}")


def main():
    """Main profiling runner."""
    print("Modan2 Detailed Performance Profiling")
    print("=" * 60)
    print("Using cProfile for detailed function-level analysis")
    print("\nThis will generate .prof files viewable with snakeviz:")
    print("  snakeviz benchmarks/<filename>.prof")
    print("=" * 60)

    # Profile each operation
    profile_procrustes()
    profile_pca()
    profile_cva()
    profile_manova()

    print("\n" + "=" * 60)
    print("PROFILING COMPLETE")
    print("=" * 60)
    print("\nGenerated profile files:")
    print("  - benchmarks/procrustes_profile.prof")
    print("  - benchmarks/pca_profile.prof")
    print("  - benchmarks/cva_small_profile.prof")
    print("  - benchmarks/cva_large_profile.prof")
    print("  - benchmarks/manova_profile.prof")
    print("\nView with: snakeviz benchmarks/<filename>.prof")


if __name__ == "__main__":
    main()
