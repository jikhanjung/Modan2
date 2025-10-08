# Release Process and Documentation Guide

**Purpose**: Guidelines for managing releases, changelogs, and release notes in Modan2
**Audience**: Developers and release managers
**Last Updated**: 2025-10-08

---

## Overview

This document describes the best practices for managing releases in Modan2, including:
- Version numbering strategy
- CHANGELOG.md maintenance
- RELEASE_NOTES.md creation
- GitHub Release automation

---

## Version Numbering Strategy

### Semantic Versioning

Modan2 follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH[-PRERELEASE.BUILD]

Examples:
- 0.1.4 (stable)
- 0.1.5-alpha.1 (pre-release)
- 0.1.5-beta.1 (pre-release)
- 0.1.5 (stable)
```

### Version Components

- **MAJOR**: Incompatible API changes (currently 0 - pre-1.0)
- **MINOR**: New functionality, backward compatible
- **PATCH**: Bug fixes, backward compatible
- **PRERELEASE**: alpha, beta, rc (release candidate)
- **BUILD**: Build number (optional)

### Pre-release Progression

**Typical flow for minor/major release**:

```
0.1.4 (stable)
  ↓
0.1.5-alpha.1 ← Initial development
  ↓
0.1.5-alpha.2 ← More features
  ↓
0.1.5-beta.1  ← Feature complete, testing
  ↓
0.1.5-beta.2  ← Bug fixes
  ↓
0.1.5-rc.1    ← Release candidate (optional)
  ↓
0.1.5 (stable) ← Production release
```

**For patch releases** (bug fixes only):
```
0.1.5 (stable)
  ↓
0.1.6-rc.1 (optional)
  ↓
0.1.6 (stable)
```

---

## Documentation Files

Modan2 maintains three types of release documentation:

### 1. CHANGELOG.md (Developer-Focused)

**Location**: `/CHANGELOG.md`

**Purpose**:
- Complete technical history
- All changes, including pre-releases
- Developer reference

**Format**: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

**Audience**: Developers, contributors, technical users

### 2. RELEASE_NOTES.md (User-Focused)

**Location**: `/RELEASE_NOTES.md`

**Purpose**:
- User-friendly release information
- Highlights and major features
- Installation and upgrade instructions

**Format**: Custom, marketing-friendly

**Audience**: End users, beta testers

### 3. GitHub Releases

**Location**: Automated via GitHub Actions

**Purpose**:
- Distribution of binaries
- Automated release announcements
- Download links and checksums

**Format**: Auto-generated from RELEASE_NOTES.md

**Audience**: All users

---

## CHANGELOG.md Management

### Structure

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### Added
- Features currently in development

### Changed
- Changes in progress

### Fixed
- Bug fixes being worked on

## [0.1.5] - 2025-10-15

### Summary
Major release with exceptional performance improvements and production-ready CI/CD.

This release consolidates all changes from 0.1.5-alpha.1 through 0.1.5-beta.1.
For detailed development history, see pre-release sections below.

### Added
- Performance testing infrastructure (alpha.1)
- CI/CD pipeline improvements (beta.1)
- JSON+ZIP dataset packaging (alpha.1)
- Comprehensive user documentation (beta.1)

### Changed
- Build system: Multi-platform support enhanced
- Test workflow: Now runs before releases

### Fixed
- macOS app bundle creation (beta.1)
- Artifact collection patterns (beta.1)

### Performance
- Load speed: 18-200× faster than targets
- Memory efficiency: 125× better than target
- UI responsiveness: 9-5091× better than targets

## [0.1.5-beta.1] - 2025-10-08

### Added (Phase 8 - Release Preparation)
- CI/CD pipeline improvements
- Build Guide (700+ lines)
- Installation Guide (600+ lines)
- Test release validation

### Fixed
- Critical CI/CD issues (3 items)
- macOS .app bundle with Info.plist
- Artifact wildcard patterns

## [0.1.5-alpha.1] - 2025-09-11

### Added
- JSON+ZIP dataset packaging system
- Security features (Zip Slip defense)
- New API functions

### Changed
- File naming conventions
- Database handling improvements

## [0.1.4] - 2025-09-10

### Added
- CI/CD and build system
- Test infrastructure
- UI/UX features

(previous versions...)
```

### Key Principles

#### For Stable Releases

**✅ DO**:
- Create a summary section at the top
- Consolidate all pre-release changes
- Group by category (Added/Changed/Fixed/Performance)
- Reference pre-release sections for details
- Include version date

**❌ DON'T**:
- Duplicate all pre-release details
- Remove pre-release sections (keep for history)
- Mix stable and pre-release in same section

