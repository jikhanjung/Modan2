# Multilingual Documentation Build System

**Date**: 2025-10-04
**Status**: ✅ Completed
**Related**: devlog/20251004_062_sphinx_documentation_implementation.md, devlog/20251004_063_korean_translation_setup.md

## Summary

Implemented a multilingual documentation build system that generates separate English and Korean documentation in `/en/` and `/ko/` subdirectories with functional language switching.

## Problem

Initial implementation built English and Korean in the same directory, making it impossible to deploy both languages simultaneously on GitHub Pages. Need separate `/en/` and `/ko/` directories for proper multilingual hosting.

## Solution

Created a Python build script (`build_all.py`) that builds both languages into separate subdirectories with proper language switching.

## Implementation

### Files Created/Modified

**1. Created: `docs/build_all.py`** (Python build script)
```python
#!/usr/bin/env python3
"""
Build both English and Korean documentation with separate output directories.
"""

def main():
    # Build English documentation
    sphinx-build -b html -D language=en . _build/html/en

    # Build Korean documentation
    sphinx-build -b html -D language=ko . _build/html/ko

    # Create root index.html that redirects to English
    # (with link to Korean)
```

**2. Modified: `docs/Makefile`**
```makefile
# Build both English and Korean documentation
html:
	@echo "Building both English and Korean documentation..."
	@python3 build_all.py
```

**3. Modified: `docs/_templates/layout.html`**
- Updated language switcher JavaScript to handle `/en/` and `/ko/` paths
- Preserves current page when switching languages
- Example: `/en/user_guide.html` → `/ko/user_guide.html`

**4. Modified: `docs/README.md`**
- Updated build instructions
- Documented new directory structure
- Added language switcher explanation

**5. Modified: `docs/.gitignore`**
- Fixed to not ignore `_templates/` and `_static/` directories
- Only ignores `_build/` output

## Directory Structure

### Before (Single Directory):
```
_build/html/
├── index.html              # Either English or Korean
├── user_guide.html
├── installation.html
└── ...
```

**Problem**: Can't have both languages at once!

### After (Separate Directories):
```
_build/html/
├── index.html              # Root redirect page
├── en/                     # English documentation
│   ├── index.html
│   ├── user_guide.html
│   ├── installation.html
│   ├── developer_guide.html
│   ├── changelog.html
│   ├── search.html
│   └── _static/
└── ko/                     # Korean documentation
    ├── index.html
    ├── user_guide.html
    ├── installation.html
    ├── developer_guide.html
    ├── changelog.html
    ├── search.html
    └── _static/
```

## Build Process

### Simple Build:
```bash
cd docs
make html
```

**Output**:
```
Building both English and Korean documentation...
✅ Success: Building English documentation completed
✅ Success: Building Korean documentation completed
✅ Build Complete!

English: _build/html/en/index.html
Korean:  _build/html/ko/index.html
```

### Manual Build (alternative):
```bash
cd docs
python build_all.py
```

### Clean Build:
```bash
make clean    # Removes _build/html/
make html     # Rebuilds everything
```

## Language Switching

### How It Works

**Language Switcher UI** (top-right corner):
```
🌐 English | 한국어
```

**On English Page** (`/en/user_guide.html`):
- Shows: English (current) | 한국어 (link)
- Click 한국어 → navigates to `/ko/user_guide.html`

**On Korean Page** (`/ko/user_guide.html`):
- Shows: English (link) | 한국어 (current)
- Click English → navigates to `/en/user_guide.html`

**JavaScript Logic**:
```javascript
function switchLanguage(targetLang) {
    var currentPath = window.location.pathname;

    // Replace language code in path (en <-> ko)
    if (currentPath.includes('/en/')) {
        newPath = currentPath.replace('/en/', '/' + targetLang + '/');
    } else if (currentPath.includes('/ko/')) {
        newPath = currentPath.replace('/ko/', '/' + targetLang + '/');
    }

    window.location.href = newPath;
}
```

**Preserves Page Context**:
- `/en/installation.html` → `/ko/installation.html`
- `/en/user_guide.html` → `/ko/user_guide.html`
- `/en/developer_guide.html` → `/ko/developer_guide.html`

### Root Index Page

The root `index.html` automatically redirects to English:

```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=en/index.html">
    <title>Redirecting to Modan2 Documentation</title>
</head>
<body>
    <p>Redirecting to <a href="en/index.html">English documentation</a>...</p>
    <p>또는 <a href="ko/index.html">한국어 문서</a>로 이동</p>
</body>
</html>
```

**Behavior**:
- Visiting `/` or `/index.html` → auto-redirects to `/en/index.html`
- Manual links provided for both languages

## Build Verification

### Test Results

**Command**:
```bash
make clean && make html
```

**Output**:
```
Removing build directory...
Building both English and Korean documentation...

============================================================
  Building Modan2 Documentation (English + Korean)
============================================================

============================================================
  Building English documentation
============================================================
Running: sphinx-build -b html -D language=en . _build/html/en

✅ Success: Building English documentation completed

============================================================
  Building Korean documentation
============================================================
Running: sphinx-build -b html -D language=ko . _build/html/ko

✅ Success: Building Korean documentation completed

============================================================
  ✅ Build Complete!
============================================================

English: _build/html/en/index.html
Korean:  _build/html/ko/index.html
Root:    _build/html/index.html
```

### File Counts

**English** (`_build/html/en/`):
- 10 HTML files (index, installation, user_guide, developer_guide, changelog, search, etc.)
- Complete English content

