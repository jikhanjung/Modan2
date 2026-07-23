"""Encoding robustness for the landmark file readers.

The readers used a bare ``open(path)``, which decodes with the platform locale,
so a UTF-8 file with a non-ASCII specimen name failed to import on a non-UTF-8
Windows box (cp949), and vice versa. ``open_text`` now decodes UTF-8 first, then
the platform encoding, then latin-1. These tests write the raw bytes directly so
they are independent of the machine's locale.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.formats._encoding import open_text
from components.formats.tps import TPS

_TPS = "LM=2\n1.0 2.0\n3.0 4.0\nID={name}\n"


class TestOpenText:
    def test_reads_utf8(self, tmp_path):
        p = tmp_path / "a.txt"
        p.write_bytes("가나다\nhello\n".encode())  # utf-8
        with open_text(str(p)) as f:
            assert f.read() == "가나다\nhello\n"

    def test_reads_legacy_cp949(self, tmp_path):
        p = tmp_path / "b.txt"
        p.write_bytes("가나다\n".encode("cp949"))  # not valid utf-8
        with open_text(str(p)) as f:
            # utf-8 decode fails -> falls back; the Korean text round-trips on a
            # cp949 box, and at worst decodes to latin-1 replacement elsewhere.
            text = f.read()
        assert text.endswith("\n")
        assert len(text) > 1

    def test_never_raises_on_arbitrary_bytes(self, tmp_path):
        p = tmp_path / "c.txt"
        p.write_bytes(bytes(range(256)))  # every byte value
        with open_text(str(p)) as f:
            assert isinstance(f.read(), str)  # latin-1 fallback, no exception

    def test_strips_utf8_bom(self, tmp_path):
        p = tmp_path / "d.txt"
        p.write_bytes(b"\xef\xbb\xbfLM=2\n")  # BOM + content
        with open_text(str(p)) as f:
            assert f.read() == "LM=2\n"  # BOM removed by utf-8-sig


class TestTpsNonAsciiName:
    def test_utf8_specimen_name_imports(self, tmp_path):
        p = tmp_path / "u.tps"
        p.write_bytes(_TPS.format(name="표본1").encode())  # utf-8
        tps = TPS(str(p), "ds")
        assert tps.object_name_list == ["표본1"]
        assert tps.landmark_data["표본1"] == [[1.0, 2.0], [3.0, 4.0]]

    def test_cp949_specimen_name_imports(self, tmp_path):
        p = tmp_path / "k.tps"
        p.write_bytes(_TPS.format(name="표본1").encode("cp949"))  # legacy
        tps = TPS(str(p), "ds")
        # The import succeeds and coordinates are intact regardless of how the
        # name decodes (it used to abort on a UTF-8 box).
        assert tps.nobjects == 1
        assert list(tps.landmark_data.values())[0] == [[1.0, 2.0], [3.0, 4.0]]
