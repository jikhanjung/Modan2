# Repository Guidelines

## Project Structure & Modules
- Root Python app: `Modan2.py` (GUI entry) and `main.py` (build entry).
- Core modules: `MdModel.py` (Peewee ORM), `MdStatistics.py` (PCA/CVA/MANOVA), `MdUtils.py`/`MdHelpers.py` (utilities), `ModanDialogs.py` and `ModanComponents.py` (PyQt5 UI), `OBJFileLoader/` and `objloader.py` (3D I/O).
- Assets: `icons/`, `translations/`, `migrations/`, `ExampleDataset/`, `Morphometrics dataset/`.
- Tooling: `build.py` (PyInstaller), `setup.py` (cx_Freeze), `migrate.py`, `version.py`, `bump_version.py`, GitHub config in `.github/`.
- Tests: `tests/` with `pytest.ini` configured.

## Build, Test, and Dev Commands
- Create/activate env, then install: `pip install -r requirements.txt`.
- Run app (standard): `python Modan2.py`.
- Run app (Linux/WSL Qt fix): `python fix_qt_import.py`.
- Build binaries: `python build.py` (produces `dist/` onefile + onedir).
- Migrations: `python migrate.py`.
- Tests (verbose): `pytest -v` • With coverage: `pytest --cov=. --cov-report=term`.

## Coding Style & Naming
- Python: PEP 8, 4-space indentation, UTF-8.
- Filenames follow existing CamelCase pattern for major modules (e.g., `MdUtils.py`), functions/methods use `snake_case`, classes `CamelCase`.
- Keep UI logic in `Modan*` files; isolate computation in `Md*` modules.
- No enforced linter; prefer clean diffs. Optional: run `black`/`ruff` locally if consistent with current style.

## Testing Guidelines
- Framework: `pytest`. Discovery: files `tests/test_*.py`, classes `Test*`, functions `test_*`.
- Use markers from `pytest.ini` (`unit`, `integration`, `slow`, `performance`, `gui`).
- Add unit tests for pure logic (`MdUtils.py`, `MdStatistics.py`) and mock GUI/DB where possible.
- Aim for meaningful coverage of core logic; include repro tests for bug fixes.

## Commit & Pull Request Guidelines
- Conventional commits preferred: `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:` (matches current history).
- Commits: imperative mood, concise scope, reference module when helpful.
- PRs: clear description, linked issues, reproduction steps; include screenshots/GIFs for UI changes; note platform specifics (Windows/macOS/Linux).
- Checklist: passes `pytest`, app launches (`python Modan2.py`), migrations updated if schema changes, docs/README touched when behavior changes.

## Security & Config Tips
- Linux/WSL: install Qt/OpenGL system libs per `requirements.txt` comments; use `fix_qt_import.py` if the Qt platform plugin fails.
- Keep large assets and sample data out of commits; prefer links or small subsets in `ExampleDataset/`.

## Code Index & Search Tools
- Build index: `python tools/build_index.py` (recursive scan; excludes `.index/`, `dist/`, `build/`, `__pycache__/`).
- Search index: `python tools/search_index.py --help`.
- Generate symbol cards: `python tools/generate_cards.py`.

Notes and conventions
- Scope: Tests (`tests/`) and tooling (`tools/`) are included in the index to improve coverage. Generated and build output folders are excluded.
- Dialog parsing: Widget/layout discovery is now limited to each dialog class block for higher precision (no file-wide mixing).
- Wait cursor scan: `--wait-cursor` inspects sources to report exact file, enclosing method, and line of `QApplication.setOverrideCursor`/`restoreOverrideCursor` usage.
- Type filter: `--type` values map to internal categories (`class→classes`, `function→functions`, `dialog→dialogs`). Use with `--symbol`.

Typical checks
- Project stats: `python tools/search_index.py --stats`.
- File info: `python tools/search_index.py --file ModanDialogs.py`.
- Qt connections: `python tools/search_index.py --qt clicked`.
- Dialog widgets: `python tools/search_index.py --dialog NewAnalysisDialog`.
