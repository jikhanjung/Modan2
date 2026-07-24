# Code Quality Guide — Multi-Platform Desktop Software

**Version**: 1.0
**Last Updated**: 2026-07-23
**Scope**: A comprehensive, reusable checklist of the code-quality practices a
cross-platform (Windows / macOS / Linux) desktop application should adopt —
written for a Python + Qt app (Modan2) but organized so the principles transfer
to any desktop stack.

---

## 0. Why desktop multi-platform is different

Most "code quality" advice is written for web services. Desktop software has a
different risk profile, and the checks must reflect it:

- **The user's machine is the production environment.** You don't control the
  OS, the Python/runtime version, the installed system libraries, the fonts, the
  locale, or the GPU. A bug that never appears on the developer's Linux box can
  crash every Windows user (real examples from this project: a Python 3.11-only
  `datetime.UTC` import, a broken `PyQt5.sip` binary, a missing `PIL._imaging`
  extension, Korean chart labels rendering as tofu because the font lacked the
  glyphs). **The single highest-leverage quality investment is testing on the
  platforms and runtime versions your users actually run.**
- **There is no "just redeploy."** A shipped installer is in the field. Rollbacks
  mean asking users to reinstall. This raises the bar on release verification.
- **A GUI event loop swallows or aborts on errors.** In Qt/PyQt, an unhandled
  exception in a slot can kill the window with no message. Robustness patterns
  (guarded slots, a global exception hook) matter more than in a request/response
  server that isolates failures per request.
- **Long-lived process, stateful UI.** Memory/handle leaks and widget-lifecycle
  bugs accumulate over a session instead of being reset every request.

The rest of this guide is organized as layers, from cheapest/most-automatic to
most-involved. Adopt top-down.

---

## 1. Formatting & Linting (static, cheap, always-on)

**Goal:** a consistent style and a large class of bugs caught before runtime.

- Use a single fast linter+formatter (this project: **Ruff**). One tool, one
  config, no black/isort/flake8 sprawl.
- **Format is not optional** — enforce via pre-commit so diffs stay clean.
- **Curate the lint ruleset deliberately.** Beyond the defaults (`E`, `F`, `I`,
  `N`, `UP`, `B`, `C4`), these rule groups repeatedly catch *real* desktop bugs:

  | Rule group | Catches | Why it matters here |
  |---|---|---|
  | `DTZ` | naive datetime / missing tzinfo | The `datetime.UTC` / timezone class of bugs |
  | `RUF012` | mutable class-level defaults | Shared-state-across-instances bugs (a real past defect) |
  | `S` (bandit) | eval/exec, `shell=True`, weak hash, unsafe yaml, path issues | Untrusted file parsing / process launching |
  | `TRY`, `LOG`, `G` | exception & logging anti-patterns | Silent failures, f-strings in logging |
  | `SIM`, `RET`, `PIE`, `PERF`, `A` | simplifications, dead returns, shadowed builtins | General rot |
  | `PTH` | `os.path` → `pathlib` | Path handling correctness across separators |
  | `C901` | function complexity (mccabe) | Flags mega-methods that hide bugs |

- **Adopt incrementally.** New rule groups on a mature codebase surface hundreds
  of findings. Turn on the zero-violation groups immediately; auto-fix the safe
  ones (`ruff check --select GRP --fix`, then run the test suite); for the noisy
  groups (`S`, `PTH`, `G`), either fix in a dedicated pass or scope to specific
  high-value rules. **Never bulk-`# noqa`; fix or deliberately ignore with a
  reason.**
- **Per-language exceptions belong in config, not scattered.** e.g. Qt uses
  camelCase, so `N802/N803/N806` are ignored globally with a comment.

## 2. Type checking (static, high-value, incremental)

**Goal:** catch wrong-type / None-misuse before it reaches a user.

- Add a static type checker (**mypy** or **pyright**). Most mature Python GUI
  apps start with *no* checker and *some* type hints; that's the worst of both —
  hints rot because nothing verifies them.
- **Adopt per-module, strict-on-new-code.** Enable the checker in CI but scope it
  to already-typed core modules first (statistics, model, utils), with a
  `[[tool.mypy.overrides]]` allowlist you expand over time. Don't try to type a
  32k-line codebase in one PR.
