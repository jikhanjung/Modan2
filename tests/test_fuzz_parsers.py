"""Property-based (fuzz) robustness tests for the landmark file parsers.

The readers ingest arbitrary user files, so malformed input must fail in a
controlled way (a ValueError / OSError the UI can surface) — never an ungraceful
IndexError/KeyError/UnboundLocalError, and never a hang. R04 hardened several of
these paths; this fuzzes them to keep it that way. See docs/CODE_QUALITY_GUIDE §3.
"""

import os
import tempfile

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import MdUtils as mu
from components.formats import NTS, TPS, X1Y1, Morphologika

# Steer random input toward real parser branches (format keywords, coord rows,
# section headers) mixed with free text.
_tokens = st.sampled_from(
    [
        "LM=3",
        "LM=",
        "LM=abc",
        "ID=spec",
        "IMAGE=x.jpg",
        "SCALE=1.0",
        "3 2 1 0 DIM=2",
        "2 3 2 0 DIM=3",
        "1.0 2.0",
        "1.0\t2.0",
        "0.5 0.5 0.5",
        "[names]",
        "[rawpoints]",
        "[individuals]",
        "[dimensions]",
        "[landmarks]",
        "1",
        "-999",
        "9\t9\t9",
        "",
        "   ",
        "'comment",
    ]
)
_line = st.one_of(
    _tokens,
    st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=40),
)
_content = st.lists(_line, max_size=40).map(lambda ls: "\n".join(ls))

_SETTINGS = settings(max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow])

# A malformed file must fail controllably, not crash ungracefully.
ACCEPTABLE = (ValueError, OSError, UnicodeError)


def _run(reader, content, suffix):
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        reader(path)
    except ACCEPTABLE:
        pass
    finally:
        os.unlink(path)


@pytest.mark.timeout(120)
@_SETTINGS
@given(content=_content)
def test_read_tps_file_robust(content):
    _run(mu.read_tps_file, content, ".tps")


@pytest.mark.timeout(120)
@_SETTINGS
@given(content=_content)
def test_read_nts_file_robust(content):
    _run(mu.read_nts_file, content, ".nts")


@pytest.mark.timeout(120)
@_SETTINGS
@given(content=_content)
def test_tps_class_robust(content):
    _run(lambda p: TPS(p, "ds"), content, ".tps")


@pytest.mark.timeout(120)
@_SETTINGS
@given(content=_content)
def test_nts_class_robust(content):
    _run(lambda p: NTS(p, "ds"), content, ".nts")


@pytest.mark.timeout(120)
@_SETTINGS
@given(content=_content)
def test_x1y1_class_robust(content):
    _run(lambda p: X1Y1(p, "ds"), content, ".txt")


@pytest.mark.timeout(120)
@_SETTINGS
@given(content=_content)
def test_morphologika_class_robust(content):
    _run(lambda p: Morphologika(p, "ds"), content, ".txt")
