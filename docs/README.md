# Modan2 Documentation

Documentation here is split by extension, and the split is deliberate:

| | Format | Where it is read |
|---|---|---|
| **`docs/manual/`** | `.rst` only | Published to <https://jikhanjung.github.io/Modan2/> (English + Korean) |
| **`docs/*.md`** | Markdown | Repository only — read on GitHub, never published |

Sphinx is not configured with `myst_parser`, so it reads `.rst` and nothing else.
A Markdown file added to `docs/manual/` would build into nothing; a `.rst` file
added to `docs/` would never be picked up. Put user-facing documentation in
`docs/manual/` and developer or release notes here.

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
| `USER_GUIDE.md` | Older monolithic user manual (see caveat below) |
| `QUICK_START.md` | Short getting-started walkthrough (see caveat below) |

### Caveat: three files predate this split

`USER_GUIDE.md`, `QUICK_START.md`, and `developer_guide.md` are user-facing in
content but sit on the unpublished side, and they overlap with
`manual/user_guide.rst` and `manual/developer_guide.rst` without being identical
— the Markdown versions carry sections the published manual does not, and they
have drifted where the `.rst` files were corrected.

Treat the `.rst` files as authoritative. Folding the remaining unique content
into them, and then removing these three, is tracked in `TODOs.md`.
