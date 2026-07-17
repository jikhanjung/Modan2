# 198 — Error-handling audit: missing try/except (silent-crash risks)

**Date:** 2026-07-17
**Type:** review / audit (checklist for follow-up fixes)
**Trigger:** Two silent-crash bugs fixed this session (dataset-tree click → `load_object`;
analysis "Save Results" → Excel export). User asked for a codebase-wide checklist of
similar unguarded spots.

## Why this matters

In this PyQt5 app, an unhandled exception raised inside a **Qt signal handler (slot)**
does not surface — the window just dies with no message. The same applies to external
**file parsers** (malformed TPS/NTS/OBJ/…) and **file/DB I/O** reachable from a user
action. The goal is to wrap these so failures are logged and shown, not silent.

## Method

Three parallel audits by area: `Modan2.py` (main window slots), `dialogs/*.py`
(dialog handlers), and `components/` + `MdModel.py` + `MdUtils.py` (parsers, viewers,
file/DB I/O). Line numbers are as-of-audit and may drift.

**Already fixed (excluded):** `ObjectDialog.save_object`/`Delete`,
`DatasetAnalysisDialog.on_btnSaveResults_clicked`, `Modan2.load_object` (per-object
guard), controller `save_object`/`delete_object_with_files`/`import_dataset`.
**Already well-guarded (excluded):** `dataset_dialog.Okay`, `analysis_dialog.btnOK_clicked`,
`import_dialog._import_json_zip`, `export_dialog._export_json_zip`/`update_estimated_size`,
`MdImage.add_file`, MdUtils `read_tps_file`/`read_nts_file`/`read_landmark_file`.

---

## 🔴 Priority 1 — High (user action → file/DB/parse with no guard → silent death)

