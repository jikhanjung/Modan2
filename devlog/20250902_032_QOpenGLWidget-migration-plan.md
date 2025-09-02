# QGLWidget → QOpenGLWidget Migration Plan (PyQt5)

**Target app:** Modan2 (PyQt5, Peewee, custom 2D/3D viewers)  
**Goal:** Replace legacy `QGLWidget` with `QOpenGLWidget` safely, improve stability across GPUs, and enable ANGLE/Software fallbacks while preserving existing rendering features.

---

## 0) Executive Summary

- **Why migrate?** `QGLWidget` is legacy and brittle on Windows (Desktop GL only, overlay semantics, timing issues). `QOpenGLWidget` is the Qt-recommended path, rendering to an internal FBO and compositing cleanly with other widgets. It supports **ANGLE (GLES)** and **software** fallbacks.
- **Strategy:** Do a **minimal-change migration** first (keep **Compatibility Profile**, keep GLU/immediate mode), then optionally modernize to Core Profile/VBOs later.
- **Success criteria:** App launches reliably from installer on clean Windows PCs; no crash at splash; 3D viewer renders correctly; fallback (`QT_OPENGL=angle/software`) both work.

---

## 1) Pre-Migration Checklist

- [ ] Branch off: `feature/qopenglwidget-migration`
- [ ] Ensure reproducible build env (same Python, PyQt, PyOpenGL versions as CI).
- [ ] Confirm **PyInstaller** collects Qt plugins and ANGLE/Software DLLs on CI.
- [ ] Prepare a **clean Windows VM** for validation (no VC++ redist, “bare” GPU driver).

**Artifacts to keep handy**
- App logs (`logging` already present).
- A small dataset to load quickly during smoke tests.
- CLI flags: `--no-splash` (for isolating splash timing), any existing safe-mode flags.

---

## 2) Inventory & Impact Analysis

- [ ] Find all classes inheriting from `QGLWidget` (e.g., `ObjectViewer3D`).  
- [ ] List GL usage: GLU, immediate mode, fixed-function matrix calls, FBOs, pick buffers, timers, etc.
- [ ] Identify code paths that do GL calls **outside** `initializeGL/resizeGL/paintGL`. Those must call `makeCurrent()`.
- [ ] Confirm any **shared GL resources** across widgets; plan for resource life-cycle under `QOpenGLWidget` (FBO re-creation on resize).

---

## 3) Minimal Migration (Compatibility Profile, least changes)

> Goal: swap the widget class and wire up the correct surface format. Keep fixed-function/GLU working.

### 3.1 Replace imports & base class

**Before**
```python
from PyQt5.QtOpenGL import QGLWidget
class ObjectViewer3D(QGLWidget):
    ...
```

**After**
```python
from PyQt5.QtWidgets import QOpenGLWidget
class ObjectViewer3D(QOpenGLWidget):
    ...
```

> If you used `QGLFormat/QGLContext`, remove/replace them (see 3.2).

### 3.2 Set the default `QSurfaceFormat` early

- Do this **before** creating `QApplication` (or at least before constructing the GL widget). If early placement is hard, put it right after creating `QApplication`, but **before** showing any GL widget.

```python
from PyQt5.QtGui import QSurfaceFormat

fmt = QSurfaceFormat()
fmt.setVersion(2, 1)  # or (3, 0) / (3, 3). For GLU/immediate mode, 2.1 Compatibility is safe.
fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
fmt.setDepthBufferSize(24)
fmt.setStencilBufferSize(8)
fmt.setSamples(4)  # MSAA if desired
QSurfaceFormat.setDefaultFormat(fmt)
```

**Notes**
- **CompatibilityProfile** lets GLU/fixed-function calls continue to work.
- If you later target **Core Profile**, you must remove GLU & fixed-function usage (see §6).

### 3.3 Ensure robust size/aspect initialization

Guard first paints that can arrive **before** a resize:

```python
class ObjectViewer3D(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aspect = 1.0  # safe default

    def initializeGL(self):
        w = max(1, self.width()); h = max(1, self.height())
        self.aspect = w / float(h)
        # setup clear color, depth test, etc.

    def resizeGL(self, w, h):
        import OpenGL.GL as gl
        h = max(1, h)
        self.aspect = w / float(h)
        gl.glViewport(0, 0, w, h)
        # update projection matrix, etc.

    def paintGL(self):
        import OpenGL.GL as gl
        if self.width() <= 0 or self.height() <= 0:
            return
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        # draw_all(self.aspect) ...
```