- Treat the checker as **advisory until a module is clean, then gating** for that
  module.

## 3. Testing strategy

**Goal:** behavior is pinned so refactors and platform differences are safe.

- **Layer the suite** and mark it so slices can run independently:
  - *Unit* — pure logic (stats, parsers, geometry), no GUI.
  - *Integration/workflow* — controller + DB + file I/O end to end.
  - *UI* — dialogs/viewers via a Qt test harness (**pytest-qt**), run **headless**
    (offscreen/xvfb) so they work in CI and over SSH.
  - *Performance* — benchmarks behind a marker, off by default.
- **Register markers** (`pytest.ini`) and use `--strict-markers` so typos fail.
- **Golden/characterization tests** for code you intend to refactor: pin the exact
  output structure so a "pure refactor" is provably behavior-preserving.
- **Regression test every fixed bug.** Each bug fix lands with a test that would
  have caught it (this is the project's standing practice — e.g. the None-axis
  scatter crash, the non-UTF-8 filename reader).
- **Property-based / fuzz testing** (**hypothesis**) for the fragile surfaces:
  file-format parsers (feed malformed/oversized/empty/mis-encoded input) and
  numeric routines (degenerate shapes, coincident points, zero-size). Desktop
  apps ingest user files; parsers are where crashes hide.

## 4. Test coverage

**Goal:** know what's untested; prevent silent erosion.

- Measure every CI run; **combine** coverage across the unit/dialog/integration
  phases into one report.
- **Set targets, then a gate.** Measuring without enforcing lets coverage drift.
  Two useful gates: an absolute floor (fail if overall < N%) and a **no-regression**
  check on PRs (fail if the diff lowers coverage). Start the floor *below* current
  coverage so it only ratchets up.
- Coverage is necessary, not sufficient — 100% line coverage of an unasserted
  path proves nothing. Pair with the property/regression tests above.

## 5. Cross-platform CI — the keystone for desktop

**This is the check most likely to be missing and most likely to catch
user-facing bugs.** A desktop app tested only on Linux is untested for most of its
users.

- **Matrix on OS × runtime version.** At minimum
  `{ubuntu, windows, macos} × {min-supported, max-supported Python}`. The bugs
  that only this catches: version-only stdlib symbols (`datetime.UTC` is 3.11+),
  path/separator/encoding differences, native-dependency breakage, font/rendering
  differences.
- **Pin the *minimum* supported version and test it.** If the code targets 3.12
  but users run 3.10, either test 3.10 or *enforce* 3.12 at install time — don't
  leave it implicit.
- **Add an import/smoke test to the matrix.** A test that simply imports every
  module and launches the app headless (`--no-splash`, offscreen Qt, then quit)
  turns import-time breakage into an immediate red build. This one cheap test
  would have caught `datetime.UTC`, `PyQt5.sip`, and `PIL._imaging` on Windows.
- **Make the checks gating.** Advisory checks (`ruff ... || true`, tests whose
  failure is swallowed) are quality theater — the signal exists but nothing acts
  on it. Once the tree is clean, remove the `|| true` and require the check for
  merge (branch protection).

## 6. Dependencies & reproducible environments

**Goal:** every machine — CI, a new contributor, a user's rebuild — gets the same,
working set of packages.

- **Lock your dependencies.** A loose `requirements.txt` lets a fresh install pull
  incompatible or half-broken wheels. Use a lockfile (**pip-tools** `pip-compile`,
  **uv**, or **Poetry**) with hashes, and install from the lock in CI and for
  releases. The corrupted-environment failures this project hit (a `PyQt5` install
  missing its `sip.pyd`, a `Pillow` missing `_imaging`) are exactly what a clean,
  locked, reproducible environment prevents.
- **Document a one-command clean rebuild** (`create env → install from lock →
  smoke test`) and prefer recreating a broken env over patching it package by
  package.
- **Automate dependency security & freshness:**
  - **Dependabot** (or Renovate) for update PRs.
  - **`pip-audit`** in CI to fail on known-vulnerable dependencies.
- **Separate runtime vs dev vs CI requirements** so the shipped app isn't bloated
  with test tooling.
