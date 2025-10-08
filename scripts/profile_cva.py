#!/usr/bin/env python3
"""Profile CVA performance to identify anomaly.

Investigates why CVA has inconsistent performance:
- 500 obj, 10 lm: 425ms (slow)
- 1000 obj, 10 lm: 25ms (fast)
- 100 obj, 100 lm: 609ms (slow)
"""

import cProfile
import pstats
import sys
import time
from io import StringIO
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

from MdStatistics import do_cva_analysis


def generate_test_data(n_objects, n_landmarks, n_groups=3):
    """Generate test landmark data with groups.

    Args:
        n_objects: Number of objects
        n_landmarks: Number of landmarks per object
        n_groups: Number of groups

    Returns:
        (landmarks_data, groups) tuple
    """
    landmarks_data = []
    groups = []

    for i in range(n_objects):
        # Generate landmarks with some group-based variation
        group_id = i % n_groups
        landmarks = []
        for j in range(n_landmarks):
            # Add group offset to create separable groups
            x = (i + j) * 10.0 + group_id * 50.0
            y = (i + j) * 5.0 + group_id * 30.0
            landmarks.append([x, y])
        landmarks_data.append(landmarks)
        groups.append(f"Group{group_id}")

    return landmarks_data, groups


def benchmark_cva(n_objects, n_landmarks, n_groups=3, n_runs=5):
    """Benchmark CVA performance.

    Args:
        n_objects: Number of objects
        n_landmarks: Number of landmarks
        n_groups: Number of groups
        n_runs: Number of runs for averaging

    Returns:
        Average execution time in seconds
    """
    landmarks_data, groups = generate_test_data(n_objects, n_landmarks, n_groups)

    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        result = do_cva_analysis(landmarks_data, groups)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return np.mean(times), np.std(times), result


def profile_cva_detailed(n_objects, n_landmarks, n_groups=3):
    """Profile CVA with detailed breakdown.

    Args:
        n_objects: Number of objects
        n_landmarks: Number of landmarks
        n_groups: Number of groups
    """
    print(f"\n{'=' * 70}")
    print(f"Profiling CVA: {n_objects} objects × {n_landmarks} landmarks × {n_groups} groups")
    print("=" * 70)

    landmarks_data, groups = generate_test_data(n_objects, n_landmarks, n_groups)

    # Profile with cProfile
    profiler = cProfile.Profile()
    profiler.enable()
    result = do_cva_analysis(landmarks_data, groups)
    profiler.disable()

    # Print stats
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats("cumulative")
    stats.print_stats(20)  # Top 20 functions

    print("\nTop 20 functions by cumulative time:")
    print(s.getvalue())

    # Manual timing breakdown
    print("\nManual timing breakdown:")

    # 1. Flatten data
    start = time.perf_counter()
    flattened_data = []
    for landmarks in landmarks_data:
        flat_coords = []
        for landmark in landmarks:
            flat_coords.extend(landmark[:2])
        flattened_data.append(flat_coords)
    data_matrix = np.array(flattened_data)
    flatten_time = time.perf_counter() - start
    print(f"  Flatten data:     {flatten_time * 1000:.2f}ms")

    # 2. LDA fit_transform
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

    lda = LinearDiscriminantAnalysis()
    start = time.perf_counter()
    cv_scores = lda.fit_transform(data_matrix, np.array(groups))
    lda_time = time.perf_counter() - start
    print(f"  LDA fit_transform: {lda_time * 1000:.2f}ms")

    # 3. Padding
    start = time.perf_counter()
    if cv_scores.shape[1] < 3:
        padding_width = 3 - cv_scores.shape[1]
        cv_scores = np.pad(cv_scores, ((0, 0), (0, padding_width)), mode="constant", constant_values=0)
    padding_time = time.perf_counter() - start
    print(f"  Padding:          {padding_time * 1000:.2f}ms")

    # 4. Predictions
    start = time.perf_counter()
    _ = lda.predict(data_matrix)
    predict_time = time.perf_counter() - start
    print(f"  Predictions:      {predict_time * 1000:.2f}ms")

    # 5. Centroids
    start = time.perf_counter()
    unique_groups = np.unique(np.array(groups))
    centroids = []
    for group in unique_groups:
        group_mask = np.array(groups) == group
        group_centroid = np.mean(cv_scores[group_mask], axis=0)
        centroids.append(group_centroid.tolist())
    centroid_time = time.perf_counter() - start
    print(f"  Centroids:        {centroid_time * 1000:.2f}ms")

    total_manual = flatten_time + lda_time + padding_time + predict_time + centroid_time
    print(f"  TOTAL (manual):   {total_manual * 1000:.2f}ms")

    # Data characteristics
    print("\nData characteristics:")
    print(f"  Objects: {n_objects}")
    print(f"  Landmarks: {n_landmarks}")
    print(f"  Features (dimensions): {data_matrix.shape[1]}")
    print(f"  Groups: {n_groups}")
    print(f"  CV dimensions: {cv_scores.shape[1]}")
    print(f"  Data matrix shape: {data_matrix.shape}")
    print(f"  CV scores shape: {cv_scores.shape}")

    return result


