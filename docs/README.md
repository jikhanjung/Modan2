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
| `TEST_RELEASE_PLAN.md` | Pre-release testing plan |
| `CODE_QUALITY_GUIDE.md` | **Superseded, frozen at v1.0** — see `.guides/desktop/` |
| `GITHUB_PAGES_SETUP.md` | How the documentation site is configured |
| `SCREENSHOT_GUIDE.md` | Conventions for documentation screenshots |
| `architecture.md` | Internal architecture notes |
| `performance.md` | Performance measurements and analysis |

**What belongs here, and what does not.** These are *this project's* operational
documents — how to build Modan2, how its site is configured, what its numbers
are. Guidance meant to transfer to other projects lives in the shared PaleoBytes
guide set at `.guides/desktop/` (a symlink; see the repository `CLAUDE.md`), not
in a copy here. `CODE_QUALITY_GUIDE.md` is the one file that crossed that line —
it was written as a reusable guide, the shared set has since taken that role, and
it is kept only as the dated baseline other records cite. Devlog 280.

### User-facing guides live in `manual/`, not here

Several Markdown guides used to duplicate the published manual and drifted from
it. Each has been reconciled against the code and merged into the `.rst`:
`USER_GUIDE.md` and `QUICK_START.md` (devlog 264), `developer_guide.md`
(devlog 265), and the repository-root `INSTALL.md` (devlog 274). Release
mechanics moved into `manual/developer_guide.rst` as well, replacing
`RELEASE_PROCESS.md`, `RELEASE_GUIDE.md` and `VERSION_MANAGEMENT.md`.

If you are about to write a user-facing or contributor-facing guide as `.md`
here, put it in `manual/` as `.rst` instead — otherwise it is invisible to
readers and starts drifting the day it is written.
