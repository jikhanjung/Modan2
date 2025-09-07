# Release Guide for Modan2

## Release Methods

### 1. Manual Release (GitHub Actions UI)
**Best for**: Controlled releases at specific points

1. Go to Actions tab in GitHub
2. Select "Manual Release" workflow
3. Click "Run workflow"
4. Fill in:
   - Version tag (e.g., `v0.1.4-beta.5`)
   - Pre-release checkbox
   - Optional release notes
5. Click "Run workflow"

### 2. Commit Message Triggered Release
**Best for**: Automated releases with specific commits

Add `[release]` or `[pre-release]` to your commit message:

```bash
git commit -m "feat: Add new feature [pre-release]"
git push
```

This will automatically:
- Build all platforms
- Create a release with version from version.py
- Tag as `v{version}-build.{number}`

### 3. Tag-based Release (Existing)
**Best for**: Version-specific releases

```bash
git tag -a v0.1.4-beta.5 -m "Release v0.1.4-beta.5"
git push origin v0.1.4-beta.5
```

## Version Management Strategy

### Option A: Build Numbers Only
Keep the same pre-release version (e.g., `0.1.4-beta.1`) and differentiate by build numbers:
- `v0.1.4-beta.1-build.100`
- `v0.1.4-beta.1-build.101`
- `v0.1.4-beta.1-build.102`

### Option B: Date-based Versions
Use date in version for nightly/continuous builds:
- `v0.1.4-beta.20250107.1`
- `v0.1.4-beta.20250107.2`

### Option C: Commit-based
Use short commit hash:
- `v0.1.4-beta.1+abc1234`
- `v0.1.4-beta.1+def5678`

## Recommended Workflow

1. **Development Phase**: 
   - Regular commits without releases
   - Use `[skip ci]` in commit message to skip builds

2. **Testing Release**:
   - Use Manual Release workflow
   - Or commit with `[pre-release]` message

3. **Official Release**:
   - Update version.py to remove pre-release tag
   - Use `python manage_version.py release`
   - Create tag and push

## Examples

### Quick Pre-release from Current Commit
```bash
git commit -m "fix: Important bug fix [pre-release]"
git push
```

### Manual Release from Specific Commit
1. Checkout the commit: `git checkout abc1234`
2. Go to GitHub Actions → Manual Release
3. Run with desired version tag

### Skip Version Bump for Testing
Use the manual workflow with custom version like:
- `v0.1.4-beta.5-test1`
- `v0.1.4-beta.5-rc1`

This way you don't need to constantly bump the version number in version.py.