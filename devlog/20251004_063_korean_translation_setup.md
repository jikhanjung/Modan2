# Korean Translation Setup for Documentation

**Date**: 2025-10-04
**Status**: 🟡 Infrastructure Complete, Partial Translation
**Related**: devlog/20251004_062_sphinx_documentation_implementation.md

## Summary

Set up complete Korean translation infrastructure for Sphinx documentation using gettext/locale system. Completed full translation of index.po as demonstration.

## Translation Infrastructure

### Files Created

```
docs/locale/ko/LC_MESSAGES/
├── index.po                 # ✅ FULLY TRANSLATED (251 lines)
├── installation.po          # ⏳ READY FOR TRANSLATION (412 lines)
├── changelog.po             # ⏳ READY FOR TRANSLATION (641 lines)
├── developer_guide.po       # ⏳ READY FOR TRANSLATION (920 lines)
└── user_guide.po            # ⏳ READY FOR TRANSLATION (1,783 lines)
```

**Total Translation Volume**: 4,007 lines

### Translation Workflow Established

**1. Extract Translatable Strings**:
```bash
cd docs
make gettext
# Creates .pot files in _build/gettext/
```

**2. Create/Update .po Files**:
```bash
sphinx-intl update -p _build/gettext -l ko
# Creates/updates .po files in locale/ko/LC_MESSAGES/
```

**3. Translate .po Files**:
- Edit msgstr fields in .po files
- Use text editor, Poedit, or OmegaT
- Maintain formatting (``code``, **bold**, etc.)

**4. Build Korean Documentation**:
```bash
make html SPHINXOPTS="-D language=ko"
# Output: _build/html/ with Korean content
```

## Completed Translation: index.po

### Translation Statistics

| Metric | Value |
|--------|-------|
| Total strings | 73 |
| Translated | 73 (100%) |
| Untranslated | 0 |
| File size | 251 lines |

### Sample Translations

**Project Title**:
- EN: "Modan2 Documentation"
- KO: "Modan2 문서"

**Welcome Message**:
- EN: "Welcome to Modan2's documentation!"
- KO: "Modan2 문서에 오신 것을 환영합니다!"

**Features Section**:
- EN: "Hierarchical Data Management: Organize data into nested datasets"
- KO: "계층적 데이터 관리: 명확한 구조로 데이터를 중첩된 데이터셋으로 구성"

**Analysis Methods**:
- EN: "Principal Component Analysis (PCA)"
- KO: "주성분 분석 (PCA)"

- EN: "Canonical Variate Analysis (CVA)"
- KO: "정준 판별 분석 (CVA)"

- EN: "MANOVA (multivariate analysis of variance)"
- KO: "다변량 분산 분석 (MANOVA)"

### Build Verification

**Korean Build Test**:
```bash
make html SPHINXOPTS="-D language=ko"
# Build succeeded, 3 warnings
```

**Generated Files**:
- `_build/html/index.html` - Korean main page
- Language switcher functional
- Search configured for Korean

**Warnings** (non-critical):
- 2x inline literal warnings (cosmetic)
- 1x lexing warning for Unicode characters (cosmetic)

## Remaining Translation Work

### Translation Priority

**Priority 1: User-Facing Content** (Essential for users)
1. ✅ `index.po` (251 lines) - COMPLETED
2. ⏳ `installation.po` (412 lines) - Installation guide
3. ⏳ `user_guide.po` (1,783 lines) - User manual

**Priority 2: Reference Content** (For completeness)
4. ⏳ `changelog.po` (641 lines) - Version history
5. ⏳ `developer_guide.po` (920 lines) - Developer docs

### Estimated Translation Effort

**Completed**: 251 lines (6.3%)
**Remaining**: 3,756 lines (93.7%)

**Time Estimates** (professional translation):
- installation.po: ~2-3 hours
- changelog.po: ~3-4 hours
- developer_guide.po: ~5-6 hours
- user_guide.po: ~10-12 hours

**Total Remaining**: ~20-25 hours of translation work

### Translation Tools

**Recommended Tools**:

