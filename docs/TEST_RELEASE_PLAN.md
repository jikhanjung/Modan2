# Test Release Workflow Validation Plan

**Purpose**: Validate GitHub Actions release workflow before production release
**Phase**: Phase 8 Day 2
**Status**: Ready to Execute

---

## Overview

This plan validates the complete CI/CD release workflow after the critical fixes implemented in Phase 8 Day 1.

**What We're Testing**:
- ✅ Tests run before release
- ✅ Multi-platform builds (Windows, macOS, Linux)
- ✅ macOS app bundle creation with Info.plist
- ✅ Artifact collection with wildcard patterns
- ✅ SHA256 checksum generation
- ✅ RELEASE_NOTES.md integration
- ✅ GitHub release creation

---

## Prerequisites

### 1. Clean Git State ✅
```bash
# Verify all changes committed
git status
# Should show: "nothing to commit, working tree clean"
```

### 2. CI/CD Fixes Applied ✅
- [x] `.github/workflows/release.yml` - Tests + checksums + RELEASE_NOTES
- [x] `.github/workflows/reusable_build.yml` - macOS bundle fix
- [x] `.github/workflows/test.yml` - workflow_call support

### 3. Documentation Ready ✅
- [x] `RELEASE_NOTES.md` exists and complete
- [x] `CHANGELOG.md` updated
- [x] `version.py` at current version (0.1.5-alpha.1)

---

## Test Release Strategy

### Option 1: Dry Run Test Tag (Recommended)

**Test Tag**: `v0.1.5-alpha.1-test`

**Purpose**: Test workflow without official release
**Advantage**: Can be deleted if issues found
**Disadvantage**: Creates temporary GitHub release

**Steps**:
```bash
# 1. Create and push test tag
git tag -a v0.1.5-alpha.1-test -m "Test release workflow validation (Phase 8 Day 2)"
git push origin v0.1.5-alpha.1-test

# 2. Monitor workflow
# Go to: https://github.com/yourusername/Modan2/actions

# 3. If successful, clean up
git tag -d v0.1.5-alpha.1-test
git push --delete origin v0.1.5-alpha.1-test
# Delete GitHub release manually
```

### Option 2: Pre-release Tag

**Test Tag**: `v0.1.5-alpha.2`

**Purpose**: Create actual pre-release for testing
**Advantage**: Real release workflow, can be used for beta testing
**Disadvantage**: Increments version

**Steps**:
```bash
# 1. Update version (if using this option)
# Edit version.py: __version__ = "0.1.5-alpha.2"

# 2. Create and push tag
git add version.py
git commit -m "chore: Bump version to 0.1.5-alpha.2 for test release"
git tag -a v0.1.5-alpha.2 -m "Pre-release test (Phase 8 Day 2)"
git push origin main
git push origin v0.1.5-alpha.2

# 3. Monitor workflow
# Go to: https://github.com/yourusername/Modan2/actions
```

### Option 3: Branch-based Test (Safe)

**Branch**: `test-release`

**Purpose**: Test on separate branch without affecting main
**Advantage**: No impact on main branch
**Disadvantage**: Requires workflow modification

**Steps**:
```bash
# 1. Create test branch
git checkout -b test-release

# 2. Modify release.yml to trigger on test-release branch (temporary)
# Add to .github/workflows/release.yml:
#   on:
#     push:
#       branches: [ test-release ]
#       tags: [ 'v*.*.*' ]

# 3. Commit and push
git add .github/workflows/release.yml
git commit -m "test: Trigger release on test-release branch"
git push origin test-release

# 4. Monitor workflow

# 5. Clean up
git checkout main
git branch -D test-release
git push --delete origin test-release
```

---

## Recommended Approach: Option 1 (Dry Run Test Tag)

**Why**: Safest, no version changes, easy cleanup

---

## Validation Checklist

### Phase 1: Workflow Trigger ✅

```bash
# Create test tag
git tag -a v0.1.5-alpha.1-test -m "Test release workflow validation"
git push origin v0.1.5-alpha.1-test
```

**Verify**:
- [ ] Workflow triggered automatically on tag push
- [ ] GitHub Actions shows "Release" workflow running
- [ ] Run number incrementing correctly

### Phase 2: Test Execution ✅

**Monitor**: https://github.com/yourusername/Modan2/actions

**Verify**:
- [ ] Test job starts first
- [ ] All tests run (1,240 tests)
- [ ] Tests complete successfully
- [ ] Build job waits for test completion
- [ ] Build job starts only after tests pass

