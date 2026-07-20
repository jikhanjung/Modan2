"""Tests for ``*...*`` -> italic legend label handling."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dialogs.scatter_utils import apply_legend_italics, format_legend_label


class TestFormatLegendLabel:
    """Whole-label spans go the fontstyle route; partial spans go mathtext."""

    def test_fully_wrapped_strips_asterisks_and_flags_italic(self):
        assert format_legend_label("*Eurekia*") == ("Eurekia", True)

    def test_fully_wrapped_multiword(self):
        assert format_legend_label("*Eurekia bella*") == ("Eurekia bella", True)

    def test_fully_wrapped_non_ascii(self):
        # Hangul cannot be rendered by mathtext, so it must take the
        # fontstyle path rather than being wrapped in $\mathit{}$.
        text, italic = format_legend_label("*유레키아*")
        assert (text, italic) == ("유레키아", True)
        assert "$" not in text

    def test_plain_label_untouched(self):
        assert format_legend_label("Eurekia") == ("Eurekia", False)

    def test_lone_asterisk_untouched(self):
        assert format_legend_label("Group *") == ("Group *", False)
        assert format_legend_label("*") == ("*", False)

    def test_empty_span_untouched(self):
        assert format_legend_label("**") == ("**", False)

    def test_partial_span_becomes_mathtext(self):
        text, italic = format_legend_label("*Eurekia* sp.")
        assert italic is False
        assert text == r"$\mathit{Eurekia}$ sp."

    def test_partial_span_escapes_spaces(self):
        text, _ = format_legend_label("*Eurekia bella* Walcott")
        assert text == r"$\mathit{Eurekia\ bella}$ Walcott"

    def test_multiple_spans(self):
        text, italic = format_legend_label("*Aa* and *Bb*")
        assert italic is False
        assert text == r"$\mathit{Aa}$ and $\mathit{Bb}$"

    def test_mathtext_special_chars_escaped(self):
        text, _ = format_legend_label("*a_b^c* x")
        assert text == r"$\mathit{a\_b\^c}$ x"

    def test_non_string_passthrough(self):
        assert format_legend_label(None) == (None, False)
        assert format_legend_label(3) == (3, False)


class _FakeText:
    def __init__(self):
        self.fontstyle = None

    def set_fontstyle(self, style):
        self.fontstyle = style


class _FakeLegend:
    def __init__(self, n):
        self._texts = [_FakeText() for _ in range(n)]

    def get_texts(self):
        return self._texts


class TestApplyLegendItalics:
    def test_only_fully_wrapped_entries_italicised(self):
        keys = ["*Eurekia*", "Outgroup", "*Bathyuriscus* sp."]
        legend = _FakeLegend(len(keys))
        apply_legend_italics(legend, keys)
        styles = [t.fontstyle for t in legend.get_texts()]
        # 3rd is a partial span -> handled by mathtext, not fontstyle
        assert styles == ["italic", None, None]

    def test_returns_legend(self):
        legend = _FakeLegend(1)
        assert apply_legend_italics(legend, ["*A*"]) is legend

    def test_tolerates_label_count_mismatch(self):
        legend = _FakeLegend(1)
        apply_legend_italics(legend, ["*A*", "*B*"])
        assert legend.get_texts()[0].fontstyle == "italic"
