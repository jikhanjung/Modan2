"""Font-rendering regression tests (i18n).

Guards the "Korean chart labels render as tofu" bug (devlog 241). The app builds
matplotlib's ``font.family`` from installed fonts (via
``MdHelpers.resolve_matplotlib_font_family``) so Latin uses a serif face and CJK
text falls back per-glyph. These tests pin that:

- the resolved family is a non-empty list and includes a CJK font when one is
  installed;
- rendering Korean text emits no "missing glyph" warning.

The render test skips when no CJK font is installed (local dev) and runs for real
on CI, which installs ``fonts-nanum``. pytest.ini also turns a missing-glyph
warning into an error globally; this test asserts it explicitly too, so it is
meaningful regardless of that config.
"""

import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest
from matplotlib import font_manager

from MdHelpers import resolve_matplotlib_font_family

_CJK_FONTS = (
    "Malgun Gothic",
    "Apple SD Gothic Neo",
    "AppleGothic",
    "NanumGothic",
    "NanumBarunGothic",
    "Gulim",
    "Batang",
)


def _has_cjk_font():
    available = {f.name for f in font_manager.fontManager.ttflist}
    return any(f in available for f in _CJK_FONTS)


def test_font_family_is_nonempty_list():
    family = resolve_matplotlib_font_family()
    assert isinstance(family, list)
    assert family  # never empty (falls back to ["serif"])


def test_font_family_includes_cjk_when_available():
    if not _has_cjk_font():
        pytest.skip("no CJK font installed on this machine")
    family = resolve_matplotlib_font_family()
    assert any(f in family for f in _CJK_FONTS), family


def test_korean_labels_render_without_missing_glyph():
    if not _has_cjk_font():
        pytest.skip("no CJK font installed on this machine")

    plt.rcParams["font.family"] = resolve_matplotlib_font_family()
    fig, ax = plt.subplots()
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ax.set_title("한글 제목")
            ax.set_xlabel("가로축 복사본")
            fig.canvas.draw()
        glyph_warnings = [w for w in caught if "missing from font" in str(w.message)]
        assert not glyph_warnings, [str(w.message) for w in glyph_warnings]
    finally:
        plt.close(fig)
