# Modan2 Documentation

Documentation here is split by extension, and the split is deliberate:

| | Format | Where it is read |
|---|---|---|
| **`docs/manual/`** | `.rst` only | Published to <https://jikhanjung.github.io/Modan2/> (English + Korean) |
| **`docs/*.md`** | Markdown | Repository only — read on GitHub, never published |

Put user-facing documentation in `docs/manual/`, as `.rst`, and developer or
release notes here. A `.rst` file added to `docs/` is never picked up.

`myst_parser` **is** enabled, but for exactly one purpose: `manual/changelog.rst`
pulls in the repository-root `CHANGELOG.md` so the release notes exist in one
place only. That file has to live at the repository root — contributors edit it
there and `release.yml` extracts the GitHub release body from it — so the manual
includes it rather than keeping a second copy. Keeping a copy is what let the two
drift apart before: each ended up with versions the other did not have.

Markdown is otherwise still not published. `manual/README.md` is excluded in
`conf.py` precisely because enabling myst would otherwise turn it into a page.

## The published manual

See `manual/README.md` for how to build it and how the Korean translation
workflow works. In short:

```bash
pip install -r manual/requirements.txt
cd manual && make html
```

## Repository-only notes

Written for contributors and maintainers, not for users of the application:

| File | What it covers |
|---|---|
| `BUILD_GUIDE.md` | Building the frozen executables and installers |
| `RELEASE_PROCESS.md` | Cutting and publishing a release |
| `TEST_RELEASE_PLAN.md` | Pre-release testing plan |
| `CODE_QUALITY_GUIDE.md` | Linting, formatting, typing, complexity |
| `GITHUB_PAGES_SETUP.md` | How the documentation site is configured |
| `SCREENSHOT_GUIDE.md` | Conventions for documentation screenshots |
| `architecture.md` | Internal architecture notes |
| `performance.md` | Performance measurements and analysis |
| `developer_guide.md` | Long-form developer notes (see caveat below) |

### Caveat: `developer_guide.md`

`developer_guide.md` overlaps `manual/developer_guide.rst` without being
identical — the Markdown version is the longer of the two and carries setup and
workflow sections the published one does not.

Treat the `.rst` as authoritative for anything that appears in both. Folding the
remaining unique content across and then removing this file is tracked in
`TODOs.md`.

`USER_GUIDE.md` and `QUICK_START.md` used to sit here with the same problem; they
were merged into `manual/user_guide.rst` and `manual/quick_start.rst` and removed.
