#!/usr/bin/env python3
"""
Script to extract components from ModanComponents.py into modular structure.
This automates the refactoring process to ensure accuracy.
"""

import os
from pathlib import Path

# Class extraction map: (start_line, end_line, target_file)
CLASS_MAP = {
    "ObjectViewer2D": (180, 1334, "components/viewers/object_viewer_2d.py"),
    "ObjectViewer3D": (1335, 2696, "components/viewers/object_viewer_3d.py"),
    "ShapePreference": (2697, 2902, "components/widgets/shape_preference.py"),
    "X1Y1": (2903, 2986, "components/formats/x1y1.py"),
    "TPS": (2987, 3121, "components/formats/tps.py"),
    "NTS": (3122, 3245, "components/formats/nts.py"),
    "Morphologika": (3246, 3364, "components/formats/morphologika.py"),
    "MdSequenceDelegate": (3365, 3374, "components/widgets/delegates.py"),
    "MdDrag": (3375, 3404, "components/widgets/drag_widgets.py"),
    "DragEventFilter": (3405, 3421, "components/widgets/drag_widgets.py"),
    "CustomDrag": (3422, 3444, "components/widgets/drag_widgets.py"),
    "MdTreeView": (3445, 3464, "components/widgets/tree_view.py"),
    "ResizableOverlayWidget": (3465, 3705, "components/widgets/overlay_widget.py"),
    "MdTableView": (3706, 4137, "components/widgets/table_view.py"),
    "MdTableModel": (4138, 4295, "components/widgets/table_view.py"),
    "AnalysisInfoWidget": (4296, None, "components/widgets/analysis_info.py"),  # to end
}


def read_source_file():
    """Read ModanComponents.py"""
    source = Path("/mnt/d/projects/Modan2/ModanComponents.py")
    with open(source, encoding="utf-8") as f:
        lines = f.readlines()
    return lines


def extract_header(lines):
    """Extract imports and constants from the header (lines 1-179)"""
    return lines[0:179]  # lines before first class


def get_class_lines(lines, start, end):
    """Extract lines for a specific class"""
    if end is None:
        return lines[start - 1 :]  # to end of file
    return lines[start - 1 : end]  # -1 because lines are 1-indexed


def create_file_with_header(filepath, header_lines, class_lines, class_name):
    """Create extracted file with appropriate imports"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        # Write module docstring
        f.write('"""\n')
        f.write(f"{class_name} - Extracted from ModanComponents.py\n")
        f.write("Part of modular refactoring effort.\n")
        f.write('"""\n\n')

        # Write imports (entire header for now, will optimize later)
        f.write("".join(header_lines))
        f.write("\n\n")

        # Write class code
        f.write("".join(class_lines))

    print(f"Created: {filepath}")
    return filepath


def main():
    print("Starting component extraction from ModanComponents.py...")

    # Read source
    lines = read_source_file()
    header = extract_header(lines)

    print(f"Total lines: {len(lines)}")
    print(f"Header lines: {len(header)}")

    # Track files to create
    files_created = {}

    # Group classes by target file
    file_to_classes = {}
    for class_name, (start, end, target) in CLASS_MAP.items():
        if target not in file_to_classes:
            file_to_classes[target] = []
        file_to_classes[target].append((class_name, start, end))

    # Extract each file
    for filepath, classes in sorted(file_to_classes.items()):
        combined_lines = []
        class_names = []

        for class_name, start, end in classes:
            class_lines = get_class_lines(lines, start, end)
            combined_lines.extend(class_lines)
            class_names.append(class_name)
            print(f"  {class_name}: lines {start}-{end if end else 'EOF'} ({len(class_lines)} lines)")

        # Create file
        full_path = f"/mnt/d/projects/Modan2/{filepath}"
        create_file_with_header(full_path, header, combined_lines, ", ".join(class_names))
        files_created[filepath] = {"classes": class_names, "lines": len(combined_lines)}

    # Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    for filepath, info in sorted(files_created.items()):
        print(f"\n{filepath}:")
        print(f"  Classes: {', '.join(info['classes'])}")
        print(f"  Lines: {info['lines']}")

    print("\n" + "=" * 60)
    print(f"Total files created: {len(files_created)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
