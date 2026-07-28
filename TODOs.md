# Modan2 — Outstanding TODOs

Tracks remaining work from the **R01 code review**
(`devlog/20260625_R01_code_review_legacy_and_db_patterns.md`).

As of **2026-06-25**, all CRITICAL/HIGH **correctness** items and the HIGH
**statistics** items are done (see `devlog/20260625_152`–`175` and the table in
`HANDOFF.md`). What remains:

---

## 📌 2026-07-28 session — install location, installer identity, settings relocation

**Done** (devlog 272). The application was writing to **four** different
locations, two of them Roaming AppData. Now two: the program folder, and
`~/PaleoBytes/Modan2/` for everything the user owns.

- Installer: `{userappdata}` → `{localappdata}` (the ~130 MB onedir payload was
  syncing with roaming profiles); `PrivilegesRequired=lowest` (it was demanding
  UAC for a per-user install, and elevating as a *different* admin account
  installed into that account's folder); a stable GUID `AppId`;
  `AppPublisher` / `UninstallDisplayIcon` (both blank before).
- QSettings deleted — `MdHelpers.load_settings` / `save_window_state` /
  `restore_window_state` were dead since the 2025-08-29/30 JSON refactor
  (`2581a72`, `ca84a36`) and used a *different* organisation name than
  `main.py` set anyway.
- Preferences `~/.modan2/config.json` → `~/PaleoBytes/Modan2/preferences.json`,
  with automatic migration; path consolidated into `mu.DEFAULT_CONFIG_PATH`
  (the duplicate `MdConstants.CONFIG_DIR` is gone).
- Fixed `--config` reading one file and saving to another.
- `MdHelpers.get_app_data_dir` no longer uses Roaming AppData / `~/.modan2`.

**Left to do:**
- [x] **Inno compiles** — confirmed by the 0.2.0-beta.2 build (devlog 274): the
      Windows installer was produced, so the `[Code]`, the `{{` GUID escape and
      the directive changes are syntactically valid.
- [ ] **Runtime behaviour is still unverified — install the beta.2 artifact.**
      Compiling proves nothing about what the installer *does*: that it lands in
      `%LOCALAPPDATA%\Programs`, that `lowest` suppresses the UAC prompt, and that the
      legacy-detection prompt appears (and its three answers work).
- [ ] **Verify the legacy-install detection on Windows** (devlog 273). The
      installer now looks for the old `Modan2_is1` uninstall key and offers to
      run its uninstaller. The `[Code]` was checked structurally only —
      begin/end balance, declaration order, no `{{` collision with `build.py`'s
      placeholders — because Inno does not compile off Windows. Test all three
      answers (remove / keep both / cancel) **and** a fresh machine with no old
      install, where the prompt must not appear at all.
- [x] **`changelog` excluded from translation** — DONE 2026-07-28 (devlog 274).
      devlog 269 repointed `changelog.rst` at the full `CHANGELOG.md`, which made
      the entire release history translatable (111 untranslated / 18 fuzzy) and
      would have added work to every future release. `changelog.po` is deleted
      and git-ignored, so `sphinx-intl update` recreating it cannot drift back
      in; the Korean page renders the English source. devlog 262's "all 8
      catalogs at zero" now reads "all 7".
- [ ] **Make the data location configurable, then change its default**
      (raised 2026-07-28, devlog 276). Two items, in this order.

      **1. Configurable (higher value).** It currently is not.
      `dialogs/preferences_dialog.py:859` `select_folder` is labelled a "legacy
      method", the `edtDataFolder` widget it writes to **is never created**, the
      chosen path is stored only on the dialog instance, and `Modan2.py:568`
      overwrites `m_app.storage_directory` with `DEFAULT_STORAGE_DIRECTORY`
      unconditionally. So it is dead UI. Research setups legitimately want data
      on a network share or a specific volume — 3D models reach tens of GB — and
      `--db` moves only the database, not the media store. Wire the setting up
      and persist it in `preferences.json`.

      **2. Default → `~/Documents/PaleoBytes/Modan2`.** `~/PaleoBytes/Modan2/`
      matches no platform convention (Windows uses `%LOCALAPPDATA%\<Vendor>\<App>`
      or `Documents\`, macOS `~/Library/Application Support/`, Linux XDG
      `~/.local/share/`); the profile root is for known folders. It predates this
      session (`MdUtils.py:100`).

      Documents rather than `%LOCALAPPDATA%`, even though LocalAppData is the
      by-the-book answer for "application data": LocalAppData is Microsoft's
      place for machine-local data whose loss is survivable, and this is the
      user's only copy of their specimens, landmarks and analyses. It is also
      excluded from OneDrive Known Folder Move, so it would not fix the backup
      gap — **KFM covers Documents/Desktop/Pictures but not arbitrary
      profile-root folders**, which is the one concrete harm in the status quo:
      users who believe their files are in the cloud have the database silently
      left out. Documents is backed up by the tooling people actually have
      (OneDrive KFM, Time Machine), is findable when sending a dataset to a
      collaborator, and matches the semantics.

      Resolve it with `QStandardPaths.DocumentsLocation`, not by joining
      `expanduser("~")` with `"Documents"` — the former handles localised folder
      names (`문서` on Korean Windows) and redirected known folders.

      **Migration is the real work.** Unlike the install path, this relocates
      every existing user's database and media, and a failure loses data. First
      thing to check: whether media paths are stored relative or absolute.
      `MdModel.get_file_path(base_path=...)` taking a base path suggests
      relative, in which case moving the directory may suffice — **but verify
      before assuming.**
- [ ] **Orphaned `~/.modan2/`.** The legacy `config.json` is deliberately left
      behind (costs nothing, keeps older builds usable), and `~/.modan2/temp`
      is now unused. Consider removing both once the beta line is retired.

---

## 📌 2026-07-27 session — docs deployment

**Done** (devlog 260): fixed `docs.yml`, which had failed on **every** run since
2026-07-24, leaving GitHub Pages 411 commits behind main — the manual update in
`be09357` (semi-landmark curves, rewritten missing-landmark handling) never reached
the site, and the live page still documented a `Mark as Missing` flow that does not
exist. Two breakages, the first masking the second: sphinx pinned `>=9.1.0` (needs
Python >=3.12) while `docs.yml` was the last workflow on 3.11; and `conf.py` imports
`version.py` → `semver`, which was missing from `docs/requirements.txt`. Both builds
verified locally on 3.12.

**Also done** (devlog 261): the Korean locale was refreshed (`sphinx-intl update`) and
the 233 new/fuzzy entries across `user_guide` / `changelog` / `index` /
`developer_guide` / `installation` were translated, matching the app's own Korean UI
terms (중첩정렬, 강건적합, 결측 추가, 추정값 보기). The installation docs were rewritten
against the real release assets: portable Windows build removed (not published), the
per-platform file names corrected (installer ZIP / DMG / AppImage, all version-stamped),
a warning added that only the Windows build is well tested, and the "From Source" /
`python …py` instructions dropped from the user-facing pages.

**Also done** (devlog 262): the three stale guides (`advanced_features`,
`troubleshooting`, `faq`) were corrected against the code — a dozen documented
features did not exist (env vars, `--verbose`/`--no-3d`, most keyboard shortcuts,
3D viewer key handling, Full/Partial Procrustes, asymmetry analysis) and the
settings/database paths were wrong. Then all three were translated: 492 + 374 +
276 entries. **All 8 Korean catalogs are now at 0 untranslated/fuzzy** (1380
entries across devlogs 261–262). `main.py`'s `--db` help was corrected too.

**Left to do (docs):**
- [x] **`docs/*.md` is never published — 12 files.** From the CTHarvester addendum
      (`../CTHarvester/docs/CI_RECOMMENDATIONS_FOR_MODAN2.md`, 2026-07-27 §1):
      `conf.py` has no `myst_parser`, so Sphinx reads `.rst` only. **DONE
      2026-07-27** (devlog 263): the boundary is now a directory, not a convention
      nobody could see — the Sphinx project moved to `docs/manual/` (`.rst` only,
      published), and `docs/*.md` stays put as repository-only notes. `docs.yml`'s
      path trigger is scoped to `docs/manual/**`, so editing the notes no longer
      redeploys the site. Documented in `docs/README.md`, `docs/manual/README.md`,
      and `CLAUDE.md`.
- [x] **Fold the unpublished user-facing Markdown into the manual.** **DONE
      2026-07-27** (devlog 264): `USER_GUIDE.md` and `QUICK_START.md` merged and
      deleted. Reconciling them against the code turned up errors on *both* sides —
      the `.rst` documented a variable-type selector and per-column table editing
      that do not exist, and the `.md` claimed a batch calibration that does not
      either. What was genuinely missing and is now published: **Calibration**
      (absent from every `.rst`), **dataset editing/deleting/re-parenting**, a
      **Glossary**, and a **Quick Start** page. The stale TPS/NTS/Morphologika
      format appendix was deliberately *not* merged — its NTS example does not match
      the parser, which expects a header line.
- [x] **`developer_guide.md`** — **DONE 2026-07-27** (devlog 265). The "110 unique
      headings" figure was wrong: `grep "^#"` counted shell comments inside bash
      code fences, and the real count was 53 against the `.rst`'s 46. Merged after
      the same verification pass, which again found errors on both sides (the
      `.rst` said Python 3.11 and `python Modan2.py`; the `.md` documented an
      analysis-type switch, file readers in `MdUtils.py`, and an `MdLogger` module
      that does not exist). `docs/*.md` now holds only repository-only notes.
- [x] **File format reference** — **DONE 2026-07-27** (devlog 265). Deliberately
      skipped in devlog 264 because the `.md`'s NTS example did not match the
      parser; the parsers were read and the TPS / NTS / Morphologika / X1Y1 specs
      documented from what they actually accept.
- [x] **`C901` complexity ratchet** — **DONE 2026-07-27** (devlog 265). Set to 20
      after refactoring the single function above it. Note the campaign in devlog
      242 never actually got everything under 15 — 12 functions were over it before
      this session — and the CHANGELOG claim was corrected to match.
- [x] **Lower the ratchet to 19** — **DONE 2026-07-27**. 19 is the application's
      own ceiling; the limit had only sat higher because two `tools/` scripts (not
      imported by the app, not shipped) were above it. Both were split.
- [ ] **Keep stepping the ratchet down.** 10 functions are over 15: 7 in
      application code — `rotate_gls_to_reference_shape` (19), `on_canvas_move`
      (19), `mouseReleaseEvent` (17), `main` (17), `run_analysis` (16),
      `pick_shape` (16), `on_btnSaveResults_clicked` (16) — and 3 in `tests/` and
      `scripts/` (16 each). Note `run_analysis` was decomposed in devlog 176–178
      and has crept back to 16 as superimposition methods were added.
- [x] **`search_index.py --wait-cursor` does not complete** — **DONE 2026-07-27**.
      `file_stats` is keyed by basename, so 127 of 146 entries missed a direct path
      lookup and fell back to `rglob` over the whole tree — 127 full walks, on a
      `/mnt/d` mount. The basename key is the tool's interface (`--file
      object_dialog.py`), so it stayed; `build_index.py` now records the
      project-relative `path` alongside it and the search tool reads that.
      **10+ minutes (never finished) → 0.96 s.**
- [x] `developer_guide.rst` stale references — **DONE 2026-07-27**. Beyond the
      `python Modan2.py` sites, the release section told readers to bump the
      version in `MdUtils.py` (`PROGRAM_VERSION = "0.1.5"`) — it is imported from
      `version.py`, and `manage_version.py` is the actual tool. The project tree
      listed `MdLogger.py` (does not exist) and `ModanDialogs.py` (deleted), and
      the architecture diagram named both plus `modan.db`. All corrected, and the
      tree I had duplicated under Development Setup was folded back into the one
      in Project Overview.
- [ ] **A broken docs build went unnoticed for two days / 6 commits.** `docs.yml`
      is not a required status check, so its failures are invisible. Making it one
      needs branch protection, and `main` currently has **none** — enabling it would
      force a PR workflow on a repo that commits directly to main, so that is a
      workflow decision, not a config tweak. Partially mitigated in devlog 265:
      `version.py` was added to the `docs.yml` path trigger, closing a gap where a
      version bump would not have rebuilt the docs at all (`conf.py` imports it).
- [x] From the same addendum: the `C901` ratchet — **DONE 2026-07-27**, set to 19.
      PyOpenGL hidden imports remain informational only (Modan2's frozen smoke test
      passes on all three platforms, so the bundle is fine as built).

---

## 📌 2026-07-26 session — done, and what is left (recorded, not started)

**Done this session** (devlogs 249–259):
- Parser test coverage `x1y1`/`nts` + fixed the `x1y1` `nlandmarks==0` latent bug (249).
- Superimposition: fixed the no-op method selector, then **implemented Bookstein**
  (250–251), **rewrote Resistant Fit** as 2D+3D RFTRA (252–253), and added
  **missing-landmark imputation** to both (254). All three methods now work in 2D/3D.
- Controller info/warning messages → status bar (255).
- ZIP-import rollback removes orphaned media/dirs (256).
- `@guard_slot` on the two unguarded save slots (257).
- Ruff **DTZ** adopted (258). Low-risk cleanups: loggers / enumerate / inf sentinels (259).

**Left to do (recorded only — not started):**
- **Features (large):** 3D semi-landmark curve tracing (2D only today); sliding
  semi-landmarks during GPA; semi-landmark weighting; image-driven assisted
  landmark suggestion (§ Semi-landmarks below, items 2/2a/2b).
- **Ruff phased adoption (R05):** DTZ (258), **PIE/RET, SIM/PERF/A, G and C901 all
  done 2026-07-27** (devlog 266–268). Ignored with rationale in `pyproject.toml`:
  RET504, SIM102, SIM108, G004. **PTH is the only group left, and is deliberately
  deferred** — see below.
- **Ruff PTH (`os.path` → `pathlib`) — deferred, not skipped.** 322 violations:
  118 application, 189 tests, 18 tools. Split by risk:
  - **Predicate/action rules are safe** — they return bool or act in place, so no
    value crosses a boundary: PTH110 exists (62), PTH103 makedirs (11),
    PTH107/108 remove/unlink (24), PTH112 isdir (5), PTH116 stat (2),
    PTH202 getsize (5), PTH104/105 rename/replace (2), PTH208 listdir (3).
  - **Value-producing rules are the risk**: PTH120 dirname (88), PTH100 abspath
    (43), PTH118 join (26), PTH119 basename, PTH122 splitext, PTH111 expanduser,
    PTH123 open (41). `MdModel.get_file_path()` and friends return
    `os.path.join(...)`, i.e. a `str`, and that value flows into `shutil`,
    `open()`, string comparisons, the JSON+ZIP path handling, and DB fields.
    Returning a `Path` instead breaks some of those loudly and others **silently**
    — `Path("a") != "a"` is True, so a comparison against a stored string simply
    stops matching.
  Suggested order when picked up: predicates first (mechanical, verifiable by the
  suite), then the value rules one function at a time, checking each caller.
  Do not bulk-autofix this group.
- **MEDIUM/LOW cleanups still open:** in-method import hoisting; `if x==""`→`if not x`;
  vectorize `MdHelpers` thin helpers; builtin shadowing; redundant `float()`;
  dead branch `object_dialog.py:~936`; stale commented cruft; hardcoded `qt_version`.
- **Validation (needs real data — user):** sanity-check missing-landmark imputation
  on a real dataset; validate live-wire curve quality on real specimen photos.
- **CI / ops (user action):** set `LOCK_REFRESH_TOKEN` PAT; confirm the frozen-build
  smoke steps are green on the next release; promote required status checks in
  GitHub branch protection.
- **R02 deferred (dead path):** standalone `run_analysis("CVA")`/`("MANOVA")` never
  persist their result — fix if those entry points are ever revived (see HANDOFF).

---

## ✅ Batch C — Structural refactor (HIGH) — **COMPLETE** (devlog 176–193)

All four items done (god-method decomposition, shared scatter helpers, dialog I/O →
controller, read_settings/color-marker hoist), each on its own commit + devlog with
the suite kept green. Kept as a record below.

- [x] **Decompose god-methods** — all done
  - [x] `ModanController.run_analysis` (~360 lines) → done (devlog 176–178): split
        into `_extract_group_values` / `_prepare_landmarks` / `_persist_analysis_results`;
        type-overloaded return smell resolved
  - [x] `Modan2.py` `read_settings` (~250 lines) → done (devlog 185–186): `SettingsWrapper`
        hoisted to module level (+ unit tests) and `_restore_main_window_geometry` extracted;
        247 → 39 lines
  - [x] `dialogs/dataset_analysis_dialog.py` `__init__` (371 → 132 lines) → done (devlog 187):
        `_init_object_table` / `_init_plot_area` / `_init_bottom_controls`
  - [x] `dialogs/object_dialog.py` `__init__` (283 → 146 lines) → done (devlog 188):
        `_init_coord_input` / `_init_tool_buttons` / `_init_option_checkboxes` / `_init_action_buttons`
  - [x] `dialogs/data_exploration_dialog.py` `prepare_scatter_data` (285 lines) →
        done (devlog 179–180): golden-master net + split into 6 phase helpers
- [x] **Extract shared scatter-plot builder** — *rescoped & done* (devlog 181–184).
      The two sites are **not** a monolithic near-duplicate (different data sources,
      output structures, centroid/colour semantics), so a single builder was
      deliberately not built. Extracted the genuinely-shared seams into
      `dialogs/scatter_utils.py`: `build_scatter_group` (group-dict factory) and
      `build_scatter_legend`, applied in both dialogs. Guarded by unit tests + the
      exploration golden-master + a dataset-analysis smoke test.
- [x] **Move DB/file I/O out of dialogs into `ModanController`** — done (devlog 189–191)
  - [x] `dialogs/object_dialog.py` `save_object()` → `ModanController.save_object` (189);
        `Delete()` → `ModanController.delete_object_with_files` (190)
  - [x] `dialogs/import_dialog.py` direct DB writes → `ModanController.import_dataset`
        (+ `_import_object` / `_import_object_image`) (191)
  - Controller injected into both dialogs via `parent.controller` with an
    `isinstance(ModanController)` guard + standalone fallback for Mock/parentless tests.
- [x] **Hoist `read_settings` / color-marker loading** — done (devlog 192–193)
  - [x] `BaseDialog._restore_geometry(key, default_rect, move_offset)` — applied in
        `DatasetDialog` / `ExportDatasetDialog` / `AnalysisResultDialog` (192)
  - [x] module-level `load_color_marker_lists` — applied in `DataExplorationDialog` /
        `DatasetAnalysisDialog` (both `QDialog`, so a free function not a BaseDialog
        method) (193)

---

## ✅ Test infra — dialog-test memory accumulation — **RESOLVED 2026-07-21**

Investigated and fixed (devlog 224/225). Root cause was NOT a Python-side leak:
pytest-qt's teardown calls `deleteLater()`, but `DeferredDelete` events are never
delivered without an event loop, so every qtbot-registered widget tree survived
the session (~5000 live widgets, RSS to ~825 MB). Fixed with a
`pytest_runtest_logfinish` hook in `tests/conftest.py` that delivers the pending
deletes (`sendPostedEvents(None, DeferredDelete)` + `gc.collect(0)`). Peak RSS
825 → 531 MB, surviving widgets 0 per test.

The investigation also exposed a REAL app leak with the same symptom: parented
dialogs are never deleted on close, so every dialog ever opened accumulated as a
hidden child of the main window. Fixed in `Modan2.py` (WA_DeleteOnClose for
non-modal show() dialogs, deleteLater() after every exec_() site) — devlog 225.

---

## 🟠 R03 improvement review (2026-07-21) — see `devlog/20260721_R03_improvement_review.md`

Post-0.1.8 review items, in priority order:

- [x] **1. Orphaned files on image replacement** — DONE 2026-07-21 (devlog
      226): `update_image` now removes the old working copy and `originals/`
      archive before writing the replacement. The related deletion gap is done
      too (devlog 228): dataset deletion removes `<storage>/<ds.id>/`, object
      deletion removes the object's files, and both UI paths now go through the
      controller instead of calling `delete_instance()` directly.
- [x] **2. Unify display-estimate vs analysis-imputation** — DONE 2026-07-21
      (devlog 227). Both paths now share `MdModel.impute_missing_landmarks`
      (fit the mean onto the observed landmarks, then borrow the gaps). The
      analysis path turned out to be badly wrong, not merely different: it
      imputed before the first rotation and never revisited the value, giving
      61% of centroid size error on noise-free synthetic data. Rebuilt as EM
      refinement — now 0.0%. Worth a sanity check on a real dataset, since
      analysis output changes for datasets with missing landmarks.
- [x] **3. Qt.SmoothTransformation for viewer pixmap scaling** — DONE
      2026-07-21 (devlog 231). Benchmarking settled the cost worry: smooth is
      1.4–2.8x slower when downscaling but only 5–14 ms absolute, and ~3x
      *faster* when upscaling, so it was applied to both call sites.
- [x] **4. Korean translation update** — DONE 2026-07-21 (devlog 229): 237 →
      290 messages, 54 translated, 0 unfinished, `.qm` rebuilt and verified via
      QTranslator. Note the pylupdate5 trap documented there: entries that
      carry a translation but keep `type="unfinished"` are dropped by lrelease.
      Left alone: `translations/Modan2_en.ts` (empty translations fall back to
      the source, which is already correct). The stale root-level
      `Modan2_ko.ts`/`.qm` that nothing referenced were deleted.
- [x] **5. Refresh CLAUDE.md + `.index/`** — DONE 2026-07-21 (devlog 230):
      version, structure (dialogs//components/), test counts, pytest.ini
      location, key-file table, hotspots and stats all corrected against the
      repo. Also fixed `tools/build_index.py`, whose case-sensitive filename
      check meant `--dialog` searches had silently returned nothing since the
      dialogs moved into `dialogs/` (0 → 83 indexed).
- [x] **6. Triage skipped tests** — DONE 2026-07-21 (devlog 233). Only one skip
      was a genuine environment constraint; the largest group (37) was the main
      window's menu/toolbar/tree suites, switched off because a real
      `QDialog.exec_()` hangs a headless test. One autouse fixture in conftest
      now suppresses modal dialogs, and the stale expectations behind them were
      corrected. A second pass found the remaining "CI timeout" skips (29) were
      not timeouts either but tests written against APIs that never existed
      (`ModanDialogs`, `edit_dataset_name`, `on_action_export`); they were
      deleted, since `tests/dialogs/` and the six real workflow suites already
      cover those paths. Skips 74 → 8 (all legitimate), passing 1482 → 1518.

---

### Noted while triaging (not acted on)

- [x] Landmark-file readers in `components/formats/` (`tps.py`, `nts.py`,
      `x1y1.py`, `morphologika.py`) call `open(self.filename)` with no
      encoding, so they decode with the platform default. On Windows outside a
      UTF-8 locale a file containing non-ASCII specimen names fails to import.
      **DONE 2026-07-23**: added `components/formats/_encoding.py::open_text`
      (decode UTF-8 first, then the platform preferred encoding, then latin-1
      which never fails), swapped into all four readers. Tests in
      `tests/test_format_encoding.py` (utf-8 / cp949 / arbitrary bytes / BOM,
      plus TPS round-trip with a non-ASCII specimen name).

- [x] `ModanController` emits `warning_occurred` and `info_message`, but
      `Modan2.py` connected neither, so those messages were dropped.
      **DONE 2026-07-26** (devlog 255): the controller now owns the info/warning
      text and it is shown in the status bar (non-modal); the duplicate hardcoded
      `show_info` modals in `on_dataset_created`/`on_analysis_completed` were
      removed. Errors stay modal.

---

## 🟠 R06 CI-recommendations review (2026-07-24) — see `devlog/20260724_R06_ci_recommendations_review_and_quickwins.md`

All five CTHarvester CI recommendations are now resolved (3 shipped in commit
`b52bab0`/devlog 244; the remaining 3 in devlog 245):

- [x] **ruff `S` (flake8-bandit) ruleset** — DONE (devlog 245). Full triage of
      the 34 app-code findings (3751 of 3818 were test asserts): fixed the 2 real
      ones (`md5` → `usedforsecurity=False` in `MdModel`), globally ignored the
      pure-noise rules (S110/S112 intentional defensive suppression, S311
      non-crypto viewer random) with rationale, per-file-ignored dev/build-tool
      subprocess (S603/S607/S602), `# noqa`'d one type-narrowing assert. `S` now
      active app-wide for the valuable rules (eval/exec/pickle/unsafe-YAML/SQL);
      `ruff check .` clean.
- [x] **Packaged-artifact smoke test** — DONE (devlog 245). Added
      `main.py --self-test` (boots the full app headless, exits 0) and a
      smoke step in each of the 3 `reusable_build.yml` build jobs that launches
      the frozen onedir exe under `QT_QPA_PLATFORM=offscreen` (Linux needs Xvfb
      for glutInit). Catches the "broken when frozen" class. `tests/test_main_cli.py`
      guards the flag. **Watch:** verify the 3 steps are green on the next release
      build (first real CI validation).
- [x] **Retire `config/requirements-ci.txt`** — DONE (devlog 245). Removed (the
      dev lockfile is a superset); `config/README.md` + `CLAUDE.md` updated.
- [ ] **Set the `LOCK_REFRESH_TOKEN` PAT** (devlog 247) — one-time repo setup so
      Dependabot PRs that change a *pinned* dependency (which force a lockfile
      update) auto-refresh the locks AND re-run CI to green. Fine-grained PAT,
      Contents: Read/write, added as an Actions secret. Without it, such a PR's
      lock is refreshed but CI must be kicked manually (the `gh pr close && gh pr
      reopen` trick used on #24 works as a no-PAT fallback). PRs that only bump a
      floor (most) don't need it — the lock is unchanged.

Not adopted (agreed overkill for this solo commit-to-main repo; documented in
R06 §3): `dependency-review` action, a dedicated performance-tracking workflow,
a README-badge auto-commit bot.

---

## 🔵 Semi-landmarks & assisted digitizing (future features)

Feature work building on the semi-landmark support planned in
`devlog/20260722_237_semilandmark_support_plan.md`.

Semi-landmark status (2026-07-22): step 1 (data model + `resample_polyline` +
migration 007), the `build_landmarks_with_curves` core, and step 3 (TPS
`CURVES=` import) are done and tested. Remaining from that plan: the viewer
curve-drawing UI (step 2) and the dataset-dialog N input.

- [x] **1. Auto-detect the curve between anchor points.** **DONE 2026-07-23**
      (live-wire; devlog 240). "Snap to curve" follows the strongest image edge
      between clicks (Dijkstra on a gradient cost field + gradient-direction
      term), with smoothing and anchor-based editing/re-snap. The snapped trace
      is the raw curve that `resample_polyline` turns into semi-landmarks, so it
      slots straight into the existing pipeline. 2D only; 3D still open.

- [ ] **Outline analysis (elliptical Fourier).** Plan written 2026-07-27:
      `devlog/20260727_P02_outline_efa_support_plan.md`. This **reverses** the
      "out of scope" call in the semi-landmark plan (devlog 237), which
      underestimated how meaning-neutral the statistics and exploration layers
      already are — `PerformPCA` just flattens whatever vector it is given, and
      `unrotate_shape` is a pure linear inverse. EFA also has no alignment step,
      so its pipeline is *shorter* than the landmark one. Roughly: an EFA
      transform module, a dataset mode plus one branch in `_prepare_landmarks`,
      a synthesis path for rendering. Not started; priority against 3D curve
      tracing and sliding semi-landmarks is undecided.

- [ ] **2. Assisted landmark suggestion (longer-term).** Given the landmarks
      already placed on other specimens in the dataset, analyze the current
      specimen's image (2D first) to estimate and propose landmark positions for
      it, so digitizing a new specimen starts from a suggested configuration the
      user only corrects. Larger effort: image analysis / registration or a
      learned predictor trained on the dataset's existing landmark+image pairs.
      Note the app already has a *geometric* estimator for missing landmarks
      (`MdModel.impute_missing_landmarks`, devlog 227) — that fills gaps from
      shape alone and does not look at the image; this item is the
      image-driven counterpart.

  - [ ] **2a. Pre-analyze images for salient geometric features (supports 1 &
        2).** Landmarks are usually placed at geometrically distinctive spots,
        so pre-extract those from each image as landmark candidates: corners /
        line intersections, straight edges, contours/curves, and curvature
        extrema (극점). Cache the result per image so suggestion (item 2) and
        curve auto-detect (item 1) both draw on a ready feature set instead of
        re-analyzing on demand. Candidate tooling: OpenCV (already a dependency)
        — Canny/Hough for edges and lines, Harris/Shi-Tomasi for corners,
        contour extraction + curvature for curves and extrema.

  - [ ] **2b. Image-recognition engine — longer term, has upstream
        dependencies.** A learned recognition engine (beyond the classical CV of
        2a) is attractive but gated on prior data work done elsewhere:
        collecting and analyzing object detection / instance detection /
        segmentation datasets, especially for **fossils**. That upstream
        modeling has to exist before Modan2 can consume it downstream for
        landmark suggestion, so treat this as a later phase depending on those
        datasets/models being ready — not something to build inside Modan2 from
        scratch.

---

## 🟡 MEDIUM — deliberately deferred (low value / higher risk)

Skipped on purpose during the 2026-06-25 pass; revisit only if desired.

- [ ] In-method imports → hoist to module scope (some are intentional lazy /
      circular-import avoidance — needs per-site judgment)
- [ ] `if x == "" / x is None` → `if not x` (semantic risk: `0` / `[]` are falsy)
- [x] Magic sentinels `99999 / -99999` → `float('inf')` — **DONE 2026-07-26**
      (devlog 259): `data_exploration_dialog` `data_range` min/max seeds. Also
      fixed the latent bug where a coordinate > 99999 was wrongly clamped.
- [ ] Vectorize thin helpers in `MdHelpers.py` (centroid/bbox/translate) — not a
      live hotspot, so low priority

### Partially done (same pattern remains in other files)
- [x] Per-method `logger = getLogger(__name__)` recreation — **DONE 2026-07-26**
      (devlog 259): removed 10 sites in `Modan2.py` (same logger as the module's).
- [x] `for i in range(len(...))` → `enumerate`/`zip` — **DONE 2026-07-26**
      (devlog 259): `MdHelpers.py` (1) and `dialogs/preferences_dialog.py` (9).

---

## ⚪ LOW — nice-to-have

- [ ] Builtin shadowing (`object`, `sum`): `Modan2.py:~1037/1436`,
      `object_dialog.py:~711/1141`, `MdStatistics.py:~51`
- [ ] Py2-isms: drop redundant `float()` in `int(x / float(total) * 100)`
      (`Modan2.py:~1377/1515`)
- [ ] Dead branch `None if dim == 3 else None` (`dialogs/object_dialog.py:~936`)
- [ ] Stale commented-out cruft in `object_dialog.py` (dozens of `# self.x...`)
- [ ] Hardcoded `"qt_version": "5.15.x"` → `QT_VERSION_STR` (`MdHelpers.py:~982`)

---

*Done items (for reference): C1/C2/C4 DB correctness; N+1 #1/#2/#3; C3 eigenvalue
view-copy; CVA inv→pinv; 3D Z-coordinate; MANOVA truncation surfaced; CVA
covariance vectorization; latent bugs (regex/`is_numeric`/`utcnow`); `locals()`
control flow; `raise … from e`; module-level loggers (MdUtils/MdModel); `tr()`
i18n placeholders; dead-module & stale-spec removal; repo-wide ruff clean.*
