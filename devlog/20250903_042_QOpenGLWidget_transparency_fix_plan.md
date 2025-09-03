# PyQt6 QOpenGLWidget Transparency Fix Plan (Shape Grid Overlay)

- Date: 2025-09-03
- Author: Codex CLI assistant
- Related: 20250903_039_PyQt6_QOpenGLWidget_transparency_issue.md

## Summary

After migrating to PyQt6, nine QOpenGLWidget-based viewers intended to overlay charts with transparent backgrounds render as opaque black, hiding the chart beneath. Root cause is the composition behavior of QOpenGLWidget (FBO-based) combined with top-level widget usage and missing alpha in the default surface format.

## Decision

- Avoid top-level transparent QOpenGLWidget overlays; embed viewers as child widgets of the dialog/container.
- Enable alpha channel in the default `QSurfaceFormat`.
- Normalize QOpenGLWidget transparent rendering and update behavior.
- Ensure matplotlib uses a Qt6-compatible backend (`qtagg`/`QtAgg`) so composition with Qt widgets is consistent.

## Changes (Concrete)

### 1) `main.py` — Default format alpha

- Location: OpenGL surface format configuration (before `QApplication` is created)
- Add alpha buffer so the composition pipeline preserves transparency across platforms/ANGLE.

```python
fmt = QSurfaceFormat()
fmt.setVersion(2, 1)
fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
fmt.setDepthBufferSize(24)
fmt.setStencilBufferSize(8)
fmt.setSamples(4)
fmt.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
fmt.setAlphaBufferSize(8)  # NEW: ensure alpha channel in default format
QSurfaceFormat.setDefaultFormat(fmt)
```

- Optional: Log `fmt.alphaBufferSize()` on GL init to confirm.

### 2) `ModanDialogs.py` — Make viewers child widgets

- Location (shape grid creation): around lines 3337–3343 and placement around line 3645.
- Change top-level creation to child creation; keep geometry in parent coordinates; ensure z-order.

```python
# Before
view = ObjectViewer3D(parent=None, transparent=True)
# After
view = ObjectViewer3D(parent=self, transparent=True)  # or a dedicated overlay container as parent
view.setGeometry(x_pos, y_pos, width, height)
view.raise_()  # ensure it sits above the chart

# If clicks must pass through to the chart beneath:
# view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
```

### 3) `ModanComponents.py` — Transparent mode normalization

- Location: constructor block handling `transparent` (1128–1164) and `paintGL()` (1968–1988).
- Keep frameless flags only for true top-level windows (parent is None). For child widgets, avoid top-level flags; minimize heavy background attributes.
- Add stable update behavior to avoid partial-update artifacts.

```python
if transparent:
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    fmt.setSamples(0)
    self.setFormat(fmt)

    # Top-level only
    if parent is None:
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
    else:
        # Child widget overlay: usually safer with fewer background overrides
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # Avoid WA_NoSystemBackground for child to reduce flicker

    # Reduce artifacts for overlays
    self.setUpdateBehavior(QOpenGLWidget.UpdateBehavior.NoPartialUpdate)
```

```python
# paintGL(): ensure real transparent clear + blending
if self.transparent:
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glClearColor(0.0, 0.0, 0.0, 0.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
```

- Optional: stylesheet to ensure no background fill leaks in parent chain

```python
self.setStyleSheet("background: transparent;")
```

### 4) `matplotlib` backend — dual-Qt compatibility

- Replace `backend_qt5agg` with `backend_qtagg` (or `QtAgg`) in:
  - `ModanDialogs.py`
  - `ModanComponents.py`

```python
# Before
from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
# After
from matplotlib.backends.backend_qtagg import FigureCanvas as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
```

## Validation Checklist

- Visual
  - 9 viewers overlay the chart with proper transparency (no black rectangles).
  - No flicker/ghosting during resize or layout changes.
  - Correct z-order (`raise_()` ensures on-top).

- Logging
  - GL init logs show `alphaBufferSize >= 8`.

- Platforms
  - Windows (ANGLE): transparent overlay works.
  - Linux (X11/Wayland): verify compositor on; overlay works.
  - macOS (Metal backends under Qt6): verify overlay behavior.

- Performance
  - Overlay update remains responsive; no excessive CPU/GPU spikes.

## Alternatives (if needed)

- QOpenGLWindow + `createWindowContainer(window, parent)`
  - Sometimes more reliable alpha composition than QOpenGLWidget on certain stacks.

- FBO → QImage → QPainter overlay
  - Guaranteed composition but potentially costly with 9 viewers; consider for thumbnails/low-FPS.

## Rollback

- If transparency remains broken on key platforms, revert to non-overlay layout (side-by-side) or use semi-transparent backgrounds as a stopgap, and track a spike using QOpenGLWindow.

## Next Steps

1) Apply alpha buffer change in `main.py` and add alpha logging.
2) Make overlay viewers child widgets and adjust z-order.
3) Normalize transparent mode in `ModanComponents.py` and enable `NoPartialUpdate`.
4) Switch matplotlib backend to `qtagg`.
5) Validate on Windows/Linux/macOS; iterate based on findings.

