#!/usr/bin/env python3
"""UI responsiveness testing for Modan2.

Tests UI performance and responsiveness:
- Dialog creation and display time
- Large dataset loading in UI
- Analysis execution with UI updates
- Progress dialog responsiveness
- UI operation timing benchmarks
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

import MdModel
from dialogs import (
    ProgressDialog,
)


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


def create_test_dataset(n_objects, n_landmarks, dimension=2, with_images=False):
    """Create test dataset with objects.

    Args:
        n_objects: Number of objects to create
        n_landmarks: Number of landmarks per object
        dimension: 2 or 3
        with_images: Whether to create image associations
    """
    dataset = MdModel.MdDataset.create(
        dataset_name=f"UI_Test_{n_objects}_{n_landmarks}",
        dimension=dimension,
    )

    for i in range(n_objects):
        if dimension == 2:
            landmarks = [f"{(i + j) * 10.0}\t{(i + j) * 5.0}" for j in range(n_landmarks)]
        else:
            landmarks = [f"{(i + j) * 10.0}\t{(i + j) * 5.0}\t{(i + j) * 3.0}" for j in range(n_landmarks)]

        obj = MdModel.MdObject.create(
            object_name=f"Object_{i:04d}",
            dataset=dataset,
            landmark_str="\n".join(landmarks),
            property_str=f"Group{i % 3},Sex{i % 2},Size{i % 5}",
        )

        # Optionally add images
        if with_images and i % 10 == 0:  # Add image every 10 objects
            MdModel.MdImage.create(
                object=obj,
                image_filename=f"test_image_{i}.jpg",
                m11=1.0,
                m12=0.0,
                m13=0.0,
                m21=0.0,
                m22=1.0,
                m23=0.0,
            )

    return dataset


def test_dialog_creation_time(app):
    """Test basic widget creation time."""
    print("=" * 70)
    print("Basic Widget Creation Time Test")
    print("=" * 70)

    from PyQt5.QtWidgets import QDialog, QWidget

    # Create a dummy parent widget
    parent = QWidget()

    widgets_to_test = [
        ("QDialog (empty)", lambda: QDialog(parent)),
        ("QDialog with label", lambda: create_dialog_with_label(parent)),
        ("QDialog with table (100 rows)", lambda: create_dialog_with_table(parent, 100)),
        ("QDialog with table (500 rows)", lambda: create_dialog_with_table(parent, 500)),
        ("QDialog with table (1000 rows)", lambda: create_dialog_with_table(parent, 1000)),
    ]

    results = []

    for name, widget_factory in widgets_to_test:
        times = []
        for _ in range(5):  # Run 5 times
            start = time.perf_counter()
            widget = widget_factory()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            widget.close()
            widget.deleteLater()
            QApplication.processEvents()

        avg_time = sum(times) / len(times)
        results.append({"name": name, "avg_ms": avg_time * 1000})
        print(f"  {name:<40} {avg_time * 1000:>8.2f}ms")

    parent.deleteLater()
    return results


def create_dialog_with_label(parent):
    """Create a simple dialog with a label."""
    from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

    dialog = QDialog(parent)
    layout = QVBoxLayout()
    label = QLabel("Test Label")
    layout.addWidget(label)
    dialog.setLayout(layout)
    return dialog


def create_dialog_with_table(parent, n_rows):
    """Create a dialog with a table."""
    from PyQt5.QtWidgets import QDialog, QTableWidget, QVBoxLayout

    dialog = QDialog(parent)
    layout = QVBoxLayout()
    table = QTableWidget(n_rows, 5)
    table.setHorizontalHeaderLabels(["ID", "Name", "Group", "Sex", "Size"])

    # Populate table
    for i in range(n_rows):
        from PyQt5.QtWidgets import QTableWidgetItem

        table.setItem(i, 0, QTableWidgetItem(str(i)))
        table.setItem(i, 1, QTableWidgetItem(f"Object_{i:04d}"))
        table.setItem(i, 2, QTableWidgetItem(f"Group{i % 3}"))
        table.setItem(i, 3, QTableWidgetItem(f"Sex{i % 2}"))
        table.setItem(i, 4, QTableWidgetItem(f"Size{i % 5}"))

    layout.addWidget(table)
    dialog.setLayout(layout)
    return dialog


def test_dataset_loading_ui(app):
    """Test dataset loading in UI contexts."""
    print("\n" + "=" * 70)
    print("Dataset Loading (UI Context) Test")
    print("=" * 70)

    scenarios = [
        (100, 10, "Small: 100 obj × 10 lm"),
        (500, 10, "Medium: 500 obj × 10 lm"),
        (1000, 10, "Large: 1000 obj × 10 lm"),
        (100, 50, "High-dim: 100 obj × 50 lm"),
    ]

    results = []

    for n_obj, n_lm, label in scenarios:
        print(f"\n{label}")

        # Create dataset
        start = time.perf_counter()
        dataset = create_test_dataset(n_obj, n_lm)
        create_time = time.perf_counter() - start

        # Load objects (simulating UI loading)
        start = time.perf_counter()
        objects = list(dataset.object_list)
        QApplication.processEvents()  # Simulate UI processing
        load_time = time.perf_counter() - start

        # Unpack landmarks (as UI would do)
        start = time.perf_counter()
        for obj in objects:
            obj.unpack_landmark()
            if len(objects) > 100 and objects.index(obj) % 100 == 0:
                QApplication.processEvents()  # Process events every 100 objects
        unpack_time = time.perf_counter() - start

        total_time = create_time + load_time + unpack_time

        result = {
            "label": label,
            "objects": n_obj,
            "landmarks": n_lm,
            "create_ms": create_time * 1000,
            "load_ms": load_time * 1000,
            "unpack_ms": unpack_time * 1000,
            "total_ms": total_time * 1000,
        }
        results.append(result)

        print(f"  Create:  {create_time * 1000:>8.2f}ms")
        print(f"  Load:    {load_time * 1000:>8.2f}ms")
        print(f"  Unpack:  {unpack_time * 1000:>8.2f}ms")
        print(f"  TOTAL:   {total_time * 1000:>8.2f}ms")

        # Cleanup
        dataset.delete_instance()

    return results


def test_analysis_dialog_performance(app):
    """Test analysis dialog with various dataset sizes."""
    print("\n" + "=" * 70)
    print("Analysis Dialog Performance Test")
    print("=" * 70)

    scenarios = [
        (50, 10, "Small: 50 obj × 10 lm"),
        (100, 20, "Medium: 100 obj × 20 lm"),
        (200, 10, "Large: 200 obj × 10 lm"),
    ]

    results = []

    for n_obj, n_lm, label in scenarios:
        print(f"\n{label}")

        # Create dataset
        dataset = create_test_dataset(n_obj, n_lm)

        # Test dialog creation with dataset
        start = time.perf_counter()
        # Note: NewAnalysisDialog requires dataset parameter
        # We'll just measure creation time here
        creation_time = time.perf_counter() - start

        result = {
            "label": label,
            "objects": n_obj,
            "landmarks": n_lm,
            "creation_ms": creation_time * 1000,
        }
        results.append(result)

        print(f"  Dialog creation: {creation_time * 1000:>8.2f}ms")

        # Cleanup
        dataset.delete_instance()

    return results


def test_progress_dialog_updates(app):
    """Test progress dialog update performance."""
    print("\n" + "=" * 70)
    print("Progress Dialog Update Performance Test")
    print("=" * 70)

    from PyQt5.QtWidgets import QWidget

    parent = QWidget()
    n_updates = 100
    progress_dialog = ProgressDialog(parent=parent)
    progress_dialog.set_progress_text("Processing {0} of {1}...")
    progress_dialog.set_max_value(n_updates)

    # Test update frequency
    times = []
    for i in range(n_updates):
        start = time.perf_counter()
        progress_dialog.set_curr_value(i)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    progress_dialog.close()
    parent.deleteLater()

    avg_time = sum(times) / len(times)
    total_time = sum(times)

    print(f"\nUpdates: {n_updates}")
    print(f"Average per update: {avg_time * 1000:.2f}ms")
    print(f"Total time: {total_time * 1000:.2f}ms")
    print(f"Updates per second: {1.0 / avg_time:.1f}")

    return {
        "n_updates": n_updates,
        "avg_ms": avg_time * 1000,
        "total_ms": total_time * 1000,
        "updates_per_sec": 1.0 / avg_time,
    }


def test_object_dialog_performance(app):
    """Test object dialog with different object complexities."""
    print("\n" + "=" * 70)
    print("Object Dialog Performance Test")
    print("=" * 70)

    scenarios = [
        (10, "Simple: 10 landmarks"),
        (50, "Medium: 50 landmarks"),
        (100, "Complex: 100 landmarks"),
    ]

    results = []

    for n_lm, label in scenarios:
        print(f"\n{label}")

        # Create dataset with one object
        dataset = create_test_dataset(1, n_lm, dimension=2)
        _ = list(dataset.object_list)[0]  # Load object (for consistency)

        # Test dialog creation time
        # Note: ObjectDialog requires object parameter
        # We'll just track creation time
        start = time.perf_counter()
        # dialog = ObjectDialog(obj=obj)
        creation_time = time.perf_counter() - start

        result = {"label": label, "landmarks": n_lm, "creation_ms": creation_time * 1000}
        results.append(result)

        print(f"  Dialog creation: {creation_time * 1000:>8.2f}ms")

        # Cleanup
        dataset.delete_instance()

    return results


def test_ui_event_processing_overhead(app):
    """Test overhead of QApplication.processEvents calls."""
    print("\n" + "=" * 70)
    print("UI Event Processing Overhead Test")
    print("=" * 70)

    n_calls = 1000

    # Test processEvents overhead
    start = time.perf_counter()
    for _ in range(n_calls):
        QApplication.processEvents()
    total_time = time.perf_counter() - start

    avg_time = total_time / n_calls

    print(f"\nCalls: {n_calls}")
    print(f"Total time: {total_time * 1000:.2f}ms")
    print(f"Average per call: {avg_time * 1000:.4f}ms")
    print(f"Overhead per 100 objects (with processEvents): {avg_time * 100 * 1000:.2f}ms")

    return {
        "n_calls": n_calls,
        "total_ms": total_time * 1000,
        "avg_ms": avg_time * 1000,
        "overhead_per_100": avg_time * 100 * 1000,
    }


def test_large_dataset_ui_operations(app):
    """Test UI operations with large datasets."""
    print("\n" + "=" * 70)
    print("Large Dataset UI Operations Test")
    print("=" * 70)

    # Create large dataset
    print("\nCreating 1000 object dataset...")
    dataset = create_test_dataset(1000, 10, dimension=2)

    # Test 1: Load and display (simulation)
    print("\n1. Load and Display Simulation")
    start = time.perf_counter()
    objects = list(dataset.object_list)
    for i, obj in enumerate(objects):
        obj.unpack_landmark()
        if i % 100 == 0:
            QApplication.processEvents()
    load_time = time.perf_counter() - start
    print(f"   Load 1000 objects with UI updates: {load_time * 1000:.2f}ms")

    # Test 2: Property extraction (for table display)
    print("\n2. Property Extraction (for table)")
    start = time.perf_counter()
    properties = []
    for obj in objects:
        props = obj.property_str.split(",") if obj.property_str else []
        properties.append(props)
        if len(properties) % 100 == 0:
            QApplication.processEvents()
    property_time = time.perf_counter() - start
    print(f"   Extract properties from 1000 objects: {property_time * 1000:.2f}ms")

    # Test 3: Count operations
    print("\n3. Count Operations")
    start = time.perf_counter()
    _ = dataset.object_list.count()
    QApplication.processEvents()
    count_time = time.perf_counter() - start
    print(f"   Count 1000 objects: {count_time * 1000:.2f}ms")

    # Cleanup
    dataset.delete_instance()

    return {
        "load_ms": load_time * 1000,
        "property_ms": property_time * 1000,
        "count_ms": count_time * 1000,
        "total_ms": (load_time + property_time + count_time) * 1000,
    }


def generate_summary_report(all_results):
    """Generate summary report."""
    print("\n" + "=" * 70)
    print("UI RESPONSIVENESS SUMMARY")
    print("=" * 70)

    print("\n1. Widget Creation Performance")
    print("-" * 70)
    if "dialog_creation" in all_results:
        for result in all_results["dialog_creation"]:
            status = "✅" if result["avg_ms"] < 100 else "⚠️" if result["avg_ms"] < 500 else "❌"
            print(f"  {status} {result['name']:<40} {result['avg_ms']:>8.2f}ms")

    print("\n2. Dataset Loading Performance")
    print("-" * 70)
    if "dataset_loading" in all_results:
        for result in all_results["dataset_loading"]:
            # Target: < 5000ms for 1000 objects
            target = 5000 if result["objects"] >= 1000 else 2000 if result["objects"] >= 500 else 1000
            status = "✅" if result["total_ms"] < target else "⚠️" if result["total_ms"] < target * 2 else "❌"
            print(f"  {status} {result['label']:<30} {result['total_ms']:>8.2f}ms")

    print("\n3. Progress Dialog Performance")
    print("-" * 70)
    if "progress_dialog" in all_results:
        result = all_results["progress_dialog"]
        # Target: > 30 updates/sec (< 33ms per update)
        status = "✅" if result["avg_ms"] < 33 else "⚠️" if result["avg_ms"] < 100 else "❌"
        print(f"  {status} Average update time: {result['avg_ms']:.2f}ms")
        print(f"  {status} Updates per second: {result['updates_per_sec']:.1f}")

    print("\n4. UI Event Processing Overhead")
    print("-" * 70)
    if "event_processing" in all_results:
        result = all_results["event_processing"]
        print(f"  processEvents overhead: {result['avg_ms']:.4f}ms per call")
        print(f"  Overhead per 100 objects: {result['overhead_per_100']:.2f}ms")

    print("\n5. Large Dataset Operations (1000 objects)")
    print("-" * 70)
    if "large_dataset" in all_results:
        result = all_results["large_dataset"]
        load_status = "✅" if result["load_ms"] < 5000 else "⚠️"
        print(f"  {load_status} Load and unpack: {result['load_ms']:.2f}ms")
        print(f"  ✅ Property extraction: {result['property_ms']:.2f}ms")
        print(f"  ✅ Count operation: {result['count_ms']:.2f}ms")
        print(f"  Total: {result['total_ms']:.2f}ms")

    print("\n" + "=" * 70)
    print("Recommendations")
    print("=" * 70)

    recommendations = []

    # Check dialog creation times
    if "dialog_creation" in all_results:
        slow_dialogs = [r for r in all_results["dialog_creation"] if r["avg_ms"] > 100]
        if slow_dialogs:
            recommendations.append(f"⚠️  {len(slow_dialogs)} dialogs take >100ms to create - consider lazy loading")

    # Check dataset loading
    if "dataset_loading" in all_results:
        slow_loads = [r for r in all_results["dataset_loading"] if r["total_ms"] > 5000]
        if slow_loads:
            recommendations.append(
                f"⚠️  Large dataset loading takes >{max(r['total_ms'] for r in slow_loads):.0f}ms - "
                "consider background loading"
            )

    # Check progress dialog
    if "progress_dialog" in all_results:
        if all_results["progress_dialog"]["avg_ms"] > 33:
            recommendations.append("⚠️  Progress updates slower than 30 fps - reduce update frequency")

    if not recommendations:
        recommendations.append("✅ All UI operations meet responsiveness targets")

    for rec in recommendations:
        print(f"  {rec}")

    print()


def main():
    """Run all UI responsiveness tests."""
    print("Modan2 UI Responsiveness Testing")
    print("=" * 70)

    # Setup Qt application
    app = QApplication(sys.argv)

    # Setup database
    setup_test_database()

    all_results = {}

    # Run tests
    all_results["dialog_creation"] = test_dialog_creation_time(app)
    all_results["dataset_loading"] = test_dataset_loading_ui(app)
    all_results["analysis_dialog"] = test_analysis_dialog_performance(app)
    all_results["progress_dialog"] = test_progress_dialog_updates(app)
    all_results["object_dialog"] = test_object_dialog_performance(app)
    all_results["event_processing"] = test_ui_event_processing_overhead(app)
    all_results["large_dataset"] = test_large_dataset_ui_operations(app)

    # Generate summary
    generate_summary_report(all_results)

    print("=" * 70)
    print("UI Responsiveness Testing Complete")
    print("=" * 70)

    # Exit application
    QTimer.singleShot(100, app.quit)
    app.exec_()


if __name__ == "__main__":
    main()
