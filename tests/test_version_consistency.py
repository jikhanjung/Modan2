"""Version single-source-of-truth tests.

``version.py`` is the only place a version number is written by hand. Every
other file that carries a version must *derive* from it rather than hardcode a
literal that can silently drift. These tests fail the build when a release bump
touches one file and forgets another — the failure mode that had left
``docs/conf.py`` pinned at ``0.1.5`` while ``version.py`` said ``0.2.0-alpha.2``
(devlog R06).

Modan2's version-bearing files and how each stays in sync:

- ``setup.py``        — ``get_version()`` reads ``version.__version__``.
- ``docs/conf.py``    — imports ``__version__`` from ``version.py``.
- InnoSetup template  — uses a ``{{VERSION}}`` placeholder injected at build time.

There is no ``[project]`` table in ``pyproject.toml`` (it holds tool config only)
and no Rust crate, so those checks from the sibling CTHarvester suite do not
apply here.
"""

import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from version import __version__, __version_info__  # noqa: E402


def test_version_is_valid_semver():
    """version.py must parse as semver; the build and installer both assume it."""
    semver = pytest.importorskip("semver")
    parsed = semver.VersionInfo.parse(__version__)
    assert (parsed.major, parsed.minor, parsed.patch) == __version_info__


def test_docs_conf_derives_version():
    """Sphinx ``release`` must be imported from version.py, not typed in."""
    source = (PROJECT_ROOT / "docs" / "conf.py").read_text(encoding="utf-8")

    hardcoded = re.search(r"^\s*release\s*=\s*['\"]", source, re.MULTILINE)
    assert not hardcoded, "docs/conf.py hardcodes `release`; import it from version.py instead"
    assert "from version import" in source, "docs/conf.py must import the version from version.py"


def test_setup_derives_version():
    """setup.py must source its version from version.py, never a literal."""
    source = (PROJECT_ROOT / "setup.py").read_text(encoding="utf-8")

    assert "version=get_version()" in source, "setup.py should call get_version() for the version"
    # get_version() must read from version.py (import or regex), not embed a literal.
    assert "from version import __version__" in source
    hardcoded = re.search(r"version\s*=\s*['\"]\d+\.\d+", source)
    assert not hardcoded, "setup.py appears to hardcode a version literal"


def test_innosetup_template_uses_placeholder():
    """The installer template must take its version from the build-time placeholder."""
    template = PROJECT_ROOT / "InnoSetup" / "Modan2.iss.template"
    source = template.read_text(encoding="utf-8")

    assert "{{VERSION}}" in source, "InnoSetup template must use the {{VERSION}} placeholder"
    # No hardcoded AppVersion literal like `#define AppVersion "0.2.0"`.
    hardcoded = re.search(r'#define\s+AppVersion\s+"\d+\.\d+', source)
    assert not hardcoded, "InnoSetup template hardcodes AppVersion; use the {{VERSION}} placeholder"
