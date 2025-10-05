# Phase 1: 기반 정리 (1개월)

**Date**: 2025-10-05
**Duration**: 1 month
**Goal**: Clean up codebase foundation and establish development standards
**Target Coverage**: 45% → 50%

---

## Overview

Phase 1 focuses on removing technical debt, standardizing code quality, and establishing development tools. This phase prepares the codebase for larger architectural improvements in Phase 2 and 3.

---

## Tasks

### 1. Dead Code Removal (Week 1)

#### 1.1 Remove Modan2_original.py
**Priority**: 🔴 Critical
**Estimated Time**: 30 minutes
**Files**: `Modan2_original.py` (1,500 lines)

**Actions:**
```bash
# 1. Verify no references exist
grep -r "Modan2_original" --include="*.py" .

# 2. Remove file
git rm Modan2_original.py

# 3. Commit
git commit -m "refactor: Remove unused Modan2_original.py (1,500 lines)"
```

**Verification:**
- [ ] No import statements reference this file
- [ ] No documentation references this file
- [ ] All tests pass after removal

---

#### 1.2 Remove/Archive test_script Directory
**Priority**: 🔴 Critical
**Estimated Time**: 2 hours
**Files**: 25 files in `test_script/`

**Actions:**
1. **Document legacy tests:**
   ```bash
   # Create documentation of what each test did
   ls test_script/*.py | xargs -I {} echo "- {}: $(head -5 {})"
   ```

2. **Create archive document:**
   ```markdown
   # test_script/ Archive

   Legacy manual test scripts replaced by pytest automation.

   ## Key Tests Migrated:
   - tps_test.py → tests/test_import.py
   - overlay_test.py → tests/test_ui_basic.py
   - ...
   ```

3. **Remove directory:**
   ```bash
   git rm -r test_script/
   git commit -m "refactor: Remove legacy test_script/ (replaced by pytest)"
   ```

**Verification:**
- [ ] All functionality covered by automated tests
- [ ] Documentation updated in CLAUDE.md
- [ ] No references in main code

---

### 2. Import Cleanup (Week 1-2)

#### 2.1 Remove Wildcard Imports
**Priority**: 🟡 High
**Estimated Time**: 4 hours
**Files**: `MdModel.py`, `migrate.py`

**Current State:**
```python
# MdModel.py
from peewee import *  # ❌ Imports 100+ symbols
```

**Target State:**
```python
# MdModel.py
from peewee import (
    Model, CharField, IntegerField, FloatField,
    TextField, BooleanField, DateTimeField,
    ForeignKeyField, SqliteDatabase, fn
)  # ✅ Explicit
```

**Actions:**
1. **Identify used symbols:**
   ```bash
   # Extract all peewee symbols used in MdModel.py
   grep -oE "\b[A-Z][a-zA-Z]*Field\b" MdModel.py | sort -u
   ```

2. **Replace wildcard import:**
   - List all used Peewee classes/functions
   - Add explicit imports
   - Test thoroughly

3. **Repeat for other files:**
   - `migrate.py`
   - Any other files with wildcard imports

**Verification:**
- [ ] All tests pass
- [ ] No unused imports (use ruff to check)
- [ ] Import order standardized

---

#### 2.2 Fix Duplicate Imports
**Priority**: 🟢 Medium
**Estimated Time**: 1 hour

**Current Issues:**
```python
# ModanDialogs.py
import logging  # Line 13
import logging  # Line 44 - DUPLICATE
```

**Actions:**
```bash
# Find all duplicate imports
ruff check --select F401,F811 .
```

**Fix:**
- Remove duplicate `import logging` statements
- Organize imports using `isort`

---

### 3. Code Quality Tools Setup (Week 2)

#### 3.1 Install Ruff (Linter + Formatter)
**Priority**: 🔴 Critical
**Estimated Time**: 2 hours

**Installation:**
```bash
pip install ruff
```

**Configuration:**
Create `pyproject.toml`:
```toml
[tool.ruff]
line-length = 120
target-version = "py312"

# Enable rules
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
]

# Ignore specific rules
ignore = [
    "E501",  # line too long (handled by formatter)
]

# Exclude directories
exclude = [
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "htmlcov",
    ".pytest_cache",
    "build",
    "dist",
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.ruff.isort]
known-first-party = ["MdModel", "MdUtils", "MdStatistics", "MdHelpers"]
```

**Actions:**
1. Run formatter on all files:
   ```bash
   ruff format .
   ```

2. Fix linting issues:
   ```bash
   ruff check --fix .
   ```

3. Review and commit changes

