# GitHub Pages Setup Guide

## Using GitHub Actions Deployment (CTHarvester Style)

Modan2 documentation uses the modern GitHub Actions deployment method (same as CTHarvester).

## Setup Instructions

### 1. Configure GitHub Pages Settings

**CRITICAL**: Set Pages to use GitHub Actions!

1. Go to: https://github.com/jikhanjung/Modan2/settings/pages
2. Under **"Build and deployment"**:
   - **Source**: Select **"GitHub Actions"** (NOT "Deploy from a branch")
3. That's it! No need to select a branch.

### 2. Push Changes to Trigger Deployment

The workflow will run automatically when you push to main:

```bash
git add .github/workflows/docs.yml
git commit -m "docs: Update workflow to use GitHub Actions deployment"
git push origin main
```

### 3. Monitor Deployment

1. Go to: https://github.com/jikhanjung/Modan2/actions
2. Click on "Build and Deploy Documentation"
3. Wait for both jobs to complete:
   - ✅ build (builds HTML)
   - ✅ deploy (deploys to Pages)

### 4. Verify Deployment

After workflow completes (usually 2-3 minutes):

- https://jikhanjung.github.io/Modan2/ → redirects to `/en/`
- https://jikhanjung.github.io/Modan2/en/ → English docs
- https://jikhanjung.github.io/Modan2/ko/ → Korean docs

## How It Works

### Workflow Structure

1. **Build Job**:
   - Builds English docs: `sphinx-build -D language=en`
   - Builds Korean docs: `sphinx-build -D language=ko`
   - Creates redirect: `index.html` → `/en/`
   - Adds `.nojekyll` file
   - Uploads artifact: `actions/upload-pages-artifact@v3`

2. **Deploy Job**:
   - Deploys artifact to GitHub Pages: `actions/deploy-pages@v4`
   - Uses environment: `github-pages`

### Permissions

The workflow has:
```yaml
permissions:
  contents: read   # Read repository
  pages: write     # Deploy to Pages
  id-token: write  # OIDC token for deployment
```

No additional repository settings needed!

## Differences from gh-pages Branch Method

| Aspect | GitHub Actions (Current) | gh-pages Branch (Old) |
|--------|-------------------------|---------------------|
| Configuration | Source: "GitHub Actions" | Source: "Deploy from a branch" |
| Branch needed | No gh-pages branch | Requires gh-pages branch |
| Deployment | Automatic via artifact | Push to branch |
| Permissions | `pages: write` | `contents: write` |
| Speed | Faster (parallel) | Slower (sequential) |
| Recommended | ✅ Yes (modern) | ❌ Legacy method |

## Troubleshooting

### Issue: 404 Errors

**Cause**: Pages source not set to "GitHub Actions"

**Solution**:
1. Go to Settings → Pages
2. Source: Select "GitHub Actions"
3. Wait 2-3 minutes
4. Refresh https://jikhanjung.github.io/Modan2/

### Issue: Workflow Fails

**Error**: "Resource not accessible by integration"

**Solution**: Workflow permissions are automatically granted. If this error occurs:
1. Check Settings → Actions → General
2. Workflow permissions should be "Read and write permissions"
3. But for Pages deployment, read-only is sufficient

**Error**: "pages build and deployment" job fails

**Solution**:
1. Ensure Pages source is set to "GitHub Actions"
2. Re-run workflow from Actions tab

### Issue: Deployed but Still 404

**Cause**: Need to wait for Pages to process

**Solution**:
1. Wait 2-3 minutes after successful deployment
2. Hard refresh browser: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
3. Check deployment environment: https://github.com/jikhanjung/Modan2/deployments
4. Look for "github-pages" environment with "Active" status

## Verification Checklist

After first deployment:

- [ ] Workflow completed successfully (Actions tab)
- [ ] Both "build" and "deploy" jobs passed
- [ ] Deployment shows in: https://github.com/jikhanjung/Modan2/deployments
- [ ] https://jikhanjung.github.io/Modan2/ redirects to /en/
- [ ] https://jikhanjung.github.io/Modan2/en/index.html loads
- [ ] https://jikhanjung.github.io/Modan2/ko/index.html loads
- [ ] Language switcher works (🌐 button)

## Expected Deployment Flow

```
Push to main
  ↓
GitHub Actions triggered
  ↓
Build Job:
  - Install dependencies
  - Build EN docs → _build/html/en/
  - Build KO docs → _build/html/ko/
  - Create redirect → _build/html/index.html
  - Create .nojekyll → _build/html/.nojekyll
  - Upload artifact
  ↓
Deploy Job:
  - Download artifact
  - Deploy to GitHub Pages
  ↓
Site live at https://jikhanjung.github.io/Modan2/
```

## Manual Trigger

You can manually trigger deployment without pushing:

1. Go to: https://github.com/jikhanjung/Modan2/actions
2. Click "Build and Deploy Documentation"
3. Click "Run workflow" → Select "main" branch → "Run workflow"

## URLs After Deployment

- **Root**: https://jikhanjung.github.io/Modan2/
  - Redirects to English
- **English**:
  - Main: https://jikhanjung.github.io/Modan2/en/
  - Installation: https://jikhanjung.github.io/Modan2/en/installation.html
  - User Guide: https://jikhanjung.github.io/Modan2/en/user_guide.html
  - Developer Guide: https://jikhanjung.github.io/Modan2/en/developer_guide.html
- **Korean**:
  - Main: https://jikhanjung.github.io/Modan2/ko/
  - 설치: https://jikhanjung.github.io/Modan2/ko/installation.html
  - 사용자 가이드: https://jikhanjung.github.io/Modan2/ko/user_guide.html

## Updating Documentation

To update docs:

```bash
# Edit documentation
cd docs
vim user_guide.rst

# Build and test locally
make html
# Check _build/html/en/

# Commit and push
git add docs/
git commit -m "docs: Update user guide"
git push origin main

# GitHub Actions will automatically deploy
# Check: https://github.com/jikhanjung/Modan2/actions
```

## Key Advantages

✅ **No gh-pages branch management**
✅ **Automatic artifact cleanup**
✅ **Better security** (limited permissions)
✅ **Deployment history** (via Deployments tab)
✅ **Rollback support** (redeploy old artifact)
✅ **Same as CTHarvester** (proven method)