- **Pin your *tooling* too, not just your dependencies.** An unpinned
  `pip install <linter>` in CI silently upgrades on every run, so an upstream
  release can turn a green tree red without any code change. (This project hit
  exactly that: a newer ruff began formatting Python blocks inside Markdown and
  reported "103 files would be reformatted".) Pin the linter/type-checker to the
  same version your pre-commit config uses, and upgrade deliberately.

## 7. Packaging & release verification

**Goal:** the thing you ship actually starts on a clean machine.

- **Build the installer per-OS in CI** (matrix), not just on the maintainer's
  laptop.
- **Smoke-test the *built artifact*, not just the source.** Install the produced
  package in a clean VM/runner and launch it headless. Source tests passing does
  not prove the frozen/packaged app (PyInstaller/py2app/MSIX) bundles every
  dependency and data file.
- **Verify data files, icons, translations, and native libs are bundled** — these
  are the usual "works from source, broken when frozen" gaps.
- **Sign** installers (Windows Authenticode, macOS notarization) so users aren't
  blocked by OS gatekeepers.
- Keep a written **release checklist** and version single-sourced.

## 8. Runtime robustness & error handling

**Goal:** a failure surfaces as a message, never a silent crash or corrupt state.

- **Guard every user-triggered handler that does I/O / parsing / DB / numeric
  work.** In Qt, wrap slots (a `guard_slot` decorator) so an exception is logged,
  the wait cursor is restored, and a dialog is shown — instead of the event loop
  aborting the process. Track coverage of this pattern; partial coverage is a
  false sense of safety.
- **Install a global exception hook** (`sys.excepthook`) as a backstop behind the
  per-slot guards, so an unguarded slot still logs and shows a non-fatal dialog.
- **Make operations atomic.** DB writes plus their side-effecting file I/O should
  be in a transaction that rolls back together, so a mid-operation failure can't
  leave a half-written record (a real past defect: an object row committed without
  its image).
- **Never report success on partial failure.** If a sub-step fails, tell the user;
  don't log a warning and emit "completed successfully" (a real past defect with
  CVA/MANOVA).
- **Treat warnings as errors in tests** (`filterwarnings = error`, scoped to
  categories you care about: missing-glyph, `DeprecationWarning`, numpy). This
  turns silent runtime degradation (tofu text, pending deprecations) into a test
  failure.

## 9. Resource & memory management

**Goal:** a long session doesn't leak handles, memory, or GUI objects.

- **Always context-manage files** (`with open(...)`); a parser that raises
  mid-read must not leak the handle.
- **Own the widget lifecycle.** Qt objects are C++-backed; `deleteLater()` needs
  an event loop to actually free them. In tests this leaks thousands of widgets +
  render buffers (this project saw ~800 MB RSS growth) until a `DeferredDelete`
  flush was added to teardown. In the app, dispose dialogs/figures you create.
- **Close what you open** — DB connections/cursors, matplotlib figures
  (`plt.close`), file dialogs, temp files/dirs.
- Periodically **profile memory** on a realistic session, not just correctness.

## 10. Internationalization, encoding & rendering

**Goal:** non-ASCII data and non-English locales work everywhere.

- **Always specify text encoding.** `open(path, encoding=...)` — never rely on the
  platform default (cp949 on Korean Windows vs utf-8 on Linux). For files of
  unknown origin, decode tolerantly (try utf-8-sig → locale → latin-1) so a
  legacy-encoded name degrades instead of aborting the import. (A real past
  defect: strict-utf-8 readers failing on non-ASCII specimen names.)
- **Handle BOMs** (`utf-8-sig`) so format detection on the first line isn't broken
  by a byte-order mark.
- **Fonts must cover the user's script.** For CJK/Arabic/etc., configure a font
  fallback chain **built from fonts actually installed on the machine** — listing
  an absent font spams warnings, and (matplotlib-specific) a generic family does
  not trigger per-glyph fallback; the concrete font names must be in the family
  list. Verify with a render test that produces no missing-glyph warnings.
- **Test with a non-English locale and non-ASCII data**, including file paths with
  spaces and non-ASCII characters.

## 11. Performance

**Goal:** known hotspots, no silent regressions.

- **Profile to find the real hotspot** before optimizing (line_profiler /
  memory_profiler / snakeviz). In this app, Procrustes superimposition dominates;
  PCA is negligible — optimizing the wrong one wastes effort.