**Expected Test Results**:
- ✅ Unit tests: ~500 passed
- ✅ Dialog tests: ~35 passed
- ✅ Integration tests: ~705 passed
- ✅ Total: 1,240 tests, 93.5% pass rate

**If Tests Fail**:
```bash
# Workflow should stop here (tests are dependency)
# Fix issues and retry
# No builds should be created
```

### Phase 3: Multi-Platform Builds ✅

**Monitor**: Build jobs running in parallel

#### Windows Build
- [ ] Windows job starts
- [ ] Python 3.12 setup
- [ ] Dependencies installed
- [ ] PyInstaller runs successfully
- [ ] One-file executable created: `dist/Modan2.exe`
- [ ] One-directory executable created: `dist/Modan2/`
- [ ] InnoSetup installer created (if available)
- [ ] ZIP package created: `Modan2-Windows-v0.1.5-alpha.1-test-build{N}.zip`
- [ ] Artifact uploaded: `modan2-windows`

**Expected Output**:
```
dist/
├── Modan2.exe (one-file)
└── Modan2/ (one-directory)

InnoSetup/Output/
└── Modan2-Windows-Installer-v0.1.5-alpha.1-test-build{N}.exe

Packaged:
└── Modan2-Windows-v0.1.5-alpha.1-test-build{N}.zip
```

#### macOS Build
- [ ] macOS job starts
- [ ] Homebrew installs qt5, create-dmg
- [ ] Python dependencies installed
- [ ] PyInstaller runs successfully
- [ ] Executable created: `dist/Modan2`
- [ ] **App bundle created**: `dist/Modan2.app/`
- [ ] **App bundle structure correct**:
  - [ ] `Contents/MacOS/Modan2` exists and executable
  - [ ] `Contents/Resources/Modan2.png` exists
  - [ ] `Contents/Info.plist` exists and valid
- [ ] Info.plist contains correct metadata:
  - [ ] CFBundleVersion = build number
  - [ ] CFBundleShortVersionString = 0.1.5-alpha.1-test
  - [ ] CFBundleIdentifier = com.paleobytes.modan2
- [ ] DMG created: `Modan2-macOS-Installer-v0.1.5-alpha.1-test-build{N}.dmg`
- [ ] Artifact uploaded: `modan2-macos`

**Critical Check** (macOS):
```bash
# Verify .app bundle structure in logs:
# Should show:
# dist/Modan2.app/
# ├── Contents/
#     ├── Info.plist
#     ├── MacOS/
#     │   └── Modan2
#     └── Resources/
#         └── Modan2.png
```

#### Linux Build
- [ ] Linux job starts
- [ ] System dependencies installed (Qt5, OpenGL, etc.)
- [ ] Python dependencies installed
- [ ] PyInstaller runs successfully
- [ ] Executable created: `dist/Modan2`
- [ ] AppRun script created
- [ ] Desktop file created
- [ ] Icon copied
- [ ] linuxdeploy runs successfully
- [ ] AppImage created: `Modan2-Linux-v0.1.5-alpha.1-test-build{N}.AppImage`
- [ ] Artifact uploaded: `modan2-linux`

### Phase 4: Artifact Collection ✅

**Monitor**: Create release job

- [ ] All three build jobs complete
- [ ] Download artifacts step runs
- [ ] Artifacts downloaded to `release-files/`
- [ ] Directory structure correct:
  ```
  release-files/
  ├── modan2-windows/
  │   ├── Modan2-Windows-*.zip
  │   └── Modan2-Windows-*.exe (if InnoSetup)
  ├── modan2-macos/
  │   └── Modan2-macOS-Installer-*.dmg
  └── modan2-linux/
      └── Modan2-Linux-*.AppImage
  ```

### Phase 5: Checksum Generation ✅

- [ ] Generate SHA256 checksums step runs
- [ ] Finds all artifacts (*.zip, *.dmg, *.AppImage)
- [ ] Creates `SHA256SUMS.txt`
- [ ] Checksums displayed in log
- [ ] File format correct:
  ```
  {hash}  ./modan2-windows/Modan2-Windows-v0.1.5-alpha.1-test-build{N}.zip
  {hash}  ./modan2-macos/Modan2-macOS-Installer-v0.1.5-alpha.1-test-build{N}.dmg
  {hash}  ./modan2-linux/Modan2-Linux-v0.1.5-alpha.1-test-build{N}.AppImage
  ```

### Phase 6: Release Creation ✅

