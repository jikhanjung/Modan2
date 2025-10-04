# Modan2 Documentation

This directory contains the Sphinx documentation for Modan2.

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
docs/
├── conf.py                 # Sphinx configuration
├── index.rst               # Main page
├── installation.rst        # Installation guide
├── user_guide.rst          # User manual
├── developer_guide.rst     # Developer documentation
├── changelog.rst           # Version history
├── _templates/
│   └── layout.html        # Language switcher
├── _static/
│   ├── screenshots/       # UI screenshots (to be added)
│   └── diagrams/          # Architecture diagrams (to be added)
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
5. Translate `.po` files
6. Build Korean version: `make html SPHINXOPTS="-D language=ko"`

## Deployment

Documentation will be automatically deployed to GitHub Pages via GitHub Actions (to be set up).

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