- **Benchmark behind a marker** (pytest-benchmark) across small/medium/large
  inputs so a regression shows up as a number, not a user complaint.
- Watch **UI responsiveness** specifically: long operations on the main thread
  freeze the window — show a wait cursor / progress and consider a worker thread.

## 12. Security (for a file-ingesting desktop app)

**Goal:** a malicious or corrupt input file can't read/write outside bounds or run
code.

- **Never `eval`/`exec`/`pickle`/unsafe-`yaml`** on data from a file.
- **Contain path joins.** When a filename comes from inside an imported archive or
  metadata, resolve it and verify it stays within the intended directory
  (reject `../../..`). Use component-based containment, not string-prefix checks.
  (Real past defects: a zip-import media path and a zip-slip prefix check.)
- **Bound resource use** driven by file-supplied counts/sizes (decompression
  bombs, huge allocations).
- Run **`bandit`** (or Ruff's `S` rules) and keep dependency CVE scanning on
  (§6).

## 13. Dead code & complexity

**Goal:** less surface area for latent bugs.

- A recurring lesson here: **latent bugs hide on parallel / dead / backward-compat
  paths** (duplicate "twin" readers, triple analysis implementations, unreachable
  post-`return` code) that don't affect the live UI but bite when paths get
  rewired. Delete dead code deliberately, verified against the suite.
- **Automate detection** (`vulture` for unused code, Ruff `F401/F841` for
  unused imports/vars, `C901`/`radon` for complexity) so the manual sweeps become
  continuous.

## 14. Developer workflow & gating

Tie it together so quality is enforced, not hoped for:

- **pre-commit hooks:** format, lint, file hygiene (large-file guard, EOF,
  trailing whitespace, merge-conflict, YAML/JSON validity). Fast; runs locally.
- **PR-gating CI:** the OS×version matrix, smoke test, lint, type check (scoped),
  tests + coverage gate, `pip-audit`. Make them **required checks**.
- **Branch protection** on the default branch: required checks + review.
- **Every bug fix → a regression test + a devlog entry.** The written record
  (this project's `devlog/` + R-series reviews) is how recurring audits build on
  each other.

---

## Appendix A — Prioritized adoption checklist

For a mature codebase that already has linting + a test suite (like this one),
adopt in this order — cheapest and highest-leverage first:

1. [ ] **Cross-platform CI matrix** (OS × min/max runtime) + a headless **import/smoke test**. *Catches the biggest class of user-only crashes.*
2. [ ] **Make lint + tests gating** (remove `|| true`; branch protection).
3. [ ] **Expand the lint ruleset** incrementally — start with `DTZ`, `RUF012`, `S`, zero-violation groups; auto-fix the safe ones.
4. [ ] **`filterwarnings = error`** in tests (missing-glyph, Deprecation, numpy).
5. [ ] **Dependency hygiene:** lockfile + `pip-audit` + Dependabot; documented clean rebuild.
6. [ ] **Coverage gate** (floor + no-regression on PRs).
7. [ ] **Static type checking** (mypy/pyright), scoped to core modules, expanding.
8. [ ] **Dead-code / complexity automation** (`vulture`, `C901`/`radon`).
9. [ ] **Packaged-artifact smoke test** in a clean runner; sign installers.
10. [ ] **Property-based/fuzz tests** for parsers and numeric code.

## Appendix B — Tooling quick reference

| Concern | Tool(s) |
|---|---|
| Lint + format | Ruff |
| Type check | mypy, pyright |
| Test | pytest, pytest-qt, pytest-xvfb, pytest-cov, pytest-benchmark |
| Property/fuzz | hypothesis |
| Coverage gate | coverage.py `--fail-under`, diff-cover |
| Security (code) | bandit / Ruff `S` |
| Security (deps) | pip-audit, Dependabot / Renovate |
| Env / lock | pip-tools, uv, Poetry |
| Dead code / complexity | vulture, radon, Ruff `F401/F841/C901` |
| Profiling | line_profiler, memory_profiler, snakeviz |
| CI | GitHub Actions matrix; pre-commit; branch protection |
| Packaging | PyInstaller / py2app / briefcase; code signing + notarization |

---

*This guide is a living document. It was distilled from the Modan2 project's
review history (see `devlog/` R-series R01–R05) and generalized for any
multi-platform desktop application.*