- [ ] Prepare release body step runs
- [ ] Finds `RELEASE_NOTES.md`
- [ ] Release body contains:
  - [ ] Complete RELEASE_NOTES.md content
  - [ ] "---" separator
  - [ ] "## SHA256 Checksums" heading
  - [ ] Checksums in code block
  - [ ] Commit SHA
- [ ] Create Release step runs
- [ ] GitHub release created at: https://github.com/yourusername/Modan2/releases/tag/v0.1.5-alpha.1-test
- [ ] Release marked as pre-release (contains "-alpha")
- [ ] All artifacts uploaded:
  - [ ] Windows ZIP
  - [ ] Windows EXE (if InnoSetup)
  - [ ] macOS DMG
  - [ ] Linux AppImage
  - [ ] SHA256SUMS.txt

### Phase 7: Release Validation ✅

**Visit**: https://github.com/yourusername/Modan2/releases/tag/v0.1.5-alpha.1-test

**Verify**:
- [ ] Release title: "Modan2 v0.1.5-alpha.1-test"
- [ ] Marked as "Pre-release"
- [ ] Release body displays correctly:
  - [ ] RELEASE_NOTES.md content formatted
  - [ ] SHA256 checksums visible in code block
  - [ ] Commit SHA shown
- [ ] Assets section contains all files:
  - [ ] Modan2-Windows-*.zip
  - [ ] Modan2-Windows-*.exe (if available)
  - [ ] Modan2-macOS-Installer-*.dmg
  - [ ] Modan2-Linux-*.AppImage
  - [ ] SHA256SUMS.txt
  - [ ] Source code (zip)
  - [ ] Source code (tar.gz)

---

## Download & Verification Tests

### 1. Download Artifacts

```bash
# Download from GitHub release
cd ~/Downloads

# Download each artifact
wget https://github.com/yourusername/Modan2/releases/download/v0.1.5-alpha.1-test/Modan2-Windows-*.zip
wget https://github.com/yourusername/Modan2/releases/download/v0.1.5-alpha.1-test/Modan2-macOS-*.dmg
wget https://github.com/yourusername/Modan2/releases/download/v0.1.5-alpha.1-test/Modan2-Linux-*.AppImage
wget https://github.com/yourusername/Modan2/releases/download/v0.1.5-alpha.1-test/SHA256SUMS.txt
```

### 2. Verify Checksums

```bash
# Verify all downloads
sha256sum -c SHA256SUMS.txt

# Expected output:
# Modan2-Windows-*.zip: OK
# Modan2-macOS-*.dmg: OK
# Modan2-Linux-*.AppImage: OK
```

### 3. Platform-Specific Tests

#### Windows (if available)
```powershell
# Extract ZIP
Expand-Archive Modan2-Windows-*.zip -DestinationPath Modan2-Test

# Run executable
cd Modan2-Test
.\Modan2.exe

# Verify:
# - Application launches
# - No missing DLL errors
# - Main window appears
# - About dialog shows correct version
```

#### macOS (if available)
```bash
# Mount DMG
hdiutil attach Modan2-macOS-*.dmg

# Copy to Applications (test location)
cp -r /Volumes/Modan2\ Installer/Modan2.app ~/Desktop/

# Verify bundle structure
ls -la ~/Desktop/Modan2.app/Contents/
ls -la ~/Desktop/Modan2.app/Contents/MacOS/
ls -la ~/Desktop/Modan2.app/Contents/Resources/
cat ~/Desktop/Modan2.app/Contents/Info.plist

# Run application
open ~/Desktop/Modan2.app

# Verify:
# - No Gatekeeper errors (or proper warning)
# - Application launches
# - Main window appears
# - About dialog shows correct version
```

#### Linux (if available)
```bash
# Make executable
chmod +x Modan2-Linux-*.AppImage

# Run AppImage
./Modan2-Linux-*.AppImage

# Verify:
# - No missing library errors
# - Application launches
# - Main window appears
# - About dialog shows correct version
```

---

## Success Criteria

### Must Pass (Critical)
- ✅ All 1,240 tests pass before build
- ✅ All three platform builds succeed
- ✅ macOS .app bundle created with Info.plist
- ✅ All artifacts collected with wildcard patterns
- ✅ SHA256 checksums generated correctly
- ✅ RELEASE_NOTES.md included in GitHub release
- ✅ All artifacts downloadable
- ✅ Checksums verify correctly

### Should Pass (Important)
- ✅ Windows installer created (if InnoSetup available)
- ✅ No workflow errors or warnings
- ✅ Artifact file sizes reasonable (< 150MB each)
- ✅ Release marked as pre-release correctly
- ✅ Release body formatted properly