**Korean** (`_build/html/ko/`):
- 10 HTML files (same structure)
- index.html: Fully Korean (index.po 100% translated)
- Other files: English content (awaiting translation of .po files)

### Verification Tests

✅ **English build**: All pages in English
✅ **Korean index**: "Modan2 문서" title, fully Korean
✅ **Language switcher**: Present on all pages
✅ **Navigation**: Preserves page when switching languages
✅ **Root redirect**: Works correctly
✅ **Search**: Configured per language (en/ko)
✅ **Separate _static/**: Each language has own assets

## GitHub Pages Deployment

### Deployment Structure

When deployed to GitHub Pages (`https://jikhanjung.github.io/Modan2/`):

```
https://jikhanjung.github.io/Modan2/
├── index.html                          # Redirects to /en/
├── en/
│   ├── index.html                      # English main page
│   ├── installation.html
│   ├── user_guide.html
│   └── ...
└── ko/
    ├── index.html                      # Korean main page (partial)
    ├── installation.html
    ├── user_guide.html
    └── ...
```

### URLs

- **Root**: https://jikhanjung.github.io/Modan2/
  - Auto-redirects to English
- **English**: https://jikhanjung.github.io/Modan2/en/
- **Korean**: https://jikhanjung.github.io/Modan2/ko/
- **Direct pages**:
  - https://jikhanjung.github.io/Modan2/en/user_guide.html
  - https://jikhanjung.github.io/Modan2/ko/user_guide.html

### GitHub Actions Workflow (Future)

Create `.github/workflows/docs.yml`:

```yaml
name: Build Documentation

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd docs
          pip install -r requirements.txt

      - name: Build documentation
        run: |
          cd docs
          python build_all.py

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/_build/html
```

## Translation Status

### Fully Translated
- ✅ `index.po` (251 lines) - Main page 100% Korean

### Ready for Translation
- ⏳ `installation.po` (412 lines)
- ⏳ `user_guide.po` (1,783 lines)
- ⏳ `developer_guide.po` (920 lines)
- ⏳ `changelog.po` (641 lines)

**Total remaining**: 3,756 lines (93.7% of total)

### Current Korean Experience

**What Korean users see**:
1. Visit https://jikhanjung.github.io/Modan2/ko/
2. Main page (index.html): Fully Korean ✅
3. Click "설치" (Installation): English content ⏳
4. Click "사용자 가이드" (User Guide): English content ⏳

**Language switcher works**:
- All pages have 🌐 switcher
- Can switch en ↔ ko on any page
- Page context preserved

## Benefits

### For Users
1. **Native language access**: Korean users can read docs in Korean
2. **Easy switching**: One click to switch languages
3. **Preserved context**: Stay on same page when switching
4. **Professional**: Industry-standard multilingual docs

### For Deployment
1. **GitHub Pages ready**: Works with standard GH Pages setup
2. **SEO friendly**: Separate URLs per language
3. **Crawlable**: Search engines can index both versions
4. **Shareable links**: Can link directly to Korean or English

### For Maintenance
1. **Independent updates**: Update English without affecting Korean
2. **Incremental translation**: Partial translations work fine
3. **Version control**: Clear diff for .po file changes
4. **Standard tooling**: Uses industry-standard gettext/Sphinx

## Usage Instructions

### For Documentation Writers

**Update English documentation**:
```bash
cd docs
# Edit .rst files (index.rst, user_guide.rst, etc.)
make html
# Check _build/html/en/
```

**Update Korean translation**:
```bash
cd docs
make gettext                              # Extract new strings
sphinx-intl update -p _build/gettext -l ko # Update .po files
# Edit locale/ko/LC_MESSAGES/*.po files
make html                                 # Build both languages
# Check _build/html/ko/
```

### For Translators

**Translate documentation**:
```bash
cd docs/locale/ko/LC_MESSAGES/
# Edit .po files with Poedit or text editor
# Fill in msgstr fields with Korean translations

cd ../../../
make html
# Verify _build/html/ko/
```

### For Deployers

**Deploy to GitHub Pages**:
```bash
cd docs
make html

# Copy _build/html/ to gh-pages branch
# or use GitHub Actions (see workflow above)
```

## Next Steps

### Priority 1: Complete Korean Translation
- [ ] Translate `installation.po` (412 lines)
- [ ] Translate `changelog.po` (641 lines)
- [ ] Translate `user_guide.po` (1,783 lines)
- [ ] Translate `developer_guide.po` (920 lines)

### Priority 2: GitHub Pages Deployment
- [ ] Create `.github/workflows/docs.yml`
- [ ] Configure GitHub Pages (Settings → Pages → Source: gh-pages branch)
- [ ] Test deployment
- [ ] Update README.md with documentation link

### Priority 3: Enhancements
- [ ] Add screenshots (Korean UI if available)
- [ ] Create tutorial videos (Korean subtitles)
- [ ] Add Korean-specific examples
- [ ] SEO optimization (meta tags, sitemap)

## Conclusion

✅ **Multilingual build system complete and tested**

- Both English and Korean build successfully
- Separate `/en/` and `/ko/` directories
- Functional language switcher
- GitHub Pages deployment ready
- index.po fully translated as demonstration
- Remaining translations can be added incrementally

The infrastructure is production-ready. Users can now access documentation in their preferred language with seamless switching between English and Korean!

## Related Files

- Build script: `docs/build_all.py`
- Makefile: `docs/Makefile`
- Language switcher: `docs/_templates/layout.html`
- English docs: `docs/*.rst`
- Korean translations: `docs/locale/ko/LC_MESSAGES/*.po`
- Build output: `docs/_build/html/{en,ko}/`