### 3.4 GL calls outside paint path

If you upload textures/buffers **outside** `initializeGL/paintGL/resizeGL`, wrap with current context:

```python
self.makeCurrent()
# ... GL calls (create textures, buffers, FBO, shaders) ...
self.doneCurrent()
```

### 3.5 Resource life-cycle with QOpenGLWidget

- On **resize**, QOpenGLWidget recreates its internal FBO. Your GL state may need re-setup in `resizeGL()`.
- **Context loss/re-creation** can lead to `initializeGL()` being called again. Structure code so resource (re)upload is safe to repeat.

### 3.6 Lazy creation of the 3D widget (optional but recommended)

Create the 3D widget only when first needed, or at least **after** the main window is shown:

```python
self.object_view_3d = None

def ensure_3d(self):
    if self.object_view_3d is None:
        self.object_view_3d = ObjectViewer3D(self)
        self.object_view_3d.hide()
```

This reduces the chance of early GL initialization clashing with splash/event pumping.

---

## 4) App Startup & Fallbacks

### 4.1 Stop forcing Desktop GL

Remove any unconditional `os.environ["QT_OPENGL"]="desktop"`.

```python
import os, sys

# Prefer allowing fallbacks in frozen builds
if getattr(sys, "frozen", False) and "QT_OPENGL" not in os.environ:
    os.environ["QT_OPENGL"] = "angle"    # or "software"
```

**Runtime tests** (Windows CMD/PowerShell before launching app):
```
set QT_OPENGL=angle
set QT_OPENGL=software
set QT_OPENGL=desktop
```

If `angle/software` makes installer builds stable, the migration is doing its job.

### 4.2 (Optional) OpenGL debug messages

In PyQt5 you can use `QOpenGLDebugLogger` (if available) to capture driver messages. Enable only in dev mode.

---

## 5) Packaging & CI (PyInstaller + Inno Setup)

### 5.1 Ensure ANGLE/Software DLLs are packaged

Make sure `d3dcompiler_47.dll`, `libEGL.dll`, `libGLESv2.dll`, `opengl32sw.dll` are in the **same folder as the exe** (or alongside the Qt `bin` the app loads from). With PyInstaller, prefer `--collect-all=PyQt5` or explicit binaries in the `.spec`.

Example (spec snippet idea):
```python
binaries = [
    ("<venv>\\Lib\\site-packages\\PyQt5\\Qt\\bin\\d3dcompiler_47.dll", "."),
    ("<venv>\\Lib\\site-packages\\PyQt5\\Qt\\bin\\libEGL.dll", "."),
    ("<venv>\\Lib\\site-packages\\PyQt5\\Qt\\bin\\libGLESv2.dll", "."),
    ("<venv>\\Lib\\site-packages\\PyQt5\\Qt\\bin\\opengl32sw.dll", "."),
]
```

### 5.2 Include Qt plugins and keep folder structure

In **Inno Setup**:
```ini
[Files]
Source: "dist\\MyApp\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
```

Ensure `platforms\\qwindows.dll`, `imageformats\\*.dll`, `styles\\*.dll` are present. Use `qt.conf` if needed:
```
[Paths]
Plugins=PyQt5/Qt/plugins
```

### 5.3 VC++ runtime / SQLite

- Bundle `vcruntime*.dll` that PyInstaller collected or run the redist installer silently.
- Verify `_sqlite3.pyd` and `sqlite3.dll` are included (Peewee + SQLite).

---

## 6) Optional Phase 2: Modernize to Core Profile

> Only after minimal migration is stable.

- [ ] Change surface format to Core profile:
  ```python
  fmt.setVersion(3, 3)
  fmt.setProfile(QSurfaceFormat.CoreProfile)
  ```
- [ ] Remove **GLU** and **fixed-function** usage:
  - Replace `glMatrixMode/glLoadIdentity/gluPerspective` with your own matrix math (e.g., `pyrr`, `numpy`) + shaders.
  - Replace immediate mode (`glBegin/glEnd`) with VBO/VAO + `glDraw*`.
