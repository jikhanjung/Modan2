# 208 — Harden Low viewer/animation paths (audit batch 10, Low)

**Date:** 2026-07-18
**Type:** implementation (NNN) — error-handling hardening (audit batch 10, Low)
**Related:** `devlog/20260717_198_error_handling_audit.md`, `..._207_...`

## What

The meaningful Low-tier items (§Priority 3 of the audit):

- **`object_viewer_2d.set_image` blank-pixmap log**: `QPixmap(file_path)` fails
  silently on a missing/corrupt/unsupported image — the viewer just goes blank with
  no clue why. Now checks `isNull()` and logs a warning. (No exception raised, so no
  user dialog — purely diagnostic, matching the Low severity.)

- **`data_exploration.create_video_from_frames` cv2 guard**: runs inside a `QTimer`
  timeout callback; a cv2 codec/encode failure would escape the callback, abort
  recording silently, and skip the following `restoreOverrideCursor()` (stuck
  cursor). The `VideoWriter` block is now `try/except/finally` — errors are logged
  and shown, and `video.release()` / `destroyAllWindows()` always run.

- **`data_exploration.animate_shape` frame-count guard + `@guard_slot`**: the
  `btnAnimate` slot did `int(self.edtNumFrames.text())` *after* setting the wait
  cursor — a non-numeric value raised and left the cursor stuck. The parse now
  happens before the cursor is set and falls back to 60; `@guard_slot` is the
  backstop.

## Deliberately not changed (Low, already covered)

- `Modan2.closeEvent` / preferences / import outer slots — the audit notes these are
  "mostly guarded internally"; wrapping `closeEvent` in `@guard_slot` risks
  swallowing the accept/ignore handshake, so it's left as-is.
- `MdImage.load_file_info` (`os.stat`) — only reachable via `MdImage.add_file`, which
  is already guarded. A second guard here would be redundant.

## Verification

- `ruff check --fix` + `ruff format` — clean.
- `pytest -k "exploration or viewer"` — 66 passed, 3 skipped.

## Audit status — High + Med + Low complete

Every actionable item in devlog 198 is now addressed across batches 1–10. A full
regression run follows this batch.
