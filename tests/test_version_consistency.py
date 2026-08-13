"""Version single-source-of-truth tests.

``version.py`` is the only place a version number is written by hand. Every
other file that carries a version must *derive* from it rather than hardcode a
literal that can silently drift. These tests fail the build when a release bump
touches one file and forgets another — the failure mode that had left
``docs/manual/conf.py`` pinned at ``0.1.5`` while ``version.py`` said ``0.2.0-alpha.2``
(devlog R06).

Modan2's version-bearing files and how each stays in sync:

- ``setup.py``        — ``get_version()`` reads ``version.__version__``.
- ``docs/manual/conf.py`` — imports ``__version__`` from ``version.py``.
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
    source = (PROJECT_ROOT / "docs" / "manual" / "conf.py").read_text(encoding="utf-8")

    hardcoded = re.search(r"^\s*release\s*=\s*['\"]", source, re.MULTILINE)
    assert not hardcoded, "docs/manual/conf.py hardcodes `release`; import it from version.py instead"
    assert "from version import" in source, "docs/manual/conf.py must import the version from version.py"


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


class TestWindowsUpgradeReplacesTheExecutable:
    """The Windows installer must actually replace the previous build.

    0.2.0-beta.3 installed over beta.2 reported success and then launched
    beta.2. Two independent defects had to line up, and each is guarded here:

    1. ``build.py`` stamped every executable 0.0.0.0. It read a version-info
       template from ``build/`` -- a git-ignored directory where the file has
       never existed -- and its "missing template" fallback was a literal
       0.0.0.0 with none of the ``{{placeholders}}`` the substitution below it
       replaced. The substitution was a no-op on every CI build.
    2. The installer payload was not marked ``ignoreversion``, so Inno decided
       per file whether to replace it by comparing exactly those numbers.

    Equal versions mean "the installed file is not older", so Modan2.exe was
    kept. A test that only checked the version *string* somewhere would have
    missed this entirely: nothing was inconsistent, everything was 0.0.0.0.
    """

    def test_file_version_is_not_zero(self):
        from build_version_info import windows_file_version

        assert windows_file_version("0.2.0-beta.3", "873") != (0, 0, 0, 0)

    def test_file_version_rises_between_prereleases(self):
        """beta.2 -> beta.3 must look like an upgrade to Inno, not a reinstall."""
        from build_version_info import windows_file_version

        assert windows_file_version("0.2.0-beta.2", "844") < windows_file_version("0.2.0-beta.3", "873")

    def test_prerelease_stage_does_not_collide(self):
        """alpha.2 and beta.2 are different releases and must differ here.

        Only digits fit in a Windows file version, so the stage cannot be
        encoded; scraping digits from the full version string gave both
        (0, 2, 0, 2). The build number in the fourth field is what separates
        them.
        """
        from build_version_info import windows_file_version

        assert windows_file_version("0.2.0-alpha.2", "700") != windows_file_version("0.2.0-beta.2", "844")

    def test_release_beats_its_prereleases(self):
        from build_version_info import windows_file_version

        assert windows_file_version("0.2.0-beta.3", "873") < windows_file_version("0.2.0", "900")

    def test_development_build_has_no_build_number(self):
        from build_version_info import windows_file_version

        assert windows_file_version("0.2.0-beta.3", "local") == (0, 2, 0, 0)

    def test_version_info_file_carries_the_real_version(self, tmp_path, monkeypatch):
        """The generated file must contain the version, not a placeholder or 0.0.0.0."""
        from build_version_info import prepare_version_info_file

        monkeypatch.chdir(tmp_path)  # prove it does not depend on a template on disk
        written = Path(prepare_version_info_file("0.2.0-beta.3", "Modan2", "873")).read_text(encoding="utf-8")

        assert "filevers=(0, 2, 0, 873)" in written
        assert "0.0.0.0" not in written, "version info still stamps the 0.0.0.0 that blocked upgrades"
        assert "{{" not in written, "unsubstituted placeholder left in the version info file"
        assert "0.2.0-beta.3" in written, "the human-readable version should appear in the string fields"

    def test_installer_payload_is_ignoreversion(self):
        """Replacement must not depend on the version numbers being right."""
        source = (PROJECT_ROOT / "InnoSetup" / "Modan2.iss.template").read_text(encoding="utf-8")

        payload = [line for line in source.splitlines() if line.startswith("Source:") and 'DestDir: "{app}"' in line]
        assert payload, "no payload entries found in the installer template"
        for line in payload:
            assert "ignoreversion" in line, f"payload entry may be skipped on upgrade: {line}"