- [ ] Migrate picking and wireframe rendering to shader pipeline.
- [ ] Add shader compilation/validation and robust error logging.

---

## 7) Test Plan & Acceptance Criteria

### 7.1 Functional smoke tests
- [ ] App launch (with splash on/off).
- [ ] Open main window; 3D viewer created lazily; first render OK.
- [ ] Interactions: rotate/zoom/pick work; no flicker over other widgets.
- [ ] Switching datasets; resizing window; DPI scaling.

### 7.2 Fallback matrix (Windows)
| Mode            | Env Var             | Expected |
|-----------------|---------------------|----------|
| ANGLE (D3D)     | `QT_OPENGL=angle`   | OK       |
| Software (LLVM) | `QT_OPENGL=software`| OK (slower)|
| Desktop         | `QT_OPENGL=desktop` | OK on healthy drivers |

### 7.3 Clean VM install
- [ ] Fresh VM (no VC++ redist).
- [ ] Install from Inno Setup package.
- [ ] Run with each `QT_OPENGL` mode (angle/software/desktop).
- [ ] No crash; logs show steady init; 3D renders.

### 7.4 Acceptance
- [ ] No crashes at startup.
- [ ] 3D viewer stable under resize/switching monitors.
- [ ] Installer works on clean VM without manual dependencies.

---

## 8) Rollout & Rollback

- Rollout: Release as **beta** in GitHub Releases with a new tag (e.g., `vX.Y.0-rc1`).
- Crash guard: Provide a launcher that can set `QT_OPENGL=angle` if last run crashed.
- Rollback: Keep `QGLWidget` build recipe for one cycle; document how to switch back.

---

## 9) Code Snippets (Drop-in Examples)

### 9.1 App startup (surface format + fallbacks)

```python
# main.py
import os, sys
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import QApplication

# Prefer fallbacks in frozen builds unless user overrides
if getattr(sys, "frozen", False) and "QT_OPENGL" not in os.environ:
    os.environ["QT_OPENGL"] = "angle"  # or "software"

fmt = QSurfaceFormat()
fmt.setVersion(2, 1)
fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
fmt.setDepthBufferSize(24)
fmt.setStencilBufferSize(8)
QSurfaceFormat.setDefaultFormat(fmt)

app = QApplication(sys.argv)
# ... create & show main window ...
sys.exit(app.exec_())
```

### 9.2 QOpenGLWidget subclass skeleton

```python
from PyQt5.QtWidgets import QOpenGLWidget

class ObjectViewer3D(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aspect = 1.0

    def initializeGL(self):
        # GL state init (clear color, depth test on, etc.)
        w = max(1, self.width()); h = max(1, self.height())
        self.aspect = w / float(h)

    def resizeGL(self, w, h):
        import OpenGL.GL as gl
        h = max(1, h)
        self.aspect = w / float(h)
        gl.glViewport(0, 0, w, h)

    def paintGL(self):
        import OpenGL.GL as gl
        if self.width() <= 0 or self.height() <= 0:
            return
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        # draw_all(self.aspect)
```

---

## 10) Timeline (suggested)

- **Day 1–2:** Minimal migration (swap class, format, guards), local tests.
- **Day 3:** CI packaging & DLL verification; Inno Setup install tests.
- **Day 4:** Clean VM tests; fallback matrix.
- **Day 5:** Beta release & targeted user testing.
- **(Later):** Core Profile modernization (as separate milestone).

---

## 11) Known Pitfalls & Tips

- First paint can occur before first resize; **guard aspect/size**.
- Any GL code outside the GL callbacks requires **`makeCurrent()`**.
- `QOpenGLWidget` recreates its internal FBO on resize; be ready to **re-bind** state.
- Don’t force `QT_OPENGL=desktop` in production; allow ANGLE/Software fallback.
- Keep splash event pumping minimal while GL is initializing (or create GL after show()).
- Prefer **lazy 3D creation** to avoid startup timing issues.

---

## 12) Done Definition

- App launches & renders 3D **without crash** from the installer.
- Fallbacks validated (`angle`, `software`, `desktop`).
- Packaging includes necessary Qt plugins and ANGLE DLLs.
- Migration documented in CHANGELOG and release notes.

---

*Prepared for Modan2 migration to QOpenGLWidget.*
