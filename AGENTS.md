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
