"""
Modan2 Components Package

This package contains modular components extracted from ModanComponents.py
for better code organization and maintainability.

Structure:
- viewers/: 2D and 3D object viewers
- widgets/: Custom PyQt5 widgets and UI components
- formats/: File format handlers for landmark data

All classes are re-exported at the package level for backward compatibility,
so existing code using `from ModanComponents import X` will continue to work.
"""

# Re-export all components for backward compatibility
from .formats import NTS, TPS, X1Y1, Morphologika
from .viewers import ObjectViewer2D, ObjectViewer3D
from .widgets import (
    AnalysisInfoWidget,
    CustomDrag,
    DatasetOpsViewer,
    DragEventFilter,
    MdDrag,
    MdSequenceDelegate,
    MdTableModel,
    MdTableView,
    MdTreeView,
    PicButton,
    ResizableOverlayWidget,
    ShapePreference,
)

__all__ = [
    # Viewers
    "ObjectViewer2D",
    "ObjectViewer3D",
    # Widgets
    "AnalysisInfoWidget",
    "DatasetOpsViewer",
    "MdSequenceDelegate",
    "CustomDrag",
    "DragEventFilter",
    "MdDrag",
    "PicButton",
    "ResizableOverlayWidget",
    "ShapePreference",
    "MdTableModel",
    "MdTableView",
    "MdTreeView",
    # Formats
    "Morphologika",
    "NTS",
    "TPS",
    "X1Y1",
]
