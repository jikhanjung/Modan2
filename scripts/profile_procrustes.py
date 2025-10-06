#!/usr/bin/env python3
"""
Detailed profiling script for Procrustes superimposition.

This script uses line_profiler to identify bottlenecks in the
Procrustes alignment algorithm.

Usage:
    kernprof -l -v scripts/profile_procrustes.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

import MdModel as mm  # noqa: N813


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
        )

    return dataset


@profile  # noqa: F821 - Added by kernprof
def run_procrustes(dataset):
    """Run Procrustes superimposition with profiling."""
    ds_ops = mm.MdDatasetOps(dataset)
    success = ds_ops.procrustes_superimposition()
    return success


def main():
    """Main profiling runner."""
    print("Procrustes Superimposition Profiling")
    print("=" * 50)

    # Create test dataset
    print("Creating test dataset (100 objects, 30 landmarks)...")
    dataset = create_test_dataset(n_objects=100, n_landmarks=30, dimension=2)

    # Run profiling
    print("Running Procrustes with profiling...")
    success = run_procrustes(dataset)

    print(f"\nProcrustes completed: {success}")
    print("\nLine-by-line profiling results will be shown by kernprof")


if __name__ == "__main__":
    main()
