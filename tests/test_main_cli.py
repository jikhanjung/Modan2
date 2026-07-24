"""CLI argument parsing for main.py.

Guards the flags the CI packaged-artifact smoke test depends on — in particular
``--self-test`` (reusable_build.yml runs the frozen exe with it). If someone
renames or drops the flag, this fails in unit tests instead of only surfacing as
a red build job.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import main  # noqa: E402


def _parse(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py", *argv])
    return main.parse_arguments()


def test_self_test_flag_defaults_false(monkeypatch):
    assert _parse([], monkeypatch).self_test is False


def test_self_test_flag_parses(monkeypatch):
    args = _parse(["--self-test", "--no-splash"], monkeypatch)
    assert args.self_test is True
    assert args.no_splash is True


def test_lang_choices(monkeypatch):
    assert _parse(["--lang", "ko"], monkeypatch).lang == "ko"
    assert _parse([], monkeypatch).lang == "en"  # default