### Nice to Have (Optional)
- ✅ Application launches on all platforms (requires hardware)
- ✅ Core functionality works (create dataset, import, analyze)
- ✅ No UI glitches or errors

---

## Troubleshooting

### Issue: Tests Fail
**Cause**: Code issues or test environment problems
**Solution**:
1. Check test logs for specific failures
2. Fix failing tests
3. Commit fixes
4. Delete test tag: `git tag -d v0.1.5-alpha.1-test`
5. Retry test release

### Issue: macOS Build Fails
**Cause**: App bundle creation issues
**Solution**:
1. Check if dist/Modan2 exists
2. Verify Info.plist creation in logs
3. Check create-dmg output
4. Review workflow changes in reusable_build.yml

### Issue: Artifact Not Found
**Cause**: Wildcard pattern mismatch
**Solution**:
1. Check artifact names in build logs
2. Verify wildcard patterns in release.yml
3. Ensure artifacts uploaded with correct names

### Issue: Checksums Don't Match
**Cause**: File corruption or generation error
**Solution**:
1. Re-download artifacts
2. Check SHA256SUMS.txt format
3. Verify file paths in checksums
4. Ensure no spaces in filenames

### Issue: RELEASE_NOTES.md Not in Release Body
**Cause**: File not found or parsing error
**Solution**:
1. Verify RELEASE_NOTES.md exists in repo
2. Check "Prepare release body" step logs
3. Ensure file is in root directory
4. Check for heredoc syntax issues

---

## Cleanup After Test

### If Test Successful ✅
```bash
# 1. Delete test tag locally
git tag -d v0.1.5-alpha.1-test

# 2. Delete test tag remotely
git push --delete origin v0.1.5-alpha.1-test

# 3. Delete GitHub release
# Go to: https://github.com/yourusername/Modan2/releases
# Find test release
# Click "Delete" button
```

### If Test Failed ❌
```bash
# 1. Fix issues
git add <fixed-files>
git commit -m "fix: Address test release issues"

# 2. Delete old test tag
git tag -d v0.1.5-alpha.1-test
git push --delete origin v0.1.5-alpha.1-test

# 3. Retry test release
git tag -a v0.1.5-alpha.1-test -m "Test release workflow validation (retry)"
git push origin v0.1.5-alpha.1-test
```

---

## Documentation of Results

### Create Test Report

**File**: `devlog/20251008_144_test_release_results.md`

**Template**:
```markdown
# Test Release Results

**Test Tag**: v0.1.5-alpha.1-test
**Date**: 2025-10-08
**Workflow URL**: [Link to GitHub Actions run]

## Summary
- Status: ✅ PASSED / ❌ FAILED
- Duration: {time}
- Issues Found: {count}

## Test Results
- Tests: ✅ / ❌
- Windows Build: ✅ / ❌
- macOS Build: ✅ / ❌
- Linux Build: ✅ / ❌
- Artifact Collection: ✅ / ❌
- Checksums: ✅ / ❌
- GitHub Release: ✅ / ❌

## Details
[Detailed results for each phase]

## Issues Found
[List any issues discovered]

## Recommendations
[Next steps based on results]
```

---

## Next Steps After Validation

### If All Tests Pass ✅
1. Document results in test report
2. Update Phase 8 progress
3. Proceed to platform testing (when hardware available)
4. Prepare for production release

### If Issues Found ❌
1. Document issues in test report
2. Create GitHub issues for tracking
3. Fix critical issues
4. Retry test release
5. Update workflow documentation

---

## Timeline

**Estimated Time**: 1-2 hours

**Breakdown**:
- Tag creation and push: 5 minutes
- Workflow execution: 20-40 minutes
  - Tests: 5-10 minutes
  - Builds (parallel): 10-20 minutes
  - Release creation: 5-10 minutes
- Verification and download: 15-30 minutes
- Documentation: 15-30 minutes

**Total**: ~1-2 hours for complete validation

---

## Conclusion

This test release validates all critical CI/CD improvements from Phase 8 Day 1:
- ✅ Test-before-release pattern
- ✅ macOS app bundle fix
- ✅ Artifact collection reliability
- ✅ SHA256 checksum integration
- ✅ RELEASE_NOTES.md automation

**Ready to Execute**: Yes, all prerequisites met
**Risk Level**: Low (using test tag, easy cleanup)
**Expected Outcome**: Full validation of release workflow

---

**Plan Version**: 1.0
**Created**: 2025-10-08
**For Phase**: Phase 8 Day 2
**Status**: ✅ Ready to Execute