**Verification:**
- [ ] All files formatted consistently
- [ ] No critical linting errors
- [ ] Tests still pass

---

#### 3.2 Setup Pre-commit Hooks
**Priority**: 🟢 Medium
**Estimated Time**: 1 hour

**Installation:**
```bash
pip install pre-commit
```

**Configuration:**
Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
```

**Setup:**
```bash
pre-commit install
pre-commit run --all-files  # Test on all files
```

**Verification:**
- [ ] Hooks run on commit
- [ ] All files pass checks
- [ ] Document in CLAUDE.md

---

### 4. Type Hints Addition (Week 3)

#### 4.1 Add Type Hints to Core Modules
**Priority**: 🟡 High
**Estimated Time**: 8 hours

**Target Files (Priority Order):**
1. `MdStatistics.py` (already good coverage)
2. `MdUtils.py`
3. `ModanController.py`
4. `MdHelpers.py`

**Example Transformation:**
```python
# Before
def do_pca_analysis(landmarks_data, n_components=None):
    pass

# After
from typing import List, Optional, Dict, Any

def do_pca_analysis(
    landmarks_data: List[List[float]],
    n_components: Optional[int] = None
) -> Dict[str, Any]:
    pass
```

**Actions:**
1. **Install mypy:**
   ```bash
   pip install mypy
   ```

2. **Add types incrementally:**
   - Start with function signatures
   - Add parameter types
   - Add return types
   - Add variable annotations where needed

3. **Configure mypy:**
   Create `mypy.ini`:
   ```ini
   [mypy]
   python_version = 3.12
   warn_return_any = True
   warn_unused_configs = True
   disallow_untyped_defs = False  # Start lenient
   ignore_missing_imports = True

   [mypy-tests.*]
   ignore_errors = True
   ```

4. **Run type checker:**
   ```bash
   mypy MdStatistics.py MdUtils.py ModanController.py
   ```

**Verification:**
- [ ] No critical type errors
- [ ] Function signatures documented
- [ ] IDE autocomplete improved

---

#### 4.2 Add Type Stubs for Third-Party Libraries
**Priority**: 🟢 Low
**Estimated Time**: 2 hours

**Install type stubs:**
```bash
pip install types-Pillow types-requests
```

**Verification:**
- [ ] Reduced type errors in mypy
- [ ] Better IDE support

---

### 5. Documentation Updates (Week 4)

#### 5.1 Update CLAUDE.md
**Priority**: 🟡 High
**Estimated Time**: 2 hours

**Add sections:**
```markdown
## Code Quality Tools

### Linting and Formatting
- **Ruff**: `ruff check .` - Fast Python linter
- **Ruff Format**: `ruff format .` - Fast Python formatter
- **Pre-commit**: Automatically runs checks before commit

### Type Checking
- **mypy**: `mypy <file>` - Static type checker
- Configuration: See `mypy.ini`

### Usage
```bash
# Format all code
ruff format .

# Check for issues
ruff check .

# Run type checker
mypy MdStatistics.py

# Run all pre-commit hooks
pre-commit run --all-files
```
```

**Update sections:**
- Remove references to `test_script/`
- Add development workflow
- Update coverage targets

---

#### 5.2 Create Development Guide
**Priority**: 🟢 Medium
**Estimated Time**: 3 hours

Create `docs/DEVELOPMENT.md`:
```markdown
# Modan2 Development Guide

## Setup Development Environment

1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install dev dependencies: `pip install -r config/requirements-dev.txt`
4. Install pre-commit hooks: `pre-commit install`

## Code Standards

### Import Order
1. Standard library
2. Third-party libraries
3. Local imports

### Type Hints
- All new functions must have type hints
- Use `typing` module for complex types

### Testing
- Write tests for all new features
- Maintain >70% coverage for new code

## Workflow

1. Create feature branch
2. Write code + tests
3. Run checks: `pre-commit run --all-files`
4. Run tests: `pytest`
5. Submit PR
```

---

### 6. Coverage Improvements (Week 3-4)

#### 6.1 MdStatistics.py: 95% → 100%
**Priority**: 🟢 Medium
**Estimated Time**: 2 hours

**Uncovered Lines:**
- 131, 212, 237, 248, 258-261, 276, 348, 405, 436
- 749, 778-779, 786-787, 794-795, 802-809

**Actions:**
- Add error handling tests
- Test edge cases in MANOVA calculations
- Test division by zero scenarios

**Tests to Add:**
```python
def test_manova_singular_matrix():
    """Test MANOVA with singular covariance matrix."""
    # Construct data that causes singular matrix
    pass

