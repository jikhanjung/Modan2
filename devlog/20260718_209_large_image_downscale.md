# 209 — Downscale oversized images in the 2D viewer (perf)

**Date:** 2026-07-18
**Type:** implementation — performance
**Trigger:** User report — a ~20 MB image makes the object viewer noticeably slow.

## Problem

`ObjectViewer2D.set_image` did `QPixmap(file_path)`, decoding the full-resolution
image (a 20 MB / ~24 MP photo → ~96 MB in memory). This decode runs every time the
object is shown (main-window selection, overlay preview, ObjectDialog), and every
zoom re-scales that full pixmap. Result: sluggish browsing and zooming.

## Fix

Decode a **downscaled render source** for oversized images while keeping the
**true pixel dimensions** for all coordinate math.

- New `_load_render_pixmap()`: reads the header size via `QImageReader` (no full
  decode), records the true `orig_width/orig_height`, and — only when the longer
  side exceeds `MAX_RENDER_DIM` (2560) — uses `QImageReader.setScaledSize()` to
  decode straight to the capped size. Falls back to a full `QPixmap` load if the
  size can't be read.
- Coordinate math now keys off `self.orig_width/height` (the true dims) instead of
  `orig_pixmap.width()/height()`: the mouse-bounds check, `calculate_resize`'s
  `image_canvas_ratio`, and the `.scaled()` targets in `adjust_scale` /
  `calculate_resize`. Landmarks are stored in original-image pixels, so the
  image↔canvas mapping is byte-for-byte unchanged; only the *display* source is
  smaller.

### Why 2560

Measured on a synthetic 6000×4000 JPEG:

| render cap | decode |
|-----------|--------|
| full (6000) | 146 ms |
| 4096 | 132 ms |
| **2560** | **57 ms (2.6×)** |
| 2048 | 44 ms (3.3×) |

libjpeg's DCT downscaling only engages well below the source half-size, so 4096
barely helps. 2560 gives a 2.6× decode win and ~5.5× less memory, and stays ≥
typical display widths so fit/moderate-zoom is still sharp. Trade-off: extreme
zoom on a huge image is softer than before — but landmark coordinates are exact.

## Tests

`tests/test_object_viewer_2d_image_scaling.py`: small image untouched; large image
downscaled with true dims preserved; coordinate mapping keys off true dims;
missing image → null pixmap + sentinel dims. Full viewer/object suites: 83 passed.
