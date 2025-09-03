# PyQt5 to PyQt6 Migration Plan

- **Date:** 2025-09-03
- **Author:** Gemini
- **Status:** Proposed

## 1. Introduction

This document outlines the plan to migrate the Modan2 application from the PyQt5 framework to PyQt6. This upgrade is the next logical step after the successful QOpenGLWidget migration, ensuring the project stays current with the latest Qt technologies, performance improvements, and features.

## 2. Justification

Migrating to PyQt6 offers several key advantages:

- **Long-Term Support:** PyQt6 is the actively developed branch, ensuring future updates and security patches.
- **Modern Features:** Access to new widgets, styling options, and APIs available in Qt6.
- **Performance:** Qt6 includes significant performance enhancements, particularly in graphics rendering and data handling.
- **Improved High-DPI Support:** More robust and consistent handling of high-resolution displays.
- **Python 3.6+ Features:** PyQt6 leverages modern Python features for a cleaner API.

## 3. Key Breaking Changes & Challenges

The migration requires addressing several breaking changes between PyQt5 and PyQt6:

1.  **Namespace-qualified Enums:** Enums are now strongly typed and namespaced.
    - **Before:** `Qt.AlignCenter`
    - **After:** `Qt.AlignmentFlag.AlignCenter`
2.  **`exec_()` method removed:** The `exec_()` method in `QApplication`, `QDialog`, etc., is renamed to `exec()`.
3.  **`pyqtSlot` Decorator:** The `@pyqtSlot` decorator is now mandatory for all slots to be visible to the Qt meta-object system.
4.  **`QAction` Constructor:** The constructor no longer accepts a parent widget. It must be set separately.
5.  **`QDesktopWidget` Removed:** This class is deprecated and replaced by the `QScreen` API for handling screen geometry.
6.  **Tooling Renames:** `pyuic5` -> `pyuic6`, `pylupdate5` -> `pylupdate6`.
7.  **Dependency Changes:** `PyQt5` is replaced by `PyQt6`, and `PyQt6-sip` becomes a required dependency.

## 4. Migration Strategy & Steps

A phased approach will be taken to minimize disruption.

1.  **Create a Feature Branch:**
    - Create a new git branch: `feature/pyqt6-migration`

2.  **Update Dependencies:**
    - In `requirements.txt` and other relevant files, replace `PyQt5` with `PyQt6` and add `PyQt6-sip`.

3.  **Automated Code Updates:**
    - Develop and run a script to perform bulk replacements for common changes:
        - `PyQt5` -> `PyQt6` in all import statements.
        - `exec_()` -> `exec()`
        - Common enums (e.g., `Qt.AlignCenter` -> `Qt.AlignmentFlag.AlignCenter`, `Qt.KeepAspectRatio` -> `Qt.AspectRatioMode.KeepAspectRatio`, `Qt.Key_Enter` -> `Qt.Key.Key_Enter`). This will require a comprehensive mapping.

4.  **Manual Code Refactoring:**
    - **Slots:** Review all classes inheriting from `QObject` and ensure every slot method is decorated with `@pyqtSlot(...)`.
    - **`QAction`:** Search for `QAction(...)` instantiations and refactor them to set the parent separately if needed.
    - **`QDesktopWidget`:** Replace all uses of `QApplication.desktop()` with `QApplication.primaryScreen()` or related `QScreen` methods. This will likely affect window centering logic in `ModanDialogs.py` and `Modan2.py`.
    - **Enums:** Manually fix any complex or less common enum usages not caught by the script.

5.  **Update UI and Resource Files:**
    - Re-compile `.ui` files to Python files using `pyuic6`.
    - Update the translation generation process to use `pylupdate6` and re-compile `.ts` files to `.qm`.

6.  **Update Build System:**
    - Modify `build.py` and any PyInstaller configurations. The paths for included Qt plugins might change with PyQt6.

## 5. Verification and Testing Plan

1.  **Static Analysis:** Run linters to catch syntax errors.
2.  **Automated Tests:** Execute the full `pytest` suite. Fix any tests that fail due to API changes.
3.  **Manual Testing:**
    - Launch the application on all target platforms (Windows, Linux, macOS).
    - Test all UI functionality, including dialogs, menus, drag-and-drop, 2D/3D viewers, and data analysis workflows.
    - Pay special attention to window positioning and display scaling on high-DPI monitors.
4.  **Build Verification:** Create builds for all platforms using the updated build scripts and confirm they run correctly.

## 6. Documentation
- Update `README.md`, `GEMINI.md`, and any other relevant documentation to reflect the framework change.