#### For Pre-releases

**✅ DO**:
- Document each alpha/beta separately
- Include only changes in that specific version
- Mark clearly as pre-release
- Use phase numbers if applicable (Phase 7, Phase 8)

**❌ DON'T**:
- Accumulate changes across pre-releases
- Skip documenting pre-releases
- Use vague descriptions

### Categories

Use these standard categories:

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes
- **Performance**: Performance improvements (Modan2 specific)

### Example Entry Format

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- **Feature Name**: Brief description
  - Sub-feature 1
  - Sub-feature 2
  - Impact: What this enables

### Changed
- **Component Name**: What changed
  - Before: Old behavior
  - After: New behavior

### Fixed
- **Issue #123**: Description of bug
  - Root cause: Brief explanation
  - Impact: Who was affected
```

---

## RELEASE_NOTES.md Management

### Structure

```markdown
# Modan2 Release Notes

**Version**: 0.1.5-beta.1
**Release Date**: 2025-10-08
**Status**: Pre-release / Beta

---

## 🎉 Highlights

Brief overview of the most important changes (3-5 bullet points)

### ⚡ Exceptional Performance (Phase 7 Validated)

**All performance targets exceeded by 8-5091×**:
- **Load Speed**: 18-200× faster than targets
- **Memory Efficiency**: 125× better than target
- **UI Responsiveness**: 9-5091× better than targets
- **Production-Ready**: Handles 100,000+ objects smoothly

### 🧪 Comprehensive Testing

- **1,240 total tests** (93.5% pass rate)
- Integration testing complete (Phase 6)
- Component testing complete (Phase 5)
- Performance profiling and validation (Phase 7)

(Continue with major sections...)

---

## ✨ New Features (This Release)

### Feature Category 1

**New Scripts**:
- `script1.py` - Description
- `script2.py` - Description

**Capabilities**:
- Capability 1
- Capability 2

(Continue...)

---

## 🔧 Improvements

### Performance

**Load Operations**:
- ✅ 18× faster loading (1000 objects: 277ms vs 5s target)
- ✅ 33× faster PCA (60ms vs 2s target)

(Continue...)

---

## 🐛 Bug Fixes

### Issue Title (Phase X Day Y)

**Issue**: Brief description

**Investigation Result**: NOT A BUG / FIXED

**Resolution**: What was done

(Continue...)

---

## 📋 Known Issues

### Platform-Specific

**Linux/WSL**:
- Issue description
- **Workaround**: Solution steps

(Continue...)

---

## 🚀 Installation

### Windows
(Instructions...)

### macOS
(Instructions...)

### Linux
(Instructions...)

---

## 📖 Documentation

### For Users
- Quick Start Guide
- User Guide
- Installation Guide

### For Developers
- Developer Guide
- Build Guide
- Performance Guide

---

## 🎯 System Requirements

### Minimum
- OS: Windows 10, macOS 10.14, Ubuntu 18.04
- RAM: 4GB
- Storage: 500MB

### Recommended
- OS: Windows 11, macOS 12+, Ubuntu 22.04+
- RAM: 8GB or more
- Storage: 2GB
- GPU: Dedicated GPU with OpenGL 3.3+

---

## 🙏 Credits

Development team, technologies used, special thanks

---

## 📝 License

MIT License

---

## 📞 Support & Feedback

GitHub Issues, email, community links

---

## 🔮 What's Next?

Short-term and long-term plans

---

**Release Version**: 0.1.5-beta.1
**Release Date**: 2025-10-08
**Build**: local
**Platform**: Multi-platform (Windows, macOS, Linux)
```

### Key Principles

#### For Stable Releases (e.g., 0.1.5)

**✅ DO**:
- Create comprehensive release notes
- Consolidate ALL changes since last stable (0.1.4)
- Include highlights from all pre-releases
- Focus on user impact, not technical details
- Include complete installation instructions
- List all known issues
- Provide upgrade path from previous stable

**Content Structure**:
```markdown
# Version 0.1.5 - YYYY-MM-DD

## Summary
One paragraph overview of the release.

## What's New Since 0.1.4
(Consolidate all alpha.1, beta.1, etc. changes)

## Major Highlights
- Performance improvements (from alpha/beta)
- New features (from alpha/beta)
- Bug fixes (from alpha/beta)

## Breaking Changes
(If any)

## Upgrade Guide
Steps to upgrade from 0.1.4

(Rest of standard sections...)
```

#### For Pre-releases (alpha, beta, rc)

**✅ DO**:
- Mark clearly as pre-release at the top
- Include warning about stability
- Document changes specific to this pre-release
- Reference what's new since previous pre-release
- Provide testing instructions
- Link to issue tracker

**Content Structure**:
```markdown
# Version 0.1.5-beta.1 (Pre-release) - YYYY-MM-DD

