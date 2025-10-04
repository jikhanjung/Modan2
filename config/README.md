# Configuration Files

This directory contains configuration files for development, testing, and CI/CD.

## Requirements Files

### `requirements-dev.txt`
Development and testing dependencies for local development.

**Install:**
```bash
pip install -r config/requirements-dev.txt
```

**Includes:**
- Testing framework (pytest, pytest-cov, pytest-mock, pytest-qt)
- Performance monitoring (psutil)
- Coverage reporting
- Optional code quality tools (commented out)

**Version Strategy:**
- Lower bound: Minimum tested version with required features
- Upper bound: Next major version (to prevent breaking changes)
- Example: `>=8.4.0,<9.0` allows 8.x series but blocks 9.x

### `requirements-ci.txt`
CI/CD testing dependencies for automated testing environments.

**Install:**
```bash
pip install -r config/requirements-ci.txt
```

**Includes:**
- All items from `requirements-dev.txt`
- Base application dependencies (`requirements.txt`)
- CI-specific tools (pytest-xvfb for headless GUI testing)

**Used by:** GitHub Actions workflow (`.github/workflows/test.yml`)

## Pytest Configuration

### `pytest.ini`
Main pytest configuration file.

**Key settings:**
- Test discovery: `tests/` directory
- Markers: unit, integration, slow, performance, gui
- Output: verbose with short tracebacks
- Qt API: PyQt5

**Run tests:**
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific markers
pytest -m unit          # Fast unit tests only
pytest -m "not slow"    # Skip slow tests
pytest -m gui           # GUI tests only
```

## Usage Examples

### Local Development

```bash
# First-time setup
pip install -r requirements.txt
pip install -r config/requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Run specific test categories
pytest -m unit          # Fast tests only
pytest -m integration   # Integration tests
pytest -m "not slow"    # Skip slow tests
```

### CI/CD (GitHub Actions)

The workflow automatically:
1. Installs system dependencies (Qt, OpenGL, etc.)
2. Installs Python dependencies from `config/requirements-ci.txt`
3. Runs tests with xvfb (headless GUI)
4. Generates coverage reports
5. Uploads results to Codecov

**Manual trigger:**
```bash
# On GitHub: Actions → Tests → Run workflow
```

### Test Coverage

Current coverage: **34%** (baseline)

**Coverage by file:**
- `MdModel.py`: 47%
- `ModanController.py`: 53%
- `MdStatistics.py`: 44%
- `Modan2.py`: 40%
- `ModanDialogs.py`: 21%
- `ModanComponents.py`: 25%

**Coverage goals:**
- Core logic (Model, Controller, Statistics): 70%+
- UI components: 40%+
- Overall: 50%+

### Adding New Dependencies

#### Development dependency:
```bash
# 1. Install locally
pip install package-name

# 2. Add to config/requirements-dev.txt with version constraint
echo "package-name>=x.y.z,<x+1.0" >> config/requirements-dev.txt

# 3. Test installation
pip install -r config/requirements-dev.txt
```

#### Application dependency:
```bash
# 1. Install locally
pip install package-name

# 2. Add to requirements.txt
echo "package-name>=x.y.z" >> requirements.txt

# 3. Test installation
pip install -r requirements.txt
```

## Version Constraints Explained

### Semantic Versioning (SemVer)
- **Major.Minor.Patch** (e.g., 8.4.1)
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Common Patterns

```python
# Exact version (not recommended - too restrictive)
pytest==8.4.1

# Minimum version (not recommended - could break)
pytest>=8.4.0

# Recommended: Major version lock
pytest>=8.4.0,<9.0      # Allows 8.x, blocks 9.x

# Very strict: Minor version lock
pytest>=8.4.0,<8.5      # Only 8.4.x series

# Compatible release (equivalent to >=8.4.0,<9.0)
pytest~=8.4.0
```

### Our Strategy
- **Lower bound**: Minimum version we've tested
- **Upper bound**: Next major version (breaking changes expected)
- **Rationale**: Balance between stability and getting bug fixes

## Troubleshooting

### Import errors in CI
```bash
# Check: Is dependency in requirements-ci.txt?
# Fix: Add to requirements-ci.txt
```

### Version conflicts
```bash
# Check: pip list | grep package-name
# Fix: Adjust version constraints in requirements files
```

### Tests pass locally but fail in CI
```bash
# Common causes:
# 1. Missing system dependency (add to test.yml)
# 2. Display-related issue (check xvfb setup)
# 3. Timing issue (add pytest-timeout)
```

### Coverage not measured
```bash
# Check: Is pytest-cov installed?
pip install pytest-cov

# Run with coverage
pytest --cov=. --cov-report=term
```

## Related Documentation

- [Test Status Analysis](../devlog/20251004_066_test_status_analysis.md)
- [GitHub Actions Workflow](../.github/workflows/test.yml)
- [Pytest Configuration](pytest.ini)
