# Thumbnail Overlay: Performance Upgrade and Rotation Debug

- Date: 2025-09-03
- Author: Codex CLI assistant
- Related: 20250903_039_PyQt6_QOpenGLWidget_transparency_issue.md, 20250903_040_QOpenGLWidget_transparency_fix_plan.md, 20250903_042_QOpenGLWidget_transparency_fix_applied.md

## Summary

Moved shape-grid thumbnails from Qt overlay to Matplotlib overlay for consistent transparency across platforms, then focused on making thumbnail updates fast during interaction while keeping final quality high. Added rotation-debug overlays to help align the main GL viewer’s viewpoint with thumbnails. Rotation preservation across drags remains partially unresolved and is parked for later.

## Key Changes

- Matplotlib overlay for thumbnails
  - Thumbnails are rendered offscreen (ObjectViewer3D) and composited onto the Matplotlib axes using `OffsetImage + AnnotationBbox`.
  - Removes platform issues with QOpenGLWidget transparency and avoids stacking Qt windows.

- Debounced, dual-mode thumbnail rendering
  - Live mode (dragging): low-cost updates (smaller size, oversample=1, MSAA=0), debounced (~90ms) to avoid spamming renders.
  - Final mode (on mouse release): single high-quality pass (larger size, oversample≥2, MSAA=4).
  - update_chart now schedules thumbnail draws; `_draw_shape_grid_thumbnails()` owns rendering.

- FBO caching + MSAA control
  - `ObjectViewer3D.render_to_image(width, height, samples)` caches FBOs by (w, h, samples) for reuse.
  - Enables switching between MSAA 0 (live) and MSAA 4 (final) without allocations.

- Rotation debug overlays
  - GL viewer overlay: shows local(GL) and global(GLOB) Euler angles.
  - Thumbnails overlay: shows global(G) and thumbnail(T) Euler angles per item (only in final mode to reduce noise).
  - Increased font sizes for readability.

- Attempts to preserve thumbnail rotation between drags
  - Final pass stores the applied global rotation matrix into each thumbnail view as a baseline (`_base_rotation`).
  - Live pass avoids resetting objects/rotations and only updates visuals.
  - show_analysis_result no longer resets thumbnail objects during routine updates (to avoid losing the baseline).

## Files Touched

- `ModanDialogs.py`
  - Added `_request_thumbnail_refresh()` and `_draw_shape_grid_thumbnails()` with live/final modes.
  - Switched to debounced scheduling from `update_chart()`.
  - Avoid resetting thumbnail objects in `show_analysis_result`; preserve baseline rotation; improved debug overlays with larger fonts.
  - Hooked into `sync_temp_rotation` (live) and `sync_rotation_with_deltas` (final) to trigger appropriate refreshes.

- `ModanComponents.py`
  - `render_to_image(width, height, samples=0)`: FBO cache + MSAA control.
  - GL viewer `paintGL()`: added rotation debug overlay (GL vs Global) with readable font and background box.
  - `sync_rotation()`: ensures internal rotation_matrix is updated on commit; `get_rotation_matrix()` accessor added.

- `main.py`
  - Previously: alpha buffer default format for QOpenGLWidget (kept as part of transparency fixes).

## Perf Behavior (expected)

- Dragging: thumbnails update smoothly with lower cost and without blocking UI.
- Release: thumbnails redraw once at high quality (crisp wireframe, consistent point sizes).

## Known Issues / Next Steps

- Rotation preservation on thumbnails across separate drags is still inconsistent in some paths.
  - Hypothesis: An indirect `set_object()` may still reset baseline in certain update flows.
  - Options:
    - Add `set_rotation_matrix_abs(R)` to thumbnails and apply absolute rotation without relying on previous state.
    - Strictly avoid `set_object()` except when underlying data changes; gate by a stable shape key/version.
    - On `mousePress`, snapshot thumbnails’ current baseline and only apply temp deltas during move; finalize on release.

- Artist reuse: current implementation removes/recreates Matplotlib artists each pass. Reusing `OffsetImage` and updating data in place will further reduce redraw overhead.

- Debug toggles: add a UI/flag to toggle rotation debug overlays (currently always on in final mode for thumbnails; always on for GL viewer).

## How to Validate

- Interaction
  - Drag the GL viewer: thumbnails should update smoothly (no heavy lag).
  - Release: thumbnails should sharpen (oversample/MSAA applied) and match GL viewpoint.

- Transparency
  - Generated images (e.g., `graph.png`) should show clean overlays without opaque backgrounds.

- Logs/Overlays
  - GL viewer overlay shows `GL:` and `GLOB:` Euler angles.
  - Thumbnails (final) show `G:` and `T:`; these should converge when rotation sync is correct.

## Rollback Plan

- To revert to previous simpler behavior: disable debounced scheduling and call `_draw_shape_grid_thumbnails()` directly in `update_chart()`; set `samples=0`, `oversample=1` for all paths.