⚠️ **Beta Release** - For testing purposes only

## What's New in Beta 1

### Since Alpha 1
- Changes since the previous pre-release

### Testing This Release
- What to test
- How to report issues

(Abbreviated sections - less detail than stable)
```

### Sections to Include

**Essential** (all releases):
- 🎉 Highlights
- ✨ New Features
- 🔧 Improvements
- 🐛 Bug Fixes
- 📋 Known Issues
- 🚀 Installation
- 📖 Documentation

**Optional** (stable releases):
- 📊 Performance Summary (if relevant)
- 🔄 Migration Guide (if breaking changes)
- 🏗️ Development Timeline
- 🙏 Credits
- 🔮 What's Next
- 📞 Support

**Pre-release specific**:
- ⚠️ Pre-release Warning
- 🧪 Testing Instructions
- 📝 Known Limitations

---

## GitHub Release Automation

### Current Implementation

Modan2 uses GitHub Actions to automatically create releases.

**Workflow**: `.github/workflows/release.yml`

**Trigger**: Push tag matching `v*.*.*`

**Process**:
1. Run all tests (1,240 tests)
2. Build multi-platform artifacts
3. Generate SHA256 checksums
4. Create GitHub release
5. Upload artifacts
6. Include RELEASE_NOTES.md in release body

### Release Body Content

**Automated**:
```markdown
(Contents of RELEASE_NOTES.md)

---

## SHA256 Checksums

```
{hash}  Modan2-Windows-*.zip
{hash}  Modan2-macOS-*.dmg
{hash}  Modan2-Linux-*.AppImage
```

Built from commit: {sha}
```

### Release Types

**Stable Release** (e.g., v0.1.5):
- NOT marked as pre-release
- Full RELEASE_NOTES.md content
- All artifacts attached
- Checksums included

**Pre-release** (e.g., v0.1.5-beta.1):
- Marked as pre-release (⚠️ warning on GitHub)
- Abbreviated release notes or full (your choice)
- All artifacts attached
- Checksums included

### Creating a Release

#### Stable Release

```bash
# 1. Update version.py
echo '__version__ = "0.1.5"' > version.py

# 2. Update CHANGELOG.md
# Add [0.1.5] section with consolidated changes

# 3. Update RELEASE_NOTES.md
# Update version at top and add 0.1.5 section

# 4. Commit changes
git add version.py CHANGELOG.md RELEASE_NOTES.md
git commit -m "chore: Prepare release 0.1.5"

# 5. Create and push tag
git tag -a v0.1.5 -m "Modan2 v0.1.5 - Production Release

Major release with:
- Exceptional performance (8-5091× improvements)
- Production-ready CI/CD
- Comprehensive documentation

See RELEASE_NOTES.md for full details."

git push origin main
git push origin v0.1.5

# 6. GitHub Actions automatically:
# - Runs tests
# - Builds artifacts
# - Creates release
# - Uploads files
```

#### Pre-release

```bash
# 1. Update version.py
echo '__version__ = "0.1.5-beta.1"' > version.py

# 2. Update CHANGELOG.md
# Add [0.1.5-beta.1] section

# 3. Update RELEASE_NOTES.md
# Update version and status

# 4. Commit
git add version.py CHANGELOG.md RELEASE_NOTES.md
git commit -m "chore: Prepare beta.1 release"

# 5. Tag and push
git tag -a v0.1.5-beta.1 -m "Modan2 v0.1.5-beta.1 - Beta Release"
git push origin main
git push origin v0.1.5-beta.1

