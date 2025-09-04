# PyQt6 QOpenGLWidget Transparency Fix Applied

- Date: 2025-09-03
- Author: Codex CLI assistant
- Context: 20250903_039_PyQt6_QOpenGLWidget_transparency_issue.md

## Summary

Implemented a scoped fix to restore transparent overlays for the 3D shape viewers in the Data Exploration dialog under PyQt6. The approach avoids top-level transparent QOpenGLWidget usage, enables alpha in the default format, normalizes widget attributes, and switches Matplotlib to a Qt6-compatible backend.

## Changes

- main.py
  - Add `QSurfaceFormat.setAlphaBufferSize(8)` before `QApplication` creation to ensure alpha in the default format for consistent composition across platforms.

- ModanDialogs.py
  - Create shape grid viewers as child widgets (`parent=self`) instead of top-level (`parent=None`).
  - Switch Matplotlib backend imports from `backend_qt5agg` to `backend_qtagg`.

- ModanComponents.py
  - Switch Matplotlib backend imports from `backend_qt5agg` to `backend_qtagg`.
  - Transparent mode: set top-level flags only when `parent is None`; for child widgets, keep `WA_TranslucentBackground` and avoid `WA_NoSystemBackground`.
  - Set `setUpdateBehavior(QOpenGLWidget.UpdateBehavior.NoPartialUpdate)` to reduce overlay artifacts.
  - OpenGL init log now includes `alphaBufferSize` for verification.

## Rationale

- QOpenGLWidget uses an internal FBO; top-level transparent windows compose inconsistently across platforms/backends (ANGLE/Metal). Embedding as child widgets keeps composition within the same top-level, preserving alpha.
- Default format alpha ensures the composition path retains transparency.
- `backend_qtagg` supports both PyQt5/6, preventing backend mismatch issues.

## Validation Plan

- Visual: 9 viewers render over the chart with transparent backgrounds; no black rectangles; z-order correct via `raise_()`.
- Logs: OpenGL init logs show nonzero `alphaBufferSize`.
- Platforms: Validate on Windows (ANGLE), Linux (X11/Wayland), macOS (Metal/Qt6) for parity.
- Performance: Confirm overlays remain responsive and stable on resize.

## Follow-ups

- If any platform still fails to compose transparently, trial a spike with `QOpenGLWindow + createWindowContainer`.
- Consider `WA_TransparentForMouseEvents` if click-through to the chart is desired.

