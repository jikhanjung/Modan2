"""Korean translations must not break the reStructuredText markup they carry.

reStructuredText requires inline markup to end at a word boundary: the closing
``**`` has to be followed by whitespace or ASCII punctuation. Korean has no
space before its particles, so the natural translation of "**Preferences** is"
comes out as ``**Preferences**(환경 설정)에서`` or ``**추가**합니다`` -- and
docutils then does not see emphasis at all. The build logs
"Inline strong start-string without end-string" among its other warnings and
carries on, so the page ships with the markup silently dropped.

The fix in the catalogue is an escaped space (``**추가**\\ 합니다``), which
renders as nothing and gives the parser the boundary it wants.

This is not hypothetical: three of these shipped in the 2026-08-07 catalogues
and were caught only because a later build was read closely.
"""

import re
from pathlib import Path

import pytest

CATALOGUE_DIR = Path(__file__).parent.parent / "docs" / "manual" / "locale" / "ko" / "LC_MESSAGES"

# What may follow a closing ``**``: whitespace, or the ASCII punctuation
# docutils accepts as a boundary. A Hangul syllable or an opening bracket is
# what this test exists to reject.
ALLOWED_AFTER_CLOSE = re.compile(r"[\s\-.,:;!?\\/'\")\]}>]")


def _catalogues():
    return sorted(CATALOGUE_DIR.glob("*.po")) if CATALOGUE_DIR.is_dir() else []


def _translated_strings(text):
    """Every msgstr value in a catalogue, joined across continuation lines.

    Reading the raw lines instead would flag the ``**`` that opens a value, its
    quote character looking exactly like the word it would have to be glued to.
    """
    values = []
    collecting = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("msgstr"):
            collecting = True
            values.append("")
            stripped = stripped[len("msgstr") :].strip()
            if not stripped:
                continue
        elif not (collecting and stripped.startswith('"')):
            collecting = False
            continue
        if stripped.startswith('"') and stripped.endswith('"') and len(stripped) >= 2:
            values[-1] += stripped[1:-1]
    return [v for v in values if v]


def _glued_closers(value):
    """Closing ``**`` markers with no boundary after them."""
    offenders = []
    for index, match in enumerate(re.finditer(r"\*\*", value)):
        if index % 2 == 0:
            continue  # an opener
        following = value[match.end() : match.end() + 1]
        if following and not ALLOWED_AFTER_CLOSE.match(following):
            offenders.append(value[max(0, match.start() - 30) : match.end() + 20])
    return offenders


@pytest.mark.skipif(not _catalogues(), reason="Korean catalogues are not present")
@pytest.mark.parametrize("catalogue", _catalogues(), ids=lambda p: p.name)
def test_bold_markup_keeps_its_boundary(catalogue):
    offenders = [
        f"{catalogue.name}: ...{context}"
        for value in _translated_strings(catalogue.read_text(encoding="utf-8"))
        for context in _glued_closers(value)
    ]

    assert not offenders, (
        "Inline markup glued to the text after it; docutils drops the emphasis.\n"
        "Put an escaped space after the closing ** (e.g. '**추가**\\ 합니다'):\n" + "\n".join(offenders)
    )