# GitHub Actions creates pre-release automatically
```

---

## Release Workflow

### Complete Release Cycle Example

#### Starting Development (0.1.5-alpha.1)

1. **Create branch** (optional):
   ```bash
   git checkout -b release/0.1.5
   ```

2. **Update version**:
   ```bash
   echo '__version__ = "0.1.5-alpha.1"' > version.py
   ```

3. **Update CHANGELOG.md**:
   ```markdown
   ## [Unreleased]
   (work in progress)

   ## [0.1.5-alpha.1] - 2025-09-11
   ### Added
   - New feature X
   ```

4. **Create/update RELEASE_NOTES.md**:
   ```markdown
   **Version**: 0.1.5-alpha.1
   **Status**: Pre-release / Alpha

   ⚠️ **Alpha Release**
   ```

5. **Commit and tag**:
   ```bash
   git commit -am "chore: Release 0.1.5-alpha.1"
   git tag v0.1.5-alpha.1
   git push origin release/0.1.5
   git push origin v0.1.5-alpha.1
   ```

#### Moving to Beta (0.1.5-beta.1)

1. **Update version**:
   ```bash
   echo '__version__ = "0.1.5-beta.1"' > version.py
   ```

2. **Update CHANGELOG.md**:
   ```markdown
   ## [0.1.5-beta.1] - 2025-10-08
   ### Added
   - Feature Y (new in beta)
   - Feature X (from alpha)
   ```

3. **Update RELEASE_NOTES.md**:
   ```markdown
   **Version**: 0.1.5-beta.1
   **Status**: Pre-release / Beta

   ## What's New Since Alpha 1
   - Feature Y
   ```

4. **Commit and tag**:
   ```bash
   git commit -am "chore: Release 0.1.5-beta.1"
   git tag v0.1.5-beta.1
   git push origin release/0.1.5
   git push origin v0.1.5-beta.1
   ```

#### Final Stable Release (0.1.5)

1. **Update version**:
   ```bash
   echo '__version__ = "0.1.5"' > version.py
   ```

2. **Update CHANGELOG.md** (consolidate):
   ```markdown
   ## [0.1.5] - 2025-10-15

   ### Summary
   Major release with exceptional performance improvements.

   This release consolidates all changes from:
   - [0.1.5-alpha.1] - Initial features
   - [0.1.5-beta.1] - CI/CD improvements

   ### Added
   - Feature X (alpha.1)
   - Feature Y (beta.1)
   - (All features consolidated)

   ### Changed
   - (All changes consolidated)

   ### Fixed
   - (All fixes consolidated)

   ### Performance
   - Load: 18-200× faster
   - Memory: 125× better
   - UI: 9-5091× better
   ```

3. **Update RELEASE_NOTES.md**:
   ```markdown
   **Version**: 0.1.5
   **Status**: Stable
   **Recommended for**: Production use

   ## What's New Since 0.1.4

   (Comprehensive summary of all changes)
   ```

4. **Merge to main and tag**:
   ```bash
   git checkout main
   git merge release/0.1.5
   git tag v0.1.5 -m "Modan2 v0.1.5 - Stable Release"
   git push origin main
   git push origin v0.1.5
   ```

5. **GitHub Actions creates final release automatically**

---

## Best Practices

### DO ✅

1. **Version Bumping**:
   - Always update `version.py` first
   - Keep version consistent across all files
   - Use semantic versioning strictly

2. **CHANGELOG.md**:
   - Update with every significant change
   - Use [Unreleased] section during development
   - Consolidate for stable releases
   - Keep all pre-release sections for history

3. **RELEASE_NOTES.md**:
   - Focus on user value, not technical details
   - Use emojis for visual organization (🎉 ✨ 🔧 🐛)
   - Include screenshots when helpful
   - Update version/date at the top

4. **Git Tags**:
   - Use annotated tags (`git tag -a`)
   - Include descriptive messages
   - Match version.py exactly (e.g., `v0.1.5`)

5. **Testing**:
   - Test release workflow with test tags first
   - Validate all artifacts before stable release
   - Check SHA256 checksums

### DON'T ❌

1. **Version Management**:
   - Don't skip pre-release stages for major changes
   - Don't reuse version numbers
   - Don't use different versions in different files

2. **CHANGELOG.md**:
   - Don't remove pre-release sections
   - Don't put everything in [Unreleased]
   - Don't use vague descriptions

3. **RELEASE_NOTES.md**:
   - Don't use technical jargon unnecessarily
   - Don't forget to mark pre-releases
   - Don't skip known issues section

4. **Git Tags**:
   - Don't use lightweight tags
   - Don't delete tags after pushing
   - Don't amend tagged commits

---

## Checklist Templates

### Pre-release Checklist

```markdown
## Pre-release Checklist (alpha/beta/rc)

### Code
- [ ] All planned features implemented
- [ ] All tests passing locally
- [ ] Ruff linting passes
- [ ] No critical TODOs remaining

### Documentation
- [ ] version.py updated
- [ ] CHANGELOG.md updated with new section
- [ ] RELEASE_NOTES.md updated
- [ ] Breaking changes documented (if any)

### Testing
- [ ] Manual testing completed
- [ ] CI/CD passing
- [ ] Platform testing (if available)

### Release
- [ ] Changes committed
- [ ] Tag created (v0.1.5-beta.1)
- [ ] Tag pushed to GitHub
- [ ] GitHub release created automatically
- [ ] Artifacts downloaded and verified
- [ ] Checksums verified

