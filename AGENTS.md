# Agents & Collaboration Guide

Purpose: Document who does what, and how we coordinate day-to-day so work stays fast, safe, and consistent.

## Roles

- Claude Code: Primary implementer
  - Drives most coding tasks and file edits.
  - Creates/updates devlog entries for material changes.
  - Opens PRs, runs tests locally/CI, and iterates on review feedback.
  - Takes point on experimental spikes (e.g., quick-test branches) and follow-up hardening.

- Codex CLI assistant (this agent): Planner, reviewer, and safety rails
  - Synthesizes repo/devlog context and proposes actionable plans.
  - Highlights risks, suggests minimal patches, and keeps changes scoped.
  - Uses short preambles before tools; keeps progress crisp.
  - Avoids long-running or destructive commands without approval.

## Current Focus: PyQt5 → PyQt6 Migration

- Primary strategy (approved):
  - Introduce a compatibility layer (`qt_compat.py`) to support PyQt5/6 dual-run.
  - Prepare an automated conversion script for common changes (imports, `.exec_()` → `.exec()`, enums).
  - Switch matplotlib backend to `qtagg` (or `QtAgg`) for dual compatibility.
  - Replace deprecated APIs (e.g., `QDesktopWidget` → `QGuiApplication.primaryScreen()`).
  - Expand enum namespaces (AlignmentFlag, AspectRatioMode, MouseButton, KeyboardModifier, Key_*, DropAction, ItemFlag, Orientation, etc.).
  - Maintain CI matrix to exercise both PyQt5 and PyQt6; PyQt6 may be allow-fail initially.

- Experimental strategy (spike):
  - Branch `feature/pyqt6-quick-test` for rapid “bulk change → run → learn” experiments.
  - If import/attribute errors are too broad, exit spike quickly and continue with the compatibility-first plan.

## Branching & Workflow

- Main branches
  - `main`: Stable (current PyQt5 baseline).
  - `feature/pyqt6-migration`: Compatibility-first migration work.
  - `feature/pyqt6-quick-test`: Spike-only, safe to fail; commit results regardless for learning.

- Commits & Devlog
  - Link significant commits to a matching `devlog/YYYYMMDD_XXX_*` entry.
  - Keep entries concise: context → change → outcome → next steps.

- PR Guidelines
  - Small, focused diffs; no unrelated refactors.
  - Include a quick test plan and expected risks.
  - Prefer idempotent scripts and reversible changes.

## Testing & CI

- Tests
  - Run unit/integration tests locally before PR where practical.
  - For GUI/OpenGL, use smoke/offscreen tests to catch regressions early.

- CI Matrix
  - Add PyQt5 and PyQt6 jobs; start PyQt6 as allow-fail until green.
  - Keep OpenGL smoke test in both jobs.

## Packaging Notes

- PyQt6 builds may require updated Qt plugin collection (PyInstaller):
  - Consider `--collect-submodules PyQt6` early; minimize later.
  - Verify ANGLE/Software/Platform plugins presence on Windows.

## Working Agreements

- Preambles: 1–2 lines describing grouped actions before tool use.
- Plans: Use short, verifiable steps when tasks span phases or teams.
- Safety: No destructive ops (e.g., `rm -rf`, reset) without explicit ask.
- Brevity: Keep messages tight; surface only what unblocks the next move.

## Next Concrete Steps (owner: Claude Code)

- Add `qt_compat.py` with conditional imports and thin helpers:
  - Export QtCore/QtGui/QtWidgets/Qt, `QOpenGLWidget`, `app_exec()`, `exec_dialog()`.
  - Normalize common enums via aliases for PyQt5/6.
- Switch matplotlib imports from `backend_qt5agg` to `backend_qtagg` (or `QtAgg`).
- Prepare conversion script (dry-run + report + backups) for `.exec_()` and frequent enum/import changes.
- Replace `QDesktopWidget` usage with `QGuiApplication.primaryScreen()` equivalents.
- Enable CI jobs for PyQt6 (allow-fail initially) and run OpenGL smoke tests in both.

This file reflects that Claude Code leads most implementation. The assistant supports with planning, reviews, and targeted patches when helpful.

