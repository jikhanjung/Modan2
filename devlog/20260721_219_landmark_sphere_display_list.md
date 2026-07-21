# 219 — Landmark spheres via a cached display list

**Date:** 2026-07-21
**Type:** implementation (NNN) — performance

## Problem

`ObjectViewer3D.draw_object` rendered every landmark sphere with
`glutSolidSphere(r, 10, 10)` — immediate mode, re-tessellated on every call.
Each sphere is ~180 triangles generated CPU-side and pushed vertex-by-vertex
through the driver, per landmark, per frame. Three multipliers stack on top:

- In `EDIT_LANDMARK`/`WIREFRAME` mode `paintGL` draws the whole scene twice
  (picker buffer + screen).
- Mouse drags repaint on every mouse-move event; auto-rotate repaints on a
  50 ms timer.
- Each sphere also paid Python-level `glPushMatrix`/`glTranslate`/`try-except`
  overhead, with a three-way GLUT/GLU/point fallback at both call sites.

Rotating a 3D object with spheres on was visibly sluggish.

## Change

`components/viewers/object_viewer_3d.py`:

- `_sphere_display_list()` compiles a **unit sphere once per GL context**
  (GLU quadric, `glNewList`/`glEndList`) and caches the list id in
  `self.sphere_list`. `initializeGL` resets the cache because display lists
  don't survive context re-creation.
- `draw_sphere(radius)` is now `glScalef(r, r, r)` + `glCallList` — no
  re-tessellation. Callers already wrap it in push/pop matrix, so the scale
  doesn't leak. `GL_NORMALIZE` is enabled in `initialize_frame_buffer` so
  lighting stays correct under the scale.
- Tessellation dropped 10×10 → **8×6** (`SPHERE_SLICES`/`SPHERE_STACKS`
  module constants): landmark spheres are a few pixels across, so this is
  visually identical at under half the triangle count.
- Both `glutSolidSphere` call sites and their fallback ladders collapsed to
  `self.draw_sphere(...)`; spheres no longer need GLUT at all (arrow
  cube/cone and index text still use it). If `glGenLists` fails the old
  direct-GLU and point fallbacks remain.

## Measured

Offscreen (WSL llvmpipe, software GL), 20 000 spheres:

| path | time |
|---|---|
| `glutSolidSphere(10×10)` | 0.530 s |
| `gluSphere(10×10)` | 0.397 s |
| display list (8×6) | 0.324 s |

**1.6× vs the old path** under a software rasterizer, which is the floor for
this change — hardware drivers pay far more per immediate-mode vertex call
than llvmpipe does, so the win on real GPUs should be larger.

## Verification

- Offscreen smoke test: list compiles (id 1), repaints run clean.
- Full suite: 1402 passed, 71 skipped. `ruff check`/`format` clean.