### A. External file parsers (malformed files crash import)
- [ ] `components/formats/tps.py:66` — `TPS.read`: `int()` header + `float()` coords; bad TPS → ValueError/IndexError
- [ ] `components/formats/nts.py:64` — `NTS.read`: `int()` header, `variable_count/dimension` division (ZeroDivision), row-index overrun
- [ ] `components/formats/x1y1.py:66` — `X1Y1.read`: empty file / odd column count → IndexError
- [ ] `components/formats/morphologika.py:61` — `Morphologika.read`: bare `open()` (no `with` → handle leak) + KeyError on missing sections
- [ ] `dialogs/import_dialog.py:313` — `import_file → _get_import_data`: constructs the above parsers unguarded (JSON+ZIP path is guarded, this one isn't)

### B. Main-window drop / import slots (file + DB, cursor left stuck)
- [ ] `Modan2.py:1488` — `tableView_drop_event`: file-drop import (`add_image`/`add_threed_model`+save); **sets WaitCursor without try/finally** → on error cursor stays frozen *and* app crashes
- [ ] `Modan2.py:1337` — `dropEvent`: drag-drop object/image copy (DB+file); progress dialog left open on error

### C. DB delete/save slots
- [ ] `Modan2.py:1036` — `on_action_delete_object_triggered`: `delete_instance()` in a loop, mid-loop failure
- [ ] `Modan2.py:1091` — `on_action_delete_analysis_triggered`: analysis delete + reload
- [ ] `Modan2.py:1026` — `on_btnSaveChanges_clicked`: `save_object_info()` DB write
- [ ] `Modan2.py:1014` — `on_action_add_variable_triggered`: user text → DB save + reload
- [ ] `dialogs/dataset_dialog.py:355` — `Delete`: `dataset.delete_instance()` (FK/locked row)

### D. Open-dialog / double-click chains (DB reload)
- [ ] `Modan2.py:1258` — `on_tableView_doubleClicked`: ObjectDialog + reset/reload chain
- [ ] `Modan2.py:1181` — `on_treeView_doubleClicked`: `selected_dataset` None → AttributeError; `get_by_id`/DoesNotExist

### E. Analysis / export slots (numpy + file I/O)
- [ ] `dialogs/dataset_analysis_dialog.py:757` — `on_btn_analysis_clicked`: `PerformCVA/PerformPCA` + `rotated_matrix.tolist()`; singular covariance/None result → LinAlgError/AttributeError, **wait cursor left stuck**
- [ ] `dialogs/export_dialog.py:278` — `export_dataset`: procrustes + `_export_tps`/`_export_morphologika` (open/write, get_by_id, `shutil.copyfile`) all unguarded
- [ ] `dialogs/calibration_dialog.py:105` — `btnOK_clicked`: `float(self.edtLength.text())` on empty/non-numeric input

### F. Central DB routine (fans out to many slots — high leverage) ⭐
- [ ] `Modan2.py:1589` — `load_dataset`: `MdDataset.filter`, `.count()`, `unpack_wireframe()`; wired to the Reload action **and every controller signal** (`on_dataset_created/updated`, `on_object_added/updated`, `on_analysis_completed`). One guard here protects many entry points.

### G. 3D-model file I/O (asymmetric with the guarded image path)
- [ ] `MdModel.py:772` — `MdThreeDModel.add_file`: `os.makedirs`/`shutil.copyfile` unguarded → DB row without its file (data loss)
- [ ] `MdModel.py:786` — `MdThreeDModel.load_file_info`: `os.stat` unguarded
- [ ] `components/viewers/object_viewer_3d.py:658` — `set_threed_model`: `OBJ()` parse unguarded; **`.ply`/`.stl` silently do nothing** (no model set, no error)

---

## 🟡 Priority 2 — Med (risky but partial/less-common path)

- [ ] `Modan2.py:1763` — `on_object_selection_changed`: `get_by_id`/`unpack_landmark` on row click
- [ ] `Modan2.py:1420` — `get_selected_object_list`: `_data[row][0]["value"]` + `int()` (IndexError/KeyError/ValueError); feeds several slots
- [ ] `Modan2.py:992` — `btnDataExploration_clicked`: `group_by` unbound (NameError) if tab isn't PCA/CVA/MANOVA
- [ ] `Modan2.py:984` / `Modan2.py:1108` — `btnAnalysisDetail_clicked` / `on_action_explore_data_triggered`: AttributeError when analysis is None
- [ ] `Modan2.py:1056` — `open_treeview_menu`: `itemFromIndex(index)` may be None → AttributeError
- [ ] `Modan2.py:1637` — `on_dataset_selection_changed`: DB/UI-swap around the (now-guarded) `load_object`
- [ ] `dialogs/dataset_analysis_dialog.py:951` — `show_result_table`: `get_by_id` + `rotated_matrix.tolist()` (reached from the unguarded analysis slots)
- [ ] `dialogs/data_exploration_dialog.py:1279` — `update_chart → _finalize_scatter_groups`: `ConvexHull(points)` → QhullError on collinear/degenerate group when the checkbox is toggled
- [ ] `dialogs/data_exploration_dialog.py:1536` — `set_analysis`: `json.loads` of object_info/pca/cva JSON (outside the existing try) → corrupt DB JSON crashes
- [ ] `dialogs/data_exploration_dialog.py:2545` — `unrotate_shape`: `json.loads` + `np.linalg.inv` (singular matrix / corrupt JSON)
- [ ] `dialogs/object_dialog.py:851` — `x_changed`: `add_landmark` → `float(x)/float(y)` on pasted non-numeric text (textChanged slot)
- [ ] `dialogs/object_dialog.py:384` — `btnAddFile_clicked`: `process_3d_file`/`set_threed_model` (trimesh/cv2) on corrupt/unsupported file
- [ ] `MdModel.py:342` — `change_dataset`: `os.remove` then `os.rename` — if rename fails, media lost moving object between datasets
- [ ] `MdUtils.py:755` — `import_dataset_from_zip`: `atomic()` rolls back DB but **copied files are orphaned**; `int(dimension)`/`float(ppm)` on bad manifest
- [ ] `MdUtils.py:736` / `MdUtils.py:749` — `safe_extract_zip` / `read_json_from_zip`: corrupt zip/manifest → BadZipFile/JSONDecodeError
- [ ] `MdUtils.py:646` — `create_zip_package`: `json.dump` + zip write unguarded (export)
- [ ] `MdModel.py:1453` — `MdDatasetOps.rotation_matrix`: `np.linalg.svd` → LinAlgError on degenerate/missing-landmark data
- [ ] `MdModel.py:993` — `MdObjectOps.rescale_to_unitsize`: `1/centroid_size` → ZeroDivision when centroid is 0

---

## ⚪ Priority 3 — Low (no crash, or rare/defensive)

- [ ] `components/viewers/object_viewer_2d.py:1067` — `set_image`: corrupt image → **silently blank** pixmap (no crash, but no validation/log)
- [ ] `dialogs/data_exploration_dialog.py:822` — `create_video_from_frames`: cv2 encode/codec failure in a QTimer callback silently aborts recording
- [ ] `dialogs/data_exploration_dialog.py:870` — `animate_shape`: `int(self.edtNumFrames.text())` on non-numeric input
- [ ] `Modan2.py:704` / `:711` / `:1114` — `closeEvent` / preferences / import outer slots (mostly guarded internally)
- [ ] `MdModel.py:613` — `MdImage.load_file_info`: `os.stat` (only reached via the guarded `add_file`)

---

## Recommended remediation (not yet applied)

Rather than 40+ ad-hoc `try/except` blocks, prefer a small shared pattern:

1. **A slot-guard decorator** for user-triggered handlers, e.g.
   `@guard_slot("Failed to …")` that wraps the body in try/except, logs with
   traceback, restores any override cursor, and shows a `QMessageBox`. Apply to the
   High-priority main-window/dialog slots (groups B–E).
2. **Parser hardening** (group A): give each `components/formats/*.read` a top-level
   try/except that raises a single typed `ImportError`-style message the import slot
   can show; use `with open(...)` everywhere (fixes the Morphologika handle leak).
3. **Symmetry fix** (group G): mirror `MdImage.add_file`'s existing guard in
   `MdThreeDModel.add_file`, and handle `.ply`/`.stl` in `set_threed_model`.
4. **High leverage first**: `Modan2.load_dataset` (F) — one guard covers the Reload
   action and all controller-signal refreshes.

Suggested order: A + F + G (broad coverage) → B/C/D/E (per-slot) → Med → Low.

## Status

Audit only — **no code changed** in this devlog. Pick a batch to implement next.

---

## Remediation complete (2026-07-18)

All actionable items above were implemented across ten batches:

**High** — parsers + main-window/dialog slots + 3D I/O
- batch 1 (199, `ff00021`) — main-window High slots via `guard_slot`
- batch 2 (200, `05a6d21`) — external file parsers hardened
- batch 3 (201, `8ce21b8`) — 3D-model file I/O (`MdThreeDModel`, viewer)
- batch 4 (202, `5a7774a`) — remaining dialog High slots + `guard_slot` arg fix

**Med**
- batch 5 (203, `88ccfbf`) — Modan2 Med slots + defensive selection parsing
- batch 6 (204, `8013ab3`) — data-exploration (update_chart, ConvexHull, unrotate)
- batch 7 (205, `b3d662e`) — analysis/object dialogs (show_analysis_result, x_changed)
- batch 8 (206, `23a4b27`) — MdModel (change_dataset move-before-save, svd, rescale)
- batch 9 (207, `b0500f7`) — zip import (orphan cleanup, manifest guards)

**Low**
- batch 10 (208, `5eb220d`) — viewer/animation (set_image, video, animate_shape)

Deliberately left as-is (documented in 208): `Modan2.closeEvent`/preferences/import
outer slots (mostly guarded internally; guarding `closeEvent` risks the
accept/ignore handshake) and `MdImage.load_file_info` (only reached via the guarded
`add_file`).