def compare_scenarios():
    """Compare the problematic scenarios."""
    print("\n" + "=" * 70)
    print("CVA Performance Investigation")
    print("=" * 70)

    scenarios = [
        # (objects, landmarks, groups, label)
        (500, 10, 3, "500 obj × 10 lm (SLOW in benchmark)"),
        (1000, 10, 3, "1000 obj × 10 lm (FAST in benchmark)"),
        (2000, 10, 3, "2000 obj × 10 lm (MEDIUM in benchmark)"),
        (100, 100, 3, "100 obj × 100 lm (SLOW in benchmark)"),
        (50, 200, 3, "50 obj × 200 lm (FAST in benchmark)"),
        # Additional test cases
        (100, 10, 3, "100 obj × 10 lm (control)"),
        (500, 10, 2, "500 obj × 10 lm × 2 groups"),
        (500, 10, 5, "500 obj × 10 lm × 5 groups"),
    ]

    results = []

    for n_obj, n_lm, n_grp, label in scenarios:
        print(f"\n{label}:")
        avg_time, std_time, result = benchmark_cva(n_obj, n_lm, n_grp, n_runs=5)
        print(f"  Average: {avg_time * 1000:.1f}ms ± {std_time * 1000:.1f}ms")

        results.append(
            {
                "label": label,
                "objects": n_obj,
                "landmarks": n_lm,
                "groups": n_grp,
                "time_ms": avg_time * 1000,
                "std_ms": std_time * 1000,
            }
        )

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Scenario':<45} {'Time (ms)':>12} {'Features':>10}")
    print("-" * 70)

    for r in results:
        features = r["objects"] * r["landmarks"] * 2  # 2D coordinates
        print(f"{r['label']:<45} {r['time_ms']:>10.1f}ms {features:>10}")

    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    # Check correlation with various factors
    times = [r["time_ms"] for r in results]
    objs = [r["objects"] for r in results]
    lms = [r["landmarks"] for r in results]
    features = [r["objects"] * r["landmarks"] * 2 for r in results]
    groups = [r["groups"] for r in results]

    print("\nCorrelation with time:")
    print(f"  Objects:  {np.corrcoef(objs, times)[0, 1]:.3f}")
    print(f"  Landmarks: {np.corrcoef(lms, times)[0, 1]:.3f}")
    print(f"  Features:  {np.corrcoef(features, times)[0, 1]:.3f}")
    print(f"  Groups:    {np.corrcoef(groups, times)[0, 1]:.3f}")


def main():
    """Main profiling routine."""
    # Compare scenarios
    compare_scenarios()

    # Detailed profiling of slow cases
    print("\n\n" + "=" * 70)
    print("DETAILED PROFILING - SLOW CASES")
    print("=" * 70)

    # Case 1: 500 obj × 10 lm (slow in benchmark)
    profile_cva_detailed(500, 10, 3)

    # Case 2: 100 obj × 100 lm (slow in benchmark)
    profile_cva_detailed(100, 100, 3)

    # Compare with fast cases
    print("\n\n" + "=" * 70)
    print("DETAILED PROFILING - FAST CASES")
    print("=" * 70)

    # Case 3: 1000 obj × 10 lm (fast in benchmark)
    profile_cva_detailed(1000, 10, 3)

    # Case 4: 50 obj × 200 lm (fast in benchmark)
    profile_cva_detailed(50, 200, 3)


if __name__ == "__main__":
    main()
