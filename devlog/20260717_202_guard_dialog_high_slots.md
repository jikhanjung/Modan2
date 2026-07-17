# 202 — Guard remaining High dialog slots + fix guard_slot arg handling

**Date:** 2026-07-17
**Type:** implementation (NNN) — error-handling hardening (audit batch 4)
**Related:** `devlog/20260717_198_error_handling_audit.md`, `199_...`

## What

Applied `@guard_slot` to the remaining High-priority dialog slots from the audit:
- `dataset_analysis_dialog.on_btn_analysis_clicked` — `PerformPCA/PerformCVA` numpy +
  `rotated_matrix.tolist()`; singular covariance / None result would crash and leave
  the **wait cursor stuck** (the decorator pops it).
- `export_dialog.export_dataset` — procrustes + TPS/Morphologika file writes.
- `calibration_dialog.btnOK_clicked` — `float()` of the length field.
- `dataset_dialog.Delete` — `delete_instance()`.

## Bug found & fixed in `guard_slot` itself

The original wrapper was `def wrapper(self, *args, **kwargs)`. PyQt inspects the
slot's signature to decide which signal args to pass; a variadic wrapper makes it
pass **all** of them (e.g. the `checked` bool from `clicked(bool)`), which the real
slot — often defined as just `def btnOK_clicked(self)` — then rejects with
`TypeError: takes 1 positional argument but 2 were given`. This surfaced as 5 failing
calibration/export tests.

Fix: `guard_slot` now inspects the wrapped function's signature and **truncates extra
positional args** to what it actually accepts (replicating PyQt's own leniency).
Slots that *do* declare the arg still receive it. This also retroactively hardens the
batch-1 main-window slots against the same issue.

## Verification

- `ruff check` + `ruff format` — clean.
- `tests/test_guard_slot.py` — added `test_guard_slot_truncates_extra_signal_args`
  (no-arg slot tolerates an extra bool; one-arg slot still gets its value).
- `pytest tests/dialogs/ tests/test_guard_slot.py` — 228 passed.
- Full suite — (pending / green).

## High batch — status

All audit **High** items are now guarded: parsers (200), 3D-model I/O (201),
main-window slots (199), dialog slots (202). Remaining audit work is **Med/Low**
(selection handlers, numeric-input `int()/float()`, zip file-orphaning, `ConvexHull`/
`svd` degeneracies) — separate follow-up.