### Communication
- [ ] Team notified (if applicable)
- [ ] Testers invited (if applicable)
```

### Stable Release Checklist

```markdown
## Stable Release Checklist (production)

### Preparation
- [ ] All pre-release testing completed
- [ ] No critical bugs remaining
- [ ] All documentation reviewed
- [ ] CHANGELOG.md consolidated
- [ ] RELEASE_NOTES.md finalized

### Code
- [ ] version.py updated to stable (e.g., 0.1.5)
- [ ] All tests passing (1,240 tests)
- [ ] Ruff linting passes
- [ ] Performance validated

### Documentation
- [ ] CHANGELOG.md has [0.1.5] section
- [ ] RELEASE_NOTES.md comprehensive
- [ ] Known issues documented
- [ ] Upgrade guide included (if needed)
- [ ] Screenshots added (if applicable)

### Testing
- [ ] Test release validated (v0.1.5-test)
- [ ] All platforms tested
- [ ] Checksums verified
- [ ] Download links work

### Release
- [ ] Final commit to main
- [ ] Tag created (v0.1.5)
- [ ] Tag pushed
- [ ] GitHub release created
- [ ] Release NOT marked as pre-release
- [ ] All artifacts present

### Post-Release
- [ ] Announcement prepared
- [ ] Social media posts (if applicable)
- [ ] Documentation website updated
- [ ] Next version planning started
```

---

## Examples from Modan2

### Example: 0.1.5-beta.1 Release

**version.py**:
```python
__version__ = "0.1.5-beta.1"
```

**CHANGELOG.md**:
```markdown
## [0.1.5-beta.1] - 2025-10-08

### Added (Phase 8 - Release Preparation)
- CI/CD pipeline improvements
- Build Guide (docs/BUILD_GUIDE.md, 700+ lines)
- Installation Guide (INSTALL.md, 600+ lines)
- Enhanced documentation structure

### Fixed
- Critical CI/CD issues (3 items):
  - Tests now run before release
  - macOS .app bundle with Info.plist
  - Artifact wildcard patterns
```

**RELEASE_NOTES.md** (excerpt):
```markdown
**Version**: 0.1.5-beta.1
**Release Date**: 2025-10-08
**Status**: Pre-release / Beta

## 🎉 Highlights

- ⚡ Exceptional Performance (8-5091× better)
- 🧪 Comprehensive Testing (1,240 tests)
- 📚 Complete Documentation
```

**Git Tag**:
```bash
git tag -a v0.1.5-beta.1 -m "Modan2 v0.1.5-beta.1 - Beta Release"
```

---

## Tools and Automation

### Version Bumping Script (Future)

```bash
#!/bin/bash
# scripts/bump_version.sh

VERSION=$1
TYPE=$2  # alpha, beta, rc, stable

if [ -z "$VERSION" ] || [ -z "$TYPE" ]; then
  echo "Usage: ./bump_version.sh 0.1.5 [alpha|beta|rc|stable]"
  exit 1
fi

# Update version.py
if [ "$TYPE" = "stable" ]; then
  echo "__version__ = \"$VERSION\"" > version.py
else
  echo "__version__ = \"$VERSION-$TYPE.1\"" > version.py
fi

echo "Version updated to $(cat version.py)"
```

### Release Notes Template Generator (Future)

```python
# scripts/generate_release_notes.py
# Auto-generate RELEASE_NOTES.md structure
```

---

## FAQ

### Q: Should I document every small bug fix in pre-releases?

**A**: Yes in CHANGELOG.md (for technical history), but group minor fixes in RELEASE_NOTES.md (for users).

### Q: Can I skip alpha/beta and go straight to stable?

**A**: Only for patch releases (0.1.5 → 0.1.6). For minor/major releases, use at least one pre-release stage.

### Q: What if I need to fix a critical bug in a stable release?

**A**:
1. Create patch version (e.g., 0.1.5 → 0.1.6)
2. Optionally use rc (0.1.6-rc.1)
3. Release stable quickly
4. Document in both CHANGELOG and RELEASE_NOTES

### Q: Should I delete pre-release sections from CHANGELOG after stable release?

**A**: No! Keep them for historical reference. Add a stable section that consolidates and references them.

### Q: How detailed should GitHub release notes be?

**A**: For stable releases, very detailed (full RELEASE_NOTES.md). For pre-releases, can be abbreviated with link to full notes.

---

## References

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Conventional Commits](https://www.conventionalcommits.org/) (optional)

---

## Revision History

- **2025-10-08**: Initial version based on Modan2 Phase 8 practices
- **TBD**: Updates based on team feedback

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**Maintainer**: Modan2 Development Team