1. **Poedit** (https://poedit.net/)
   - GUI translation editor
   - Translation memory
   - Automatic formatting preservation
   - Free and cross-platform

2. **OmegaT** (https://omegat.org/)
   - CAT (Computer-Assisted Translation) tool
   - Translation memory and glossary
   - Free and open-source

3. **Text Editor** (VSCode, Sublime, etc.)
   - Direct .po file editing
   - Search and replace
   - Faster for technical translators

### Translation Guidelines

**General Principles**:
- Maintain technical term consistency (e.g., "landmark" → "랜드마크")
- Preserve code formatting: ``Ctrl+N`` stays as is
- Keep URLs unchanged
- Maintain paragraph structure
- Use formal/technical Korean style

**Key Term Translations**:
| English | Korean |
|---------|--------|
| Dataset | 데이터셋 |
| Object | 객체 |
| Landmark | 랜드마크 |
| Analysis | 분석 |
| Procrustes superimposition | Procrustes 중첩 |
| Principal Component Analysis (PCA) | 주성분 분석 (PCA) |
| Canonical Variate Analysis (CVA) | 정준 판별 분석 (CVA) |
| MANOVA | 다변량 분산 분석 (MANOVA) |
| Missing landmark | 결측 랜드마크 |
| Estimation | 추정 |
| Visualization | 시각화 |

**Formatting Preservation**:

```po
# Correct - preserves ``code``
msgid "Press ``Ctrl+N`` to create a dataset"
msgstr "``Ctrl+N``을 눌러 데이터셋을 만드세요"

# Incorrect - breaks formatting
msgid "Press ``Ctrl+N`` to create a dataset"
msgstr "Ctrl+N을 눌러 데이터셋을 만드세요"  # Missing backticks!
```

```po
# Correct - preserves **bold**
msgid "**Important**: Save your work"
msgstr "**중요**: 작업을 저장하세요"

# Incorrect
msgid "**Important**: Save your work"
msgstr "중요: 작업을 저장하세요"  # Missing **
```

## Current Build Status

### English Documentation
```bash
make html
# ✅ Build succeeded, 1 warning
# Output: _build/html/index.html (English)
```

### Korean Documentation (Partial)
```bash
make html SPHINXOPTS="-D language=ko"
# ✅ Build succeeded, 3 warnings
# Output: _build/html/index.html (Korean index, English others)
```

**What Works**:
- ✅ Main page (index.html) fully Korean
- ✅ Language switcher (en ↔ ko)
- ✅ Korean search configuration
- ✅ Navigation menu (partially Korean)
- ✅ Table of contents

**What's Untranslated** (still English):
- ⏳ Installation guide
- ⏳ User guide (majority of content)
- ⏳ Developer guide
- ⏳ Changelog

## Language Switcher Verification

The language switcher in `_templates/layout.html` is functional:

**On English Page**:
```
🌐 English | 한국어
```

**On Korean Page**:
```
🌐 English | 한국어
     ▲ (current, bold)
```

Clicking switches to `/ko/index.html` or `/en/index.html` while preserving page path.

## Next Steps

### Immediate (for MVP Korean docs):
1. ⏳ Translate `installation.po` (412 lines) - High priority for users
2. ⏳ Translate key sections of `user_guide.po`:
   - Getting Started
   - Working with Datasets
   - Statistical Analysis (PCA, CVA, MANOVA)
   - Keyboard Shortcuts

### Medium-Term:
3. ⏳ Complete `user_guide.po` translation (all sections)
4. ⏳ Translate `changelog.po` (version history)
5. ⏳ Translate `developer_guide.po` (for Korean contributors)

### Long-Term:
6. 📸 Add screenshots with Korean UI
7. 🎥 Create Korean tutorial videos
8. 📝 Add Korean-specific examples
9. 🌐 Deploy to GitHub Pages with language subdirectories

## How to Continue Translation

### For Contributors:

**1. Choose a file to translate**:
```bash
cd docs/locale/ko/LC_MESSAGES/
# Edit one of: installation.po, changelog.po, developer_guide.po, user_guide.po
```

**2. Translate msgstr fields**:
```po
#: ../../installation.rst:10
msgid "System Requirements"
msgstr "시스템 요구사항"  # Add Korean translation here

#: ../../installation.rst:12
msgid "**Minimum Requirements**:"
msgstr "**최소 요구사항**:"  # Preserve ** formatting
```

**3. Test the build**:
```bash
cd docs
make html SPHINXOPTS="-D language=ko"
# Check _build/html/ for Korean content
```

**4. Verify formatting**:
- Open `_build/html/installation.html` in browser
- Check that formatting (bold, code, lists) is preserved
- Verify no broken links or missing sections

### Using Poedit (Recommended for Non-Technical Translators):

1. Install Poedit: https://poedit.net/
2. Open `docs/locale/ko/LC_MESSAGES/installation.po`
3. Translate strings in the GUI
4. Save file (Poedit compiles .mo automatically)
5. Run `make html SPHINXOPTS="-D language=ko"` to build

### Using Text Editor (Faster for Technical Translators):

1. Open .po file in VSCode/Sublime/etc.
2. Search for `msgstr ""`  (empty translations)
3. Fill in Korean translations
4. Save file
5. Build and test

## Translation Quality Checklist

When translating, ensure:

- [ ] All msgstr fields filled (no empty "")
- [ ] Code formatting preserved (``code``, **bold**, *italic*)
- [ ] URLs unchanged
- [ ] Technical terms consistent (use glossary above)
- [ ] Korean grammar natural and clear
- [ ] No English mixed in (except code/URLs)
- [ ] Special characters escaped properly
- [ ] Build succeeds without errors
- [ ] Rendered HTML looks correct

## Benefits of Complete Translation

**For Korean Users**:
- Native language documentation (easier to learn)
- Reduced language barrier for adoption
- Better understanding of complex features
- Increased confidence in using the software

**For Project**:
- Wider user base in Korea and Korean diaspora
- Academic credibility in Korean institutions
- Potential for Korean research publications using Modan2
- Community contributions from Korean developers

**For Maintainers**:
- Reduced support burden (users can self-serve in Korean)
- Clear translation infrastructure for future updates
- Professional appearance matching international standards

## Related Files

- English docs: `docs/*.rst`
- Korean translations: `docs/locale/ko/LC_MESSAGES/*.po`
- Build config: `docs/conf.py`
- Language switcher: `docs/_templates/layout.html`

## Conclusion

✅ **Translation infrastructure complete and tested**
✅ **index.po fully translated as proof-of-concept**
⏳ **3,756 lines remaining (20-25 hours of work)**

The Korean documentation is ready for incremental translation. Each .po file can be translated independently, and partial translations will build successfully. The index page demonstrates that the translation system works correctly with proper formatting preservation and language switching.

**Recommendation**: Prioritize `installation.po` and key sections of `user_guide.po` for immediate Korean user support. Complete translation can be done incrementally as time permits.
