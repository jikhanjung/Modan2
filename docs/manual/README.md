# Modan2 Manual (published)

This directory is the Sphinx project behind
<https://jikhanjung.github.io/Modan2/> — the user-facing manual, in English and
Korean.

**Everything here is `.rst`.** The one exception is `changelog.rst`, which is a
two-line include of the repository-root `CHANGELOG.md` — release notes are
written there and nowhere else. `myst_parser` is enabled for that include alone;
because it makes Sphinx treat `.md` in this directory as pages, this README is
listed in `conf.py`'s `exclude_patterns`.

Repository-only notes (build guides, release process, architecture notes) live
one level up in `docs/` as Markdown and are read on GitHub; see `docs/README.md`.

## Building Documentation

### Prerequisites

```bash
pip install -r requirements.txt
```

### Build HTML Documentation

```bash
# Build both English and Korean
make html

# Or use the Python script directly
python build_all.py
```

Output:
- English: `_build/html/en/index.html`
- Korean: `_build/html/ko/index.html`
- Root redirect: `_build/html/index.html`

### View Documentation

Open in your browser:
- English: `_build/html/en/index.html`
- Korean: `_build/html/ko/index.html`

The language switcher (🌐) at the top-right allows switching between languages while preserving the current page.

### Development Server

For live reloading during documentation writing:

```bash
sphinx-autobuild . _build/html
```

Open http://127.0.0.1:8000

## Translation Workflow

### Extract Translatable Strings

```bash
make gettext
```

### Update Korean Translation Files

```bash
sphinx-intl update -p _build/gettext -l ko
```

**`changelog` is deliberately untranslated.** `changelog.rst` includes the whole
of `CHANGELOG.md`, so translating it would mean maintaining a Korean copy of
every past release note. `sphinx-intl update` recreates
`locale/ko/LC_MESSAGES/changelog.po` regardless, so that one file is
git-ignored — delete it or leave it, but do not commit it. The Korean changelog
page renders the English source, which is the intended result.

Every other catalog is kept at **zero untranslated and zero fuzzy entries**;
check with:

```bash
python -c "import polib,glob; [print(f, len(polib.pofile(f).untranslated_entries()), len(polib.pofile(f).fuzzy_entries())) for f in sorted(glob.glob('locale/ko/LC_MESSAGES/*.po'))]"
```

### Edit Translation Files

Edit `locale/ko/LC_MESSAGES/*.po` files using:
- Text editor
- [Poedit](https://poedit.net/)
- [OmegaT](https://omegat.org/)

### Build Korean Documentation

```bash
make html SPHINXOPTS="-D language=ko"
```

## Structure

```
docs/manual/
├── conf.py                 # Sphinx configuration
├── index.rst               # Main page
├── installation.rst        # Installation guide
├── user_guide.rst          # User manual
├── faq.rst                 # Frequently asked questions
├── troubleshooting.rst     # Troubleshooting guide
├── advanced_features.rst   # Advanced features
├── developer_guide.rst     # Developer documentation
├── changelog.rst           # Version history
├── _templates/
│   └── layout.html        # Language switcher
└── locale/
    └── ko/
        └── LC_MESSAGES/   # Korean translations
```

## Contributing

When adding new content:

1. Write in English first (`.rst` files)
2. Build to test: `make html`
3. Extract strings: `make gettext`
4. Update translations: `sphinx-intl update -p _build/gettext -l ko`
5. Translate `.po` files (all except `changelog.po` — see above)
6. Build Korean version: `make html SPHINXOPTS="-D language=ko"`

## Deployment

`.github/workflows/docs.yml` builds both languages and deploys to GitHub Pages on
every push to `main` that touches `docs/manual/**`. Because the trigger is scoped
to this directory, editing the Markdown notes in `docs/` does not redeploy the
site — which is correct, since they are not part of it.

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