def test_manova_zero_variance():
    """Test MANOVA with zero variance group."""
    pass
```

---

#### 6.2 MdUtils.py: 78% → 85%
**Priority**: 🟡 High
**Estimated Time**: 4 hours

**Focus Areas:**
- Lines 554-570: Image/Model file metadata
- Lines 689-702: ZIP package creation
- Lines 811-812, 828: Error handling

**Actions:**
1. Create mock file tests:
   ```python
   def test_collect_image_metadata(tmp_path):
       """Test image metadata collection."""
       # Create temporary image file
       img_path = tmp_path / "test.png"
       # ... test metadata extraction
   ```

2. Test ZIP operations with tempfile

---

#### 6.3 MdModel.py: 54% → 65%
**Priority**: 🟡 High
**Estimated Time**: 6 hours

**Focus Areas:**
- Lines 1064-1222: `MdDatasetOps` methods
- Lines 1438-1883: `MdObjectOps` methods
- Lines 611-728: File operations

**Actions:**
1. Test centroid calculations:
   ```python
   def test_get_centroid_size_2d():
       """Test 2D centroid size calculation."""
       obj = MdObject.create(...)
       obj.landmark_list = [[0, 0], [1, 0], [0, 1]]
       assert obj.get_centroid_size() > 0
   ```

2. Test file attachment methods (with mocks)

3. Test dataset operations:
   - Add/remove objects
   - Procrustes alignment
   - Mean shape calculation

---

## Testing Strategy

### Test Categories

1. **Unit Tests** (maintain >95%)
   - Pure functions
   - Helper methods
   - Calculations

2. **Integration Tests** (expand)
   - Database operations
   - File I/O
   - Analysis workflows

3. **Coverage Tracking**
   ```bash
   # Run with coverage
   pytest --cov=. --cov-report=html --cov-report=term

   # View report
   open htmlcov/index.html
   ```

---

## Deliverables

### Code Changes
- [ ] Modan2_original.py removed
- [ ] test_script/ removed (documented)
- [ ] Wildcard imports replaced with explicit imports
- [ ] Duplicate imports removed
- [ ] Code formatted with Ruff
- [ ] Type hints added to 4 core modules

### Tools & Configuration
- [ ] Ruff configured (`pyproject.toml`)
- [ ] Pre-commit hooks installed (`.pre-commit-config.yaml`)
- [ ] mypy configured (`mypy.ini`)
- [ ] Import order standardized

### Documentation
- [ ] CLAUDE.md updated
- [ ] DEVELOPMENT.md created
- [ ] Changelog updated

### Testing
- [ ] Coverage: 45% → 50%+
- [ ] MdStatistics.py: 95% → 100%
- [ ] MdUtils.py: 78% → 85%
- [ ] MdModel.py: 54% → 65%

### Quality Metrics
- [ ] 0 wildcard imports
- [ ] 0 duplicate imports
- [ ] <10 ruff errors
- [ ] <50 mypy errors (on typed modules)

---

## Success Criteria

1. ✅ All dead code removed (~2,000 lines)
2. ✅ Code quality tools operational
3. ✅ Import statements standardized
4. ✅ Type hints on core modules
5. ✅ Coverage increased to 50%+
6. ✅ Documentation updated
7. ✅ All existing tests pass
8. ✅ Pre-commit hooks enforcing standards

---

## Risks & Mitigation

### Risk 1: Breaking Changes from Refactoring
**Mitigation:**
- Run full test suite after each change
- Use feature branches
- Review diffs carefully

### Risk 2: Type Hint Errors
**Mitigation:**
- Start with lenient mypy config
- Gradually increase strictness
- Focus on public APIs first

### Risk 3: Time Overrun
**Mitigation:**
- Prioritize critical tasks (dead code, ruff)
- Type hints can extend into Phase 2
- Coverage improvements can be incremental

---

## Timeline

| Week | Tasks | Milestone |
|------|-------|-----------|
| **Week 1** | Dead code removal, Import cleanup start | Clean codebase |
| **Week 2** | Ruff setup, Pre-commit hooks, Import cleanup done | Tools operational |
| **Week 3** | Type hints addition, Coverage improvements | Better code quality |
| **Week 4** | Documentation, Final coverage push | Phase 1 complete |

---

## Next Steps

After Phase 1 completion:
- **Phase 2**: Architecture improvements (file splitting, MVC enforcement)
- **Phase 3**: Testing expansion (UI tests, integration tests, CI/CD)

---

**Status**: 📝 Planning
**Owner**: Development Team
**Last Updated**: 2025-10-05
